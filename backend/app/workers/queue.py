from redis import Redis
from rq import Queue

from app.core.config import get_settings


def get_queue() -> Queue:
    return Queue("default", connection=Redis.from_url(get_settings().redis_url))
