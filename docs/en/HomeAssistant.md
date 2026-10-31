# ZTE H186: Local DSL Line Telemetry in Home Assistant

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](HomeAssistant.md) | [Deutsch](../de/HomeAssistant.md) | [Français](../fr/HomeAssistant.md) | [Español](../es/HomeAssistant.md)

---

## Purpose and Scope

This project retrieves DSL line telemetry from a compatible ZTE H186 modem via its local web interface. A client authenticates, fetches the DSL XML status data, and delivers it to Home Assistant. Neither a cloud connection nor MQTT is required. DSL, router, Wi-Fi, and WAN configurations are not modified. Note that logging in establishes an active session on the modem and is not completely stateless.

The Home Assistant package and integration provide a coordinator poll entity and 27 measuring/telemetry sensors. These represent physical line status metrics, not real-time network traffic or Internet speed tests.

This documentation contains no site-specific IP addresses, network subnets, credentials, or links to private Home Assistant instances. Neutral placeholders such as `<MODEM-LAN-IP>` are used throughout.

---

## Architecture

The project supports two integration methods with Home Assistant:

1. **Home Assistant Custom Integration (`custom_components/zte_h186`) (Recommended)**:
   - Native integration with UI Config Flow (**Settings > Devices & Services > Add Integration**)
   - Automatic discovery of 27 sensors, 2 binary sensors, and a diagnostic trigger button
   - Central asynchronous `DataUpdateCoordinator` with authenticated session caching
   - Full HACS compatibility and seamless reconfiguration upon IP or password changes

2. **Classic YAML Package (`zte-h186-package.yaml`)**:
   - Command-line polling process (`zte_h186_stats.py`) every 300 seconds
   - Coordinates poll sensor and template sensor entities
   - Designed for purely file-based legacy environments

```text
Home Assistant Core
  -> Custom Integration (custom_components/zte_h186)
     -> Config Flow (Host, Username, Password)
     -> DataUpdateCoordinator (asynchronous aiohttp polling)
     -> 27 Sensor Entities, 2 Binary Sensors, 1 Action Button
  -> OR legacy YAML package:
     -> Python Process (zte_h186_stats.py)
     -> Shared JSON with status, timestamp, and line data
     -> 26 Template Sensors
```

---

## Hardware Cabling and Local Management of the Modem

This section details the physical cabling and network configuration required to run the ZTE H186 as a dedicated DSL modem in front of a downstream router while maintaining local administrative access.

### Physical Ports and Color Coding

The ports of the ZTE H186 perform distinct roles in home and operational network topologies:

| Port / Color Mark | Designation | Target Connection | Operational Function & Data Flow |
|---|---|---|---|
| **Red** | WAN / Router Port | Connect to the **WAN port** of your downstream router | Passes the pure DSL link (Bridge mode / PPPoE passthrough) to the main router. **No local web management access or login occurs over this port.** |
| **Yellow** | LAN / Management | Connect to a **network switch** in the local management network/VLAN | Exclusively used for administrative access to the web interface and local telemetry queries by Home Assistant. |
| **Grey** | DSL | Connect to the **DSL / Telephone line** (TAE/socket/splitter) | Carries the high-frequency DSL subscriber line signal directly into the modem. |

> **Notice on Manufacturer Labels and Model Variations:**  
> The color coding described above (Grey = DSL, Red = WAN, Yellow = LAN) corresponds to the standard factory enclosure of the ZTE H186. Depending on the distributor, hardware revision, or ISP branding, specific devices may feature different port markings (e.g. neutral black sockets labeled `DSL`, `WAN`, or `LAN1`). Always check the embossed labels directly on the device ports and cross-reference with manufacturer documentation before connecting cables.

---

### Step-by-Step Configuration of Local Management

To prevent IP address collisions on your production network and ensure reliable telemetry polling, configure the modem before integrating it into your home network switch:

1. **Initial Direct PC Connection:**  
   If necessary (e.g. on new modems, after a factory reset, or with unknown pre-configurations), connect a PC or laptop directly to the **yellow LAN port** using an Ethernet cable. Open the modem's web interface in a web browser using its factory default LAN IP address.

2. **Assign a Static IP in the Local Management Network:**  
   In the modem's LAN network settings, assign a free, static IPv4 address (`<MODEM-LAN-IP>`) and appropriate subnet mask (`<SUBNET-MASK>`) from your local management network or management VLAN.
   - Choose a subnet mask matching your management network.
   - Ensure the assigned `<MODEM-LAN-IP>` is strictly outside any dynamic DHCP lease pool to prevent conflicts with other devices.

3. **Disable the ZTE H186 DHCP Server:**  
   **CRITICAL**: Deactivate the built-in DHCP server of the ZTE H186 in the LAN settings **before** connecting the yellow LAN port to your production network switch.
   - *Rationale:* Two active DHCP servers on the same network segment ("Rogue DHCP") result in uncontrolled IP assignments and severe connection outages for clients across your network.
   - The DHCP server on your downstream main router remains active and continues to manage regular client IP assignments.

4. **Save Settings and Verify Access:**  
   Save the updated settings on the modem. Adjust your test PC's IP address to the chosen management subnet and open `http://<MODEM-LAN-IP>` in your browser to verify connectivity.

5. **Connect to the Management Network Switch:**  
   Connect the **yellow LAN port** with an Ethernet cable to a switch port on the appropriate management network/VLAN.

6. **Future Management Access:**  
   All subsequent administration logins and Home Assistant telemetry polling occur strictly via the assigned LAN IP (`<MODEM-LAN-IP>`) on the yellow LAN port — never through the red WAN port.

---

### Relation to Home Assistant Integration

Home Assistant queries DSL telemetry locally over the configured management interface:

1. **Network Reachability from Home Assistant:**  
   - The modem address configured in Home Assistant must match the reachable static LAN IP (`<MODEM-LAN-IP>`).
   - The Home Assistant instance (e.g. on Home Assistant OS / HAOS) requires network reachability to this IP over port 80 (HTTP). If Home Assistant and the modem operate in different VLANs or subnets, intermediate routing and firewall rules must permit traffic to `<MODEM-LAN-IP>:80`.

2. **Configuring Credentials in the Integration:**  
   - Navigate to **Settings > Devices & Services**.
   - Click **Add Integration** and search for **ZTE H186 DSL Modem**.
   - Enter the connection parameters:
     - **IP Address or Hostname** (`host`): The static management IP (`<MODEM-LAN-IP>`).
     - **Username** (`username`): Web UI username (default: `admin`).
     - **Password** (`password`): Administrative web UI password.
   - *Protected Storage:* Passwords are submitted exclusively in the masked password field in the UI. Home Assistant securely stores these credentials inside the encrypted `ConfigEntry`. Credentials must never be stored in plaintext scripts or automations.

3. **Intended Topology vs. Verified Software State:**  
   - *Intended Topology:* The dual-cable topology described here (Red WAN for internet traffic to router; Yellow LAN for management & Home Assistant telemetry via switch) provides clean, manufacturer-compliant separation for bridge operation.
   - *Verified Software State:* Software workflows, authentication handshakes, coordinator polling, and entity updates have been verified in the test suite and local interface tests. Physical wiring, VLAN tags, and firewall rules must be verified in your individual environment.

---

## Complete Sensor Field Reference

The integration exposes 27 sensors and 2 binary sensors:

| Key | XML Field | Conversion / Unit | Category |
|---|---|---|---|
| `downstream_sync` | `Downstream_current_rate` | /1000, Mbit/s | Telemetry |
| `upstream_sync` | `Upstream_current_rate` | /1000, Mbit/s | Telemetry |
| `downstream_max` | `Downstream_max_rate` | /1000, Mbit/s | Telemetry |
| `upstream_max` | `Upstream_max_rate` | /1000, Mbit/s | Telemetry |
| `downstream_capacity_ratio` | Calculated ratio | %, (Sync / Max * 100) | Diagnostic |
| `downstream_snr` | `Downstream_noise_margin` | /10, dB | Telemetry |
| `upstream_snr` | `Upstream_noise_margin` | /10, dB | Telemetry |
| `downstream_attenuation` | `Downstream_attenuation` | /10, dB | Telemetry |
| `upstream_attenuation` | `Upstream_attenuation` | /10, dB | Telemetry |
| `downstream_power` | `Downstream_power` | /10, dBm | Diagnostic |
| `upstream_power` | `Upstream_power` | /10, dBm | Diagnostic |
| `profile` | `CurrentProfile` | String (e.g. 17a, 35b) | Telemetry |
| `modulation` | `Module_type` | String (e.g. VDSL2) | Telemetry |
| `dsl_status` | `Status` | String (e.g. Up) | Telemetry |
| `data_path` | `Data_path` | String (Interleaved/Fast) | Diagnostic |
| `downstream_interleave_depth` | `DownInterleavedepth` | Integer | Diagnostic |
| `upstream_interleave_depth` | `UpInterleaveDepth` | Integer | Diagnostic |
| `downstream_interleave_delay` | `DownInterleaveDelay` | ms | Diagnostic |
| `upstream_interleave_delay` | `UpInterleaveDelay` | ms | Diagnostic |
| `downstream_inp` | `DownstreamInp` | /10, symbols | Diagnostic |
| `upstream_inp` | `UpstreamInp` | /10, symbols | Diagnostic |
| `showtime` | `Showtime_start` | Integer, seconds | Diagnostic |
| `link_encapsulation` | `tLinkEncapsulationUsed` | String | Diagnostic |
| `downstream_crc` | `DownCrc_errors` | Integer, errors | Diagnostic |
| `upstream_crc` | `UpCrc_errors` | Integer, errors | Diagnostic |
| `downstream_fec` | `Fec_errors` | Integer, errors | Diagnostic |
| `upstream_fec` | `Atuc_fec_errors` | Integer, errors | Diagnostic |

### Binary Sensors & Buttons
- `binary_sensor.dsl_link`: Indicates physical DSL link state (`connected` / `disconnected`).
- `binary_sensor.line_noise_warning`: Safety monitor triggering a warning when SNR margin falls below 6.0 dB.
- `button.refresh_stats`: Triggers immediate coordinator poll.

---

## Authentication Protocol & Security Boundaries

1. The modem homepage supplies a JavaScript session temporary token (`_sessionTmpToken`) with hexadecimal escapes.
2. The client fetches a numeric challenge token from `/function_module/login_module/login_page/logintoken_lua.lua`.
3. The client computes `SHA-256(password + challenge_token)` and posts user, hash, action, and session token to the login handler.
4. The response yields an authenticated `SID` cookie.
5. The client loads `getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp` to establish expected internal state.
6. The client requests `/common_page/internet_dsl_interface_lua.lua` and parses the XML payload.

---

## Troubleshooting

| Error Code | Recommended Action |
|---|---|
| `network_denied` | Target address violated SSRF rules (e.g. not a private RFC 1918 IPv4 address). Check host settings. |
| `cannot_connect` | Verify IP address, physical Ethernet cabling, and port 80 accessibility. |
| `invalid_auth` | Check web interface username and password. |
| `timeout` | Verify network routing, firewall rules, and modem responsiveness. |
