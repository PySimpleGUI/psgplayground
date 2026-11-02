"""
SNAPSHOT TEST 1b - Text.update() (18 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.1 source. Every
keyword in Text.update() is exercised: value, background_color,
text_color, font, visible.

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically, so
any difference between them is an update() bug, not a theme/platform
difference.

Also covered: non-string value conversion, multiline value, empty-string
value, COLOR_SYSTEM_DEFAULT ignored, no-arg update as no-op, sequential
updates (last wins), visible False and False->True round trip,
justification/size surviving a value update.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Text.update() - 18 variants (verified against 6.3.1 source)"

col_a = [
    [sg.Text('--- value & colors ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 value'), sg.Text('BEFORE', key='-T1-')],
    [sg.Text('2 value int'), sg.Text('BEFORE', key='-T2-')],
    [sg.Text('3 value multiline'), sg.Text('BEFORE', key='-T3-')],
    [sg.Text('4 value empty string'), sg.Text('BEFORE', size=(20, 1), background_color='pink', key='-T4-'), sg.Text('<-')],
    [sg.Text('5 text_color red [ref->]'), sg.Text('updated', key='-T5-'), sg.Text('constructed', text_color='red')],
    [sg.Text('6 background_color yellow [ref->]'), sg.Text('updated', key='-T6-'), sg.Text('constructed', background_color='yellow')],
    [sg.Text('7 both colors white/purple [ref->]'), sg.Text('updated', key='-T7-'), sg.Text('constructed', text_color='white', background_color='purple')],
    [sg.Text('8 COLOR_SYSTEM_DEFAULT ignored'), sg.Text('stays lime on black', text_color='lime', background_color='black', key='-T8-')],
    [sg.Text('9 update() no args'), sg.Text('unchanged', key='-T9-')],
    [sg.Text('10 sequential, last wins'), sg.Text('first', key='-T10-')],
]

col_b = [
    [sg.Text('--- font, visibility, combos ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('11 font tuple Courier 14 [ref->]'), sg.Text('updated', key='-T11-'), sg.Text('constructed', font=('Courier', 14))],
    [sg.Text('12 font single string [ref->]'), sg.Text('updated', key='-T12-'), sg.Text('constructed', font='Helvetica 14 bold')],
    [sg.Text('13 font bold italic [ref->]'), sg.Text('updated', key='-T13-'), sg.Text('constructed', font=('Helvetica', 12, 'bold italic'))],
    [sg.Text('14 value+colors+font combo'), sg.Text('BEFORE', key='-T14-')],
    [sg.Text('15 visible=False ->'), sg.Text('15 hidden', key='-T15-'), sg.Text('<-')],
    [sg.Text('16 visible False->True ->'), sg.Text('16 restored', key='-T16-'), sg.Text('<-')],
    [sg.Text('17 value keeps center just+size'), sg.Text('BEFORE', justification='center', size=(24, 1), background_color='light grey', key='-T17-')],
    [sg.Text('18 text_color only, bg kept'), sg.Text('red on light blue', background_color='light blue', key='-T18-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 01 - Text.update() (18)', layout, finalize=True, resizable=True)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-T1-'].update(value='AFTER')                                            # 1
window['-T2-'].update(value=12345)                                              # 2
window['-T3-'].update(value='line one\nline two')                               # 3
window['-T4-'].update(value='')                                                 # 4
window['-T5-'].update(text_color='red')                                         # 5
window['-T6-'].update(background_color='yellow')                                # 6
window['-T7-'].update(text_color='white', background_color='purple')              # 7
window['-T8-'].update(text_color=sg.COLOR_SYSTEM_DEFAULT,                       # 8
                      background_color=sg.COLOR_SYSTEM_DEFAULT)
window['-T9-'].update()                                                         # 9
window['-T10-'].update(value='second')                                          # 10
window['-T10-'].update(value='third (correct)')
window['-T11-'].update(font=('Courier', 14))                                    # 11
window['-T12-'].update(font='Helvetica 14 bold')                                # 12
window['-T13-'].update(font=('Helvetica', 12, 'bold italic'))                   # 13
window['-T14-'].update(value='COMBO', text_color='yellow',                      # 14
                       background_color='maroon', font=('Courier', 12, 'bold'))
window['-T15-'].update(visible=False)                                           # 15
window['-T16-'].update(visible=False)                                           # 16
window['-T16-'].update(visible=True)
window['-T17-'].update(value='AFTER')                                           # 17
window['-T18-'].update(text_color='red')                                        # 18

window.refresh()
snap_window(window, 'output/screenshots/SNAP_01_text_update.png')
window.close()
