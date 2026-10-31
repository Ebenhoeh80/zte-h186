# Intégration Home Assistant ZTE H186 (HACS)

<p align="center">
  <img src="images/icon.png" alt="ZTE H186 DSL Modem" width="240">
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/Ebenhoeh80/zte-h186)](https://github.com/Ebenhoeh80/zte-h186/releases)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Quality Scale: Bronze](https://img.shields.io/badge/Quality%20Scale-Bronze-brown.svg)](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
[![Languages: en, de, fr, es](https://img.shields.io/badge/Languages-en%20%7C%20de%20%7C%20fr%20%7C%20es-brightgreen.svg)](#internationalisation-i18n)

[English](README.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md)

Une intégration personnalisée asynchrone pour le **modem DSL ZTE H186**. Lit la télémétrie de ligne DSL en temps réel (débits de synchronisation, marge SNR, atténuation, compteurs d'erreurs CRC/FEC, profil et temps de fonctionnement Showtime) directement depuis l'interface web locale du modem.

---

## 🚀 Fonctionnalités

- **Configuration via l'interface UI (Config Flow)** : Configuration rapide directement dans l'interface utilisateur de Home Assistant (*Paramètres > Appareils et services > Ajouter une intégration*). Aucun YAML requis.
- **Flux de Reconfiguration** : Modifiez l'adresse IP, le nom d'hôte ou le mot de passe sans perdre vos identifiants d'entité, historiques ou tableaux de bord.
- **Flux d'Options** : Intervalle de scrutation configurable de 15 à 600 secondes (par défaut : 60 secondes).
- **Mise en cache de session & Efficacité** : Maintient la session active et gère automatiquement les expirations de session.
- **Prise en charge intégrale des 4 langues (i18n)** : Localisation en anglais, allemand, français et espagnol.
- **27 capteurs complets** :
  - **Bande passante et synchronisation** : Débit de synchronisation montant et descendant (Mbit/s), capacité maximale (Mbit/s), utilisation de la ligne (%).
  - **Qualité du signal** : Marge de bruit (SNR en dB), atténuation de ligne (dB), puissance de transmission (dBm).
  - **Trames & Latence** : Profil DSL (ex. 17a, 35b), standard de modulation (VDSL2), chemin de données (Fast/Interleaved), profondeur et délai d'entrelacement, protection contre le bruit impulsionnel (INP).
  - **Temps de fonctionnement & Erreurs** : Durée de synchronisation Showtime, erreurs CRC non corrigées, erreurs binaires FEC corrigées.
- **Capteurs binaires** :
  - `dsl_link` : État de la liaison physique DSL.
  - `line_noise_warning` : Alerte si la marge de bruit descend en dessous de 6,0 dB.
- **Bouton d'action** :
  - `refresh_stats` : Déclenche une mise à jour immédiate des statistiques.

---

## 📦 Installation via HACS

1. Ouvrez **Home Assistant**.
2. Allez dans **HACS** > **Intégrations**.
3. Cliquez sur le menu à trois points (⋮) en haut à droite et choisissez **Dépôts personnalisés**.
4. Saisissez l'URL :
   ```text
   https://github.com/Ebenhoeh80/zte-h186
   ```
5. Sélectionnez le type **Intégration** et cliquez sur **Ajouter**.
6. Téléchargez **ZTE H186 DSL Modem** et redémarrez Home Assistant.

---

## ⚙️ Configuration

1. Dans Home Assistant, allez dans **Paramètres** > **Appareils et services**.
2. Cliquez sur **Ajouter une intégration** et recherchez **ZTE H186 DSL Modem**.
3. Renseignez l'adresse IP (`<MODEM-LAN-IP>`), le nom d'utilisateur (`admin`) et le mot de passe.
4. Validez.

> 💡 **Câblage physique** : Consultez le [Guide de câblage et de gestion locale](docs/fr/HomeAssistant.md#câblage-et-gestion-locale-du-modem).

---

## 📄 Licence

Ce projet est sous licence GNU General Public License v3.0 – voir [LICENSE](LICENSE).  
Copyright (C) 2026 Daniel Ebenhöh.
