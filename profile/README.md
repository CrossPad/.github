<div align="center">

<img src="../docs/images/banner.jpg" alt="CrossPad — a pocket-size open-source sampler" width="100%">

# CrossPad

### A pocket-size, battery-powered, open-source sampler and pad instrument you can reprogram.

**ESP32-S3 · 16 pressure-sensitive RGB pads · 320×240 touch screen · encoder · speakers and mics · USB MIDI + USB audio · BLE MIDI · TRS MIDI in/out · SD card**

<p>
  <a href="https://crosspad.app">
    <img src="https://img.shields.io/badge/Website-crosspad.app-8B5CF6?style=for-the-badge" alt="crosspad.app">
  </a>
  <a href="https://crosspad.app/docs/">
    <img src="https://img.shields.io/badge/Docs-crosspad.app%2Fdocs-00C896?style=for-the-badge" alt="crosspad.app/docs">
  </a>
  <a href="https://play.crosspad.app">
    <img src="https://img.shields.io/badge/Explore%20kits-play.crosspad.app-F59E0B?style=for-the-badge" alt="play.crosspad.app">
  </a>
  <a href="https://discord.gg/WscqnaDwFJ">
    <img src="https://img.shields.io/discord/1368493946552062002?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2" alt="CrossPad Discord — members online">
  </a>
</p>

</div>

---

CrossPad is a sampler, sequencer and MIDI controller in one handheld box: 16 pressure-sensitive RGB pads, a touch screen and an encoder, built-in speakers and microphones, two audio codecs, an SD card for kits and songs, haptics and a motion sensor. It talks USB MIDI and USB audio to a computer, BLE MIDI to phones and tablets, and TRS MIDI to other gear.

Everything on it is an app. Sampler, mixer, sequencer, song arranger, recorder, slicer and the rest are separate repositories built on a shared C++ core and an LVGL UI framework, so the same app code runs on the board and in a desktop simulator. Writing your own is the point.

<div align="center">
<img src="../docs/images/sim_home.png" alt="The whole device in the simulator: home screen with the pad map" width="220">
<img src="../docs/images/sim_sampler.png" alt="The whole device in the simulator: Sampler with a kit loaded, two pads hit" width="220">
<br>
<img src="../docs/images/sim_launcher.png" alt="App launcher: the home screen as an icon grid" width="260">
<img src="../docs/images/sim_kits.png" alt="Kit browser" width="260">
<img src="../docs/images/sim_mixer.png" alt="Mixer" width="260">
<br>
<img src="../docs/images/sim_sequencer.png" alt="Sequencer with a recorded pattern" width="260">
<img src="../docs/images/sim_help.png" alt="Help app showing the simulator manual" width="260">
<br>
<sub>Captured from the PC simulator, which runs the same UI and apps as the device: home pad map, Sampler, app launcher (grid view), kit browser, Mixer, Sequencer and the Help app.</sub>
</div>

## Start here

| I want to… | Go to |
|---|---|
| Build and flash the firmware | [platform-idf](https://github.com/CrossPad/platform-idf) and the [Start here](https://crosspad.app/docs/start-here/) guide |
| Try it without hardware | [crosspad-pc](https://github.com/CrossPad/crosspad-pc), the desktop simulator ([guide](https://crosspad.app/docs/start-here/pc-simulator/)) |
| Write an app | [Create a new app](https://crosspad.app/docs/how-to/new-app/), then [Publish an app](https://crosspad.app/docs/how-to/publish-app/) |
| Install the toolchain in one line | [crosspad-apps](https://github.com/CrossPad/crosspad-apps#quickstart) installer (Windows, macOS, Linux) |
| Add or remove apps | [Install and remove apps](https://crosspad.app/docs/how-to/install-apps/), [App catalog](https://crosspad.app/docs/reference/app-catalog/) |

## Repositories

### Firmware

| Repo | What it is |
|---|---|
| [**platform-idf**](https://github.com/CrossPad/platform-idf) | The ESP-IDF firmware: board support, drivers, USB/BLE/TRS MIDI, audio, OTA. **Start here.** |
| [**crosspad-core**](https://github.com/CrossPad/crosspad-core) | Portable C++ core: app registry, event bus, pads, settings, audio engines, songs. No platform code |
| [**crosspad-gui**](https://github.com/CrossPad/crosspad-gui) | LVGL UI framework: app lifecycle, home screen, top bar, settings, widgets |
| [**crosspad-pc**](https://github.com/CrossPad/crosspad-pc) | Desktop simulator (SDL2) running the same core, UI and apps — Linux, Windows, macOS |

### Apps

| Repo | What it does |
|---|---|
| [**crosspad-sampler**](https://github.com/CrossPad/crosspad-sampler) | Sample player for the 16 pads: kits, waveform editing, kit browser |
| [**crosspad-mixer**](https://github.com/CrossPad/crosspad-mixer) | Audio mixer and router: channels, sends, outputs |
| [**crosspad-pattern-seq**](https://github.com/CrossPad/crosspad-pattern-seq) | Sequencer: record, loop, erase and bounce scenes |
| [**crosspad-song**](https://github.com/CrossPad/crosspad-song) | Song: scenes arranged as blocks on a timeline |
| [**crosspad-arrange**](https://github.com/CrossPad/crosspad-arrange) | Arrange: audio, kit and Pitch tracks on a timeline |
| [**crosspad-recorder**](https://github.com/CrossPad/crosspad-recorder) | Record a sample from the mics, the line-in or the pads, and trim it to a loop |
| [**crosspad-slicer**](https://github.com/CrossPad/crosspad-slicer) | Chop a loop by its hits, into equal parts or live on the pads, and save it as a kit |
| [**crosspad-pitchplay**](https://github.com/CrossPad/crosspad-pitchplay) | Pitch Play: one sample or many, played chromatically on the pads and from a MIDI keyboard |
| [**crosspad-pad-mixer**](https://github.com/CrossPad/crosspad-pad-mixer) | Sixteen faders, one per pad |
| [**crosspad-dawcontrol**](https://github.com/CrossPad/crosspad-dawcontrol) | DAW controller: the pads play the DAW, the DAW lights the pads (FL Studio, Ableton Live, REAPER) |
| [**crosspad-instructions**](https://github.com/CrossPad/crosspad-instructions) | Markdown help viewer on the device |
| [**crosspad-doom**](https://github.com/CrossPad/crosspad-doom) | DOOM on the pads, the encoder and the screen |
| [**crosspad-pong**](https://github.com/CrossPad/crosspad-pong) | Pong against the CPU or for two players |
| [**crosspad-pianotiles**](https://github.com/CrossPad/crosspad-pianotiles) | Piano Tiles: melodies and levels on the pads |
| [**crosspad-sdr**](https://github.com/CrossPad/crosspad-sdr) | The board's Wi-Fi radio as a 2.4 GHz receiver: spectrum, waterfall, I/Q |

### Tools

| Repo | What it is |
|---|---|
| [**crosspad-apps**](https://github.com/CrossPad/crosspad-apps) | App registry, CP Tools (the app manager) and the one-line installer |
| [**crosspad-mcp**](https://github.com/CrossPad/crosspad-mcp) | MCP server for AI coding assistants: build, flash, simulator and device tools |
| [**FT6236**](https://github.com/CrossPad/FT6236), [**ML_SynthTools**](https://github.com/CrossPad/ML_SynthTools) | Forks of third-party libraries (touch driver, synthesis tools) |

## 👥 The team behind CrossPad

CrossPad was born from inside the scene it serves: built by musicians and engineers who wanted a controller designed around how finger drummers actually perform, practice, and share. Every layer of the device — from pad response to app structure — is shaped by players and builders, not spec sheets.

<table align="center">
  <tr>
    <td align="center" width="33%">
      <a href="https://github.com/stevenashbeats">
        <img src="https://github.com/stevenashbeats.png" width="120" style="border-radius: 50%;" alt="Steve Nash"><br>
        <b>Steve Nash</b>
      </a><br>
      <sub>Fingerdrummer / Performer / Program Founder</sub><br><br>
      <sub>World Champion fingerdrummer and creative technologist. Founder of the CrossPad project, combining music, design, and open technology to empower creators around the world.</sub><br><br>
      <a href="https://github.com/stevenashbeats">
        <img src="https://img.shields.io/badge/GitHub-%40stevenashbeats-181717?logo=github&logoColor=white" alt="GitHub @stevenashbeats">
      </a><br>
      <a href="https://www.instagram.com/stevenashbeats/">
        <img src="https://img.shields.io/badge/Instagram-%40stevenashbeats-E4405F?logo=instagram&logoColor=white" alt="Instagram @stevenashbeats">
      </a>
    </td>
    <td align="center" width="33%">
      <a href="https://github.com/marcel-licence">
        <img src="https://github.com/marcel-licence.png" width="120" style="border-radius: 50%;" alt="Marcel Licence"><br>
        <b>Marcel Licence</b>
      </a><br>
      <sub>Programmer / Audio Systems Developer</sub><br><br>
      <sub>Software engineer specializing in embedded audio and real-time DSP. Brings CrossPad's sound engine to life with precision, efficiency, and an open-source mindset.</sub><br><br>
      <a href="https://github.com/marcel-licence">
        <img src="https://img.shields.io/badge/GitHub-%40marcel--licence-181717?logo=github&logoColor=white" alt="GitHub @marcel-licence">
      </a>
    </td>
    <td align="center" width="33%">
      <a href="https://github.com/matixan">
        <img src="https://github.com/matixan.png" width="120" style="border-radius: 50%;" alt="Mateusz Czarnecki"><br>
        <b>Mateusz Czarnecki</b>
      </a><br>
      <sub>Hardware Designer</sub><br><br>
      <sub>Electronics designer and prototyping expert responsible for CrossPad's hardware architecture. Focused on compact design, intuitive layout, and seamless integration between music and technology.</sub><br><br>
      <a href="https://github.com/matixan">
        <img src="https://img.shields.io/badge/GitHub-%40matixan-181717?logo=github&logoColor=white" alt="GitHub @matixan">
      </a>
    </td>
  </tr>
</table>

<p align="center">
  <a href="https://crosspad.app">
    <img src="https://img.shields.io/badge/Website-crosspad.app-8B5CF6?style=for-the-badge&logo=googlechrome&logoColor=white" alt="crosspad.app">
  </a>
  &nbsp;
  <a href="https://play.crosspad.app">
    <img src="https://img.shields.io/badge/Web%20App-play.crosspad.app-00C896?style=for-the-badge&logo=googlechrome&logoColor=white" alt="play.crosspad.app">
  </a>
  &nbsp;
  <a href="https://discord.gg/WscqnaDwFJ">
    <img src="https://img.shields.io/discord/1368493946552062002?style=for-the-badge&logo=discord&logoColor=white&label=Discord&color=5865F2" alt="CrossPad Discord — members online">
  </a>
  &nbsp;
  <a href="https://www.instagram.com/stevenashbeats/">
    <img src="https://img.shields.io/badge/Follow-%40stevenashbeats-E4405F?style=for-the-badge&logo=instagram&logoColor=white" alt="Instagram @stevenashbeats">
  </a>
</p>

<p align="center">
  <a href="https://discord.gg/WscqnaDwFJ">
    <img src="https://discord.com/api/guilds/1368493946552062002/widget.png?style=banner2" alt="CrossPad Discord: who is online right now">
  </a>
</p>

Got ideas, feedback, or something you built with CrossPad? Join us on [Discord](https://discord.gg/WscqnaDwFJ), reach out on Instagram, or open an issue on any repo — the community is the reason this project exists.

---

## License

CrossPad's code is free software under the **GNU General Public License v3.0 or later**; third-party parts keep their own licences, listed in each repository's README. The firmware can optionally be built with a prebuilt sample-streaming engine that is a separately licensed binary and is not linked by default — see [platform-idf → Audio engines](https://github.com/CrossPad/platform-idf#audio-engines).
