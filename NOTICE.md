# Notice

*(Español: [NOTICE.es.md](NOTICE.es.md))*

## No affiliation

This project is not affiliated with, endorsed by or connected to **Atari Games** or **Midway**,
the rights holders of *San Francisco Rush 2049*; nor **Microsoft**; nor the authors of
[N64Recomp](https://github.com/N64Recomp/N64Recomp), [RT64](https://github.com/rt64/rt64),
[N64ModernRuntime](https://github.com/N64Recomp/N64ModernRuntime),
[RecompFrontend](https://github.com/N64Recomp/RecompFrontend), the game project
[`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp), the UWP forks by
**worleydl**, or the cheats mod by **Deozaan**. Nothing here is sold, and nothing here is asked
for in return.

## What is not distributed here

- **No ROM, no game data, no game assets.** You bring your own ROM; the recipe never downloads
  one and this repository never contained one.
- **No recompiled code.** The C the recompiler produces from the ROM is a derivative of the ROM
  and stays on the machine that built it.
- **No executable and no package.** No `.exe`, no `.msix`, no `.appx`.
- **No art.** The package's tiles are not in here; the game's own art least of all.
- **None of worleydl's patches**, and none of his UWP dependency bundle. The recipe fetches both
  from his repositories.
- **No wrapper project.** The `uwp/` folder that produces the appx derives from worleydl's and
  belongs in his repositories, not here.
- **None of the game project's own 24 runtime patches.** They are in its repository and the
  recipe runs the project's own script to apply them.
- **Not the cheats mod.** [Hotwire 2049](https://github.com/Deozaan/Rush2049RecompCheatsMod) is
  Deozaan's work; the README only says where to get it and what it does.

## How much of other people's work is quoted, and why

The tools in `tools/` work by matching **exact anchors** in the trees they patch: they find a
known piece of text and put something in its place. Those anchors are lines of other people's
code, and the only way to publish a working tool is to publish them.

**How this was measured.** Every string literal in each tool was taken apart line by line, and
each line was looked for **only in the files that tool declares it touches** — so a generic line
is never credited to the wrong file. Each file was checked in two versions: as the project
publishes it (`HEAD`), and as it stands after worleydl's UWP patches are applied. A line found
only in the second is the *"theirs"* side of his patch: a fork keeps its original's license, so
those lines belong to the project they live in and are listed under it.

| Project | License | Lines quoted | Where |
|---|---|---|---|
| [`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp) | GPL-3.0 | **17** | `parche_uwp_build.py` — the anchors in `CMakeLists.txt` (13) and `src/main.cpp` (4) |
| [`rt64`](https://github.com/rt64/rt64) | MIT | **18** | `resolver_conflictos.py` — the conflict markers of `rt64_application.cpp` (9) and `rt64_application_window.cpp` (9) |
| [`N64ModernRuntime`](https://github.com/N64Recomp/N64ModernRuntime) | GPL-3.0 | **12** | `resolver_conflictos.py` — `addresses.hpp` (7) and `recomp.cpp` (5) |
| [`RecompFrontend`](https://github.com/N64Recomp/RecompFrontend) | GPL-3.0 | **3** | `parche_data_path.py` — the anchors in `recompui/src/util/file.cpp` |
| | | **50 in total** | |

Of those 50, **24 are in the projects as published** and 26 are the *"theirs"* side of worleydl's
patches inside `rt64` (17) and `N64ModernRuntime` (9). Some of them carry his comments
(`// DLW: …`) for that reason.

Everything the tools **write** is this project's own and is not counted above.

`tools/graphics-xbox.json` quotes nothing: it is a settings file, and every value in it was
measured on the console.

### Why two of the tools quote nothing of this game's

`resolver_conflictos.py` and `parche_data_path.py` match text in the **libraries** — `rt64`,
`N64ModernRuntime` and `RecompFrontend` — and not a line of the game itself. That is why all the
lines credited to them above belong to those three projects, and why they resolved this tree
without a single change: what they depend on is the library commits listed in the README, not
Rush 2049. Their anchors are measured above against **this** tree, which is the only tree
anything here claims to have been measured on.

## The game project is written by AI

[`n64hub/rush-2049-recomp`](https://github.com/n64hub/rush-2049-recomp) states in its own README
that it is written by AI agents, directed and play-tested by a person. That is its authors'
statement, repeated here because anyone following this recipe should know what they are building,
not as a judgement of it.

## Contact

If you hold rights in any of the above and want something here taken down, write to
**jajdpmail@gmail.com** and it will be removed.
