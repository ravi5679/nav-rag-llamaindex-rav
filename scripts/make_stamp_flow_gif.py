"""Generates the animated stamp-verification flow GIF shown in the "Architecture & Workflow" tab.

Run from the repo root (uses the backend's venv, which already has Pillow):
    uv run --directory backend python ../scripts/make_stamp_flow_gif.py

Output: frontend/src/assets/stamp-verification-flow.gif
Same look as make_naive_rag_flow_gif.py. Edit STEPS / timing below if the pipeline changes.
Keep in sync with backend/stamp_verification/.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "assets" / "stamp-verification-flow.gif"

# ---------- canvas + theme (matches frontend/src/shared/theme/global.css) ----------
W, H = 1200, 410
BG, CARD, BORDER = (7, 13, 26), (15, 24, 48), (29, 43, 77)
TEXT, MUTED = (232, 238, 252), (147, 160, 189)
BLUE, CYAN, GREEN = (59, 130, 246), (34, 211, 238), (74, 222, 128)

FONTS = Path("C:/Windows/Fonts")
F_TITLE = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 15)
F_SUB = ImageFont.truetype(str(FONTS / "consola.ttf"), 12)
F_NUM = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 11)
F_LABEL = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 20)
F_SMALL = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 13)
F_MONO = ImageFont.truetype(str(FONTS / "consola.ttf"), 13)
F_CAP_T = ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 17)
F_CAP_D = ImageFont.truetype(str(FONTS / "segoeui.ttf"), 15)

# ---------- layout: 7 columns, detection row on top (left), verification row below (right) ----------
MARGIN, COLS = 24, 7
COL_W = (W - 2 * MARGIN) / COLS
NODE_W, NODE_H = 142, 70
TOP_Y, BOT_Y = 82, 250


def col_x(i: int) -> float:
    return MARGIN + COL_W * (i + 0.5)


# key: (row y, column, number, title, subtitle, caption title, caption text, color)
STEPS = {
    "upload":   (TOP_Y, 0, 1, "Upload PDF", "POST /verify", "Upload",
                 "The page sends the PDF with the login token. Only .pdf, max 20 MB and 20 pages; it is processed in memory, not stored.", BLUE),
    "render":   (TOP_Y, 1, 2, "Render pages", "PyMuPDF 200 dpi", "Render pages",
                 "Every page becomes an image, so scans, pasted images and vector stamps are all caught.", BLUE),
    "ink":      (TOP_Y, 2, 3, "Ink mask", "HSV saturation", "Ink mask",
                 "Keep only coloured ink (saturation). Black text and white paper drop out, even text printed over a stamp.", BLUE),
    "blobs":    (TOP_Y, 3, 4, "Find stamps", "contours + shape", "Find stamp-like regions",
                 "Close gaps so each stamp is one blob, then keep round / rectangular shapes of the right size and ink density.", BLUE),
    "features": (BOT_Y, 3, 1, "Features", "SIFT on ink", "Features",
                 "Each crop is scaled, its ink cleaned (Otsu), and SIFT keypoints are found: the same way as the references.", CYAN),
    "match":    (BOT_Y, 4, 2, "Match", "vs stamps/*.png", "Match every reference",
                 "Keypoints are compared with every reference stamp in backend/stamps/; Lowe's ratio test drops ambiguous pairs.", CYAN),
    "align":    (BOT_Y, 5, 3, "Align", "RANSAC + overlap", "Align + overlap",
                 "RANSAC finds one rotation / scale / shift that most matches agree on; the warped ink overlap confirms the shape.", CYAN),
    "decide":   (BOT_Y, 6, 4, "Decide", "≥ 0.55 + margin", "Decide",
                 "confidence = 0.7 · keypoints + 0.3 · overlap. Matched only if ≥ 0.55 and 0.10 ahead of the runner-up.", CYAN),
}
DETECT = ["upload", "render", "ink", "blobs"]
VERIFY = ["features", "match", "align", "decide"]

# ---------- timing (frames at 40 ms = 25 fps) ----------
FRAME_MS = 40
HOLD, MOVE, DROP, END_HOLD = 26, 12, 22, 55


def node_box(key):
    y, c = STEPS[key][0], STEPS[key][1]
    x = col_x(c)
    return (x - NODE_W / 2, y - NODE_H / 2, x + NODE_W / 2, y + NODE_H / 2)


def edge_points(a, b):
    ax0, ay0, ax1, ay1 = node_box(a)
    bx0, by0, bx1, by1 = node_box(b)
    return (ax1 + 2, (ay0 + ay1) / 2), (bx0 - 8, (by0 + by1) / 2)


def drop_points():
    s, r = node_box("blobs"), node_box("features")
    x = (s[0] + s[2]) / 2
    return (x, s[3] + 2), (x, r[1] - 8)


# ---------- timeline: list of per-frame states ----------
def build_timeline():
    frames = []

    def add(n, **state):
        for i in range(n):
            frames.append({**state, "t": i / max(n - 1, 1)})

    for flow, color in ((DETECT, BLUE), (VERIFY, CYAN)):
        for i, key in enumerate(flow):
            done_before = set(DETECT[: DETECT.index(key)] if flow is DETECT else DETECT + VERIFY[: VERIFY.index(key)])
            if key == "decide":
                add(HOLD // 2, active=key, done=done_before, cap=key)
                add(HOLD // 2, active=key, done=done_before, cap=key, badge=True)
            else:
                add(HOLD, active=key, done=done_before, cap=key)
            if i < len(flow) - 1:
                add(MOVE, active=None, done=done_before | {key}, cap=key, edge=(key, flow[i + 1]), color=color)
        if flow is DETECT:   # the detected crops drop down to the verification row
            add(DROP, active=None, done=set(DETECT), cap="blobs", drop=True)
    add(END_HOLD, active=None, done=set(DETECT + VERIFY), cap="end")
    return frames


# ---------- drawing ----------
def glow_dot(img, x, y, color, r=7):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for rr, a in ((r + 9, 40), (r + 5, 80), (r + 2, 140)):
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(*color, a))
    d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 255))
    d.ellipse((x - r + 2, y - r + 2, x + r - 2, y + r - 2), fill=(*color, 255))
    img.alpha_composite(layer)


def arrow(d, p0, p1, color, width=2):
    (x0, y0), (x1, y1) = p0, p1
    d.line((x0, y0, x1, y1), fill=color, width=width)
    if x1 != x0:   # horizontal arrowhead
        d.polygon([(x1 + 7, y1), (x1, y1 - 5), (x1, y1 + 5)], fill=color)
    else:          # vertical arrowhead (pointing down)
        d.polygon([(x1, y1 + 7), (x1 - 5, y1), (x1 + 5, y1)], fill=color)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_static(d):
    # row labels in the two empty corners of the staggered layout
    x = col_x(4) - NODE_W / 2
    d.text((x, TOP_Y - 34), "1  DETECTION", font=F_LABEL, fill=BLUE)
    d.text((x, TOP_Y - 6), "POST /api/v1/stamps/verify", font=F_MONO, fill=TEXT)
    d.text((x, TOP_Y + 14), "finds stamp-like regions on every page", font=F_SMALL, fill=MUTED)

    x = MARGIN + 8
    d.text((x, BOT_Y - 34), "2  VERIFICATION", font=F_LABEL, fill=CYAN)
    d.text((x, BOT_Y - 6), "runs for every detected stamp", font=F_MONO, fill=TEXT)
    d.text((x, BOT_Y + 14), "compared with each reference stamp", font=F_SMALL, fill=MUTED)

    for flow in (DETECT, VERIFY):
        for a, b in zip(flow, flow[1:]):
            arrow(d, *edge_points(a, b), BORDER)

    p0, p1 = drop_points()
    arrow(d, p0, p1, BORDER)
    d.text((p0[0] + 10, (p0[1] + p1[1]) / 2 - 9), "stamp crops", font=F_SMALL, fill=MUTED)


def draw_node(img, d, key, active, done):
    y, c, num, title, sub, *_rest, color = STEPS[key]
    box = node_box(key)
    if active:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(
            (box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=18, fill=(*color, 45))
        img.alpha_composite(layer)
        d = ImageDraw.Draw(img)
    fill = mix(CARD, color, 0.18) if active else CARD
    outline = color if active else (mix(BORDER, GREEN, 0.35) if done else BORDER)
    d.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=2 if active else 1)

    # step number badge
    bx, by = box[0] + 10, box[1] + 9
    d.ellipse((bx, by, bx + 17, by + 17), fill=color if (active or done) else BORDER)
    nw = d.textlength(str(num), font=F_NUM)
    d.text((bx + 8.5 - nw / 2, by + 1), str(num), font=F_NUM, fill=BG if (active or done) else MUTED)

    # title centred in the space between the number badge and the "done" dot
    tx0, tx1 = box[0] + 30, box[2] - 16
    tw = d.textlength(title, font=F_TITLE)
    d.text(((tx0 + tx1 - tw) / 2, box[1] + 10), title, font=F_TITLE, fill=TEXT)
    cx = (box[0] + box[2]) / 2
    sw = d.textlength(sub, font=F_SUB)
    d.text((cx - sw / 2, box[1] + 42), sub, font=F_SUB, fill=TEXT if active else MUTED)

    if done:   # finished steps keep a small dot
        d.ellipse((box[2] - 15, box[1] + 9, box[2] - 6, box[1] + 18), fill=GREEN)
    return d


def draw_caption(d, cap):
    top = H - 78
    d.rounded_rectangle((MARGIN, top, W - MARGIN, H - 16), radius=12, fill=CARD, outline=BORDER)
    if cap == "end":
        title, text, color = "Done", "Status: Matched, Unknown Stamp or No Stamp, with confidence. The animation restarts.", GREEN
    else:
        _y, _c, _n, _t, _s, title, text, color = STEPS[cap]
    d.ellipse((MARGIN + 18, top + 25, MARGIN + 30, top + 37), fill=color)
    d.text((MARGIN + 42, top + 9), title, font=F_CAP_T, fill=color)
    d.text((MARGIN + 42, top + 32), text, font=F_CAP_D, fill=TEXT)
    # legend
    lx = W - MARGIN - 250
    d.ellipse((lx, top + 15, lx + 9, top + 24), fill=GREEN)
    d.text((lx + 15, top + 10), "finished step", font=F_SMALL, fill=MUTED)
    d.ellipse((lx + 120, top + 14, lx + 131, top + 25), fill=BLUE)
    d.text((lx + 137, top + 10), "data moving", font=F_SMALL, fill=MUTED)


def render(state):
    img = Image.new("RGBA", (W, H), (*BG, 255))
    d = ImageDraw.Draw(img)
    draw_static(d)

    if state.get("edge"):   # light up the edge being travelled
        arrow(d, *edge_points(*state["edge"]), state["color"])
    if state.get("drop"):
        arrow(d, *drop_points(), CYAN)

    for key in STEPS:
        d = draw_node(img, d, key, active=key == state["active"], done=key in state["done"])

    if state.get("badge"):  # the verdict
        r = node_box("decide")
        d.rounded_rectangle((r[2] - 62, r[3] - 12, r[2] + 14, r[3] + 10), radius=10, fill=GREEN)
        d.text((r[2] - 53, r[3] - 10), "Matched", font=F_NUM, fill=BG)

    t = state["t"]
    ease = t * t * (3 - 2 * t)
    if state.get("edge"):
        (x0, y0), (x1, y1) = edge_points(*state["edge"])
        glow_dot(img, x0 + (x1 - x0) * ease, y0 + (y1 - y0) * ease, state["color"])
    if state.get("drop"):
        (x0, y0), (x1, y1) = drop_points()
        glow_dot(img, x0, y0 + (y1 - y0) * ease, BLUE)

    draw_caption(ImageDraw.Draw(img), state["cap"])
    return img.convert("RGB")


def main():
    timeline = build_timeline()
    frames = [render(s) for s in timeline]

    # One shared palette for all frames, so colours don't flicker between frames
    sample = Image.new("RGB", (W, H * 4))
    for i, idx in enumerate((0, len(frames) // 3, 2 * len(frames) // 3, len(frames) - 1)):
        sample.paste(frames[idx], (0, H * i))
    palette = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    gif_frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    gif_frames[0].save(OUT, save_all=True, append_images=gif_frames[1:],
                       duration=FRAME_MS, loop=0, optimize=True, disposal=1)
    print(f"Wrote {OUT} ({len(frames)} frames, {len(frames) * FRAME_MS / 1000:.1f}s, "
          f"{OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
