"""
SNAPSHOT TEST 16 - TabGroup + Tab Elements (7 tab groups), non-interactive.

Parameter lists verified against the PySimpleGUI 6.3.2 source.
TabGroup covered: layout, tab_location (topleft/bottom/lefttop/righttop),
title_color, tab_background_color, selected_title_color,
selected_background_color, background_color, focus_color, font,
border_width, tab_border_width, size, pad. Tab covered: title, layout,
title_color, background_color, disabled, border_width, tooltip,
element_justification, image_source (emoji base64), visible.
NOT covered (no resting-state visual): change_submits/enable_events,
theme (ttk theme interplay - see SNAP_18 window-level ttk_theme),
mouseover_image_source, right_click_menu, key/k/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "TabGroup + Tab - 7 tab groups (verified against 6.3.2 source)"

def tabs(prefix, n=3):
    return [sg.Tab(f'{prefix}{i}', [[sg.Text(f'{prefix}{i} content')]]) for i in range(1, n + 1)]

tg1 = sg.TabGroup([[
    sg.Tab('Tab 1', [[sg.Text('Plain')]]),
    sg.Tab('Tab 2 Disabled', [[sg.Text('Disabled')]], disabled=True),
    sg.Tab('Tab 3', [[sg.Text('Orange title')]], title_color='orange'),
    sg.Tab('Tab 4', [[sg.Text('Custom bg')]], background_color='light yellow'),
    sg.Tab('Tab 5', [[sg.Text('Tooltip')]], tooltip='Tab tip!'),
    sg.Tab('Tab 6', [[sg.Text('Thick border')]], border_width=6),
    sg.Tab('Tab 7', [[sg.Frame('Nested', [[sg.Button('Nested Btn')]])]]),
    sg.Tab('Tab 8 Long Title Text', [[sg.Text('Long title')]]),
]], tab_location='topleft', selected_title_color='white', selected_background_color='blue')

tg2 = sg.TabGroup([tabs('Bottom')], tab_location='bottom')
tg3 = sg.TabGroup([tabs('L', 3)], tab_location='lefttop')
tg4 = sg.TabGroup([tabs('R', 3)], tab_location='righttop')

tg5 = sg.TabGroup([tabs('Color')], title_color='navy', tab_background_color='light blue',
                  selected_title_color='yellow', selected_background_color='maroon',
                  background_color='light grey', focus_color='red')

tg6 = sg.TabGroup([tabs('Style')], font=('Courier', 12, 'bold'),
                  border_width=6, tab_border_width=6, pad=(20, 20))

tg7 = sg.TabGroup([[
    sg.Tab('Just-Right', [[sg.Text('right-justified content')], [sg.Button('Btn')]], element_justification='right'),
    sg.Tab('Img', [[sg.Text('Tab with emoji image title')]], image_source=sg.EMOJI_BASE64_HAPPY_JOY),
    sg.Tab('Hidden', [[sg.Text('never shown')]], visible=False),
    sg.Tab('Wide', [[sg.Text('Fixed size group 420x140')]]),
]], size=(420, 140))

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column([
        [sg.Text('1 original 8-tab group, topleft, selected colors:')],
        [tg1],
        [sg.Text('2 tab_location=bottom:')],
        [tg2],
        [sg.Text('3 lefttop:'), tg3, sg.Text('4 righttop:'), tg4],
    ], vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column([
        [sg.Text('5 full color set (title/tab bg/selected/group bg/focus):')],
        [tg5],
        [sg.Text('6 Courier bold font, border_width=6, tab_border_width=6, pad 20:')],
        [tg6],
        [sg.Text('7 Tab params: element_justification, image title, visible=False, size=(420,140):')],
        [tg7],
     ], vertical_alignment='top')],
]

window = sg.Window('SNAP 16 - TabGroup/Tab All Params (7 groups)', layout,
                   finalize=True, resizable=True, keep_on_top=True)
snap_window(window, 'output/screenshots/SNAP_16_tabgroup_all_params.png')
window.close()
