"""Asynchronous API Client for ZTE H186 DSL modem."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
import ipaddress
import logging
import re
import time
import xml.etree.ElementTree as ET

import aiohttp

_LOGGER = logging.getLogger(__name__)

# ZTE H186 web-UI endpoints (relative to the modem base URL)
DSL_STATUS_PATH = "/getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp"
DSL_XML_PATH = "/common_page/internet_dsl_interface_lua.lua"
# Device information (serial number, MAC address, versions). The modem only answers this request
# after the status page was requested in the same session.
STATUS_PAGE_PATH = "/getpage.lua?pid=1002&nextpage=ManagDiag_StatusManag_t.lp"
DEVICE_INFO_PATH = "/common_page/ManagReg_lua.lua"
_SERIAL_PATTERN = re.compile(r"^[A-Za-z0-9]{6,32}$")


class ZteH186Error(Exception):
    """Base exception for ZTE H186."""


class ZteH186ConnectionError(ZteH186Error):
    """Cannot connect to ZTE H186 modem."""


class ZteH186AuthError(ZteH186Error):
    """Authentication failed."""


class ZteH186ProtocolError(ZteH186Error):
    """Unexpected protocol response from modem."""


@dataclass(slots=True, frozen=True)
class ZteH186DeviceInfo:
    """What identifies the physical modem, as reported by the modem itself."""

    serial_number: str
    mac_address: str | None = None
    model: str | None = None
    hardware_version: str | None = None
    software_version: str | None = None
    boot_version: str | None = None
    dsl_version: str | None = None


@dataclass(slots=True, frozen=True)
class ZteH186Data:
    """Dataclass holding all normalized ZTE H186 DSL statistics."""

    # Core line metrics. None when the field is absent, e.g. while the line is
    # not in Showtime (link down / training) and the modem omits it.
    downstream_sync: float | None  # Mbit/s
    upstream_sync: float | None  # Mbit/s
    downstream_max: float | None  # Mbit/s
    upstream_max: float | None  # Mbit/s
    downstream_snr: float | None  # dB
    upstream_snr: float | None  # dB
    downstream_attenuation: float | None  # dB
    upstream_attenuation: float | None  # dB
    profile: str | None  # e.g., "17a", "35b"
    modulation: str | None  # e.g., "VDSL2"

    # Optional fields
    dsl_status: str | None = None  # e.g., "Up"
    downstream_power: float | None = None  # dBm
    upstream_power: float | None = None  # dBm
    data_path: str | None = None  # "Interleaved" / "Fast"
    downstream_interleave_depth: int | None = None
    upstream_interleave_depth: int | None = None
    downstream_interleave_delay: int | None = None  # ms
    upstream_interleave_delay: int | None = None  # ms
    downstream_inp: float | None = None  # symbols
    upstream_inp: float | None = None  # symbols
    showtime: int | None = None  # seconds uptime of link
    link_encapsulation: str | None = None  # "PTM" / "ATM"
    downstream_crc: int | None = None  # errors
    upstream_crc: int | None = None  # errors
    downstream_fec: int | None = None  # errors
    upstream_fec: int | None = None  # errors

    # Raw XML values dictionary for diagnostics
    raw_values: dict[str, str] | None = None


class ZteH186ApiClient:
    """API client interacting with ZTE H186 modem via HTTP web endpoints."""

    def __init__(
        self,
        host: str,
        username: str = "admin",
        password: str = "",
        session: aiohttp.ClientSession | None = None,
        timeout: int = 15,
    ) -> None:
        """Initialize the API client."""
        self._raw_host = host.strip()
        self._username = username.strip()
        self._password = password.rstrip("\r\n")
        self._custom_session = session is not None
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._base_url = self._format_base_url(self._raw_host)
        self._is_authenticated = False
        self._sid: str | None = None
        self._lock = asyncio.Lock()

    @property
    def base_url(self) -> str:
        """Return the resolved modem base URL (e.g. http://192.168.10.2)."""
        return self._base_url

    @staticmethod
    def _format_base_url(host: str) -> str:
        """Format base URL, handling IPv6 bracket enclosure and scheme."""
        clean_host = host.rstrip("/")
        if clean_host.startswith(("http://", "https://")):
            return clean_host

        try:
            addr = ipaddress.ip_address(clean_host)
            if addr.version == 6:
                return f"http://[{addr}]"
            return f"http://{addr}"
        except ValueError:
            return f"http://{clean_host}"

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp client session with unsafe=True cookie storage."""
        if self._session is None or self._session.closed:
            # Crucial: unsafe=True is required so aiohttp does not reject cookies from IP addresses!
            jar = aiohttp.CookieJar(unsafe=True, quote_cookie=False)
            self._session = aiohttp.ClientSession(
                cookie_jar=jar,
                timeout=self._timeout,
            )
        return self._session

    async def close(self) -> None:
        """Log out of the modem and close the client session if internally created.

        The modem allows one admin session at a time. A session that is not logged out stays
        occupied
        until it times out, and the next login (after a reload, a restart or a dialog) is refused.
        """
        await self.async_logout()
        if not self._custom_session and self._session and not self._session.closed:
            await self._session.close()

    async def async_logout(self) -> None:
        """Log out of the modem so that its single admin session is free again (best effort)."""
        async with self._lock:
            await self._async_logout_internal()

    async def _async_logout_internal(self) -> None:
        """Send the web UI's log-off request (must hold self._lock)."""
        session, sid = self._session, self._sid
        self._is_authenticated = False
        self._sid = None
        if session is None or session.closed or not sid:
            return
        try:
            async with asyncio.timeout(5):
                async with session.post(
                    f"{self._base_url}/",
                    data={"IF_LogOff": "1", "IF_LanguageSwitch": ""},
                    headers={
                        "Cookie": f"SID={sid}; _TESTCOOKIESUPPORT=1",
                        "Referer": f"{self._base_url}/",
                    },
                ) as resp:
                    await resp.read()
        except (TimeoutError, aiohttp.ClientError) as err:
            _LOGGER.debug(
                "Log-off from the modem failed (%s); the session times out by itself", err
            )

    @staticmethod
    def _decode_session_token(html_text: str) -> str:
        """Extract and decode hex-encoded session token from login page."""
        match = re.search(
            r'_sessionTmpToken\s*=\s*[\'"]((?:\\x[0-9a-fA-F]{2})+)[\'"]',
            html_text,
        )
        if not match:
            # Fallback pattern
            match = re.search(r'_sessionTmpToken\s*=\s*[\'"]([^\'"]+)[\'"]', html_text)
            if not match:
                raise ZteH186ProtocolError("Session token missing on modem login page.")
            val = match.group(1)
            if "\\x" in val:
                hex_bytes = "".join(re.findall(r"\\x([0-9a-fA-F]{2})", val))
                return bytes.fromhex(hex_bytes).decode("ascii", errors="replace")
            return val

        hex_bytes = "".join(re.findall(r"\\x([0-9a-fA-F]{2})", match.group(1)))
        try:
            return bytes.fromhex(hex_bytes).decode("ascii", errors="replace")
        except Exception as err:
            raise ZteH186ProtocolError(f"Failed to decode session token: {err}") from err

    @staticmethod
    def _extract_xml_values(xml_string: str) -> dict[str, str]:
        """Extract XML root and parse name-value pairs from ZTE modem response."""
        match = re.search(
            r"<ajax_response_xml_root\b[^>]*>.*?</ajax_response_xml_root>",
            xml_string,
            re.DOTALL,
        )
        if not match:
            raise ZteH186ProtocolError("Router response does not contain expected XML root.")

        try:
            root = ET.fromstring(match.group(0))
        except ET.ParseError as err:
            raise ZteH186ProtocolError(f"Router response has invalid XML syntax: {err}") from err

        values: dict[str, str] = {}
        for element in root.iter():
            name = element.tag.rsplit("}", 1)[-1]
            if element.text and element.text.strip():
                values[name] = element.text.strip()
            if name == "Instance":
                param: str | None = None
                for child in element:
                    tag = child.tag.rsplit("}", 1)[-1]
                    text = (child.text or "").strip()
                    if tag == "ParaName":
                        param = text
                    elif tag == "ParaValue" and param:
                        values[param] = text
                        param = None
        return values

    async def _async_login_internal(self, session: aiohttp.ClientSession) -> None:
        """Execute the 4-step authentication handshake (internal, must hold self._lock)."""
        root_url = f"{self._base_url}/"
        self._sid = None

        # Step 1: Request root login page and extract _sessionTmpToken
        try:
            async with session.get(root_url) as resp:
                if resp.status != 200:
                    raise ZteH186ConnectionError(f"Login page returned HTTP {resp.status}")
                login_page_text = await resp.text(encoding="latin-1", errors="replace")
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ZteH186ConnectionError(
                f"Unable to reach modem at {self._base_url}: {err}"
            ) from err

        # Validate that we reached the genuine login page (raises if the token is
        # absent). The decoded token itself is NOT used during login (see below).
        self._decode_session_token(login_page_text)

        # Step 2: Fetch login token (challenge)
        token_url = f"{self._base_url}/function_module/login_module/login_page/logintoken_lua.lua"
        try:
            async with session.get(token_url, headers={"Referer": root_url}) as resp:
                token_resp = await resp.text(encoding="latin-1", errors="replace")
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ZteH186ConnectionError(f"Failed to fetch login token: {err}") from err

        token_match = re.search(r"(\d+)", token_resp)
        if not token_match:
            raise ZteH186ProtocolError("Could not retrieve numeric login token.")
        login_token = token_match.group(1)

        # Step 3: Compute SHA-256 and submit login form
        pass_hash = hashlib.sha256((self._password + login_token).encode("utf-8")).hexdigest()

        # Post exactly the three fields the modem's own webSubmitForm login uses.
        # Adding _sessionTOKEN here makes the firmware hand out an UNauthorized SID,
        # after which every protected page answers with 404 / SessionTimeout.
        login_payload = {
            "Username": self._username,
            "Password": pass_hash,
            "action": "login",
        }

        # Some ZTE firmware builds require the _TESTCOOKIESUPPORT cookie during login POST
        login_headers = {
            "Referer": root_url,
            "Content-Type": "application/x-www-form-urlencoded",
            "Cookie": "_TESTCOOKIESUPPORT=1",
        }

        try:
            async with session.post(
                root_url,
                data=login_payload,
                headers=login_headers,
                allow_redirects=False,
            ) as resp:
                # Direct Set-Cookie header extraction (bypasses any IP cookie-jar limitations)
                for cookie_header in resp.headers.getall("Set-Cookie", []):
                    sid_match = re.search(r"\bSID=([^;,\s]+)", cookie_header)
                    if sid_match:
                        self._sid = sid_match.group(1)
                        break

                if not self._sid and "SID" in resp.cookies:
                    self._sid = resp.cookies["SID"].value
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ZteH186ConnectionError(f"Failed to send login form: {err}") from err

        # Fallback check from session cookie jar
        if not self._sid:
            try:
                cookies = session.cookie_jar.filter_cookies(self._base_url)
                if "SID" in cookies and cookies["SID"].value:
                    self._sid = cookies["SID"].value
            except Exception:
                pass

        if not self._sid:
            raise ZteH186AuthError(
                "Authentication failed: no SID session cookie received. "
                "Check username and password."
            )

        # Step 4: Prime DSL status page
        status_url = f"{self._base_url}{DSL_STATUS_PATH}"
        status_headers = {
            "Referer": root_url,
            "Cookie": f"SID={self._sid}; _TESTCOOKIESUPPORT=1",
        }
        try:
            async with session.get(status_url, headers=status_headers) as resp:
                status_page_html = await resp.text(encoding="latin-1", errors="replace")
                authorized = (
                    resp.status == 200 and "internet_dsl_interface_lua.lua" in status_page_html
                )
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ZteH186ConnectionError(
                f"Failed to load intermediate DSL status page: {err}"
            ) from err

        # The modem returns a SID even for rejected credentials, but then every
        # protected page falls back to SessionTimeout. A primed status page without
        # the DSL reference means the session is not authorized -> treat as an auth
        # failure so Home Assistant starts a reauth flow instead of retrying forever.
        if not authorized:
            raise ZteH186AuthError(
                "The modem did not authorize the session after login. "
                "Check the username and password."
            )

        self._is_authenticated = True
        _LOGGER.debug(
            "Successfully authenticated with ZTE H186 at %s (SID=%s)",
            self._base_url,
            self._sid[:4] + "***",
        )

    async def async_login(self) -> None:
        """Execute the 4-step authentication handshake with the modem."""
        async with self._lock:
            session = await self._get_session()
            await self._async_login_internal(session)

    async def async_get_device_info(self) -> ZteH186DeviceInfo:
        """Read the identity of the modem: serial number, MAC address, model and versions."""
        async with self._lock:
            session = await self._get_session()
            if not self._is_authenticated or not self._sid:
                await self._async_login_internal(session)

            response_text = await self._async_fetch_device_info_xml(session)
            if response_text is None:
                _LOGGER.debug("Session expired, re-authenticating to read the device information")
                self._is_authenticated = False
                self._sid = None
                await self._async_login_internal(session)
                response_text = await self._async_fetch_device_info_xml(session)
            if response_text is None:
                raise ZteH186ProtocolError("The modem did not return its device information.")

            values = self._extract_xml_values(response_text)
            error = values.get("IF_ERRORSTR", "")
            if error not in ("", "SUCC"):
                raise ZteH186ProtocolError(f"Modem returned error: {error}")
            serial = values.get("SerialNumber", "").strip()
            if not _SERIAL_PATTERN.match(serial):
                raise ZteH186ProtocolError("The modem did not report a usable serial number.")
            return ZteH186DeviceInfo(
                serial_number=serial,
                mac_address=(values.get("MACAddress") or "").strip().lower() or None,
                model=values.get("ModelName") or None,
                hardware_version=values.get("HardwareVer") or None,
                software_version=values.get("SoftwareVer") or None,
                boot_version=values.get("BootVer") or None,
                dsl_version=values.get("ModelFirmwareVer") or None,
            )

    async def _async_fetch_device_info_xml(self, session: aiohttp.ClientSession) -> str | None:
        """Request the status page and then the device data; ``None`` if the session has expired."""
        status_url = f"{self._base_url}{STATUS_PAGE_PATH}"
        cookie = f"SID={self._sid}; _TESTCOOKIESUPPORT=1"
        endpoint = f"{self._base_url}{DEVICE_INFO_PATH}?_={int(time.time() * 1000)}"
        try:
            async with session.get(status_url, headers={"Cookie": cookie}) as page:
                await page.read()
            async with session.get(
                endpoint,
                headers={
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/xml, text/xml, */*; q=0.01",
                    "Referer": status_url,
                    "Cookie": cookie,
                },
            ) as resp:
                text = await resp.text(encoding="latin-1", errors="replace")
                if resp.status != 200 or "SessionTimeout" in text:
                    return None
                return text
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ZteH186ConnectionError(
                f"Unable to reach modem at {self._base_url}: {err}"
            ) from err

    @staticmethod
    async def async_probe_model(host: str, session: aiohttp.ClientSession) -> str | None:
        """Return the model title of the login page (no login), for example "H186"; ``None`` if
        unreachable."""
        try:
            async with asyncio.timeout(5):
                async with session.get(ZteH186ApiClient._format_base_url(host) + "/") as resp:
                    if resp.status != 200:
                        return None
                    text = await resp.text(encoding="latin-1", errors="replace")
        except (TimeoutError, aiohttp.ClientError):
            return None
        match = re.search(r"<title>(.*?)</title>", text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        # The page writes the title as HTML character references (&#72;&#49;...).
        return re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), match.group(1)).strip() or None

    async def async_get_dsl_stats(self) -> ZteH186Data:
        """Fetch and parse current DSL statistics from the modem."""
        async with self._lock:
            session = await self._get_session()

            if not self._is_authenticated or not self._sid:
                await self._async_login_internal(session)

            status_url = f"{self._base_url}{DSL_STATUS_PATH}"
            ts_ms = int(time.time() * 1000)
            endpoint = f"{self._base_url}{DSL_XML_PATH}?_={ts_ms}"

            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/xml, text/xml, */*; q=0.01",
                "Referer": status_url,
                "Cookie": f"SID={self._sid}; _TESTCOOKIESUPPORT=1",
            }

            try:
                async with session.get(endpoint, headers=headers) as resp:
                    response_text = await resp.text(encoding="latin-1", errors="replace")
                    if resp.status != 200 or "SessionTimeout" in response_text:
                        _LOGGER.debug("Session expired or HTTP error, re-authenticating...")
                        self._is_authenticated = False
                        self._sid = None
                        await self._async_login_internal(session)
                        headers["Cookie"] = f"SID={self._sid}; _TESTCOOKIESUPPORT=1"
                        async with session.get(endpoint, headers=headers) as retry_resp:
                            response_text = await retry_resp.text(
                                encoding="latin-1", errors="replace"
                            )
                            if retry_resp.status != 200:
                                raise ZteH186ProtocolError(
                                    f"DSL endpoint returned HTTP {retry_resp.status} "
                                    "after re-login."
                                )
            except (TimeoutError, aiohttp.ClientError) as err:
                raise ZteH186ConnectionError(
                    f"Connection error requesting DSL stats: {err}"
                ) from err

            values = self._extract_xml_values(response_text)
            error = values.get("IF_ERRORSTR", "")
            if error not in ("", "SUCC"):
                raise ZteH186ProtocolError(f"Modem returned error: {error}")

            required_keys = (
                "Downstream_current_rate",
                "Upstream_current_rate",
                "Downstream_max_rate",
                "Upstream_max_rate",
                "Downstream_noise_margin",
                "Upstream_noise_margin",
                "Downstream_attenuation",
                "Upstream_attenuation",
                "CurrentProfile",
                "Module_type",
            )
            missing = [k for k in required_keys if k not in values]
            dsl_status = values.get("Status", "Down")
            is_up = str(dsl_status).strip().lower() == "up"

            if missing and is_up:
                raise ZteH186ProtocolError(
                    "Missing required fields in DSL response while link is Up: "
                    f"{', '.join(missing)}"
                )
            if missing:
                _LOGGER.debug(
                    "DSL line not in Showtime (Status=%s). "
                    "Reporting 'unknown' for missing fields: %s",
                    dsl_status,
                    missing,
                )

        def _to_opt_float(key: str, divisor: float = 1.0) -> float | None:
            val = values.get(key)
            if not val:
                return None
            try:
                return float(val) / divisor
            except ValueError:
                return None

        def _to_opt_int(key: str) -> int | None:
            val = values.get(key)
            if not val:
                return None
            try:
                return int(val)
            except ValueError:
                return None

        return ZteH186Data(
            downstream_sync=_to_opt_float("Downstream_current_rate", 1000.0),
            upstream_sync=_to_opt_float("Upstream_current_rate", 1000.0),
            downstream_max=_to_opt_float("Downstream_max_rate", 1000.0),
            upstream_max=_to_opt_float("Upstream_max_rate", 1000.0),
            downstream_snr=_to_opt_float("Downstream_noise_margin", 10.0),
            upstream_snr=_to_opt_float("Upstream_noise_margin", 10.0),
            downstream_attenuation=_to_opt_float("Downstream_attenuation", 10.0),
            upstream_attenuation=_to_opt_float("Upstream_attenuation", 10.0),
            profile=values.get("CurrentProfile"),
            modulation=values.get("Module_type"),
            dsl_status=values.get("Status", "Down"),
            downstream_power=_to_opt_float("Downstream_power", 10.0),
            upstream_power=_to_opt_float("Upstream_power", 10.0),
            data_path=values.get("Data_path"),
            downstream_interleave_depth=_to_opt_int("DownInterleavedepth"),
            upstream_interleave_depth=_to_opt_int("UpInterleaveDepth"),
            downstream_interleave_delay=_to_opt_int("DownInterleaveDelay"),
            upstream_interleave_delay=_to_opt_int("UpInterleaveDelay"),
            downstream_inp=_to_opt_float("DownstreamInp", 10.0),
            upstream_inp=_to_opt_float("UpstreamInp", 10.0),
            showtime=_to_opt_int("Showtime_start"),
            link_encapsulation=values.get("tLinkEncapsulationUsed"),
            downstream_crc=_to_opt_int("DownCrc_errors"),
            upstream_crc=_to_opt_int("UpCrc_errors"),
            downstream_fec=_to_opt_int("Fec_errors"),
            upstream_fec=_to_opt_int("Atuc_fec_errors"),
            raw_values=values,
        )
