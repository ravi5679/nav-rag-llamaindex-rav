"""Generates the animated Hybrid RAG flow GIF for the Hybrid RAG "Architecture & Workflow" tab.

Run from the repo root (uses the backend's venv, which already has Pillow):
    uv run --directory backend python ../scripts/make_hybrid_rag_flow_gif.py

Output: frontend/src/assets/hybrid-rag-flow.gif
Same ingestion as Naive RAG; the query splits into vector + keyword (BM25) search, then fuses.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from make_naive_rag_flow_gif import (
    BG, BLUE, BORDER, CARD, CYAN, F_CAP_D, F_CAP_T, F_LABEL, F_MONO, F_NUM, F_SMALL, FRAME_MS,
    GREEN, MARGIN, MUTED, NODE_H, NODE_W, TEXT, arrow, glow_dot,
)
from make_session_flow_gif import draw_box

OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "assets" / "hybrid-rag-flow.gif"
W, H = 1200, 480
VIOLET = (167, 139, 250)   # keyword search branch

COL_W = (W - 2 * MARGIN) / 7
TOP_Y, MID_Y, BOT_Y = 72, 196, 312
FUSE_Y = (MID_Y + BOT_Y) / 2


def col_x(i: float) -> float:
    return MARGIN + COL_W * (i + 0.5)


# key: (column, row y, number, title, subtitle, caption title, caption text, color)
NODES = {
    "upload":   (0, TOP_Y, 1, "Upload", "POST /ingest", "Upload",
                 "Same as Naive RAG: replaces the session's previous file, then SimpleDirectoryReader reads it.", BLUE),
    "chunk":    (1, TOP_Y, 2, "Chunk", "SentenceSplitter", "Chunk",
                 "SentenceSplitter cuts the text into 512-token chunks with 50 tokens of overlap.", BLUE),
    "embed":    (2, TOP_Y, 3, "Embed", "text-embed-3-sm", "Embedding",
                 "OpenAI text-embedding-3-small turns every chunk into a vector.", BLUE),
    "store":    (3, TOP_Y, 4, "Vector DB", "LanceDB + index", "Vector DB + indexing",
                 "Chunk text + vectors go to the session's LanceDB; the index + chunks are saved next to it.", BLUE),
    "question": (1, MID_Y, 1, "Question", "POST /query", "Question",
                 "The chat sends {question, top_k} to /api/v1/hybrid/query; two searches run in parallel.", CYAN),
    "qembed":   (2, MID_Y, 2, "Embed query", "same model", "Embed the question",
                 "The SAME embedding model turns the question into a vector, for the vector search.", CYAN),
    "vsearch":  (3, MID_Y, 3, "Vector", "meaning · top 5", "Vector search",
                 "LanceDB returns the 5 chunks closest in MEANING (VectorIndexRetriever). Good with synonyms.", CYAN),
    "keyword":  (3, BOT_Y, 3, "Keyword", "BM25 · top 5", "Keyword search (BM25)",
                 "LanceDB full-text search ranks chunks by BM25: finds EXACT words like codes, IDs and names.", VIOLET),
    "fuse":     (4, FUSE_Y, 4, "Fuse", "RRF · top 4", "Fuse with Reciprocal Rank Fusion",
                 "QueryFusionRetriever merges both lists: score = sum of 1/(60 + rank). High in both lists wins.", CYAN),
    "prompt":   (5, FUSE_Y, 5, "Build prompt", "chunks + question", "Build prompt",
                 "The response synthesizer puts the fused chunks and the question into one prompt.", CYAN),
    "generate": (6, FUSE_Y, 6, "Generate", "gpt-4o-mini", "Generate",
                 "gpt-4o-mini answers from that context; the API returns the answer + sources.", CYAN),
}
INGEST = ["upload", "chunk", "embed", "store"]

HOLD, MOVE, DROP, END_HOLD = 26, 12, 22, 55


def box(key):
    c, y = NODES[key][0], NODES[key][1]
    x = col_x(c)
    return (x - NODE_W / 2, y - NODE_H / 2, x + NODE_W / 2, y + NODE_H / 2)


def mid_y(key):
    b = box(key)
    return (b[1] + b[3]) / 2


# ---------- paths (polylines) between nodes ----------
def path(a, b):
    ab, bb = box(a), box(b)
    if (a, b) == ("question", "keyword"):            # down, then right
        x = (ab[0] + ab[2]) / 2
        return [(x, ab[3] + 2), (x, mid_y(b)), (bb[0] - 8, mid_y(b))]
    if b == "fuse":                                    # right, then up/down into Fuse
        xm = (ab[2] + bb[0]) / 2
        return [(ab[2] + 2, mid_y(a)), (xm, mid_y(a)), (xm, mid_y(b)), (bb[0] - 8, mid_y(b))]
    return [(ab[2] + 2, mid_y(a)), (bb[0] - 8, mid_y(b))]


EDGES = [("upload", "chunk"), ("chunk", "embed"), ("embed", "store"),
         ("question", "qembed"), ("qembed", "vsearch"), ("question", "keyword"),
         ("vsearch", "fuse"), ("keyword", "fuse"), ("fuse", "prompt"), ("prompt", "generate")]


def draw_path(d, pts, color, width=2):
    for p0, p1 in zip(pts[:-2], pts[1:-1]):
        d.line((*p0, *p1), fill=color, width=width)
    arrow(d, pts[-2], pts[-1], color, width)


def point_on(pts, t):
    """Point at fraction t (0..1) of the polyline's length."""
    lengths = [abs(x1 - x0) + abs(y1 - y0) for (x0, y0), (x1, y1) in zip(pts, pts[1:])]
    dist = t * sum(lengths)
    for ((x0, y0), (x1, y1)), seg in zip(zip(pts, pts[1:]), lengths):
        if dist <= seg and seg:
            f = dist / seg
            return x0 + (x1 - x0) * f, y0 + (y1 - y0) * f
        dist -= seg
    return pts[-1]


def drop_points():
    s, v = box("store"), box("vsearch")
    x = (s[0] + s[2]) / 2
    return (x, s[3] + 2), (x, v[1] - 8)


# ---------- timeline ----------
def build_timeline():
    frames = []

    def add(n, **state):
        for i in range(n):
            frames.append({"active": set(), "done": set(), "moving": [], "badges": set(), **state,
                           "t": i / max(n - 1, 1)})

    done = set()

    def step(key, hold=HOLD, **extra):
        add(hold, active={key}, done=set(done), cap=key, **extra)
        done.add(key)

    def move(*edges, cap, color=CYAN):
        add(MOVE, done=set(done), cap=cap, moving=[(e, color) for e in edges])

    for a, b in zip(INGEST, INGEST[1:]):
        step(a)
        move((a, b), cap=a, color=BLUE)
    step("store")

    step("question")
    move(("question", "qembed"), cap="question")
    step("qembed")
    move(("qembed", "vsearch"), cap="qembed")
    add(HOLD // 2, active={"vsearch"}, done=set(done), cap="vsearch")
    add(DROP, active={"vsearch"}, done=set(done), cap="vsearch", drop=True)
    step("vsearch", hold=HOLD // 2, badges={"vsearch"})
    move(("question", "keyword"), cap="keyword", color=VIOLET)
    step("keyword", badges={"vsearch", "keyword"})
    move(("vsearch", "fuse"), ("keyword", "fuse"), cap="fuse")
    step("fuse", hold=HOLD + 8, badges={"fuse"})
    move(("fuse", "prompt"), cap="fuse")
    step("prompt")
    move(("prompt", "generate"), cap="prompt")
    step("generate")
    add(END_HOLD, done=set(NODES), cap="end")
    return frames


# ---------- drawing ----------
def draw_static(d):
    for a, b in EDGES:
        draw_path(d, path(a, b), BORDER, 2)
    # "same embedding model" and "similarity search" vertical links
    e, q = box("embed"), box("qembed")
    ex = (e[0] + e[2]) / 2
    arrow(d, (ex, e[3] + 4), (ex, q[1] - 4), MUTED, width=1, dashed=True)
    label = "same embedding model"
    d.text((ex - d.textlength(label, font=F_SMALL) - 8, (e[3] + q[1]) / 2 - 9), label, font=F_SMALL, fill=MUTED)
    p0, p1 = drop_points()
    arrow(d, p0, p1, BORDER)
    d.text((p0[0] + 10, (p0[1] + p1[1]) / 2 - 9), "similarity search", font=F_SMALL, fill=MUTED)
    # keyword search reads the same LanceDB table (full-text index on the chunk text)
    k = box("keyword")
    d.text((k[2] + 10, k[1] + 46), "full-text index on the same LanceDB table", font=F_SMALL, fill=MUTED)

    # row labels in the empty corners
    x = col_x(4) - NODE_W / 2
    d.text((x, TOP_Y - 30), "1  INGESTION", font=F_LABEL, fill=BLUE)
    d.text((x, TOP_Y - 2), "POST /api/v1/hybrid/ingest", font=F_MONO, fill=TEXT)
    d.text((x, TOP_Y + 18), "same steps as Naive RAG", font=F_SMALL, fill=MUTED)
    x = MARGIN + 8
    d.text((x, BOT_Y - 34), "2  QUERY", font=F_LABEL, fill=CYAN)
    d.text((x, BOT_Y - 6), "POST /api/v1/hybrid/query", font=F_MONO, fill=TEXT)
    d.text((x, BOT_Y + 14), "two searches, one answer", font=F_SMALL, fill=MUTED)


def draw_badge(d, key, text, color):
    b = box(key)
    w = d.textlength(text, font=F_NUM) + 16
    d.rounded_rectangle((b[2] - w + 12, b[3] - 11, b[2] + 12, b[3] + 10), radius=10, fill=color)
    d.text((b[2] - w + 20, b[3] - 9), text, font=F_NUM, fill=BG)


def draw_caption(d, cap):
    top = H - 78
    d.rounded_rectangle((MARGIN, top, W - MARGIN, H - 16), radius=12, fill=CARD, outline=BORDER)
    if cap == "end":
        title, text, color = "Done", "Answer + sources go back to the chat. The animation restarts.", GREEN
    else:
        *_x, title, text, color = NODES[cap]
    d.ellipse((MARGIN + 18, top + 25, MARGIN + 30, top + 37), fill=color)
    d.text((MARGIN + 42, top + 9), title, font=F_CAP_T, fill=color)
    d.text((MARGIN + 42, top + 32), text, font=F_CAP_D, fill=TEXT)


def render(state):
    img = Image.new("RGBA", (W, H), (*BG, 255))
    d = ImageDraw.Draw(img)
    draw_static(d)

    for (a, b), color in state["moving"]:
        draw_path(d, path(a, b), color, 2)
    if state.get("drop"):
        arrow(d, *drop_points(), CYAN)

    for key, (_c, _y, num, title, sub, _ct, _cx, color) in NODES.items():
        d = draw_box(img, d, box(key), title, sub, color, key in state["active"], key in state["done"], num)

    if "vsearch" in state["badges"]:
        draw_badge(d, "vsearch", "5 by meaning", CYAN)
    if "keyword" in state["badges"]:
        draw_badge(d, "keyword", "5 by keyword", VIOLET)
    if "fuse" in state["badges"]:
        draw_badge(d, "fuse", "top 4 fused", GREEN)

    t = state["t"]
    ease = t * t * (3 - 2 * t)
    for (a, b), color in state["moving"]:
        glow_dot(img, *point_on(path(a, b), ease), color)
    if state.get("drop"):
        (x0, y0), (x1, y1) = drop_points()
        glow_dot(img, x0, y0 + (y1 - y0) * ease, BLUE)

    draw_caption(ImageDraw.Draw(img), state["cap"])
    return img.convert("RGB")


def main():
    frames = [render(s) for s in build_timeline()]
    picks = frames[:: max(1, len(frames) // 12)]
    sample = Image.new("RGB", (W, H * len(picks)))
    for i, f in enumerate(picks):
        sample.paste(f, (0, H * i))
    palette = sample.quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    gif_frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    gif_frames[0].save(OUT, save_all=True, append_images=gif_frames[1:],
                       duration=FRAME_MS, loop=0, optimize=True, disposal=1)
    print(f"Wrote {OUT} ({len(frames)} frames, {len(frames) * FRAME_MS / 1000:.1f}s, "
          f"{OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
