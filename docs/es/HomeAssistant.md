# ZTE H186: Telemetría DSL Local en Home Assistant

```text
# Copyright (C) 2026 Daniel Ebenhöh
# SPDX-License-Identifier: GPL-3.0-only
```

[English](../en/HomeAssistant.md) | [Deutsch](../de/HomeAssistant.md) | [Français](../fr/HomeAssistant.md) | [Español](HomeAssistant.md)

---

## Propósito y Alcance

Este proyecto lee los valores de la línea DSL de un módem compatible ZTE H186 a través de su interfaz web local. Un cliente se autentica, extrae los datos XML de estado DSL y los proporciona a Home Assistant. No se requiere conexión a la nube ni broker MQTT. No se modifican las configuraciones de DSL, enrutamiento, Wi-Fi o WAN. El inicio de sesión genera una sesión activa en el módem.

El paquete y la integración de Home Assistant proporcionan 27 sensores de medición y telemetría, así como 2 sensores binarios.

Esta documentación no contiene direcciones IP reales, rangos de red o credenciales privadas de producción. Se utilizan marcadores de posición neutrales como `<MODEM-LAN-IP>`.

---

## Arquitectura

El proyecto admite dos métodos de integración:

1. **Integración Personalizada de Home Assistant (`custom_components/zte_h186`) (Recomendada)**:
   - Integración nativa con interfaz gráfica de configuración (**Ajustes > Dispositivos y servicios > Añadir integración**)
   - Creación automática de 27 sensores, 2 sensores binarios y un botón de acción
   - `DataUpdateCoordinator` asíncrono central con almacenamiento en caché de sesión
   - Reconfiguración fluida en caso de cambios de IP o contraseña

2. **Paquete YAML clásico (`zte-h186-package.yaml`)**:
   - Sondeo mediante proceso de línea de comandos (`zte_h186_stats.py`) cada 300 segundos
   - Diseñado para entornos tradicionales basados exclusivamente en archivos

---

## Cableado de Hardware y Administración Local del Módem

Esta sección describe el cableado físico y la configuración de red requeridos para operar el ZTE H186 como un módem DSL dedicado en modo puente (bridge) frente a un enrutador principal, manteniendo simultáneamente el acceso de administración local.

### Puertos Físicos y Código de Colores

Los puertos del ZTE H186 desempeñan funciones distintas en la topología de red:

| Puerto / Color | Denominación | Conexión | Función operativa y flujo de datos |
|---|---|---|---|
| **Rojo** | WAN / Enrutador | Conectar al **puerto WAN** del enrutador principal | Transmite el enlace DSL puro (modo puente / PPPoE passthrough) al enrutador. **No se realiza ningún acceso de administración web ni inicio de sesión a través de este puerto.** |
| **Amarillo** | LAN / Administración | Conectar a un **conmutador de red (switch)** en la VLAN/red de administración local | Dedicado exclusivamente al acceso administrativo a la interfaz web y a las consultas de telemetría de Home Assistant. |
| **Gris** | DSL | Conectar a la **línea telefónica / DSL** | Conduce la señal DSL de alta frecuencia directamente al módem. |

> **Nota sobre variaciones de hardware del fabricante:**  
> El código de colores descrito (Gris = DSL, Rojo = WAN, Amarillo = LAN) corresponde al diseño estándar de fábrica. Según el distribuidor o proveedor de servicios, algunos dispositivos pueden tener puertos de color neutro con etiquetas grabadas (`DSL`, `WAN` o `LAN1`). Verifique siempre las etiquetas físicas en su dispositivo antes de conectar cables.

---

### Configuración paso a paso de la administración local

1. **Conexión directa inicial:**  
   Si es necesario, conecte primero un PC directamente al **puerto LAN amarillo** con un cable Ethernet. Abra la interfaz web del módem en el navegador con la IP predeterminada de fábrica.
2. **Asignar IP estática en la red de administración:**  
   En la configuración LAN del módem, asigne una dirección IPv4 estática libre (`<MODEM-LAN-IP>`) y la máscara de subred correspondiente. Asegúrese de que la IP asignada esté fuera del rango dinámico DHCP de otros dispositivos.
3. **Desactivar el servidor DHCP del ZTE H186:**  
   **OBLIGATORIO**: Desactive el servidor DHCP integrado del ZTE H186 en los ajustes de LAN **antes** de conectar el puerto amarillo al conmutador de red de producción. Dos servidores DHCP en el mismo segmento de red causan conflictos graves. El servidor DHCP de su enrutador principal permanece activo.
4. **Guardar y comprobar acceso:**  
   Guarde los ajustes y verifique la conexión en el navegador abriendo `http://<MODEM-LAN-IP>`.
5. **Conectar al conmutador de red:**  
   Conecte el **puerto LAN amarillo** a un puerto del conmutador en la VLAN o red de administración adecuada.
6. **Acceso futuro:**  
   Todos los accesos de administración y consultas de Home Assistant se realizarán exclusivamente a través de la IP LAN configurada (`<MODEM-LAN-IP>`) en el puerto amarillo, nunca a través del puerto rojo.

---

### Relación con la integración de Home Assistant

1. **Accesibilidad de red:**  
   Home Assistant debe tener acceso de red a `<MODEM-LAN-IP>` en el puerto 80 (HTTP).
2. **Configuración de credenciales:**  
   - Vaya a **Ajustes > Dispositivos y servicios > Añadir integración**.
   - Busque **ZTE H186 DSL Modem**.
   - Introduzca la dirección IP (`<MODEM-LAN-IP>`), el nombre de usuario (`admin`) y la contraseña.
   - Las contraseñas se introducen únicamente en el campo enmascarado de la interfaz.
