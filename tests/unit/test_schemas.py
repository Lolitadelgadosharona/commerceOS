from uuid import uuid4

import pytest
from commerce_os.governance.schemas import CustomerIdentityCreate, OrganizationCreate
from commerce_os.operations.schemas import SalesOpportunityCreate
from pydantic import ValidationError


def test_organization_slug_requires_lowercase_kebab_case() -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(name="Example", slug="Not Valid")


def test_identity_confidence_is_bounded() -> None:
    with pytest.raises(ValidationError):
        CustomerIdentityCreate(
            organization_id=uuid4(),
            customer_id=uuid4(),
            identity_type="email",
            normalized_value="buyer@example.test",
            source="test",
            confidence=1.1,
        )


def test_sales_opportunity_has_no_generic_opportunity_contract() -> None:
    schema = SalesOpportunityCreate(
        organization_id=uuid4(),
        name="Wholesale agreement",
    )
    assert schema.name == "Wholesale agreement"
    assert "opportunity_type" not in schema.model_dump()
