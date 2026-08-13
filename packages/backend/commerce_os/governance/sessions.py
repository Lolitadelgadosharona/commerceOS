import hashlib
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.governance.audit import AuditService
from commerce_os.governance.models import AuthSession, User, UserStatus
from commerce_os.shared.models import utc_now


class SessionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def digest(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def issue(
        self, user: User, lifetime: timedelta = timedelta(hours=8)
    ) -> tuple[str, AuthSession]:
        token = secrets.token_urlsafe(48)
        record = AuthSession(
            organization_id=user.organization_id,
            user_id=user.id,
            token_hash=self.digest(token),
            expires_at=utc_now() + lifetime,
        )
        self.session.add(record)
        self._audit(user, "authentication.session_created", "success")
        self.session.commit()
        self.session.refresh(record)
        return token, record

    def verify(self, token: str) -> tuple[User, AuthSession] | None:
        record = self.session.scalar(
            select(AuthSession).where(AuthSession.token_hash == self.digest(token))
        )
        now = utc_now()
        if record is None or record.revoked_at is not None:
            return None
        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=now.tzinfo)
        if expires_at <= now:
            return None
        user = self.session.get(User, record.user_id)
        if (
            user is None
            or user.status != UserStatus.ACTIVE
            or user.organization_id != record.organization_id
        ):
            return None
        record.last_used_at = now
        self.session.commit()
        return user, record

    def revoke(self, user: User, record: AuthSession) -> None:
        if record.revoked_at is None:
            record.revoked_at = utc_now()
        self._audit(user, "authentication.logout", "success")
        self.session.commit()

    def _audit(self, user: User, action: str, result: str) -> None:
        AuditService(self.session).record(
            organization_id=user.organization_id,
            actor_type=str(user.principal_type),
            actor_id=user.id,
            action=action,
            entity_type="auth_session",
            entity_id=user.id,
            metadata={"result": result},
        )
