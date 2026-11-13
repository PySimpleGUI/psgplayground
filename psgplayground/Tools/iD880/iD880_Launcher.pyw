#!/usr/bin/env python
"""
iD880 Launcher - one window with a button for each iD880 program.  Each program opens in its own window; the launcher stays up.

    Keys 1-7 launch the programs.   Esc closes the launcher (the other programs keep running).
Needs id880_lib.py and the other iD880 programs in the same folder.
"""
import os

import PySimpleGUI as sg

import id880_lib as lib

K_LAUNCH = '-LAUNCH-'
KT_LAUNCH = lambda name: (K_LAUNCH, name)
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'

FOLDER = os.path.dirname(os.path.abspath(__file__))
PROGRAMS = [('iD880_Setup', 'Printer Setup', 'Connection, test prints, nudge, raw commands', lib.BLUE),
            ('iD880_Notes', 'Notes', 'Lists and notes on the receipt paper', lib.GREEN),
            ('iD880_Address_Labels', 'Address Labels', 'Mailing, To-only and return labels', lib.GREEN),
            ('iD880_Ship_Label', 'Ship Label', 'Print a carrier PDF label as 4x6', lib.GREEN),
            ('iD880_Picture', 'Picture', 'Photos, drawings and screenshots', lib.GREEN),
            ('iD880_Figlet', 'Figlet', 'Big FIGlet lettering and banners', lib.GREEN),
            ('iD880_Banner', 'Banner', 'Big lettering in any font on this PC - banner or across', lib.GREEN)]


def make_window():
    sg.theme(lib.THEME)
    rows = []
    for i, (name, title, blurb, color) in enumerate(PROGRAMS, 1):
        rows.append([sg.Button(f'{i}  {title}', key=KT_LAUNCH(name), size=(18, 2), font=('Helvetica', 12, 'bold'), button_color=('white', color)),
                     sg.Text(blurb, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)])
    rows.append([sg.Text(lib.printer_summary(), key=K_STATUS, font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)])
    window = sg.Window('iD880 Launcher', rows, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True)
    window.bind('<Escape>', K_ESCAPE)
    for i, (name, *_) in enumerate(PROGRAMS, 1):
        window.bind(str(i), KT_LAUNCH(name))
    return window


def main():
    window = make_window()
    while True:
        event, values = window.read()
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        if event == K_ESCAPE:
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70,10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif isinstance(event, tuple) and event[0] == K_LAUNCH:
            path = os.path.join(FOLDER, event[1] + '.pyw')
            if os.path.isfile(path):
                sg.execute_py_file(path, cwd=FOLDER)
                window[K_STATUS].update(f'Started {event[1]}    ({lib.printer_summary()})', text_color='#9CCC65')
            else:
                sg.popup_error(f'Missing: {path}', title='iD880 Launcher', keep_on_top=True)
    window.close()


if __name__ == '__main__':
    main()
