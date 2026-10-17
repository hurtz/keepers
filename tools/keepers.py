#!/usr/bin/env python3
"""Keepers round tool. Turns one photo of stuff laid out on the floor into swipe cards.

Commands
  grid   PHOTO                     Draw a labeled percent grid on the photo, so item boxes are easy to read off.
  detect PHOTO                     Guess the item boxes automatically (works best on a plain, even floor).
  crop   PHOTO BOXES --round ID    Cut every box into its own card image and add the items to that round.
  build                            Bake the rounds data into one page (dist/index.html) for single file hosting.
  files                            Print the image map to publish next to a built page.

Boxes are a JSON list in percent of the photo:  [{"x": 4, "y": 6, "w": 21, "h": 30, "rot": 0, "name": ""}]
"rot" (optional) turns the crop clockwise by 90, 180 or 270. "name" (optional) prefills the item name.
"""
import argparse
import datetime
import json
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


def load_photo(path):
    if path.lower().endswith((".heic", ".heif")):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            sys.exit("This is a HEIC photo. Run: pip install pillow-heif")
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB")


def font(size):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "C:/Windows/Fonts/arialbd.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    try:
        return ImageFont.load_default(size)
    except TypeError:
        return ImageFont.load_default()


def label(draw, xy, text, f, fg=(255, 255, 255), bg=(0, 0, 0, 170)):
    x, y = xy
    l, t, r, b = draw.textbbox((x, y), text, font=f)
    draw.rectangle((l - 3, t - 2, r + 3, b + 2), fill=bg)
    draw.text((x, y), text, font=f, fill=fg)


def load_data(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"config": {}, "rounds": []}


def save_data(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# ---------------------------------------------------------------- grid
def cmd_grid(a):
    im = load_photo(a.photo)
    im.thumbnail((1600, 1600))
    W, H = im.size
    d = ImageDraw.Draw(im, "RGBA")
    f = font(max(13, W // 75))
    for p in range(0, 101, a.step):
        major = p % (a.step * 2) == 0
        col = (255, 0, 170, 220 if major else 120)
        wid = 2 if major else 1
        x, y = round((W - 1) * p / 100), round((H - 1) * p / 100)
        d.line([(x, 0), (x, H)], fill=col, width=wid)
        d.line([(0, y), (W, y)], fill=col, width=wid)
        if 0 < p < 100:
            label(d, (x + 3, 3), str(p), f)
            label(d, (3, y + 3), str(p), f)
    im.save(a.out, quality=88)
    print(f"grid saved: {a.out}  ({W}x{H}, lines every {a.step}%)")


# ---------------------------------------------------------------- detect
def merge_boxes(boxes):
    changed = True
    while changed:
        changed = False
        out = []
        while boxes:
            x, y, w, h = boxes.pop()
            for i, (X, Y, Wd, Hd) in enumerate(out):
                ix = max(0, min(x + w, X + Wd) - max(x, X))
                iy = max(0, min(y + h, Y + Hd) - max(y, Y))
                if ix * iy > 0.3 * min(w * h, Wd * Hd):
                    nx, ny = min(x, X), min(y, Y)
                    out[i] = [nx, ny, max(x + w, X + Wd) - nx, max(y + h, Y + Hd) - ny]
                    changed = True
                    break
            else:
                out.append([x, y, w, h])
        boxes = out
    return boxes


def reading_order(boxes):
    if not boxes:
        return boxes
    hs = sorted(b[3] for b in boxes)
    tol = hs[len(hs) // 2] * 0.5
    boxes = sorted(boxes, key=lambda b: b[1] + b[3] / 2)
    rows, row = [], [boxes[0]]
    for b in boxes[1:]:
        if abs((b[1] + b[3] / 2) - (row[-1][1] + row[-1][3] / 2)) <= tol:
            row.append(b)
        else:
            rows.append(row)
            row = [b]
    rows.append(row)
    return [b for r in rows for b in sorted(r, key=lambda b: b[0])]


def cmd_detect(a):
    import cv2
    import numpy as np
    im = load_photo(a.photo)
    small = im.copy()
    small.thumbnail((1000, 1000))
    w, h = small.size
    lab = cv2.cvtColor(np.array(small), cv2.COLOR_RGB2LAB).astype(np.float32)
    lab = cv2.GaussianBlur(lab, (7, 7), 0)
    b = max(4, min(w, h) // 40)
    border = np.concatenate([lab[:b].reshape(-1, 3), lab[-b:].reshape(-1, 3),
                             lab[:, :b].reshape(-1, 3), lab[:, -b:].reshape(-1, 3)])
    floor = np.median(border, axis=0)
    dist = np.linalg.norm(lab - floor, axis=2)
    # anything that differs from the floor by more than the floor's own texture counts as an item
    bdist = np.linalg.norm(border - floor, axis=1)
    thr = max(10.0, float(np.percentile(bdist, 98)) * 1.6)
    mask = ((dist > thr) * 255).astype(np.uint8)
    k = max(3, min(w, h) // 120) | 1
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((k, k), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((k * 2, k * 2), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in cnts:
        x, y, bw, bh = cv2.boundingRect(c)
        frac = bw * bh / (w * h)
        if a.min / 100 <= frac <= 0.6:
            boxes.append([x, y, bw, bh])
    boxes = reading_order(merge_boxes(boxes))
    out = [{"x": round(100 * x / w, 1), "y": round(100 * y / h, 1),
            "w": round(100 * bw / w, 1), "h": round(100 * bh / h, 1)} for x, y, bw, bh in boxes]
    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    prev = small.copy()
    d = ImageDraw.Draw(prev, "RGBA")
    f = font(max(14, w // 40))
    for i, (x, y, bw, bh) in enumerate(boxes, 1):
        d.rectangle((x, y, x + bw, y + bh), outline=(255, 0, 170, 255), width=3)
        label(d, (x + 6, y + 6), str(i), f, bg=(255, 0, 170, 230))
    prev.save(a.preview, quality=85)
    print(f"found {len(out)} items -> {a.out}  (check {a.preview}, then fix boxes by hand if needed)")


# ---------------------------------------------------------------- crop
def cmd_crop(a):
    im = load_photo(a.photo)
    W, H = im.size
    with open(a.boxes) as fh:
        boxes = json.load(fh)
    root = os.path.dirname(os.path.abspath(a.data))
    data = load_data(a.data)
    data.setdefault("config", {})
    rounds = data.setdefault("rounds", [])
    rnd = next((r for r in rounds if r.get("id") == a.round), None)
    if rnd is None:
        rnd = {"id": a.round, "title": a.title or a.round.replace("-", " ").title(),
               "date": datetime.date.today().strftime("%b %-d"), "note": a.note or "", "items": []}
        rounds.append(rnd)
    elif a.title:
        rnd["title"] = a.title
    outdir = os.path.join(root, "rounds", a.round)
    os.makedirs(outdir, exist_ok=True)
    start = len(rnd["items"])
    pad = a.pad / 100
    tiles = []
    for n, b in enumerate(boxes, start + 1):
        x0 = max(0, (b["x"] / 100 - pad) * W)
        y0 = max(0, (b["y"] / 100 - pad) * H)
        x1 = min(W, (b["x"] + b["w"]) / 100 * W + pad * W)
        y1 = min(H, (b["y"] + b["h"]) / 100 * H + pad * H)
        crop = im.crop((round(x0), round(y0), round(x1), round(y1)))
        if b.get("rot"):
            crop = crop.rotate(-int(b["rot"]), expand=True)
        crop.thumbnail((a.size, a.size))
        name = f"{n:02d}.jpg"
        crop.save(os.path.join(outdir, name), quality=82, optimize=True, progressive=True)
        rnd["items"].append({"id": f"{a.round}-{n:02d}", "img": f"rounds/{a.round}/{name}",
                             "name": b.get("name", ""), "sub": "", "where": a.where or "",
                             "bio": "", "tags": []})
        tiles.append((n, crop))
    save_data(a.data, data)
    # contact sheet for checking the crops (not published: starts with _)
    if tiles:
        T, cols = 260, 4
        rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * T, rows * T), (236, 238, 243))
        d = ImageDraw.Draw(sheet, "RGBA")
        f = font(20)
        for i, (n, c) in enumerate(tiles):
            t = c.copy()
            t.thumbnail((T - 16, T - 16))
            ox, oy = (i % cols) * T, (i // cols) * T
            sheet.paste(t, (ox + (T - t.width) // 2, oy + (T - t.height) // 2))
            label(d, (ox + 8, oy + 6), str(n), f, bg=(255, 0, 170, 230))
        sheet.save(os.path.join(outdir, "_sheet.jpg"), quality=85)
    print(f"round '{a.round}': added {len(tiles)} items (now {len(rnd['items'])})")
    print(f"images: {outdir}   check: {os.path.join(outdir, '_sheet.jpg')}")
    print(f"next: fill in name, sub, bio, tags for each item in {a.data}")


# ---------------------------------------------------------------- build / files
def cmd_build(a):
    root = os.path.dirname(os.path.abspath(a.data))
    data = load_data(a.data)
    with open(a.html, encoding="utf-8") as fh:
        html = fh.read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    pat = re.compile(r'(<script id="keepers-data" type="application/json">)(.*?)(</script>)', re.S)
    html, n = pat.subn(lambda m: m.group(1) + blob + m.group(3), html, count=1)
    if n != 1:
        sys.exit("could not find the keepers-data block in " + a.html)
    out = a.out or os.path.join(root, "dist", "index.html")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(html)
    missing = [it["img"] for r in data.get("rounds", []) for it in r.get("items", [])
               if not os.path.exists(os.path.join(root, it["img"]))]
    print(f"built {out}  ({len(data.get('rounds', []))} rounds)")
    if missing:
        print("missing images:", *missing, sep="\n  ")


def cmd_files(a):
    root = os.path.dirname(os.path.abspath(a.data))
    data = load_data(a.data)
    out = {}
    for r in data.get("rounds", []):
        if a.round and r.get("id") != a.round:
            continue
        for it in r.get("items", []):
            if os.path.exists(os.path.join(root, it["img"])):
                out[it["img"]] = it["img"]
    print(json.dumps(out, indent=1))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--data", default=os.path.join(REPO, "rounds.json"), help="rounds file (images live next to it)")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("grid")
    g.add_argument("photo")
    g.add_argument("--out", default="grid.jpg")
    g.add_argument("--step", type=int, default=5)

    d = sub.add_parser("detect")
    d.add_argument("photo")
    d.add_argument("--out", default="boxes.json")
    d.add_argument("--preview", default="detect.jpg")
    d.add_argument("--min", type=float, default=0.4, help="smallest item, percent of photo area")

    c = sub.add_parser("crop")
    c.add_argument("photo")
    c.add_argument("boxes")
    c.add_argument("--round", required=True, help="short id, like books or garage-2")
    c.add_argument("--title")
    c.add_argument("--note")
    c.add_argument("--where", help="label tape text, like 'Blue tote · garage'")
    c.add_argument("--pad", type=float, default=1.5, help="extra margin, percent of photo")
    c.add_argument("--size", type=int, default=1200, help="longest side of each card image")

    b = sub.add_parser("build")
    b.add_argument("--html", default=os.path.join(REPO, "index.html"))
    b.add_argument("--out")

    f = sub.add_parser("files")
    f.add_argument("--round")

    a = p.parse_args()
    {"grid": cmd_grid, "detect": cmd_detect, "crop": cmd_crop, "build": cmd_build, "files": cmd_files}[a.cmd](a)


if __name__ == "__main__":
    main()
