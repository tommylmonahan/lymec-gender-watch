# LYMEC Gender Watch

A small, private, local app for tracking who takes the floor at a LYMEC Congress, including first-time delegates.

The interface uses LYMEC's blue-and-pink visual language and a voice-wave motif inspired by the organisation's public identity.
The bundled header logo is the official logo served by LYMEC's public website.

## Run it

Double-click `start.bat`. A small Python server starts on `http://127.0.0.1:8765` and opens the app in your browser.

Keep the console window open while using the tracker. Close it, or press `Ctrl+C`, when the session is finished. No internet connection, account, or third-party Python package is needed.

## Features

- One-click entries for men, women, and other delegates
- Optional first-time delegate marker
- Optional per-record comment
- Live totals, first-time totals, and gender balance
- Recent-entry log and one-click undo
- JSON export
- Automatic browser and disk saving
- Live JSON backup and archived sessions
- Light and dark themes
- Keyboard shortcuts: `M`, `W`, `O`, and `F`

## Data and privacy

Every change is stored in both the browser and these local files:

- `data/records.json` - the live backup and recovery source used when the app starts
- `data/archive/` - timestamped JSON copies of sessions that were reset

The server listens only on `127.0.0.1`, so it is accessible only from this computer. Nothing is sent over the internet.

## Notes

- The first-time checkbox and comment field clear after each recorded intervention.
- Resetting creates a timestamped JSON archive before starting a blank session.
- Opening `index.html` directly still works, but runs in browser-only mode without the automatic disk backup.
