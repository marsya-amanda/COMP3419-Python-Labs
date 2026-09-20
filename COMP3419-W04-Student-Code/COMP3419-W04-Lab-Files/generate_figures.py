"""Regenerate the publication figure used by the Week 4 lab sheet.

The figure is derived from the supplied videos and the same keyer settings as
the notebook.  It does not depend on a display server or saved notebook output.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from video_compositing import (
    BACKGROUND_VIDEO,
    FOREGROUND_VIDEO,
    BlueScreenKeyer,
    Image,
    alpha_composite,
    blue_screen_mask,
    foreground_alpha,
    inspect_video,
    resize_to_cover,
)


LAB_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = LAB_DIR / "figures" / "chroma_key_pipeline.png"
FRAME_INDEX = 100


def read_frame(path: Path, frame_index: int) -> Image:
    """Decode one indexed frame or fail with a useful error."""

    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise FileNotFoundError(f"Could not open video: {path}")
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not decode frame {frame_index} from {path}")
        return frame
    finally:
        capture.release()


def main() -> int:
    foreground_info = inspect_video(FOREGROUND_VIDEO)
    background_info = inspect_video(BACKGROUND_VIDEO)
    source_time = FRAME_INDEX / foreground_info.fps
    background_index = (
        int(source_time * background_info.fps) % background_info.frame_count
    )

    foreground = read_frame(FOREGROUND_VIDEO, FRAME_INDEX)
    background = read_frame(BACKGROUND_VIDEO, background_index)
    background = resize_to_cover(
        background,
        foreground_info.width,
        foreground_info.height,
    )

    keyer = BlueScreenKeyer(
        lower_hsv=(90, 45, 20),
        upper_hsv=(140, 255, 255),
        morphology_radius=2,
        feather_radius=2,
    )
    screen_mask = blue_screen_mask(foreground, keyer)
    alpha = foreground_alpha(screen_mask, keyer.feather_radius)
    composite = alpha_composite(foreground, background, alpha)

    plt.rcParams.update(
        {
            "font.size": 12,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "figure.facecolor": "white",
        }
    )
    figure, axes = plt.subplots(2, 2, figsize=(12, 7), constrained_layout=True)
    panels = (
        (
            cv2.cvtColor(foreground, cv2.COLOR_BGR2RGB),
            "(a) Foreground frame",
            None,
            None,
        ),
        (screen_mask, "(b) Screen mask", "gray", (0, 255)),
        (alpha, "(c) Foreground alpha", "gray", (0, 1)),
        (
            cv2.cvtColor(composite, cv2.COLOR_BGR2RGB),
            "(d) Alpha composite",
            None,
            None,
        ),
    )
    for axis, (image, title, colour_map, limits) in zip(axes.flat, panels):
        kwargs: dict[str, object] = {}
        if colour_map is not None:
            kwargs["cmap"] = colour_map
        if limits is not None:
            kwargs["vmin"], kwargs["vmax"] = limits
        axis.imshow(image, **kwargs)
        axis.set_title(title)
        axis.axis("off")

    figure.suptitle(
        "HSV keying and vectorised alpha compositing "
        f"(foreground {FRAME_INDEX}, background {background_index})",
        fontsize=15,
        fontweight="bold",
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(
        OUTPUT_PATH,
        dpi=200,
        bbox_inches="tight",
        metadata={"Software": "COMP3419 Week 4 figure generator"},
    )
    plt.close(figure)
    print(f"Wrote {OUTPUT_PATH.relative_to(LAB_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
