# Sécurité et Versions Publiques

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Security.md) | [Deutsch](../de/Security.md) | [Français](Security.md) | [Español](../es/Security.md)

## Gestion des Secrets

L'adresse du modem et le mot de passe d'administration doivent être conservés dans des fichiers chiffrés sous `secrets/` à l'aide de `store-age-secret.sh` (ou gérés de manière sécurisée dans Home Assistant ConfigEntries). Le dépôt ignore strictement les fichiers `.age` et le contenu local de `secrets/`.

La clé privée Age située dans `~/.config/age/keys.txt` ne doit jamais être committée, partagée ou publiée.

## Comportement à l'Exécution

Le client déchiffre l'adresse et le mot de passe uniquement en mémoire vive. Le mot de passe est haché avant transmission ; il n'est jamais envoyé en clair ni enregistré sur disque. Les messages d'erreur ne révèlent jamais les valeurs secrètes.

Le modem utilise une interface HTTP non chiffrée. N'exécutez le client que sur un réseau local de confiance et n'exposez jamais l'interface d'administration à des réseaux non fiables ou à Internet.
