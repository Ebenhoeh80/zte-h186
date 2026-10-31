# ZTE H186 Documentation Index / Dokumentationsübersicht

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

Welcome to the technical documentation repository for the **ZTE H186 DSL Modem Integration**. In accordance with project governance, all documentation is available in four official languages:

[🇬🇧 English](en/) | [🇩🇪 Deutsch](de/) | [🇫🇷 Français](fr/) | [🇪🇸 Español](es/)

---

## 🇬🇧 English Documentation

- **[Home Assistant Integration & Cabling Guide](en/HomeAssistant.md)**: Physical port wiring (Red WAN, Yellow LAN, Grey DSL), local management IP configuration, Home Assistant UI Config Flow setup, entity directory, and secrets.
- **[Setup & Credential Methods](en/Setup.md)**: Credential configuration via JSON files, CLI flags, Environment variables, Age-encrypted at-rest files, and Home Assistant UI.
- **[Modem Protocol](en/Protocol.md)**: Reverse-engineered 5-step authentication sequence, session token decoding, and DSL XML endpoint details.
- **[Security & Audit](en/Security.md)**: SSRF prevention, age identity protection, secret storage, and public release hygiene.

---

## 🇩🇪 Deutsche Dokumentation

- **[Home-Assistant-Integration & Verkabelungsanleitung](de/HomeAssistant.md)**: Physische Portverkabelung (Rot WAN, Gelb LAN, Grau DSL), Zuweisung fester Verwaltungs-IPs, UI Config Flow in Home Assistant, Entitätenübersicht und Secrets.
- **[Einrichtung & Zugangsdaten-Methoden](de/Setup.md)**: Konfiguration über JSON-Dateien, CLI-Argumente, Umgebungsvariablen, Age-Verschlüsselung und Home Assistant UI.
- **[Modem-Protokoll](de/Protocol.md)**: Dokumentation des 5-stufigen Anmeldeprozesses, Session-Token-Dekodierung und DSL-XML-Endpunkte.
- **[Sicherheit & Veröffentlichung](de/Security.md)**: SSRF-Schutz, Schutz lokaler Age-Schlüssel, Secrets-Handling und Prüfschritte vor Veröffentlichungen.

---

## 🇫🇷 Documentation Française

- **[Intégration Home Assistant & Guide de Câblage](fr/HomeAssistant.md)**: Câblage physique des ports (Rouge WAN, Jaune LAN, Gris DSL), configuration de l'IP statique de gestion, intégration dans Home Assistant via l'interface UI, liste des entités.
- **[Configuration & Méthodes d'Identifiants](fr/Setup.md)**: Configuration via fichier JSON, arguments CLI, variables d'environnement, chiffrement Age au repos et interface Home Assistant.
- **[Protocole du Modem](fr/Protocol.md)**: Séquence d'authentification en 5 étapes, décodage du jeton de session et point de terminaison XML DSL.
- **[Sécurité & Publication](fr/Security.md)**: Protection contre les attaques SSRF, gestion des clés d'identité Age, stockage sécurisé et audit avant publication.

---

## 🇪🇸 Documentación en Español

- **[Integración en Home Assistant y Guía de Cableado](es/HomeAssistant.md)**: Cableado físico de puertos (Rojo WAN, Amarillo LAN, Gris DSL), asignación de IP estática de gestión, configuración mediante interfaz de usuario (UI Config Flow) y directorio de entidades.
- **[Configuración y Métodos de Credenciales](es/Setup.md)**: Configuración mediante archivos JSON, argumentos CLI, variables de entorno, cifrado en reposo con Age e interfaz de Home Assistant.
- **[Protocolo del Módem](es/Protocol.md)**: Secuencia de autenticación en 5 pasos, decodificación de token de sesión y punto final XML DSL.
- **[Seguridad y Publicación](es/Security.md)**: Protección contra ataques SSRF, protección de identidades Age, almacenamiento seguro y auditoría antes del lanzamiento.
