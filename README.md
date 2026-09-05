# D30 Printer - Windows print server 

Print labels on a Phomemo D30 thermal label printer from Windows, over its
Bluetooth SPP (COM port) connection — from the command line, or from any
website via a small local print server.

The print protocol was reverse-engineered by the
[phomemo_d30](https://github.com/polskafan/phomemo_d30) project (by
sniffing the "Print Master" Android app's Bluetooth traffic) and is
reimplemented here in pure Python — no ImageMagick/Wand dependency, just
`pyserial`, `Pillow`, and `Flask`.

## Quick start (no coding experience needed)

1. **Install Python** — download and run the installer from
   [python.org/downloads](https://www.python.org/downloads/). On the first
   install screen, tick **"Add python.exe to PATH"** before clicking
   Install.
2. **Download this project** — on this page, click the green **Code**
   button, then **Download ZIP**, and extract it somewhere handy (e.g.
   your Desktop).
3. **Pair the D30** in Windows Bluetooth settings, if you haven't already
   (Settings > Bluetooth & devices > Add device).
4. **Run setup** — double-click `setup.bat` in the extracted folder. This
   installs everything needed and only has to be done once.
5. **Start printing** — double-click `start_server.bat`. A window opens
   showing the server running, and your browser opens a page where you can
   type a label and click Print.

Leave that window open while printing; closing it stops the server. If a
label doesn't print, see [Troubleshooting](#troubleshooting) below — the
most common issue is Windows not having actually connected the Bluetooth
link yet (shows as "Driver is unavailable" in Bluetooth settings).

The rest of this README covers the command-line tools and the HTTP API in
more detail, for anyone who wants to script it or wire it into their own
website.

## Setup (command line)

1. Pair the D30 in Windows Bluetooth settings, if you haven't already.
2. Find its COM port: **Settings > Bluetooth & devices > Devices >
   [your D30] > More Bluetooth options > COM Ports** tab, or check
   **Device Manager > Ports (COM & LPT)**. Use the **Outgoing** port.
   (You generally won't need this — see auto-detection below.)
3. Install dependencies (Python 3.9+):

   ```powershell
   python -m venv venv
   venv\Scripts\pip install -r requirements.txt
   ```

## Usage

`--port` is optional — if you omit it, the script scans Windows' listed
COM ports for one that accepts data and uses it automatically:

```powershell
venv\Scripts\python print_text.py "Hello World!"
```

Or specify it directly if you already know it (faster, and required if more
than one port responds):

```powershell
venv\Scripts\python print_text.py "Hello World!" --port COM4
```

Multi-line label (use `\n` literally, it's converted to a real line break):

```powershell
venv\Scripts\python print_text.py "First line\nSecond line" --port COM5
```

Custom font:

```powershell
venv\Scripts\python print_text.py --font C:\Windows\Fonts\comic.ttf "Hi" --port COM5
```

Smaller label stock — the printhead is a fixed 96px/12mm wide no matter
what, so only `--length` (the feed-direction size, in mm) needs setting;
default is 40mm (Phomemo's standard label):

```powershell
venv\Scripts\python print_text.py --length 30 "Hi" --port COM4
```

Multiple copies — for die-cut labels on a continuous roll there's no cut
command, so a short pause (`--pause-ms`, default 250) runs between copies
to let the printer settle and advance to the next label:

```powershell
venv\Scripts\python print_text.py --count 10 "Hi" --port COM4
```

### Batch / best-before labels

`print_batch_label.py` prints a ready-made two-line label — `Batch <n>` on
one line, `Best Before: <date>` on the other — sized for 14x30mm stock by
default:

```powershell
venv\Scripts\python print_batch_label.py --batch 123456 --best-before 04-09-26
```

`--best-before` is printed exactly as given (no date parsing/validation),
so pass it already formatted the way you want it on the label. `--length`,
`--font`, `--count`, and `--pause-ms` all work the same as `print_text.py`
if you need a different
label size.

## Web API (for printing from a website)

`server.py` runs a small local HTTP server with a single print endpoint
and a docs/usage page. Double-click `start_server.bat`, or run it directly:

```powershell
venv\Scripts\python server.py
```

Then open `http://localhost:8787/` for the full docs — parameters,
examples, and a live test form. In short: `GET`, `POST`, or `PUT` to
`/api/print` with `mode` (`text` or `batch`) plus that mode's fields
(`text`, or `batch` + `best_before`), sent as a JSON body or as query
string / form fields, e.g.:

```js
fetch("http://localhost:8787/api/print", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ mode: "batch", batch: "123456", best_before: "04-09-26" }),
})
```

It binds to `127.0.0.1` by default (this machine only, matches "runs on
localhost"). There's no authentication, so only pass `--host 0.0.0.0` if
you understand anyone on the network could then trigger a print.
COM-port auto-detection happens per request, same as the CLI scripts — a
request fails with a clear JSON error (not a hang) if nothing responds or
more than one port does.

## Troubleshooting

- **Script just hangs / freezes**: `print_text.py` now sets a 5s write
  timeout, so it should fail with a clear error instead. If it still hangs,
  run `debug_port.py` (below) for a step-by-step trace.
- **"Driver is unavailable" next to D30 in Windows Bluetooth devices**: this
  means Windows paired the device but never bonded it as a serial (SPP)
  device, so the COM port exists but nothing actually connects when you
  open it — this is very likely the cause of a freeze/timeout. Try removing
  the device and re-pairing; make sure it shows **Connected**, not just
  **Paired**, before printing.
- **Two COM ports show up (e.g. COM3 & COM4)**: Windows creates an
  "Outgoing" and an "Incoming" port for each Bluetooth SPP device — check
  Device Manager or Bluetooth settings > More Bluetooth options > COM Ports
  tab to see which is which, and use the **Outgoing** one.
- **Garbled or blank print**: the D30 sometimes needs the port closed and
  reopened between jobs — the script does this automatically per run.
- Label dots are physically 96px across; the script handles resizing and
  rotation, so any text length works as long as it fits after auto-shrinking
  the font.

### debug_port.py

A standalone connectivity probe — opens a COM port, sends the printer's
init sequence one packet at a time, and logs (with timestamps) whether each
write succeeded and whether anything came back:

```powershell
venv\Scripts\python debug_port.py --port COM3
```

Things to look for in the output:

- **A write times out** ("WRITE TIMED OUT") → the OS accepted the port
  handle but the Bluetooth link itself isn't actually connected. This is a
  Windows/pairing problem, not the script — see the "Driver is unavailable"
  note above.
- **Everything sends successfully, nothing ever comes back** → expected.
  The D30 protocol is one-way (fire-and-forget, no acknowledgement from the
  printer), so no reply doesn't mean anything is wrong — it confirms the
  COM port and pairing work, but not that a label physically printed.
- **Data comes back** → unexpected for this protocol; worth inspecting the
  hex the printer sent.

Run it against both COM ports if you're not sure which is outgoing.

### find_port.py

Faster than `debug_port.py` when you just want an answer, not a trace.
Brute-forces a numeric range (COM1..COM8 by default) or, with `--listed`,
probes only the ports Windows currently enumerates:

```powershell
venv\Scripts\python find_port.py
venv\Scripts\python find_port.py --range 1-16
venv\Scripts\python find_port.py --listed
```

Same caveat as everywhere else: the D30 never replies, so "accepted data"
means the OS took the write without timing out, not that it's confirmed to
be a D30 specifically. If multiple ports accept data, that's normal (an
Outgoing + Incoming port pair per Bluetooth device) — pick the Outgoing
one, or just try each with `print_text.py`.

## Project layout

- `d30/protocol.py` — raw byte protocol (init sequence, raster header, bit
  packing).
- `d30/image.py` — renders text into the 1-bit image the printer expects,
  at whatever length (`--length`, in mm) the label needs.
- `d30/printer.py` — `D30Printer`, the serial connection wrapper.
- `d30/discovery.py` — COM port auto-detection.
- `d30/cli.py` — `--port` resolution for the CLI scripts (prints + exits on failure).
- `d30/jobs.py` — shared "render + resolve port + print N copies" logic,
  used by both the CLI scripts and the API server.
- `d30/docs_page.py` — the HTML for the API's docs page.
- `print_text.py` — CLI entry point for free-form text labels.
- `print_batch_label.py` — CLI entry point for batch/best-before labels.
- `server.py` — local HTTP API + docs page, for printing from a website.
- `find_port.py`, `debug_port.py` — connectivity diagnostics.
- `setup.bat`, `start_server.bat` — double-click setup/run for Windows
  users who don't want a terminal.

## Possible next steps

- Print arbitrary images (barcodes, QR codes, logos) — `image_to_rows()`
  already accepts any 96px-wide 1-bit image, so this is mostly a new
  `print_image.py` CLI (and an `image` mode on the API), no protocol work
  needed.
- Package as an installable CLI (`pip install -e .`).
- Auth on the API server, if it ever needs to listen on more than
  `127.0.0.1`.
