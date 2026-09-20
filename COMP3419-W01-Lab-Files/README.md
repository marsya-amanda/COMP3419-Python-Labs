# Week 1 — Python and image-array foundations

<!-- ai-disclosure-2026 -->
## Use of generative AI

Generative AI was used to assist the preparation of these teaching materials. The teaching team is responsible for their content.
<!-- /ai-disclosure-2026 -->

> **Keep the course root and this weekly folder intact.** The Week 1 package
> creates `COMP3419-Python-Labs`; keep the Week 1 folder at
> `COMP3419-Python-Labs/COMP3419-W01-Lab-Files`. Retain every notebook, Python
> file, and media file in its original location. See the
> [directory layout](../README.md#keep-the-weekly-package-structure).

Week 1 is a formative orientation using the same locked Python environment as
the later labs. It assumes prior introductory programming experience and
concentrates on the array conventions that cause the most errors later in
COMP3419.

## Keep this course root

Week 1 initialises the course folder and its single shared `.venv`. When the
Week 2 ZIP arrives, add its intact `COMP3419-W02-Lab-Files` directory beside
this Week 1 directory; follow the same pattern for later weeks. Keep earlier
work, never place one week inside another, and run all `uv` commands from the
course root containing `pyproject.toml` and `uv.lock`.

## Start

If `uv` is not installed yet, follow the cross-platform installation and usage
quickstart in the root [`README.md`](../README.md#install-uv). The complete
Week 1 orientation sheet is published in the separate LaTeX lab book.

From the course root:

```bash
uv sync --locked
uv run --locked jupyter lab
```

Open
`COMP3419-W01-Lab-Files/week01_python_image_foundations.ipynb` and run it from
top to bottom. The supplied `sample_image.jpg` is used for the exercises.

## Learning outcomes

After the orientation, you should be able to:

1. identify an image's shape, dtype, value range, and channel order;
2. distinguish `(row, column)` array coordinates from `(x, y)` display
   coordinates;
3. use slicing and Boolean masks without pixel-by-pixel loops;
4. explain and prevent unsigned-integer overflow;
5. recognise the RGB/BGR difference between ImageIO and OpenCV; and
6. validate image operations with shapes, assertions, and simple timings.

## Optional orientation self-check

Complete the final notebook exercise if you would like to confirm that the
setup and array conventions are clear. Check:

- the central crop as an independent copy;
- an overflow-safe brightness operation;
- a vectorised mask;
- the assertions passing; and
- a short explanation of one coordinate or dtype bug you prevented.

No formal review or Week 1 notebook submission is required.

The older Anaconda installation and elementary Python-syntax material is no
longer part of the orientation.

### Updating an earlier course package

If your course root was created from an earlier Week 1 ZIP, check for
`scripts/notebook_support.py` before running the revised labs. If it is missing,
extract the updated Week 1 ZIP into a temporary directory and copy only that
file into your existing course root’s `scripts` directory. Keep your existing
weekly folders and completed work. New installations already include it.
