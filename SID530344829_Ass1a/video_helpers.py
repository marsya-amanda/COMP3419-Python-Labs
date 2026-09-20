from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt

LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "SID530344829_Ass1a"

# macroblock matcher, filtering, visualisation
# drawing and video-I/o utils: cv2.arrowedLine and cv2.VideoWriter

ORIGINAL_VIDEO = DATA_DIR

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

@dataclass(frozen=True) // frozen?
class MacroblockMatcher:
    """params for macroblock matcher"""
    # common checkpoint baseline
    n_pairs: int
    block_width: int
    grid_stride: int
    search_radius: int
    first_last_valid_centres: tuple[tuple[int, int], tuple[int, int]]

@dataclass(frozen=True)
class EncodingReport:
    width: int
    height: int
    fps: float
    frame_count: int

    def inspect_representative_frames():
        pass

@dataclass(frozen=True)
class ParameterEvidenceReport:
    baseline: list[tuple[int, int]] # in numpy pixel indexing
    runtime: float
    grid_coverage: float
    vector_counts: int

def inspect_video(path: str | Path) -> VideoIndo:
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
        channels = len(capture.read()[1].shape) == 3 ? capture.read()[1].shape[2]
    finally:
        capture.release()

    if width <= 0 or height <= 0:
        raise ValueError(f"Invalid frame size reported for {video_path}")
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError(f"Invalid frame rate reported for {video_path}: {fps}")
    if frame_count <= 0:
        raise ValueError(f"No frames reported for {video_path}")
    return VideoInfo(video_path, width, height, channels, fps, frame_count, codec)
    