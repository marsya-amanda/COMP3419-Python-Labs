from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt
import math

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
    fps: int
    frame_count: int
    codec: str

    @property
    def duration_seconds(self) -> float:
        return self.frame_count / self.fps

    def inspect_representative_frames():
        """inspect representative frames from beginning, middle, end"""
        pass

@dataclass(frozen=False)
class Macroblock:
    image: Image
    frame_i: int
    x: int # x-coord of source centre
    y: int
    search_radius: int
    block_width: int
    motion_displacement: tuple[float, float] | None

    def update_centre(self, new_centre: tuple[int, int]):
        """if want to do iterative"""
        self.x = new_centre[0]
        self.y = new_centre[1]

    def set_displacement(self, d: tuple[float, float]):
        self.motion_displacement = d

@dataclass(frozen=True)
class ParameterEvidenceReport:
    baseline: list[tuple[int, int]] # in numpy pixel indexing
    runtime: float
    grid_coverage: float
    vector_counts: int

@dataclass(frozen=True)
class MotionVector:
    """vector data"""
    filtering_rule: str
    source_centre: tuple[int, int]
    displacement: tuple[int, int]
    #confidence_measure: float

@dataclass(frozen=True) 
class MotionEstimationReport:
    video_info: VideoInfo
    frame_i: int
    block_width: int
    grid_stride: int
    search_radius: int # non-negative
    first_last_valid_centres: tuple[tuple[int, int], tuple[int, int]]
    n_rows: int
    n_cols: int
    blocks: list[Macroblock]
    retained_vectors: list[MotionVector]

@dataclass(frozen=True)
class MotionField:
    initial_frame: int
    block_size: tuple[int, int]
    search_radius: float
    retained_count: int
    rejected_count: int
    sample_count: int
    motion_vectors: list[MotionVector]

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
    capture = cv2.VideoCapture(str(info.path))
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

def plot_samples(path: str | Path, count: int = 1) -> None:
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

"""def get_macroblocks(path: str | Path, frame_i: int = 0, block_width: int, n_rows: int = 10, n_cols: int = 12, search_radius: int = 6) -> list[Macroblock]:
    #returns a stream of macroblock objects
    #by number of columns and rows (wrong)
    
    vid_info = inspect_video(path)
    frame = sample_ith_frame(path, frame_i)
    temp_x = n_rows * 2 + 1
    temp_y = n_cols * 2 + 1
    gap_x = vid_info.width / ( temp_x - 1)
    gap_y = vid_info.height / ( temp_y - 1)
    candidate_centres = []

    for y_index in range(1, temp_y, 2):
        for x_index in range(1, temp_x, 2):
            candidate_centres.append((x_index, y_index))
            
    macroblocks = []
    for x_index, y_index in candidate_centres:
        y_start = int((y_index - 1) * gap_y)
        y_end = int((y_index+1) * gap_y)
        x_start = int((x_index-1)*gap_x)
        x_end = int((x_index+1) *gap_x)
        cropped_img = frame[y_start:y_end, x_start:x_end]
        macroblocks.append(Macroblock(image=cropped_img, frame_i=frame_i, x=x_index * gap_x, y=y_index*gap_y, search_radius=search_radius))

    return macroblocks """

def get_macroblocks(path: str | Path, frame_i: int = 0, block_width: int = 15, grid_stride: int = 48, search_radius: int = 6) -> tuple[tuple[int, int], tuple[int, int], list[Macroblock]]:
    """returns first and last candidate centres, number of candidate rows, number of candidate columns, and list of macroblock objects"""
    if block_width <= 0:
        raise ValueError("block width must be odd positive integer")

    vid_info = inspect_video(path)
    frame = sample_ith_frame(path, frame_i)

    #get n_blocks and n_cols
    n_blocks_per_row = int((vid_info.width - block_width / 2) // grid_stride)
    n_blocks_per_row += 1 if (vid_info.width - block_width / 2) % grid_stride >= (block_width+1) // 2 else 0

    n_blocks_per_column = int((vid_info.height - block_width / 2) // grid_stride)
    n_blocks_per_column += 1 if (vid_info.height - block_width / 2) % grid_stride >= (block_width+1) // 2 else 0

    # get candidate centres
    pad_col = max(0, (vid_info.width - grid_stride * (n_blocks_per_row - 1) - block_width) // 2)
    pad_row = max(0, (vid_info.height - grid_stride * (n_blocks_per_column - 1) - block_width) // 2)
    #print((vid_info.width - grid_stride * n_blocks_per_row - block_width) // 2, pad_row)
    
    candidate_centres = []
    for x_index in range(n_blocks_per_column):
        for y_index in range(n_blocks_per_row):
            candidate_centres.append((int(x_index * grid_stride + block_width // 2 + pad_row), int(y_index * grid_stride + block_width // 2 + pad_col)))

    # partition original frame to macroblocks
    macroblocks = []
    for x_centre, y_centre in candidate_centres:
        y_start = int(y_centre - block_width // 2)
        y_end = int(y_start + block_width)
        x_start = int(x_centre - block_width // 2)
        x_end = int(x_start + block_width)
        cropped_img = frame[x_start:x_end, y_start:y_end]
        if cropped_img.size != 0:
            macroblocks.append(Macroblock(image=cropped_img, frame_i=frame_i, x=x_centre, y=y_centre, block_width=block_width, search_radius=search_radius, motion_displacement=None))
        if cropped_img.size == 0:
            print(f"{(x_start, y_start)}, {(x_end, y_end)} has no cropped image")

    return candidate_centres[0], candidate_centres[-1], n_blocks_per_row, n_blocks_per_column, macroblocks

def get_macroblocks_consecutive_frames(path: str | Path, frame_start: int = 0, count: int = 50, block_width: int = 15, grid_stride: int = 48, search_radius: int = 6) -> list[tuple[int, int], tuple[int, int], int, int, list[Macroblock]]:
    """output frames as a stream"""
    consecutive_frames = []
    for i in range(frame_start, frame_start + count):
        macroblocks_i = get_macroblocks(path=path, frame_i=i, block_width=block_width, grid_stride=grid_stride, search_radius=search_radius)
        consecutive_frames.append(macroblocks_i)
    return consecutive_frames

def plot_macroblocks(macroblocks: list[Macroblock], n_rows: int = 10, n_cols: int = 12):
    """plot macroblocks"""
    fig, axes = plt.subplots(nrows=n_cols, ncols=n_rows) 
    axes=axes.ravel()

    for ax, block in zip(axes, macroblocks):
        ax.imshow(block.image)
        ax.axis('off')
    plt.tight_layout()
    plt.show()

def calculate_ssd(
    frame_1: Image, 
    frame_2: Image, 
    source_x: int, source_y: int, candidate_x: int, candidate_y: int, k: int, n_channels: int) -> np.float64:
    """direct arithmetic in uint8 not valid for SSD → convert to float32 or float64, subtract, then accumulate in float64.
    iterate per-pixel
    SSD(x', y')=(over row_v,col_k,channel_c)[F_i - F_{i+1}]^2
    calculation in float64, returns ssd in float64
    """
    frame_1 = frame_1.astype(np.float64)
    frame_2 = frame_2.astype(np.float64)
    ssd: np.float64 = 0

    # need to optimise this - create into dict w frame value as key? avoid double-counting?
    candidate = {}
    for v in range(-k, k+1):
        for u in range(-k, k+1):
            for c in range(0, n_channels):
                ssd += np.square(frame_1[source_y+v, source_x+u, c] - frame_2[candidate_y+v, candidate_x+u, c]) # swap y and x around if wrong

    return ssd

def filter_vectors(mode: str | None):
    pass # use neighbour-filtering

def get_valid_candidate_centres(width: int, height: int, source_x: int, source_y: int, k: int, search_radius: int) -> list[tuple[int, int]]:
    """find candidate centres within [x-R,x+R]x[y-R,y+R] (inclusive!), 
    whose complete blocks lie in F_{i+1}"""
    
    candidates = []
    for v in range(-search_radius, search_radius+1):
        for u in range(-search_radius, search_radius+1):
            x = source_x + u
            y = source_y + v
            if (x < k or x >= width - k - 2 or y < k or y >= height - k - 2) is not True:
                candidates.append((x,y)) # update col (x) first, so winning candidate is row-major
    return candidates
    
def get_winning_candidate_of_block(
    width: int, 
    height: int, 
    frame_1: Image, 
    frame_2: Image, 
    search_radius: int, 
    block_width: int, 
    block: Macroblock, 
    n_channels: int) -> tuple[tuple[int, int], MotionVector]:
    """run calculate_ssd and update when find smaller. if tie, apply first min in row-major order
    check if x' and y' in frame here, not in calc ssd"""
    k = int(block_width // 2)
    source_x = block.x
    source_y = block.y
    
    # generate valid candidate centres
    candidate_centres = get_valid_candidate_centres(width=width, height=height, source_x=source_x, source_y=source_y, k=k, search_radius=search_radius)
    if candidate_centres is None:
        raise ValueError("no valid candidate centres found")

    # get min ssd
    min_ssd = math.inf #previously -inf
    winning_candidate = None # tuple

    for candidate_y, candidate_x in candidate_centres:
        prev_min = min_ssd
        min_ssd = min(min_ssd, calculate_ssd(frame_1=frame_1, frame_2=frame_2, source_x=source_x, source_y=source_y, candidate_x=candidate_x, candidate_y=candidate_y, k=k, n_channels=n_channels))
        winning_candidate = (candidate_x, candidate_y) if min_ssd == prev_min else winning_candidate # update winning candidate if min_ssd updates
    # print(winning_candidate)
    displacement = (winning_candidate[0] - source_x, winning_candidate[1] - source_y) if winning_candidate is not None else (0, 0) # no candidate_centres
    
    motion_vector_obj = MotionVector(filtering_rule="ssd", source_centre=(source_x, source_y), displacement=displacement)
    return displacement, motion_vector_obj

def estimate_motion_one_pair(path: str | Path, frame_i: int = 0, block_width: int = 15, grid_stride: int = 48, search_radius: int = 6) -> MotionEstimationReport:
    print(f"Starting motion estimation between frame {frame_i} and {frame_i+1}.")
    vid_info = inspect_video(path)

    print(f"Getting macroblocks...")
    first_centre, last_centre, n_candidate_rows, n_candidate_cols, blocks = get_macroblocks(path, frame_i, block_width, grid_stride, search_radius) #macroblock centres are fixed

    print(f"First valid centre: {first_centre}\nLast valid centre: {last_centre}\nNumber of macroblocks: {len(blocks)}")
    
    retained_vectors = []
    frame_1: Image = sample_ith_frame(path, frame_i)
    frame_2: Image = sample_ith_frame(path, frame_i + 1) # next frame

    print("Getting motion displacements for each block...")
    for block in blocks:
        print(f"Getting best motion vector for block ({block.x}, {block.y})")
        curr_d, curr_mv = get_winning_candidate_of_block(vid_info.width, vid_info.height, frame_1, frame_2, search_radius, block_width, block, vid_info.channels)
        block.set_displacement(curr_d)
        retained_vectors.append(curr_mv)

    return MotionEstimationReport(vid_info, 
                                  frame_i, 
                                  block_width, 
                                  grid_stride, 
                                  search_radius, 
                                  (first_centre, last_centre), 
                                  n_candidate_rows, 
                                  n_candidate_cols, 
                                  blocks, 
                                  retained_vectors)

def estimate_motion_consecutive_pairs(path: str | Path, frame_start: int = 0, count: int = 50, block_width: int = 15, grid_stride: int = 48, search_radius: int = 6) -> list[MotionEstimationReport]:
    """expect n-1 motion vector lists, from n-1 pairs"""
    all_reports = []
    frame_end = frame_start + count

    for i in range(frame_start, frame_end):
        all_reports.append(estimate_motion_one_pair(path, i, block_width, grid_stride, search_radius))

    return all_reports

def draw_macroblock(img: Image, out_path: str | Path | None, block: Macroblock) -> Image:
    # draw macroblock w centre
    x1 = int(block.x - block.block_width // 2)
    x2 = int(block.x + (block.block_width + 1) // 2)
    y1 = int(block.y - block.block_width // 2)
    y2 = int(block.y + (block.block_width + 1) // 2)

    cv2.rectangle(img, (y1, x1), (y2, x2), (255, 255, 255), 2) # draw macroblock rectangle on image in white with thickness 3
    cv2.circle(img, (block.y, block.x), 5, (255, 255, 255), -1)
    if out_path is not None:
        cv2.imwrite(out_path, img) # save
    return img

def draw_macroblocks(img: Image, out_path: str | Path | None, blocks: list[Macroblock]) -> Image:
    for block in blocks:
        draw_macroblock(img, out_path, block)
    return img

def draw_search_window(img: Image, out_path: str | Path | None, block: Macroblock) -> Image:
    cv2.circle(img, (block.x, block.y), block.search_radius, (255, 255, 255), 3) # search window on image in white w thickness 3
    if out_path is not None:
        cv2.imwrite(out_path, img)
    return img

def draw_search_windows(img, out_path: str | Path | None, blocks: list[Macroblock]) -> Image:
    for block in blocks:
        draw_search_window(img, out_path, block)
    return img

def draw_one_motion_vector(img: Image, out_path: str | Path | None, vector: MotionVector) -> Image:
    start = vector.source_center
    end = vector.source_center + displacement
    cv2.arrowedLine(img, start, end, (0, 0, 255), 3) # draw motion vector in red w thickess 3
    if out_path is not None:
        cv2.imwrite(out_path, img)
    return img

def draw_motion_vectors(img: Image, out_path: str | Path | None, vector_arr: list[MotionVector]) -> Image:   
    for vector in vector_arr:
        draw_one_motion_vector(img, out_path, vector)
    return img

def draw_block_search_motion_overlay(out_path: str | Path | None, report: MotionEstimationReport) -> tuple[Image, Image, Image]:
    og_img = sample_ith_frame(report.path, report.path_i)
    target_img = sample_ith_frame(report.path, report.path_i + 1)
    annotated_img = None

    # draw macroblock
    annotated_img = draw_macroblocks(og_img, out_path, report.blocks)

    # draw search radius
    annotated_img = draw_search_windows(og_img, out_path, report.blocks)

    # draw motion vectors
    annotated_img = draw_motion_vectors(og_img, out_path, report.retained_vectors)

    return og_img, target_img, annotated_img

def calculate_and_draw_search_motion_one_pair(path: str | Path, out_path: str | Path | None, frame_i: int = 0, block_width: int = 15, grid_stride: int = 48, search_radius: int = 6) -> tuple[MotionEstimationReport, Image, Image, Image]:
    report = estimate_motion_one_pair(path, frame_i, block_width, grid_stride, search_radius)
    og, target, annotated = draw_block_search_motion_overlay(out_path, report)

    return report, og, target, annotated

def calculate_and_show_search_motion_pairs_as_video(path: str | Path, vid_out_path: str | Path = "SID430344829_Ass1a_output.mp4", frame_start: int = 0, count: int = 50, block_width: int = 15, grid_stride: int = 48, search_radius: int = 6) -> str | Path:
    """returns report of size pair_count-1, og video and annotated video. no directory for each frame, write to videowriter"""
    vid_info = inspect_video(path)
    frame_end = frame_start + count
    vid_dims = (vid_info.height, vid_info.width)

    video_writer = cv2.VideoWriter(out_path, vid_info.codec, vid_info.fps, vid_dims)
    for i in range(frame_start, frame_end):
        report_i, og_i, target_i, annotated_i = calculate_and_draw_search_motion_one_pair(path, None, i, block_width_grid_stride, search_radius) # out_path is None to prevent writing on directory
        annotated_i = cv2.resize(annotated_i, vid_dims)
        video_writer.write(annotated_i)

    video_writer.release()
    return vid_out_path


def plot_frame_arr(frames: list[tuple[str, Image]], count: int = 1) -> None:
    figure, axes = plt.subplots(1, len(samples), figsize=(4 * len(samples), 3))
    axes_array = np.atleast_1d(axes)
    for axis, (title, frame) in zip(axes_array,frames):
        axis.imshow(frame)
        axis.set_title(f"{title}")
        axis.axis("off")
    figure.tight_layout()