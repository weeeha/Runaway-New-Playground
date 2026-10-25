#!/usr/bin/env python3
"""Create a Seedance task on BytePlus ModelArk, poll it, download the clip.

Key: ARK_API_KEY from the environment, else from ~/Documents/Claude/Projects/SeedDance/.env.
Reference: ~/Documents/Claude/Projects/SeedDance/seedance_api_reference.md

Usage:
  python3 scripts/seedance.py --prompt "..." [--model ID] [--duration 4]
      [--resolution 480p] [--ratio 16:9] [--audio] [--video-url URL]
      [--image-url URL] [--out output/clip.mp4]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODELS = {
    "2.5": "dreamina-seedance-2-5-260628",
    "2.0": "dreamina-seedance-2-0-260128",
    "2.0-fast": "dreamina-seedance-2-0-fast-260128",
}
ENV_FILE = Path.home() / "Documents/Claude/Projects/SeedDance/.env"


def load_key() -> str:
    k = os.environ.get("ARK_API_KEY")
    if k:
        return k
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("ARK_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ARK_API_KEY not found in env or " + str(ENV_FILE))


def call(method: str, path: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    req.add_header("Authorization", "Bearer " + load_key())
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read().decode()[:600]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--model", default="2.5", help="2.5 | 2.0 | 2.0-fast | full model ID")
    ap.add_argument("--duration", type=int, default=4)
    ap.add_argument("--resolution", default="480p")
    ap.add_argument("--ratio", default="16:9")
    ap.add_argument("--audio", action="store_true", help="generate native audio (default off)")
    ap.add_argument("--video-url", action="append", default=[], help="public URL, role reference_video")
    ap.add_argument("--image-url", action="append", default=[], help="public URL or data URI, role reference_image")
    ap.add_argument("--seed", type=int, default=-1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--poll", type=int, default=10, help="seconds between status checks")
    a = ap.parse_args()

    model = MODELS.get(a.model, a.model)
    content = [{"type": "text", "text": a.prompt}]
    for u in a.image_url:
        content.append({"type": "image_url", "image_url": {"url": u}, "role": "reference_image"})
    for u in a.video_url:
        content.append({"type": "video_url", "video_url": {"url": u}, "role": "reference_video"})

    body = {
        "model": model,
        "content": content,
        "resolution": a.resolution,
        "ratio": a.ratio,
        "duration": a.duration,
        "generate_audio": a.audio,
        "seed": a.seed,
        "watermark": False,
    }
    created = call("POST", "/contents/generations/tasks", body)
    task_id = created["id"]
    print(f"task {task_id} created ({model}, {a.duration}s, {a.resolution}, audio={a.audio})", flush=True)

    t0 = time.time()
    while True:
        info = call("GET", f"/contents/generations/tasks/{task_id}")
        st = info.get("status")
        if st in ("succeeded", "failed", "expired"):
            break
        print(f"  {st} ... {int(time.time() - t0)}s", flush=True)
        time.sleep(a.poll)

    usage = info.get("usage", {})
    print(f"status: {st} after {int(time.time() - t0)}s")
    print(f"tokens charged: {usage.get('completion_tokens')}  (usage={json.dumps(usage)})")
    if st != "succeeded":
        print(json.dumps(info.get("error"), indent=2))
        sys.exit(1)

    url = info["content"]["video_url"]
    out = Path(a.out or f"output/{task_id}.mp4")
    out.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, out)
    print(f"saved {out} ({out.stat().st_size // 1024} KB); URL valid 24h")
    log = out.parent / "runs.jsonl"
    with log.open("a") as f:
        f.write(json.dumps({"task": task_id, "model": model, "params": body | {"content": content},
                            "tokens": usage.get("completion_tokens"), "file": str(out),
                            "created": created, "finished": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")


if __name__ == "__main__":
    main()
