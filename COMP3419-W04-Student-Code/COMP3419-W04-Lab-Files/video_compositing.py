"""Week 4 video compositing utilities.

The functions in this module deliberately operate on one frame at a time.  A
complete video can therefore be processed without writing an intermediate
directory of TIFF images or keeping every frame in memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray


LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "W4LabData"
FOREGROUND_VIDEO = DATA_DIR / "monkey.avi"
BACKGROUND_VIDEO = DATA_DIR / "Quadrangle.mov"

Image = NDArray[np.uint8]


@dataclass(frozen=True)
class VideoInfo:
    """Metadata needed to process a video without hard-coded assumptions."""

    path: Path
    width: int
    height: int
    fps: float
    frame_count: int
    codec: str

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / self.fps


@dataclass(frozen=True)
class BlueScreenKeyer:
    """Parameters for an HSV blue-screen key.

    OpenCV represents hue on [0, 179]. The supplied monkey video's blue screen
    is around 120 in that scale (approximately 240 degrees on a colour wheel).
    """

    lower_hsv: tuple[int, int, int] = (90, 45, 20)
    upper_hsv: tuple[int, int, int] = (140, 255, 255)
    morphology_radius: int = 2
    feather_radius: int = 2

    def __post_init__(self) -> None:
        if any(lo > hi for lo, hi in zip(self.lower_hsv, self.upper_hsv)):
            raise ValueError("Each lower HSV bound must be <= its upper bound")
        if self.morphology_radius < 0 or self.feather_radius < 0:
            raise ValueError("Morphology and feather radii must be non-negative")


@dataclass(frozen=True)
class CompositeReport:
    output_path: Path
    frames_written: int
    fps: float
    width: int
    height: int
    output_codec: str
    mean_screen_fraction: float


def _decode_fourcc(value: int) -> str:
    return "".join(chr((value >> (8 * index)) & 0xFF) for index in range(4)).strip()


def inspect_video(path: str | Path) -> VideoInfo:
    """Read and validate basic video metadata."""

    video_path = Path(path).expanduser().resolve()
    capture = cv2.VideoCapture(str(video_path))
    try:
        if not capture.isOpened():
            raise FileNotFoundError(f"Could not open video: {video_path}")
        width = int(round(capture.get(cv2.CAP_PROP_FRAME_WIDTH)))
        height = int(round(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(round(capture.get(cv2.CAP_PROP_FRAME_COUNT)))
        codec = _decode_fourcc(int(capture.get(cv2.CAP_PROP_FOURCC)))
    finally:
        capture.release()

    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid frame size reported for {video_path}")
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError(f"Invalid frame rate reported for {video_path}: {fps}")
    if frame_count <= 0:
        raise ValueError(f"No frames reported for {video_path}")
    return VideoInfo(video_path, width, height, fps, frame_count, codec)


def blue_screen_mask(frame_bgr: Image, keyer: BlueScreenKeyer) -> Image:
    """Return a cleaned uint8 mask: 255 for screen pixels, 0 for foreground."""

    if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        raise ValueError("Expected a BGR image with shape (height, width, 3)")
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(
        hsv,
        np.asarray(keyer.lower_hsv, dtype=np.uint8),
        np.asarray(keyer.upper_hsv, dtype=np.uint8),
    )
    if keyer.morphology_radius:
        size = 2 * keyer.morphology_radius + 1
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (size, size))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def foreground_alpha(screen_mask: Image, feather_radius: int = 2) -> NDArray[np.float32]:
    """Convert a screen mask to a soft foreground alpha matte on [0, 1]."""

    if screen_mask.ndim != 2:
        raise ValueError("Expected a single-channel screen mask")
    alpha = 1.0 - screen_mask.astype(np.float32) / 255.0
    if feather_radius:
        size = 2 * feather_radius + 1
        alpha = cv2.GaussianBlur(alpha, (size, size), sigmaX=0)
    return np.clip(alpha, 0.0, 1.0)


def alpha_composite(foreground_bgr: Image, background_bgr: Image, alpha: NDArray) -> Image:
    """Vectorised Porter-Duff 'over' compositing for equally sized BGR frames."""

    if foreground_bgr.shape != background_bgr.shape:
        raise ValueError("Foreground and background frames must have the same shape")
    if alpha.shape != foreground_bgr.shape[:2]:
        raise ValueError("Alpha must match the frame height and width")
    alpha_3d = np.asarray(alpha, dtype=np.float32)[..., None]
    result = (
        foreground_bgr.astype(np.float32) * alpha_3d
        + background_bgr.astype(np.float32) * (1.0 - alpha_3d)
    )
    return np.clip(np.rint(result), 0, 255).astype(np.uint8)


def resize_to_cover(frame: Image, width: int, height: int) -> Image:
    """Resize and centre-crop a frame without changing its aspect ratio."""

    source_height, source_width = frame.shape[:2]
    scale = max(width / source_width, height / source_height)
    resized = cv2.resize(
        frame,
        (int(np.ceil(source_width * scale)), int(np.ceil(source_height * scale))),
        interpolation=cv2.INTER_LINEAR,
    )
    y0 = (resized.shape[0] - height) // 2
    x0 = (resized.shape[1] - width) // 2
    return resized[y0 : y0 + height, x0 : x0 + width]


def _codec_candidates(path: Path) -> Sequence[str]:
    suffix = path.suffix.lower()
    if suffix == ".avi":
        return ("MJPG", "XVID")
    if suffix in {".mp4", ".m4v", ".mov"}:
        return ("mp4v", "avc1")
    raise ValueError("Use an .mp4, .m4v, .mov, or .avi output filename")


def open_video_writer(
    path: str | Path,
    fps: float,
    size: tuple[int, int],
    codec: str | None = None,
) -> tuple[cv2.VideoWriter, str]:
    """Open a writer, using a container-appropriate fallback codec if needed."""

    output_path = Path(path).expanduser().resolve()
    default_candidates = _codec_candidates(output_path)
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be positive")
    if size[0] <= 0 or size[1] <= 0:
        raise ValueError("Video width and height must be positive")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates = (codec,) if codec is not None else default_candidates
    for candidate in candidates:
        if candidate is None or len(candidate) != 4:
            raise ValueError("A codec must be a four-character code")
        writer = cv2.VideoWriter(
            str(output_path),
            cv2.VideoWriter_fourcc(*candidate),
            fps,
            size,
        )
        if writer.isOpened():
            return writer, candidate
        writer.release()
    raise RuntimeError(
        f"Could not open a video writer for {output_path}; tried {', '.join(candidates)}"
    )


class _LoopingBackground:
    """Sequential, cached access to a background video on a looping timeline."""

    def __init__(self, info: VideoInfo) -> None:
        self.info = info
        self.capture = cv2.VideoCapture(str(info.path))
        if not self.capture.isOpened():
            raise FileNotFoundError(f"Could not open background video: {info.path}")
        self._index = -1
        self._frame: Image | None = None

    def close(self) -> None:
        self.capture.release()

    def frame_at(self, seconds: float) -> Image:
        if not np.isfinite(seconds) or seconds < 0:
            raise ValueError("seconds must be finite and non-negative")
        target = int(np.floor(seconds * self.info.fps)) % self.info.frame_count
        if target < self._index:
            self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self._index = -1
            self._frame = None
        reset_attempted = False
        while self._index < target:
            ok, frame = self.capture.read()
            if not ok:
                if reset_attempted:
                    raise RuntimeError(
                        f"Could not decode background frame {target} "
                        f"from {self.info.path}"
                    )
                self.capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self._index = -1
                self._frame = None
                reset_attempted = True
                continue
            self._index += 1
            self._frame = frame
        if self._frame is None:
            raise RuntimeError(f"Could not decode a frame from {self.info.path}")
        return self._frame


def composite_videos(
    foreground_path: str | Path,
    background_path: str | Path,
    output_path: str | Path,
    *,
    keyer: BlueScreenKeyer = BlueScreenKeyer(),
    max_frames: int | None = None,
    codec: str | None = None,
) -> CompositeReport:
    """Stream a keyed foreground over a looping, time-synchronised background."""

    foreground_info = inspect_video(foreground_path)
    background_info = inspect_video(background_path)
    fps = foreground_info.fps
    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames must be positive or None")

    foreground = cv2.VideoCapture(str(foreground_info.path))
    if not foreground.isOpened():
        raise FileNotFoundError(
            f"Could not reopen foreground video: {foreground_info.path}"
        )
    background: _LoopingBackground | None = None
    writer: cv2.VideoWriter | None = None
    try:
        background = _LoopingBackground(background_info)
        writer, chosen_codec = open_video_writer(
            output_path,
            fps,
            (foreground_info.width, foreground_info.height),
            codec,
        )
    except Exception:
        foreground.release()
        if background is not None:
            background.close()
        raise
    assert background is not None and writer is not None

    frames_written = 0
    screen_fraction_sum = 0.0
    frames_to_write = (
        foreground_info.frame_count
        if max_frames is None
        else min(max_frames, foreground_info.frame_count)
    )
    try:
        while frames_written < frames_to_write:
            ok, foreground_frame = foreground.read()
            if not ok:
                raise RuntimeError(
                    "Foreground ended before its reported frame count: "
                    f"{foreground_info.path} (decoded {frames_written}, "
                    f"expected {frames_to_write})"
                )
            source_time = frames_written / foreground_info.fps
            background_frame = resize_to_cover(
                background.frame_at(source_time),
                foreground_info.width,
                foreground_info.height,
            )
            screen_mask = blue_screen_mask(foreground_frame, keyer)
            alpha = foreground_alpha(screen_mask, keyer.feather_radius)
            writer.write(alpha_composite(foreground_frame, background_frame, alpha))
            screen_fraction_sum += float(np.mean(screen_mask > 0))
            frames_written += 1
    finally:
        foreground.release()
        background.close()
        writer.release()

    if frames_written == 0:
        raise RuntimeError("No output frames were written")
    report = CompositeReport(
        Path(output_path).expanduser().resolve(),
        frames_written,
        fps,
        foreground_info.width,
        foreground_info.height,
        chosen_codec,
        screen_fraction_sum / frames_written,
    )
    validate_video(
        report.output_path,
        expected_frames=frames_written,
        expected_fps=fps,
        expected_size=(foreground_info.width, foreground_info.height),
    )
    return report


def validate_video(
    path: str | Path,
    *,
    expected_frames: int | None = None,
    expected_fps: float | None = None,
    expected_size: tuple[int, int] | None = None,
) -> VideoInfo:
    """Decode a written video sequentially and return validated metadata."""

    info = inspect_video(path)
    capture = cv2.VideoCapture(str(info.path))
    decoded_frames = 0
    try:
        if not capture.isOpened():
            raise RuntimeError(f"Could not reopen generated video: {info.path}")
        while True:
            readable, frame = capture.read()
            if not readable:
                break
            decoded_frames += 1
            if expected_size is not None:
                decoded_size = (frame.shape[1], frame.shape[0])
                if decoded_size != expected_size:
                    raise ValueError(
                        f"Expected frame size {expected_size}, "
                        f"decoded {decoded_size} at frame {decoded_frames - 1}"
                    )
    finally:
        capture.release()

    if decoded_frames == 0:
        raise ValueError(f"No frames could be decoded from {info.path}")
    if expected_frames is not None and decoded_frames != expected_frames:
        raise ValueError(f"Expected {expected_frames} frames, decoded {decoded_frames}")
    if expected_frames is None and abs(decoded_frames - info.frame_count) > 1:
        raise ValueError(
            f"Container reports {info.frame_count} frames, decoded {decoded_frames}"
        )
    if expected_fps is not None and not np.isclose(info.fps, expected_fps, rtol=0.02):
        raise ValueError(f"Expected about {expected_fps:.3f} FPS, decoded {info.fps:.3f}")
    if expected_size is not None and (info.width, info.height) != expected_size:
        raise ValueError(
            f"Expected frame size {expected_size}, decoded {(info.width, info.height)}"
        )
    return VideoInfo(
        path=info.path,
        width=info.width,
        height=info.height,
        fps=info.fps,
        frame_count=decoded_frames,
        codec=info.codec,
    )


def sample_rgb_frames(path: str | Path, count: int = 4) -> list[tuple[int, Image]]:
    """Return evenly spaced RGB frames for notebook-safe Matplotlib previews."""

    if count <= 0:
        raise ValueError("count must be positive")
    info = inspect_video(path)
    indices = np.linspace(0, info.frame_count - 1, min(count, info.frame_count), dtype=int)
    capture = cv2.VideoCapture(str(info.path))
    samples: list[tuple[int, Image]] = []
    try:
        for index in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, int(index))
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Could not decode frame {index} from {info.path}")
            samples.append((int(index), cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
    finally:
        capture.release()
    return samples


def plot_samples(path: str | Path, count: int = 4) -> None:
    """Display representative frames inline; this never opens GUI windows."""

    from matplotlib import pyplot as plt

    samples = sample_rgb_frames(path, count)
    figure, axes = plt.subplots(1, len(samples), figsize=(4 * len(samples), 3))
    axes_array = np.atleast_1d(axes)
    for axis, (index, frame) in zip(axes_array, samples):
        axis.imshow(frame)
        axis.set_title(f"frame {index}")
        axis.axis("off")
    figure.tight_layout()
