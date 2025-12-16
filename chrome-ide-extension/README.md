# Selenium IDE Lite (Chrome Extension)

A lightweight, manifest v3 Chrome extension that records clicks, form interactions, and submissions, and lets you save and replay the captured steps—similar to Selenium IDE basics.

## Features
- Start and stop recording from the popup.
- Save recordings by name and load them later.
- Replay the latest or saved recordings directly on the active tab.

## File structure
- `manifest.json` — extension definition and permissions.
- `background.js` — service worker handling storage and cross-script messaging.
- `content.js` — content script that records actions and replays steps on the page.
- `popup.html`, `popup.css`, `popup.js` — popup UI and controls.

## Developing locally
1. Open Chrome and navigate to `chrome://extensions`.
2. Enable **Developer mode**.
3. Choose **Load unpacked** and select the `chrome-ide-extension` directory.
4. Open any page, click the extension icon, and use the popup to record, save, and replay steps.

Tips:
- For best selectors, interact with elements that have unique IDs or stable classes.
- Playback dispatches `click`, `input`, `change`, and `submit` events with small delays between steps.
