# Decisions log

One line per decision: what I chose and why. Newest at the bottom of each section.
Labels: **Verified** = backed by a source in `research/sources.md`. **Estimate** = my best guess.

## Setup
- D001: Python engine lives in `engine/` with its own `.venv` (not committed). Reason: keeps installs inside this folder as required.
- D002: Renders use three.js in headless Chromium (Playwright). Reason: Blender is not installed, and using the same renderer as the 3D app keeps renders and app identical.
