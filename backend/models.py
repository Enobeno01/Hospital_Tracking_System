from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


# =========================
# ZONES
# =========================

class Zone(SQLModel, table=True):
    __tablename__ = "zones"

    zone_id: Optional[int] = Field(default=None, primary_key=True)
    zone_name: str
    is_return_zone: bool = False


# =========================
# GATEWAYS
# =========================

class Gateway(SQLModel, table=True):
    __tablename__ = "gateways"

    gateway_id: Optional[int] = Field(default=None, primary_key=True)
    gateway_name: str
    zone_id: Optional[int] = Field(default=None, foreign_key="zones.zone_id")


# =========================
# ASSETS
# =========================

class Asset(SQLModel, table=True):
    __tablename__ = "assets"

    asset_id: str = Field(primary_key=True, max_length=50)
    asset_type: Optional[str] = Field(default=None, max_length=50)

    current_zone_id: Optional[int] = Field(default=None, foreign_key="zones.zone_id")

    status: str = Field(default="UNKNOWN", max_length=20)

    last_seen_at: Optional[datetime] = None
    last_in_return_zone_at: Optional[datetime] = None


# =========================
# ZONE EVENTS
# =========================

class ZoneEvent(SQLModel, table=True):
    __tablename__ = "zone_events"

    event_id: Optional[int] = Field(default=None, primary_key=True)

    asset_id: str = Field(foreign_key="assets.asset_id", max_length=50)
    zone_id: int = Field(foreign_key="zones.zone_id")

    gateway_id: Optional[int] = Field(default=None, foreign_key="gateways.gateway_id")

    observed_at: datetime = Field(default_factory=datetime.utcnow)