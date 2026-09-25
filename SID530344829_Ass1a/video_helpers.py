from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt

ASS_DIR = Path(__file__).resolve().parent
DATA_DIR = ASS_DIR / "data"
ORIGINAL_VIDEO = DATA_DIR / "monkey.avi"

# macroblock matcher, filtering, visualisation
# drawing and video-I/o utils: cv2.arrowedLine and cv2.VideoWriter

Image = NDArray[np.uint8]

@dataclass(frozen=True)
class VideoInfo:
    """video metadata"""
    path: Path
    width: int
    height: int
    channels: int
    fps: float
    frame_count: int
    codec: str

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / self.fps

    def inspect_representative_frames():
        """inspect representative frames from beginning, middle, end"""
        pass

@dataclass(frozen=True)
class Macroblock:
    sample: Image
    frame_i: int
    x: float # x-coord of source centre
    y: float
    search_radius: float

@dataclass(frozen=True) 
class MacroblockMatcher:
    """params for macroblock matcher"""
    # common checkpoint baseline
    n_pairs: int
    block_width: int
    grid_stride: int
    search_radius: float # non-negative
    first_last_valid_centres: tuple[tuple[int, int], tuple[int, int]]

@dataclass(frozen=True)
class ParameterEvidenceReport:
    baseline: list[tuple[int, int]] # in numpy pixel indexing
    runtime: float
    grid_coverage: float
    vector_counts: int

@dataclass(frozen=True)
class RetainedVectors:
    """vector data"""
    filtering_rule: str
    source_block: tuple[int, int]
    deltas: tuple[int, int]
    confidence_measure: float

@dataclass(frozen=True)
class MotionField:
    initial_frame: int
    block_size: tuple[int, int]
    search_radius: float
    retained_count: int
    rejected_count: int
    sample_count: int
    motion_vectors: list[RetainedVectors]

def _decode_fourcc(value: int) -> str:
    """convert 4 byte seq to 4 ascii chars to get codec identifier"""
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
        channels = capture.read()[1].shape[2] if len(capture.read()[1].shape) == 3 else 1
    finally:
        capture.release()

    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid frame size reported for {video_path}")
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError(f"Invalid frame rate reported for {video_path}: {fps}")
    if frame_count <= 0:
        raise ValueError(f"No frames reported for {video_path}")
    return VideoInfo(video_path, width, height, channels, fps, frame_count, codec)

def sample_ith_frame(path: str | Path, i: int = 0) -> Image:
    if i < 0:
        raise ValueError("frame index must be positive")
    info = inspect_video(path)
    if i >= info.frame_count:
        raise IndexError("frame index out of bounds")
    sample = None
    capture = cv2.VideoCapture(str(info.path))
    try:
        capture.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not decode frame {index} from {info.path}")
        sample = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    finally:
        capture.release()
    return sample

def sample_rgb_frames(path: str | Path, count: int = 4) -> list[tuple[int, Image]]:
    """return evenly spaced rgb frames for notebook-safe matplotlib previews. taken from w4 video_compositing.py file
    does not use sample_ith_frame to avoid repeated calls to inspect)"""
    if count <= 0:
        raise ValueError("count must be positive")
    info = inspect_video(path)
    indices = np.linspace(0, info.frame_count - 1, min(count, info.frame_count), dtype=int)
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
    """inline display of frames"""
    samples = sample_rgb_frames(path, count)
    figure, axes = plt.subplots(1, len(samples), figsize=(4 * len(samples), 3))
    axes_array = np.atleast_1d(axes)
    for axis, (index, frame) in zip(axes_array, samples):
        axis.imshow(frame)
        axis.set_title(f"frame {index}")
        axis.axis("off")
    figure.tight_layout()

def validate_video(path: str | Path, *, expected_frames: int | None = None, expected_fps: float | None, expected_size: tuple[int, int] | None = None, ) -> VideoInfo:
    """Decode encoded video by stream and return validated metadata"""

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
        channels=info.channels,
    )

def get_macroblocks(path: str | Path, frame_i: int, n_rows: int = 10, n_cols: int = 12) -> dict[tuple[float, float], Macroblock]:
    vid_info = inspect_video(path)
    frame = sample_ith_frame(path, frame_i)
    temp_x = n_rows * 2 + 1
    temp_y = n_cols * 2 + 1
    gap_x = vid_info.width / ( temp_x )
    gap_y = vid_info.height / ( temp_y )
    candidate_centres = [(x*gap_x, y*gap_y) for x, y in zip(range(1, temp_x, 2), range(1, temp_y, 2))]

    macroblocks = {}
    for x_accent, y_accent in candidate_centres:
        macroblocks[x_accent, y_accent] = Macroblock(sample=frame, frame_i=frame_i, x=x_accent, y=y_accent)

    return macroblocks

def macroblock_stream_to_pairs(dict[tuple[int, int], Macroblock]) -> dict[int, tuple[Macroblock, Macroblock]]:
    """group macroblock streams to pairs"""
    pass

def calculate_ssd(width: int, height: int, search_radius: float, x: np.uint8, y: np.uint8):
    """direct arithmetic in uint8 not valid for SSD → convert to float32 or float64, subtract, then accumulate in float64.
    iterate per-pixel
    SSD(x', y')=(over v,k,c)[F_i - F_{i+1}]^2
    """
    pass
    
def get_winning_candidate():
    """run calculate ssd and update when find smaller"""
    pass

def get_minimum_ssd():
    pass

def show_search_window():
    pass

def translate_crop(x: float, y: float):
    pass
    
def inspect_candidate_centres():
    pass

def select_candidate_minimum_ssd():
    pass

def draw_retained_vectors():
    pass

def match_macroblock_video(video_path: str | Path, output_path: str | Path, codec: str | None = None):
    pass