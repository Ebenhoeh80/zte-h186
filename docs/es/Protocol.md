# Protocolo de Solicitudes del Módem

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Protocol.md) | [Deutsch](../de/Protocol.md) | [Français](../fr/Protocol.md) | [Español](Protocol.md)

El cliente utiliza la sesión existente de la interfaz web del módem para realizar solicitudes de telemetría DSL de solo lectura.

## Secuencia de Solicitudes

1. Cargar la página de inicio y decodificar el token de sesión temporal de JavaScript (`_sessionTmpToken`) con secuencias de escape hexadecimales.
2. Solicitar el token de desafío numérico desde `/function_module/login_module/login_page/logintoken_lua.lua`.
3. Calcular el hash SHA-256 de la contraseña concatenada con el token de desafío y enviarlo junto con el token de sesión.
4. Cargar la página de estado DSL: `getpage.lua?pid=1002&nextpage=Internet_AdminInternetStatus_DSL_t.lp`.
5. Solicitar `/common_page/internet_dsl_interface_lua.lua` con la misma sesión autenticada.

La carga intermedia de `getpage.lua` es indispensable para inicializar el estado interno requerido por el módem.
