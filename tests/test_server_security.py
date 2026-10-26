# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only

"""Security tests verifying SSRF protection and host boundary enforcement."""

import json
import unittest
import urllib.error
import urllib.request


SERVER_URL = "http://127.0.0.1:3000/api/modem/stats"


class ServerSecurityTests(unittest.TestCase):
    """Test suite ensuring that server-side proxy routes reject forbidden destinations."""

    def _post_stats(self, host: str, simulate: bool = False):
        payload = json.dumps({"host": host, "simulate": simulate}).encode("utf-8")
        req = urllib.request.Request(
            SERVER_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as err:
            return err.code, json.loads(err.read().decode("utf-8"))
        except urllib.error.URLError as err:
            self.skipTest(f"Local dev server not accessible: {err.reason}")

    def test_cloud_metadata_ip_rejected(self):
        """Reject cloud instance metadata service 169.254.169.254."""
        status, body = self._post_stats("169.254.169.254")
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "error")
        self.assertIn("forbidden", body["error"].lower())

    def test_cloud_metadata_hostname_rejected(self):
        """Reject GCP metadata hostname."""
        status, body = self._post_stats("metadata.google.internal")
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "error")
        self.assertIn("forbidden", body["error"].lower())

    def test_loopback_ip_rejected(self):
        """Reject loopback 127.0.0.1."""
        status, body = self._post_stats("127.0.0.1")
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "error")
        self.assertIn("forbidden", body["error"].lower())

    def test_loopback_name_rejected(self):
        """Reject localhost."""
        status, body = self._post_stats("localhost")
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "error")
        self.assertIn("forbidden", body["error"].lower())

    def test_public_ip_rejected(self):
        """Reject public internet IP addresses."""
        status, body = self._post_stats("8.8.8.8")
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "error")
        self.assertIn("rfc1918", body["error"].lower())

    def test_public_domain_rejected(self):
        """Reject public internet domain names."""
        status, body = self._post_stats("example.com")
        self.assertEqual(status, 400)
        self.assertEqual(body["status"], "error")
        self.assertIn("domain names", body["error"].lower())

    def test_simulated_private_ip_accepted(self):
        """Allow private RFC1918 IP addresses in simulation mode."""
        status, body = self._post_stats("192.168.10.2", simulate=True)
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["is_demo"], True)


if __name__ == "__main__":
    unittest.main()
