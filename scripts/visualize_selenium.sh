#!/usr/bin/env bash
# Lightweight helper to run Selenium tests on a virtual display and expose it via VNC.
# Usage: sudo apt install -y xvfb x11vnc fluxbox || install equivalents
# Then run: ./scripts/visualize_selenium.sh

set -euo pipefail

PORT=5901
DISPLAY_NUM=99
DISPLAY=:$DISPLAY_NUM
XVFB_PID=""
WM_PID=""
X11VNC_PID=""

check_bin(){
  command -v "$1" >/dev/null 2>&1 || return 1
}

echo "Preparing visual environment (DISPLAY=$DISPLAY)"

if ! check_bin Xvfb && ! check_bin xvfb-run; then
  echo "Neither Xvfb nor xvfb-run found. Install with: sudo apt install xvfb"
  exit 1
fi

if ! check_bin x11vnc; then
  echo "x11vnc not found. Install with: sudo apt install x11vnc"
  echo "Without x11vnc you won't be able to connect via VNC, but xvfb-run can still create a virtual display."
fi

if ! check_bin fluxbox && ! check_bin openbox; then
  echo "No lightweight window manager found (fluxbox/openbox). This is optional but improves visuals."
fi

cleanup(){
  echo "Cleaning up..."
  if [ -n "$X11VNC_PID" ]; then kill "$X11VNC_PID" 2>/dev/null || true; fi
  if [ -n "$WM_PID" ]; then kill "$WM_PID" 2>/dev/null || true; fi
  if [ -n "$XVFB_PID" ]; then kill "$XVFB_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

if check_bin Xvfb; then
  echo "Starting Xvfb on $DISPLAY"
  Xvfb $DISPLAY -screen 0 1920x1080x24 &
  XVFB_PID=$!
  sleep 0.5
fi

export DISPLAY

# Start window manager if available
if check_bin fluxbox; then
  fluxbox &
  WM_PID=$!
elif check_bin openbox; then
  openbox &
  WM_PID=$!
fi

sleep 0.5

if check_bin x11vnc; then
  echo "Starting x11vnc on port $PORT (connect with VNC client to localhost:$PORT)"
  x11vnc -display $DISPLAY -nopw -forever -shared -rfbport $PORT &
  X11VNC_PID=$!
  sleep 0.5
fi

echo "Environment ready. You can connect with a VNC client to localhost:$PORT (or :$DISPLAY_NUM if tunneled)."
echo "Running Selenium tests with visible browser (SHOW_BROWSER=1)."

# Run tests against homologation by default; allow overriding via env or args
TEST_CMD="APP_ENV=${APP_ENV:-hom} CHECK_BUTTONS=1 SHOW_BROWSER=1 ./run_tests.sh --selenium"
echo "Executing: $TEST_CMD"
bash -c "$TEST_CMD"

echo "Tests finished. Screenshots and reports are in the repo root. Keep the VNC server running to inspect the display, or press Ctrl-C to stop and cleanup."
