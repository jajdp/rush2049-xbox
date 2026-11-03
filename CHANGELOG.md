# Changelog

All notable changes to this repository. Dates are `YYYY-MM-DD`.

This file is not translated: it is a historical record that grows with each version, and
translating it would mean two histories that drift apart.

## [1.0.1] — 2026-11-03

Documentation only. Nothing in the recipe or the tools changed behaviour, and that was checked
rather than assumed: the tools still reproduce the tree that is built and running, byte for byte,
and `compilar.ps1` still parses under the Windows PowerShell 5.1 a clean Windows ships with.

### Changed

- **This repository no longer leans on another game's port to explain itself.** The recipe used
  to be introduced as "the same one published for another project", and a dozen passages
  explained this game by comparing it against that one — which asked a reader who came here for
  Rush 2049 to go and read about a different game first. Everything those comparisons carried is
  now stated here on its own terms: the library commits this project pins and what each one
  costs against worleydl's patches; where the anchors are and why `parche_uwp_build.py` takes
  nothing but the tree; and why the other two tools are not specific to this game at all. The
  only repositories cited now are the ones this recipe is actually built on.
- **The FPS counter is documented instead of pointed at.** It is still not in here — it is a
  diagnostic tool rather than a part of the port — but `docs/HOW-IT-WORKS.md` now gives every
  decision in it: where it hooks and why that is the only point that works, why counting the
  game's own frames tells you nothing, what it draws with, why R3 is free, and ⚠ why the file
  switch has to be looked for in the data folder and not the working directory. Enough to write
  one in an afternoon.

### Fixed

- `compilar.ps1` has **seven** steps, not six. The README and this file both left out `pc`, the
  desktop build — which is the step that gives you something to compare a graphics fault
  against, and is how the Stunt arena fault was diagnosed.

## [1.0.0] — 2026-11-02

First release. The recipe for taking **San Francisco Rush 2049: Recompiled** to an Xbox Series X
in Developer Mode, as it was actually done on 2026-11-02.

### Added

- `tools/compilar.ps1` — the whole recipe in seven steps (`rom`, `runtime`, `parches`,
  `recompilar`, `pc`, `libs`, `appx`), each repeatable on its own, with the reason for each
  decision beside it.
- `tools/parche_uwp_build.py` — the three changes the game itself needs, by exact anchors,
  idempotent. **The anchors are this game's**: `main()` is in `src/main.cpp`, and the desktop
  executable's block reaches further than expected — the `.rc` icon and `/SUBSYSTEM:WINDOWS` as
  well as the DLLs and desktop SDL2.
- `tools/resolver_conflictos.py` and `tools/parche_data_path.py` — they match text in the
  libraries rather than in the game, and they resolved this tree without a single change, which
  is the measurement that mattered.
- `tools/graphics-xbox.json` — the video settings this console will take, ready to upload. Four
  options have to be left alone; everything else, high resolution included, can stay on.
- `docs/HOW-IT-WORKS.md` — the two builds, the four things that each cost an attempt, and the
  traps, each with the error it actually produces.
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
- The FPS counter patch is not here: it is a diagnostic tool rather than a part of the port.
  `docs/HOW-IT-WORKS.md` gives every decision in it — where it hooks, what it draws with, and why
  R3 — in enough detail to write one.
- A Series S has never been tried.
