# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: MIT

"""Comprehensive unit tests for the ZTE H186 Home Assistant API client."""

import asyncio
from dataclasses import is_dataclass
import unittest
from unittest.mock import MagicMock

import aiohttp

from custom_components.zte_h186.api import (
    ZteH186ApiClient,
    ZteH186AuthError,
    ZteH186ConnectionError,
    ZteH186Data,
    ZteH186ProtocolError,
)

SAMPLE_LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>ZTE Login</title></head>
<body>
<script>
var _sessionTmpToken = "\\x61\\x64\\x6d\\x69\\x6e\\x5f\\x74\\x6f\\x6b\\x65\\x6e";
</script>
</body>
</html>
"""

SAMPLE_DSL_XML = """
<ajax_response_xml_root>
    <IF_ERRORSTR>SUCC</IF_ERRORSTR>
    <Instance>
        <ParaName>Status</ParaName>
        <ParaValue>Up</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Module_type</ParaName>
        <ParaValue>VDSL2</ParaValue>
    </Instance>
    <Instance>
        <ParaName>CurrentProfile</ParaName>
        <ParaValue>17a</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_current_rate</ParaName>
        <ParaValue>109200</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_current_rate</ParaName>
        <ParaValue>42800</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_max_rate</ParaName>
        <ParaValue>118500</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_max_rate</ParaName>
        <ParaValue>46100</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_noise_margin</ParaName>
        <ParaValue>114</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_noise_margin</ParaName>
        <ParaValue>121</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_attenuation</ParaName>
        <ParaValue>142</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_attenuation</ParaName>
        <ParaValue>180</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Downstream_power</ParaName>
        <ParaValue>145</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Upstream_power</ParaName>
        <ParaValue>72</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Data_path</ParaName>
        <ParaValue>Interleaved</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownInterleavedepth</ParaName>
        <ParaValue>8</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpInterleaveDepth</ParaName>
        <ParaValue>1</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownInterleaveDelay</ParaName>
        <ParaValue>4</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpInterleaveDelay</ParaName>
        <ParaValue>0</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownstreamInp</ParaName>
        <ParaValue>20</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpstreamInp</ParaName>
        <ParaValue>0</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Showtime_start</ParaName>
        <ParaValue>345600</ParaValue>
    </Instance>
    <Instance>
        <ParaName>tLinkEncapsulationUsed</ParaName>
        <ParaValue>PTM</ParaValue>
    </Instance>
    <Instance>
        <ParaName>DownCrc_errors</ParaName>
        <ParaValue>3</ParaValue>
    </Instance>
    <Instance>
        <ParaName>UpCrc_errors</ParaName>
        <ParaValue>0</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Fec_errors</ParaName>
        <ParaValue>1240</ParaValue>
    </Instance>
    <Instance>
        <ParaName>Atuc_fec_errors</ParaName>
        <ParaValue>185</ParaValue>
    </Instance>
</ajax_response_xml_root>
"""


class TestZteH186ApiClient(unittest.TestCase):
    """Test suite for ZTE H186 API client functions and edge cases."""

    def test_base_url_formatting(self):
        """Test formatting of IPv4, IPv6, and standard scheme URLs."""
        client_v4 = ZteH186ApiClient("192.168.10.2")
        self.assertEqual(client_v4._base_url, "http://192.168.10.2")

        client_v6 = ZteH186ApiClient("2001:db8::1")
        self.assertEqual(client_v6._base_url, "http://[2001:db8::1]")

        client_scheme = ZteH186ApiClient("http://192.168.1.1/")
        self.assertEqual(client_scheme._base_url, "http://192.168.1.1")

        client_https = ZteH186ApiClient("https://modem.local")
        self.assertEqual(client_https._base_url, "https://modem.local")

    def test_decode_session_token_hex(self):
        """Test decoding hex-escaped session token."""
        decoded = ZteH186ApiClient._decode_session_token(SAMPLE_LOGIN_HTML)
        self.assertEqual(decoded, "admin_token")

    def test_decode_session_token_fallback(self):
        """Test decoding plain session token."""
        html = '<script>var _sessionTmpToken = "plain_token_abc";</script>'
        decoded = ZteH186ApiClient._decode_session_token(html)
        self.assertEqual(decoded, "plain_token_abc")

    def test_decode_session_token_missing(self):
        """Test error raised when session token is missing."""
        with self.assertRaises(ZteH186ProtocolError):
            ZteH186ApiClient._decode_session_token("<html><body>No token here</body></html>")

    def test_extract_xml_values(self):
        """Test XML parsing of router name-value pairs."""
        values = ZteH186ApiClient._extract_xml_values(SAMPLE_DSL_XML)
        self.assertEqual(values["IF_ERRORSTR"], "SUCC")
        self.assertEqual(values["Status"], "Up")
        self.assertEqual(values["Module_type"], "VDSL2")
        self.assertEqual(values["CurrentProfile"], "17a")
        self.assertEqual(values["Downstream_current_rate"], "109200")
        self.assertEqual(values["DownCrc_errors"], "3")

    def test_extract_xml_missing_root(self):
        """Test error raised when XML root tag is missing."""
        with self.assertRaises(ZteH186ProtocolError):
            ZteH186ApiClient._extract_xml_values("<other_root><foo>bar</foo></other_root>")

    def test_extract_xml_invalid_syntax(self):
        """Test error raised when XML contains broken syntax."""
        with self.assertRaises(ZteH186ProtocolError):
            ZteH186ApiClient._extract_xml_values(
                "<ajax_response_xml_root><unclosed></ajax_response_xml_root>"
            )

    def test_lock_initialization(self):
        """Test that asyncio.Lock is properly initialized to prevent session collisions."""
        client = ZteH186ApiClient("192.168.10.2")
        self.assertIsInstance(client._lock, asyncio.Lock)

    def test_dataclass_structure(self):
        """Verify ZteH186Data dataclass fields and slots."""
        self.assertTrue(is_dataclass(ZteH186Data))
        data = ZteH186Data(
            downstream_sync=109.2,
            upstream_sync=42.8,
            downstream_max=118.5,
            upstream_max=46.1,
            downstream_snr=11.4,
            upstream_snr=12.1,
            downstream_attenuation=14.2,
            upstream_attenuation=18.0,
            profile="17a",
            modulation="VDSL2",
            dsl_status="Up",
        )
        self.assertEqual(data.downstream_sync, 109.2)
        self.assertEqual(data.dsl_status, "Up")


class TestAsyncMockFlow(unittest.IsolatedAsyncioTestCase):
    """Async tests for network and session handshake with mocked aiohttp."""

    async def test_full_successful_handshake(self):
        """Test complete 5-step mock handshake returning populated ZteH186Data."""
        mock_session = MagicMock()

        # Helper context manager for mocked async GET/POST
        class MockResponse:
            def __init__(self, status=200, text_data="", headers=None, cookies=None):
                self.status = status
                self._text = text_data
                self.headers = headers or {}
                self.cookies = cookies or {}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def text(self, *args, **kwargs):
                return self._text

        resp_login_page = MockResponse(200, SAMPLE_LOGIN_HTML)
        resp_token = MockResponse(200, "12345678")
        resp_post = MockResponse(
            200,
            "",
            headers=MagicMock(getall=MagicMock(return_value=["SID=valid_sid_9999; path=/"])),
            cookies={"SID": MagicMock(value="valid_sid_9999")},
        )
        resp_status_page = MockResponse(200, '<html>"internet_dsl_interface_lua.lua"</html>')
        resp_dsl_xml = MockResponse(200, SAMPLE_DSL_XML)

        mock_session.get.side_effect = [
            resp_login_page,
            resp_token,
            resp_status_page,
            resp_dsl_xml,
        ]
        mock_session.post.return_value = resp_post
        mock_session.closed = False

        client = ZteH186ApiClient("192.168.10.2", "admin", "secret", session=mock_session)
        stats = await client.async_get_dsl_stats()

        self.assertEqual(stats.downstream_sync, 109.2)
        self.assertEqual(stats.upstream_sync, 42.8)
        self.assertEqual(stats.profile, "17a")
        self.assertEqual(stats.modulation, "VDSL2")
        self.assertEqual(stats.dsl_status, "Up")
        self.assertEqual(stats.downstream_crc, 3)
        self.assertEqual(stats.upstream_crc, 0)
        self.assertEqual(stats.downstream_fec, 1240)
        self.assertEqual(stats.upstream_fec, 185)
        self.assertEqual(client._sid, "valid_sid_9999")
        self.assertTrue(client._is_authenticated)

    async def test_auth_failure_no_sid(self):
        """Test that missing SID cookie raises ZteH186AuthError."""
        mock_session = MagicMock()

        class MockResponse:
            def __init__(self, status=200, text_data=""):
                self.status = status
                self._text = text_data
                self.headers = MagicMock(getall=MagicMock(return_value=[]))
                self.cookies = {}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def text(self, *args, **kwargs):
                return self._text

        mock_session.get.side_effect = [
            MockResponse(200, SAMPLE_LOGIN_HTML),
            MockResponse(200, "12345678"),
        ]
        mock_session.post.return_value = MockResponse(200, "Wrong password")
        mock_session.cookie_jar.filter_cookies.return_value = {}
        mock_session.closed = False

        client = ZteH186ApiClient("192.168.10.2", "admin", "wrong_pass", session=mock_session)
        with self.assertRaises(ZteH186AuthError):
            await client.async_login()

    async def test_training_mode_graceful_handling(self):
        """Test that missing rate fields when line is training/Down do not crash."""
        training_xml = """
        <ajax_response_xml_root>
            <IF_ERRORSTR>SUCC</IF_ERRORSTR>
            <Instance>
                <ParaName>Status</ParaName>
                <ParaValue>Down</ParaValue>
            </Instance>
        </ajax_response_xml_root>
        """
        mock_session = MagicMock()

        class MockResponse:
            def __init__(self, status=200, text_data=""):
                self.status = status
                self._text = text_data
                self.headers = MagicMock(getall=MagicMock(return_value=["SID=test_sid"]))
                self.cookies = {"SID": MagicMock(value="test_sid")}

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

            async def text(self, *args, **kwargs):
                return self._text

        mock_session.get.side_effect = [
            MockResponse(200, SAMPLE_LOGIN_HTML),
            MockResponse(200, "12345678"),
            MockResponse(200, '<html>"internet_dsl_interface_lua.lua"</html>'),
            MockResponse(200, training_xml),
        ]
        mock_session.post.return_value = MockResponse(200, "")
        mock_session.closed = False

        client = ZteH186ApiClient("192.168.10.2", "admin", "pass", session=mock_session)
        stats = await client.async_get_dsl_stats()

        self.assertEqual(stats.dsl_status, "Down")
        # Missing metrics are reported as unknown (None), not a misleading 0.0.
        self.assertIsNone(stats.downstream_sync)
        self.assertIsNone(stats.upstream_sync)
        self.assertIsNone(stats.profile)
        self.assertIsNone(stats.modulation)

    async def test_concurrent_requests_serialized_by_lock(self):
        """Concurrent requests are serialized by the lock without race conditions."""
        mock_session = MagicMock()

        call_order = []

        class MockResponse:
            def __init__(self, status=200, text_data="", label=""):
                self.status = status
                self._text = text_data
                self.label = label
                self.headers = MagicMock(getall=MagicMock(return_value=["SID=locked_sid"]))
                self.cookies = {"SID": MagicMock(value="locked_sid")}

            async def __aenter__(self):
                if self.label:
                    call_order.append(f"enter_{self.label}")
                await asyncio.sleep(0.01)
                return self

            async def __aexit__(self, *args):
                if self.label:
                    call_order.append(f"exit_{self.label}")

            async def text(self, *args, **kwargs):
                return self._text

        mock_session.get.side_effect = [
            # First handshake
            MockResponse(200, SAMPLE_LOGIN_HTML),
            MockResponse(200, "12345678"),
            MockResponse(200, '<html>"internet_dsl_interface_lua.lua"</html>'),
            MockResponse(200, SAMPLE_DSL_XML, label="call_1"),
            # Second call (already authenticated)
            MockResponse(200, SAMPLE_DSL_XML, label="call_2"),
        ]
        mock_session.post.return_value = MockResponse(200, "")
        mock_session.closed = False

        client = ZteH186ApiClient("192.168.10.2", "admin", "pass", session=mock_session)

        # Launch two stats requests in parallel
        results = await asyncio.gather(
            client.async_get_dsl_stats(),
            client.async_get_dsl_stats(),
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].downstream_sync, 109.2)
        self.assertEqual(results[1].downstream_sync, 109.2)
        self.assertEqual(call_order, ["enter_call_1", "exit_call_1", "enter_call_2", "exit_call_2"])


class _Resp:
    """Minimal async context-manager response for handshake mocking."""

    def __init__(self, status=200, text_data="", sid=None):
        self.status = status
        self._text = text_data
        self.headers = MagicMock(
            getall=MagicMock(return_value=[f"SID={sid}; path=/"] if sid else [])
        )
        self.cookies = {"SID": MagicMock(value=sid)} if sid else {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def text(self, *args, **kwargs):
        return self._text


def _client(mock_session):
    mock_session.closed = False
    return ZteH186ApiClient("192.168.10.2", "admin", "secret", session=mock_session)


class ApiErrorPathTests(unittest.IsolatedAsyncioTestCase):
    """Coverage for the handshake error paths."""

    async def test_login_connection_error(self):
        """A network error during login raises ZteH186ConnectionError."""
        mock_session = MagicMock()
        mock_session.get.side_effect = aiohttp.ClientError("boom")
        with self.assertRaises(ZteH186ConnectionError):
            await _client(mock_session).async_login()

    async def test_login_token_not_found(self):
        """A login-token page without digits raises ZteH186ProtocolError."""
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            _Resp(200, SAMPLE_LOGIN_HTML),
            _Resp(200, "no-digits-here"),
        ]
        with self.assertRaises(ZteH186ProtocolError):
            await _client(mock_session).async_login()

    async def test_unauthorized_session_raises_auth_error(self):
        """A primed status page without the DSL reference is an auth failure."""
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            _Resp(200, SAMPLE_LOGIN_HTML),
            _Resp(200, "12345678"),
            _Resp(200, "<html>login form</html>"),
        ]
        mock_session.post.return_value = _Resp(200, "", sid="sid_x")
        with self.assertRaises(ZteH186AuthError):
            await _client(mock_session).async_login()

    async def test_missing_required_fields_when_up(self):
        """Status=Up but missing rate fields raises ZteH186ProtocolError."""
        xml = (
            "<ajax_response_xml_root>"
            "<IF_ERRORSTR>SUCC</IF_ERRORSTR>"
            "<Instance><ParaName>Status</ParaName><ParaValue>Up</ParaValue></Instance>"
            "</ajax_response_xml_root>"
        )
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            _Resp(200, SAMPLE_LOGIN_HTML),
            _Resp(200, "12345678"),
            _Resp(200, '<html>"internet_dsl_interface_lua.lua"</html>'),
            _Resp(200, xml),
        ]
        mock_session.post.return_value = _Resp(200, "", sid="sid_x")
        with self.assertRaises(ZteH186ProtocolError):
            await _client(mock_session).async_get_dsl_stats()

    async def test_relogin_on_session_timeout(self):
        """A SessionTimeout in the stats response triggers a re-login and retry."""
        timeout_xml = (
            "<ajax_response_xml_root><IF_ERRORSTR>SessionTimeout</IF_ERRORSTR>"
            "</ajax_response_xml_root>"
        )
        mock_session = MagicMock()
        mock_session.get.side_effect = [
            _Resp(200, SAMPLE_LOGIN_HTML),
            _Resp(200, "12345678"),
            _Resp(200, '<html>"internet_dsl_interface_lua.lua"</html>'),
            _Resp(200, timeout_xml),
            _Resp(200, SAMPLE_LOGIN_HTML),
            _Resp(200, "12345678"),
            _Resp(200, '<html>"internet_dsl_interface_lua.lua"</html>'),
            _Resp(200, SAMPLE_DSL_XML),
        ]
        mock_session.post.return_value = _Resp(200, "", sid="sid_x")
        stats = await _client(mock_session).async_get_dsl_stats()
        self.assertEqual(stats.dsl_status, "Up")


if __name__ == "__main__":
    unittest.main()
