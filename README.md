# Runaway-New-Playground

A small playground for generating video clips with Seedance on BytePlus ModelArk, driven from one Python script.

![A frame from the first generated test clip: a glowing hexagonal wall lamp on a white wall with an orange dart in front of it](output/test_2_5_480p_4s_frame.jpg)

_A frame from `test_2_5_480p_4s`, the first clip made with the script (Seedance 2.5, 480p, 4 seconds). The clip itself is gitignored; the frame is kept._

**Problem.** A Seedance video run on BytePlus ModelArk is an asynchronous task that has to be created, polled and downloaded, and each run's settings and token cost need recording.

**Idea.** One Python script runs the whole task and appends the model, the full request parameters, the task ID and the tokens charged to a JSONL log.

**Built.** `scripts/seedance.py`, standard library only, covering Seedance 2.5, 2.0 and 2.0-fast with duration, resolution, ratio, audio, seed and image or video references. One test clip so far (2.5, 480p, 4 seconds, 38,830 tokens charged). 5 commits on 2 days, Oct 23 to Oct 25, 2026.

## What it does

`scripts/seedance.py` creates a video generation task on the ModelArk API, polls it until it finishes, downloads the result and appends a record of the run to `output/runs.jsonl`. It uses only the Python standard library.

- Models: `2.5` (default), `2.0`, `2.0-fast`, or a full model ID.
- Options: `--duration`, `--resolution`, `--ratio`, `--audio`, `--seed`, repeatable `--image-url` and `--video-url` references, and `--out`.
- Each log line stores the model, the full request parameters, the task ID and the tokens charged.

## Run it

This calls a paid API. The key is read from the `ARK_API_KEY` environment variable (a local `.env` is gitignored).

```bash
export ARK_API_KEY=...
python3 scripts/seedance.py --prompt "your prompt" --duration 4 --resolution 480p --out output/clip.mp4
```

Reference images and videos must be public URLs (images can also be data URIs).

## Layout

- `scripts/seedance.py`: the runner.
- `input/nerf_10s_720p.mp4`: a 10 second, 1280x720 source clip.
- `output/runs.jsonl`: one line per run. The only entry so far is the 4 second 480p test with no audio, which was charged 38,830 tokens.
- `output/test_2_5_480p_4s_frame.jpg`: a frame from that test clip. Generated `.mp4` and `.mov` files in `output/` are gitignored.
