# ZTE H186 : Télémétrie DSL locale dans Home Assistant

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/HomeAssistant.md) | [Deutsch](../de/HomeAssistant.md) | [Français](HomeAssistant.md) | [Español](../es/HomeAssistant.md)

---

## Objet et Portée

Ce projet lit les valeurs de ligne DSL d'un modem compatible ZTE H186 via son interface web locale. Un client s'authentifie, extrait les données XML d'état DSL et les transmet à Home Assistant. Aucun cloud ni courtier MQTT n'est requis. Les paramètres DSL, de routage, Wi-Fi ou WAN ne sont jamais modifiés. La connexion établit toutefois une session active sur le modem.

L'intégration Home Assistant fournit 27 capteurs de mesure et de télémétrie ainsi que 2 capteurs binaires.

Cette documentation ne contient aucune adresse IP réelle, plage réseau ou mot de passe de production. Des espaces réservés neutres tels que `<MODEM-LAN-IP>` sont utilisés.

---

## Architecture

Le projet prend en charge deux méthodes d'intégration :

1. **Intégration Personnalisée Home Assistant (`custom_components/zte_h186`) (Recommandée)** :
   - Intégration native avec interface graphique Config Flow (**Paramètres > Appareils et services > Ajouter une intégration**)
   - Création automatique de 27 capteurs, 2 capteurs binaires et un bouton d'action
   - `DataUpdateCoordinator` asynchrone central avec mise en cache de session
   - Reconfiguration transparente en cas de changement d'IP ou de mot de passe

2. **Paquet YAML classique (`zte-h186-package.yaml`)** :
   - Exécution du script en ligne de commande (`zte_h186_stats.py`) toutes les 300 secondes
   - Pour environnements sans composants personnalisés

---

## Câblage et Gestion Locale du Modem

Cette section décrit le câblage physique et la configuration réseau nécessaires pour exploiter le ZTE H186 comme simple modem DSL en pont (bridge) devant un routeur principal, tout en conservant l'accès d'administration local.

### Ports Physiques et Code Couleur

Les ports du ZTE H186 ont des fonctions bien distinctes :

| Port / Couleur | Désignation | Raccordement | Rôle et flux de données |
|---|---|---|---|
| **Rouge** | WAN / Routeur | Relier au **port WAN** du routeur principal | Achemine la liaison DSL pure (mode pont / PPPoE passthrough) vers le routeur. **Aucun accès à l'interface d'administration ou login ne s'effectue sur ce port.** |
| **Jaune** | LAN / Gestion | Relier à un **switch réseau** dans le réseau local de gestion/VLAN | Dédié exclusivement à l'accès d'administration de l'interface web et à la télémétrie Home Assistant. |
| **Gris** | DSL | Relier à la **prise téléphonique / DSL** | Achemine le signal DSL haute fréquence vers le modem. |

> **Remarque sur les variantes matérielles :**  
> Ce code couleur (Gris = DSL, Rouge = WAN, Jaune = LAN) correspond au boîtier standard d'usine. Certains modèles d'opérateurs peuvent présenter des marquages différents (ex. ports noirs avec étiquettes gravées `DSL`, `WAN` ou `LAN1`). Vérifiez toujours les inscriptions physiques sur votre appareil.

---

### Configuration pas-à-pas de la gestion locale

1. **Connexion directe initiale :**  
   Si nécessaire, raccordez d'abord un PC directement au **port LAN jaune** avec un câble Ethernet. Ouvrez l'interface web du modem à l'adresse IP d'usine par défaut.
2. **Attribuer une IP fixe dans le réseau de gestion :**  
   Dans les paramètres LAN du modem, attribuez une adresse IPv4 fixe libre (`<MODEM-LAN-IP>`) et le masque de sous-réseau correspondant. Assurez-vous que cette adresse se trouve en dehors de la plage DHCP dynamique de votre routeur.
3. **Désactiver le serveur DHCP du ZTE H186 :**  
   **OBLIGATOIRE** : Désactivez le serveur DHCP intégré du ZTE H186 dans les réglages LAN **avant** de relier le port jaune au switch de votre réseau principal. Deux serveurs DHCP sur le même segment réseau provoquent des conflits majeurs. Le serveur DHCP de votre routeur principal reste actif.
4. **Enregistrer et tester :**  
   Enregistrez les paramètres et vérifiez l'accès dans votre navigateur sur `http://<MODEM-LAN-IP>`.
5. **Raccorder au switch :**  
   Connectez le **port LAN jaune** au switch dans le réseau/VLAN de gestion approprié.
6. **Accès futur :**  
   Toutes les connexions et requêtes de Home Assistant s'effectuent exclusivement via l'IP LAN (`<MODEM-LAN-IP>`) sur le port jaune — jamais via le port rouge.

---

### Relation avec l'intégration Home Assistant

1. **Accessibilité réseau :**  
   Home Assistant doit pouvoir joindre l'adresse `<MODEM-LAN-IP>` sur le port HTTP 80.
2. **Saisie des identifiants :**  
   - Accédez à **Paramètres > Appareils et services > Ajouter une intégration**.
   - Recherchez **ZTE H186 DSL Modem**.
   - Renseignez l'adresse IP (`<MODEM-LAN-IP>`), le nom d'utilisateur (`admin`) et le mot de passe.
   - Les mots de passe sont saisis dans des champs masqués sécurisés.
