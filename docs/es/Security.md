# Seguridad y Versiones Públicas

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Security.md) | [Deutsch](../de/Security.md) | [Français](../fr/Security.md) | [Español](Security.md)

## Tratamiento de Secretos

La dirección del módem y la contraseña de administración deben guardarse en archivos cifrados bajo `secrets/` mediante `store-age-secret.sh` (o en ConfigEntries protegidos de Home Assistant). El repositorio ignora los archivos `.age` y el contenido de `secrets/`.

La clave privada de Age en `~/.config/age/keys.txt` no debe subirse ni compartirse jamás.

## Comportamiento en Tiempo de Ejecución

El cliente descifra la dirección y la contraseña únicamente en la memoria del proceso. La contraseña se procesa con hash antes de enviarse; nunca se transmite en texto plano ni se escribe en disco. Los mensajes de error nunca imprimen secretos.

El módem expone su interfaz web mediante HTTP no cifrado. Ejecute el cliente únicamente en una red local de confianza y nunca exponga la interfaz de administración a redes no seguras o a Internet.
