# Week 4 — Streaming video compositing

> **Keep this weekly folder intact.** Place it at
> `COMP3419-Python-Labs/COMP3419-W04-Lab-Files`, beside the earlier weeks. If
> the ZIP extractor creates a wrapper, move only this inner weekly folder into
> the course root. Run setup and tests from that root. See the
> [directory layout](../README.md#keep-the-weekly-package-structure).

This refresh keeps the original blue-screen task but removes the slow
frame-to-TIFF-to-video workflow. It uses one Python process and holds only the
current foreground/background frames in memory.

## Learning outcomes

- inspect frame count, resolution, frame rate and codec instead of assuming them;
- build a vectorised blue-screen mask in HSV colour space;
- clean a mask with morphological opening/closing and create a soft alpha edge;
- apply alpha compositing with NumPy broadcasting;
- synchronise videos with different frame rates and stream encoded output; and
- validate the decoded result quantitatively.

The supplied foreground is correctly located at `W4LabData/monkey.avi`. It is
720×576 at 25 FPS; the 320×240 replacement background is 10 FPS. The module
uses their source timelines, loops the shorter background, and resizes it with
an aspect-ratio-preserving centre crop. Output keeps the foreground's source
FPS; changing playback speed or performing temporal resampling is outside this
lab's compositing function.

## Run

From the repository root:

```bash
uv sync --locked
uv run --locked jupyter lab
```

Open `week04_video_compositing.ipynb`. The notebook defaults
to a 75-frame preview. Set `MAX_FRAMES = None` only after inspecting the key.
Outputs are written under `outputs/`, which can be deleted and regenerated.

Run the built-in tests from the repository root:

```bash
uv run --locked python -m unittest discover -s COMP3419-W04-Lab-Files/tests -v
```

The tests cover synthetic pixel correctness, flat notebook path discovery,
bounded handling of background decode failure, container/codec validation,
supplied-video metadata and a short real streaming encode/decode. Generated
output is reopened and decoded sequentially rather than trusted from container
frame-count metadata alone.

## Student self-check

Retain:

1. a representative original foreground, binary/soft mask, and composite;
2. the validated output video metadata;
3. a short justification of the HSV bounds and morphology/feather settings;
4. an explanation of why per-frame Python loops and intermediate TIFFs are
   unnecessary here; and
5. one observed failure case (for example spill, shadow or foreground blue)
   plus a proposed improvement.

Do not use `cv2.imshow` in the notebook. The supplied plotting helpers render
inline and also work on JupyterHub or other headless lab machines.
