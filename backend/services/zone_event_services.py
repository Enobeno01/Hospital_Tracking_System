from datetime import datetime

from sqlmodel import Session

from backend.models import Asset, Zone, ZoneEvent
from backend.schemas import ZoneEventIn


class ZoneEventService:

    @staticmethod
    def handle_zone_event(session: Session, event_data: ZoneEventIn):

        observed_time = event_data.observed_at or datetime.utcnow()

        asset = session.get(Asset, event_data.asset_id)
        if not asset:
            raise ValueError("Asset not found")

        zone = session.get(Zone, event_data.zone_id)
        if not zone:
            raise ValueError("Zone not found")

        zone_event = ZoneEvent(
            asset_id=event_data.asset_id,
            zone_id=event_data.zone_id,
            gateway_id=event_data.gateway_id,
            observed_at=observed_time
        )

        session.add(zone_event)

        # Update asset
        asset.current_zone_id = event_data.zone_id
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
        session.refresh(asset)

        return asset