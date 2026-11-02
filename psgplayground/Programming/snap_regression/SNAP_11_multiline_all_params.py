"""
SNAPSHOT TEST 11 - Multiline Element (30 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
default_text, size/s, disabled, autoscroll, border_width, background/
text colors, horizontal_scroll, wrap_lines, justification, no_scrollbar,
all seven sbar_* params, font, pad/p, tooltip, expand_x/expand_y,
rstrip, visible, write_only. Deliberately NOT covered (no deterministic
resting-state visual): focus (blinking caret = flaky diffs),
selected_text_color/selected_background_color (needs a focused
selection), enter_submits/change_submits/enable_events/do_not_clear/
auto_refresh/reroute_*/echo_stdout_stderr (behavioral only), key/k/
setting/metadata (no visual; k= used as API smoke test).

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Multiline Element - 30 parameter variants (verified against 6.3.2 source)"

LONG = chr(10).join(f'Line {i}' for i in range(20))
WIDE = 'This is a long line of text meant to scroll horizontally when wrap is off.'

col_a = [
    [sg.Text('--- Basics, Colors, Fonts ---', font=('Helvetica', 11, 'bold'))],
    [sg.Multiline('1: Plain editable', size=(38, 3), key='-M1-')],
    [sg.Multiline('2: Disabled', size=(38, 3), disabled=True, key='-M2-')],
    [sg.Multiline('3: Custom colors black/lime', size=(38, 3), background_color='black', text_color='lime', key='-M3-')],
    [sg.Multiline('4: Bold font', size=(38, 3), font=('Helvetica', 12, 'bold'), key='-M4-')],
    [sg.Multiline('5: Courier italic', size=(38, 3), font=('Courier', 11, 'italic'), key='-M5-')],
    [sg.Multiline('6: Large 16pt font', size=(30, 2), font=('Helvetica', 16), key='-M6-')],
    [sg.Multiline('7: Thick border 6', size=(38, 3), border_width=6, key='-M7-')],
    [sg.Multiline('8: border_width=0', size=(38, 3), border_width=0, key='-M8-')],
    [sg.Multiline('9: Tooltip (hover)', size=(38, 3), tooltip='Multiline tooltip!', key='-M9-')],
    [sg.Multiline('10: write_only=True', size=(38, 3), write_only=True, key='-M10-')],
]

col_b = [
    [sg.Text('--- Size, Wrap, Justification ---', font=('Helvetica', 11, 'bold'))],
    [sg.Multiline(WIDE, size=(38, 3), wrap_lines=False, horizontal_scroll=True, key='-M11-')],
    [sg.Multiline(WIDE, size=(38, 3), wrap_lines=True, key='-M12-')],
    [sg.Multiline('13: s= size alias', s=(38, 2), key='-M13-')],
    [sg.Multiline('14: size=25 as bare int', size=25, key='-M14-')],
    [sg.Multiline('15: tall size 38,6\n' + LONG, size=(38, 6), key='-M15-')],
    [sg.Multiline('16: justification=left\nsecond line', size=(38, 3), justification='left', key='-M16-')],
    [sg.Multiline('17: justification=center\nsecond line', size=(38, 3), justification='center', key='-M17-')],
    [sg.Multiline('18: justification=right\nsecond line', size=(38, 3), justification='right', key='-M18-')],
    [sg.Multiline('19: rstrip=False keeps trailing blank lines\n\n\n', size=(38, 5), rstrip=False, key='-M19-')],
    [sg.Multiline('20: autoscroll=True (appended text below is visible)\n' + LONG, size=(38, 4), autoscroll=True, key='-M20-')],
]

col_c = [
    [sg.Text('--- Scrollbars, Pad, Expand ---', font=('Helvetica', 11, 'bold'))],
    [sg.Multiline('21: no_scrollbar=True\n' + LONG, size=(38, 3), no_scrollbar=True, key='-M21-')],
    [sg.Multiline('22: default scrollbar\n' + LONG, size=(38, 3), key='-M22-')],
    [sg.Multiline('23: sbar trough+arrow orange\n' + LONG, size=(38, 3), sbar_trough_color='orange', sbar_arrow_color='orange', key='-M23-')],
    [sg.Multiline('24: sbar_background_color navy\n' + LONG, size=(38, 3), sbar_background_color='navy', key='-M24-')],
    [sg.Multiline('25: sbar_width=30 arrow_width=30\n' + LONG, size=(38, 3), sbar_width=30, sbar_arrow_width=30, key='-M25-')],
    [sg.Multiline('26: sbar_frame_color red, relief solid\n' + LONG, size=(38, 3), sbar_frame_color='red', sbar_relief='solid', key='-M26-')],
    [sg.Multiline('27: pad=(30,15)', size=(30, 2), pad=(30, 15), key='-M27-')],
    [sg.Multiline('28: p= alias ((40,5),(15,0))', size=(30, 2), p=((40, 5), (15, 0)), key='-M28-')],
    [sg.Multiline('29: expand_x=True', size=(20, 2), expand_x=True, key='-M29-')],
    [sg.Text('30: visible=False between arrows ->'), sg.Multiline('hidden', size=(15, 2), visible=False, k='-M30-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 11 - Multiline Element All Params (30)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)
# Trigger the autoscroll path so variant 20 shows its bottom line
window['-M20-'].update('\n<-- autoscrolled to bottom', append=True)
snap_window(window, 'output/screenshots/SNAP_11_multiline_all_params.png')
window.close()
