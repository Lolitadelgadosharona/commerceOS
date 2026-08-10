from sqlalchemy import select
from sqlalchemy.orm import Session

from commerce_os.decision.cfo_models import CFOInsight
from commerce_os.decision.cfo_schemas import CFOInsightCreate
from commerce_os.decision.errors import DecisionScopeError
from commerce_os.shared.database import Base


class CFOInsightService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, payload: CFOInsightCreate) -> CFOInsight:
        table = Base.metadata.tables["organizations"]
        organization = self.session.execute(
            select(table.c.id).where(table.c.id == payload.organization_id)
        ).scalar_one_or_none()
        if organization is None:
            raise DecisionScopeError("Organization was not found.")
        insight = CFOInsight(**payload.model_dump())
        self.session.add(insight)
        self.session.commit()
        self.session.refresh(insight)
        return insight
