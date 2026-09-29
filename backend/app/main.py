from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.database import engine, get_db
from app.core.logging import configure_logging
from app.models import AlertRule, Listing, User
from app.schemas.alert import AlertRuleCreate, AlertRuleOut
from app.schemas.auth import TokenPair, UserLogin, UserOut, UserRegister
from app.schemas.listing import ListingOut
from app.utils.security import create_access_token, decode_token, hash_password, verify_password
from app.websocket.manager import ws_manager


configure_logging()
app = FastAPI(title=settings.APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    await db.execute(select(1))
    return {"status": "ok"}


@app.post("/api/auth/register", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    duplicate = await db.scalar(
        select(User.id).where(or_(User.email == data.email, User.username == data.username)).limit(1)
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists")

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email or username already exists") from exc
    return {
        "access_token": create_access_token(str(user.id)),
        "user": UserOut.model_validate(user),
    }


@app.post("/api/auth/login", response_model=TokenPair)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.email == data.email))
    if user is None or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return {
        "access_token": create_access_token(str(user.id)),
        "user": UserOut.model_validate(user),
    }


@app.get("/api/listings", response_model=list[ListingOut])
async def list_listings(
    q: str | None = None,
    max_price: float | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(Listing).where(Listing.is_active.is_(True))
    if q:
        query = query.where(or_(Listing.title.ilike(f"%{q}%"), Listing.description.ilike(f"%{q}%")))
    if max_price is not None:
        query = query.where(Listing.price <= max_price)
    result = await db.execute(query.order_by(Listing.last_seen_at.desc()).limit(limit))
    return result.scalars().all()


@app.get("/api/listings/stats/summary")
async def listing_stats(db: AsyncSession = Depends(get_db)):
    total, active, average = (await db.execute(
        select(
            func.count(Listing.id),
            func.count(Listing.id).filter(Listing.is_active.is_(True)),
            func.avg(Listing.price),
        )
    )).one()
    return {"total": total, "active": active, "avg_price": average}


@app.get("/api/alerts", response_model=list[AlertRuleOut])
async def list_alerts(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AlertRule).where(AlertRule.user_id == user.id).order_by(AlertRule.created_at.desc())
    )
    return result.scalars().all()


@app.post("/api/alerts", response_model=AlertRuleOut, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertRuleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = AlertRule(user_id=user.id, **data.model_dump())
    db.add(rule)
    await db.flush()
    return rule


@app.delete("/api/alerts/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    rule_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rule = await db.scalar(
        select(AlertRule).where(AlertRule.id == rule_id, AlertRule.user_id == user.id)
    )
    if rule is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    await db.delete(rule)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    payload = decode_token(token)
    try:
        user_id = UUID(payload["sub"]) if payload and payload.get("sub") else None
    except (KeyError, ValueError):
        user_id = None
    if user_id is None:
        await websocket.close(code=4401)
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id, websocket)


@app.on_event("shutdown")
async def close_database_connection():
    await engine.dispose()