from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.models.trip import Trip, TripContext, TripInvitation, TripMember
from app.models.user import User
from app.schemas.trip import (
    AddMemberRequest,
    ContextItem,
    MemberInfo,
    TripContextResponse,
    TripCreate,
    TripResponse,
)
from app.services.email_service import send_trip_invitation

router = APIRouter(prefix="/trips", tags=["trips"])


async def _check_membership(
    trip_id: int, user_id: int, db: AsyncSession
) -> None:
    result = await db.execute(
        select(TripMember).where(
            TripMember.trip_id == trip_id,
            TripMember.user_id == user_id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Not a member of this trip"
        )


async def _build_trip_response(trip: Trip, db: AsyncSession) -> TripResponse:
    result = await db.execute(
        select(TripMember, User)
        .join(User, TripMember.user_id == User.id)
        .where(TripMember.trip_id == trip.id)
    )
    members = [
        MemberInfo(user_id=u.id, email=u.email, joined_at=m.joined_at)
        for m, u in result.all()
    ]
    return TripResponse(
        id=trip.id,
        name=trip.name,
        owner_id=trip.owner_id,
        created_at=trip.created_at,
        members=members,
    )


@router.post(
    "", response_model=TripResponse, status_code=status.HTTP_201_CREATED
)
async def create_trip(
    body: TripCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user["sub"])
    trip = Trip(name=body.name, owner_id=user_id)
    db.add(trip)
    await db.flush()
    db.add(TripMember(trip_id=trip.id, user_id=user_id))
    await db.commit()
    await db.refresh(trip)
    return await _build_trip_response(trip, db)


@router.get("", response_model=list[TripResponse])
async def list_trips(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user["sub"])
    result = await db.execute(
        select(Trip)
        .join(TripMember, Trip.id == TripMember.trip_id)
        .where(TripMember.user_id == user_id)
        .order_by(Trip.created_at.desc())
    )
    trips = result.scalars().all()
    return [await _build_trip_response(t, db) for t in trips]


@router.post("/{trip_id}/members", status_code=status.HTTP_201_CREATED)
async def add_member(
    trip_id: int,
    body: AddMemberRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user["sub"])

    trip = await db.get(Trip, trip_id)
    if not trip:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Trip not found")
    if trip.owner_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Only the trip owner can add members"
        )

    inviter_result = await db.execute(select(User).where(User.id == user_id))
    inviter = inviter_result.scalar_one()

    result = await db.execute(select(User).where(User.email == body.email))
    friend = result.scalar_one_or_none()

    if friend:
        existing = await db.execute(
            select(TripMember).where(
                TripMember.trip_id == trip_id,
                TripMember.user_id == friend.id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "User is already a member"
            )
        db.add(TripMember(trip_id=trip_id, user_id=friend.id))
        await db.commit()
        return {"message": f"{friend.email} added to trip"}

    # User not registered — send invitation email
    existing_inv = await db.execute(
        select(TripInvitation).where(
            TripInvitation.trip_id == trip_id,
            TripInvitation.email == body.email,
            TripInvitation.status == "pending",
        )
    )
    if existing_inv.scalar_one_or_none():
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invitation already sent to that email"
        )

    invitation = TripInvitation(trip_id=trip_id, email=body.email)
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    try:
        await send_trip_invitation(
            to_email=body.email,
            trip_name=trip.name,
            inviter_email=inviter.email,
            token=invitation.token,
        )
    except Exception as exc:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            f"Invitation saved but email failed: {exc}",
        )

    return {"message": f"Invitation sent to {body.email}"}


@router.get("/invitations/accept")
async def accept_invitation_link(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handles the link click from the invitation email."""
    result = await db.execute(
        select(TripInvitation).where(TripInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation or invitation.status != "pending":
        return RedirectResponse(
            f"{settings.frontend_url}/login?error=invalid_invitation"
        )

    if invitation.expires_at < datetime.now(timezone.utc):
        return RedirectResponse(
            f"{settings.frontend_url}/login?error=invitation_expired"
        )

    # Check if the invited email is now registered
    user_result = await db.execute(
        select(User).where(User.email == invitation.email)
    )
    user = user_result.scalar_one_or_none()

    if user:
        existing = await db.execute(
            select(TripMember).where(
                TripMember.trip_id == invitation.trip_id,
                TripMember.user_id == user.id,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(TripMember(trip_id=invitation.trip_id, user_id=user.id))

        invitation.status = "accepted"
        await db.commit()
        return RedirectResponse(f"{settings.frontend_url}/?trip_joined=1")

    # Not registered yet — send them to register with the token embedded
    return RedirectResponse(
        f"{settings.frontend_url}/register?invitation={token}"
    )


@router.post("/invitations/{token}/accept", status_code=status.HTTP_200_OK)
async def accept_invitation_after_register(
    token: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Called after registration to complete a pending invitation."""
    user_id = int(current_user["sub"])

    result = await db.execute(
        select(TripInvitation).where(TripInvitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation or invitation.status != "pending":
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invalid or expired invitation"
        )

    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Invitation has expired"
        )

    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    if user.email != invitation.email:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This invitation was sent to a different email address",
        )

    existing = await db.execute(
        select(TripMember).where(
            TripMember.trip_id == invitation.trip_id,
            TripMember.user_id == user_id,
        )
    )
    if not existing.scalar_one_or_none():
        db.add(TripMember(trip_id=invitation.trip_id, user_id=user_id))

    invitation.status = "accepted"
    await db.commit()
    return {"message": "You have joined the trip"}


@router.get("/{trip_id}/context", response_model=TripContextResponse)
async def get_context(
    trip_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = int(current_user["sub"])
    await _check_membership(trip_id, user_id, db)

    result = await db.execute(
        select(TripContext).where(TripContext.trip_id == trip_id)
    )
    items = result.scalars().all()
    return TripContextResponse(
        trip_id=trip_id,
        items=[
            ContextItem(
                key=i.key,
                value=i.value,
                confidence=i.confidence,
                updated_at=i.updated_at,
            )
            for i in items
        ],
    )
