"""Generates the animated Naive RAG flow GIF shown in the frontend's "Architecture & Workflow" tab.

Run from the repo root (uses the backend's venv, which already has Pillow):
    uv run --directory backend python ../scripts/make_naive_rag_flow_gif.py

Output: frontend/src/assets/naive-rag-flow.gif
Edit STEPS / timing below if the pipeline changes.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "assets" / "naive-rag-flow.gif"

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

# ---------- layout: 7 columns, ingestion row on top, query row below (staggered) ----------
MARGIN, COLS = 24, 7
COL_W = (W - 2 * MARGIN) / COLS
NODE_W, NODE_H = 142, 70
TOP_Y, BOT_Y = 82, 250


def col_x(i: int) -> float:
    return MARGIN + COL_W * (i + 0.5)


# key: (row y, column, number, title, subtitle, caption title, caption text, color)
STEPS = {
    "upload":   (TOP_Y, 1, 1, "Upload", "POST /ingest", "Upload",
                 "Replaces the session's previous file in data/sessions/<id>/, then SimpleDirectoryReader reads it.", BLUE),
    "chunk":    (TOP_Y, 2, 2, "Chunk", "SentenceSplitter", "Chunk",
                 "SentenceSplitter cuts the text into 512-token chunks with 50 tokens of overlap.", BLUE),
    "embed":    (TOP_Y, 3, 3, "Embed", "text-embed-3-sm", "Embedding",
                 "OpenAI text-embedding-3-small turns every chunk into a vector.", BLUE),
    "store":    (TOP_Y, 4, 4, "Vector DB", "LanceDB + index", "Vector DB + indexing",
                 "Vectors go to the session's LanceDB; the index + chunks are saved next to it (storage/sessions/<id>/).", BLUE),
    "question": (BOT_Y, 2, 1, "Question", "POST /query", "Question",
                 "The chat sends {question, top_k} with the login token + X-Session-Id: only that session's index is used.", CYAN),
    "qembed":   (BOT_Y, 3, 2, "Embed query", "same model", "Embed the question",
                 "The SAME embedding model turns the question into a vector, so it can be compared.", CYAN),
    "retrieve": (BOT_Y, 4, 3, "Retrieve", "top-k = 4", "Retrieve",
                 "VectorIndexRetriever: LanceDB returns the 4 chunks whose vectors are closest.", CYAN),
    "prompt":   (BOT_Y, 5, 4, "Build prompt", "chunks + question", "Build prompt",
                 "The response synthesizer puts the retrieved chunks and the question into one prompt.", CYAN),
    "generate": (BOT_Y, 6, 5, "Generate", "gpt-4o-mini", "Generate",
                 "gpt-4o-mini answers from that context; the API returns the answer + sources.", CYAN),
}
INGEST = ["upload", "chunk", "embed", "store"]
QUERY = ["question", "qembed", "retrieve", "prompt", "generate"]

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
    s, r = node_box("store"), node_box("retrieve")
    x = (s[0] + s[2]) / 2
    return (x, s[3] + 2), (x, r[1] - 8)


# ---------- timeline: list of per-frame states ----------
def build_timeline():
    frames = []

    def add(n, **state):
        for i in range(n):
            frames.append({**state, "t": i / max(n - 1, 1)})

    for flow, color in ((INGEST, BLUE), (QUERY, CYAN)):
        for i, key in enumerate(flow):
            done_before = set(INGEST[: INGEST.index(key)] if flow is INGEST else INGEST + QUERY[: QUERY.index(key)])
            if key == "retrieve":
                add(HOLD // 2, active=key, done=done_before, cap=key)
                # the similarity search: a dot drops from LanceDB down to Retrieve
                add(DROP, active=key, done=done_before, cap=key, drop=True, also="store")
                add(HOLD // 2, active=key, done=done_before, cap=key, also="store", badge=True)
            else:
                add(HOLD, active=key, done=done_before, cap=key)
            if i < len(flow) - 1:
                add(MOVE, active=None, done=done_before | {key}, cap=key, edge=(key, flow[i + 1]), color=color)
    add(END_HOLD, active=None, done=set(INGEST + QUERY), cap="end")
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


def arrow(d, p0, p1, color, width=2, dashed=False):
    (x0, y0), (x1, y1) = p0, p1
    if dashed:
        n = int(max(abs(x1 - x0), abs(y1 - y0)) // 10)
        for k in range(0, n, 2):
            a, b = k / n, min((k + 1) / n, 1)
            d.line((x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b), fill=color, width=width)
        return
    d.line((x0, y0, x1, y1), fill=color, width=width)
    if x1 != x0:   # horizontal arrowhead
        d.polygon([(x1 + 7, y1), (x1, y1 - 5), (x1, y1 + 5)], fill=color)
    else:          # vertical arrowhead (pointing down)
        d.polygon([(x1, y1 + 7), (x1 - 5, y1), (x1 + 5, y1)], fill=color)


def mix(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def draw_static(d):
    # row labels in the two empty corners of the staggered layout
    x = col_x(5) - NODE_W / 2
    d.text((x, TOP_Y - 34), "1  INGESTION", font=F_LABEL, fill=BLUE)
    d.text((x, TOP_Y - 6), "POST /api/v1/naive/ingest", font=F_MONO, fill=TEXT)
    d.text((x, TOP_Y + 14), "one file per session, replaced on upload", font=F_SMALL, fill=MUTED)

    x = MARGIN + 8
    d.text((x, BOT_Y - 34), "2  QUERY", font=F_LABEL, fill=CYAN)
    d.text((x, BOT_Y - 6), "POST /api/v1/naive/query", font=F_MONO, fill=TEXT)
    d.text((x, BOT_Y + 14), "runs for every question, per session", font=F_SMALL, fill=MUTED)

    # horizontal edges
    for flow in (INGEST, QUERY):
        for a, b in zip(flow, flow[1:]):
            arrow(d, *edge_points(a, b), BORDER)

    # "same embedding model" (dashed) and "similarity search" (solid) vertical links
    e, q = node_box("embed"), node_box("qembed")
    ex = (e[0] + e[2]) / 2
    arrow(d, (ex, e[3] + 4), (ex, q[1] - 4), MUTED, width=1, dashed=True)
    label = "same embedding model"
    tw = d.textlength(label, font=F_SMALL)
    d.text((ex - tw - 8, (e[3] + q[1]) / 2 - 9), label, font=F_SMALL, fill=MUTED)

    p0, p1 = drop_points()
    arrow(d, p0, p1, BORDER)
    d.text((p0[0] + 10, (p0[1] + p1[1]) / 2 - 9), "similarity search", font=F_SMALL, fill=MUTED)


def draw_node(img, d, key, active, done, highlight):
    y, c, num, title, sub, *_rest, color = STEPS[key]
    box = node_box(key)
    if active:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(
            (box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=18, fill=(*color, 45))
        img.alpha_composite(layer)
        d = ImageDraw.Draw(img)
    fill = mix(CARD, color, 0.18) if active else CARD
    outline = color if (active or highlight) else (mix(BORDER, GREEN, 0.35) if done else BORDER)
    d.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=2 if (active or highlight) else 1)

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
        title, text, color = "Done", "Answer + sources go back to the chat. The animation restarts.", GREEN
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
    if state.get("drop") or state.get("badge"):
        arrow(d, *drop_points(), CYAN)

    for key in STEPS:
        d = draw_node(img, d, key,
                      active=key == state["active"],
                      done=key in state["done"],
                      highlight=key == state.get("also"))

    if state.get("badge"):  # retrieved chunks coming back
        r = node_box("retrieve")
        d.rounded_rectangle((r[2] - 46, r[3] - 12, r[2] + 14, r[3] + 10), radius=10, fill=CYAN)
        d.text((r[2] - 38, r[3] - 10), "4 chunks", font=F_NUM, fill=BG)

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
