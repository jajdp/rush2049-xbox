# How the port works, and the twelve traps

*(Español: [HOW-IT-WORKS.es.md](HOW-IT-WORKS.es.md))*

## The shape of it: two builds, not one

| | What is built | How |
|---|---|---|
| 1 | **The game, as static libraries** | Ninja + clang-cl, as a **desktop** target, with `-DUWP_BUILD=ON` |
| 2 | **The appx** | The `uwp/` project, with the Visual Studio generator — the only genuine `WindowsStore` project |

**Why not one build.** MSBuild only offers the `v143` toolset for "Application Type = UWP", not
`ClangCL`, so asking for `-T ClangCL` against `WindowsStore` gives `error MSB8020`. And building
the game with `cl.exe` instead is not an option either: the ecosystem is written for clang —
`-Wno-*` flags in ultramodern and recompinput, `C4146` promoted to an error in rabbitizer.

So the game is compiled exactly as it is for the desktop, with clang-cl, and **what makes it UWP
is the `_UWP` macro** the patches define — not the Store SDK. The appx project links the
resulting `.lib` files and supplies the entry point.

## What had to change in the game

| File | Change |
|---|---|
| `CMakeLists.txt` | The `UWP_BUILD` option: defines `_UWP`, turns the executable into a static library, and leaves out what belongs to the `.exe` alone (link flags, the `.rc` icon, linking against desktop SDL2, and copying the DLLs) |
| `src/main.cpp` | Under `_UWP`, `main()` becomes `rush2049_uwp_main()` and is exported with `extern "C"` |
| `src/main.cpp` | `SDL_INIT_HAPTIC` out, under the same condition the project already had for the web build |
| `uwp/` (new) | `main.cpp`, `CMakeLists.txt`, `Package.appxmanifest`, `Assets/` and `patches/` |

All three are done by [`tools/parche_uwp_build.py`](../tools/parche_uwp_build.py), by exact
anchors, and it is idempotent.

## The libraries: this game is a free ride

Rush 2049 pins **exactly the same three library commits as Mario Party**, which is the single
reason this port took one evening instead of a week: worleydl's UWP patches and the four
conflict resolutions already published applied without a change.

| Library | Rush 2049 pins | Against worleydl's patches |
|---|---|---|
| `rt64` | `5473732` | the UWP patches apply with `--3way` |
| `N64ModernRuntime` | `cdf5abb` | 2 conflicts, both of the "keep both sides" kind |
| `RecompFrontend` | `b2c5c18` | no conflicts at all |
| `N64Recomp-browser` | `14241d9` (v0.159.0) | the web layer; each project applies its own |

### The four conflicts, and why they are all the same

All four resolve by **keeping both sides**, with worleydl's under `#ifdef _UWP` so the tree
still builds for the desktop. [`tools/resolver_conflictos.py`](../tools/resolver_conflictos.py)
does it, and it is byte for byte the one published in `marioparty-xbox`.

| File | What is done |
|---|---|
| `rt64_application.cpp` | The `#include "hle/rt64_uwp_mods.h"` under `#ifdef _UWP`; `showing_inspector` stays global, because both paths use it |
| `rt64_application_window.cpp` | ⚠ worleydl left a **`#if 0`** where an `#ifdef` belonged, and that kills the desktop path (`undefined symbol: uwp_GetRefreshRate`). It becomes `#ifndef _UWP` |
| `addresses.hpp` | Three branches: `mem_size` on Emscripten, **512 MB** on UWP and 4 GB on the desktop |
| `recomp.cpp` | `uwp_ProcessEvents()` — its declaration and its call in the UI loop — under `#ifdef _UWP` |

⚠ **The 512 MB was investigated and was NOT the cause of anything here.** It looked like a fit
for the crash that stopped this port for an evening: the heap asks for `0x1F000000` on top of a
`0x01000000` offset, which is exactly those 512 MB with no guard page behind it. It was raised to
4 GB, rebuilt and reinstalled, and **the crash was identical** — 4.16 s instead of 3.92. The
change was left in because it is harmless, but the cause was elsewhere: the video options.

## ⚠ What this game does differently from Mario Party

### 1. The project applies 24 patches of its own, and they go first

`tools/apply_runtime_patches.sh`, in the game's own repository, patches the submodules: the web
support from `N64Recomp-browser` first, then this game's own `runtime-patches/`. Without it the
game's code calls into things the libraries do not have:

```text
ultramodern::set_vi_rate
common/rt64_gpu_timings.h
```

It is this family's equivalent of Mario Party's `sellar.cmake`, but explicit and cleaner — which
is why **there is no `sellar.cmake` in this repository**.

⚠ **It has to run before worleydl's patches.** The script works out which of its patches are
already applied by reversing them, newest first, on a scratch copy — and it stops before touching
a submodule that has other changes on top. Apply the UWP patches first and it refuses to run.

Those 24 patches are also worth reading if you are chasing a graphics fault: `rt64-0008`
implements `G_CULLDL`, which upstream RT64 treats as a no-op, and `rt64-0005` is the one that
says what happens when a texture is not in the cache — *«undefined to read, whatever a driver
does with it»*. That sentence is the whole explanation of the Stunt arena fault below.

### 2. A different file layout, so different anchors

`main()` lives in `src/main.cpp`, not `src/main/main.cpp`; the `WIN32` block's comment at the top
of `CMakeLists.txt` is worded differently; and the desktop executable's block reaches further
than Mario Party's — besides the DLL `POST_BUILD` and desktop SDL2, it covers the `.rc` icon and
`/SUBSYSTEM:WINDOWS`. The tool here takes only `<tree>` for that reason: no argument would make
Mario Party's anchors fit.

### 3. The ROM's name carries no version

The runtime stores the ROM as `<game_id>.z64`, and this game's `game_id` is plain
`rush2049.n64.us`, so the file is **`rush2049.n64.us.z64`**. Mario Party's includes a `.1.0`.
Get it wrong and the launcher sits on "Load ROM" without a word in the log.

### 4. The clone leaves submodules half done

`git clone --recurse-submodules` left six of them empty — `json`, `plainargs`, `spirv-cross`,
`stb`, `xxHash`, `zstd` — **without an error**, and the configure died much later with *«does not
contain a CMakeLists.txt file»*. `compilar.ps1` repeats `submodule update --init --recursive`
until no folder under `lib/rt64/src/contrib` is empty.

## The twelve traps

| # | What happens |
|---|---|
| 1 | **`patches/` needs a clang with a MIPS backend.** Visual Studio's clang-cl does not have one; MSYS2's CLANG64 clang does |
| 2 | ⚠ **But the linker must not be LLD 22**: it no longer accepts `-nostdlib`, which `patches/Makefile` passes. LLD 19 does |
| 3 | ⚠ **`vcvars64.bat` rebuilds `PATH` and drops Windows' git.** MSYS2's git answers in Unix paths and the configure dies in a three-way merge. Put `C:\Program Files\Git\cmd` back, explicitly, before MSYS2 |
| 4 | ⚠ **`clone --recurse-submodules` leaves submodules half done, silently.** Repeat until none is empty |
| 5 | **`git apply --3way` wants the state in the index**: `add -A` before… and `reset` after |
| 6 | **A duplicate symbol between the patch and the game** (`osPfsIsPlug_recomp`). The game's wins |
| 7 | **`AddVectoredExceptionHandler` is not declared for UWP** — `error C3861`. Declare it by hand |
| 8 | ⚠ **`recompui_uwp_data_path` is in none of worleydl's patches.** Nothing complains until the appx links, at the very end: `LNK2019` |
| 9 | ⚠ **`SDL_INIT_HAPTIC` does not exist in WinRT's SDL**, and `SDL_Init` returns -1 **for the whole set**, so the window is never created |
| 10 | ⚠ **Portable mode is no way around the data folder.** `FOLDERID_LocalAppData` returns a folder the Device Portal does not expose; it has to be `LocalFolder` |
| 11 | ⚠ **The ROM's file name has no version in it here.** Wrong name, silent "Load ROM" |
| 12 | ⚠ **The project's own patches go before worleydl's**, or its script refuses to run |

## ⚠ The video options, which is where the real time went

Three of the game's own options cannot be left on, and finding that out took two rounds of
measuring because **the first round used tests that were too short**.

| What was on | How it dies |
|---|---|
| `hires_font` | Uncaught C++ exception `0xE06D7363` at **4.06 s** |
| `hires_title` | The same exception at **4.03 s** |
| `res_option=Auto` **+** `msaa_option=MSAA2X` | `0xC0000005 … (read 0x0000000000000000)` at **21.19 s** |

The two `hires` options fail **identically**, at the same point — right after overlay 1 loads —
and they share a mechanism: both build textures at runtime and register them with RT64 as a
built-in texture pack. They do write: the folders `hires_font\` and `hires_title\` appear inside
`LocalState`. What breaks is loading them back.

The third is a **different kind** of exception. A null read is the signature of a GPU allocation
that failed and whose result nobody checked, and it fits: a framebuffer at the TV's resolution
**per MSAA sample** is more than the UWP container grants. Either option on its own is fine.

⚠ **And this is the method lesson.** Every option passed a 40-second test on its own. With all of
them on at once — minus the two `hires` — the game died at **15.2 s**. The short test was handing
out false passes. Re-run at 3 and 4 minutes, checking every 30 s, the guilty pair fell out at
once. **Three minutes minimum, and test the set as well as the pieces**: GPU memory failures are
cumulative and do not show up one at a time.

### The fourth option, which does not crash — it drops textures

`scenery_culling` is this port's own option, and `Off` is the most expensive setting there is: it
draws **every scenery object from every stretch of track**, ignoring the game's visibility table.
On a desktop that is a frame-rate cost. On the console it produced something stranger: in the
**Stunt arena**, jumping high, a flat grey band appeared over the stands and moved with the car's
height.

What it was, measured on screenshots from both machines: the band is a **flat colour, exactly
(124,126,124)**, about 30 pixels deep, in the very place the PC draws the roof lattice with its
texture. So nothing was missing from the geometry — **a surface was being drawn without its
texture**. Which is what `rt64-0005` describes: a texture slot with nothing in it is *«undefined
to read, whatever a driver does with it»*. The GDK's D3D12 driver paints that grey; the desktop
one does not.

**And the part worth keeping:** the same mod and the same executable ran on both machines, so the
difference could not be the mod — it was load. `Off` plus a mod that rewrites memory every
retrace was more than the console had in hand, and when distant geometry arrived all at once its
textures were no longer cached. Setting `scenery_culling` to `Original` fixed it **with the mod
still on**. A graphics fault that only shows on the console is almost never "the console".

## The wrapper project

Not in this repository — it derives from worleydl's. What it has to do:

| Piece | Why |
|---|---|
| `WinMain` → `SDL_WinRTRunApp` | The container owns the thread; SDL creates the `CoreWindow` and then calls `rush2049_uwp_main` |
| The data path through `LocalFolder` | Trap 10: it is the only folder the Device Portal exposes |
| `AddVectoredExceptionHandler` declared by hand | Trap 7 |
| The SDL subsystems brought up one at a time | So a failing one does not take the rest with it — trap 9 |
| A log file of its own | The container's `stderr` is a fail-fast: without this there is no crash message at all |

## The two switches, and the FPS counter

Two optional files in `LocalState` make testing without a controller possible:

| File | What it does |
|---|---|
| `autoarranque.txt` | The wrapper adds `--boot`, the project's own development switch: it enters the ROM on the launcher's first frame |
| `fps.txt` | The FPS counter starts switched on |

The counter itself is **not in this repository**. The game does not have one — nor does the
frontend, nor the wrapper — so this catalogue adds one, in `RecompFrontend`'s `draw_hook`, the
only point that runs once per *presented* frame. Counting the game's own frames would always say
30, because RT64 interpolates up to the display's rate. It is bound to **R3**, read straight from
SDL so the game keeps that button. The patch lives with the Mario Party projects it was written
for, and applied here unchanged because both pin the same `RecompFrontend` commit.
