from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np


WEEK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEEK_DIR))

from video_compositing import (  # noqa: E402
    BACKGROUND_VIDEO,
    FOREGROUND_VIDEO,
    BlueScreenKeyer,
    VideoInfo,
    _LoopingBackground,
    alpha_composite,
    blue_screen_mask,
    composite_videos,
    foreground_alpha,
    inspect_video,
    open_video_writer,
    validate_video,
)


class KeyingTests(unittest.TestCase):
    def test_vectorised_key_and_alpha_composite(self) -> None:
        foreground = np.full((40, 60, 3), (255, 0, 0), dtype=np.uint8)
        foreground[10:30, 20:40] = (0, 0, 255)
        background = np.full_like(foreground, (0, 255, 0))
        keyer = BlueScreenKeyer(morphology_radius=0, feather_radius=0)

        screen = blue_screen_mask(foreground, keyer)
        alpha = foreground_alpha(screen, keyer.feather_radius)
        result = alpha_composite(foreground, background, alpha)

        np.testing.assert_array_equal(result[0, 0], background[0, 0])
        np.testing.assert_array_equal(result[20, 30], foreground[20, 30])
        self.assertEqual(screen.dtype, np.uint8)
        self.assertEqual(alpha.dtype, np.float32)

    def test_keyer_rejects_invalid_bounds(self) -> None:
        with self.assertRaises(ValueError):
            BlueScreenKeyer(lower_hsv=(100, 0, 0), upper_hsv=(90, 255, 255))


class VideoContractTests(unittest.TestCase):
    def test_flat_notebook_path_supports_repository_root(self) -> None:
        notebook_path = WEEK_DIR / "week04_video_compositing.ipynb"
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        source = "".join(
            "".join(cell.get("source", [])) for cell in notebook["cells"]
        )
        self.assertIn('Path.cwd() / "COMP3419-W04-Lab-Files"', source)
        self.assertNotIn(
            'Path.cwd() / "COMP3419-W04-Lab-Files" / "COMP3419-W04-Lab-Files"',
            source,
        )

    def test_explicit_codec_does_not_bypass_container_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "preview.unsupported"
            with self.assertRaisesRegex(ValueError, "output filename"):
                open_video_writer(output, 25.0, (32, 24), codec="MJPG")

    def test_background_decode_restart_is_bounded(self) -> None:
        class FailedCapture:
            def __init__(self) -> None:
                self.read_count = 0

            def isOpened(self) -> bool:
                return True

            def read(self) -> tuple[bool, None]:
                self.read_count += 1
                return False, None

            def set(self, _property: int, _value: int) -> bool:
                return True

            def release(self) -> None:
                pass

        failed_capture = FailedCapture()
        info = VideoInfo(Path("truncated.avi"), 32, 24, 10.0, 5, "MJPG")
        with patch("video_compositing.cv2.VideoCapture", return_value=failed_capture):
            background = _LoopingBackground(info)
            with self.assertRaisesRegex(RuntimeError, "background frame"):
                background.frame_at(0.0)
            background.close()
        self.assertEqual(failed_capture.read_count, 2)


class SuppliedVideoTests(unittest.TestCase):
    def test_supplied_video_metadata(self) -> None:
        foreground = inspect_video(FOREGROUND_VIDEO)
        background = inspect_video(BACKGROUND_VIDEO)
        self.assertEqual((foreground.width, foreground.height), (720, 576))
        self.assertAlmostEqual(foreground.fps, 25.0, places=1)
        self.assertEqual((background.width, background.height), (320, 240))
        self.assertAlmostEqual(background.fps, 10.0, places=1)

    def test_short_streaming_composite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "preview.avi"
            report = composite_videos(
                FOREGROUND_VIDEO,
                BACKGROUND_VIDEO,
                output,
                max_frames=6,
                codec="MJPG",
            )
            self.assertEqual(report.frames_written, 6)
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1_000)
            self.assertGreater(report.mean_screen_fraction, 0.25)
            self.assertLess(report.mean_screen_fraction, 1.0)
            validated = validate_video(
                output,
                expected_frames=6,
                expected_fps=report.fps,
                expected_size=(report.width, report.height),
            )
            self.assertEqual(validated.frame_count, 6)


if __name__ == "__main__":
    unittest.main()
