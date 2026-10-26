# ZTE H186: lokale DSL-Leitungswerte in Home Assistant

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

## Zweck und Umfang

Das Projekt liest DSL-Leitungswerte eines kompatiblen ZTE-H186-Modems ueber dessen
lokale Weboberflaeche. Ein Python-Client meldet sich an, liest die DSL-XML-Daten und
liefert sie gemeinsam an Home Assistant. Weder eine Cloud noch MQTT sind erforderlich.
Es werden keine DSL-, Router-, WLAN- oder WAN-Einstellungen veraendert. Der Login
erzeugt jedoch eine Sitzung auf dem Modem und ist daher nicht voellig zustandslos.

Das Home-Assistant-Paket erzeugt einen Abrufsensor und 26 Mess-/Textsensoren.
Diese sind Leitungsdaten, keine Messung des aktuellen Datenverkehrs und kein
Internet-Speedtest. Die 26 Felder entsprechen der beigefuegten Bash-Vorlage,
nicht einer vollstaendigen Auflistung aller moeglichen Firmwarefunktionen.

Diese Beschreibung enthaelt keine installationsbezogenen Adressen, Netzbereiche,
Zugangsdaten oder Links zu einer privaten Home-Assistant-Instanz. Die persoenliche
Urheberangabe ist ausdruecklich beabsichtigt. Der restliche Quellbestand muss vor
Veroeffentlichung separat geprueft werden, siehe Abschnitt Veroeffentlichung.

## Dateien

| Datei | Aufgabe |
|---|---|
| [custom_components/zte_h186](../custom_components/zte_h186) | Home Assistant Custom Integration (HACS / UI Config Flow) |
| [zte-h186-stats.py](zte-h186-stats.py) | Python-Client mit Login, Parser, Netzpruefung und JSON-Ausgabe |
| [zte-h186-package.yaml](zte-h186-package.yaml) | Gemeinsamer Command-Line-Abruf und 26 Template-Sensoren |
| [zte-h186-stats.sh](zte-h186-stats.sh) | Urspruengliche interaktive Feldreferenz, nicht Teil des HA-Laufzeitwegs |
| [zte-h186-credentials.example.json](zte-h186-credentials.example.json) | Optionale JSON-Strukturvorlage, vor Veroeffentlichung auf eigene Werte pruefen |
| [tests/test_zte_h186.py](tests/test_zte_h186.py) | Netzfreie Unittests mit synthetischen Antworten |
| [README.md](../README.md) | Kompakte Installations- und Betriebsanleitung |

## Architektur

Das Projekt unterstützt zwei Einbindungsvarianten für Home Assistant:

1. **Home Assistant Custom Integration (`custom_components/zte_h186`)**:
   - Native Integration mit UI Config Flow (**Einstellungen > Geräte & Dienste > Integration hinzufügen**)
   - Automatisches Erstellen von 27 Sensoren, Binärsensoren und Diagnose-Button
   - Zentraler asynchroner DataUpdateCoordinator mit Session-Caching
   - Unterstützt HACS und automatische Reorganisation bei IP-/Passwort-Änderung

2. **Klassisches YAML-Paket (`zte-h186-package.yaml`)**:
   - Command-Line-Prozessabruf (`zte-h186-stats.py`) alle 300 Sekunden
   - Bereitstellung von Abrufsensor und Template-Sensoren
   - Für rein dateibasierte Umgebungen ohne Custom Components

```text
Home Assistant Core
  -> Custom Integration (custom_components/zte_h186)
     -> Config Flow (Host, Username, Password)
     -> DataUpdateCoordinator (asynchrone aiohttp-Abfragen)
     -> 27 Sensor-Entitäten, 2 Binärsensoren, 1 Action-Button
  -> ODER command_line YAML-Paket:
     -> Python-Prozess (zte-h186-stats.py)
     -> gemeinsames JSON mit Status, Zeitpunkt und Daten
     -> 26 Template-Sensoren
```

## Voraussetzungen und Kompatibilitaet

- Ein berechtigt verwaltetes Modem mit kompatibler Weboberflaeche. Andere ZTE-Modelle,
  Provider-Firmware, Bonding und mehrere gleichnamige DSL-Instanzen sind nicht zugesagt.
- Der Benutzername ist im Python-Client fest `admin`. Andere Benutzer sind nicht
  konfigurierbar. Es muss der mehrstufige Token-/SID-Login dieser Firmware vorliegen.
- Python 3 im tatsaechlichen Home-Assistant-Core-Ausfuehrungskontext. Fuer den
  primaeren YAML-Secretsweg ist PyYAML erforderlich; die HTTP-Verarbeitung nutzt die
  Standardbibliothek. Kein `pip` in einen laufenden HA-Core nachinstallieren.
- Zugriff auf HA-Konfigurationsdateien und eine Sicherung vor Aenderungen.
- Eine literale IPv4-Managementadresse, HTTP-Standardport und die passende lokale
  Quelladresse. HTTPS, DNS-Namen, eigene Ports und Proxybetrieb sind nicht implementiert.

Die bisherige Abnahme umfasste Home Assistant Core 2026.10.2 und lokale Offline-Tests
mit Python 3.14. Eine allgemeine Mindestversion oder Kompatibilitaet mit allen anderen
HA-/Python-/Firmwareversionen wurde nicht bestimmt.

### Netzfreigabe vor der Uebernahme

Die aktuelle Implementierung enthaelt eine installationsspezifische Netzfreigabe in
`local_source_address()`, einschliesslich zugehoeriger Fehlertexte und Testdaten.
Sie wird nicht aus den Zugangsdaten geladen und ist nicht per CLI konfigurierbar.
Das Eintragen einer anderen Modemadresse allein reicht daher nicht fuer andere Netze.

Vor Nutzung in einer anderen Installation muss eine gepruefte Kopie des Clients auf
das eigene, eng begrenzte Managementnetz angepasst werden, einschliesslich der
zugehoerigen positiven und negativen Tests. Ziel und tatsaechliche Quelladresse muessen
beide zugelassen bleiben. Die Netzpruefung weder entfernen noch pauschal erweitern.
Diese Beschreibung nennt absichtlich nicht die Werte einer bestehenden Installation.

Die Quelle wird ueber die lokale Routenwahl ermittelt und die HTTP-Verbindung daran
gebunden. Ein erfolgreicher Zugriff von einem Entwicklungsrechner oder einer Terminal-App
beweist deshalb keinen Zugriff aus Core. Eine App ist ein anderer Ausfuehrungskontext.
Keine Firewall-, Routing- oder Proxy-Umgehung verwenden.

## Verkabelung und lokale Verwaltung des Modems

Diese Anleitung beschreibt die physische Verkabelung und die netzwerkseitige Einrichtung für den zuverlässigen Betrieb des ZTE H186 als reines DSL-Modem vor einem nachgeschalteten Router bei gleichzeitigem lokalem Managementzugriff.

### Anschlüsse und Farbcodierung

Die Anschlüsse des ZTE H186 übernehmen getrennte Rollen im Heim- und Betriebsnetzwerk:

| Port / Farbmarkierung | Bezeichnung | Verbindung | Funktion und Datenfluss |
|---|---|---|---|
| **Rot** | WAN / Routeranschluss | Mit dem **WAN-Port** des nachgeschalteten Routers verbinden | Leitet die reine DSL-Verbindung (Bridge-Modus / PPPoE-Passthrough) an den Hauptrouter weiter. Über diesen Port findet **keine** lokale Geräteverwaltung oder Weboberflächen-Anmeldung statt. |
| **Gelb** | LAN / Verwaltung | Mit einem **Netzwerkswitch** im lokalen Verwaltungsnetz verbinden | Dient ausschließlich dem administrativen Zugriff auf die Weboberfläche sowie der lokalen Telemetrieabfrage durch Home Assistant. |
| **Grau** | DSL | Mit der **DSL-/Telefonleitung** (TAE/Splitter/Anschlussdose) verbinden | Führt das Hochfrequenz-DSL-Signal der Teilnehmeranschlussleitung direkt an das Modem. |

> **Hinweis zu Herstellerunterlagen und Modellabweichungen:**  
> Die oben genannte Farbkodierung (Grau = DSL, Rot = WAN, Gelb = LAN) entspricht der geläufigen Werks- und Gehäuseausführung des ZTE H186. Je nach Distributor, Hardware-Revision oder Provider-Variante können einzelne Geräte abweichende Markierungen aufweisen (beispielsweise neutrale Buchsen mit eingeprägter Beschriftung wie `DSL`, `WAN` bzw. `LAN1` statt farbiger Ringe). Prüfen Sie vor dem Anstecken stets die Beschriftung direkt an den Buchsen des vorhandenen Geräts und gleichen Sie diese mit den zugehörigen Herstellerunterlagen ab.

---

### Schritt-für-Schritt-Einrichtung der lokalen Verwaltung

Um IP-Adresskollisionen im Produktivnetz zu verhindern und einen stabilen Abruf zu gewährleisten, wird das Modem vor der Einbindung in das Hausnetz vorkonfiguriert:

1. **Initialer Direktzugriff:**  
   Falls erforderlich (z. B. bei Neugeräten, nach einem Werksreset oder bei unbekannter Vorbelegung), schließen Sie zunächst einen PC oder Laptop direkt mit einem Ethernetkabel am **gelben LAN-Anschluss** an. Öffnen Sie die Weboberfläche des Modems im Webbrowser über die aktuell gültige bzw. werksseitige LAN-IP.

2. **Feste IP-Adresse im lokalen Verwaltungsnetz zuweisen:**  
   Weisen Sie dem LAN-Anschluss des ZTE H186 in den lokalen Netzwerkeinstellungen eine freie, feste IPv4-Adresse (`<MODEM-LAN-IP>`) aus Ihrem lokalen Verwaltungsnetz (z. B. Management-Subnetz oder Administrations-VLAN) zu.  
   - Wählen Sie die Subnetzmaske (`<SUBNETZ-MASKE>`) passend zu Ihrem Verwaltungsnetzwerk.  
   - Stellen Sie sicher, dass die vergebene `<MODEM-LAN-IP>` außerhalb des dynamischen DHCP-Vergabebereichs (DHCP-Pool) anderer Netzwerkgeräte liegt und keine Adresskonflikte mit bestehenden festen IP-Adressen im Netz entstehen.

3. **DHCP-Server des ZTE H186 deaktivieren:**  
   Deaktivieren Sie den integrierten DHCP-Server des ZTE H186 in den LAN-Einstellungen zwingend, **bevor** der gelbe Anschluss mit dem Switch des produktiven Netzwerks verbunden wird.  
   - *Hintergrund:* Zwei aktive DHCP-Server im selben Netzwerksegment ("Rogue DHCP") führen zu unkontrollierten Adressvergaben und massiven Verbindungsabbrüchen von Clients im Heimnetz.  
   - Der DHCP-Server des nachgeschalteten Hauptrouters bleibt unverändert aktiv und verwaltet weiterhin zentral alle regulären Netzwerk-Clients.

4. **Einstellungen speichern und neue Adresse aufrufen:**  
   Speichern Sie die geänderten Einstellungen auf dem Modem. Passen Sie die IP-Adresse des Test-PCs an das gewählte Verwaltungsnetz an und rufen Sie die Modemoberfläche im Browser unter der neuen statischen Adresse `http://<MODEM-LAN-IP>` auf, um die einwandfreie Erreichbarkeit zu prüfen.

5. **Verbindung mit dem Verwaltungsnetzwerk herstellen:**  
   Verbinden Sie den **gelben LAN-Anschluss** nun mit einem Switchport im passenden lokalen Verwaltungsnetzwerk.

6. **Zukünftiger Anmeldepfad:**  
   Das spätere Login sowie sämtliche Sensorabfragen erfolgen ausschließlich über die konfigurierte LAN-IP (`<MODEM-LAN-IP>`) am gelben LAN-Port – niemals über den roten WAN-Anschluss.

---

### Bezug zur Home-Assistant-Integration

Home Assistant fragt die DSL-Telemetriedaten lokal über die konfigurierte Management-Schnittstelle ab:

1. **Netzwerkerreichbarkeit aus Home Assistant:**  
   - Die in Home Assistant hinterlegte Modemadresse muss der erreichbaren lokalen LAN-IP (`<MODEM-LAN-IP>`) entsprechen.  
   - Die Home-Assistant-Instanz (z. B. auf Home Assistant OS / HAOS) benötigt netzwerkseitigen Zugriff auf diese LAN-IP über Port 80 (HTTP). Werden Home Assistant und das Modem in unterschiedlichen VLANs oder Subnetzen betrieben, müssen zwischengeschaltetes Routing und Firewall-Regeln den Zugriff auf `<MODEM-LAN-IP>` explizit gestatten.

2. **Hinterlegen der Zugangsdaten in der Home-Assistant-Integration:**  
   In Home Assistant wird die Verbindung über die vorhandene Integration eingerichtet:  
   - Navigieren Sie zu **Einstellungen > Geräte & Dienste**.  
   - Klicken Sie auf **Integration hinzufügen** und suchen Sie nach **ZTE H186 DSL Modem**.  
   - Hinterlegen Sie im Einrichtungsdialog die folgenden Parameter:  
     - **IP-Adresse oder Hostname** (`host`): Die feste LAN-IP des Modems (`<MODEM-LAN-IP>`).  
     - **Benutzername** (`username`): Der Benutzername der Weboberfläche (Voreinstellung: `admin`).  
     - **Passwort** (`password`): Das administrative Kennwort der Modem-Weboberfläche.  
   - *Geschützte Speicherung:* Das Passwort wird im Einrichtungsdialog ausschließlich in das dafür vorgesehene maskierte Passwortfeld eingetragen. Home Assistant speichert diese Zugangsdaten geschützt im internen Konfigurationseintrag (`ConfigEntry`). Zugangsdaten dürfen niemals in ungesicherten Skripten, Automatisierungen oder Klartextdateien hinterlegt werden.

3. **Klassischer Weg (YAML-Paket / Secrets):**  
   Wird alternativ das legacy YAML-Paket verwendet, werden die Werte ausschließlich in `/config/secrets.yaml` als sichere Referenz hinterlegt:  
   ```yaml
   zte_h186_host: "<MODEM-LAN-IP>"
   zte_h186_password: "<MODEM-PASSWORT>"
   ```

4. **Vorgesehene Einrichtung und tatsächlich geprüfter Zustand:**  
   - *Vorgesehene Einrichtung:* Die hier beschriebene Zwei-Kabel-Topologie (roter WAN-Port für Internetdatenverkehr zum Router; gelber LAN-Port für lokale Verwaltung und Home-Assistant-Telemetrie über Switch/VLAN) stellt die herstellerkonforme und netzwerktechnisch saubere Trennung für den Bridge-Betrieb dar.  
   - *Geprüfter Zustand:* Die Software-Integration und Protokollabläufe wurden im Rahmen der Testsuite und lokaler Schnittstellentests (u. a. Token-/Challenge-Handshake, Session-Handling, Coordinator-Updates, Entity-Registry) evidenzbasiert validiert. Die tatsächliche physische Verkabelung, VLAN-Segmentierung, Switchport-Konfiguration und Firewall-Freigaben müssen in der jeweiligen Zielumgebung vor Ort anhand der individuellen Netzwerktopologie verifiziert werden.

## Installation

### 1. Sichern und Zugangsdaten hinterlegen

Zuerst ein HA-Backup und eine gezielte Kopie der betroffenen Konfiguration erstellen.
Wiederherstellungsweg und Zugriff ausserhalb der HA-Oberflaeche sicherstellen.
Bestehende Dateien nicht ersetzen und keine fremden Pakete nebenbei aktivieren.

In der bestehenden HA-Secretsdatei die Schluessel `zte_h186_host` und
`zte_h186_password` ausschliesslich am Ziel mit den eigenen Werten hinterlegen.
Die Adresse ist eine reine IPv4-Zeichenkette, keine URL. Das Passwort als
YAML-Zeichenkette quotieren; in einfachen Anfuehrungszeichen wird ein enthaltenes
einfaches Anfuehrungszeichen verdoppelt. Passwort-Leerzeichen werden nicht entfernt.
Keine doppelten Schluessel und keine verschachtelten `!secret`-Verweise verwenden.

Im Core liegt die Datei unter `/config/secrets.yaml`; eine Verwaltungs-App kann
dieselbe Konfiguration unter `/homeassistant/secrets.yaml` zeigen. Tatsächliche
Mounts vor Ort pruefen. Geheimnisdateien nur dem benoetigten Ausfuehrungskonto
zugaenglich machen, beispielsweise Dateimodus `600` bei passendem Eigentuemer.
Bestehende Dateirechte nicht rekursiv und pauschal aendern.

### 2. Client bereitstellen und pruefen

Den Client nach `/config/scripts/zte-h186/zte-h186-stats.py` uebertragen.
Ein Ausfuehrungsbit ist nicht noetig, da `python3` ihn startet. Nur administrative
Schreibrechte zulassen und die uebertragene Datei beispielsweise per SHA-256 vergleichen.

Im echten Core-Kontext zunaechst ohne Netzwerkzugriff pruefen:

```sh
python3 /config/scripts/zte-h186/zte-h186-stats.py --secrets-file /config/secrets.yaml --check-config
```

Dies prueft das Zugangsdatenformat, nicht die Route, das Passwort oder das Modem.
Danach genau einen geschuetzten Abruf im zugelassenen Core-Kontext pruefen:

```sh
python3 /config/scripts/zte-h186/zte-h186-stats.py --secrets-file /config/secrets.yaml --ha-json
```

Erfolg verlangt `status: ok`, einen neuen UTC-Zeitpunkt und alle zehn Pflichtwerte.
Bis zu 16 optionale Werte kommen hinzu. Exitcode `0` allein ist kein Erfolgsnachweis.
Ist ein direkter Core-Aufruf nicht verfuegbar, den Client nicht ersatzweise aus einer
beliebigen App starten: nach gepruefter Paketaktivierung den echten Abrufsensor nutzen.

### 3. Paket einbinden

Das Paket nach `/config/packages/zte-h186.yaml` uebertragen. Eine bestehende
Package-Einbindung weiterverwenden. Nur wenn noch keine passende Einbindung existiert,
das Paket gezielt unter dem vorhandenen einzigen `homeassistant:`-Block einordnen:

```yaml
homeassistant:
  packages:
    zte_h186: !include packages/zte-h186.yaml
```

Das ist ein generisches Strukturbeispiel ohne private Konfigurationswerte. Bestehende
Unterpunkte erhalten; niemals einen zweiten `homeassistant:`-Block anlegen oder eine
vorhandene `packages:`-Include-Struktur ueberschreiben. Bei bereits aktiver automatischer
Package-Einbindung keine zweite Einbindung derselben Datei hinzufuegen.

Der Paketbefehl liest die Secretsdatei ueber einen statischen Pfad. Passwoerter werden
nicht in Shellargumente oder YAML-Befehlstexte eingesetzt. Ein Poll laeuft alle 300 Sekunden,
der aeussere Command-Timeout betraegt 90 Sekunden. Pfade nur dann anpassen, wenn der
eigene Core tatsaechlich andere Mounts verwendet.

### 4. Validieren und aktivieren

Die native HA-Konfigurationspruefung ausfuehren. Bei Fehlern nicht aktivieren.
Ist ein erstmaliger Core-Neustart erforderlich, ihn bewusst und gesondert freigeben.
Bei bereits geladenen Komponenten nach gueltiger Pruefung `command_line.reload` und
`template.reload` ueber die HA-Aktionen verwenden. Das sind komponentenweite Reloads;
weitere dort konfigurierte Entitaeten koennen ebenfalls betroffen sein.

Unter **Einstellungen > Geraete & Dienste > Entitaeten** nach `ZTE H186` suchen.
Alternativ unter **Entwicklerwerkzeuge > Zustaende** nach `sensor.zte_h186_` filtern.
Erwartet werden 27 Entitaeten. Bei ID-Kollisionen die tatsaechlichen IDs und die
Paketreferenzen abgleichen, statt vorhandene Entitaeten blind umzubenennen.
Der Quellsensor heisst standardmaessig `sensor.zte_h186_abruf`.

Nach mindestens einem regulären Pollintervall einen neuen automatischen `sampled_at`
nachweisen. Werte und Einheiten gegen die Modemoberflaeche vergleichen. Kontinuierliche
Messwerte koennen in den Entitaetseinstellungen mit einer Nachkommastelle dargestellt
werden; Rohdaten werden dafuer nicht gerundet. Zaehler bleiben ganzzahlig.

## Vollstaendige Feldreferenz

Die Spalte Schluessel nennt die normalisierten Eintraege in `data`. Entity-IDs werden
aus den Anzeigenamen erzeugt und koennen insbesondere bei Daempfung oder Profil vom
Schluesselnamen abweichen. Bestehende Registry-IDs haben Vorrang.

| Schluessel | XML-Feld | Umrechnung / Einheit | Pflicht |
|---|---|---|---|
| `downstream_sync` | `Downstream_current_rate` | /1000, Mbit/s | ja |
| `upstream_sync` | `Upstream_current_rate` | /1000, Mbit/s | ja |
| `downstream_max` | `Downstream_max_rate` | /1000, Mbit/s | ja |
| `upstream_max` | `Upstream_max_rate` | /1000, Mbit/s | ja |
| `downstream_snr` | `Downstream_noise_margin` | /10, dB | ja |
| `upstream_snr` | `Upstream_noise_margin` | /10, dB | ja |
| `downstream_attenuation` | `Downstream_attenuation` | /10, dB | ja |
| `upstream_attenuation` | `Upstream_attenuation` | /10, dB | ja |
| `profile` | `CurrentProfile` | Text | ja |
| `modulation` | `Module_type` | Text | ja |
| `dsl_status` | `Status` | Text | nein |
| `downstream_power` | `Downstream_power` | /10, dBm | nein |
| `upstream_power` | `Upstream_power` | /10, dBm | nein |
| `data_path` | `Data_path` | Text | nein |
| `downstream_interleave_depth` | `DownInterleavedepth` | Ganzzahl | nein |
| `upstream_interleave_depth` | `UpInterleaveDepth` | Ganzzahl | nein |
| `downstream_interleave_delay` | `DownInterleaveDelay` | ms | nein |
| `upstream_interleave_delay` | `UpInterleaveDelay` | ms | nein |
| `downstream_inp` | `DownstreamInp` | /10, Symbole | nein |
| `upstream_inp` | `UpstreamInp` | /10, Symbole | nein |
| `showtime` | `Showtime_start` | Ganzzahl, s | nein |
| `link_encapsulation` | `tLinkEncapsulationUsed` | Text | nein |
| `downstream_crc` | `DownCrc_errors` | Ganzzahl, Fehler | nein |
| `upstream_crc` | `UpCrc_errors` | Ganzzahl, Fehler | nein |
| `downstream_fec` | `Fec_errors` | Ganzzahl, Fehler | nein |
| `upstream_fec` | `Atuc_fec_errors` | Ganzzahl, Fehler | nein |

Firmwareeinheiten, insbesondere INP, Delay und Showtime, sowie die Down-/Up-Richtung
der Fehlerzaehler muessen unabhaengig am eigenen Geraet bestaetigt werden. Die Angaben
folgen der Bash-Vorlage und sind keine allgemeingueltige Firmwaregarantie.
Showtime nicht als Geraete-Uptime interpretieren. CRC/FEC erhalten ohne belegte
Resetsemantik keine `state_class`; Resync-Zaehler sind nicht implementiert.

Fehlende oder ungueltige Pflichtwerte machen den Abruf ungueltig. Fehlende oder ungueltige
Zusatzwerte werden ausgelassen; nur ihre jeweiligen Sensoren sind dann nicht verfuegbar.
Es werden keine fehlenden Messungen als echte Nullwerte ausgegeben. Negative SNR und
Leistung sind zulaessig, negative Raten, Daempfung und Zaehler nicht. Zaehler und
Interleaving-Tiefen muessen nichtnegative Ganzzahlen sein.

## Loginprotokoll und Sicherheitsgrenzen

1. Die Startseite liefert den JavaScript-Session-Token mit Hex-Escapes.
2. `function_module/login_module/login_page/logintoken_lua.lua` liefert den Login-Token.
3. SHA-256 wird ueber Passwort und Login-Token berechnet; Benutzer, Hash, Aktion und
   Session-Token werden mit Cookie-Unterstuetzung an die Startseite gepostet.
4. Eine nichtleere SID ist erforderlich. HTTP 302/303 direkt beim Login wird nur mit
   dieser SID akzeptiert. Kein `Location`-Ziel wird aufgerufen; andere Redirects bleiben
   gesperrt. Eine SID allein gilt noch nicht als erfolgreicher Datenabruf.
5. Die festgelegte DSL-Seite `getpage.lua` mit DSL-Statusparametern muss den erwarteten
   Endpunkt enthalten. Anschliessend wird `common_page/internet_dsl_interface_lua.lua`
   gelesen und die XML-Antwort auf Sitzung, Eindeutigkeit und Pflichtdaten geprueft.

Alle HTTP-Abfragen bleiben am geprueften Ziel und an der geprueften Quelladresse.
Ein UDP-Routensocket ermittelt die lokale Quelle, ohne selbst ein Anwendungsdatagramm
zu senden. Proxys sind deaktiviert. Eine HTTP-Antwort ist auf 1 MiB begrenzt;
pro Request gelten 15 Sekunden Socket-Timeout. Unter Linux begrenzt eine Deadline
den Abruf samt Sperre auf insgesamt 70 Sekunden. Unter anderen Plattformen sind
nicht alle Linux-Schutzmechanismen verfuegbar; HA-Laufzeitweg ist Linux.

Eine nichtblockierende `flock`-Sperre im temporaeren Verzeichnis verhindert parallele
Clientabrufe im selben Container. Eigentuemer, regulaerer Dateityp, Linkanzahl und
Symlinkschutz werden geprueft. Die Sperrdatei nicht waehrend eines Abrufs loeschen.
Das Betriebssystem gibt die eigentliche Sperre beim Prozessende frei.

YAML wird mit SafeLoader sowie Duplikat-/Tagpruefung gelesen. XML-Dokumentdefinitionen,
Entities, doppelte bekannte DSL-Felder, nichtendliche Zahlen und ungueltige Texte
werden abgewiesen. Der YAML-Eingabetext ist ebenfalls groessenbegrenzt.

Das Modem verwendet unverschluesseltes HTTP. Der tokengebundene Passworthash ersetzt
keine TLS-Serverauthentisierung und schuetzt nicht vollstaendig vor Angreifern im LAN.
Secretsdatei, alternative JSON-Datei und Backups enthalten Klartext-Geheimnisse.
HA-Administratoren und Apps mit Konfigurationszugriff bleiben Vertrauensgrenzen.
Python garantiert kein sicheres Loeschen von Geheimnissen aus dem Prozessspeicher.

Kein belegter Logoutendpunkt ist implementiert. Parallele Browseranmeldungen und
Sessionlimits sind gesondert zu pruefen. Es gibt keine direkte Login-Wiederholung;
spaetere automatische Polls mit falschem Passwort koennen dennoch eine Sperre ausloesen.
Bei Authentifizierungsfehlern deshalb zuerst Polling abschalten.

Die Bash-Referenz ist kein gleichwertig gehaerteter Produktionsclient: Sie zeigt
Session-/Login-Token und SID an, folgt Login-Redirects und besitzt nicht dieselben
Netz-, Deadline- und Eingabeschutzmassnahmen. Sie wird vom Paket nicht gestartet und
wurde bei der beschriebenen Abnahme nicht ausgefuehrt. Ihre rohe Ausgabe nicht teilen.

## Ausgabe, Fehler und Datenalter

`--ha-json` liefert bei Erfolg `status: ok`, `sampled_at` als UTC-Zeitpunkt und `data`
mit normalisierten Werten. Bei erkannten Fehlern liefert es `status: error`,
`error_code`, `sampled_at: null` und `data: {}`. Im HA-Modus ist der Exitcode dabei
bewusst `0`, damit der Abrufsensor alte Attribute ersetzen kann.
Stderr enthaelt nur einen generischen Fehlerhinweis. Harte Prozessabbrueche oder
Fehler vor Programmeinstieg koennen diese Fehlerhuelle nicht garantieren.

| Kategorie | Vorgehen |
|---|---|
| `network_denied` | Ziel, Netzfreigabe und wirklichen Core-Ausfuehrungskontext pruefen; Schutz nicht entfernen |
| `connection_error` | Lokale Route, Modemverfuegbarkeit und Zugriff aus Core untersuchen |
| `http_error` | Sicheren HTTP-Status und Request-Phase pruefen, keine Antwortseiten veroeffentlichen |
| `auth_failed` | Polling stoppen, eigenes Passwort und Firmware/Login lokal pruefen |
| `invalid_data` | Pflichtfelder, Einheiten und Mehrfachinstanzen pruefen |
| `config_invalid` | Eigene Datei, Schluessel, Typen, Duplikate und YAML-Tags pruefen |
| `timeout` | Erreichbarkeit und Laufzeit pruefen, nicht blind die Grenzen erhoehen |
| `busy` | Bereits laufenden Abruf bzw. lokale Sperrdateieigenschaften pruefen |
| `local_error`, `protocol_error` | Ausfuehrungsumgebung und Firmwarekompatibilitaet lokal untersuchen |

Die Kategorien sind grob; einzelne Format-/Routingfehler koennen unter allgemeinere
Kategorien fallen. Bei HTTP-Fehlern werden nur `http_status` und eine feste
`request_stage` ausgegeben: `login_page`, `login_token`, `login`, `dsl_page`, `dsl_data`.
Keine Antwortinhalte, Token, Cookies, Hashes oder Weiterleitungsziele werden exportiert.

Die Templates verlangen einen erfolgreichen Abruf, einen nicht zukuenftigen Zeitpunkt
und ein Alter unter 600 Sekunden. Eine minuetliche Neubewertung sperrt veraltete Werte
auch ohne neue Antwort spaetestens nach knapp elf Minuten. Ein stehengebliebenes `ok`
am Abrufsensor ist allein kein Frischenachweis. Bei Fehlern oder Alter werden Sensoren
nicht verfuegbar; es werden keine Ersatznullen erfunden.

## Alternative CLI-Wege

`--json` liefert erkannte rohe XML-Werte als Zeichenketten; ohne Ausgabeoption wird
lesbarer Text erzeugt. `--credentials` liest statt HA-Secrets eine geschuetzte
JSON-Datei mit `host` und `password`. Beide Dateioptionen schliessen sich aus.
`--ha-json` und `--check-config` benoetigen eine dieser Dateioptionen.

Ohne Dateioption bleibt der alte `age`-Ladeweg erhalten: benachbarte Dateien nach den
Mustern `secrets/zte-ipaddress-*.age` und `secrets/zte-admin-password-*.age`, jeweils
lexikografisch letzter Treffer; Identity ueber `--identity`, `AGE_IDENTITY` oder den
Standardpfad `~/.config/age/keys.txt`. Dafuer ist das externe Programm `age` erforderlich.
Dieser Weg ist nicht Grundlage des HA-Pakets und erfordert keine Nachinstallation im Core.

## Entwicklung und bisherige Abnahme

Aus dem Projektverzeichnis mit einer lokalen Python-Umgebung und PyYAML:

```sh
python -B -m unittest discover -s tests -p test_zte_h186.py -v
```

PyYAML fuer die Entwicklungsumgebung installieren, falls es dort fehlt, nicht in einen
laufenden HA-Core. Tests verwenden synthetische Geheimnisse und Antworten und sperren
echte Socket-/HTTP-Aufrufe. Sie pruefen unter anderem Ziel-/Quellgrenzen, Quellbindung,
Token-/SID-Login, Redirectbehandlung, YAML-Sicherheit, XML-/Antwortgrenzen, Fehlerh uelle,
Zahlenvalidierung, optionale Felder und den exakten 26-Feldvertrag zwischen Bash,
Python und Paket. In der bisherigen Abnahme bestanden 30 Offline-Tests.

Zusaetzlich wurden native HA-Konfigurationspruefung, ein echter Core-Abruf aller 26 Felder,
27 Registry-Entitaeten und die Uebereinstimmung aller 26 Template-Zustaende mit den
gemeinsamen Daten geprueft. Dateiuebertragungen wurden per SHA-256 rueckgelesen und
gezielte Backups vor Aenderungen angelegt. Der echte Login erforderte die beschriebene
302/303-Behandlung mit SID; Redirectziele wurden dabei weiterhin nicht aufgerufen.

Noch nicht abschliessend abgenommen: automatischer Folgeabruf im bisherigen Pruefzeitraum,
unabhaengiger Einheiten-/Zaehlervergleich mit der Modemoberflaeche, Showtime-Semantik,
Sessionvertraeglichkeit, Firmwarevarianten, Anzeigepräzision und vollstaendige
Linux-Sperr-/Deadline-Grenzfalltests. Ein erfolgreicher Einzelabruf ersetzt dies nicht.
Keine unabhaengige Sicherheitszertifizierung oder allgemeine Firmwarefreigabe behaupten.

## Rueckbau und Aktualisierung

Vor Aktualisierungen betroffene Dateien sichern, neue Dateien pruefen und ihre Hashes
nach Uebertragung vergleichen. Native Konfigurationspruefung vor Reload/Neustart
ausfuehren. Das Paket, die dokumentierten Pfade und die eigene Netzfreigabe zusammenhalten.
Polling- oder Timeoutaenderungen muessen zur Frischepruefung und Sessionbelastung passen.

Zum Rueckbau nur die eigene ZTE-Paketeinbindung entfernen, Konfiguration pruefen und
Komponenten gezielt neu laden bzw. einen erforderlichen Neustart separat freigeben.
Andere Pakete und gemeinsame Includes erhalten. Erst nach Ende des Pollings Client
und ausschliesslich die eigenen ZTE-Secretschluessel entfernen. Niemals die gesamte
Secretsdatei loeschen. Bei Problemen die gezielt gesicherte Ausgangskonfiguration
wiederherstellen; ein Vollrestore ist nicht der erste Schritt.

## Veroeffentlichung

Diese Datei kann getrennt von privaten Instanzunterlagen verwendet werden. Sie ist
keine Freigabe, den gesamten uebergeordneten Workspace oder das aktuelle Verzeichnis
ungeprueft zu veroeffentlichen. Vor einem oeffentlichen Release:

1. Nur Client, Paket, bereinigte Feldreferenz/Vorlage, Tests und oeffentliche Dokumentation
   in einen getrennten Release-Stand uebernehmen. Private Exporte, Backups, Secrets,
   Screenshots, Logs und Hardware-/Instanznotizen nicht uebernehmen.
2. Fest eingetragene Netzwerte in Client, Fehlertexten, Tests und JSON-Vorlage auf einer
   separaten Release-Kopie anonymisieren oder durch eindeutig dokumentierte,
   nicht installationsbezogene Beispielwerte ersetzen. Die aktive Installation nicht
   fuer die Veroeffentlichung veraendern. Positiv-/Negativtests danach erneut ausfuehren.
3. Auch Kommentare, Dateinamen, URLs, Beispielausgaben, Archive und gegebenenfalls
   Versionshistorie auf private Adressen, Domains, Pfade, Token und Zugangsdaten pruefen.
   Eine reine Adresssuche ersetzt keine manuelle Inhaltspruefung.
4. Bash-Ausgaben weder als Diagnosebeleg noch als Screenshot veroeffentlichen. Einen
   erforderlichen Fehlerbericht auf Kategorie, HTTP-Status und feste Phase begrenzen.
5. Copyright-/SPDX-Zeilen unveraendert erhalten und die GPL-3.0-only-Lizenzpflichten
   fuer die verteilten Bestandteile beachten. Einen vollstaendigen Lizenztext im
   eigenstaendigen Release beilegen; diese Beschreibung ersetzt ihn nicht.

Im vorliegenden Dokument ist das generische Package-Beispiel absichtlich frei von
privaten Werten. Die Schluesselnamen, Standardpfade und Protokollendpunkte sind
technische Schnittstellen, keine echten Zugangsdaten.

## Quellen und Lizenz

- [Home Assistant: Command Line](https://www.home-assistant.io/integrations/command_line/)
- [Home Assistant: Template](https://www.home-assistant.io/integrations/template/)
- [Home Assistant: Packages](https://www.home-assistant.io/docs/configuration/packages/)
- [Home Assistant: Secrets](https://www.home-assistant.io/docs/configuration/secrets/)
- [SPDX: GPL-3.0-only](https://spdx.org/licenses/GPL-3.0-only.html)
- [GNU GPL Version 3: Lizenztext](https://www.gnu.org/licenses/gpl-3.0.html)

Die Copyright- und SPDX-Kennzeichnung am Dokumentanfang ist unveraendert zu erhalten.
