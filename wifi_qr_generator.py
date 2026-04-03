#!/usr/bin/env python3
"""
WiFi QR Card Generator
Generates a print-ready 4x6 PNG with a scannable WiFi QR code.

Requirements:
    pip install pillow reportlab

Usage:
    python wifi_qr_generator.py
    python wifi_qr_generator.py --name "Guest" --ssid "MyNetwork" --password "MyPass123!"
    python wifi_qr_generator.py --name "Home" --ssid "MyNet" --password "abc123" --output home.png
"""

import argparse
import json
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

import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
from PIL import ImageTk


# ── Load colour presets from JSON ─────────────────────────────────────────────
def _load_presets():
    presets_file = Path(__file__).parent / "presets.json"
    if not presets_file.exists():
        sys.exit(f"Error: presets.json not found at {presets_file}")
    try:
        with open(presets_file, "r") as f:
            data = json.load(f)
        # Convert lists to tuples for use as RGB values
        return {name: {k: tuple(v) if isinstance(v, list) else v for k, v in colors.items()} 
                for name, colors in data.items()}
    except json.JSONDecodeError as e:
        sys.exit(f"Error: Invalid JSON in presets.json: {e}")

presets = _load_presets()


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


def draw_wifi_signal(draw, x: int, y: int, size: int, color: tuple) -> None:
    """
    Draw a WiFi signal icon (dot + radiating arcs) at the given position.
    x, y: center of the icon
    size: approximate height of the icon
    color: RGB tuple for the icon color
    """
    # Dot at the bottom center
    dot_radius = max(1, size // 10)
    dot_gap = max(8, size // 20)  # Gap between dot and first arc
    dot_y = y + size - dot_radius + dot_gap
    draw.ellipse(
        [(x - dot_radius, dot_y - dot_radius), (x + dot_radius, dot_y + dot_radius)],
        fill=color
    )
    
    # Draw 3 concentric arcs radiating upward
    arc_width = max(1, size // 12)
    for arc_num in range(3):
        radius = size // 3 + arc_num * (size // 4)
        # Draw arc from 225° to 315° (upward opening arc)
        bbox = [
            (x - radius, y + size - radius),
            (x + radius, y + size + radius)
        ]
        draw.arc(bbox, start=225, end=315, fill=color, width=arc_width)


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
    canvas = Image.new("RGB", (total * cell, total * cell), (255, 255, 255))
    draw   = ImageDraw.Draw(canvas)

    for r in range(n):
        for c in range(n):
            if qr.isDark(r, c):
                x0 = (c + quiet) * cell
                y0 = (r + quiet) * cell
                draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=(0, 0, 0))

    return canvas.resize((size_px, size_px), Image.NEAREST)


def generate_card(network_name: str, ssid: str, password: str, output_path: str, palette: dict = None) -> None:
    if palette is None:
        palette = presets["Default"]
    
    # Build full palette with common colors
    common = {
        "WHITE": (255, 255, 255),
        "BLACK": (0, 0, 0),
        "GRAY_LIGHT": (221, 228, 237),
        "GRAY_MED": (90, 122, 154),
    }
    full_palette = {**common, **palette}
    
    # Get background color, default to white if not specified
    bg_color = full_palette.get("background", full_palette["WHITE"])
    
    # Calculate text_inverse based on secondary color brightness
    r, g, b = full_palette["secondary"]
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    text_inverse = brightness > 128
    text_on_primary = full_palette["BLACK"] if text_inverse else full_palette["WHITE"]
    
    DPI = 600
    W   = int(4 * DPI)   # 1200 px
    H   = int(6 * DPI)   # 1800 px

    img  = Image.new("RGB", (W, H), bg_color)
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
    draw.rectangle([(0, 0), (W, int(0.10 * DPI))], fill=full_palette["primary"])

    # ── Tag pill ──────────────────────────────────────────────────────────
    tag_text = "WI-FI NETWORK QR CODE"
    tb = draw.textbbox((0, 0), tag_text, font=fnt_tag)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    px, py = int(0.12 * DPI), int(0.08 * DPI)
    tx = (W - tw - 2 * px) // 2
    pill_height = th + 2*py
    pill_y = cy
    
    # WiFi icon size and positioning around the pill
    wifi_icon_size = int(0.3 * DPI)
    wifi_gap = int(0.3 * DPI)
    
    # Calculate pill center Y for icon vertical alignment
    wifi_center_y = cy
    
    # Draw left WiFi icon
    left_wifi_x = tx - wifi_gap - wifi_icon_size // 2
    draw_wifi_signal(draw, left_wifi_x, wifi_center_y, wifi_icon_size, full_palette["primary"])
    
    # Draw pill
    draw.rectangle([(tx, pill_y), (tx + tw + 2*px, pill_y + pill_height)], fill=full_palette["secondary"])
    text_y = pill_y + py
    draw.text((tx + px, text_y-5), tag_text, font=fnt_tag, fill=text_on_primary)
    
    # Draw right WiFi icon
    right_wifi_x = tx + tw + 2*px + wifi_gap + wifi_icon_size // 2
    draw_wifi_signal(draw, right_wifi_x, wifi_center_y, wifi_icon_size, full_palette["primary"])
    
    cy += pill_height + int(0.12 * DPI)

    # ── Network Name ──────────────────────────────────────────────────────────────
    tb = draw.textbbox((0, 0), network_name, font=fnt_title)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.text(((W - tw) // 2, cy), network_name, font=fnt_title, fill=full_palette["BLACK"])
    cy += th + int(0.15 * DPI)

    # ── Subtitle ──────────────────────────────────────────────────────────────
    sub = "Scan to connect instantly"
    tb  = draw.textbbox((0, 0), sub, font=fnt_sub)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    draw.text(((W - tw) // 2, cy), sub, font=fnt_sub, fill=full_palette["GRAY_MED"])
    cy += th + int(0.15 * DPI)

    # ── QR code ───────────────────────────────────────────────────────────────
    wifi_string = f"WIFI:T:WPA;S:{ssid};P:{password};H:false;;"
    qr_px  = int(3.2 * DPI)
    qr_img = make_qr_image(wifi_string, qr_px)

    border = int(0.07 * DPI)
    shadow = int(0.04 * DPI)
    qx = (W - qr_px - 2 * border) // 2

    draw.rectangle(                                              # drop shadow
        [(qx+shadow, cy+shadow),
         (qx+qr_px+2*border+shadow, cy+qr_px+2*border+shadow)],
        fill=full_palette["secondary"],
    )
    draw.rectangle(                                              # blue border
        [(qx, cy), (qx+qr_px+2*border, cy+qr_px+2*border)],
        fill=full_palette["primary"],
    )
    draw.rectangle(                                              # background inset
        [(qx+border, cy+border), (qx+border+qr_px, cy+border+qr_px)],
        fill=bg_color,
    )
    img.paste(qr_img, (qx+border, cy+border))
    cy += qr_px + 2*border + int(0.15 * DPI)

    # ── Footer ────────────────────────────────────────────────────────────────
    footer = "Point your camera at the code above"
    fb = draw.textbbox((0, 0), footer, font=fnt_sub)
    draw.text(((W-(fb[2]-fb[0]))//2, cy+int(0.05*DPI)), footer, font=fnt_sub, fill=full_palette["GRAY_MED"])
    cy += (fb[3]-fb[1]) + int(0.20 * DPI)

    # ── Divider ───────────────────────────────────────────────────────────────
    draw.rectangle([(pad, cy), (W-pad, cy+3)], fill=full_palette["GRAY_LIGHT"])
    cy += int(0.12 * DPI)

    # ── Info rows ─────────────────────────────────────────────────────────────
    rows = [
        ("Network",  ssid,       True),
        ("Password", password,   False),
    ]
    for label, value, highlight in rows:
        lb = draw.textbbox((0, 0), label.upper(), font=fnt_label)
        vb = draw.textbbox((0, 0), value,          font=fnt_value)
        lh, vh = lb[3]-lb[1], vb[3]-vb[1]
        row_h  = max(lh, vh)

        draw.text((pad, cy+(row_h-lh)//2),
                  label.upper(), font=fnt_label, fill=full_palette["GRAY_MED"])
        draw.text((W-pad-(vb[2]-vb[0]), cy+(row_h-vh)//2),
                  value, font=fnt_value,
                  fill=full_palette["BLACK"] if highlight else full_palette["GRAY_MED"])

        cy += row_h + int(0.08 * DPI)
        draw.rectangle([(pad, cy), (W-pad, cy+2)], fill=full_palette["GRAY_LIGHT"])
        cy += int(0.08 * DPI)


    # ── Save ──────────────────────────────────────────────────────────────────
    img.save(output_path, dpi=(DPI, DPI))
    print(f"Saved: {output_path}  ({W}x{H} px @ {DPI} dpi)")


def custom_colors():
    global current_palette
    for key in ["primary", "secondary"]:
        color = colorchooser.askcolor(title=f"Choose {key.title()}", color=tuple(current_palette.get(key, presets["Default"][key])))[1]
        if color:
            current_palette[key] = tuple(int(color[i:i+2], 16) for i in (1,3,5))  # hex to rgb
    preset_var.set("Custom")
    update_preview()

def update_preview():
    try:
        temp_path = "temp_preview.png"
        generate_card(network_name_var.get(), ssid_var.get(), password_var.get(), temp_path, current_palette)
        img = Image.open(temp_path)
        preview_x = 400
        preview_y = preview_x * 1.5
        img.thumbnail((preview_x, preview_y))  # scale down for preview
        photo = ImageTk.PhotoImage(img)
        preview_label.config(image=photo)
        preview_label.image = photo  # keep reference
    except Exception as e:
        print(e)

def launch_gui():
    global network_name_var, ssid_var, password_var, output_var, preset_var, current_palette, preview_label, filename_auto
    root = tk.Tk()
    root.title("WiFi QR Card Generator")

    # Variables
    network_name_var = tk.StringVar(value="Home")
    ssid_var = tk.StringVar(value="MyNetwork")
    password_var = tk.StringVar(value="MyPass123")
    output_var = tk.StringVar(value="Home_qr.png")
    preset_var = tk.StringVar(value="Default")
    current_palette = presets["Default"].copy()
    filename_auto = True

    # Widgets
    ttk.Label(root, text="Network Name:").grid(row=0, column=0, sticky="w")
    ttk.Entry(root, textvariable=network_name_var).grid(row=0, column=1, sticky="ew")
    ttk.Label(root, text="SSID:").grid(row=1, column=0, sticky="w")
    ttk.Entry(root, textvariable=ssid_var).grid(row=1, column=1, sticky="ew")
    ttk.Label(root, text="Password:").grid(row=2, column=0, sticky="w")
    ttk.Entry(root, textvariable=password_var).grid(row=2, column=1, sticky="ew")
    ttk.Label(root, text="Output:").grid(row=3, column=0, sticky="w")
    ttk.Entry(root, textvariable=output_var).grid(row=3, column=1, sticky="ew")
    ttk.Button(root, text="Browse", command=lambda: output_var.set(filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")]))).grid(row=3, column=2)
    ttk.Label(root, text="Preset:").grid(row=4, column=0, sticky="w")
    preset_cb = ttk.Combobox(root, textvariable=preset_var, values=list(presets.keys()), state="readonly")
    preset_cb.grid(row=4, column=1, sticky="ew")
    def on_preset_change(*args):
        p = preset_var.get()
        if p != "Custom":
            current_palette.update(presets[p])
        update_preview()
    preset_var.trace_add("write", on_preset_change)
    ttk.Button(root, text="Custom Colors", command=custom_colors).grid(row=4, column=2)

    # Preview
    preview_label = ttk.Label(root)
    preview_label.grid(row=5, column=0, columnspan=3)

    # Bind filename auto-update (no preview on keystroke)
    def on_network_name_change(*args):
        global filename_auto
        if filename_auto:
            name = network_name_var.get().replace(" ", "_")
            output_var.set(f"{name}_qr.png")
    network_name_var.trace_add("write", on_network_name_change)

    def on_output_change(*args):
        global filename_auto
        expected = f"{network_name_var.get().replace(' ', '_')}_qr.png"
        if output_var.get() != expected:
            filename_auto = False
    output_var.trace_add("write", on_output_change)

    # Initial preview
    update_preview()

    # Buttons
    ttk.Button(root, text="Preview", command=update_preview).grid(row=6, column=0, sticky="ew")
    ttk.Button(root, text="Generate", command=lambda: generate_card(network_name_var.get(), ssid_var.get(), password_var.get(), output_var.get(), current_palette)).grid(row=6, column=1, columnspan=2, sticky="ew")

    root.mainloop()


# ── CLI ───────────────────────────────────────────────────────────────────────
def cli_main():
    parser = argparse.ArgumentParser(
        description="Generate a print-ready 4x6 WiFi QR card (PNG)."
    )
    parser.add_argument("--name",    help='Network name, e.g. "Guest" or "Home"')
    parser.add_argument("--ssid",     help="WiFi network name (SSID)")
    parser.add_argument("--password", help="WiFi password")
    parser.add_argument("--output",   default="wifi_qr.png",
                        help="Output filename (default: wifi_qr.png)")
    args = parser.parse_args()

    network_name    = args.name    or input("Network name (e.g. Guest, Home): ").strip()
    ssid     = args.ssid     or input("SSID: ").strip()
    password = args.password or input("Password: ").strip()

    if not network_name or not ssid or not password:
        sys.exit("Error: network name, SSID, and password are all required.")

    generate_card(network_name, ssid, password, args.output)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli_main()
    else:
        launch_gui()
