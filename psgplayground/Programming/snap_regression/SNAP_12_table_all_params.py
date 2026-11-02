"""
SNAPSHOT TEST 12 - Table Element (24 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
values, headings, visible_column_map, col_widths, cols_justification,
def_col_width, auto_size_columns, max_col_width, display_row_numbers,
starting_row_number, num_rows, row_height, font, justification,
text_color, background_color, alternating_row_color, selected_row_colors
(via a programmatic select_rows update - ttk selection shows without
focus), header_text_color/background_color/font/border_width/relief,
row_colors, vertical_scroll_only, hide_vertical_scroll, border_width,
sbar_* colors/width, expand_x, tooltip, visible. NOT covered (no
resting-state visual): select_mode, enable_cell_editing,
cell_edit_colors, enable_click_events, right_click_selects,
bind_return_key, change_submits/enable_events, size/s (Table sizing is
via num_rows/col widths), key/k/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

headings = ['Name', 'Age', 'City']
data = [['Alice', 30, 'NYC'], ['Bob', 25, 'LA'], ['Cara', 35, 'SF'],
        ['Dan', 40, 'Austin'], ['Eve', 28, 'Denver'], ['Fay', 33, 'Miami']]
wide_data = [[f'r{r}c{c}-' + 'x' * 10 for c in range(8)] for r in range(6)]

def make_table(num_rows=4, **kwargs):
    kw = dict(values=data, num_rows=num_rows, headings=headings,
              auto_size_columns=True, max_col_width=20, justification='center')
    kw.update(kwargs)
    return sg.Table(**kw)

header = "Table Element - 24 parameter variants (verified against 6.3.2 source)"

col_a = [
    [sg.Text('--- Rows, Numbers, Colors ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 default:'), make_table(key='-T1-')],
    [sg.Text('2 display_row_numbers:'), make_table(display_row_numbers=True, key='-T2-')],
    [sg.Text('3 starting_row_number=100:'), make_table(display_row_numbers=True, starting_row_number=100, key='-T3-')],
    [sg.Text('4 alternating_row_color:'), make_table(alternating_row_color='lightyellow', key='-T4-')],
    [sg.Text('5 row_colors 2 rows:'), make_table(row_colors=[(0, 'white', 'red'), (2, 'black', 'orange')], key='-T5-')],
    [sg.Text('6 text/background color:'), make_table(text_color='white', background_color='navy', key='-T6-')],
    [sg.Text('7 selected_row_colors (row 1 selected):'), make_table(selected_row_colors=('yellow', 'purple'), key='-T7-')],
    [sg.Text('8 num_rows=2:'), make_table(num_rows=2, key='-T8-')],
]

col_b = [
    [sg.Text('--- Headers, Fonts, Geometry ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('9 header colors:'), make_table(header_text_color='white', header_background_color='navy', key='-T9-')],
    [sg.Text('10 header_font bold 12:'), make_table(header_font=('Helvetica', 12, 'bold'), key='-T10-')],
    [sg.Text('11 header_border_width=4 + relief raised:'), make_table(header_border_width=4, header_relief='raised', key='-T11-')],
    [sg.Text('12 body font Courier 12:'), make_table(font=('Courier', 12), key='-T12-')],
    [sg.Text('13 row_height=34:'), make_table(row_height=34, key='-T13-')],
    [sg.Text('14 justification=left:'), make_table(justification='left', key='-T14-')],
    [sg.Text('15 justification=right:'), make_table(justification='right', key='-T15-')],
    [sg.Text('16 border_width=6:'), make_table(border_width=6, key='-T16-')],
]

col_c = [
    [sg.Text('--- Columns, Scrollbars ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('17 auto_size=False def_col_width=6:'), make_table(auto_size_columns=False, def_col_width=6, key='-T17-')],
    [sg.Text('18 col_widths=[12,4,10]:'), make_table(auto_size_columns=False, col_widths=[12, 4, 10], key='-T18-')],
    [sg.Text('19 cols_justification l/c/r:'), make_table(cols_justification=['l', 'c', 'r'], auto_size_columns=False, def_col_width=10, key='-T19-')],
    [sg.Text('20 visible_column_map hides Age:'), make_table(visible_column_map=[True, False, True], key='-T20-')],
    [sg.Text('21 hide_vertical_scroll (6 rows in 3):'), make_table(num_rows=3, hide_vertical_scroll=True, key='-T21-')],
    [sg.Text('22 h-scroll (vertical_scroll_only=False):'),
     sg.Table(values=wide_data, headings=[f'H{c}' for c in range(8)], num_rows=4,
              auto_size_columns=False, def_col_width=12, vertical_scroll_only=False,
              size=(30, 4), key='-T22-')],
    [sg.Text('23 sbar colors orange/navy wide:'),
     sg.Table(values=data * 3, headings=headings, num_rows=4, sbar_trough_color='orange',
              sbar_arrow_color='navy', sbar_width=25, sbar_arrow_width=25, key='-T23-')],
    [sg.Text('24 expand_x + tooltip:'), make_table(expand_x=True, tooltip='Table tooltip!', key='-T24-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 12 - Table Element All Params (24)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
# Programmatic selection so selected_row_colors is actually visible
window['-T7-'].update(select_rows=[1])
snap_window(window, 'output/screenshots/SNAP_12_table_all_params.png')
window.close()
