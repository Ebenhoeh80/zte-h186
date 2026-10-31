# 05 - Hardware Cabling & Local Management Rules

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](#english) | [Deutsch](#deutsch)

---

## English

### 1. Physical Port Roles & Color Coding
The ZTE H186 uses a three-port physical topology when operated as a bridge modem before a downstream router:

| Color Mark | Label | Target Device / Cable | Function & Operational Rule |
|---|---|---|---|
| **Red** | WAN / Router Port | Downstream Router **WAN Port** | Passes pure DSL data traffic (Bridge mode / PPPoE passthrough) to the router. **No web management access or login allowed over this port.** |
| **Yellow** | LAN / Management | Local Management **Network Switch / VLAN** | Dedicated administrative access to the web interface and Home Assistant telemetry polling. |
| **Grey** | DSL | **DSL / Telephone line** (TAE/socket) | Receives the high-frequency DSL subscriber line signal. |

*Note on Hardware Variations*: Markings correspond to standard ZTE H186 factory enclosures. Always verify port labels (`DSL`, `WAN`, `LAN`) stamped on the device casing against manufacturer manuals.

### 2. Step-by-Step Configuration Sequence
1. **Direct PC Connection**: Connect a PC directly to the **yellow LAN port** with an Ethernet cable. Open the modem web interface at its factory default IP address.
2. **Assign Static Management IP**: In LAN settings, configure a static IPv4 address (`<MODEM-LAN-IP>`) and appropriate subnet mask (`<SUBNET-MASK>`) from your local management network or management VLAN.
   - The IP must be outside any dynamic DHCP lease pool to prevent conflicts.
3. **Disable Modem DHCP Server**: **CRITICAL**: Deactivate the ZTE H186's built-in DHCP server **before** connecting the yellow port to your local network switch.
   - *Rationale*: Two active DHCP servers on the same network segment cause IP conflicts and client disconnects ("Rogue DHCP"). The downstream router's DHCP server remains active.
4. **Save & Test Access**: Save the settings. Adjust the PC's IP to the management subnet and verify access at `http://<MODEM-LAN-IP>`.
5. **Connect to Switch**: Plug the yellow port into your switch on the appropriate management VLAN/subnet.
6. **Access Rule**: All subsequent management and Home Assistant polling occurs strictly via `<MODEM-LAN-IP>` on the yellow port.

### 3. Relation to Home Assistant Integration
1. **Reachability**: The Home Assistant host (e.g. Home Assistant OS / HAOS) must have Layer-3 / Layer-2 network reachability to `<MODEM-LAN-IP>` on HTTP port 80.
2. **Setup**: Configured via **Settings > Devices & Services > Add Integration > ZTE H186 DSL Modem**.
3. **Protected Input**: Passwords must only be entered into the masked password field in the UI.

---

## Deutsch

### 1. Physische Anschlüsse & Farbcodierung
Bei Betrieb als reines DSL-Modem vor einem nachgeschalteten Router gilt folgende Port-Zuordnung:

| Farbe | Bezeichnung | Verbindung | Funktion und Regel |
|---|---|---|---|
| **Rot** | WAN / Routeranschluss | **WAN-Port** des nachgeschalteten Routers | Reiner DSL-Datenverkehr (Bridge-Modus / PPPoE-Passthrough). **Keine Weboberfläche oder Administration über diesen Port.** |
| **Gelb** | LAN / Verwaltung | **Netzwerkswitch** im lokalen Verwaltungsnetz | Dedizierter Verwaltungszugriff und Home-Assistant-Telemetrie. |
| **Grau** | DSL | **DSL-/Telefonleitung** (TAE/Dose) | Hochfrequenz-DSL-Signal der Teilnehmeranschlussleitung. |

### 2. Schritt-für-Schritt-Einrichtung
1. **Direktanschluss**: PC per Ethernetkabel am **gelben LAN-Port** anschließen und Weboberfläche unter der Werks-IP öffnen.
2. **Feste IP vergeben**: Dem LAN-Port eine freie feste IPv4-Adresse (`<MODEM-LAN-IP>`) aus dem lokalen Verwaltungsnetz/VLAN zuweisen (außerhalb des DHCP-Pools).
3. **DHCP zwingend deaktivieren**: Den internen DHCP-Server des ZTE H186 in den LAN-Einstellungen deaktivieren, **bevor** der gelbe Port mit dem Switch verbunden wird (Vermeidung von Rogue DHCP).
4. **Speichern & Prüfen**: Einstellungen speichern und Erreichbarkeit unter `http://<MODEM-LAN-IP>` testen.
5. **Mit Switch verbinden**: Gelben Port mit dem Switchport im Verwaltungsnetzwerk verbinden.
6. **Zugriff**: Zukünftiger Zugriff erfolgt ausschließlich über `<MODEM-LAN-IP>` am gelben Port.

### 3. Bezug zur Home-Assistant-Integration
- Home Assistant benötigt Zugriff auf `<MODEM-LAN-IP>` über Port 80 (HTTP).
- Konfiguration in Home Assistant unter **Einstellungen > Geräte & Dienste > Integration hinzufügen > ZTE H186 DSL Modem**.
- Zugangsdaten nur in den dafür vorgesehenen geschützten Eingabefeldern hinterlegen.
