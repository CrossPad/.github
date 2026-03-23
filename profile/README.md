## Hi there 👋

# CrossPad

Open-source MIDI pad controller with a 320x240 LCD, 4x4 RGB pads, rotary encoder, and built-in audio engine. Runs on ESP32-S3 + STM32 hardware. Fully simulatable on PC (Windows, macOS, Linux).

<p align="center">
  <img src="https://github.com/user-attachments/assets/e97d61b6-2c96-48e4-b83f-9352cd6c97d8" alt="CrossPad PC Simulator" width="350">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/C%2B%2B-17-00599C?logo=c%2B%2B&logoColor=white" alt="C++17">
  <img src="https://img.shields.io/badge/ESP32--S3-firmware-E7352C?logo=espressif&logoColor=white" alt="ESP32-S3">
  <img src="https://img.shields.io/badge/STM32-coprocessor-03234B?logo=stmicroelectronics&logoColor=white" alt="STM32">
  <img src="https://img.shields.io/badge/LVGL-GUI-blue" alt="LVGL">
  <img src="https://img.shields.io/badge/SDL2-simulator-1C2333" alt="SDL2">
  <img src="https://img.shields.io/badge/PlatformIO-Arduino-orange?logo=platformio&logoColor=white" alt="PlatformIO">
  <img src="https://img.shields.io/badge/CMake-build-064F8C?logo=cmake&logoColor=white" alt="CMake">
  <img src="https://img.shields.io/badge/MIDI-USB%20%7C%20BLE%20%7C%20UART-brightgreen" alt="MIDI">
  <img src="https://img.shields.io/badge/License-Open%20Source-success" alt="Open Source">
</p>

## What is CrossPad?

CrossPad is a music controller built from scratch — hardware, firmware, and software. It combines:

- **4x4 velocity-sensitive RGB pad grid** for drum machines, samplers, sequencers
- **320x240 color LCD** with LVGL-based GUI (themes, animations, app launcher)
- **Rotary encoder** for navigation and parameter control
- **MIDI I/O** (USB, BLE, UART) — class-compliant, no drivers needed
- **Built-in FM synth** and audio engine with mixer, effects chain
- **App system** — modular apps (piano, sampler, mixer, sequencer) that can be added without touching the core

The same code runs on real hardware and on a desktop simulator with full feature parity.

<p align="center">
  <img src="https://github.com/user-attachments/assets/c0c1d56d-cede-47b3-a38f-1142d9b8ad13" alt="App Launcher" width="280">
  &nbsp;
  <img src="https://github.com/user-attachments/assets/c6210281-97df-43e9-ac92-35c72026fc83" alt="Simulator Controls" width="280">
</p>

## Repository map

CrossPad is split across several repos, each with a clear responsibility:

### Core libraries (shared across all platforms)

| Repo | Visibility | Description |
|---|---|---|
| [**crosspad-core**](https://github.com/CrossPad/crosspad-core) | Private | Portable C++ library: AppRegistry, EventBus, PadManager, PadLedController, Settings, MIDI handler, platform interfaces (`IClock`, `IMidiOutput`, `ILedStrip`, `IAudioOutput`, `ISynthEngine`) |
| [**crosspad-gui**](https://github.com/CrossPad/crosspad-gui) | Private | LVGL UI components: theme, styles, launcher, status bar, settings UI, widgets (keypad buttons, radial menu, VU meter, file explorer, modals/toasts) |

### Platform repos (thin wrappers around core + gui)

| Repo | Visibility | Description |
|---|---|---|
| [**crosspad-pc**](https://github.com/CrossPad/crosspad-pc) | Public | Desktop simulator (SDL2 + LVGL). MIDI via RtMidi, audio via RtAudio/WASAPI, STM32 hardware emulator window. For rapid development without hardware |
| [**ESP32-S3**](https://github.com/CrossPad/ESP32-S3) | Private | Main firmware (Arduino framework). WiFi/BLE, I2S audio, NVS persistence, DFU updates, pad grid driver |
| [**platform-idf**](https://github.com/CrossPad/platform-idf) | Private | ESP-IDF native platform variant — alternative to Arduino, using ESP-IDF components directly |
| [**CrossPad_STM32**](https://github.com/CrossPad/CrossPad_STM32) | Private | STM32F0 firmware for hardware management: pad scanning (MPR121), LED strip (WS2812B), vibration motor, encoder readout. Communicates with ESP32 via SPI |

### Tooling

| Repo | Visibility | Description |
|---|---|---|
| [**crosspad-mcp**](https://github.com/CrossPad/crosspad-mcp) | Private | MCP server for Claude Code integration — 17 tools: build, test, screenshot, input injection, code search, settings, runtime stats |

### Hardware

| Repo | Visibility | Description |
|---|---|---|
| [**PICO_drumpad**](https://github.com/CrossPad/PICO_drumpad) | Private | KiCad 9.0 PCB project |

### Dependencies (forks)

| Repo | Description |
|---|---|
| [**ML_SynthTools**](https://github.com/CrossPad/ML_SynthTools) | FM synthesis engine (fork) |
| [**FT6236**](https://github.com/CrossPad/FT6236) | Touchscreen driver for FocalTech FT6236 (fork) |

## Architecture

```
                    +-----------------+     +-----------------+
                    |   crosspad-gui  |     |  crosspad-core  |
                    |   (LVGL UI)     |     |  (business logic)|
                    +--------+--------+     +--------+--------+
                             |                       |
         +-------------------+----------+------------+----------+
         |                              |                       |
+--------v--------+     +--------------v-----------+    +-------v---------+
|   crosspad-pc   |     |  ESP32-S3 / platform-idf |    |  CrossPad_STM32 |
|  (SDL2 + MSVC)  |     |   (Arduino / ESP-IDF)    |    |  (pad scanning) |
|   PC simulator  |     |     main firmware         |    |  LED + encoder  |
+-----------------+     +--------------------------+    +-----------------+
```

**Write once, run everywhere.** Apps implement crosspad-core's `IApp` interface. Platform repos provide thin implementations of hardware interfaces. Business logic never knows what chip it's running on.

## Getting started

### PC Simulator (fastest way to start)

The simulator runs the exact same GUI and app code as the real device.

**Requirements:** Git, CMake, Ninja, vcpkg, SDL2, Visual Studio 2022 (Windows) or clang/gcc (Mac/Linux)

```bash
# Clone with submodules
git clone --recursive https://github.com/CrossPad/crosspad-pc.git
cd crosspad-pc

# Install SDL2 via vcpkg
vcpkg install sdl2:x64-windows   # Windows
# or: brew install sdl2           # macOS
# or: apt install libsdl2-dev     # Linux

# Build
cmake -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake -DCMAKE_BUILD_TYPE=Debug
cmake --build build

# Run
bin/main.exe   # Windows
bin/main       # Mac/Linux
```

The simulator window shows the full device body: LCD, 4x4 pad grid, rotary encoder, and audio devices.

### ESP32-S3 firmware (Arduino)

**Requirements:** PlatformIO with Arduino framework for ESP32-S3

```bash
git clone --recursive https://github.com/CrossPad/ESP32-S3.git
cd ESP32-S3
pio run              # build
pio run -t upload    # flash via USB
```

There is also a native ESP-IDF variant in [platform-idf](https://github.com/CrossPad/platform-idf) for those who prefer the ESP-IDF component system directly.

### MCP integration (for Claude Code users)

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

Then ask Claude: *"build and run the simulator, take a screenshot, press pad 5"* — it just works.

## Key design decisions

- **PadManager is the single source of truth** for pad state, note mapping, and LED coordination. All pad events flow through PadManager, never directly to apps.
- **Platform capabilities** are runtime bitflags (`hasCapability(Capability::Midi)`), not compile-time `#ifdef`. Apps query what's available instead of null-checking pointers.
- **Settings** use `IKeyValueStore` abstraction (NVS on ESP32, filesystem on PC). The settings UI is 100% shared in crosspad-gui.
- **App lifecycle** follows `start` / `pause` / `resume` / `destroy`. Apps register via static `AppRegistrar` constructors — no central list to maintain.
- **Event-driven** architecture via `IEventBus`. Pad presses, MIDI, encoder events are dispatched to subscribers. PC uses synchronous dispatch; ESP32 uses FreeRTOS queues.

## Contributing

CrossPad is open source. The architecture is designed so you can contribute without reading the entire codebase:

- **Add an app:** Use `crosspad_scaffold_app` (MCP) or look at `src/apps/ml_piano/` as a template
- **Add a platform:** Implement the interfaces in `crosspad-core/include/crosspad/platform/`
- **UI components:** Add widgets to crosspad-gui, they'll work on all platforms

See [crosspad-pc/CLAUDE.md](https://github.com/CrossPad/crosspad-pc/blob/master/CLAUDE.md) for detailed architecture documentation.

## License

Open source. Schematics, firmware, PC tools, documentation — all in the open. A music controller you can't modify isn't yours.
