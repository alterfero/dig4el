# Copyright (C) 2024 Sebastien CHRISTIAN, University of French Polynesia
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""Utilities for queuing sentence augmentation tasks using Redis RQ."""

from __future__ import annotations

import json
import os
from typing import Dict, Optional, Iterable, List
from libs import utils as u
from redis import Redis
from rq import Queue, get_current_job
from rq.job import Job
import time


from libs import semantic_description_utils as sdu

# Default Redis connection details
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = os.getenv("QUEUE_NAME", "sentence")
RESULT_TTL_SECONDS = 604800  # 7 days
redis_client = Redis.from_url(REDIS_URL)
DATA_PATH = os.path.join(
    os.getenv("RAILWAY_VOLUME_MOUNT_PATH", "./job_outputs"), "data")


def _process_sentence_pair(sentence_pair: Dict, batch_id: Optional[str] = None) -> Optional[Dict]:
    """
    Long-running worker: enrich and return JSON-serializable dict.
    Also updates Redis sets for progress and stores heartbeat progress in job.meta.
    """
    print("_process_sentence_pair {}, batch_id {}".format(sentence_pair["source"], batch_id))
    job = get_current_job()
    try:
        # mark started for batch progress (idempotent)
        if batch_id:
            redis_client.sadd(f"batch:{batch_id}:started", job.id)

        # optional: progress checkpoints in meta (visible via Job.fetch)
        job.meta["progress"] = {"stage": "enriching", "ts": time.time()}
        job.save_meta()
        print(job.meta)

        result, filename = sdu.add_description_and_keywords_to_sentence_pair(sentence_pair)

        # save on worker's volume
        with open(os.path.join(DATA_PATH, filename), "w") as f:
            json.dump(result, indent=2, ensure_ascii=False)


        if result is None:
            raise RuntimeError("Augmentation returned None")

        # update meta upon success
        job.meta["progress"] = {"stage": "done", "ts": time.time()}
        job.save_meta()
        print(job.meta)

        # mark finished
        if batch_id:
            pipe = redis_client.pipeline()
            pipe.sadd(f"batch:{batch_id}:finished", job.id)
            pipe.srem(f"batch:{batch_id}:started", job.id)
            pipe.execute()
        output = {"result": result,
                  "filename": filename}
        print("output: {}".format(output))
        return output

    except Exception as e:
        # mark failed for batch progress
        if batch_id:
            pipe = redis_client.pipeline()
            pipe.sadd(f"batch:{batch_id}:failed", job.id)
            pipe.srem(f"batch:{batch_id}:started", job.id)
            pipe.execute()
        raise

def enqueue_sentence_pair(sentence_pair: Dict, batch_id: Optional[str]) -> str:
    q = Queue(QUEUE_NAME, connection=redis_client)
    job = q.enqueue(
        _process_sentence_pair,
        sentence_pair,
        batch_id,
        job_timeout=900,          # 15 min to be safe
        result_ttl=RESULT_TTL_SECONDS,
        ttl=RESULT_TTL_SECONDS,   # keep queued jobs around
        failure_ttl=RESULT_TTL_SECONDS
    )
    if batch_id:
        pipe = redis_client.pipeline()
        pipe.sadd(f"batch:{batch_id}:jobs", job.id)
        pipe.sadd(f"batch:{batch_id}:queued", job.id)
        pipe.execute()
    return job.id


def enqueue_batch(pairs: Iterable[Dict]) -> str:
    # get a meaningful batch id
    try:
        batch_id = "batch_" + u.clean_sentence(pairs[0]["source"], filename=True)
    except:
        batch_id = os.urandom(8).hex()

    for p in pairs:
        enqueue_sentence_pair(p, batch_id)
    return batch_id


def get_batch_progress(batch_id: str) -> Dict:
    key = lambda suffix: f"batch:{batch_id}:{suffix}"

    pipe = redis_client.pipeline()
    pipe.scard(key("jobs"))
    pipe.scard(key("queued"))
    pipe.scard(key("started"))
    pipe.scard(key("finished"))
    pipe.scard(key("failed"))
    total, queued, started, finished, failed = pipe.execute()

    pct = (finished / total * 100) if total else 0.0
    return {
        "batch_id": batch_id,
        "total": total,
        "queued": queued,
        "started": started,
        "finished": finished,
        "failed": failed,
        "percent_complete": round(pct, 1),
    }


def _decode_ids(ids: List[object]) -> List[str]:
    """Convert Redis bytes IDs to strings for RQ."""
    out = []
    for x in ids:
        if isinstance(x, (bytes, bytearray)):
            out.append(x.decode("utf-8"))
        else:
            out.append(str(x))
    return out


def load_job_return(job: Job):
    # Always refresh to pull latest data from Redis
    job.refresh()

    status = job.get_status()
    if status == "failed":
        # Reads the traceback string
        return {"_status": "failed", "_exc": job.exc_info}

    val = job.return_value()  # RQ >= 1.16
    # If you're on older RQ, use: val = job.result

    if val is None:
        print("Job value is None: statut: {}, meta: {}".format(status, job.meta))
        # Common reasons: result_ttl expired OR task returned None
        return {
            "_status": status,
            "_note": "No return value (maybe expired or task returned None)",
            "_enqueued_at": job.enqueued_at,
            "_ended_at": job.ended_at,
            "_meta": job.meta,
        }
    return val


def persist_finished_results(batch_id: str, output_dir: str, max_items: int = 1000) -> int:
    print("Persist finished results")
    os.makedirs(output_dir, exist_ok=True)

    finished_key = f"batch:{batch_id}:finished"
    raw_ids = list(redis_client.sscan_iter(finished_key, count=max_items))
    finished_ids = _decode_ids(raw_ids)[:max_items]
    if not finished_ids:
        return 0

    jobs = Job.fetch_many(finished_ids, connection=redis_client)

    written = 0
    for job in jobs:
        if job is None:
            continue
        job.refresh()
        result = job.return_value()
        if not result:
            print(f"Job {job.id}: no return value (status={job.get_status()})")
            print(job.meta)
            continue

        fname = result.get("filename", job.id) + ".json"
        print("Writing {} on volume".format(fname))
        with open(os.path.join(output_dir, fname), "w", encoding="utf-8") as f:
            u.save_json_normalized(result.get("result", result), f, ensure_ascii=False)
        written += 1
    print("Written {} job results on volume".format(written))
    return written


def clear_batch(batch_id: str, delete_jobs: bool = False) -> dict:
    """
    Remove all Redis keys and optionally delete all RQ jobs for a batch.
    """
    prefixes = ["jobs", "queued", "started", "finished", "failed"]
    keys = [f"batch:{batch_id}:{suffix}" for suffix in prefixes]

    removed_jobs = 0
    removed_keys = 0

    # Optionally delete the RQ job hashes themselves
    if delete_jobs:
        # Collect all job IDs from all sets
        job_ids = set()
        for key in keys:
            job_ids.update(x.decode("utf-8") if isinstance(x, bytes) else str(x)
                           for x in redis_client.smembers(key))
        for jid in job_ids:
            try:
                Job.fetch(jid, connection=redis_client).delete(remove_from_queue=True, pipeline=None)
                removed_jobs += 1
            except Exception as e:
                print(f"Could not delete job {jid}: {e}")

    # Delete the batch tracking keys
    if keys:
        removed_keys = redis_client.delete(*keys)

    return {
        "removed_batch_keys": removed_keys,
        "removed_jobs": removed_jobs
    }

def flush_all():
    redis_client.flushall()

