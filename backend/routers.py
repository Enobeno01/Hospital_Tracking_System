from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime

from database.connection import get_session
from backend.models import Zone, Gateway, Asset, ZoneEvent
#from backend.schemas import ZoneEventIn
from backend.models import Zone, Asset
from datetime import datetime, timedelta
from backend.schemas import ZoneEventIn, AssetCreate 



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
        asset.loan_start_at = None

    else:
        asset.status = "LOANED"

        if asset.loan_start_at is None:
            asset.loan_start_at = observed_time

    session.add(asset)
    session.commit()

    return {"message": "Zone event stored"}


# -----------------------------
# GET ALL ASSETS
# -----------------------------

@router.get("/assets")
def get_assets(session: Session = Depends(get_session)):
    assets = session.exec(select(Asset)).all()
    zones = session.exec(select(Zone)).all()

    zone_map = {zone.zone_id: zone.zone_name for zone in zones}

    result = []

    for asset in assets:
        result.append({
            "asset_id": asset.asset_id,
            "asset_type": asset.asset_type,
            "status": asset.status,
            "current_zone_id": asset.current_zone_id,
            "current_zone_name": zone_map.get(asset.current_zone_id, "Unknown"),
            "last_seen_at": asset.last_seen_at.isoformat() if asset.last_seen_at else None,
            "last_in_return_zone_at": asset.last_in_return_zone_at.isoformat() if asset.last_in_return_zone_at else None,
            "loan_start_at": asset.loan_start_at.isoformat() if asset.loan_start_at else None,

        })

    return result

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


# -----------------------------
# GET dashboard
# -----------------------------

@router.get("/dashboard")
def get_dashboard(session: Session = Depends(get_session)):
    assets = session.exec(select(Asset)).all()
    zones = session.exec(select(Zone)).all()

    zone_map = {zone.zone_id: zone.zone_name for zone in zones}

    available = []
    loaned = []
    not_returned = []
    prioritized = []
    unknown = []

    now = datetime.utcnow()
    priority_limit = 5  # minuter

    for asset in assets:
        status = (asset.status or "UNKNOWN").upper().strip()

        minutes_since_seen = None
        if asset.last_seen_at:
            minutes_since_seen = int((now - asset.last_seen_at).total_seconds() // 60)

        loan_duration_minutes = None
        if asset.loan_start_at:
            loan_duration_minutes = int((now - asset.loan_start_at).total_seconds() // 60)

        asset_data = {
            "asset_id": asset.asset_id,
            "asset_type": asset.asset_type,
            "status": status,
            "current_zone_id": asset.current_zone_id,
            "current_zone_name": zone_map.get(asset.current_zone_id, "Unknown"),
            "last_seen_at": asset.last_seen_at.isoformat() if asset.last_seen_at else None,
            "last_in_return_zone_at": asset.last_in_return_zone_at.isoformat() if asset.last_in_return_zone_at else None,
            "loan_start_at": asset.loan_start_at.isoformat() if asset.loan_start_at else None,
            "minutes_since_seen": minutes_since_seen,
            "loan_duration_minutes": loan_duration_minutes,
        }

        if status == "AVAILABLE":
            available.append(asset_data)

        elif status == "LOANED":
            loaned.append(asset_data)
            not_returned.append(asset_data)

            if loan_duration_minutes is not None and loan_duration_minutes >= priority_limit:
                prioritized.append(asset_data)

        else:
            unknown.append(asset_data)

    return {
        "summary": {
            "available_count": len(available),
            "loaned_count": len(loaned),
            "not_returned_count": len(not_returned),
            "prioritized_count": len(prioritized),
            "unknown_count": len(unknown),
        },
        "available": available,
        "loaned": loaned,
        "not_returned": not_returned,
        "prioritized": prioritized,
        "unknown": unknown,
    }

# -----------------------------
# Post Assets Loan
# -----------------------------
@router.post("/assets/{asset_id}/loan")
def loan_asset(asset_id: str, session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    current_status = (asset.status or "UNKNOWN").upper().strip()

    if current_status == "LOANED":
        raise HTTPException(
            status_code=400,
            detail=f"Asset {asset_id} is already loaned"
        )

    now = datetime.utcnow()

    asset.status = "LOANED"
    asset.loan_start_at = now
    asset.last_seen_at = now

    session.add(asset)
    session.commit()
    session.refresh(asset)

    return {
        "message": f"{asset_id} loan registered",
        "asset_id": asset.asset_id,
        "status": asset.status,
    }

# -----------------------------
# Post Assets Return
# -----------------------------

@router.post("/assets/{asset_id}/return")
def return_asset(asset_id: str, session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    current_status = (asset.status or "UNKNOWN").upper().strip()

    if current_status != "LOANED":
        raise HTTPException(
            status_code=400,
            detail=f"Asset {asset_id} is not currently loaned"
        )

    return_zone = session.exec(
        select(Zone).where(Zone.is_return_zone == True)
    ).first()

    if not return_zone:
        raise HTTPException(status_code=404, detail="Return zone not found")

    now = datetime.utcnow()

    asset.status = "AVAILABLE"
    asset.current_zone_id = return_zone.zone_id
    asset.last_in_return_zone_at = now
    asset.last_seen_at = now
    asset.loan_start_at = None

    session.add(asset)
    session.commit()
    session.refresh(asset)

    return {
        "message": f"{asset_id} return registered",
        "asset_id": asset.asset_id,
        "status": asset.status,
    }


# -----------------------------
# create test asset
# -----------------------------
@router.post("/create-test-assets")
def create_test_assets(session: Session = Depends(get_session)):

    assets = [
        Asset(asset_id="W001", asset_type="Wheelchair"),
        Asset(asset_id="W002", asset_type="Wheelchair"),
        Asset(asset_id="W003", asset_type="Wheelchair"),
        Asset(asset_id="B001", asset_type="Bed"),
        Asset(asset_id="B002", asset_type="Bed"),
        Asset(asset_id="B003", asset_type="Bed"),
    ]

    for asset in assets:
        existing = session.get(Asset, asset.asset_id)
        if not existing:
            session.add(asset)

    session.commit()

    return {"message": "Test assets created"}


# -----------------------------
# # post new item (create asset)
# -----------------------------
@router.post("/assets")
def create_asset(asset: AssetCreate, session: Session = Depends(get_session)):
    existing = session.get(Asset, asset.asset_id)

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Asset {asset.asset_id} already exists"
        )

    new_asset = Asset(
        asset_id=asset.asset_id,
        asset_type=asset.asset_type,
        beacon_id=asset.beacon_id,
        status="UNKNOWN"
    )

    session.add(new_asset)
    session.commit()
    session.refresh(new_asset)

    return new_asset

# -----------------------------
# post new zone
# -----------------------------
@router.post("/zones")
def create_zone(zone_name: str, is_return_zone: bool = False, session: Session = Depends(get_session)):
    
    zone = Zone(
        zone_name=zone_name,
        is_return_zone=is_return_zone
    )

    session.add(zone)
    session.commit()
    session.refresh(zone)

    return zone

# -----------------------------
#  delete zone
# -----------------------------
@router.delete("/zones/{zone_id}")
def delete_zone(zone_id: int, session: Session = Depends(get_session)):

    zone = session.get(Zone, zone_id)

    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    assets = session.exec(
        select(Asset).where(Asset.current_zone_id == zone_id)
    ).all()

    if assets:
        raise HTTPException(
            status_code=400,
            detail="Zone cannot be deleted because assets are using it"
        )

    session.delete(zone)
    session.commit()

    return {"message": f"Zone {zone_id} deleted"}


# -----------------------------
#  tracking statistic
#an endpoint that counts how many times an asset has been registered in each zone.
# -----------------------------
@router.get("/assets/{asset_id}/zone-stats")
def get_asset_zone_stats(asset_id: str, session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    events = session.exec(
        select(ZoneEvent).where(ZoneEvent.asset_id == asset_id)
    ).all()

    zones = session.exec(select(Zone)).all()
    zone_map = {zone.zone_id: zone.zone_name for zone in zones}

    stats = {}

    for event in events:
        zone_name = zone_map.get(event.zone_id, f"Zone {event.zone_id}")

        if zone_name not in stats:
            stats[zone_name] = 0

        stats[zone_name] += 1

    result = []
    for zone_name, count in stats.items():
        result.append({
            "zone_name": zone_name,
            "visits": count
        })

    result.sort(key=lambda x: x["visits"], reverse=True)

    return {
        "asset_id": asset_id,
        "most_used_zones": result
    }

# -----------------------------
#   statistic of which zones are used the most overall
# -----------------------------
@router.get("/zones/stats")
def get_zone_stats(session: Session = Depends(get_session)):
    events = session.exec(select(ZoneEvent)).all()
    zones = session.exec(select(Zone)).all()

    zone_map = {zone.zone_id: zone.zone_name for zone in zones}
    stats = {}

    for event in events:
        zone_name = zone_map.get(event.zone_id, f"Zone {event.zone_id}")

        if zone_name not in stats:
            stats[zone_name] = 0

        stats[zone_name] += 1

    result = []
    for zone_name, count in stats.items():
        result.append({
            "zone_name": zone_name,
            "visits": count
        })

    result.sort(key=lambda x: x["visits"], reverse=True)

    return result

# -----------------------------
# DELETE ASSET
# -----------------------------
@router.delete("/assets/{asset_id}")
def delete_asset(asset_id: str, session: Session = Depends(get_session)):
    asset = session.get(Asset, asset_id)

    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    session.delete(asset)
    session.commit()

    return {"message": f"{asset_id} deleted"}