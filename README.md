# COMP3419 lab codebase

This repository uses one course-level Python virtual environment managed by
[`uv`](https://docs.astral.sh/uv/). Anaconda, Miniconda, and manual package
installation are not required.

The shared environment covers every lab session and both parts of Assignment 1,
including the Python replacements for the former Processing-based Week 6,
Week 7, and Assignment 1b material. The `.pde` files remain only as staff
migration references; students need neither Anaconda nor Processing.
Assignment 2 is outside this environment and will be handled separately.

## Install `uv`

Install `uv` once on the computer. A separate Python, Anaconda, or Miniconda
installation is not required. The commands below are from the
[official `uv` installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### macOS

These steps use the Terminal application with its default `zsh` shell. The
locked binary packages target macOS 13 or later on Apple Silicon and macOS 14
or later on Intel Macs.

1. Open **Terminal**.
2. Install `uv` with the official standalone installer:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

   If Homebrew is already installed, `brew install uv` is an alternative. Use
   one installation method, not both.
3. Close and reopen Terminal so that its updated `PATH` is loaded.
4. Confirm that the installation works:

   ```bash
   uv --version
   ```

### Windows 10 or 11

Use native 64-bit Windows on an Intel or AMD PC and **PowerShell** for these
steps. Windows on Arm is not currently part of the supported course setup. WSL
is not recommended because the audio and interactive graphics labs need access
to the Windows desktop, speakers, and graphics driver.

1. Open **PowerShell** from the Start menu. Administrator access is not needed.
2. Install `uv` with the official standalone installer:

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

   On a managed computer that blocks downloaded PowerShell scripts, the
   official WinGet package is an alternative:

   ```powershell
   winget install --id=astral-sh.uv -e
   ```
3. Close and reopen PowerShell so that its updated `PATH` is loaded.
4. Confirm that the installation works:

   ```powershell
   uv --version
   ```

### Linux

Open a terminal, run the same standalone installer used for macOS, restart the
terminal, and confirm the result with `uv --version`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Week 1 structure and setup guide

The Week 1 ZIP is the one-time bootstrap package. It creates the persistent
`COMP3419-Python-Labs` course root and includes this guide, the locked `uv`
environment files, student check scripts, and the complete Week 1 folder. Move
that course root to a stable location and keep using it throughout the semester.

Use one shared `.venv` for all lab sessions and both parts of Assignment 1.
Each copy of the course root has its own `.venv`; do not copy `.venv` between
computers or operating systems, and do not create a separate environment for
each week.

### Keep the weekly package structure

The code package for each week is distributed separately. Fully extract every
ZIP; do not run a notebook from inside a ZIP or drag only the notebook or data
files elsewhere. The `.python-version` bootstrap file may be hidden by Finder
or File Explorer, so always copy or move the complete folder.

The expected layout is:

```text
COMP3419-Python-Labs/
├── README.md
├── .gitignore
├── .python-version
├── pyproject.toml
├── uv.lock
├── .venv/                 # created locally by uv
├── scripts/
├── COMP3419-W01-Lab-Files/
├── COMP3419-W02-Lab-Files/
└── ...
```

Keep earlier week folders and your completed work when adding a new package.
Do not rename a week folder, flatten its contents, or place one week folder
inside another. Notebooks, Python modules, data, media, and tests use relative
paths based on this structure. Run `uv` commands from the course root—the
directory containing `pyproject.toml` and `uv.lock`—unless a weekly guide
explicitly says otherwise.

### Week 1: create the course root once

1. Download and fully extract `COMP3419-W01-Student-Code.zip`. It contains one
   folder named `COMP3419-Python-Labs`.
2. If Finder or Windows **Extract All** adds a package-name wrapper, open that
   wrapper and use the inner `COMP3419-Python-Labs` folder as the course root.
3. Move that one course-root folder to a stable location. Verify that it
   contains `README.md`, `.gitignore`, `.python-version`, `pyproject.toml`,
   `uv.lock`, `scripts/`, and `COMP3419-W01-Lab-Files/`. To reveal hidden
   files, press **Command+Shift+.** in macOS Finder, run `ls -la` in a
   macOS/Linux terminal, or run `Get-ChildItem -Force` in PowerShell.
4. Keep the entire folder for the semester, including work completed in the
   Week 1 notebook.

### Weeks 2–9: add one intact weekly folder

1. Fully extract the new weekly ZIP in Downloads or another temporary folder.
2. Locate its single weekly folder—for example,
   `COMP3419-W02-Lab-Files` for Week 2—and move that folder directly into the
   existing `COMP3419-Python-Labs` course root, beside the earlier weeks. The
   two digits change with the week number. Discard only an archive-name wrapper
   created by the extractor.
   If that exact weekly folder already exists, do not replace it and lose your
   work; confirm that you downloaded the intended week or ask your tutor.
3. Keep the existing `.venv`, earlier week folders, and your completed work.
   Do not create a second course root or run `uv sync` inside a weekly folder.
4. From the course root, run
   `uv run --locked python scripts/check_environment.py`. You can also run
   `uv run --locked python scripts/run_course_checks.py` to check every weekly
   folder installed so far.

These nested or renamed layouts are incorrect:

```text
COMP3419-Python-Labs/COMP3419-Python-Labs/...
COMP3419-Python-Labs/COMP3419-W01-Lab-Files/COMP3419-W02-Lab-Files/...
COMP3419-Python-Labs/COMP3419-W02-Student-Code/COMP3419-W02-Lab-Files/...
```

### Create and use the shared environment

1. Open Terminal on macOS/Linux or PowerShell on Windows and change to the
   extracted course root. Quote the path if it contains spaces:

   macOS example:

   ```bash
   cd "/Users/your-name/Documents/COMP3419-Python-Labs"
   ```

   Windows PowerShell example:

   ```powershell
   cd "C:\Users\your-name\Documents\COMP3419-Python-Labs"
   ```
2. Create `.venv` and install the exact locked dependencies:

   ```text
   uv sync --locked
   ```

   `uv` reads `.python-version`, downloads Python 3.12 if necessary, and creates
   `.venv` automatically. Do not run `pip install` or create another
   environment first.
3. Check Python, the course libraries, and the supplied media:

   ```text
   uv run --locked python scripts/check_environment.py
   ```
4. Start JupyterLab:

   ```text
   uv run --locked jupyter lab
   ```

The three `uv` commands above are identical in macOS Terminal, Windows
PowerShell, and Linux terminals. On later visits, open a terminal in the course
root and run the JupyterLab command again. Open a lab notebook and
select the `.venv`/Python 3 kernel if prompted.

Week 7 includes an [interactive scene-graph notebook](COMP3419-W07-Lab-Files/week07_scene_graphs.ipynb).
It needs `ipywidgets` from the updated shared environment. If your Week 1 setup
predates this notebook, apply the separately supplied
`COMP3419-W07-Environment-Update.zip` to the course root, preserving your weekly
folders. Stop JupyterLab, run `uv sync --locked`, then restart JupyterLab.
If controls show only text, confirm that you opened the notebook in JupyterLab
with the course kernel, not a static notebook preview.

## Reference notebooks and academic integrity

Some completed code cells in the supplied Jupyter notebooks are runnable
reference examples. They present the method and allow each notebook to execute
from start to finish; they are not model answers and are not authorised for
reuse in assessed work. Your submitted code must be your own, and you must be
able to explain it.

Copying, lightly modifying, translating, or closely reproducing supplied
reference code in a submission is plagiarism. **Any submission found to
plagiarise the supplied reference code will receive zero marks** and may also
be referred under the University Academic Integrity Policy.

## Current lab entry points

This repository contains runnable code, data, notebooks, tests, and concise
operational guides. The authoritative weekly lab sheets and Assignment 1
specifications are maintained and compiled in the separate
`COMP3419 Lab Tutorial` LaTeX repository. Students receive one PDF for each
week and one for each part of Assignment 1; those handouts remain separate from
the Python code archives.

Links below become available after the corresponding weekly or assignment
package has been added to the course root. Assignment 1 code is distributed
separately from the weekly lab packages.

| Session       | Current focus                                                                     | Code guide                                              |
| ------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------- |
| Week 1        | Orientation: uv, Python 3.12, and image-array foundations                         | [Open](COMP3419-W01-Lab-Files/README.md)                 |
| Week 2        | Convolution and histogram enhancement                                             | [Open](COMP3419-W02-Lab-Files/README.md)                 |
| Week 3        | Mathematical morphology and components                                            | [Open](COMP3419-W03-Lab-Files/README.md)                 |
| Week 4        | Streaming video compositing                                                       | [Open](COMP3419-W04-Lab-Files/README.md)                 |
| Week 5        | Detection, association, and Kalman tracking                                       | [Open](COMP3419-W05-Lab-Files/README.md)                 |
| Week 6        | Digital audio with NumPy/SciPy and `pygame-ce`                                  | [Open](COMP3419-W06-Lab-Files/README.md)                 |
| Week 7        | Panda3D geometry, transforms, and hierarchy                                       | [Open](COMP3419-W07-Lab-Files/README.md)                 |
| Week 8        | Canny and the Hough transform                                                     | [Open](COMP3419-W08-Lab-Files/README.md)                 |
| Week 9        | Template and feature matching                                                     | [Open](COMP3419-W09-Lab-Files/README.md)                 |
| Assignment 1a | Python macroblock motion estimation; specification only, with no solution starter | [Code-use note](COMP3419-Assignment1a/README.md)         |
| Assignment 1b | Python/Panda3D starter                                                            | [Starter guide](COMP3419-Assignment1b-Starter/README.md) |

The published book gives Weeks 2–9 student self-check checklists. Week 1 is
formative orientation and deliberately has no checkpoint checklist or
submission requirement. Historical PDFs and Processing sketches remain under
`legacy/` for staff reference and are excluded from the student release.

Run non-interactive syntax, notebook-structure, and unit checks for all week
folders currently installed with:

```bash
uv run --locked python scripts/run_course_checks.py
```

The checker discovers the cumulative weekly folders already present and does
not require packages for future weeks.

Week 6 and Week 7 also provide headless smoke-test commands in their guides.
Those checks complement, but do not replace, a tutor test of real speakers,
desktop windows, and graphics drivers on each managed platform.

## Build the weekly student distributions

In the staff source repository (not inside a distributed weekly package),
teaching staff can build all nine deterministic weekly ZIPs with:

```bash
uv run --locked python scripts/build_weekly_distributions.py
```

Build or rebuild one selected week with, for example:

```bash
uv run --locked python scripts/build_weekly_distributions.py --week 4
```

The archives are written to `dist/weekly/` as
`COMP3419-W01-Student-Code.zip` through
`COMP3419-W09-Student-Code.zip`. Week 1 contains the one-time course-root
bootstrap and this structure guide. Each later ZIP contains exactly one intact
weekly folder and no repeated environment files. Publication figures, lab
sheets, Processing sketches, caches, and generated outputs are excluded. The
reproducible figure-generation script is included when the corresponding lab
sheet asks students to run it; the script recreates its local `figures/`
directory.

## Build the all-weeks validation archive

In the staff source repository, teaching staff can build an all-weeks archive
to validate the complete codebase:

```bash
uv run --locked python scripts/build_student_release.py
```

The archive is written to `dist/COMP3419-Python-Labs.zip`. It is a staff QA
artifact, not the package distributed during an individual lab week. Students
receive the current weekly package and add its intact week folder to their
persistent course root as described above. The all-weeks archive excludes lab
sheets, publication figures, `legacy/`, Processing sketches, caches, and
generated outputs. Build the lab book independently from the canonical LaTeX
repository.

## VS Code

After `uv sync --locked`, choose the interpreter inside `.venv`:

- macOS/Linux: `.venv/bin/python`
- Windows: `.venv\Scripts\python.exe`

The environment already includes `ipykernel`, so it can also be selected as the
kernel for `.ipynb` files.

## Working without activation

Activation is optional. Prefer `uv run --locked <command>` so the command uses
the committed dependency resolution without changing it. If activation is
needed for an editor or shell:

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```batch
.\.venv\Scripts\activate.bat
```

If Windows reports that script execution is disabled, skip activation and use
the documented `uv run --locked ...` commands; activation is not required.

Do not install packages from inside a notebook. Course dependencies belong in
`pyproject.toml` and `uv.lock` so that every student and tutor gets the same
versions.

## Setup troubleshooting

| Problem                                             | Action                                                                                                                                                                                                                       |
| --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `uv` is not recognised or `command not found`       | Close all Terminal/PowerShell windows, open a new one, and retry `uv --version`. If it still fails, repeat the appropriate official installation method above and follow any `PATH` instruction printed by the installer. |
| The course-root path contains spaces                | Put the complete path in quotes, as in the `cd` examples above.                                                                                                                                                        |
| PowerShell blocks `.venv` activation                | Do not change a university computer's execution policy. Activation is optional; use `uv run --locked ...`.                                                                                                             |
| Jupyter uses the wrong Python                       | Stop JupyterLab, restart it from the course root, and select `.venv/bin/python` on macOS/Linux or `.venv\Scripts\python.exe` on Windows.                                                                               |
| Week 6 produces no sound                            | Check the operating system's selected output device and volume, then run the Week 6 smoke test documented in its `README.md`.                                                                                           |
| Week 7 cannot open a window                         | Run it on the local desktop rather than through SSH, WSL, or a headless session. Update the graphics driver and run the Week 7 offscreen smoke test documented in its `README.md`.                                      |
| A managed computer blocks installation or downloads | Use the approved package-manager alternative above or ask the teaching team/IT support; do not substitute Anaconda or install packages individually.                                                                         |

### Updating an earlier course package

If your course root was created from an earlier Week 1 ZIP, check for
`scripts/notebook_support.py` before running the revised labs. If it is missing,
extract the updated Week 1 ZIP into a temporary directory and copy only that
file into your existing course root’s `scripts` directory. Keep your existing
weekly folders and completed work. New installations already include it.
