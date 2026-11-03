# San Francisco Rush 2049 on Xbox — the UWP port

How to take **San Francisco Rush 2049: Recompiled**
([`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp)) — a static
recompilation built on **N64Recomp + RT64** — to an **Xbox Series X in Developer Mode**.

*(Español: [README.es.md](README.es.md))*

This is the same recipe published for the three Mario Party ports
([`marioparty-xbox`](https://github.com/jajdp/marioparty-xbox) and its siblings), which is the
point: the game is by the same author and pins the **same three library commits**, so the
platform work carries over untouched. What had to change for this game is listed below and is
most of what this repository adds.

⚠ **Mind the name.** This is *San Francisco Rush 2049* (2000). The other Rush port in this
catalogue, [`rush2-xbox`](https://github.com/jajdp/rush2-xbox), is *Rush 2: Extreme Racing USA*
(1998) — a different game by a different author.

## Which console this was tested on

**An Xbox Series X**, in Developer Mode. Both consoles this was built and tested on are Series X,
so that is the only hardware anything here covers.

**A Series S has never been tried — not once.** It is a different machine: less memory available
to a game and a weaker GPU. This may work on one, it may run slower, or it may not start at all;
nothing here has been measured on it.

## Where this port stands

Built from the game's **v0.1.46**. Measured on an Xbox Series X on 2026-11-02:

| | |
|---|---|
| ✅ Boots, draws and takes controller input | Package «Rush 2049 Recomp» 0.1.0.3, installed through the Device Portal |
| ✅ **Played for real**, with a controller | Stunt arena, jumps and all — not just the attract demo |
| ✅ **56–60 FPS** | The game's own counter, which this port adds on **R3** |
| ✅ The launcher comes up | Start Game / Controls / Settings / Mods / Exit |
| ✅ The ROM validates by itself | From `LocalState`, with no dialog |
| ✅ **Mods load**, including the cheats menu | [Hotwire 2049](https://github.com/Deozaan/Rush2049RecompCheatsMod) puts CHEATS in the main menu |
| ⚠ Three video options have to stay off | They crash the game or break the scenery — the table below |

**What is NOT claimed here:** that every track and mode runs cleanly end to end. What was
measured is the launch, the Stunt arena played with a controller, mods loading, and the frame
rate.

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
| [`tools/compilar.ps1`](tools/compilar.ps1) | **The whole recipe**, in six steps you can repeat one at a time: ROM, runtime patches, recompile, patches, static libraries, appx |
| [`tools/parche_uwp_build.py`](tools/parche_uwp_build.py) | The three changes **the game itself** needs: the `UWP_BUILD` option, renaming `main()`, and `SDL_INIT_HAPTIC`. By exact anchors, idempotent. ⚠ **This game's anchors**, which are not Mario Party's |
| [`tools/resolver_conflictos.py`](tools/resolver_conflictos.py) | The four conflicts worleydl's UWP patches hit. Byte for byte the one published in `marioparty-xbox`: it resolved this tree untouched |
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

**And the good news, which is why this port took one evening:** Rush 2049 pins exactly the same
library commits as Mario Party, so worleydl's patches and the four conflict resolutions already
written apply unchanged.

| Library | Rush 2049 | Mario Party |
|---|---|---|
| `rt64` | `5473732` | `5473732` ✓ |
| `N64ModernRuntime` | `cdf5abb` | `cdf5abb` ✓ |
| `RecompFrontend` | `b2c5c18` | `b2c5c18` ✓ |
| `N64Recomp-browser` | `14241d9` (v0.159.0) | `889b627` (v0.156.0) — different, but each project applies its own |

## ⚠ What this game does differently from Mario Party

Four things, and each one cost a failed attempt:

| | What is different |
|---|---|
| 1 | **`tools/apply_runtime_patches.sh` has to be run before building.** The project applies **24 patches of its own** to its submodules — the web layer first, then its own — and without them the game's code calls things the libraries do not have (`ultramodern::set_vi_rate`, `common/rt64_gpu_timings.h`). It is this family's equivalent of Mario Party's `sellar.cmake`, but explicit and cleaner — which is why **there is no `sellar.cmake` in this repository** |
| 2 | **A different file layout.** `main()` lives in `src/main.cpp`, not `src/main/main.cpp`, and the `WIN32` block's comment is worded differently, so `parche_uwp_build.py` needs **its own anchors**. The desktop executable's block also reaches further: it includes the `.rc` icon and `/SUBSYSTEM:WINDOWS` |
| 3 | ⚠ **The ROM's name in `LocalState` carries no version.** The runtime stores it as `<game_id>.z64`, and here the `game_id` is plain `rush2049.n64.us`, so the file is **`rush2049.n64.us.z64`**. Mario Party's includes a `.1.0`. With the wrong name the launcher just sits on "Load ROM" and says nothing |
| 4 | **`git clone --recurse-submodules` left six submodules half done** (`json`, `plainargs`, `spirv-cross`, `stb`, `xxHash`, `zstd`), without a word, and the configure died later with *«does not contain a CMakeLists.txt file»*. Repeat `git submodule update --init --recursive` until no folder under `lib/rt64/src/contrib` is empty |

## What it is not

No **ROM**, no recompiled code, no executable, no appx, no game art. Not worleydl's patches
either — they are in his repositories — nor the UWP bundle, nor the `uwp/` wrapper project
itself, which derives from his. Nor the FPS counter patch, which is this catalogue's own addition
and lives with the Mario Party projects it was written for. What this repository holds is the
recipe, the four tools, the video settings that work, and the record of what went wrong.

## Credits and license

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
