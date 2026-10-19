# LYMEC Gender Watch

A small, private, local app for tracking who takes the floor at a LYMEC Congress, including first-time delegates.

The interface uses LYMEC's blue-and-pink visual language and a voice-wave motif inspired by the organisation's public identity.
The bundled header logo is the official logo served by LYMEC's public website.

## Run it

Double-click `start.bat`. A small Python server starts on `http://127.0.0.1:8765` and opens the app in your browser.

Keep the console window open while using the tracker. Close it, or press `Ctrl+C`, when the session is finished. No internet connection, account, or third-party Python package is needed.

## Features

- One-click entries for men, women, and non-binary delegates
- Optional first-time delegate marker
- Live totals, first-time totals, and gender balance
- Recent-entry log and one-click undo
- CSV export
- Automatic browser and disk saving
- Live Excel-compatible CSV backup
- JSON recovery copy and archived sessions
- Light and dark themes
- Keyboard shortcuts: `M`, `W`, `N`, and `F`

## Data and privacy

Every change is stored in both the browser and these local files:

- `data/current-session.csv` - the live backup, ready to open in Excel
- `data/records.json` - the recovery source used when the app starts
- `data/archive/` - timestamped copies of sessions that were reset

The server listens only on `127.0.0.1`, so it is accessible only from this computer. Nothing is sent over the internet.

## Notes

- The first-time checkbox stays in its chosen state so consecutive first-time interventions can be logged quickly.
- Resetting creates timestamped CSV and JSON archives before starting a blank session.
- Avoid keeping `current-session.csv` open in Excel while recording. Excel may lock the file; if that happens, the app displays a warning and retains the records in the browser and JSON recovery file.
- Opening `index.html` directly still works, but runs in browser-only mode without the automatic disk backup.
