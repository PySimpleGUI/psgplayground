"""
screenshot_utils.py - Shared helper for NON-INTERACTIVE PySimpleGUI
screenshot regression tests.

    import PySimpleGUI as sg
    from screenshot_utils import snap_window

    window = sg.Window('My Test', layout, finalize=True)
    snap_window(window, 'output/screenshots/my_test.png')
    window.close()

LABELED OUTPUT FOLDERS:
Every SNAP_*.py script passes a hardcoded path like
'output/screenshots/SNAP_01_text_all_params.png' to snap_window(). To
support saving different runs to different folders (e.g. one folder per
PySimpleGUI version you're testing) WITHOUT editing every SNAP_*.py
script, snap_window() checks the environment variable SNAP_OUTPUT_DIR.

If SNAP_OUTPUT_DIR is set, the DIRECTORY portion of whatever path a
script passes in is IGNORED and replaced with SNAP_OUTPUT_DIR - only
the filename itself (e.g. "SNAP_01_text_all_params.png") is kept. This
is what run_snapshots_gui.py's "Label" field uses under the hood: it
launches each SNAP_*.py script with SNAP_OUTPUT_DIR set to something
like "output/screenshots_6.3" instead of the default "output/screenshots".

If SNAP_OUTPUT_DIR is not set, behavior is unchanged from before -
scripts save to whatever path they hardcoded (normally
output/screenshots/...).

PLATFORM NOTES:
- Requires Pillow: pip install Pillow
- ImageGrab.grab() works natively on Windows/macOS. On Linux needs
  Pillow >= 8 and a running X11 session (not pure Wayland).
- Don't move the mouse or cover the window while a suite runs.
- Increase settle_ms if screenshots show partially-rendered widgets.
"""
import os
import time


def snap_window(window, filename, settle_ms=350):
    """
    Renders the window, waits briefly, and captures a screenshot of the
    window's bounding box to `filename`. Does NOT close the window -
    call window.close() yourself after calling this.

    If the environment variable SNAP_OUTPUT_DIR is set, the directory
    portion of `filename` is replaced with SNAP_OUTPUT_DIR (only the
    basename of `filename` is kept) - this is how labeled/versioned
    screenshot runs are supported without editing every test script.

    :param window: A PySimpleGUI Window (finalized or about to be)
    :param filename: Full path (including .png) to save the screenshot to
    :param settle_ms: Milliseconds to wait after rendering before capture
    :return: True if saved successfully, False otherwise
    """
    # INTERACTIVE MODE: if SNAP_INTERACTIVE is set (to anything non-empty),
    # skip the screenshot entirely and leave the window open for manual
    # inspection until the user closes it. Lets any SNAP_*.py script be
    # viewed live without editing it. Used by the GUI's "View" button.
    if os.environ.get('SNAP_INTERACTIVE'):
        print(f'INTERACTIVE MODE - no screenshot. Close the window to finish. ({os.path.basename(filename)})')
        while True:
            event, _ = window.read()
            if event == '__TIMEOUT__':
                continue
            break   # window closed (or any event - these tests have no buttons)
        return True

    try:
        from PIL import ImageGrab
    except ImportError:
        print('ERROR: Pillow is required for screenshots. Run: pip install Pillow')
        return False

    override_dir = os.environ.get('SNAP_OUTPUT_DIR')
    if override_dir:
        filename = os.path.join(override_dir, os.path.basename(filename))

    try:
        window.read(timeout=1)
        window.refresh()
        time.sleep(settle_ms / 1000.0)

        widget = window.TKroot
        widget.update_idletasks()
        x = widget.winfo_rootx()
        y = widget.winfo_rooty()
        w = widget.winfo_width()
        h = widget.winfo_height()

        os.makedirs(os.path.dirname(filename) or '.', exist_ok=True)
        img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        img.save(filename)
        print(f'Saved screenshot: {filename}  ({w}x{h})')
        return True
    except Exception as e:
        print(f'ERROR capturing screenshot for {filename}: {e}')
        return False
