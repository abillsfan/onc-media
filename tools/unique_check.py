"""Refuse a Facebook reel post that repeats anything already posted (Carl: every reel post must be unique).

Usage:
    python3 -I tools/unique_check.py REEL.mp4 CAPTION.txt [SPEC.json]

Fails (exit 1) if:
  - the mp4 is byte-identical to any reel already in reels/log.json or posted from reels/hit_queue.json
  - the caption matches a caption already posted (log captions, posted hit-queue captions, and the stock
    caption of every retro theme that has already been used)
  - the spec (retro reels) matches a spec already logged, or is a used theme's stock spec unchanged
Prints OK and exits 0 otherwise.
"""
import hashlib, json, os, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def norm(s): return " ".join((s or "").split()).lower()

def canon(spec): return json.dumps(spec, sort_keys=True)

def main(reel, cap_path, spec_path=None):
    log = json.load(open(os.path.join(ROOT, "reels/log.json")))
    queue = json.load(open(os.path.join(ROOT, "reels/hit_queue.json")))["items"]
    themes = json.load(open(os.path.join(ROOT, "brand/retro_themes.json")))
    used_ids = {e["theme_or_show"].split("|")[0].strip()[len("retro:"):].split("#")[0] for e in log
                if e.get("theme_or_show", "").startswith("retro:")}
    files = [e["file"] for e in log] + [i["file"] for i in queue if i.get("posted_at")]
    caps = [e.get("caption") for e in log] + [i.get("caption") for i in queue if i.get("posted_at")]
    specs = [canon(e["spec"]) for e in log if e.get("spec")]
    for t in themes:
        if t["id"] in used_ids:
            caps.append(t.get("caption")); specs.append(canon(t["spec"]))
    problems = []
    me = os.path.abspath(reel); h = sha(reel)
    for f in files:
        p = os.path.join(ROOT, f)
        if os.path.exists(p) and os.path.abspath(p) != me and sha(p) == h:
            problems.append(f"video is identical to already-posted {f}")
    cap = open(cap_path).read()
    if norm(cap) in {norm(c) for c in caps if c}:
        problems.append("caption was already used on an earlier post - write a new one")
    if spec_path:
        if canon(json.load(open(spec_path))) in specs:
            problems.append("spec repeats an earlier reel - change hook, color, variant, names or pack label, and the seed")
    if problems:
        print("NOT UNIQUE:\n- " + "\n- ".join(problems)); sys.exit(1)
    print("OK: unique")

if __name__ == "__main__":
    main(*sys.argv[1:4])
