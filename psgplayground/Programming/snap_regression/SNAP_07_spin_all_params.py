"""
SNAPSHOT TEST 7 - Spin Element (26 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-20 kept with identical parameters (reflowed into columns);
21-26 appended. Covered: values (ints/floats/strings/negative/single),
initial_value, wrap, readonly, disabled, background/text colors, font,
auto_size_text, size/s (tuple + bare int), pad/p, tooltip, expand_x,
visible. NOT covered: bind_return_key/change_submits/enable_events
(behavioral - bind_return_key kept from original as smoke test),
right_click_menu (dropdown only), key/k/setting/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Spin Element - 26 parameter variants (verified against 6.3.2 source)"

R11 = list(range(0, 11))

col_a = [
    [sg.Text('1 Ints 0-10 no wrap'), sg.Spin(R11, initial_value=5, key='-S1-')],
    [sg.Text('2 Ints 0-10 wrap=True'), sg.Spin(R11, initial_value=5, wrap=True, key='-S2-')],
    [sg.Text('3 Strings XS-XL'), sg.Spin(['XS', 'S', 'M', 'L', 'XL'], initial_value='M', key='-S3-')],
    [sg.Text('4 Floats step 0.5'), sg.Spin([round(x * 0.5, 1) for x in range(20)], initial_value=2.5, key='-S4-')],
    [sg.Text('5 Readonly'), sg.Spin(R11, initial_value=5, readonly=True, key='-S5-')],
    [sg.Text('6 Disabled'), sg.Spin(R11, initial_value=5, disabled=True, key='-S6-')],
    [sg.Text('7 Custom colors'), sg.Spin(R11, initial_value=5, background_color='black', text_color='lime', key='-S7-')],
    [sg.Text('8 Bold font'), sg.Spin(R11, initial_value=5, font=('Helvetica', 12, 'bold'), key='-S8-')],
    [sg.Text('9 bind_return_key'), sg.Spin(R11, initial_value=5, bind_return_key=True, key='-S9-')],
]

col_b = [
    [sg.Text('10 Tooltip'), sg.Spin(R11, initial_value=5, tooltip='Spin tooltip!', key='-S10-')],
    [sg.Text('11 Negative ints -10 to 10'), sg.Spin(list(range(-10, 11)), initial_value=0, key='-S11-')],
    [sg.Text('12 Large range 0-1000 step10'), sg.Spin(list(range(0, 1001, 10)), initial_value=500, key='-S12-')],
    [sg.Text('13 auto_size_text=False size8'), sg.Spin(R11, initial_value=5, auto_size_text=False, size=(8, 1), key='-S13-')],
    [sg.Text('14 Courier font'), sg.Spin(R11, initial_value=5, font=('Courier', 11), key='-S14-')],
    [sg.Text('15 pad=(20,20)'), sg.Spin(R11, initial_value=5, pad=(20, 20), key='-S15-')],
    [sg.Text('16 Right-click menu'), sg.Spin(R11, initial_value=5, right_click_menu=['', ['Item A', 'Item B']], key='-S16-')],
    [sg.Text('17 Months list wrap'), sg.Spin(['Jan', 'Feb', 'Mar', 'Apr', 'May'], initial_value='Jan', wrap=True, key='-S17-')],
    [sg.Text('18 Single value list'), sg.Spin(['OnlyOption'], initial_value='OnlyOption', key='-S18-')],
]

col_c = [
    [sg.Text('19 Visible=False'), sg.Spin(R11, initial_value=5, visible=False, key='-S19-')],
    [sg.Text('20 Small size 3'), sg.Spin(R11, initial_value=5, size=(3, 1), key='-S20-')],
    [sg.Text('21 s= size alias (10,1)'), sg.Spin(R11, initial_value=5, s=(10, 1), key='-S21-')],
    [sg.Text('22 size=15 bare int'), sg.Spin(R11, initial_value=5, size=15, key='-S22-')],
    [sg.Text('23 p= alias asymmetric'), sg.Spin(R11, initial_value=5, p=((40, 5), (15, 0)), key='-S23-')],
    [sg.Text('24 expand_x=True'), sg.Spin(R11, initial_value=5, expand_x=True, key='-S24-')],
    [sg.Text('25 readonly + custom colors'), sg.Spin(R11, initial_value=7, readonly=True,
                                                     background_color='light yellow', text_color='maroon', key='-S25-')],
    [sg.Text('26 combined colors+font+size'), sg.Spin(R11, initial_value=9, background_color='navy', text_color='white',
                                                      font=('Courier', 14, 'bold'), size=(6, 1), key='-S26-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 07 - Spin Element All Params (26)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
snap_window(window, 'output/screenshots/SNAP_07_spin_all_params.png')
window.close()
