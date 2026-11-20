# Identity of the modem

A physical ZTE H186 is one device for its whole life, whatever its network address does. This page
records what identifies what, the rules the code follows, how existing installations are migrated and
what was found about the modem itself.

## What identifies what

| Thing | Identity | Stable? |
|---|---|---|
| Config entry (`unique_id`) | serial number of the modem (15 characters, read from the modem) | yes, printed on the device |
| Title in the integration list | `ZTE H186 (<serial>)` (a name chosen by the user is kept) | yes |
| Device in the device registry | identifier `(zte_h186, <serial>)`, with serial number, model, hardware and software version | yes |
| Entities | unique id `<serial>_<key>` | yes |
| Hardware address (MAC) | stored in `data["mac_address"]`, used only to recognise the modem in DHCP discovery | yes |
| **Network address** | stored in `data["host"]` only | **no**, it is data, not identity |

Before 1.5.0 the identity was the address (`unique_id`, title and entity ids of older installations contain
`192.168.10.2`), later the random id of the config entry. The first breaks with every new address; the
second survives an address change, but not removing and adding the integration again, and it identified
the config entry, not the modem. A modem that was reached under two names (IP address and host name) was
not recognised as one device.

## What the modem reports

After the login, `GET /getpage.lua?pid=1002&nextpage=ManagDiag_StatusManag_t.lp` (the status page) followed
by `GET /common_page/ManagReg_lua.lua` returns XML with `SerialNumber`, `MACAddress`, `ModelName`,
`HardwareVer`, `SoftwareVer`, `BootVer`, `ModelFirmwareVer` and `systemTime`. The second request is only answered
in a session that has requested the status page first (otherwise it answers `SessionTimeout`). Verified on
a real H186 on 2026-11-20; the MAC address agrees with the one seen on the network. The serial number is the
most stable identity available (assigned by the manufacturer, independent of the network); the MAC address
is only a second characteristic.

**The modem allows one admin session at a time.** A login while another session exists is refused with
"did not authorize the session", and a session that is not logged out stays occupied until it times out. Versions
before 1.5.0 never logged out, so after a reload, a restart or a setup dialog the next login was refused for
some minutes and Home Assistant started a re-authentication that was not needed. From 1.5.0 the client logs off
(`POST /` with `IF_LogOff=1`, the request of the web UI's logout link) when it is closed, after a failed setup and
before a dialog checks a running entry, and when Home Assistant stops (stopping does not unload the entries).

## Rules in the code

1. **A new entry takes the serial number from the modem.** The dialog logs in, reads the device information and
   sets `async_set_unique_id(serial)`; `_abort_if_unique_id_configured(updates={host})` makes a second attempt for a
   known modem update its address instead of adding a duplicate. A modem that reports no usable serial number is
   not accepted.
2. **Older entries are migrated at their next successful setup** (the serial number comes from the modem, so it
   cannot happen while the modem is unreachable): `unique_id`, title (if it was generated), `data` (serial number,
   MAC address), minor version 2; the entities' unique ids move from `<entry id>_<key>` to `<serial>_<key>` and the
   device identifier from `(zte_h186, <entry id>)` (or the address, in the oldest entries) to `(zte_h186, <serial>)`.
   The registries are migrated first and the entry last, independently of what the entry stores, and again at
   every setup: an entry that a reconfigure, an interrupted setup or a downgrade left half-way is healed, and an
   entity that an older version created a second time after a downgrade is removed in favour of the original.
   Entity ids, names, areas, history and customisations are untouched: only the unique id changes. A modem that cannot report its serial number at
   that moment leaves the entry as it is.
3. **The modem that answers must be the modem of the entry.** Every setup compares the serial number with the
   stored one. A different modem at the saved address stops the setup with a clear message and creates nothing;
   it is never mixed into the entry. The same check protects reconfigure and re-authentication (`wrong_device`).
4. **One modem, one entry.** A second entry for a modem that already has one stops with a message; it creates no devices.
5. **A changed address is only data.** The reconfigure dialog and DHCP discovery change `data["host"]`; identity and
   title stay. DHCP discovery (hardware address prefix) recognises a known modem by its stored MAC address and saves
   its new address; an unknown device is offered only if its login page says it is an H186 (the page title is shown
   without logging in). The login credentials are asked for in the usual dialog; the serial number is read after it.
6. **Dialogs release the single session.** Checking a running entry first logs its client off; the client logs in
   again by itself at the next poll.
7. **An entry whose identity was overwritten** (a downgrade) is put right at its next setup, registries included.
8. **The device keeps what it knows.** Serial number and versions that the modem did not report at this setup are
   not sent to the registry as empty values.

Known limit: an entry of an older version whose modem changed its address before the entry could read the serial
number has no way to recognise the modem; adding the modem then creates a second entry, and the old one stops with
the message that the modem is used by another entry. Reconfigure the old entry instead (it adopts the serial number).

## Decisions and rejected options

- **MAC address as the unique id:** rejected. It is shown on the network but the integration cannot read it
  from the network layer; the modem reports it only after a login, together with the better serial number.
  Network adapters can be replaced or share MACs; the serial number is the manufacturer's identity.
- **MAC address as a `connection` in the device registry:** not set. A network device that another integration
  (for example the router's) already knows by that MAC would be merged with this one; the serial number identifier
  is enough to find the device again.
- **Migrating while the modem is offline:** not possible, the serial number is not stored by older versions.
  An entry that has never been able to read it stays as it is until it can.
- **Minor, not major version:** the data stays readable by older code.
- **Reauth** keeps working as before and additionally refuses a different modem.
- **Removing and adding the integration again:** Home Assistant restores entity id, name and area from its
  registry of deleted entities for 30 days; after that they are created anew.
