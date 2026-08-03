"""Entrypoint for the arq background worker.

Run with:  uv run python run_worker.py
"""

import asyncio

from arq import create_pool
from arq.worker import Worker

from app.workers.settings import WorkerSettings


async def main() -> None:
    pool = await create_pool(WorkerSettings.redis_settings)
    worker = Worker(
        functions=WorkerSettings.functions,
        cron_jobs=WorkerSettings.cron_jobs,
        redis_pool=pool,
        on_startup=WorkerSettings.on_startup,
        on_shutdown=WorkerSettings.on_shutdown,
        max_jobs=WorkerSettings.max_jobs,
        job_timeout=WorkerSettings.job_timeout,
        keep_result=WorkerSettings.keep_result,
        max_tries=WorkerSettings.max_tries,
    )
    await worker.async_run()


if __name__ == "__main__":
    asyncio.run(main())
