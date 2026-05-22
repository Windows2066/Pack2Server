from collections.abc import Callable
from typing import TypeVar

from redis import Redis
from rq import Queue

from app.core.config import get_settings

T = TypeVar("T")


def get_queue() -> Queue:
    return Queue("default", connection=Redis.from_url(get_settings().redis_url))


def enqueue_or_run_job(func: Callable[..., T], *args: object) -> T | object:
    if get_settings().run_jobs_inline:
        return func(*args)
    return get_queue().enqueue(func, *args)
