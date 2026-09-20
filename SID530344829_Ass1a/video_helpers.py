from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
from numpy.typing import NDArray
import matplotlib.pyplot as plt

LAB_DIR = Path(__file__).resolve().parent
DATA_DIR = LAB_DIR / "SID530344829_Ass1a"

// macroblock matcher, filtering, visualisation
// drawing and video-I/o utils: cv2.arrowedLine and cv2.VideoWriter

ORIGINAL_