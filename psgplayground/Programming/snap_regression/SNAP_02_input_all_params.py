"""
SNAPSHOT TEST 2 - Input Element (30 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-22 kept with identical parameters (reflowed into columns);
23-30 appended. Covered: default_text, placeholder + its color/bg/
justification params, size/s (tuple + bare int), disabled, readonly,
use_readonly_for_disable=False, disabled_readonly_background_color/
text_color, password_char, justification, background/text colors,
selected_* colors (param smoke test - needs focused selection to show),
font, border_width, do_not_clear, pad/p, tooltip, expand_x, visible.
NOT covered: focus (blinking caret = flaky), change_submits/
enable_events/right_click_menu (behavioral), key/k/setting/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Input Element - 30 parameter variants (verified against 6.3.2 source)"

col_a = [
    [sg.Text('1 Plain empty'), sg.Input(key='-I1-')],
    [sg.Text('2 Pre-filled default_text'), sg.Input(default_text='Pre-filled', key='-I2-')],
    [sg.Text('3 Password char *'), sg.Input(password_char='*', default_text='secret', key='-I3-')],
    [sg.Text('4 Password char bullet'), sg.Input(password_char='•', default_text='secret', key='-I4-')],
    [sg.Text('5 Left justified'), sg.Input(justification='left', default_text='left', key='-I5-')],
    [sg.Text('6 Center justified'), sg.Input(justification='center', default_text='center', key='-I6-')],
    [sg.Text('7 Right justified'), sg.Input(justification='right', default_text='right', key='-I7-')],
    [sg.Text('8 Disabled'), sg.Input(disabled=True, default_text='disabled', key='-I8-')],
    [sg.Text('9 Readonly'), sg.Input(readonly=True, default_text='readonly', key='-I9-')],
    [sg.Text('10 Placeholder basic'), sg.Input(placeholder='Type here...', key='-I10-')],
]

col_b = [
    [sg.Text('11 Placeholder red text'), sg.Input(placeholder='red placeholder', placeholder_text_color='red', key='-I11-')],
    [sg.Text('12 Placeholder yellow bg'), sg.Input(placeholder='yellow bg', placeholder_background_color='yellow', key='-I12-')],
    [sg.Text('13 Placeholder right-just'), sg.Input(placeholder='right', placeholder_justification='right', key='-I13-')],
    [sg.Text('14 Courier font 14'), sg.Input(font=('Courier', 14), default_text='Courier14', key='-I14-')],
    [sg.Text('15 Bold font'), sg.Input(font=('Helvetica', 12, 'bold'), default_text='Bold', key='-I15-')],
    [sg.Text('16 Border width 5'), sg.Input(border_width=5, default_text='thick border', key='-I16-')],
    [sg.Text('17 Custom bg/text color'), sg.Input(background_color='black', text_color='lime', default_text='colors', key='-I17-')],
    [sg.Text('18 Selected text colors'), sg.Input(selected_text_color='white', selected_background_color='blue', default_text='select me', key='-I18-')],
    [sg.Text('19 Tooltip'), sg.Input(tooltip='Input tooltip!', default_text='hover me', key='-I19-')],
    [sg.Text('20 Small size 10'), sg.Input(size=(10, 1), default_text='small', key='-I20-')],
]

col_c = [
    [sg.Text('21 Large size 50'), sg.Input(size=(50, 1), default_text='large width input box', key='-I21-')],
    [sg.Text('22 do_not_clear=False'), sg.Input(do_not_clear=False, default_text='clears on event', key='-I22-')],
    [sg.Text('23 disabled_readonly bg/text colors'), sg.Input(readonly=True,
                                                              default_text='styled readony',
                                                              disabled=True,
                                                              disabled_readonly_background_color='navy',
                                                              disabled_readonly_text_color='yellow', key='-I23-')],
    [sg.Text('24 use_readonly_for_disable=False'), sg.Input(disabled=True, use_readonly_for_disable=False,
                                                            default_text='true tk disabled', key='-I24-')],
    [sg.Text('25 placeholder center-just'), sg.Input(placeholder='centered', placeholder_justification='center', key='-I25-')],
    [sg.Text('26 s= size alias (15,1)'), sg.Input(s=(15, 1), default_text='s alias', key='-I26-')],
    [sg.Text('27 size=25 bare int'), sg.Input(size=25, default_text='bare int size', key='-I27-')],
    [sg.Text('28 pad=(30,15)'), sg.Input(pad=(30, 15), default_text='padded', key='-I28-')],
    [sg.Text('29 p= alias asymmetric'), sg.Input(p=((40, 5), (15, 0)), default_text='p alias', key='-I29-')],
    [sg.Text('30 expand_x / hidden ->'), sg.Input(default_text='expand_x', expand_x=True, key='-I30-'),
     sg.Input(default_text='hidden', visible=False, k='-I31-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 02 - Input Element All Params (30)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

snap_window(window, 'output/screenshots/SNAP_02_input_all_params.png')
window.close()
