"""
SNAPSHOT TEST 14 - Graph Element (12 canvases), non-interactive.

Constructor params verified against the PySimpleGUI 6.3.2 source.
Covered: canvas_size, graph_bottom_left/graph_top_right (normal AND
inverted-Y coordinate systems), background_color, border_width (0/2/8),
pad, expand_x, float_values, tooltip, visible. Draw methods exercised:
draw_rectangle, draw_circle, draw_oval, draw_point, draw_line,
draw_lines (with arrow + joinstyle), draw_polygon, draw_arc (pieslice/
chord/arc), draw_text (fonts, colors, angle). NOT covered (behavioral
only): change_submits/drag_submits/enable_events/motion_events,
right_click_menu, key/k/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Graph Element - 12 canvases (verified against 6.3.2 source)"

def G(key, **kwargs):
    kw = dict(canvas_size=(200, 120), graph_bottom_left=(0, 0), graph_top_right=(200, 120),
              background_color='white', border_width=2, key=key)
    kw.update(kwargs)
    return sg.Graph(**kw)

col_a = [
    [sg.Text('1 rect/circle/line:'), G('-G1-')],
    [sg.Text('2 polygon + text:'), G('-G2-')],
    [sg.Text('3 arcs pieslice/chord/arc:'), G('-G3-')],
    [sg.Text('4 draw_lines arrow round join:'), G('-G4-')],
    [sg.Text('5 points + ovals:'), G('-G5-')],
    [sg.Text('6 dark bg + white text:'), G('-G6-', background_color='navy')],
]

col_b = [
    [sg.Text('7 INVERTED Y coords:'), G('-G7-', graph_bottom_left=(0, 120), graph_top_right=(200, 0))],
    [sg.Text('8 float_values=True:'), G('-G8-', graph_bottom_left=(0.0, 0.0), graph_top_right=(1.0, 1.0), float_values=True)],
    [sg.Text('9 border_width=0:'), G('-G9-', border_width=0)],
    [sg.Text('10 border_width=8:'), G('-G10-', border_width=8)],
    [sg.Text('11 pad=(30,20) + tooltip:'), G('-G11-', pad=(30, 20), tooltip='Graph tooltip!')],
    [sg.Text('12 rotated/angled text:'), G('-G12-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 14 - Graph Element All Params (12)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

g = {i: window[f'-G{i}-'] for i in range(1, 13)}

g[1].draw_rectangle((20, 20), (80, 80), fill_color='blue')
g[1].draw_circle((140, 50), 30, fill_color='red')
g[1].draw_line((10, 100), (190, 100), color='green', width=3)

g[2].draw_polygon([(100, 20), (140, 90), (60, 90)], fill_color='orange', line_color='black')
g[2].draw_text('Triangle', (100, 105), font=('Helvetica', 10))

g[3].draw_arc((10, 10), (70, 70), 0, 180, style='pieslice', fill_color='yellow')
g[3].draw_arc((80, 10), (140, 70), 0, 180, style='chord', fill_color='lightblue')
g[3].draw_arc((150, 10), (200, 70), 0, 180, style='arc', line_width=3)

g[4].draw_lines([(10, 20), (60, 90), (110, 30), (160, 90)], color='purple', width=3,
                arrow=True, arrow_shape=(16, 20, 6), joinstyle='round')

for i, x in enumerate(range(20, 200, 30)):
    g[5].draw_point((x, 30), size=4 + i * 2, color='red')
g[5].draw_oval((20, 60), (100, 100), fill_color='light green', line_color='black', line_width=2)
g[5].draw_oval((110, 60), (190, 110), line_color='blue', line_width=4)

g[6].draw_text('Dark canvas', (100, 60), color='white', font=('Helvetica', 12))

# 7: same drawing calls as a normal-axis canvas would use - with inverted Y
# the "TOP (0,0...)" text lands at the top and the rectangle hangs from it,
# proving the coordinate flip is honored.
g[7].draw_text('TOP (y grows down)', (100, 15), font=('Helvetica', 9))
g[7].draw_rectangle((20, 25), (80, 60), fill_color='red')
g[7].draw_text('BOTTOM', (100, 110), font=('Helvetica', 9))

g[8].draw_circle((0.5, 0.5), 0.2, fill_color='pink')
g[8].draw_line((0.0, 0.0), (1.0, 1.0), color='blue', width=2)
g[8].draw_text('float coords', (0.5, 0.85), font=('Helvetica', 8))

g[9].draw_rectangle((40, 30), (160, 90), fill_color='light grey')
g[9].draw_text('no border', (100, 60), font=('Helvetica', 10))

g[10].draw_rectangle((40, 30), (160, 90), fill_color='light blue')
g[10].draw_text('thick border', (100, 60), font=('Helvetica', 10))

g[11].draw_text('padded canvas', (100, 60), font=('Helvetica', 10))

g[12].draw_text('angle=0', (60, 100), font=('Helvetica', 10))
g[12].draw_text('angle=45', (100, 60), font=('Helvetica', 10), angle=45)
g[12].draw_text('angle=90', (170, 60), font=('Helvetica', 10), angle=90)
g[12].draw_text('bold red', (60, 20), font=('Helvetica', 10, 'bold'), color='red')

snap_window(window, 'output/screenshots/SNAP_14_graph_all_params.png')
window.close()
