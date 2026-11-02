"""
SNAPSHOT TEST 13b - Tree.update() (5 variants), non-interactive.

Signature: update(values, key, value, text, icon, visible). Tree is
unusual: `values` takes a whole new TreeData; `key` addresses ONE node,
then `text` renames it and `value` replaces its column values. Covered:
values (whole tree replaced), key+text (node renamed), key+value
(node's column values changed), visible round trip, no-arg no-op.
NOT covered: icon (needs image data per node; add later if wanted).

Pattern: created "before", update() after finalize, snapshot = "after".

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Tree.update() - 5 variants"

def make_tree():
    td = sg.TreeData()
    td.insert('', '-FRUIT-', 'Fruit', [3])
    td.insert('-FRUIT-', '-APPLE-', 'Apple', [5])
    td.insert('-FRUIT-', '-BANANA-', 'Banana', [12])
    td.insert('', '-VEG-', 'Veg', [1])
    td.insert('-VEG-', '-CARROT-', 'Carrot', [7])
    return td

def make_tree2():
    td = sg.TreeData()
    td.insert('', '-A-', 'ReplacedRoot', [99])
    td.insert('-A-', '-B-', 'ReplacedChild', [1])
    return td

def TR(key):
    return sg.Tree(data=make_tree(), headings=['Qty'], num_rows=6,
                   col0_width=14, auto_size_columns=False, key=key)

col_a = [
    [sg.Text('1 values: whole tree replaced'), TR('-TR1-')],
    [sg.Text('2 key+text: Apple renamed AFTER'), TR('-TR2-')],
    [sg.Text('3 key+value: Banana qty 12->[999]'), TR('-TR3-')],
]

col_b = [
    [sg.Text('4 update() no args'), TR('-TR4-')],
    [sg.Text('5 visible False->True ->'), TR('-TR5-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 13 - Tree.update() (5)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

window['-TR1-'].update(values=make_tree2())                                     # 1
window['-TR2-'].update(key='-APPLE-', text='AFTER')                             # 2
window['-TR3-'].update(key='-BANANA-', value=[999])                             # 3
window['-TR4-'].update()                                                        # 4
window['-TR5-'].update(visible=False)                                           # 5
window['-TR5-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_13_tree_update.png')
window.close()
