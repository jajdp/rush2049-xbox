# The tools, and which one you actually run

**You run one: [`compilar.ps1`](compilar.ps1).** The other three it calls itself, in this order.
They are listed here so you can run one on its own when something fails halfway, and so you can
read what each does before letting it touch your tree.

| # | Tool | When `compilar.ps1` calls it | What it does |
|---|---|---|---|
| 1 | [`parche_uwp_build.py`](parche_uwp_build.py) | step `parches`, first | The three changes the **game itself** needs: the `UWP_BUILD` option in its `CMakeLists.txt`, renaming `main()` to `rush2049_uwp_main()`, and taking `SDL_INIT_HAPTIC` out under `_UWP`. ⚠ **This game's anchors** — see below |
| 2 | [`resolver_conflictos.py`](resolver_conflictos.py) | step `parches`, after worleydl's patches | The four conflicts those patches hit on this tree. All four resolve the same way: **keep both sides**, with worleydl's under `#ifdef _UWP` so the tree still builds for the desktop |
| 3 | [`parche_data_path.py`](parche_data_path.py) | step `parches`, last | Defines `recompui_uwp_data_path` in RecompFrontend and makes `get_app_folder_path` use it. **Without it the appx does not link** — see below |

[`graphics-xbox.json`](graphics-xbox.json) is not a tool: it is the video settings this console
will take, ready to upload to `LocalState`. The README explains every value in it, and three of
them are there because the alternative crashes the game.

**None of these three is the `runtime` step**, and that step is not optional. The game's project
applies **24 runtime patches of its own** with its own `tools/apply_runtime_patches.sh`, which
`compilar.ps1` runs for you. ⚠ It goes **before** worleydl's patches: the project's script checks
it can reverse what is already there and stops if the submodule has other changes on top.

All three tools are **idempotent**: run them twice and the second time they say "already there"
and change nothing. All three take the game's tree as an argument and have **no path of their
own** baked in.

## ⚠ Tool 1 is this tree's, and takes no other argument

It matches text in **this game's** `CMakeLists.txt` and `src/main.cpp`, so there is nothing to
parameterise and no target or prefix to pass:

- `main()` lives in `src/main.cpp`, not under `src/main/`;
- the desktop executable's block reaches further than you would expect: besides the DLL
  `POST_BUILD` and linking against desktop SDL2, it covers the `.rc` icon and
  `/SUBSYSTEM:WINDOWS` — all of which has to stay out of a static-library build.

Tools 2 and 3 are the other way round: every line they match is in `rt64`, `N64ModernRuntime` or
`RecompFrontend`, and not one is in the game. Nothing in them is specific to Rush 2049 — what
they depend on is the library commits the README lists, which is why they resolved this tree
without a change.

## ⚠ Tool 3 is the one that is easy to miss

It is not in any of worleydl's patches: it is this recipe's own, and the symptom of forgetting
it only shows at the very end, when the appx links:

```text
main.obj : error LNK2019: unresolved external symbol recompui_uwp_data_path
```

## Running one by hand

> **Where this goes:** in **PowerShell** — press the **Windows** key, type `powershell` and
> press **Enter** — in an **ordinary** window: no "run as administrator" needed, from this
> repository's folder.

```powershell
py -3.13 -X utf8 tools\parche_uwp_build.py <tree>
py -3.13 -X utf8 tools\resolver_conflictos.py <tree>
py -3.13 -X utf8 tools\parche_data_path.py <tree>
```

`<tree>` is the game's checkout — the folder with `CMakeLists.txt` and `src\main.cpp`.

## Roughly how long each step takes

Measured on a desktop with a recent 8-core CPU and an NVMe disk. Yours will differ, but the
*shape* will not: the recompile and the two builds are where the time goes.

| Step | Time |
|---|---|
| `rom` | seconds |
| `runtime` | seconds |
| `parches` | seconds |
| `recompilar` | a few minutes the first time |
| `pc` | a few minutes the first time, under a minute after a code change |
| `libs` | a few minutes the first time |
| `appx` | about a minute |

The hours are the one-off ones, and they are not in this table: installing Visual Studio with
the C++ and Clang tools, installing MSYS2, and the first `git clone --recurse-submodules`, which
pulls a few GB — and which, on this project, **has to be repeated** until no submodule is left
empty.

⚠ A rebuild being fast does **not** mean nothing happened — CMake and Ninja only redo what
depends on what changed. The way to check that a recompile really happened is the file count in
`RecompiledFuncs\`: this game produces **43**.
