"""
SNAPSHOT TEST 8b - Slider.update() (14 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. The
Slider.update() signature is small: value, range, disabled, visible.
Covered: value (mid-range move, to min, to max, float on a float
range, on a vertical slider), range (shrunk with the old value outside
the new range - documents the clamp, replaced together with a value,
switched to a negative span), disabled (True and re-enable), visible
(hide and hide->restore), no-arg update as a no-op, and sequential
updates (last wins).

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically.

NOTE variant 6: after range=(0,10) the old value 50 is outside the new
range - tk clamps the displayed value to the new max. Whatever renders
becomes the documented baseline; the annotation marks the cell.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Slider.update() - 14 variants (verified against 6.3.2 source)"

def HS(key=None, **kwargs):
    kw = dict(range=(0, 100), default_value=50, orientation='h', size=(25, 15))
    if key is not None:
        kw['key'] = key
    kw.update(kwargs)
    return sg.Slider(**kw)

col_a = [
    [sg.Text('--- value ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 value 50->90 [ref->]'), HS('-SL1-'), HS(default_value=90)],
    [sg.Text('2 value to min (0)'), HS('-SL2-')],
    [sg.Text('3 value to max (100)'), HS('-SL3-')],
    [sg.Text('4 float value 2.5->7.5'), HS('-SL4-', range=(0.0, 10.0), default_value=2.5, resolution=0.1)],
    [sg.Text('5 update() no args'), HS('-SL5-'), sg.Text('<- stays 50')],
    [sg.Text('6 range shrunk (0,10), 50 clamps'), HS('-SL6-'), sg.Text('<- what shows?')],
    [sg.Text('7 range + value together [ref->]'), HS('-SL7-'), HS(range=(0, 10), default_value=3)],
]

col_b = [
    [sg.Text('--- range, state, visibility ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('8 range negative (-50,50), value 0 [ref->]'), HS('-SL8-'), HS(range=(-50, 50), default_value=0)],
    [sg.Text('9 sequential, last wins'), HS('-SL9-'), sg.Text('<- 75')],
    [sg.Text('10 disabled=True [ref->]'), HS('-SL10-', text_color='red'), HS(text_color='red', disabled=True)],
    [sg.Text('11 disabled True->False (re-enabled)'), HS('-SL11-', disabled=True)],
    [sg.Text('12 visible=False ->'), HS('-SL12-'), sg.Text('<-')],
    [sg.Text('13 visible False->True ->'), HS('-SL13-'), sg.Text('<-')],
]

col_v = [
    [sg.Text('--- Vertical ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('14 vert value 0->8 [ref->]'),
     sg.Slider(range=(-10, 10), default_value=0, orientation='v', key='-SL14-'),
     sg.Slider(range=(-10, 10), default_value=8, orientation='v')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_v, vertical_alignment='top')],
]

window = sg.Window('SNAP 08 - Slider.update() (14)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-SL1-'].update(value=90)                                                # 1
window['-SL2-'].update(value=0)                                                 # 2
window['-SL3-'].update(value=100)                                               # 3
window['-SL4-'].update(value=7.5)                                               # 4
window['-SL5-'].update()                                                        # 5
window['-SL6-'].update(range=(0, 10))                                           # 6  50 outside new range
window['-SL7-'].update(range=(0, 10), value=3)                                  # 7
window['-SL8-'].update(range=(-50, 50), value=0)                                # 8
window['-SL9-'].update(value=25)                                                # 9
window['-SL9-'].update(value=75)                                                #    last wins
window['-SL10-'].update(disabled=True)                                          # 10
window['-SL11-'].update(disabled=False)                                         # 11
window['-SL12-'].update(visible=False)                                          # 12
window['-SL13-'].update(visible=False)                                          # 13
window['-SL13-'].update(visible=True)
window['-SL14-'].update(value=8)                                                # 14

window.refresh()
snap_window(window, 'output/screenshots/SNAP_08_slider_update.png')
window.close()
