# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

import ipaddress
import tempfile
import unittest
from pathlib import Path

from zte_h186_stats import RouterError, find_secret, modem_url_from_ip


class SecretConfigTests(unittest.TestCase):
    def test_ipv4_secret_builds_http_url(self):
        address = ".".join(str(part) for part in (10, 24, 8, 3))
        self.assertEqual(modem_url_from_ip(address.encode()), f"http://{address}")

    def test_ipv6_secret_is_bracketed(self):
        address = ipaddress.ip_address(bytes.fromhex("20010db8000000000000000000000001"))
        self.assertEqual(
            modem_url_from_ip(address.compressed.encode()), f"http://[{address}]"
        )

    def test_invalid_address_is_rejected(self):
        with self.assertRaises(RouterError):
            modem_url_from_ip(b"not-an-ip-address")

    def test_latest_matching_secret_is_selected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            secrets_dir = Path(temp_dir)
            older = secrets_dir / "zte-ipaddress-20260101T000000Z.age"
            newer = secrets_dir / "zte-ipaddress-20260102T000000Z.age"
            older.touch()
            newer.touch()
            self.assertEqual(find_secret(secrets_dir, "zte-ipaddress-*.age"), newer)

    def test_missing_secret_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(RouterError, "secrets/zte-ipaddress"):
                find_secret(Path(temp_dir), "zte-ipaddress-*.age")


if __name__ == "__main__":
    unittest.main()