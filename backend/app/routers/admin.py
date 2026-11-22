"""E10 Administration: PB-30 manage accounts and roles, PB-36 platform analytics."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_role
from app.models import Role, User
from app.schemas import UserAdminOut, UserAdminUpdate
from app.services import admin as svc

router = APIRouter(prefix="/api/admin", tags=["Administration"])
admin_only = require_role(Role.admin)


@router.get("/users", response_model=list[UserAdminOut])
def list_users(
    role: Role | None = None, search: str = "", user: User = Depends(admin_only), db: Session = Depends(get_db)
):
    return svc.list_users(db, role, search.strip())


@router.patch("/users/{user_id}", response_model=UserAdminOut)
def update_user(user_id: int, data: UserAdminUpdate, admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    try:
        return svc.update_user(db, admin, user_id, data)
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found.")
    except svc.AdminError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/analytics")
def analytics(admin: User = Depends(admin_only), db: Session = Depends(get_db)):
    return svc.analytics(db)
