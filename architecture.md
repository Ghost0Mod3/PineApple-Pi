# Architecture

Pineapple-Pi protects `wlan0` as the management interface and uses the approved Techkey RTL88x2BU on `wlan1` for NetworkManager inventory scans. The scan service refuses to run when the management route is absent or the scanner MAC/driver does not match.
