#!/usr/bin/env python3
"""
WiFi QR Card Generator
Generates a print-ready 4x6 PNG with a scannable WiFi QR code.

Requirements:
    pip install pillow reportlab

Usage:
    python wifi_qr_generator.py
    python wifi_qr_generator.py --title "Guest" --ssid "MyNetwork" --password "MyPass123!"
    python wifi_qr_generator.py --title "Home" --ssid "MyNet" --password "abc123" --output home.png
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("Missing dependency: pip install pillow")

try:
    from reportlab.graphics.barcode.qr import QrCodeWidget
except ImportError:
    sys.exit("Missing dependency: pip install reportlab")


# ── Colour palette ────────────────────────────────────────────────────────────
BLUE_DARK  = (27,  45,  66)
BLUE_MID   = (27,  79, 138)
BLUE_LIGHT = (197, 213, 232)
GRAY_LIGHT = (221, 228, 237)
GRAY_MED   = (90,  122, 154)
WHITE      = (255, 255, 255)
BLACK      = (0,   0,   0)


# ── Font discovery ────────────────────────────────────────────────────────────
BOLD_FONTS = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",   # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",       # Linux fallback
    "/Library/Fonts/Arial Bold.ttf",                               # macOS
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",          # macOS alt
    "C:/Windows/Fonts/arialbd.ttf",                                # Windows
]
REG_FONTS = [
    "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
    "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

def _first(paths):
    for p in paths:
        if Path(p).exists():
            return p
    return None


def make_qr_image(wifi_string: str, size_px: int, quiet: int = 4) -> Image.Image:
    """
    Render a WiFi QR code as a PIL image using only reportlab's QR matrix.
    Does NOT use renderPM or Cairo — no extra native libraries needed.
    """
    widget = QrCodeWidget(wifi_string)
    qr = widget.qr
    qr.make()
    n = qr.moduleCount

    total  = n + 2 * quiet
    cell   = max(1, size_px // total)
    canvas = Image.new("RGB", (total * cell, total * cell), WHITE)
    draw   = ImageDraw.Draw(canvas)

    for r in range(n):
        for c in range(n):
            if qr.isDark(r, c):
                x0 = (c + quiet) * cell
                y0 = (r + quiet) * cell
                draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=BLACK)

    return canvas.resize((size_px, size_px), Image.NEAREST)


def generate_card(title: str, ssid: str, password: str, output_path: str) -> None:
    DPI = 600
    W   = int(4 * DPI)   # 1200 px
    H   = int(6 * DPI)   # 1800 px

    img  = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    bold_path = _first(BOLD_FONTS)
    reg_path  = _first(REG_FONTS)
    if not bold_path:
        sys.exit("No bold font found. Install fonts-open-sans or place Arial Bold on your system.")
    if not reg_path:
        reg_path = bold_path

    fnt_tag   = ImageFont.truetype(bold_path, int(0.130 * DPI))
    fnt_title = ImageFont.truetype(bold_path, int(0.420 * DPI))
    fnt_sub   = ImageFont.truetype(reg_path,  int(0.100 * DPI))
    fnt_label = ImageFont.truetype(reg_path,  int(0.095 * DPI))
    fnt_value = ImageFont.truetype(bold_path, int(0.130 * DPI))

    pad = int(0.28 * DPI)
    cy  = int(0.14 * DPI)

    # ── Top accent bar ────────────────────────────────────────────────────────
    draw.rectangle([(0, 0), (W, int(0.10 * DPI))], fill=BLUE_MID)

    # ── Tag pill ──────────────────────────────────────────────────────────────
    tag_text = "WI-FI NETWORK QR CODE"
    tb = draw.textbbox((0, 0), tag_text, font=fnt_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    px, py = int(0.12 * DPI), int(0.08 * DPI)
    tx = (W - tw - 2 * px) // 2
    pill_height = th + 2*py
    pill_y = cy
    draw.rectangle([(tx, pill_y), (tx + tw + 2*px, pill_y + pill_height)], fill=BLUE_MID)
    text_y = pill_y + py
    draw.text((tx + px, text_y-5), tag_text, font=fnt_tag, fill=WHITE)
    cy += pill_height + int(0.12 * DPI)

    # ── Title ──────────────────────────────────────────────────────────────
    tb = draw.textbbox((0, 0), title, font=fnt_title)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.text(((W - tw) // 2, cy), title, font=fnt_title, fill=BLUE_DARK)
    cy += th + int(0.15 * DPI)

    # ── Subtitle ──────────────────────────────────────────────────────────────
    sub = "Scan to connect instantly"
    tb  = draw.textbbox((0, 0), sub, font=fnt_sub)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.text(((W - tw) // 2, cy), sub, font=fnt_sub, fill=GRAY_MED)
    cy += th + int(0.35 * DPI)

    # ── QR code ───────────────────────────────────────────────────────────────
    wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};H:false;;"
    qr_px  = int(2.80 * DPI)
    qr_img = make_qr_image(wifi_string, qr_px)

    border = int(0.07 * DPI)
    shadow = int(0.04 * DPI)
    qx = (W - qr_px - 2 * border) // 2

    draw.rectangle(                                              # drop shadow
        [(qx+shadow, cy+shadow),
         (qx+qr_px+2*border+shadow, cy+qr_px+2*border+shadow)],
        fill=BLUE_LIGHT,
    )
    draw.rectangle(                                              # blue border
        [(qx, cy), (qx+qr_px+2*border, cy+qr_px+2*border)],
        fill=BLUE_MID,
    )
    draw.rectangle(                                              # white inset
        [(qx+border, cy+border), (qx+border+qr_px, cy+border+qr_px)],
        fill=WHITE,
    )
    img.paste(qr_img, (qx+border, cy+border))
    cy += qr_px + 2*border + int(0.20 * DPI)

    # ── Divider ───────────────────────────────────────────────────────────────
    draw.rectangle([(pad, cy), (W-pad, cy+3)], fill=GRAY_LIGHT)
    cy += int(0.12 * DPI)

    # ── Info rows ─────────────────────────────────────────────────────────────
    rows = [
        ("Network",  ssid,       True),
        ("Password", password,   False),
        ("Security", "WPA/WPA2", False),
    ]
    for label, value, highlight in rows:
        lb = draw.textbbox((0, 0), label.upper(), font=fnt_label)
        vb = draw.textbbox((0, 0), value,          font=fnt_value)
        lh, vh = lb[3]-lb[1], vb[3]-vb[1]
        row_h  = max(lh, vh)

        draw.text((pad, cy+(row_h-lh)//2),
                  label.upper(), font=fnt_label, fill=GRAY_MED)
        draw.text((W-pad-(vb[2]-vb[0]), cy+(row_h-vh)//2),
                  value, font=fnt_value,
                  fill=BLUE_MID if highlight else BLUE_DARK)

        cy += row_h + int(0.08 * DPI)
        draw.rectangle([(pad, cy), (W-pad, cy+2)], fill=GRAY_LIGHT)
        cy += int(0.08 * DPI)

    # ── Footer ────────────────────────────────────────────────────────────────
    footer = "Point your camera at the code above"
    fb = draw.textbbox((0, 0), footer, font=fnt_sub)
    draw.text(((W-(fb[2]-fb[0]))//2, cy+int(0.05*DPI)),
              footer, font=fnt_sub, fill=BLUE_LIGHT)

    # ── Save ──────────────────────────────────────────────────────────────────
    img.save(output_path, dpi=(DPI, DPI))
    print(f"Saved: {output_path}  ({W}x{H} px @ {DPI} dpi)")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate a print-ready 4x6 WiFi QR card (PNG)."
    )
    parser.add_argument("--title",    help='Card label, e.g. "Guest" or "Home"')
    parser.add_argument("--ssid",     help="WiFi network name (SSID)")
    parser.add_argument("--password", help="WiFi password")
    parser.add_argument("--output",   default="wifi_qr.png",
                        help="Output filename (default: wifi_qr.png)")
    args = parser.parse_args()

    title    = args.title    or input("Network label (e.g. Guest, Home): ").strip()
    ssid     = args.ssid     or input("Network name (SSID): ").strip()
    password = args.password or input("Password: ").strip()

    if not title or not ssid or not password:
        sys.exit("Error: title, SSID, and password are all required.")

    generate_card(title, ssid, password, args.output)


if __name__ == "__main__":
    main()
