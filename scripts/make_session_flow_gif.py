"""Generates the animated login + session lifecycle GIF for the "Architecture & Workflow" tab.

Run from the repo root (uses the backend's venv, which already has Pillow):
    uv run --directory backend python ../scripts/make_session_flow_gif.py

Output: frontend/src/assets/session-flow.gif
Reuses the theme and drawing helpers from make_naive_rag_flow_gif.py so both GIFs match.
"""
from pathlib import Path

from PIL import Image, ImageDraw

from make_naive_rag_flow_gif import (
    BG, BLUE, BORDER, CARD, CYAN, F_CAP_D, F_CAP_T, F_MONO, F_NUM, F_SMALL, F_SUB, F_TITLE, FRAME_MS,
    GREEN, MARGIN, MUTED, NODE_H, TEXT, arrow, glow_dot, mix,
)

OUT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "assets" / "session-flow.gif"
W, H = 1200, 380
AMBER, RED = (251, 191, 36), (248, 113, 113)

# ---------- layout: 5 nodes in one row, two "end" triggers below node 4 ----------
ROW_Y = 92
COL_W = (W - 2 * MARGIN) / 5
NODE_W = 196          # wider than the RAG GIF's nodes: only 5 columns here
TRIG_Y = 238


def col_x(i: float) -> float:
    return MARGIN + COL_W * (i + 0.5)


# key: (column, number, title, subtitle, caption title, caption text, color)
NODES = {
    "login":   (0, 1, "Login / Sign up", "POST /auth/login", "Login or sign up",
                "Passwords are checked against scrypt hashes in storage/users.db.", BLUE),
    "token":   (1, 2, "Token + session", "server-issued", "Token + session id",
                "The server returns a token AND a new session id; the browser sends both on every request.", BLUE),
    "work":    (2, 3, "Upload & ask", "one file at a time", "Upload and ask",
                "Each request refreshes last_active. A new upload replaces the old file, vectors and index.", CYAN),
    "ends":    (3, 4, "Session ends", "logout or timeout", "Session ends",
                "Either the user logs out, or the cleanup job (every 5 min) finds the session expired.", AMBER),
    "deleted": (4, 5, "Data deleted", "file · vectors · index", "Everything is deleted",
                "data/sessions/<id>, storage/sessions/<id> and the in-memory index are removed; the token stops working.", GREEN),
}
ORDER = ["login", "token", "work", "ends", "deleted"]
TRIGGERS = {   # shown under "Session ends"
    "logout":  (col_x(3) - 96, "Logout", "deleted immediately"),
    "timeout": (col_x(3) + 96, "60 min idle / 24 h", "cleanup job, every 5 min"),
}
TRIG_W, TRIG_H = 182, 50

HOLD, MOVE, LOOP, TRIG, END_HOLD = 30, 12, 34, 30, 50


def node_box(key):
    x = col_x(NODES[key][0])
    return (x - NODE_W / 2, ROW_Y - NODE_H / 2, x + NODE_W / 2, ROW_Y + NODE_H / 2)


def trig_box(key):
    x = TRIGGERS[key][0]
    return (x - TRIG_W / 2, TRIG_Y - TRIG_H / 2, x + TRIG_W / 2, TRIG_Y + TRIG_H / 2)


def edge_points(a, b):
    ax0, ay0, ax1, ay1 = node_box(a)
    bx0, by0, *_ = node_box(b)
    return (ax1 + 2, ROW_Y), (bx0 - 8, ROW_Y)


# ---------- timeline ----------
def build_timeline():
    frames = []

    def add(n, **state):
        for i in range(n):
            frames.append({"active": None, "done": set(), "trigger": None, **state, "t": i / max(n - 1, 1)})

    done = set()
    for i, key in enumerate(ORDER):
        color = NODES[key][6]
        if key == "work":
            add(HOLD // 2, active=key, done=set(done), cap=key)
            # requests going back and forth: each one refreshes last_active
            add(LOOP, active=key, done=set(done), cap=key, loop=True)
            add(LOOP, active=key, done=set(done), cap=key, loop=True)
        elif key == "ends":
            add(HOLD // 2, active=key, done=set(done), cap=key)
            add(TRIG, active=key, done=set(done), cap="logout", trigger="logout")
            add(TRIG, active=key, done=set(done), cap="timeout", trigger="timeout")
        elif key == "deleted":
            add(HOLD + 10, active=key, done=set(done), cap=key, wipe=True)
        else:
            add(HOLD, active=key, done=set(done), cap=key)
        done.add(key)
        if i < len(ORDER) - 1:
            add(MOVE, done=set(done), cap=key, edge=(key, ORDER[i + 1]), color=color)
    add(END_HOLD, done=set(ORDER), cap="end")
    return frames


# ---------- drawing ----------
def draw_box(img, d, box, title, sub, color, active, done, num=None):
    if active:
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).rounded_rectangle(
            (box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), radius=18, fill=(*color, 45))
        img.alpha_composite(layer)
        d = ImageDraw.Draw(img)
    fill = mix(CARD, color, 0.18) if active else CARD
    outline = color if active else (mix(BORDER, GREEN, 0.35) if done else BORDER)
    d.rounded_rectangle(box, radius=12, fill=fill, outline=outline, width=2 if active else 1)
    tx0, tx1 = box[0] + (30 if num else 10), box[2] - (16 if num else 10)
    if num:
        bx, by = box[0] + 10, box[1] + 9
        d.ellipse((bx, by, bx + 17, by + 17), fill=color if (active or done) else BORDER)
        nw = d.textlength(str(num), font=F_NUM)
        d.text((bx + 8.5 - nw / 2, by + 1), str(num), font=F_NUM, fill=BG if (active or done) else MUTED)
    tw = d.textlength(title, font=F_TITLE)
    d.text(((tx0 + tx1 - tw) / 2, box[1] + (10 if num else 6)), title, font=F_TITLE, fill=TEXT)
    sw = d.textlength(sub, font=F_SUB)
    d.text(((box[0] + box[2] - sw) / 2, box[1] + (42 if num else 28)), sub, font=F_SUB, fill=TEXT if active else MUTED)
    if done:
        d.ellipse((box[2] - 15, box[1] + 9, box[2] - 6, box[1] + 18), fill=GREEN)
    return d


def draw_static(d):
    for a, b in zip(ORDER, ORDER[1:]):
        arrow(d, *edge_points(a, b), BORDER)
    # triggers hang under "Session ends"
    e = node_box("ends")
    for key in TRIGGERS:
        t = trig_box(key)
        x = (t[0] + t[2]) / 2
        d.line((x, e[3] + 4, x, t[1] - 4), fill=BORDER, width=1)
    # "keeps the session alive" label under Upload & ask
    w = node_box("work")
    label = "every request: Bearer token + X-Session-Id"
    lw = d.textlength(label, font=F_SMALL)
    d.text(((w[0] + w[2] - lw) / 2, w[3] + 30), label, font=F_SMALL, fill=MUTED)
    label = "→ last_active updated"
    lw = d.textlength(label, font=F_SMALL)
    d.text(((w[0] + w[2] - lw) / 2, w[3] + 48), label, font=F_SMALL, fill=MUTED)


def draw_caption(d, cap):
    top = H - 78
    d.rounded_rectangle((MARGIN, top, W - MARGIN, H - 16), radius=12, fill=CARD, outline=BORDER)
    if cap == "end":
        title, text, color = ("Done", "Your account (storage/users.db) is kept: log in again for a fresh, empty session.",
                              GREEN)
    elif cap == "logout":
        title, text, color = "Logout", "POST /auth/logout ends the login and deletes the session's data right away.", RED
    elif cap == "timeout":
        title, text, color = ("Timeout", "No request for 60 minutes, or 24 hours since login: the cleanup job deletes it "
                              "(also at server start).", AMBER)
    else:
        _c, _n, _t, _s, title, text, color = NODES[cap]
    d.ellipse((MARGIN + 18, top + 25, MARGIN + 30, top + 37), fill=color)
    d.text((MARGIN + 42, top + 9), title, font=F_CAP_T, fill=color)
    d.text((MARGIN + 42, top + 32), text, font=F_CAP_D, fill=TEXT)


def render(state):
    img = Image.new("RGBA", (W, H), (*BG, 255))
    d = ImageDraw.Draw(img)
    draw_static(d)

    if state.get("edge"):
        arrow(d, *edge_points(*state["edge"]), state["color"])

    for key in ORDER:
        _c, num, title, sub, _ct, _cx, color = NODES[key]
        d = draw_box(img, d, node_box(key), title, sub, color, key == state["active"], key in state["done"], num)

    for key, (_x, title, sub) in TRIGGERS.items():
        color = RED if key == "logout" else AMBER
        d = draw_box(img, d, trig_box(key), title, sub, color, key == state["trigger"], False)

    t = state["t"]
    ease = t * t * (3 - 2 * t)
    if state.get("edge"):
        (x0, y0), (x1, y1) = edge_points(*state["edge"])
        glow_dot(img, x0 + (x1 - x0) * ease, y0, state["color"])
    if state.get("loop"):
        # a request travels down to the API and back up, under the "Upload & ask" box
        w = node_box("work")
        x = (w[0] + w[2]) / 2
        y = w[3] + 4 + 22 * (1 - abs(1 - 2 * ease))
        glow_dot(img, x, y, CYAN, r=5)
    if state.get("trigger"):
        b = trig_box(state["trigger"])
        e = node_box("ends")
        x = (b[0] + b[2]) / 2
        glow_dot(img, x, b[1] - 4 + (e[3] + 4 - (b[1] - 4)) * ease, RED if state["trigger"] == "logout" else AMBER, r=5)
    if state.get("wipe"):   # the three kinds of data fade out
        dbox = node_box("deleted")
        labels = ["file", "vectors", "index"]
        gap = 18
        widths = [d.textlength(label, font=F_SMALL) for label in labels]
        x = (dbox[0] + dbox[2] - sum(widths) - gap * (len(labels) - 1)) / 2   # centred under the box
        d = ImageDraw.Draw(img)
        for i, (label, lw) in enumerate(zip(labels, widths)):
            col = mix(BG, RED, max(0.0, 1 - ease * 1.4 + i * 0.15))
            d.text((x, dbox[3] + 10), label, font=F_SMALL, fill=col)
            d.line((x, dbox[3] + 19, x + lw * min(1, ease * 1.6), dbox[3] + 19), fill=col, width=1)  # strike-through
            x += lw + gap

    draw_caption(ImageDraw.Draw(img), state["cap"])
    return img.convert("RGB")


def main():
    timeline = build_timeline()
    frames = [render(s) for s in timeline]
    # Build the shared palette from many frames so short-lived colours (the red Logout) survive
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
