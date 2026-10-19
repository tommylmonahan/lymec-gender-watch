# LYMEC Gender Watch

A small, private, browser-based app for tracking who takes the floor at a LYMEC Congress, including first-time delegates.

The interface uses LYMEC's blue-and-pink visual language and a voice-wave motif inspired by the organisation's public identity.

## Run it

Open `index.html` in a modern browser. No installation, server, account, or internet connection is needed.

## Features

- One-click entries for men and women
- Optional first-time delegate marker
- Live totals, first-time totals, and gender balance
- Recent-entry log and one-click undo
- CSV export
- Automatic browser-local saving
- Light and dark themes
- Keyboard shortcuts: `M`, `W`, and `F`

## Data and privacy

All entries are stored in the browser's `localStorage`. Nothing is sent over the internet. Data remains tied to the browser and device used, unless it is exported as CSV.

## Notes

- The first-time checkbox stays in its chosen state so consecutive first-time interventions can be logged quickly.
- “Reset session” permanently clears the saved data after confirmation.
