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

    def inspect_representative_frames():
        """inspect representative frames from beginning, middle, end"""
        pass

@dataclass(frozen=True) // frozen?
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
    initial_frame: int
    block_size: tuple[int, int]
    search_radius: float
    retained_count: int
    rejected_count: int
    sample_count: int

def _decode_fourcc(value: int) -> str:
    """convert 4 byte seq to 4 ascii chars to get codec identifier"""
    return "".join(chr((value >> (8 * index)) & 0xFF) for index in range(4)).strip()

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

def validate_video(path: str | Path, *, expected_frames: int | None = None, expected_fps: float | None, expected_size: tuple[int, int] | None = None, ) -> VideoInfo:
    """Decode encoded video by stream and return validated metadata"""
    pass

def calculate_ssd():
    pass
    
def show_search_window():
    pass

def translate_crop(float x, float y):
    pass

def get_winning_candidate():
    pass

def get_minimum_ssd():
    pass

def inspect_candidate_centres():
    pass

def select_candidate_minimum_ssd():
    pass

def draw_retained_vectors():
    pass

def match_macroblock_video(video_path: str | Path, output_path: str | Path, codec: str | None = None):
    pass