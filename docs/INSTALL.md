# Building the port and getting it onto the console

*(Español: [INSTALL.es.md](INSTALL.es.md))*

⚠ **Read "Where this port stands" and the video settings table in the
[`README.md`](../README.md) before spending an evening on this.** Three of the game's video
options have to be left off, and one of them does not crash — it quietly drops textures.

## 0. Where the commands go

> **Where this goes:** in **PowerShell** — press the **Windows** key, type `powershell` and
> press **Enter** on *Windows PowerShell* — in an **ordinary** window: no "run as administrator"
> needed, from this repository's folder.

**No administrator needed** — and for the certificate step, using an administrator window
actively breaks things, because the certificate lands in whichever account ran the command.
**PowerShell 7 is not required**, and the examples carry `-ExecutionPolicy Bypass` because a
stock Windows refuses to run a `.ps1` at all.

How to tell whether a command worked: type `$?` right after it. It answers `True` or `False`
about the command before it.

## 1. What you need first

| | What for |
|---|---|
| **Visual Studio** with the C++ tools and **C++ Clang tools for Windows** | The MSVC environment (`vcvars64`), **clang-cl**, **Ninja** and the appx. The year does not matter; what matters is that `vcvars64.bat` exists and `clang-cl.exe` is in `VC\Tools\Llvm\x64\bin` |
| **Your ROM** of *San Francisco Rush 2049* (USA), SHA-1 `3f99351d7bb61656614bdb2aa1a90cfe55d1922c` | The recompiler translates it to C. No other region or revision is supported |
| **MSYS2**, CLANG64 environment | The only clang here with a **MIPS backend**, which `patches/` needs, plus `make` |
| **LLVM 19** (just for `ld.lld.exe`) | ⚠ LLD 22 rejects `-nostdlib`; see trap 2 in [`HOW-IT-WORKS.md`](HOW-IT-WORKS.md) |
| **worleydl's UWP forks and his `uwp-dep` bundle, branch `rt64`** | SDL2 for WinRT, `libuwp`, freetype, dxil and dxcompiler, and the platform patches |
| **Git and Python 3.13** | Cloning, patching and the tools here |
| **CMake 3.x** | ⚠ CMake 4 rejects some of this project's submodules |
| **An Xbox Series X in Developer Mode** and a self-signed certificate | Installing and signing |
| **About 3 GB of disk** | The tree, its submodules and two builds |

## 2. The recipe

```powershell
powershell -ExecutionPolicy Bypass -File tools\compilar.ps1 -Arbol C:\rush -Rom "C:\roms\rush2049.z64"
```

That runs every step in order. Each can be repeated on its own, which is what helps when
something fails halfway:

| `-Paso` | What it does |
|---|---|
| `rom` | Runs the project's own `tools/extract.py`, which writes the two copies it needs into `roms\` |
| `runtime` | ⚠ **The step Mario Party does not have.** The project's own `tools/apply_runtime_patches.sh`: its 24 patches to the submodules, the web layer first and then its own |
| `parches` | The game's own three changes, worleydl's UWP patches, the four conflict resolutions, and the data path |
| `recompilar` | `tools/recompile.sh`: translates the ROM's MIPS to C (N64Recomp) and the audio microcode (RSPRecomp). **43 files** in `RecompiledFuncs\` |
| `pc` | The **desktop** executable. Build it first: without a PC build there is nowhere to compare a graphics fault against — which is exactly how the Stunt arena fault was diagnosed |
| `libs` | The game **as static libraries**, with **Ninja and clang-cl** |
| `appx` | The only genuine `WindowsStore` project: links the libraries and produces the `.msix` |

⚠ **The `libs` step cannot use the Visual Studio generator.** The why is the first section of
[`HOW-IT-WORKS.md`](HOW-IT-WORKS.md), and it is the one thing to know before starting.

⚠ **`runtime` goes before `parches`, not after.** `apply_runtime_patches.sh` works out which of
its patches are already applied by reversing them on a scratch copy, and it stops before
touching a submodule that has other changes on top. Apply worleydl's patches first and it will
refuse to run.

## 3. The wrapper project

This repository does **not** carry `uwp/` — it derives from worleydl's and belongs in his
repositories. What it has to contain, and why each piece is there, is written out in
[`HOW-IT-WORKS.md`](HOW-IT-WORKS.md): a `WinMain` that calls `SDL_WinRTRunApp`, the data path
through `LocalFolder`, `AddVectoredExceptionHandler` declared by hand, the subsystems brought up
one at a time, and a log file of its own because the container's `stderr` is a fail-fast.

⚠ If you start from the Mario Party wrapper, the names to change are the CMake project and
target, the entry point (`rush2049_uwp_main`), the package identity and display name, and **the
ROM's file name** — which is the one that bites, because it has no version in it here.

## 4. Installing it on the console

### Before touching anything: how the console has to be

- **In Developer Mode**, with Dev Home installed.
- **On, and with your profile signed in.** ⚠ With no user signed in the console **will not launch
  apps**.
- **On the same network**, with its address at hand. The Device Portal listens on port **11443**
  over HTTPS and asks for the username and password you set in Dev Home.

Open `https://<ip>:11443`. ⚠ The browser will warn that the certificate is not trusted: it is the
console's own. Go in anyway — in Edge and Chrome, **Advanced** → **Continue to … (unsafe)**; in
Firefox, **Advanced** → **Accept the Risk and Continue**. Then **My games & apps → Add**.

## 5. The ROM, the settings and the switches, inside the package

⚠ **`LocalState` does not exist until the first launch.** Upload before that and the portal says
it cannot find the path. So: install, **open the game once**, close it, and only then upload with
the portal's **File explorer**:

| File | Why |
|---|---|
| `rush2049.n64.us.z64` | ⚠ The ROM, under **exactly** that name — no version in it. With any other name the launcher sits on "Load ROM" and says nothing |
| `graphics.json` | [`tools/graphics-xbox.json`](../tools/graphics-xbox.json), renamed. Without it the defaults crash the game within 21 seconds |
| `fps.txt` *(optional)* | The FPS counter starts on, which on a console is the only way to see it without a controller in hand to press **R3** |
| `autoarranque.txt` *(optional)* | Boots straight into the ROM, for testing with nobody in front of the console |

## If something goes wrong

| Symptom | Cause |
|---|---|
| `does not contain a CMakeLists.txt file` during a configure | `clone --recurse-submodules` left submodules half done. Repeat `git submodule update --init --recursive` until no folder under `lib/rt64/src/contrib` is empty |
| `ultramodern::set_vi_rate` or `common/rt64_gpu_timings.h` not found | The `runtime` step was skipped: the project's own 24 patches are not applied |
| `apply_runtime_patches.sh` stops saying a patch will not apply | It ran **after** worleydl's patches. Start from a clean submodule checkout and run it first |
| `error MSB8020` building the libraries | The Visual Studio generator was used: it has to be Ninja + clang-cl |
| `lld: error: unknown argument: -nostdlib` | `PATCHES_LD` is LLD 22. Point it at an LLVM 19 `ld.lld.exe` |
| `does not match index` from `git apply --3way` | `git add -A` in that submodule first — and `git reset` afterwards |
| `lld-link: error: duplicate symbol: osPfsIsPlug_recomp` | The patch's and the game's both defined. Keep the game's |
| `error C3861: AddVectoredExceptionHandler` | Not declared for UWP: declare it by hand in the wrapper |
| `LNK2019: unresolved external symbol recompui_uwp_data_path` **when the appx links** | `tools/parche_data_path.py` was not run. It is the one change that is in none of worleydl's patches, and nothing complains until the very last step |
| The link leaves `uwp_PickMultipleFiles` unresolved | The UWP bundle is from the wrong branch: for this family it is `rt64` |
| Boots with no video and hangs creating the window | `SDL_INIT_HAPTIC`: WinRT's SDL has no haptics and `SDL_Init` fails the whole set |
| The launcher stays on "Load ROM" | The ROM's name. Here it is `rush2049.n64.us.z64`, with no version in it |
| Dies after ~4 s, `0xE06D7363` | `hires_font` or `hires_title` is on |
| Dies after ~21 s, `0xC0000005 … read 0x0000...0000` | High resolution **and** MSAA together |
| A flat grey band over the stands when jumping in Stunt | `scenery_culling` is `Off`. Set it to `Original` |
| The portal cannot find the path when uploading the ROM | `LocalState` does not exist until the first launch (§5) |
| The console answers `0x800B0100` | The `.msix` is unsigned (below) |

## Reinstalling: three things that bite

1. **MSBuild leaves the appx unsigned.** Sign it with a self-signed certificate whose **subject
   is exactly the manifest's `Publisher`** — that is what keeps the package family name, so the
   console treats it as an update and keeps `LocalState`:
   `signtool sign /fd SHA256 /sha1 <thumbprint> <msix>`.
2. ⚠ **Installing the same version with different contents is refused**, with
   `-2147009285`: *«the provided package has the same identity as an already-installed package
   but the contents are different»*. Bump the manifest's `Identity Version` first, and anchor
   the regular expression that does it (`\sVersion="…"`), because `MinVersion` contains
   `Version`. Uninstalling also clears it, but that takes `LocalState` and the ROM with it.
3. **A shader cache written by an older build is no good.** Delete `LocalState\shadercache\`;
   the game rebuilds it.
