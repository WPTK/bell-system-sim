# Remediation Report — Audit Sections 1–4

Companion to `AUDIT_REPORT.md`. That document records what the audit found;
this one records what was changed in response, what was deliberately left
alone, and what the measurements look like on either side of the work.

Scope: audit sections 1 (Language & Stack), 2 (Code Quality), 3 (Dead Code)
and 4 (Linting & Security). Section 5 (Historical Authenticity), section 6
(Engagement) and the section 7 roadmap past Priority 2 are untouched and
remain open.

## Measurements

| Measure | Before | After |
|---|---:|---:|
| ruff findings (`src` + `tests`) | 249 | **0** |
| mypy errors | 252 | **0 gated** (69 suppressed in `terminal.py`) |
| bandit HIGH severity | 3 | **0** |
| Undefined names at runtime (F821) | 179 | **0** |
| Tests | 0 real assertions | **195 passing** |
| CI | none (deleted in `8d417a8`) | restored, all steps verified |
| Modules that import successfully | 5 of 12 | **10 of 10** |
| `terminal.py` length | 10,224 lines | 8,492 lines |
| Commands reachable from dispatch | 69 | 70 |
| Commands with a manual page | 66 of 70 | **70 of 70** |
| Methods called but never defined | 9 | **0** |
| Unreachable lines after `return` | 96 | **0** |
| Broken command aliases | 8 | **0** |
| Installed console script | `ModuleNotFoundError` | works |

## What changed

### Section 1 — Language & Stack

The audit's verdict was that Python is the right language and no migration is
justified. That verdict was accepted; nothing was ported. The work was
structural.

- **The single systemic defect.** Seven modules had their import blocks pasted
  *inside* the module docstring, where they parse as a string literal. The
  modules compiled and then died with `NameError` on first use. Fixing this
  one paste error accounts for 179 of the 249 ruff findings.
- **A real package.** `src/bell_system/` now exists with one `cli.py` entry
  point, replacing four divergent launchers — `bell-system.py`,
  `bin/bell-system`, `src/main.py`, and a console script naming a
  `bell_system.cli` module that had never been written. `pip install -e .`
  followed by `bell-system` now works, which is what the README always claimed.
- **`--role N` works.** It previously set two attributes nothing read, and
  `run()` re-prompted for a role regardless.
- **The Replit stack is gone.** `package.json` (still named `rest-express`),
  `package-lock.json`, `server/index.ts` and `.replit` were removed. Nothing
  in the Python referenced them and four of the five npm scripts could not run.

### Section 2 — Code Quality

- **Dispatch table built once** during construction rather than rebuilt on
  every command.
- **Man pages extracted** to `bell_system/data/man_pages.py`. The literal was
  2,288 lines, roughly a fifth of the module, and is now data. Pages are
  copied per session so one session cannot mutate another's.
- **A display layer.** `console.py` holds terminal output primitives. Screen
  clearing writes the ANSI sequence directly instead of shelling out from
  three separate modules.
- **Command history** is recorded once instead of twice, and the bounded
  `deque` is no longer clobbered by a plain list assigned four lines later.
- **`trunk status`** was rejected as an unknown option by the very message
  that listed the available options; the manual page advertised four more
  subcommands that did not exist. Command, error message and manual page now
  agree, and a test enforces that rule across every command.
- **Placeholder text no longer leaks.** Thirty commands returned the internal
  string `"implementation follows pattern"`, which reads like real output.
  Three are now implemented from data the simulation already built (see
  below); the remaining 27 state plainly that the subsystem is not in this
  release and point at their manual page.

### Section 3 — Dead Code

- **Five orphaned modules deleted** (2,329 lines): `main.py`,
  `logging_enhancements.py`, `logging_diagnostics.py`,
  `ux_command_enhancements.py`, `performance_profiling.py`. Each was imported
  by nothing and crashed on import. The two logging modules defined the same
  class as each other, and `terminal.py` already implements rotating-file
  logging, command suggestions and timing natively — so no capability was lost.
- **The trouble-ticket engine is reachable.** `cmd_trouble` — a ~574-line
  procedural ticket system with dashboard, listing, detail, assignment,
  escalation and resolution — was missing from the dispatch table. It is the
  most substantial single thing the codebase had built and could not run.
- **Nine methods implemented** that were called but never defined: eight TNDS
  report generators (collection control, forecasting, hierarchy analysis,
  dynamic routing, five named reports, export handling) and manual ticket
  creation. These were whole command branches raising `AttributeError`.
- **96 unreachable lines removed.** Three report functions returned a bare
  header and stranded the body that built the actual report; the `crossbar`
  command emitted a heading with no data under it.
- **Orphaned state wired to commands.** Of twelve structures built at startup
  and never read, three now drive commands that were stubs: `alarm` reads
  `system_health` and `active_alarms` (and can acknowledge them), `handoff`
  reads `shift_handoff` cross-referenced against live tickets, and `tariff`
  reads `rate_structures`.
- Also removed: the shadowed duplicate `cmd_ps` (~520 unreachable lines), the
  dead `self.tickets` field, eight aliases pointing at handlers that never
  existed, `.DS_Store` and `logs/` (both already in `.gitignore`).

### Section 4 — Linting & Security

- **ruff clean** across `src` and `tests`. The dead `[tool.flake8]` block was
  removed — flake8 cannot read `pyproject.toml`, so that configuration had
  never taken effect. ruff does read it and supersedes flake8 here.
- **Typing.** `types.py` declares the shapes of the operational state. These
  dictionaries hold mixed value types, so a checker inferred `object` for
  every value and rejected the arithmetic done on them — 88 of the 252 mypy
  findings had that single cause. Nine of ten modules now check clean;
  `terminal.py`'s remaining backlog is suppressed by an explicit per-module
  override so the rest can be gated. Lifting that override is the next step.
- **No subprocess launches.** The three `os.system` screen clears were
  bandit's only HIGH findings.
- **Ctrl-C exits the role menu.** `KeyboardInterrupt` was caught alongside
  `ValueError` and reported as "Invalid input" inside an infinite loop, so the
  menu could not be escaped.
- **State goes to a per-user directory** (`BELL_SYSTEM_HOME`, else
  `XDG_STATE_HOME`, else `~/.local/state/bell-system`). The installed command
  previously created a `logs/` directory wherever it happened to be run.
- **Tab completion completes commands**, not host filesystem paths.
- **Bare `except:`** replaced; it silently swallowed history-write failures.

### Tests and CI

The previous suite had zero assertions and printed `Success Rate: 93.1%`
while all twelve of its role setups died with `NameError`. It was replaced
with 195 pytest tests that assert on real output.

Several are structural guards that fail the build if a repaired defect class
returns: imports inside docstrings, unreachable code after `return`, duplicate
method definitions, calls to undefined methods, aliases expanding to
unregistered commands, subcommands advertised but not implemented, commands
without manual pages, and modules shelling out to clear the screen.

Writing them surfaced two live bugs: manual ticket creation lowercased the
category before matching uppercase keys, so every `trouble create` was
rejected; and four commands had no manual page.

CI was restored in place of the 132-line workflow deleted in `8d417a8`. That
one targeted Python 3.6 and a `--test` flag that never worked, which is why it
was removed. The replacement gates undefined names as a hard failure — the
check that would have caught the original defect — then runs ruff, the suite
on Python 3.9 through 3.12, and an end-to-end run of the installed console
script. Every step was verified locally before being committed.

### Documentation

Module paths, import forms, class names and run commands were corrected
throughout `README.md` and `docs/`. Documentation of deleted modules was
removed, noting that their logging, suggestion and timing features still exist
inside `terminal.py`. Fabricated environment variables were replaced with the
real `BELL_SYSTEM_HOME`.

Two documents were deleted for asserting things that were not true:

- `docs/security_audit.md` described "secure" classes and validators that
  exist nowhere in the codebase, with a 0-of-8 implementation checklist.
- `docs/test_validation_report.md` claimed "100% validation success" and
  "COMPLETE" while all eleven of its role sections read "Pending".

Where the documentation claimed role-based access control was enforced, it now
says plainly that role only filters the `help` listing — `execute_command`
performs no permission check.

## Deliberately not done

- **`attached_assets/` was kept.** The audit flagged 187 MB with only one file
  referenced by code. Those are period Bell System scans — the source material
  for the historical-accuracy work in section 5 — so deleting them would harm
  the next phase. Shrinking the repository properly means rewriting history to
  move them to LFS or a release download, which is destructive on a branch with
  an open pull request and needs an explicit decision.
- **The god class was not split.** `terminal.py` is still 8,492 lines and 166
  methods. Extracting the man pages removed the largest mechanical chunk;
  splitting the class along behavioural seams is a large refactor that is much
  safer now that a real test suite exists, and is better done as its own change.
- **The 27 remaining stubs were not implemented.** Filling them in is feature
  work from the section 7 roadmap, not a section 1–4 defect. They now report
  their own absence honestly instead of emitting placeholder text.
- **`terminal.py`'s 69 mypy findings** are suppressed rather than fixed, for
  the same reason: they are a backlog to ratchet down, not a blocker.
- **In-loop string accumulation** (roughly 72 `+=` sites) was left alone. The
  audit rated it minor and the loops are short; the churn would outweigh the
  benefit.
- **`docs/ux_improvements.md`** was left in place. It proposes a design that
  already shipped and mentions two aliases that have since been removed as
  broken, but it reads as a historical design note rather than a false
  assurance, so removing it is a judgement call for the maintainer.

## Known remaining issues

- Bare subcommands that require an argument report `Unknown option 'detail'`
  rather than explaining that an argument is missing. Misleading, but not a
  missing implementation; there are roughly 17 such sites.
- The simulation still prints the real wall-clock date in a setting dated
  1978–1983. This is the first item of section 5 and was left for that phase.
