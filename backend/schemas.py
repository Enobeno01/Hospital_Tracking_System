from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssetCreate(BaseModel):
    asset_id: str
    asset_type: str
   #asset_type: Optional[str] = None


class AssetOut(BaseModel):
    asset_id: str
    asset_type: Optional[str] = None
    current_zone_id: Optional[int] = None
    status: str
    last_seen_at: Optional[datetime] = None
    last_in_return_zone_at: Optional[datetime] = None


class ZoneEventIn(BaseModel):
    asset_id: str
    zone_id: int
    gateway_id: Optional[int] = None
    observed_at: Optional[datetime] = None