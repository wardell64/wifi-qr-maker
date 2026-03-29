# AGENTS.md

## Project Overview

**wifi-qr-maker** is a Python utility that generates print-ready 4x6" WiFi QR code cards (PNG @ 600 DPI). The project has two operational modes:
- **GUI mode**: Interactive Tkinter interface for live preview and color customization
- **CLI mode**: Headless generation with arguments or interactive prompts

Single-file architecture: `/wifi_qr_generator.py` contains all logic (360 lines).

---

## Core Architecture

### Entry Point Logic (`if __name__ == "__main__"`)
- **No CLI args** → launches `launch_gui()` (Tkinter interface)
- **With CLI args** → calls `cli_main()` (argparse-driven, prompts for missing values)

### Three Functional Layers

1. **QR Generation** (`make_qr_image()`)
   - Uses `reportlab.graphics.barcode.qr.QrCodeWidget` (NOT renderPM/Cairo—avoids native deps)
   - Renders QR matrix pixel-by-pixel onto PIL Image
   - Input: WiFi auth string in format `WIFI:T:WPA;S:{ssid};P:{password};H:false;;`
   - Output: PIL Image, square, resized with `Image.NEAREST` (no blur)

2. **Card Layout** (`generate_card()`)
   - Fixed 4x6" @ 600 DPI = 1200×1800 px canvas
   - **Layout order** (top to bottom): accent bar → tag pill → network name → subtitle → QR code (with border/shadow) → divider → info rows → footer
   - **Font system**: Discovers fonts via platform-specific paths (see `BOLD_FONTS`/`REG_FONTS` lists), falls back gracefully
   - **Dynamic text color**: Brightness calculation on secondary color determines if text on secondary should be black/white
   - **Saves with DPI metadata** via `img.save(..., dpi=(600, 600))`

3. **GUI State Management**
   - Uses global `current_palette` dict to track active color scheme
   - Uses `filename_auto` flag to detect manual filename changes (disables auto-generation)
   - Live preview via `temp_preview.png` (scaled to 300×450 for UI)
   - All field changes trigger `on_change()` which calls `update_preview()`

---

## Color Presets System

Located in external `presets.json` file. Each preset defines:
```json
"Preset Name": {
    "primary": [R, G, B],       # UI accents, borders, accent bar
    "secondary": [R, G, B],     # Tag pill background, QR drop shadow
    "background": [R, G, B]     # Card background (optional, defaults to white)
}
```

The `_load_presets()` function loads the JSON and converts lists to tuples for PIL compatibility. Missing `background` fields default to white to maintain backward compatibility.

**Currently 7 presets**: Default, University of Oregon, Oregon State University, Portland State University, University of Washington, Washington State University, and Cornell University.

**Adding custom presets**: 
- Edit `presets.json` directly with RGB values (as lists)
- All three fields are optional; unspecified values default to white
- Or use GUI "Custom Colors" button (launches `colorchooser.askcolor()` and auto-adds to "Custom" preset)

---

## Cross-Platform Font Discovery

The project prioritizes system fonts without hard dependencies:

1. **Bold fonts** tried in order: Google Fonts Poppins-Bold (Linux) → DejaVu (Linux fallback) → Arial Bold (macOS) → Windows Arial Bold
2. **Regular fonts** similar chain with Regular/Medium weights
3. **Fallback**: If no bold found, exits with clear error message

**Platform detection**: Pure path checking (`Path(p).exists()`), no OS imports needed. Enables Windows/macOS/Linux without platform-specific code.

---

## Input/Output

### CLI Arguments (argparse)
```bash
--name STRING         # Display name on card (e.g., "Guest", "Home")
--ssid STRING         # WiFi network SSID
--password STRING     # WiFi password
--output FILENAME     # PNG output file (default: wifi_qr.png)
```

Missing args are prompted interactively. Validation requires all three.

### Output Format
- PNG @ 600 DPI (printable quality)
- Size: 1200×1800 px (4×6 inches exact)
- DPI metadata embedded in PNG

---

## Dependencies

**Required**:
- `pillow` – Image generation and rendering
- `reportlab` – QR code matrix generation (no renderPM backend needed)
- `tkinter` – GUI (built-in on most Python installations)

**Install**: `pip install pillow reportlab`

**Note**: No native C extensions or Cairo required—pure Python fallback for QR rendering.

---

## Key Patterns & Conventions

### Dynamic Layout with DPI Units
All layout calculations use `int(multiplier * DPI)` syntax. This keeps coordinates readable:
```python
font_size = int(0.130 * DPI)   # 78 pt @ 600 DPI
padding = int(0.28 * DPI)      # 168 px @ 600 DPI
```

### Cumulative Y-Position (`cy` variable)
Card sections stack vertically; `cy` tracks the current Y position and increments after each section. Simplifies layout math.

### Brightness-Based Text Color
```python
brightness = (r * 299 + g * 587 + b * 114) / 1000
text_on_primary = BLACK if brightness > 128 else WHITE
```
Ensures tag text readable on any secondary color background.

### Global State for GUI
`current_palette`, `filename_auto`, and field variables (`network_name_var`, etc.) stored as globals; accessed by event handlers. Simple but functional for single-form UI.

### WiFi QR Format String
Standard format: `WIFI:T:WPA;S:{ssid};P:{password};H:false;;`
- `T:WPA` – hardcoded security (no WEP support)
- `H:false` – network is broadcast (not hidden)
- Trailing `;;` required by spec

---

## Testing & Validation

**Manual testing**:
1. CLI: `python wifi_qr_generator.py --name "Test" --ssid "TestNet" --password "pass123"`
2. GUI: `python wifi_qr_generator.py` → verify preview updates on field changes
3. Output: Open PNG in image viewer or print preview; verify 4×6" dimensions and QR scannability

**Common issues**:
- Font not found → Install system fonts or add custom paths to `BOLD_FONTS`/`REG_FONTS`
- QR too small to scan → Verify `qr_px = int(2.80 * DPI)` is sufficient (1680 px at 600 DPI)
- Preview stalls → Check `temp_preview.png` isn't locked by another process

---

## Extending the Project

### Add a New Preset
Edit `presets` dict, add new entry with `"primary"` and `"secondary"` RGB tuples.

### Customize Card Layout
Modify `generate_card()` function:
- Change `W`, `H` for different print sizes (update layout proportions accordingly)
- Adjust section order by moving `cy +=` and `draw.rectangle()`/`draw.text()` calls
- Add new rows: append tuple to `rows` list for info display

### Add Font Customization to GUI
In `launch_gui()`, add font selection ComboBox, store selection in global, pass to `generate_card()`.

### Support Additional WiFi Modes
Update WiFi string format in `make_qr_image()` call. Current hardcodes WPA; to support WEP or Open: parameterize `T:` field and security label in info rows.

