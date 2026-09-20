"""Check the COMP3419 Python environment and representative lab media."""

from __future__ import annotations

from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]

# The checker validates audio loading without depending on a physical sound
# device. This affects only the checker process, not the lab applications.
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

PACKAGES = (
    "imageio",
    "ipykernel",
    "ipython",
    "ipywidgets",
    "jupyterlab",
    "matplotlib",
    "numpy",
    "opencv-python",
    "panda3d",
    "pillow",
    "pygame-ce",
    "scipy",
)

MODULES = (
    "imageio.v2",
    "IPython",
    "ipywidgets",
    "ipykernel",
    "jupyterlab",
    "matplotlib",
    "numpy",
    "cv2",
    "panda3d.core",
    "PIL",
    "pygame",
    "scipy",
)

IMAGES = (
    "COMP3419-W01-Lab-Files/sample_image.jpg",
    "COMP3419-W02-Lab-Files/parking.jpg",
    "COMP3419-W03-Lab-Files/W3LabData/BinaryTestImage.jpg",
    "COMP3419-W03-Lab-Files/W3LabData/coins.jpg",
    "COMP3419-W07-Lab-Files/W07LabData/earth.jpg",
    "COMP3419-W07-Lab-Files/W07LabData/moon.jpg",
    "COMP3419-W08-Lab-Files/W08LabData/binary.png",
    "COMP3419-W09-Lab-Files/W09LabData/input.png",
    "COMP3419-W09-Lab-Files/W09LabData/input_feature_based_matching.png",
    "COMP3419-W09-Lab-Files/W09LabData/template.png",
)

VIDEOS = (
    "COMP3419-W04-Lab-Files/W4LabData/monkey.avi",
    "COMP3419-W04-Lab-Files/W4LabData/Quadrangle.mov",
    "COMP3419-W05-Lab-Files/ping_pang.mov",
)

AUDIO = (
    "COMP3419-W06-Lab-Files/W6LabData/audio_drum.wav",
    "COMP3419-W06-Lab-Files/W6LabData/audio_sample.wav",
)


def distributed_media(paths: tuple[str, ...]) -> tuple[str, ...]:
    """Return media whose top-level weekly folder has been distributed."""

    return tuple(
        relative_path
        for relative_path in paths
        if (ROOT / Path(relative_path).parts[0]).is_dir()
    )


def main() -> int:
    failures: list[str] = []

    expected_week_directories = {
        Path(relative_path).parts[0]
        for relative_path in (*IMAGES, *VIDEOS, *AUDIO)
    }
    pending_week_directories = sorted(
        directory
        for directory in expected_week_directories
        if not (ROOT / directory).is_dir()
    )
    if pending_week_directories:
        print(
            "Media checks skipped for weekly packages not yet distributed: "
            + ", ".join(pending_week_directories)
        )

    expected_python = (3, 12)
    actual_python = sys.version_info[:2]
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    if actual_python != expected_python:
        failures.append(
            f"expected Python {expected_python[0]}.{expected_python[1]}, "
            f"found {actual_python[0]}.{actual_python[1]}"
        )

    for package in PACKAGES:
        try:
            package_version = version(package)
        except PackageNotFoundError:
            failures.append(f"missing package: {package}")
        else:
            print(f"{package}: {package_version}")

    for module in MODULES:
        try:
            import_module(module)
        except ImportError as exc:
            failures.append(f"cannot import {module}: {exc}")

    try:
        import cv2
        import numpy as np
        from scipy import ndimage
    except ImportError as exc:
        failures.append(f"scientific-stack import failed: {exc}")
    else:
        sample = np.zeros((5, 5), dtype=bool)
        sample[2, 2] = True
        expanded = ndimage.binary_dilation(sample, iterations=1)
        if int(expanded.sum()) != 5:
            failures.append("SciPy morphology smoke test returned an unexpected result")

        for relative_path in distributed_media(IMAGES):
            path = ROOT / relative_path
            image = cv2.imread(str(path))
            if image is None:
                failures.append(f"cannot read image: {relative_path}")
            else:
                print(f"image ok: {relative_path} {image.shape}")

        for relative_path in distributed_media(VIDEOS):
            path = ROOT / relative_path
            capture = cv2.VideoCapture(str(path))
            readable, frame = capture.read()
            capture.release()
            if not readable or frame is None:
                failures.append(f"cannot decode video: {relative_path}")
            else:
                print(f"video ok: {relative_path} {frame.shape}")

    try:
        import pygame
    except ImportError as exc:
        failures.append(f"pygame-ce audio import failed: {exc}")
    else:
        try:
            pygame.mixer.init()
            for relative_path in distributed_media(AUDIO):
                path = ROOT / relative_path
                sound = pygame.mixer.Sound(path)
                if sound.get_length() <= 0:
                    failures.append(f"empty audio file: {relative_path}")
                else:
                    print(
                        f"audio ok: {relative_path} "
                        f"({sound.get_length():.2f} seconds)"
                    )
        except pygame.error as exc:
            failures.append(f"pygame-ce audio smoke test failed: {exc}")
        finally:
            pygame.mixer.quit()

    try:
        from panda3d.core import Mat4, Point3
    except ImportError as exc:
        failures.append(f"Panda3D import failed: {exc}")
    else:
        transformed = Mat4.translate_mat(1, 2, 3).xform_point(Point3(0, 0, 0))
        if not transformed.almost_equal(Point3(1, 2, 3)):
            failures.append("Panda3D transform smoke test returned an unexpected result")
        else:
            print("Panda3D transform ok")

    if failures:
        print("\nEnvironment check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("\nEnvironment check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
