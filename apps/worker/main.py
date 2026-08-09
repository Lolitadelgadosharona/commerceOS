"""Minimal worker readiness process; business event delivery is intentionally absent."""

from __future__ import annotations

import logging
import signal
import time

from commerce_os.shared.config import get_settings
from redis import Redis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
running = True


def stop_worker(_signum: int, _frame: object) -> None:
    global running
    running = False


def main() -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    client.ping()
    logger.info("Commerce OS worker ready; external delivery disabled")
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    while running:
        time.sleep(1)


if __name__ == "__main__":
    main()
