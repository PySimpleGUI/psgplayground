"""
SNAPSHOT TEST 18 - WINDOW LEVEL (30 scenarios), non-interactive.

Opens 30 separate windows ONE AT A TIME, each demonstrating a distinct
Window()-level parameter combination, screenshotted to its own PNG.

Parameter list verified against the PySimpleGUI 6.3.2 source. Added in
this version (21-30): default_element_size, auto_size_buttons=False +
default_button_element_size, text_justification, border_depth,
progress_bar_color, ttk_theme + use_ttk_buttons, use_custom_titlebar +
titlebar_background_color/text_color/font, window-wide sbar_* styling,
watermark, scaling (kept LAST - tk scaling can leak into later windows).

Deliberately NOT covered: transparent_color (whatever is behind the
window shows through, so the capture depends on the desktop = flaky),
icon/titlebar_icon (OS titlebar not in capture area), auto_close,
force_toplevel, grab_anywhere_using_control, debugger_enabled,
enable_*_event flags, repeating_timer_ms, auto_save_location,
print_event_values, metadata (all behavioral, no resting visual).

APPEND ONLY - never renumber existing scenarios, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

SCENARIOS = [
    ("01_default", "1: Default window (baseline)", {"finalize": True}, []),
    ("02_no_titlebar", "2: no_titlebar=True, grab_anywhere=True", {"no_titlebar": True, "grab_anywhere": True, "finalize": True}, []),
    ("03_resizable_min_size", "3: resizable=True, use_min_size=True", {"resizable": True, "use_min_size": True, "finalize": True}, []),
    ("04_keep_on_top", "4: keep_on_top=True", {"keep_on_top": True, "finalize": True}, []),
    ("05_alpha_channel", "5: alpha_channel=0.6", {"alpha_channel": 0.6, "finalize": True}, []),
    ("06_disable_close", "6: disable_close=True", {"disable_close": True, "finalize": True}, []),
    ("07_disable_minimize", "7: disable_minimize=True", {"disable_minimize": True, "finalize": True}, []),
    ("08_location_anchor_center", "8: location=(700,400), location_anchor='center'", {"location": (700, 400), "location_anchor": 'center', "finalize": True}, []),
    ("09_relative_location", "9: relative_location=(100,100)", {"relative_location": (100, 100), "finalize": True}, []),
    ("10_custom_size", "10: size=(500,300)", {"size": (500, 300), "finalize": True}, []),
    ("11_margins", "11: margins=(50,50)", {"margins": (50, 50), "finalize": True}, []),
    ("12_element_padding", "12: element_padding=(30,20)", {"element_padding": (30, 20), "finalize": True}, []),
    ("13_button_color", "13: button_color=('white','purple') window-wide", {"button_color": ('white', 'purple'), "finalize": True},
     [[sg.Button('Sample Btn 1')], [sg.Button('Sample Btn 2')]]),
    ("14_font", "14: font=('Courier', 14) window-wide", {"font": ('Courier', 14), "finalize": True}, []),
    ("15_background_color", "15: background_color='light green'", {"background_color": 'light green', "finalize": True}, []),
    ("16_return_keyboard_events", "16: return_keyboard_events=True", {"return_keyboard_events": True, "finalize": True},
     [[sg.Text('Key events enabled (no typing during snapshot)')]]),
    ("17_right_click_menu_colors", "17: right_click_menu black bg / white text",
     {"right_click_menu": ['', ['Item A', 'Item B', 'Item C']], "right_click_menu_background_color": 'black',
      "right_click_menu_text_color": 'white', "finalize": True}, []),
    ("18_modal", "18: modal=True", {"modal": True, "finalize": True}, []),
    ("19_element_justification_center", "19: element_justification='center'", {"element_justification": 'center', "finalize": True}, []),
    ("20_tooltip_colors", "20: tooltip_background_color/text_color window-wide",
     {"tooltip_background_color": 'black', "tooltip_text_color": 'white', "tooltip_time": 200, "finalize": True},
     [[sg.Button('Hover Me', tooltip='Window-wide tooltip style')]]),
    # ---- Added in expanded version - verified against 6.3.2 signature ----
    ("21_default_element_size", "21: default_element_size=(30,2)", {"default_element_size": (30, 2), "finalize": True},
     [[sg.Input('input inherits 30x2')], [sg.Combo(['a', 'b'], default_value='combo too')]]),
    ("22_default_button_size", "22: auto_size_buttons=False, default_button_element_size=(25,3)",
     {"auto_size_buttons": False, "default_button_element_size": (25, 3), "finalize": True},
     [[sg.Button('A')], [sg.Button('Much Longer Button Text')]]),
    ("23_text_justification", "23: text_justification='right' window-wide", {"text_justification": 'right', "finalize": True},
     [[sg.Text('short', size=(35, 1))], [sg.Text('a much longer text line', size=(35, 1))]]),
    ("24_border_depth", "24: border_depth=5 window-wide", {"border_depth": 5, "finalize": True},
     [[sg.Input('deep border input')], [sg.Multiline('deep border multiline', size=(30, 2))]]),
    ("25_progress_bar_color", "25: progress_bar_color=('red','black') window-wide",
     {"progress_bar_color": ('red', 'black'), "finalize": True},
     [[sg.ProgressBar(100, orientation='h', size=(25, 20), key='-PB25-')]]),
    ("26_ttk_theme", "26: ttk_theme='clam', use_ttk_buttons=True", {"ttk_theme": 'clam', "use_ttk_buttons": True, "finalize": True},
     [[sg.Button('TTK Button 1'), sg.Button('TTK Button 2')],
      [sg.Combo(['ttk', 'styled'], default_value='ttk'), sg.Checkbox('check')]]),
    ("27_custom_titlebar", "27: use_custom_titlebar + titlebar colors/font",
     {"use_custom_titlebar": True, "titlebar_background_color": 'purple', "titlebar_text_color": 'yellow',
      "titlebar_font": ('Courier', 12, 'bold'), "finalize": True}, []),
    ("28_window_sbar_colors", "28: window-wide sbar_* styling",
     {"sbar_trough_color": 'orange', "sbar_arrow_color": 'navy', "sbar_width": 25, "sbar_arrow_width": 25,
      "sbar_relief": 'solid', "finalize": True},
     [[sg.Multiline(chr(10).join(f'Line {i}' for i in range(30)), size=(30, 4))],
      [sg.Column([[sg.Text(f'Row {i}')] for i in range(12)], scrollable=True, vertical_scroll_only=True, size=(150, 80))]]),
    ("29_watermark", "29: watermark=True (version stamped in window)", {"watermark": True, "finalize": True}, []),
    # scaling LAST: tk scaling is interpreter-global and can leak into
    # any window created after it in the same process.
    ("30_scaling", "30: scaling=1.5 (everything larger)", {"scaling": 1.5, "finalize": True},
     [[sg.Button('Scaled Button')], [sg.Input('scaled input')]]),
]

for name, desc, window_kwargs, extra_rows in SCENARIOS:
    layout = [[sg.Text(desc, font=('Helvetica', 12, 'bold'))]] + extra_rows + [[sg.Text('(non-interactive snapshot)')]]
    window = sg.Window(f'Scenario: {desc}', layout, **window_kwargs)
    if name == '25_progress_bar_color':
        window['-PB25-'].update(50)
    snap_window(window, f'output/screenshots/SNAP_18_window_{name}.png')
    window.close()

print('All 30 window-level scenarios captured.')
