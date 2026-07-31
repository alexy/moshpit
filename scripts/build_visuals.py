#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "book" / "assets"

YELLOW = "#f6d44a"
PURPLE = "#b78cff"
INK = "#f7f1d7"


def font(size, bold=False, mono=False):
    if mono:
        path = "/System/Library/Fonts/SFNSMono.ttf"
    elif bold:
        path = "/System/Library/Fonts/Supplemental/Avenir Next Condensed.ttc"
    else:
        path = "/System/Library/Fonts/Supplemental/Avenir Next.ttc"
    return ImageFont.truetype(path, size=size, index=1 if bold else 0)


def fit_text(draw, text, max_width, start, bold=True):
    size = start
    while size > 24:
        f = font(size, bold=bold)
        if draw.textbbox((0, 0), text, font=f)[2] <= max_width:
            return f
        size -= 2
    return font(size, bold=bold)


def tint_mask(mask_path, color, max_alpha=120):
    mask = Image.open(mask_path).convert("L")
    alpha = mask.point(lambda value: round(value * max_alpha / 255))
    rgba = Image.new("RGBA", mask.size, color)
    rgba.putalpha(alpha)
    return rgba


def dark_gradient(im, top=155, bottom=35):
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    px = layer.load()
    for y in range(im.height):
        a = round(top + (bottom - top) * y / max(1, im.height - 1))
        for x in range(im.width):
            px[x, y] = (5, 12, 17, a)
    return Image.alpha_composite(im.convert("RGBA"), layer)


def compose_cover():
    src = Image.open(ASSETS / "moshpit-cover-art.png").convert("RGB")
    canvas = src.resize((1800, 2700), Image.Resampling.LANCZOS)
    canvas = dark_gradient(canvas, 185, 15)
    draw = ImageDraw.Draw(canvas)
    title1 = "MOSHPIT"
    title2 = "A GUIDE TO AGENT DEVELOPMENT"
    title3 = "WITH MOSH, TMUX AND GHOSTTY"
    f1 = fit_text(draw, title1, 1500, 235)
    f2 = fit_text(draw, title2, 1500, 75)
    f3 = fit_text(draw, title3, 1500, 66)
    for text, y, f, fill in [(title1, 205, f1, YELLOW), (title2, 475, f2, INK), (title3, 575, f3, PURPLE)]:
        box = draw.textbbox((0, 0), text, font=f)
        x = (canvas.width - (box[2] - box[0])) // 2
        draw.text((x + 3, y + 4), text, font=f, fill="#050810", stroke_width=5, stroke_fill="#050810")
        draw.text((x, y), text, font=f, fill=fill)
    author = "ALEXY KHRABROV"
    af = fit_text(draw, author, 1050, 58)
    ab = draw.textbbox((0, 0), author, font=af)
    draw.text(((canvas.width - (ab[2] - ab[0])) // 2, 730), author, font=af, fill=INK)
    mark = tint_mask(ASSETS / "firstpair-publisher-mask.png", "#f2d36b", 128)
    mw = round(canvas.width * 0.22)
    mark = mark.resize((mw, round(mark.height * mw / mark.width)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, ((canvas.width - mark.width) // 2, canvas.height - mark.height - 28))
    canvas.convert("RGB").save(ASSETS / "moshpit-cover.png", quality=96)


def compose_headboard():
    src = Image.open(ASSETS / "moshpit-headboard-art.png").convert("RGB")
    canvas = src.resize((2400, 1350), Image.Resampling.LANCZOS).convert("RGBA")
    shade = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    sd.rectangle((0, 0, 1220, 1350), fill=(3, 9, 14, 135))
    shade = shade.filter(ImageFilter.GaussianBlur(70))
    canvas = Image.alpha_composite(canvas, shade)
    draw = ImageDraw.Draw(canvas)
    f1 = fit_text(draw, "MOSHPIT", 1000, 180)
    f2 = fit_text(draw, "MOSH · TMUX · GHOSTTY", 1000, 56)
    draw.text((145, 245), "MOSHPIT", font=f1, fill=YELLOW, stroke_width=3, stroke_fill="#081017")
    draw.text((155, 465), "MOSH · TMUX · GHOSTTY", font=f2, fill=PURPLE)
    draw.text((155, 555), "A field guide to persistent remote agent work", font=font(42), fill=INK)
    mark = tint_mask(ASSETS / "firstpair-publisher-mask.png", "#f2d36b", 115)
    mw = 360
    mark = mark.resize((mw, round(mark.height * mw / mark.width)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, (155, 1350 - mark.height - 75))
    canvas.convert("RGB").save(ASSETS / "moshpit-headboard.png", quality=95)


def terminal_shot(name, title, lines, highlights=()):
    w, pad, line_h = 1800, 78, 49
    h = 135 + pad + line_h * len(lines) + 70
    im = Image.new("RGB", (w, h), "#101319")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((12, 12, w - 12, h - 12), radius=28, fill="#11151c", outline="#39404d", width=3)
    d.rounded_rectangle((12, 12, w - 12, 82), radius=28, fill="#242a34")
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        d.ellipse((38 + i * 42, 35, 58 + i * 42, 55), fill=c)
    tf = font(29, bold=True)
    tb = d.textbbox((0, 0), title, font=tf)
    d.text(((w - (tb[2] - tb[0])) // 2, 28), title, font=tf, fill="#cbd2dc")
    mf = font(29, mono=True)
    y = 115
    for idx, line in enumerate(lines):
        fill = YELLOW if idx in highlights else (PURPLE if line.lstrip().startswith("#") else "#e5e9f0")
        d.text((pad, y), line, font=mf, fill=fill)
        y += line_h
    im.save(ASSETS / name, quality=94)


def build_screenshots():
    terminal_shot("screenshot-ghostty.png", "Mac · ~/.config/ghostty/config", [
        "clipboard-write = allow",
        "keybind = cmd+left=previous_tab",
        "keybind = cmd+right=next_tab",
        "",
        "# Ghostty receives OSC 52 and writes the Mac clipboard.",
    ], (0, 1, 2))
    terminal_shot("screenshot-tmux-copy.png", "Remote Linux · ~/.tmux.conf", [
        "set -g mouse on",
        "setw -g mode-keys vi",
        "set -g copy-command 'ssh mac pbcopy'",
        "set -g set-clipboard on",
        "set -as terminal-features ',*:clipboard'",
        r"set -as terminal-overrides ',*:Ms=\E]52;c%p1%.0s;%p2%s\7'",
        "",
        "bind -T copy-mode-vi MouseDragEnd1Pane send -X copy-pipe-no-clear",
    ], (2, 5, 7))
    terminal_shot("screenshot-session.png", "Moshpit · named windows and scrollback", [
        "┌ agent-api ───────────────┬ tests ──────────────────────┐",
        "│ $ codex                  │ $ pytest -q                │",
        "│ editing remote code…     │ 128 passed                 │",
        "├ logs ────────────────────┴──────────────────────────────┤",
        "│ $ journalctl -f          Shift+←/→ changes tmux windows │",
        "│                           C-b , renames a window         │",
        "└──────────────────────────────────────────────────────────┘",
        "mouse wheel → tmux copy-mode → inspect long output",
    ], (0, 7))


if __name__ == "__main__":
    compose_cover()
    compose_headboard()
    build_screenshots()
