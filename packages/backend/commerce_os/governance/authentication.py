from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.governance.audit import AuditService
from commerce_os.governance.errors import NotFoundError
from commerce_os.governance.models import PasswordCredential, PrincipalType, User, UserStatus
from commerce_os.governance.passwords import Argon2PasswordHasher, PasswordHasher


class AuthenticationService:
    def __init__(self, session: Session, password_hasher: PasswordHasher | None = None) -> None:
        self.session = session
        self.password_hasher = password_hasher or Argon2PasswordHasher()

    def create_user(
        self,
        *,
        organization_id: UUID,
        email: str,
        display_name: str,
        password: str,
        principal_type: PrincipalType = PrincipalType.HUMAN,
        actor_id: UUID | None = None,
    ) -> User:
        normalized_email = email.strip().lower()
        user = User(
            organization_id=organization_id,
            email=normalized_email,
            display_name=display_name.strip(),
            status=UserStatus.ACTIVE,
            principal_type=principal_type,
        )
        self.session.add(user)
        self.session.flush()
        credential = PasswordCredential(
            user_id=user.id,
            password_hash=self.password_hasher.hash(password),
            algorithm=self.password_hasher.algorithm,
        )
        self.session.add(credential)
        AuditService(self.session).record(
            organization_id=organization_id,
            actor_type="human" if actor_id else "system",
            actor_id=actor_id,
            action="user.created",
            entity_type="user",
            entity_id=user.id,
            metadata={"principal_type": principal_type.value},
        )
        self.session.commit()
        self.session.refresh(user)
        return user

    def set_password(self, *, user_id: UUID, password: str, actor_id: UUID) -> None:
        user = self.session.get(User, user_id)
        if user is None:
            raise NotFoundError("User was not found.")
        credential = self.session.scalar(
            select(PasswordCredential).where(PasswordCredential.user_id == user_id)
        )
        if credential is None:
            credential = PasswordCredential(
                user_id=user_id,
                password_hash=self.password_hasher.hash(password),
                algorithm=self.password_hasher.algorithm,
            )
            self.session.add(credential)
        else:
            credential.password_hash = self.password_hasher.hash(password)
            credential.algorithm = self.password_hasher.algorithm
        AuditService(self.session).record(
            organization_id=user.organization_id,
            actor_type="human",
            actor_id=actor_id,
            action="credential.password_changed",
            entity_type="user",
            entity_id=user.id,
        )
        self.session.commit()

    def authenticate_password(
        self, *, organization_id: UUID, email: str, password: str
    ) -> User | None:
        user = self.session.scalar(
            select(User).where(
                User.organization_id == organization_id,
                User.email == email.strip().lower(),
            )
        )
        if user is None or user.status != UserStatus.ACTIVE:
            return None
        credential = self.session.scalar(
            select(PasswordCredential).where(PasswordCredential.user_id == user.id)
        )
        if credential is None or not self.password_hasher.verify(
            password, credential.password_hash
        ):
            AuditService(self.session).record(
                organization_id=organization_id,
                actor_type=str(user.principal_type),
                actor_id=user.id,
                action="authentication.failed",
                entity_type="user",
                entity_id=user.id,
            )
            self.session.commit()
            return None
        AuditService(self.session).record(
            organization_id=organization_id,
            actor_type=str(user.principal_type),
            actor_id=user.id,
            action="authentication.succeeded",
            entity_type="user",
            entity_id=user.id,
        )
        self.session.commit()
        return user
