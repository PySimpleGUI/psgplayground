#!/usr/bin/env python3
"""
app_template.pyw - a one-file PySimpleGUI app with the Playground conventions already in place.  Copy it, rename it, fill in the middle.

    What's here:  K_ key constants, VERSION + change log, right-click Edit Me / Version / Exit, Esc to close,
                  Up/Down/PgUp/PgDn/Home/End on the scrollable area, settings that persist, a background job that reports back
                  through write_event_value, and a crash popup (pythonw has no console - without it an error is just a vanished window).

CHANGE LOG (newest first, 1 line per change):
2026-10-30  v1.0  First version
"""
import threading
import time
import traceback

import PySimpleGUI as sg

VERSION = '1.0'
APP_NAME = 'My App'                                   # shows in the title bar with the version
SETTINGS_FILE = 'my_app.json'                         # kept in PySimpleGUI's user settings folder
FONT = ('Segoe UI', 11)
sg.theme('DarkGrey13')

# ---- keys: constants so the editor completes them; KT_ makes tuple keys for repeated elements ----
K_INPUT = '-INPUT-'
K_GO = '-GO-'
K_LOG = '-LOG-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_JOB_DONE = '-JOB DONE-'            # sent from the worker thread
K_JOB_ERROR = '-JOB ERROR-'
K_ROW = '-ROW-'
KT_ROW = lambda num: (K_ROW, num)    # e.g. for a grid of buttons:  sg.Button(str(n), key=KT_ROW(n))


def make_window():
    layout = [[sg.Text('Something to do:'), sg.Input(sg.user_settings_get_entry('-last input-', ''), key=K_INPUT, expand_x=True, focus=True),
               sg.Button('Go', key=K_GO, bind_return_key=True)],
              [sg.Multiline('', key=K_LOG, size=(80, 15), disabled=True, autoscroll=True, expand_x=True, expand_y=True)],
              [sg.Text('', key=K_STATUS, expand_x=True), sg.Text(f'v{VERSION}', text_color='grey')]]
    window = sg.Window(f'{APP_NAME}  v{VERSION}', layout, font=FONT, resizable=True, finalize=True, auto_save_location=True,
                       right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT)
    window.bind('<Escape>', K_ESCAPE)
    text = window[K_LOG].Widget                       # keyboard scrolling of the read-only log: the keys do nothing on a disabled Text widget by default
    text.bind('<Button-1>', lambda e: text.focus_set(), add='+')
    for seq, amount, unit in (('<Up>', -1, 'units'), ('<Down>', 1, 'units'), ('<Prior>', -1, 'pages'), ('<Next>', 1, 'pages')):
        text.bind(seq, lambda e, a=amount, u=unit: (text.yview_scroll(a, u), 'break')[1])
    text.bind('<Home>', lambda e: (text.yview_moveto(0), 'break')[1])
    text.bind('<End>', lambda e: (text.yview_moveto(1), 'break')[1])
    return window


def job(window, text):
    """Runs in a thread.  Never touch the window from here except through write_event_value."""
    try:
        time.sleep(1.5)                               # the actual work goes here
        window.write_event_value(K_JOB_DONE, f'Did "{text}"')
    except Exception:
        window.write_event_value(K_JOB_ERROR, traceback.format_exc())


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    window = make_window()
    while True:
        event, values = window.read()
        if event in ('Exit', sg.WINDOW_CLOSED, K_ESCAPE):
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == K_GO:
            sg.user_settings_set_entry('-last input-', values[K_INPUT])
            window[K_STATUS].update('Working…')
            threading.Thread(target=job, args=(window, values[K_INPUT]), daemon=True).start()
        elif event == K_JOB_DONE:
            window[K_LOG].print(values[event])
            window[K_STATUS].update('Done')
        elif event == K_JOB_ERROR:
            window[K_STATUS].update('Failed')
            sg.popup_error_with_traceback('The job failed', values[event])     # popups must run on the main thread - that's why the thread sends the traceback here
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
