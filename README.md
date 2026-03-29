# wifi-qr-maker

Generate print-ready 4×6" WiFi QR code cards (PNG @ 600 DPI).

## Overview

**wifi-qr-maker** creates branded WiFi QR cards perfect for printing on standard index cards. Each card includes:
- A large, scannable QR code
- Network name, SSID, and security info
- Customizable color presets (6 university themes included)
- Professional layout with accent colors and shadows

Use it to:
- Print guest WiFi instructions at your office or venue
- Create branded WiFi cards for university networks
- Generate custom cards with your own colors

## Installation

```bash
pip install pillow reportlab
```

Then download or clone this repository.

## Usage

### GUI Mode (Interactive)

```bash
python wifi_qr_generator.py
```

Opens a Tkinter window where you can:
- Enter network name, SSID, and password
- Preview changes in real-time
- Select from 6 color presets or create custom colors
- Browse for output filename
- Generate and save

**Screenshot:**
![GUI Preview Placeholder]

## CLI Mode (Command Line)

Generate directly without opening the GUI:

```bash
# With all arguments
python wifi_qr_generator.py --name "Guest" --ssid "MyNetwork" --password "MyPass123!" --output guest.png

# With interactive prompts (provide SSID/password when asked)
python wifi_qr_generator.py --name "Guest"

# Minimal (all prompts)
python wifi_qr_generator.py
```

**Arguments:**
- `--name STRING` – Display name on card (e.g., "Guest", "Home")
- `--ssid STRING` – WiFi network SSID
- `--password STRING` – WiFi password
- `--output FILENAME` – Output PNG file (default: `wifi_qr.png`)

## Features

- ✅ **Print-ready**: 1200×1800 px PNG @ 600 DPI (fits 4×6" cards)
- ✅ **No native dependencies**: Pure Python QR rendering (reportlab), no Cairo/RenderPM needed
- ✅ **Cross-platform**: Works on Windows, macOS, Linux
- ✅ **Dual mode**: GUI for interactive use, CLI for automation
- ✅ **Presets**: 6 university color schemes (UO, OSU, PSU, UW, WSU, Cornell) + custom colors
- ✅ **Live preview**: See changes instantly in GUI mode
- ✅ **Auto-naming**: Output filename auto-updates based on network name in GUI

## Color Presets

Presets are stored in `presets.json` and include:
- Default (blue/light blue)
- University of Oregon (green/gold)
- Oregon State University (orange/black)
- Portland State University (maroon/gray)
- University of Washington (purple/tan)
- Washington State University (maroon/gray)
- Cornell University (carnelian/dark gray)

Each preset defines three colors:
- **Primary** – accent bar, QR code border, tag pill text
- **Secondary** – tag pill background, QR code shadow
- **Background** – card background (defaults to white)

**Customize presets**:
- Edit `presets.json` directly to modify colors or add new presets
- Use "Custom Colors" in the GUI to define colors interactively
- Pro tip: When secondary color is light (e.g., white), set a darker `background` color to ensure the tag pill remains visible

## Sample Output

**Place a screenshot of a generated card here:**

```
[Insert 4×6" WiFi QR card image here]
- Shows accent bar at top
- "WI-FI NETWORK QR CODE" tag pill
- Network name (e.g., "Guest")
- "Scan to connect instantly" subtitle
- Large QR code with colored border and shadow
- Divider line
- Info rows: Network / Password / Security
- Footer: "Point your camera at the code above"
```

Or describe what to expect: The output is a 4×6" card with a scannable QR code centered on the page, surrounded by network info and branding. Print at actual size (no scaling) for best results.

## Requirements

- Python 3.6+
- `pillow` – Image generation and rendering
- `reportlab` – QR code matrix generation
- `tkinter` – GUI (built-in on most Python installations)

## Troubleshooting

**Font not found error:**
- Install system fonts (Google Fonts Poppins or Arial)
- On macOS: Check `/Library/Fonts/Arial.ttf` exists
- On Linux: Run `sudo apt install fonts-open-sans`
- On Windows: Arial should be pre-installed

**QR code too small to scan:**
- Verify your printer's DPI setting matches 600 DPI
- Try scanning from different angles
- Ensure contrast isn't reduced by print settings

**Preview stalls in GUI:**
- Close any other program that might be locking `temp_preview.png`
- Restart the application

## License

See LICENSE file for details.

