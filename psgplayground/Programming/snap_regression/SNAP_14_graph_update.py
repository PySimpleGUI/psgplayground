"""
SNAPSHOT TEST 14b - Graph.update() (5 variants), non-interactive.

Signature: update(background_color, visible) - Graph's post-finalize
behavior is mostly its draw_* METHODS (covered in SNAP_14 all_params);
update() itself only changes background and visibility. Covered:
background_color [ref], background_color with existing drawing kept,
erase() then redraw (method smoke proving post-finalize drawing),
visible round trip, no-arg no-op.

Pattern: created "before", update() after finalize, snapshot = "after".

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Graph.update() - 5 variants"

def G(key=None, **kwargs):
    kw = dict(canvas_size=(160, 90), graph_bottom_left=(0, 0),
              graph_top_right=(160, 90), background_color='white')
    if key is not None:
        kw['key'] = key
    kw.update(kwargs)
    return sg.Graph(**kw)

col_a = [
    [sg.Text('1 background white->yellow [ref->]'), G('-G1-'), G(background_color='yellow')],
    [sg.Text('2 bg change keeps drawing'), G('-G2-'), sg.Text('<- circle survives on pink')],
    [sg.Text('3 erase + redraw (method smoke)'), G('-G3-'), sg.Text('<- square only, no circle')],
]

col_b = [
    [sg.Text('4 update() no args'), G('-G4-')],
    [sg.Text('5 visible False->True ->'), G('-G5-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 14 - Graph.update() (5)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

window['-G1-'].update(background_color='yellow')                                # 1
window['-G2-'].draw_circle((80, 45), 25, fill_color='blue')                     # 2
window['-G2-'].update(background_color='pink')
window['-G3-'].draw_circle((80, 45), 25, fill_color='blue')                     # 3
window['-G3-'].erase()
window['-G3-'].draw_rectangle((50, 20), (110, 70), fill_color='green')
window['-G4-'].update()                                                         # 4
window['-G5-'].update(visible=False)                                            # 5
window['-G5-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_14_graph_update.png')
window.close()
