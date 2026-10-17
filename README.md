# PineApple-Pi v0.6.4 AP Activity Prototype

Adds a liability acknowledgement, administrator login, yellow-tool GUI catalog, reviewed download plans, authorization projects, and read-only adapter/AP settings.

The disclaimer does not replace scope enforcement. Browser-based package installation and unrestricted execution are intentionally not enabled.

```bash
cp .env.example .env
./scripts/deploy-dev.sh
```

## Open-AP Settings controls

Settings now contains validated controls for creating, starting, and stopping an open `wlan2` access point. Real changes remain off until `ENABLE_AP_CHANGES=true` is set. The backend locks actions to `wlan2`, approved channels, `10.42.0.1/24`, open security, and explicit `OPEN NETWORK` confirmation.

## AP activity log
Shows wlan2 client IP, MAC, optional DHCP hostname, first/last seen, state, and connect/disconnect history.


## Channel 6

The wlan2 AP Settings default remains 2.4 GHz channel 6. MeshCore integration has been removed from this build.
