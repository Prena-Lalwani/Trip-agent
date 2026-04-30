from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.security import hash_password
from app.db.database import get_db
from app.models.user import User
from app.schemas.auth import RegisterRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/admin", tags=["admin"])


def _to_response(u: User) -> UserResponse:
    return UserResponse(
        id=u.id,
        email=u.email,
        role=u.role,
        is_active=u.is_active,
        total_consumed_tokens=u.total_consumed_tokens,
    )


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return [_to_response(u) for u in result.scalars().all()]


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    body: RegisterRequest,
    _: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where(User.email == body.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _to_response(user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdateRequest,
    current_admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email is not None:
        existing = await db.execute(
            select(User).where(User.email == body.email)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = body.email

    if body.password is not None:
        user.hashed_password = hash_password(body.password)

    if body.role is not None:
        if body.role not in ("user", "admin"):
            raise HTTPException(
                status_code=400, detail="Role must be 'user' or 'admin'"
            )
        if int(current_admin["sub"]) == user_id and body.role != "admin":
            raise HTTPException(
                status_code=400, detail="Cannot remove your own admin role"
            )
        user.role = body.role

    if body.is_active is not None:
        if int(current_admin["sub"]) == user_id and not body.is_active:
            raise HTTPException(
                status_code=400, detail="Cannot deactivate your own account"
            )
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    return _to_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_admin: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if int(current_admin["sub"]) == user_id:
        raise HTTPException(
            status_code=400, detail="Cannot delete your own account"
        )

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await db.delete(user)
    await db.commit()