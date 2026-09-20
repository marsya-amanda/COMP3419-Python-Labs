"""Keep example previews separate from unfinished student implementations.

This is teaching scaffolding, not a plagiarism detector or copy-protection system.
Only the explicit unfinished-task exception enables a reference preview. Errors
in attempted implementations propagate normally and must never be hidden.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable, Any


class StudentImplementationRequired(NotImplementedError):
    """The student has not yet replaced the starter function body."""


class PreviewSession:
    """Label example output and track which tasks actually ran student code."""

    def __init__(self, references: dict[str, Callable[..., Any]]) -> None:
        self._references = dict(references)
        self.status = {name: "not run" for name in references}
        self.use_reference = True

    def exercise(self, name: str) -> Callable:
        if name not in self._references:
            raise KeyError(f"Unknown exercise: {name}")

        def decorate(student: Callable) -> Callable:
            # Re-running an edited definition invalidates its previous status.
            self.status[name] = "not run"

            @wraps(student)
            def run(*args: Any, **kwargs: Any) -> Any:
                previous = self.status[name]
                self.status[name] = "student error"
                try:
                    result = student(*args, **kwargs)
                except StudentImplementationRequired:
                    self.status[name] = "reference preview"
                    if not self.use_reference:
                        self.status[name] = "incomplete"
                        raise
                    if previous != "reference preview":
                        print(f"REFERENCE PREVIEW — TASK INCOMPLETE: {name}")
                    return self._references[name](*args, **kwargs)
                self.status[name] = "student output"
                if previous != "student output":
                    print(f"STUDENT OUTPUT: {name} — verify the assertions and results.")
                return result

            return run

        return decorate

    def report(self) -> None:
        print("Implementation status (reference previews do not complete a task):")
        for name, status in self.status.items():
            print(f"  {name}: {status}")
        if all(value == "student output" for value in self.status.values()):
            print("All task functions ran student code. Review every check; this is not a mark or proof of authorship.")
        else:
            print("Work remains. Replace the unfinished bodies and rerun their cells.")
