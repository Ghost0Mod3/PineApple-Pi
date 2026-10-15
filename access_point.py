from pydantic import BaseModel
class AccessPoint(BaseModel):
    ssid: str | None = None
    bssid: str
    channel: int | None = None
    frequency_mhz: int | None = None
    signal_percent: int | None = None
    security: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None
    sightings: int = 1
