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

#!/usr/bin/env python
"""RQ worker to process sentence augmentation tasks."""

import os
from redis import Redis
from rq import SpawnWorker, Worker, Queue
import time

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
QUEUE_NAME = os.getenv("QUEUE_NAME", "sentence")
WORKER_TTL = 86400


def wait_for_redis(url: str, retries: int = 20, delay: float = 0.5) -> Redis:
    last_err = None
    for _ in range(retries):
        try:
            conn = Redis.from_url(url)
            conn.ping()
            return conn
        except Exception as e:
            last_err = e
            time.sleep(delay)
    raise last_err

def main() -> None:
    redis_conn = Redis.from_url(REDIS_URL)
    print("=================== REDIS WORKER =============================================")
    print(f"Connecting to Redis at: {REDIS_URL}")
    queue = Queue('sentence', connection=redis_conn)
    if os.getenv("CODE_LOCATION", "non-mac") == "mac":
        print("New worker on Mac")
        worker = SpawnWorker([queue], worker_ttl=WORKER_TTL)
    elif os.getenv("CODE_LOCATION", "non-mac") == "railway":
        print("New worker on Railway")
        worker = Worker([queue], worker_ttl=WORKER_TTL)
    else:
        print("New worker not on Mac or Railway... did you forget to set the CODE_LOCATION environment variable?")
        worker = SpawnWorker([queue], worker_ttl=WORKER_TTL)
    worker.work()

if __name__ == "__main__":
    main()
