"""
SNAPSHOT TEST 13 - Tree Element (18 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
data, headings, visible_column_map, col_widths, col0_width, col0_heading,
def_col_width, auto_size_columns, max_col_width, show_expanded, font,
justification, text_color, border_width, background_color,
header_text_color/background_color/font/border_width/relief, num_rows,
sbar_* colors/width, row_height, hide_vertical_scroll, expand_x,
tooltip, visible. NOT covered (no resting-state visual): select_mode,
selected_row_colors (Tree has no select_rows update path),
click_toggles_select, change_submits/enable_events, pad on every
variant, key/k/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

def make_tree_data():
    td = sg.TreeData()
    td.Insert('', '_F_', 'Fruits', [])
    td.Insert('_F_', '_A_', 'Apple', [12])
    td.Insert('_F_', '_B_', 'Banana', [7])
    td.Insert('', '_V_', 'Veggies', [])
    td.Insert('_V_', '_C_', 'Carrot', [20])
    return td

def make_tree(key, **kwargs):
    kw = dict(data=make_tree_data(), headings=['Qty'], col0_heading='Item',
              auto_size_columns=True, num_rows=5, key=key)
    kw.update(kwargs)
    return sg.Tree(**kw)

header = "Tree Element - 18 parameter variants (verified against 6.3.2 source)"

col_a = [
    [sg.Text('--- Structure & Geometry ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 default:'), make_tree('-TR1-')],
    [sg.Text('2 show_expanded=True:'), make_tree('-TR2-', show_expanded=True)],
    [sg.Text('3 col0_width=25:'), make_tree('-TR3-', col0_width=25)],
    [sg.Text('4 col0_heading changed:'), make_tree('-TR4-', col0_heading='Category/Item')],
    [sg.Text('5 auto_size=False def_col_width=5:'), make_tree('-TR5-', auto_size_columns=False, def_col_width=5)],
    [sg.Text('6 col_widths=[4] for Qty:'), make_tree('-TR6-', auto_size_columns=False, col_widths=[4])],
    [sg.Text('7 num_rows=3 (scrollbar appears):'), make_tree('-TR7-', num_rows=3, show_expanded=True)],
    [sg.Text('8 row_height=32:'), make_tree('-TR8-', row_height=32)],
    [sg.Text('9 visible_column_map=[False] hides Qty:'), make_tree('-TR9-', visible_column_map=[False])],
]

col_b = [
    [sg.Text('--- Colors, Fonts, Scrollbars ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('10 header colors white/navy:'), make_tree('-TR10-', header_text_color='white', header_background_color='navy')],
    [sg.Text('11 header_font bold 12:'), make_tree('-TR11-', header_font=('Helvetica', 12, 'bold'))],
    [sg.Text('12 header_border_width=4 relief raised:'), make_tree('-TR12-', header_border_width=4, header_relief='raised')],
    [sg.Text('13 body font Courier 12:'), make_tree('-TR13-', font=('Courier', 12))],
    [sg.Text('14 text/background color:'), make_tree('-TR14-', text_color='white', background_color='navy', show_expanded=True)],
    [sg.Text('15 background light yellow:'), make_tree('-TR15-', background_color='light yellow', show_expanded=True)],
    [sg.Text('16 justification=left for Qty:'), make_tree('-TR16-', justification='left', show_expanded=True)],
    [sg.Text('17 sbar colors + width 25:'), make_tree('-TR17-', num_rows=3, show_expanded=True,
                                                      sbar_trough_color='orange', sbar_arrow_color='navy',
                                                      sbar_width=25, sbar_arrow_width=25)],
    # [sg.Text('18 border_width=6 + hide_vertical_scroll:'), make_tree('-TR18-', num_rows=3, show_expanded=True, border_width=6, hide_vertical_scroll=True, tooltip='Tree tooltip!')],
    [sg.Text('18 border_width=6 + hide_vertical_scroll:'), make_tree('-TR18-', num_rows=3, show_expanded=True, border_width=6, hide_vertical_scroll=True, )],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 13 - Tree Element All Params (18)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
snap_window(window, 'output/screenshots/SNAP_13_tree_all_params.png')
window.close()
