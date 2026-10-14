from pydantic import BaseModel
class Radio(BaseModel):
    interface: str
    role: str
    state: str
    driver: str | None = None
    mac_address: str | None = None
    ip_address: str | None = None
    connection: str | None = None
    identity_ok: bool = True
