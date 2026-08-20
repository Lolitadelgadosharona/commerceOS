"""Minimal worker readiness process; business event delivery is intentionally absent."""

from __future__ import annotations

import logging
import signal
import time
from uuid import UUID

from commerce_os.ai_runtime.adapters import ProviderAdapter
from commerce_os.ai_runtime.execution import AIExecutionService
from commerce_os.ai_runtime.models import AIRequest
from commerce_os.shared.config import get_settings
from redis import Redis
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
running = True
WORKER_PRINCIPAL = "commerce-os-worker"


def execute_ai_request(
    session: Session,
    *,
    request_id: UUID,
    organization_id: UUID,
    service_actor_id: UUID,
    adapters: dict[str, ProviderAdapter] | None = None,
) -> AIRequest:
    """Controlled worker composition path; the service identity has no approval authority."""
    service = AIExecutionService(session, adapters)
    return service.execute(
        service.scoped_request(request_id, organization_id), worker_actor_id=service_actor_id
    )


def stop_worker(_signum: int, _frame: object) -> None:
    global running
    running = False


def main() -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    client.ping()
    logger.info(
        "Commerce OS worker ready; external delivery disabled; principal=%s",
        WORKER_PRINCIPAL,
    )
    signal.signal(signal.SIGTERM, stop_worker)
    signal.signal(signal.SIGINT, stop_worker)
    while running:
        time.sleep(1)


if __name__ == "__main__":
    main()
