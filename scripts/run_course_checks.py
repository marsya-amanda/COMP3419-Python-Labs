"""Run non-interactive checks for the portable COMP3419 code release."""

from __future__ import annotations

import json
from pathlib import Path
import py_compile
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {
    ".git",
    ".venv",
    ".ipynb_checkpoints",
    "__MACOSX",
    "dist",
    "frames",
    "legacy",
    "outputs",
}

# Stable cell IDs make the student-facing TODO contract part of the release
# manifest.  Each token list checks task-specific substance in addition to the
# common Inputs/Expected output headings.
TODO_NOTEBOOK_CONTRACTS: dict[Path, dict[str, tuple[str, ...]]] = {
    Path("COMP3419-W01-Lab-Files/week01_python_image_foundations.ipynb"): {
        "9e43c0b4": ("uint8", "(h, w, 3)", "independent", "boolean"),
    },
    Path(
        "COMP3419-W02-Lab-Files/"
        "COMP3419-W02-Lab-Image Enhancement.ipynb"
    ): {
        "a5b5593f": ("float64", "(3, 3)", "sums to 1"),
        "3ba33b66": ("float64", "same", "unclipped", "unchanged"),
        "2a58b734": ("2-d uint8", "same-shape", "constant", "does not mutate"),
    },
    Path(
        "COMP3419-W03-Lab-Files/"
        "COMP3419-W03-Lab-Morphological Image Processing.ipynb"
    ): {
        "1bbf25c2": ("boolean", "(h, w)", "outside-image", "unchanged"),
        "4eb00d2b": ("min_area", "8-connected", "boolean", "unchanged"),
    },
    Path("COMP3419-W04-Lab-Files/week04_video_compositing.ipynb"): {
        "w4-run": ("positive int", "none", "compositereport", "writes"),
    },
    Path("COMP3419-W05-Lab-Files/week05_object_tracking.ipynb"): {
        "w5-component-detection-todo": (
            "uint8",
            "(h, w)",
            "componentdetection",
            "circularity",
            "neither input may be mutated",
        ),
        "w5-association-todo": (
            "sequence",
            "euclidean-distance",
            "inclusive distance gate",
            "does not mutate or reorder",
        ),
        "w5-kalman-update-todo": (
            "float64",
            "(4, 1)",
            "seconds",
            "joseph-form",
            "positive semidefinite",
        ),
    },
    Path("COMP3419-W06-Lab-Files/week06_audio.ipynb"): {
        "measure-clipping": (
            "float32",
            "independent float32",
            "outside [-1, 1]",
            "inputs are not",
            "mutated",
        ),
        "synthesise-tone": (
            "float64",
            "frames//2 + 1",
            "hann window",
            "nyquist scaling",
        ),
        "filter-validation": (
            "float32",
            "same shape",
            "second-order sections",
            "axis 0",
            "leaves the input unchanged",
        ),
    },
    Path("COMP3419-W08-Lab-Files/week08_hough_transform.ipynb"): {
        "w08-canny": ("uint8", "(h, w)", "0 or 255"),
        "w08-vote": ("uint32", "float64", "radians", "seconds"),
        "w08-peaks": ("houghpeak", "rho_radius", "theta_radius"),
    },
    Path("COMP3419-W09-Lab-Files/week09_template_matching.ipynb"): {
        "w09-manual": (
            "uint8",
            "float64",
            "hi-ht+1",
            "top-left coordinate",
            "neither input is mutated",
        ),
        "w09-nms": (
            "templatematch",
            "top-left",
            "best-to-worst",
            "input score map is not mutated",
        ),
        "w09-scale": ("float64", "tuples", "top-left", "plot"),
        "w09-features": ("featurematchresult", "sift", "orb", "dmatch"),
    },
}

TODO_PYTHON_CONTRACTS: dict[Path, tuple[int, tuple[str, ...]]] = {
    Path("COMP3419-Assignment1b-Starter/assignment1b_starter/factory.py"): (
        3,
        ("float64", "shape (3,)", "expected output:", "rng"),
    ),
    Path("COMP3419-Assignment1b-Starter/assignment1b_starter/physics.py"): (
        7,
        ("mutates:", "expected output:", "return ``none``", "hpr"),
    ),
}

# Week 7's interactive notebook reuses the Python starter. Its three top-level
# contract blocks are keyed by function name so a deleted, duplicated, or
# relabelled implementation task is detected just like a stable notebook ID.
STUDENT_PYTHON_CONTRACTS: dict[Path, dict[str, tuple[str, ...]]] = {
    Path("COMP3419-W07-Lab-Files/checkpoint_scene.py"): {
        "student_build_hierarchy": (
            "nodepath",
            "orbit_radius",
            "checkpointnodes",
            "8-position",
            "12-triangle",
        ),
        "student_advance_angles": (
            "degrees/second",
            "dt_seconds",
            "modulo",
            "does not mutate",
        ),
        "student_apply_angles": (
            "returns none",
            "mutates only",
            "local_spin",
            "orbit_pivot",
            "orbit_spin",
        ),
    },
}

PRIVATE_HOME_PATTERNS = (
    re.compile(r"/(?:home|Users)/[^/\s\"']+/"),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s\"']+\\"),
)


def is_course_file(path: Path) -> bool:
    return not EXCLUDED_PARTS.intersection(path.relative_to(ROOT).parts)


def check_python_files() -> list[str]:
    failures: list[str] = []
    python_files = sorted(path for path in ROOT.rglob("*.py") if is_course_file(path))
    for path in python_files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            failures.append(f"cannot compile {path.relative_to(ROOT)}: {exc.msg}")
    print(f"Python syntax: {len(python_files)} files")
    return failures


def check_notebooks() -> list[str]:
    failures: list[str] = []
    notebooks = sorted(path for path in ROOT.rglob("*.ipynb") if is_course_file(path))
    for path in notebooks:
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"invalid notebook {path.relative_to(ROOT)}: {exc}")
            continue

        if notebook.get("nbformat") != 4:
            failures.append(
                f"{path.relative_to(ROOT)} uses unsupported "
                f"nbformat {notebook.get('nbformat')!r}"
            )

        language_info = notebook.get("metadata", {}).get("language_info", {})
        if not str(language_info.get("version", "")).startswith("3.12"):
            failures.append(
                f"{path.relative_to(ROOT)} does not declare the Python 3.12 kernel"
            )

        cells = notebook.get("cells")
        if not isinstance(cells, list) or not cells:
            failures.append(f"{path.relative_to(ROOT)} has no cells")

    noun = "file" if len(notebooks) == 1 else "files"
    print(f"Notebook structure: {len(notebooks)} {noun}")
    return failures


def _cell_source(cell: dict[str, object]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(str(item) for item in source)
    return str(source)


def _text_value(value: object) -> str:
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def check_notebook_privacy() -> list[str]:
    """Reject saved notebook text that exposes a machine-specific home path."""

    failures: list[str] = []
    checked = 0
    notebooks = sorted(path for path in ROOT.rglob("*.ipynb") if is_course_file(path))
    for path in notebooks:
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # check_notebooks reports the more useful structural error.
            continue
        for index, cell in enumerate(notebook.get("cells", [])):
            if not isinstance(cell, dict):
                continue
            text_parts = [_cell_source(cell)]
            for output in cell.get("outputs", []):
                if not isinstance(output, dict):
                    continue
                if "text" in output:
                    text_parts.append(_text_value(output["text"]))
                if "traceback" in output:
                    text_parts.append(_text_value(output["traceback"]))
                data = output.get("data", {})
                if isinstance(data, dict):
                    for mime_type in ("text/plain", "text/markdown", "text/html"):
                        if mime_type in data:
                            text_parts.append(_text_value(data[mime_type]))

            checked += 1
            combined = "\n".join(text_parts)
            if any(pattern.search(combined) for pattern in PRIVATE_HOME_PATTERNS):
                cell_id = str(cell.get("id", index))
                failures.append(
                    f"{path.relative_to(ROOT)}#{cell_id} contains a private "
                    "absolute home path"
                )

    print(f"Notebook privacy: {checked} cells")
    return failures


def check_todo_contracts() -> list[str]:
    """Require concrete type and I/O guidance in every TODO code block."""

    failures: list[str] = []
    checked_notebook_cells = 0

    for relative_path, expected_cells in TODO_NOTEBOOK_CONTRACTS.items():
        path = ROOT / relative_path
        if not path.is_file():
            # The checker is distributed in Week 1 and must remain useful as
            # later weekly folders are added to the persistent course root.
            continue
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            failures.append(f"cannot inspect TODO contracts in {relative_path}: {exc}")
            continue

        actual_todo_cells: dict[str, str] = {}
        for cell in notebook.get("cells", []):
            if not isinstance(cell, dict) or cell.get("cell_type") != "code":
                continue
            source = _cell_source(cell)
            if "TODO" not in source:
                continue
            cell_id = str(cell.get("id", ""))
            actual_todo_cells[cell_id] = source

        missing_ids = sorted(set(expected_cells).difference(actual_todo_cells))
        unexpected_ids = sorted(set(actual_todo_cells).difference(expected_cells))
        if missing_ids:
            failures.append(
                f"{relative_path} is missing TODO cells: {', '.join(missing_ids)}"
            )
        if unexpected_ids:
            failures.append(
                f"{relative_path} has undocumented TODO cells: "
                + ", ".join(unexpected_ids)
            )

        for cell_id, required_tokens in expected_cells.items():
            source = actual_todo_cells.get(cell_id)
            if source is None:
                continue
            checked_notebook_cells += 1
            lowered = source.lower()
            if "# inputs:" not in lowered or "# expected output:" not in lowered:
                failures.append(
                    f"{relative_path}#{cell_id} lacks Inputs/Expected output headings"
                )
            missing_tokens = [
                token for token in required_tokens if token.lower() not in lowered
            ]
            if missing_tokens:
                failures.append(
                    f"{relative_path}#{cell_id} lacks contract details: "
                    + ", ".join(missing_tokens)
                )

    checked_student_python_functions = 0
    for relative_path, expected_functions in STUDENT_PYTHON_CONTRACTS.items():
        path = ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing student TODO starter: {relative_path}")
            continue

        source = path.read_text(encoding="utf-8")
        marker_count = source.count("TODO(student)")
        if marker_count != len(expected_functions):
            failures.append(
                f"{relative_path} has {marker_count} TODO(student) markers; "
                f"expected {len(expected_functions)}"
            )

        # Each top-level contract begins with '# Inputs:' and owns the text up
        # to the next contract. This associates detailed claims with a stable
        # function name without treating unrelated prose as a TODO contract.
        contract_segments = source.split("# Inputs:")[1:]
        actual_functions: dict[str, str] = {}
        for segment in contract_segments:
            for function_name in expected_functions:
                if re.search(rf"^def {re.escape(function_name)}\s*\(", segment, re.M):
                    actual_functions[function_name] = segment

        missing_functions = sorted(set(expected_functions).difference(actual_functions))
        if missing_functions:
            failures.append(
                f"{relative_path} is missing TODO functions or local contracts: "
                + ", ".join(missing_functions)
            )

        for function_name, required_tokens in expected_functions.items():
            segment = actual_functions.get(function_name)
            if segment is None:
                continue
            checked_student_python_functions += 1
            lowered = segment.lower()
            if "# expected output:" not in lowered or "todo(student)" not in lowered:
                failures.append(
                    f"{relative_path}#{function_name} lacks an Expected output "
                    "heading or TODO(student) marker"
                )
            missing_tokens = [
                token for token in required_tokens if token.lower() not in lowered
            ]
            if missing_tokens:
                failures.append(
                    f"{relative_path}#{function_name} lacks contract details: "
                    + ", ".join(missing_tokens)
                )

    checked_python_markers = 0
    for relative_path, (expected_count, required_tokens) in (
        TODO_PYTHON_CONTRACTS.items()
    ):
        path = ROOT / relative_path
        if not path.is_file():
            continue
        source = path.read_text(encoding="utf-8")
        marker_count = source.count("TODO(assessed)")
        checked_python_markers += marker_count
        if marker_count != expected_count:
            failures.append(
                f"{relative_path} has {marker_count} TODO(assessed) markers; "
                f"expected {expected_count}"
            )

        # Every marker owns the text up to the next marker. This catches a new
        # or moved TODO that lacks its local contract even when the file has a
        # comprehensive module/method docstring elsewhere.
        for marker_index, segment in enumerate(
            source.split("TODO(assessed)")[1:], start=1
        ):
            lowered_segment = segment.lower()
            if "inputs:" not in lowered_segment or "expected output:" not in (
                lowered_segment
            ):
                failures.append(
                    f"{relative_path} TODO marker {marker_index} lacks a local "
                    "Inputs/Expected output contract"
                )

        lowered_source = source.lower()
        missing_tokens = [
            token for token in required_tokens if token.lower() not in lowered_source
        ]
        if missing_tokens:
            failures.append(
                f"{relative_path} lacks contract details: "
                + ", ".join(missing_tokens)
            )

    print(
        "TODO contracts: "
        f"{checked_notebook_cells} notebook cells, "
        f"{checked_student_python_functions} student Python functions, "
        f"{checked_python_markers} assessed markers"
    )
    return failures


def check_publication_separation() -> list[str]:
    """Keep canonical lab-sheet and assignment-spec sources out of the code tree."""

    forbidden: list[Path] = []
    for week in range(1, 10):
        directory = ROOT / f"COMP3419-W{week:02d}-Lab-Files"
        candidates = (
            directory / "LAB_SHEET.md",
            directory / f"COMP3419-W{week:02d}-LabSheet.pdf",
        )
        forbidden.extend(path for path in candidates if path.exists())

    duplicate_specs = (
        ROOT / "docs" / "latex" / "ASM1a" / "asm1a.tex",
        ROOT / "docs" / "latex" / "ASM1b" / "asm1b.tex",
    )
    forbidden.extend(path for path in duplicate_specs if path.exists())

    if forbidden:
        return [
            "publication source is embedded in the code repository: "
            + ", ".join(path.relative_to(ROOT).as_posix() for path in forbidden)
        ]

    print("Publication separation: lab sheets and specifications are LaTeX-only")
    return []


def run_unit_tests() -> list[str]:
    failures: list[str] = []
    test_directories = sorted(
        {
            path.parent
            for path in ROOT.rglob("test_*.py")
            if path.is_file() and is_course_file(path)
        }
    )
    for test_directory in test_directories:
        if test_directory.name == "tests":
            project_directory = test_directory.parent
            start_directory = "tests"
        else:
            project_directory = test_directory
            start_directory = "."
        command = [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            start_directory,
            "-p",
            "test_*.py",
        ]
        print(f"Unit tests: {project_directory.relative_to(ROOT)}", flush=True)
        result = subprocess.run(command, cwd=project_directory, check=False)
        if result.returncode:
            failures.append(
                f"unit tests failed in {project_directory.relative_to(ROOT)}"
            )
    if not test_directories:
        print("Unit tests: no test directories found")
    return failures


def check_student_release_manifest() -> list[str]:
    distributed_weeks = {
        week
        for week in range(1, 10)
        if (ROOT / f"COMP3419-W{week:02d}-Lab-Files").is_dir()
    }
    assignment_directories = (
        ROOT / "COMP3419-Assignment1a",
        ROOT / "COMP3419-Assignment1b-Starter",
    )
    release_builder = ROOT / "scripts" / "build_student_release.py"
    has_complete_qa_tree = (
        distributed_weeks == set(range(1, 10))
        and all(path.is_dir() for path in assignment_directories)
        and release_builder.is_file()
    )
    if not has_complete_qa_tree:
        weeks = ", ".join(str(week) for week in sorted(distributed_weeks)) or "none"
        print(
            "All-weeks QA manifest: skipped for cumulative weekly package "
            f"(weeks present: {weeks})"
        )
        return []

    try:
        from build_student_release import release_files, validate_manifest

        files = release_files()
        validate_manifest(files)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        return [f"student release manifest is invalid: {exc}"]
    print(f"All-weeks QA manifest: {len(files)} files")
    return []


def main() -> int:
    failures = check_python_files()
    failures.extend(check_notebooks())
    failures.extend(check_notebook_privacy())
    failures.extend(check_todo_contracts())
    failures.extend(check_publication_separation())
    failures.extend(run_unit_tests())
    failures.extend(check_student_release_manifest())

    if failures:
        print("\nCourse checks failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nCourse checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
