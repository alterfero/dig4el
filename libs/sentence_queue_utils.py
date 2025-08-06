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
from typing import Dict
from libs import utils as u
from redis import Redis
from rq import Queue

from libs import semantic_description_utils as sdu

# Default Redis connection details
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = os.getenv("QUEUE_NAME", "sentence")
redis_client = Redis.from_url(REDIS_URL)

def _process_sentence_pair(sentence_pair: Dict, output_dir: str) -> Dict:
    """Worker task to enrich a sentence pair and append it to a JSONL file."""
    print("_process_sentence_pair")
    print(sentence_pair)
    result = sdu.add_description_and_keywords_to_sentence_pair(sentence_pair)
    if result is not None:
        filename = u.clean_sentence(sentence_pair["source"], filename=True) + ".json"
        # write file to volume
        with open(os.path.join(output_dir, filename), "a", encoding="utf-8") as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
    return result


def enqueue_sentence_pair(sentence_pair: Dict, output_dir: str) -> str:
    q = Queue(QUEUE_NAME, connection=redis_client)
    job = q.enqueue(
        _process_sentence_pair,
        sentence_pair,
        output_dir,
        job_timeout=600,
    )
    return job.id
