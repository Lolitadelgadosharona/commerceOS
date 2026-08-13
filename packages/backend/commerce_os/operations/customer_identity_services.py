from sqlalchemy.orm import Session

from commerce_os.operations.customer_identity_models import CustomerIdentityLink
from commerce_os.operations.customer_identity_schemas import IdentityLinkCreate
from commerce_os.operations.errors import OperationsError
from commerce_os.shared.scope import reference_belongs_to_organization


class CustomerIdentityLinkService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: IdentityLinkCreate) -> CustomerIdentityLink:
        if not reference_belongs_to_organization(
            self.session,
            table_name="customers",
            reference_id=payload.customer_id,
            organization_id=payload.organization_id,
        ):
            raise OperationsError("Customer was not found in this organization.", "not_found")
        entity = CustomerIdentityLink(**payload.model_dump())
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
