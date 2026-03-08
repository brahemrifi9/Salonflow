from fastapi import APIRouter, Depends
from app.core.deps import require_admin
from app import models

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/me")
def admin_me(current_user: models.User = Depends(require_admin)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
    }