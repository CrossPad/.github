<div align="center">

<img src="https://i.ibb.co/twTZr0mp/videoframe-2033.jpg" alt="CrossPad — the open-source MIDI pad controller" width="100%">

# 🎛️ CrossPad

### An open-source MIDI pad controller — hardware, firmware, and software, all in the open.

**4×4 velocity-sensitive RGB pads · 320×240 LCD · FM synth · MIDI USB/BLE/UART · Full PC simulator**

<p>
  <img src="https://img.shields.io/badge/License-Open%20Source-success?style=for-the-badge" alt="Open Source">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Active">
  <img src="https://img.shields.io/badge/Platforms-ESP32--S3%20%7C%20STM32%20%7C%20PC-blue?style=for-the-badge" alt="Platforms">
</p>

<p>
  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?logo=c%2B%2B&logoColor=white" alt="C++17">
  <img src="https://img.shields.io/badge/ESP32--S3-firmware-E7352C?logo=espressif&logoColor=white" alt="ESP32-S3">
  <img src="https://img.shields.io/badge/STM32-coprocessor-03234B?logo=stmicroelectronics&logoColor=white" alt="STM32">
  <img src="https://img.shields.io/badge/LVGL-GUI-blue" alt="LVGL">
  <img src="https://img.shields.io/badge/SDL2-simulator-1C2333" alt="SDL2">
  <img src="https://img.shields.io/badge/PlatformIO-Arduino-orange?logo=platformio&logoColor=white" alt="PlatformIO">
  <img src="https://img.shields.io/badge/CMake-build-064F8C?logo=cmake&logoColor=white" alt="CMake">
  <img src="https://img.shields.io/badge/MIDI-USB%20%7C%20BLE%20%7C%20UART-brightgreen" alt="MIDI">
  <img src="https://img.shields.io/badge/Claude%20Code-MCP%20integrated-8B5CF6" alt="Claude Code MCP">
</p>

<img src="../docs/images/simulator_full.png" alt="CrossPad PC Simulator" width="420">

<sub><b>The same code runs on real hardware and in a full desktop simulator.</b></sub>

</div>

---

## ✨ Why CrossPad?

CrossPad is a music controller built **from scratch** — PCB to pixel. It's not a firmware flashed onto someone else's board. The schematics, the firmware, the GUI framework integration, the desktop simulator, and even the Claude-Code developer tooling are all open and hackable.

- 🎹 **Play it.** 4×4 velocity-sensitive RGB pads, rotary encoder, crisp 320×240 color LCD with animated LVGL UI.
- 🔊 **Hear it.** Built-in FM synth, mixer, and effects chain with I2S audio out.
- 🔌 **Connect it.** Class-compliant MIDI over USB, BLE, and UART — no drivers.
- 🧩 **Extend it.** Modular app system — drop in a new app (sequencer, sampler, piano…) without touching the core.
- 💻 **Develop it anywhere.** A PC simulator with full feature parity — build and test apps in seconds, no hardware required.
- 🤖 **Build it with Claude.** A dedicated [MCP server](https://github.com/CrossPad/crosspad-mcp) gives Claude Code 17 tools to build, test, screenshot, inject input, search code, tweak settings, and inspect runtime state.

<div align="center">
<img src="../docs/images/simulator_launcher.png" alt="App Launcher" width="320">
&nbsp;
<img src="../docs/images/simulator_instructions.png" alt="Simulator Controls" width="320">
</div>

---

## 🏗️ Architecture at a glance

```
                   ┌─────────────────┐     ┌──────────────────┐
                   │  crosspad-gui   │     │  crosspad-core   │
                   │   (LVGL UI)     │     │  (business logic)│
                   └────────┬────────┘     └────────┬─────────┘
                            │                       │
      ┌─────────────────────┼───────────┬───────────┴─────────┐
      │                     │           │                     │
┌─────▼─────────┐  ┌────────▼────────────────┐  ┌─────────────▼─────┐
│  crosspad-pc  │  │ ESP32-S3 / platform-idf │  │  CrossPad_STM32   │
│ (SDL2 + MSVC) │  │  (Arduino / ESP-IDF)    │  │  (pad scanning,   │
│  PC simulator │  │     main firmware       │  │  LED + encoder)   │
└───────────────┘  └─────────────────────────┘  └───────────────────┘
```

**Write once, run everywhere.** Apps implement `IApp`. Platform repos provide thin implementations of hardware interfaces (`IClock`, `IMidiOutput`, `ILedStrip`, `IAudioOutput`, `ISynthEngine`). Business logic never knows what chip it's running on.

---

## 🗺️ Repository map

CrossPad lives across several repos, each with a single clear responsibility.

### Core libraries (shared across all platforms)

| Repo | Visibility | Description |
|---|---|---|
| [**crosspad-core**](https://github.com/CrossPad/crosspad-core) | Private | Portable C++ library: AppRegistry, EventBus, PadManager, PadLedController, Settings, MIDI handler, platform interfaces |
| [**crosspad-gui**](https://github.com/CrossPad/crosspad-gui) | Private | LVGL UI: theme, styles, launcher, status bar, settings UI, widgets (keypad buttons, radial menu, VU meter, file explorer, modals/toasts) |

### Platform repos (thin wrappers around core + gui)

| Repo | Visibility | Description |
|---|---|---|
| [**crosspad-pc**](https://github.com/CrossPad/crosspad-pc) | **Public** | Desktop simulator (SDL2 + LVGL). MIDI via RtMidi, audio via RtAudio/WASAPI, STM32 hardware emulator window. For rapid development without hardware |
| [**ESP32-S3**](https://github.com/CrossPad/ESP32-S3) | Private | Main firmware (Arduino framework). WiFi/BLE, I2S audio, NVS persistence, DFU updates, pad grid driver |
| [**platform-idf**](https://github.com/CrossPad/platform-idf) | Private | ESP-IDF native platform variant — alternative to Arduino, using ESP-IDF components directly |
| [**CrossPad_STM32**](https://github.com/CrossPad/CrossPad_STM32) | Private | STM32F0 firmware for hardware management: MPR121 pad scanning, WS2812B LEDs, vibration motor, encoder. SPI link to ESP32 |

### Tooling

| Repo | Visibility | Description |
|---|---|---|
| [**crosspad-mcp**](https://github.com/CrossPad/crosspad-mcp) | Private | MCP server for Claude Code — 17 tools: build, test, screenshot, input injection, code search, settings, runtime stats |

### Hardware

| Repo | Visibility | Description |
|---|---|---|
| [**PICO_drumpad**](https://github.com/CrossPad/PICO_drumpad) | Private | KiCad 9.0 PCB project |

### Dependencies (forks)

| Repo | Description |
|---|---|
| [**ML_SynthTools**](https://github.com/CrossPad/ML_SynthTools) | FM synthesis engine (fork) |
| [**FT6236**](https://github.com/CrossPad/FT6236) | Touchscreen driver for FocalTech FT6236 (fork) |

---

## 🚀 Getting started

### PC Simulator — the fastest way in

The simulator runs the **exact same GUI and app code** as the real device. No hardware needed.

**Requirements:** Git, CMake, Ninja, vcpkg, SDL2, Visual Studio 2022 (Windows) or clang/gcc (macOS/Linux)

```bash
# Clone with submodules
git clone --recursive https://github.com/CrossPad/crosspad-pc.git
cd crosspad-pc

# Install SDL2 via vcpkg
vcpkg install sdl2:x64-windows   # Windows
# or: brew install sdl2          # macOS
# or: apt install libsdl2-dev    # Linux

# Build
cmake -B build -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake \
  -DCMAKE_BUILD_TYPE=Debug
cmake --build build

# Run
bin/main.exe   # Windows
bin/main       # macOS / Linux
```

The simulator window shows the full device: LCD, 4×4 pad grid, rotary encoder, and audio device selection.

### ESP32-S3 firmware (Arduino)

```bash
git clone --recursive https://github.com/CrossPad/ESP32-S3.git
cd ESP32-S3
pio run              # build
pio run -t upload    # flash via USB
```

There's also a native ESP-IDF variant in [platform-idf](https://github.com/CrossPad/platform-idf) for those who prefer the ESP-IDF component system directly.

### 🤖 Claude Code integration

Give Claude Code full control over the build/test/run cycle:

```bash
git clone https://github.com/CrossPad/crosspad-mcp.git
cd crosspad-mcp
npm install && npm run build
```

Add to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "crosspad": {
      "command": "node",
      "args": ["/path/to/crosspad-mcp/dist/index.js"]
    }
  }
}
```

Then just ask Claude: *"Build and run the simulator, take a screenshot, press pad 5"* — it just works. Scaffold a new app, run UI tests, inspect live state, iterate on pixel-level details — all from a single conversation.

---

## 🧠 Key design decisions

- **PadManager is the single source of truth** for pad state, note mapping, and LED coordination. All pad events flow through PadManager, never directly to apps.
- **Platform capabilities** are runtime bitflags (`hasCapability(Capability::Midi)`), not compile-time `#ifdef`. Apps query what's available instead of null-checking pointers.
- **Settings** use `IKeyValueStore` abstraction (NVS on ESP32, filesystem on PC). The settings UI is 100% shared in crosspad-gui.
- **App lifecycle** follows `start` / `pause` / `resume` / `destroy`. Apps register via static `AppRegistrar` constructors — no central list to maintain.
- **Event-driven** architecture via `IEventBus`. Pad presses, MIDI, encoder events are dispatched to subscribers. PC uses synchronous dispatch; ESP32 uses FreeRTOS queues.

---

## 🤝 Contributing

CrossPad is designed so you can contribute **without reading the entire codebase**:

- **Add an app** → use `crosspad_scaffold_app` (MCP) or copy `src/apps/ml_piano/` as a template
- **Add a platform** → implement the interfaces in `crosspad-core/include/crosspad/platform/`
- **Add UI components** → drop widgets into crosspad-gui, they'll work on every platform

See [crosspad-pc/CLAUDE.md](https://github.com/CrossPad/crosspad-pc/blob/master/CLAUDE.md) for detailed architecture documentation.

---

## 📄 License

**Open source.** Schematics, firmware, PC tools, documentation — all in the open.

> A music controller you can't modify isn't yours.

---

<div align="center">

**Built with ❤️ and a soldering iron.**

If CrossPad is useful to you, a ⭐ on the repos really helps.

</div>
