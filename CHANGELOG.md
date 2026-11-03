# Changelog

All notable changes to this repository. Dates are `YYYY-MM-DD`.

This file is not translated: it is a historical record that grows with each version, and
translating it would mean two histories that drift apart.

## [1.0.0] — 2026-11-02

First release. The recipe for taking **San Francisco Rush 2049: Recompiled** to an Xbox Series X
in Developer Mode, as it was actually done on 2026-11-02.

### Added

- `tools/compilar.ps1` — the whole recipe in six steps (`rom`, `runtime`, `recompilar`,
  `parches`, `libs`, `appx`), each repeatable on its own, with the reason for each decision
  beside it.
- `tools/parche_uwp_build.py` — the three changes the game itself needs, by exact anchors,
  idempotent. **This game's anchors**, which are not Mario Party's: `main()` is in
  `src/main.cpp`, the `WIN32` block is worded differently, and the desktop executable's block
  reaches further.
- `tools/resolver_conflictos.py` and `tools/parche_data_path.py` — byte for byte the ones
  published in `marioparty-xbox`, verified with `cmp`. They resolved this tree without a single
  change, which is the measurement that mattered.
- `tools/graphics-xbox.json` — the video settings this console will take, ready to upload. Four
  options have to be left alone; everything else, high resolution included, can stay on.
- `docs/HOW-IT-WORKS.md` — the two builds, what this game does differently from Mario Party, and
  the traps, each with the error it actually produces.
- `docs/INSTALL.md` — requirements, the commands, getting it onto the console, and a symptom
  table.
- `NOTICE.md` — what is not distributed, and the 50 lines of other people's code this repository
  quotes, measured and attributed one by one against **this** tree.
- Spanish versions of the README, the notice and the docs.

### Measured on the console

Xbox Series X in Developer Mode, package 0.1.0.3, on 2026-11-02: boots, draws, validates the ROM
from `LocalState` on its own, loads mods, and runs at **56–60 FPS**. Played with a controller in
hand in the Stunt arena — not only the attract demo. Not every track and mode has been run end to
end.

### Known not to be covered

- The `uwp/` wrapper project is not here: it derives from worleydl's forks.
- worleydl's `.patch` files are not here either; the recipe applies them from his repositories.
- The game project's own 24 runtime patches are not here: the recipe runs that project's
  `tools/apply_runtime_patches.sh`.
- The FPS counter patch is not here: it belongs to the Mario Party projects it was written for,
  and applied to this tree unchanged because both pin the same `RecompFrontend` commit.
- A Series S has never been tried.
