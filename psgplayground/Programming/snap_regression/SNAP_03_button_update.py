"""
SNAPSHOT TEST 3b - Button.update() (17 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
text (keyword and positional), button_color (tuple + single string),
disabled (True, False re-enable, BUTTON_DISABLED_MEANS_IGNORE smoke),
disabled_button_color, image_data (set on a text button, and swap),
image_subsample, image_zoom, visible (hide and hide->restore), plus
no-arg update as a no-op and sequential updates (last wins).
NOT covered: image_filename/image_source (same code path as
image_data, needs files on disk).

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically, so
any difference between them is an update() bug, not a theme/platform
difference.

NOTE: variant 8 BUTTON_DISABLED_MEANS_IGNORE is behavioral (clicks are
ignored) - visually it must look IDENTICAL to its enabled reference.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Button.update() - 17 variants (verified against 6.3.2 source)"

BG = (sg.theme_background_color(), sg.theme_background_color())

col_a = [
    [sg.Text('--- text, colors, disabled ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 text keyword'), sg.Button('BEFORE', key='-B1-')],
    [sg.Text('2 text positional'), sg.Button('BEFORE', key='-B2-')],
    [sg.Text('3 button_color tuple [ref->]'), sg.Button('updated', key='-B3-'), sg.Button('constructed', button_color=('white', 'maroon'))],
    [sg.Text('4 button_color single string [ref->]'), sg.Button('updated', key='-B4-'), sg.Button('constructed', button_color='blue')],
    [sg.Text('5 disabled=True [ref->]'), sg.Button('updated', key='-B5-'), sg.Button('constructed', disabled=True)],
    [sg.Text('6 disabled + disabled_button_color [ref->]'), sg.Button('updated', key='-B6-'), sg.Button('constructed', disabled=True, disabled_button_color=('grey', 'black'))],
    [sg.Text('7 disabled True->False (re-enabled)'), sg.Button('enabled again', disabled=True, key='-B7-')],
    [sg.Text('8 DISABLED_MEANS_IGNORE [ref->]'), sg.Button('looks enabled', key='-B8-'), sg.Button('looks enabled')],
    [sg.Text('9 update() no args'), sg.Button('unchanged', key='-B9-')],
]

col_b = [
    [sg.Text('--- images, visibility, combos ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('10 sequential, last wins'), sg.Button('first', key='-B10-')],
    [sg.Text('11 image_data set on text button'), sg.Button('text gone', button_color=BG, key='-B11-')],
    [sg.Text('12 image swapped star->laugh [ref->]'), sg.Button('', image_data=sg.EMOJI_BASE64_GOLD_STAR, button_color=BG, key='-B12-'),
     sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_LAUGH, button_color=BG)],
    [sg.Text('13 image_subsample=2 (half) [ref->]'), sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, button_color=BG, key='-B13-'),
     sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, image_subsample=2, button_color=BG)],
    [sg.Text('14 image_zoom=2 (double) [ref->]'), sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, button_color=BG, key='-B14-'),
     sg.Button('', image_data=sg.EMOJI_BASE64_HAPPY_JOY, image_zoom=2, button_color=BG)],
    [sg.Text('15 visible=False ->'), sg.Button('hidden', key='-B15-'), sg.Text('<-')],
    [sg.Text('16 visible False->True ->'), sg.Button('restored', key='-B16-'), sg.Text('<-')],
    [sg.Text('17 text+color combo [ref->]'), sg.Button('BEFORE', key='-B17-'), sg.Button('AFTER', button_color=('yellow', 'purple'))],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 03 - Button.update() (17)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-B1-'].update(text='AFTER')                                             # 1
window['-B2-'].update('AFTER positional')                                       # 2
window['-B3-'].update(button_color=('white', 'maroon'))                         # 3
window['-B4-'].update(button_color='blue')                                      # 4
window['-B5-'].update(disabled=True)                                            # 5
window['-B6-'].update(disabled=True,                                            # 6
                      disabled_button_color=('grey', 'black'))
window['-B7-'].update(disabled=False)                                           # 7
window['-B8-'].update(disabled=sg.BUTTON_DISABLED_MEANS_IGNORE)                 # 8
window['-B9-'].update()                                                         # 9
window['-B10-'].update(text='second')                                           # 10
window['-B10-'].update(text='third (correct)')
window['-B11-'].update(image_data=sg.EMOJI_BASE64_GOLD_STAR)                    # 11
window['-B12-'].update(image_data=sg.EMOJI_BASE64_HAPPY_LAUGH)                  # 12
window['-B13-'].update(image_data=sg.EMOJI_BASE64_HAPPY_JOY,                    # 13
                       image_subsample=2)
window['-B14-'].update(image_data=sg.EMOJI_BASE64_HAPPY_JOY, image_zoom=2)      # 14
window['-B15-'].update(visible=False)                                           # 15
window['-B16-'].update(visible=False)                                           # 16
window['-B16-'].update(visible=True)
window['-B17-'].update(text='AFTER', button_color=('yellow', 'purple'))         # 17

window.refresh()
snap_window(window, 'output/screenshots/SNAP_03_button_update.png')
window.close()
