# 🌱 OpenGrowBox Dev Environment

[![GitHub stars](https://img.shields.io/github/stars/OpenGrow-Box/OpenGrowBox-Dev-Enviorment?style=flat-square)](https://github.com/OpenGrow-Box/OpenGrowBox-Dev-Enviorment/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/OpenGrow-Box/OpenGrowBox-Dev-Enviorment?style=flat-square)](https://github.com/OpenGrow-Box/OpenGrowBox-Dev-Enviorment/issues)
[![License](https://img.shields.io/badge/license-OGBCL-blue?style=flat-square)](https://github.com/OpenGrow-Box/OpenGrowBox-Dev-Enviorment/blob/main/LICENSE)
[![HA Version](https://img.shields.io/badge/Home%20Assistant-2025.1.0+-green?style=flat-square)](https://www.home-assistant.io)

**A virtual development environment for OpenGrowBox HA integration testing.** Simulate a complete grow box ecosystem without hardware, enabling safe prototyping of automations, dashboards, and integrations for the [OpenGrowBox HA system](https://github.com/OpenGrow-Box/OpenGrowBox-HA).

## 📋 Purpose

This is a **development-only simulator** for the [OpenGrowBox HA](https://github.com/OpenGrow-Box/OpenGrowBox-HA) integration. It provides:

- Physics-based environmental simulation (temperature, humidity, CO₂, soil parameters)
- Virtual devices for control (lights, fans, heaters, pumps)
- Full Home Assistant entity integration
- Risk-free testing of grow automations and UI

**Not for production use.** For real grow room automation, install the [main OpenGrowBox HA integration](https://github.com/OpenGrow-Box/OpenGrowBox-HA).

## ✨ Features

- **Environmental Simulation**: Realistic model of air/soil conditions with seasonal effects, device interactions, and outside weather integration
- **Virtual Devices**: 20+ simulated actuators (standard lights, special spectrum lights/IR/UV, climate control, irrigation, fans) and sensors
- **Home Assistant Integration**: Exposes entities as sensors, switches, lights, fans, climate, etc., with proper labeling
- **Periodic Updates**: Real-time simulation every 30 seconds
- **Multi-Zone Support**: Assign devices to "Grow Room" area for organized control
- **No Hardware Required**: Pure software simulation for development and testing

## 🔧 Installation

### Via HACS (Recommended)

1. Install [HACS](https://hacs.xyz/) in Home Assistant
2. Add this repository: `https://github.com/OpenGrow-Box/OpenGrowBox-Dev-Enviorment`
3. Search for "OpenGrowBox Dev Environment" and install
4. Restart Home Assistant

### Manual Installation

```bash
cd /config
git clone https://github.com/OpenGrow-Box/OpenGrowBox-Dev-Enviorment.git
cp -r OpenGrowBox-Dev-Enviorment/custom_components/ogb-dev-env /config/custom_components/
```

Restart Home Assistant.

## ⚙️ Configuration

Add the integration in HA: **Settings → Devices & Services → Add Integration → OpenGrowBox Dev Environment**.

No YAML configuration needed. The simulator creates a "Grow Room" area and populates it with virtual devices.

## 📖 Usage

1. **Add Integration**: Follow installation steps.
2. **Explore Devices**: Check HA devices for simulated sensors (e.g., temperature, humidity) and controls (e.g., lights, fans).
3. **Test Automations**: Create HA automations (e.g., "turn on lights at dawn") using virtual entities.
4. **View Dashboards**: Build Lovelace dashboards with simulated data.
5. **Debug Integrations**: Test how your setup interacts with OGB-HA features like VPD control.

Example: Toggle the virtual main light and observe temperature/humidity changes in the simulator. Special lights (IR, Red/Blue, UV) include spectrum sensors for advanced testing.

## 🏗️ How It Works

- **Simulation Engine**: Models environmental dynamics with device effects (e.g., lights increase temperature, heaters raise air temp), VPD, and outside air exchange.
- **Device Layer**: Defines virtual hardware with properties, controls, and sensors (including spectrum sensors for special lights).
- **HA Platforms**: Registers entities for monitoring and control with clean naming (e.g., switch.devheater).
- **Updates**: Runs every 30 seconds, applying physics, randomness, and seasonal/weather effects for realism.

See [main OGB-HA docs](https://github.com/OpenGrow-Box/OpenGrowBox-HA) for how this simulates real systems.

## 🤝 Contributing

- Report issues or request features in the [main OpenGrowBox HA repo](https://github.com/OpenGrow-Box/OpenGrowBox-HA/issues)
- For feedback on this dev tool, use GitHub issues here or [opencode issues](https://github.com/anomalyco/opencode/issues)

## 📄 License

Licensed under the [OpenGrowBox Community License (OGBCL) v2.0](https://github.com/OpenGrow-Box/OpenGrowBox-Dev-Enviorment/blob/main/LICENSE). Free for non-commercial development; commercial rights reserved.

---

*Built for the OpenGrowBox community. Happy simulating! 🌱*

---

## About

Virtual development environment for testing OpenGrowBox HA integrations without physical hardware.