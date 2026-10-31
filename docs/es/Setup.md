# Instalación y Configuración

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/Setup.md) | [Deutsch](../de/Setup.md) | [Français](../fr/Setup.md) | [Español](Setup.md)

El proyecto ZTE H186 proporciona varios métodos flexibles y seguros para suministrar las credenciales de conexión según su entorno.

## Métodos de Credenciales

El cliente admite cuatro métodos en orden de prioridad:

### 1. Archivo de credenciales JSON (Recomendado para automatización)
Proporcione un archivo JSON protegido mediante `--credentials`:
```sh
python3 zte_h186_stats.py --credentials /ruta/a/credentials.json --ha-json
```
Formato JSON:
```json
{
  "host": "<MODEM-LAN-IP>",
  "username": "admin",
  "password": "<MODEM-CONTRASEÑA>"
}
```

### 2. Argumentos de línea de comandos y variables de entorno
Para uso interactivo o entornos en contenedores:
```sh
# Parámetros CLI:
python3 zte_h186_stats.py --host <MODEM-LAN-IP> --user admin --password "<MODEM-CONTRASEÑA>"

# O variables de entorno:
export ZTE_MODEM_HOST="<MODEM-LAN-IP>"
export ZTE_MODEM_USER="admin"
export ZTE_MODEM_PASSWORD="<MODEM-CONTRASEÑA>"
python3 zte_h186_stats.py --ha-json
```

### 3. Secretos cifrados con Age (Máxima seguridad en reposo)
Para entornos que requieren cifrado de datos en reposo:
```sh
./store-age-secret.sh zte-ipaddress
./store-age-secret.sh zte-admin-password
```
Y ejecute:
```sh
python3 zte_h186_stats.py --ha-json
```

### 4. Flujo de configuración en la interfaz de Home Assistant
En Home Assistant:
1. Vaya a **Ajustes > Dispositivos y servicios > Añadir integración**.
2. Busque **ZTE H186 DSL Modem**.
3. Introduzca la dirección IP (`<MODEM-LAN-IP>`), el usuario (`admin`) y la contraseña.
4. La integración crea automáticamente los 27 sensores y el botón de actualización.

Para obtener detalles sobre el cableado de puertos y la asignación de IP estática, consulte la [Guía de Cableado](HomeAssistant.md#cableado-de-hardware-y-administración-local-del-módem).
