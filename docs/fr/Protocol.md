# Protocole de Requêtes du Modem

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Protocol.md) | [Deutsch](../de/Protocol.md) | [Français](Protocol.md) | [Español](../es/Protocol.md)

Le client utilise la session de l'interface web existante du modem pour effectuer des requêtes de télémétrie DSL en lecture seule.

## Séquence des Requêtes

1. Chargement de la page d'accueil et décodage du jeton de session JavaScript (`_sessionTmpToken`) contenant des échappements hexadécimaux.
2. Récupération du jeton défi (challenge) numérique depuis `/function_module/login_module/login_page/logintoken_lua.lua`.
3. Calcul du hachage SHA-256 du mot de passe avec le jeton défi et envoi avec le jeton de session.
4. Chargement de la page d'état DSL : `getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp`.
5. Requête sur `/common_page/internet_dsl_interface_lua.lua` avec la session authentifiée.

Le chargement intermédiaire de `getpage.lua` est obligatoire pour amorcer l'état interne attendu par le firmware du modem.
