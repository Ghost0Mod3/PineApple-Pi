from backend.services.scanner import parse_nmcli


def test_parse_nmcli():
    text = (
        r"60\:F4\:19\:FA\:10\:66:Abraham_blinkin:6:2437:100:WPA2" + "\n"
        r"7C\:67\:AB\:76\:28\:2D:Roku82149393:40:5200:89:WPA2" + "\n"
    )
    items = parse_nmcli(text)
    assert len(items) == 2
    assert items[0]["bssid"] == "60:f4:19:fa:10:66"
    assert items[1]["frequency_mhz"] == 5200
