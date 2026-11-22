"""Jobs, internships, events and announcements (PB-14 to PB-17, PB-34)."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Opportunity, OpportunityKind, PublishStatus, User
from app.schemas import OpportunityCreate, OpportunityUpdate


def list_published(db: Session, kind: OpportunityKind | None = None) -> list[Opportunity]:
    query = select(Opportunity).where(Opportunity.status == PublishStatus.published)
    if kind is not None:
        query = query.where(Opportunity.kind == kind)
    return list(db.scalars(query.order_by(Opportunity.created_at.desc(), Opportunity.id.desc())))


def list_all(db: Session) -> list[Opportunity]:
    return list(db.scalars(select(Opportunity).order_by(Opportunity.created_at.desc(), Opportunity.id.desc())))


def get(db: Session, opportunity_id: int) -> Opportunity | None:
    return db.get(Opportunity, opportunity_id)


def publish(db: Session, admin: User, data: OpportunityCreate) -> Opportunity:
    opportunity = Opportunity(created_by=admin.id, **data.model_dump())
    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)
    return opportunity


def update(db: Session, opportunity: Opportunity, data: OpportunityUpdate) -> Opportunity:
    for field, value in data.model_dump().items():
        setattr(opportunity, field, value)
    db.commit()
    db.refresh(opportunity)
    return opportunity


def set_status(db: Session, opportunity: Opportunity, status: PublishStatus) -> Opportunity:
    opportunity.status = status
    db.commit()
    db.refresh(opportunity)
    return opportunity
