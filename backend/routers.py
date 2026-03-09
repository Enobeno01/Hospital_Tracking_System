from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from database.connection import get_session
from backend.models import Zone, Gateway, Asset, ZoneEvent
from backend.schemas import ZoneEventIn


router = APIRouter()


# -----------------------------
# ROOT
# -----------------------------

@router.get("/")
def root():
    return {"message": "Hospital Tracking Backend Running"}


# -----------------------------
# CREATE ZONE EVENT
# -----------------------------

@router.post("/zone-events")
def create_zone_event(event: ZoneEventIn, session: Session = Depends(get_session)):

    asset = session.get(Asset, event.asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    zone = session.get(Zone, event.zone_id)

    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    observed_time = event.observed_at or datetime.utcnow()

    zone_event = ZoneEvent(
        asset_id=event.asset_id,
        zone_id=event.zone_id,
        gateway_id=event.gateway_id,
        observed_at=observed_time
    )

    session.add(zone_event)

    # Update asset
    asset.current_zone_id = event.zone_id
    asset.last_seen_at = observed_time

    if zone.is_return_zone:
        asset.status = "AVAILABLE"
        asset.last_in_return_zone_at = observed_time
    else:
        asset.status = "LOANED"

    session.add(asset)
    session.commit()

    return {"message": "Zone event stored"}


# -----------------------------
# GET ALL ASSETS
# -----------------------------

@router.get("/assets")
def get_assets(session: Session = Depends(get_session)):

    statement = select(Asset)
    assets = session.exec(statement).all()

    return assets


# -----------------------------
# GET ASSET HISTORY
# -----------------------------

@router.get("/assets/{asset_id}/history")
def get_asset_history(asset_id: str, session: Session = Depends(get_session)):

    statement = select(ZoneEvent).where(ZoneEvent.asset_id == asset_id)
    events = session.exec(statement).all()

    return events


# -----------------------------
# GET ALL ZONES
# -----------------------------

@router.get("/zones")
def get_zones(session: Session = Depends(get_session)):

    statement = select(Zone)
    zones = session.exec(statement).all()

    return zones


# -----------------------------
# GET OVERDUE / NOT RETURNED
# -----------------------------

@router.get("/assets/not-returned")
def get_not_returned(session: Session = Depends(get_session)):

    statement = select(Asset).where(Asset.status == "LOANED")
    assets = session.exec(statement).all()

    return assets