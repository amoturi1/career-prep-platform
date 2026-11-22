"""E4/E5 Opportunities and content.

PB-14 browse jobs/internships, PB-15 event details, PB-16 publish a listing,
PB-17 publish events/announcements, PB-34 update or archive published content.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models import OpportunityKind, PublishStatus, Role, User
from app.schemas import OpportunityCreate, OpportunityOut, OpportunityUpdate, PublishStatusUpdate
from app.services import opportunities

router = APIRouter(prefix="/api/opportunities", tags=["Opportunities"])
admin_only = require_role(Role.admin)
_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, detail="Listing not found.")


@router.get("", response_model=list[OpportunityOut])
def browse(
    kind: OpportunityKind | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Everyone signed in sees published items only; drafts and archived items stay hidden (NFR-14)."""
    return opportunities.list_published(db, kind)


@router.get("/manage", response_model=list[OpportunityOut])
def list_for_admin(user: User = Depends(admin_only), db: Session = Depends(get_db)):
    """Admins see every item, including drafts and archived ones."""
    return opportunities.list_all(db)


@router.get("/{opportunity_id}", response_model=OpportunityOut)
def view(opportunity_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    opportunity = opportunities.get(db, opportunity_id)
    visible = opportunity is not None and (
        opportunity.status == PublishStatus.published or user.role == Role.admin
    )
    if not visible:
        raise _NOT_FOUND
    return opportunity


@router.post("", response_model=OpportunityOut, status_code=status.HTTP_201_CREATED)
def publish(data: OpportunityCreate, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    return opportunities.publish(db, admin, data)


@router.put("/{opportunity_id}", response_model=OpportunityOut)
def edit(
    opportunity_id: int, data: OpportunityUpdate, admin: User = Depends(admin_only), db: Session = Depends(get_db)
):
    opportunity = opportunities.get(db, opportunity_id)
    if opportunity is None:
        raise _NOT_FOUND
    return opportunities.update(db, opportunity, data)


@router.patch("/{opportunity_id}/status", response_model=OpportunityOut)
def change_status(
    opportunity_id: int, data: PublishStatusUpdate, admin: User = Depends(admin_only), db: Session = Depends(get_db)
):
    opportunity = opportunities.get(db, opportunity_id)
    if opportunity is None:
        raise _NOT_FOUND
    return opportunities.set_status(db, opportunity, data.status)
