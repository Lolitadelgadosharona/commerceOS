from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from commerce_os.shared.database import Base
from commerce_os.shared.models import IdMixin, TimestampMixin, VersionMixin


class VentureOpportunity(IdMixin, TimestampMixin, VersionMixin, Base):
    __tablename__ = "venture_opportunities"

    organization_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id"), nullable=False, index=True
    )
    project_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("projects.id"))
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    thesis: Mapped[str | None] = mapped_column(Text)
    stage: Mapped[str] = mapped_column(String(30), default="observed", nullable=False)
