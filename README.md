# San Francisco Rush 2049 on Xbox — the UWP port

How to take **San Francisco Rush 2049: Recompiled**
([`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp)) — a static
recompilation built on **N64Recomp + RT64** — to an **Xbox Series X in Developer Mode**.

*(Español: [README.es.md](README.es.md))*

**The platform work is not this repository's.** The UWP forks of RT64, N64ModernRuntime and
RecompFrontend are [**worleydl**](https://github.com/worleydl)'s, and this game pins library
commits close enough to them that his patches go in with **four conflicts and nothing else**,
all four of the same kind. That is the whole reason this port took one evening. What this
repository adds is what had to change **for this game**: its three source changes, the order the
patches have to go in, the video settings the console will take, and the record of what went
wrong.

⚠ **Mind the name.** This is *San Francisco Rush 2049* (2000), **not** *Rush 2: Extreme Racing
USA* (1998). Different game, different recompilation project, different author — if you came for
*Rush 2*, this is not the recipe.

## Which console this was tested on

**An Xbox Series X**, in Developer Mode. Both consoles this was built and tested on are Series X,
so that is the only hardware anything here covers.

**A Series S has never been tried — not once.** It is a different machine: less memory available
to a game and a weaker GPU. This may work on one, it may run slower, or it may not start at all;
nothing here has been measured on it.

## Where this port stands

Built from the game's **v0.1.46**. Measured on an Xbox Series X on 2026-11-02, with the
full Circuit run confirmed on 2026-11-05:

| | |
|---|---|
| ✅ Boots, draws and takes controller input | Package «Rush 2049 Recomp» 0.1.0.3, installed through the Device Portal |
| ✅ **Played through**, with a controller | The six Circuit tracks run end to end, plus the Stunt arena with its jumps — not just the attract demo |
| ✅ **56–60 FPS** | Measured with a counter drawn over the frame on **R3**. The game has none; this one is a diagnostic tool, described in [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md) rather than shipped here |
| ✅ The launcher comes up | Start Game / Controls / Settings / Mods / Exit |
| ✅ The ROM validates by itself | From `LocalState`, with no dialog |
| ✅ **Mods load**, including the cheats menu | [Hotwire 2049](https://github.com/Deozaan/Rush2049RecompCheatsMod) puts CHEATS in the main menu |
| ⚠ Three video options have to stay off | They crash the game or break the scenery — the table below |

**What is NOT claimed here:** that every mode runs cleanly. The six Circuit tracks have been
run end to end on the console; **Ghost Race, Battle and the split-screen modes have not been
measured there at all.**

## ⚠ The video settings this console will take

This is the part that cost the most and the part you most want before starting. Four options
have to be left alone; **everything else can stay on, high resolution included**, which is the
one you actually notice.

```jsonc
// LocalState\graphics.json  — tools/graphics-xbox.json is this file, ready to upload
"res_option":      "Auto",       // ✅ the TV's resolution
"msaa_option":     "None",       // ❌ multisampling does NOT fit beside high resolution
"hires_font":      "Off",        // ❌ kills the game after 4 s
"hires_title":     "Original",   // ❌ kills the game after 4 s
"scenery_culling": "Original",   // ❌ "Off" does not fit either — see below
// everything else on:
"ar_option": "Expand", "menu_ratio": "Expand", "game_frame_rate": "60",
"input_lag": "Reduced", "draw_distance": "Far", "level_of_detail": "High"
```

| Option | What happens on the console |
|---|---|
| `hires_font`, `hires_title` | Uncaught C++ exception (`0xE06D7363`) **4 seconds in**, right after overlay 1 loads. Both build textures at runtime and register them with RT64 as a built-in texture pack |
| `res_option=Auto` **+** `msaa_option=MSAA2X` | Null read (`0xC0000005 … read 0x0000000000000000`) **21 seconds in**: a framebuffer at TV resolution *per MSAA sample* is more than the container grants. Either one alone is fine |
| `scenery_culling=Off` | Does not crash — it **drops textures**. In the Stunt arena, jumping high, a flat grey band appears over the stands. `Off` draws every scenery object from every stretch of track, and when distant geometry arrives all at once its textures are no longer cached. A missing texture is *«undefined to read, whatever a driver does with it»*, and the GDK driver paints it grey where the desktop one does not |

⚠ **And the method lesson, which is the reusable part:** a 40-second test is not enough to
approve a video option. The two `hires` ones die at 4 s, but res+MSAA takes 21 s, and with
everything on at once the game died at 15 s. Test for **at least 3 minutes**, and when each
piece passes on its own, **test the set as well**: GPU memory failures are cumulative and do not
show up one at a time.

## What this repository is

**A recipe, not a product.** There is no ROM, no recompiled code, no executable and no `.msix`
here — and that is deliberate, not an oversight.

| Piece | What it is |
|---|---|
| [`tools/compilar.ps1`](tools/compilar.ps1) | **The whole recipe**, in seven steps you can repeat one at a time: ROM, runtime patches, patches, recompile, the desktop build, static libraries, appx |
| [`tools/parche_uwp_build.py`](tools/parche_uwp_build.py) | The three changes **the game itself** needs: the `UWP_BUILD` option, renaming `main()`, and `SDL_INIT_HAPTIC`. By exact anchors, idempotent. ⚠ **The anchors are this game's**, which is why it takes the tree and nothing else |
| [`tools/resolver_conflictos.py`](tools/resolver_conflictos.py) | The four conflicts worleydl's UWP patches hit. What it matches is in the libraries, not in the game, so it resolved this tree untouched |
| [`tools/parche_data_path.py`](tools/parche_data_path.py) | Defines `recompui_uwp_data_path`. **Without it the appx does not link** |
| [`tools/graphics-xbox.json`](tools/graphics-xbox.json) | The settings above, ready to upload to `LocalState` |
| [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md) | The two builds, what this game does differently, and the traps |
| [`docs/INSTALL.md`](docs/INSTALL.md) | What you need, the commands, and getting it onto the console |

The game is **GPL-3.0**, so its code can be quoted and the changes to it are published here. What
is quoted, how much and from where is measured in [`NOTICE.md`](NOTICE.md).

## The two things to understand before trying

**1. The Visual Studio generator will NOT do for the game's libraries.** MSBuild only has the
`v143` toolset for "Application Type = UWP", not `ClangCL`, so `-T ClangCL` with `WindowsStore`
gives `error MSB8020`; and with `cl.exe` the whole ecosystem falls over, because it is written
for clang. The right way is **Ninja + clang-cl**, with the libraries as a **desktop** target:
what makes them UWP is the `_UWP` macro the patches define. The only genuine `WindowsStore`
project is the appx one.

**2. The platform work comes from worleydl's forks**, not from here: `rt64-dev` (branch
`uwp-dk64`), `N64ModernRuntime-dev` (`uwp-rebase`), `RecompFrontend-dev` (`uwp-compat`) and the
[`worleydl/uwp-dep`](https://github.com/worleydl/uwp-dep) bundle, **branch `rt64`**.

**The commits this game pins** are what decide how much of worleydl's work you get for free, so
check them first in any tree you are about to patch. If they match, everything below applies as
written; if they do not, expect the conflicts somewhere else.

| Library | Commit pinned here | Against worleydl's UWP patches |
|---|---|---|
| `rt64` | `5473732` | they go in with `--3way`, **2 conflicts** |
| `N64ModernRuntime` | `cdf5abb` | **2 conflicts**, both of the "keep both sides" kind |
| `RecompFrontend` | `b2c5c18` | none at all |
| `N64Recomp-browser` | `14241d9` (v0.159.0) | the web layer; this project patches it itself, in the `runtime` step |

## ⚠ The four things that each cost a failed attempt

None of them is in worleydl's patches or in the game's README — they are what this port had to
find out:

| | What it is |
|---|---|
| 1 | **`tools/apply_runtime_patches.sh` has to be run before building, and before worleydl's patches.** The project applies **24 patches of its own** to its submodules — the web layer first, then its own — and without them the game's code calls things the libraries do not have (`ultramodern::set_vi_rate`, `common/rt64_gpu_timings.h`). Its script works out what is already applied by reversing it, so it refuses to run on a submodule that has other changes on top |
| 2 | **Where the anchors are.** `main()` lives in `src/main.cpp`, not under `src/main/`, and the desktop executable's block in `CMakeLists.txt` reaches further than you would expect: besides copying the DLLs and linking desktop SDL2, it covers the `.rc` icon and `/SUBSYSTEM:WINDOWS`. All of that has to come out of the library build, which is why `parche_uwp_build.py` is specific to this tree |
| 3 | ⚠ **The ROM's name in `LocalState` carries no version.** The runtime stores it as `<game_id>.z64`, and here the `game_id` is plain `rush2049.n64.us`, so the file is **`rush2049.n64.us.z64`** — no `1.0`, no suffix, nothing. With any other name the launcher just sits on "Load ROM" and says nothing |
| 4 | **`git clone --recurse-submodules` left six submodules half done** (`json`, `plainargs`, `spirv-cross`, `stb`, `xxHash`, `zstd`), without a word, and the configure died later with *«does not contain a CMakeLists.txt file»*. Repeat `git submodule update --init --recursive` until no folder under `lib/rt64/src/contrib` is empty |

## What it is not

No **ROM**, no recompiled code, no executable, no appx, no game art. Not worleydl's patches
either — they are in his repositories — nor the UWP bundle, nor the `uwp/` wrapper project
itself, which derives from his. Nor the FPS counter: it is a diagnostic tool rather than a part
of the port, so [`docs/HOW-IT-WORKS.md`](docs/HOW-IT-WORKS.md) sets out how it works and where it
hooks in — in enough detail to write one — instead of shipping it. What this repository holds is
the recipe, the four tools, the video settings that work, and the record of what went wrong.

## Credits and license

**Almost none of what makes this work is ours.** This repository is a recipe that glues together other people's work; without any one of these pieces there would be no port at all.

| What it does | Who made it | License |
|---|---|---|
| **[rush-2049-recomp](https://github.com/n64hub/rush-2049-recomp)** — recompiles *San Francisco Rush 2049* | **n64hub** | GPL-3.0 |
| **[uwp-dep](https://github.com/worleydl/uwp-dep)** — Dawn, SDL3, nod and dxcompiler **built for UWP** — the single reason any of this runs on an Xbox | **Daniel Worley** (worleydl) | libuwp: zlib, © 2025 |
| **[N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime)** — the runtime those recompilations run on | the **N64Recomp** project | GPL-3.0 |
| **[RecompFrontend](https://github.com/N64Recomp/RecompFrontend)** — the in-game menus and configuration UI | the **N64Recomp** project | GPL-3.0 |
| **[N64Recomp](https://github.com/N64Recomp/N64Recomp)** — statically recompiles N64 games into native executables | **Mr-Wiseguy** and the N64Recomp project | MIT |
| **[rt64](https://github.com/rt64/rt64)** — the N64 renderer, with its enhancements | the **RT64** project | MIT |
| **[SDL](https://github.com/libsdl-org/SDL)** — window, input and audio | **Sam Lantinga** and the SDL contributors | zlib |

Special mention to **Daniel Worley**: the UWP builds in `uwp-dep` are what make an Xbox port of this possible. We did not build them, we used them.

**The packaging recipe, the tooling and this documentation** are by **Recompilaciones**.


Recipe and tooling by **Recompilaciones**, under the **[GPL-3.0](LICENSE)** — the license of the
game project this recipe patches,
[`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp), and of
[N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime) and
[RecompFrontend](https://github.com/N64Recomp/RecompFrontend), whose lines the conflict
resolutions quote. [N64Recomp](https://github.com/N64Recomp/N64Recomp) and
[RT64](https://github.com/rt64/rt64) are MIT. The UWP forks the recipe builds on are
**worleydl**'s. The cheats mod named above is **Deozaan**'s and is not distributed here.

The game project is **written by AI** and says so itself; it is directed and play-tested by a
person. That is its authors' statement, not a claim made here.

*San Francisco Rush 2049* is © Atari Games / Midway. This project is not affiliated with them,
with Microsoft, or with the authors of N64Recomp, RT64, the game project or the UWP forks. Rights
holders: **jajdpmail@gmail.com**.
