# Integración de ZTE H186 para Home Assistant (HACS)

<p align="center">
  <img src="images/icon.png" alt="ZTE H186 DSL Modem" width="240">
</p>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/v/release/Ebenhoeh80/zte-h186)](https://github.com/Ebenhoeh80/zte-h186/releases)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Quality Scale: Bronze](https://img.shields.io/badge/Quality%20Scale-Bronze-brown.svg)](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
[![Languages: en, de, fr, es](https://img.shields.io/badge/Languages-en%20%7C%20de%20%7C%20fr%20%7C%20es-brightgreen.svg)](#internacionalización-i18n)

[English](README.md) | [Deutsch](README.de.md) | [Français](README.fr.md) | [Español](README.es.md)

Una integración personalizada asíncrona para el **módem DSL ZTE H186**. Lee telemetría de línea DSL en tiempo real (velocidades de sincronización, margen SNR, atenuación, contadores de errores CRC/FEC, perfil de transmisión y tiempo de actividad Showtime) directamente desde la interfaz web local del módem.

---

## 🚀 Características

- **Configuración mediante interfaz de usuario (Config Flow)**: Configuración rápida directamente desde la interfaz de Home Assistant (*Ajustes > Dispositivos y servicios > Añadir integración*). No requiere YAML.
- **Flujo de Reconfiguración**: Actualice la dirección IP, el nombre de host o la contraseña sin perder ID de entidades, paneles o historial.
- **Flujo de Opciones**: Intervalo de sondeo configurable de 15 a 600 segundos (predeterminado: 60 segundos).
- **Caché de sesión y eficiencia**: Mantiene activa la sesión autenticada y se recupera automáticamente tras expiraciones.
- **Soporte completo de 4 idiomas (i18n)**: Inglés, alemán, francés y español.
- **27 sensores completos**:
  - **Ancho de banda y sincronización**: Velocidad de sincronización de bajada y subida (Mbit/s), capacidad máxima alcanzable (Mbit/s), utilización de línea (%).
  - **Calidad de señal**: Margen de ruido (SNR en dB), atenuación de línea (dB), potencia de transmisión (dBm).
  - **Tramas y latencia**: Perfil DSL (ej. 17a, 35b), estándar de modulación (VDSL2), ruta de datos (Fast/Interleaved), profundidad y retardo de entrelazado, protección contra ruido impulsivo (INP).
  - **Tiempo de actividad y errores**: Duración de sincronización Showtime, errores CRC no corregidos, errores de bit FEC corregidos.
- **Sensores binarios**:
  - `dsl_link`: Estado de la conexión física DSL.
  - `line_noise_warning`: Alerta de ruido cuando el margen SNR cae por debajo de 6,0 dB.
- **Botón de acción**:
  - `refresh_stats`: Desencadena un sondeo inmediato de estadísticas.

---

## 📦 Instalación mediante HACS

1. Abra **Home Assistant**.
2. Vaya a **HACS** > **Integraciones**.
3. Haga clic en el menú de tres puntos (⋮) en la esquina superior derecha y seleccione **Repositorios personalizados**.
4. Ingrese la URL:
   ```text
   https://github.com/Ebenhoeh80/zte-h186
   ```
5. Seleccione la categoría **Integración** y haga clic en **Añadir**.
6. Descargue **ZTE H186 DSL Modem** y reinicie Home Assistant.

---

## ⚙️ Configuración

1. En Home Assistant, vaya a **Ajustes** > **Dispositivos y servicios**.
2. Haga clic en **Añadir integración** y busque **ZTE H186 DSL Modem**.
3. Introduzca la dirección IP (`<MODEM-LAN-IP>`), el usuario (`admin`) y la contraseña.
4. Envíe el formulario.

> 💡 **Cableado de hardware**: Consulte la [Guía de cableado y administración local](docs/es/HomeAssistant.md#cableado-de-hardware-y-administración-local-del-módem).

---

## 📄 Licencia

Este proyecto está bajo la Licencia Pública General GNU v3.0 – consulte [LICENSE](LICENSE).  
Copyright (C) 2026 Daniel Ebenhöh.
