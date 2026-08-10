from sqlalchemy.orm import Session

from commerce_os.governance.models import CustomerIdentity
from commerce_os.governance.schemas import CustomerIdentityCreate


class CustomerIdentityService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def observe(self, payload: CustomerIdentityCreate) -> CustomerIdentity:
        identity = CustomerIdentity(
            organization_id=payload.organization_id,
            customer_id=payload.customer_id,
            provider=payload.provider,
            external_identifier=payload.external_identifier,
            confidence_score=payload.confidence_score,
            verification_status=payload.verification_status,
            provenance=payload.provenance,
            identity_type=payload.provider,
            normalized_value=payload.external_identifier,
            source=payload.provider,
            confidence=payload.confidence_score,
            link_status=payload.verification_status,
        )
        self.session.add(identity)
        self.session.commit()
        self.session.refresh(identity)
        return identity
