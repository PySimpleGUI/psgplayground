"""
SNAPSHOT TEST 2b - Input.update() (22 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.1 source. Covered:
value, disabled (both use_readonly_for_disable modes, plus re-enable),
readonly (set and clear), text_color, background_color, font,
password_char (set and clear), paste, visible (hide and hide->restore),
and no-arg update as a no-op. COLOR_SYSTEM_DEFAULT ignore path included
(the 6.3.1 changelog fix). select and move_cursor_to are parameter
smoke tests only - selection highlight and the caret need focus to
render, and a blinking caret is flaky in screenshots, so the window is
created with use_default_focus=False and those two just must not error.

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Input.update() - 22 variants (verified against 6.3.1 source)"

col_a = [
    [sg.Text('--- value, colors, font, password ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 value'), sg.Input('before', key='-I1-')],
    [sg.Text('2 value int'), sg.Input('before', key='-I2-')],
    [sg.Text('3 value replaces placeholder'), sg.Input(placeholder='placeholder gone', key='-I3-')],
    [sg.Text('4 update() no args'), sg.Input('unchanged', key='-I4-')],
    [sg.Text('5 text_color red [ref v]'), sg.Input('updated', key='-I5-')],
    [sg.Text('   reference'), sg.Input('constructed', text_color='red')],
    [sg.Text('6 both colors lime/black [ref v]'), sg.Input('updated', key='-I6-')],
    [sg.Text('   reference'), sg.Input('constructed', text_color='lime', background_color='black')],
    [sg.Text('7 COLOR_SYSTEM_DEFAULT ignored'), sg.Input('stays lime on black', text_color='lime', background_color='black', key='-I7-')],
    [sg.Text('8 font Courier 14 [ref v]'), sg.Input('updated', key='-I8-')],
    [sg.Text('   reference'), sg.Input('constructed', font=('Courier', 14))],
    [sg.Text('9 password_char * set'), sg.Input('secret', key='-I9-')],
    [sg.Text('10 password_char cleared'), sg.Input('now visible', password_char='*', key='-I10-')],
]

col_b = [
    [sg.Text('--- state, paste, visibility ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('11 disabled=True (readonly style)'), sg.Input('disabled after update', key='-I11-')],
    [sg.Text('12 disabled=True + dis/ro colors'), sg.Input('navy/yellow when disabled',
                                                           disabled_readonly_background_color='navy',
                                                           disabled_readonly_text_color='yellow', key='-I12-')],
    [sg.Text('13 disabled=True, readonly off'), sg.Input('true tk disabled', use_readonly_for_disable=False, key='-I13-')],
    [sg.Text('14 disabled False (re-enabled)'), sg.Input('enabled again', disabled=True, key='-I14-')],
    [sg.Text('15 readonly=True'), sg.Input('readonly after update', key='-I15-')],
    [sg.Text('16 readonly True->False'), sg.Input('writable again', key='-I16-')],
    [sg.Text('17 paste=True appends'), sg.Input('', key='-I17-')],
    [sg.Text('18 select=True (smoke)'), sg.Input('select me', key='-I18-')],
    [sg.Text('19 move_cursor_to=0 (smoke)'), sg.Input('cursor to start', key='-I19-')],
    [sg.Text('20 visible=False ->'), sg.Input('hidden', size=(10, 1), key='-I20-'), sg.Text('<-')],
    [sg.Text('21 visible False->True ->'), sg.Input('restored', size=(10, 1), key='-I21-'), sg.Text('<-')],
    [sg.Text('22 value+colors+font combo'), sg.Input('before', key='-I22-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 02 - Input.update() (22)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-I1-'].update(value='updated value')                                    # 1
window['-I2-'].update(value=12345)                                              # 2
window['-I3-'].update(value='value replaced placeholder')                       # 3
window['-I4-'].update()                                                         # 4
window['-I5-'].update(text_color='red')                                         # 5
window['-I6-'].update(text_color='lime', background_color='black')              # 6
window['-I7-'].update(text_color=sg.COLOR_SYSTEM_DEFAULT,                       # 7
                      background_color=sg.COLOR_SYSTEM_DEFAULT)
window['-I8-'].update(font=('Courier', 14))                                     # 8
window['-I9-'].update(password_char='*')                                        # 9
window['-I10-'].update(password_char='')                                        # 10
window['-I11-'].update(disabled=True)                                           # 11
window['-I12-'].update(disabled=True)                                           # 12
window['-I13-'].update(disabled=True)                                           # 13
window['-I14-'].update(disabled=False)                                          # 14
window['-I15-'].update(readonly=True)                                           # 15
window['-I16-'].update(readonly=True)                                           # 16
window['-I16-'].update(readonly=False)
window['-I17-'].update(value='Hello')                                           # 17  cursor lands at end
window['-I17-'].update(value=' World', paste=True)                              #     -> 'Hello World'
window['-I18-'].update(select=True)                                             # 18
window['-I19-'].update(move_cursor_to=0)                                        # 19
window['-I20-'].update(visible=False)                                           # 20
window['-I21-'].update(visible=False)                                           # 21
window['-I21-'].update(visible=True)
window['-I22-'].update(value='COMBO', text_color='yellow',                      # 22
                       background_color='maroon', font=('Courier', 12, 'bold'))

window.refresh()
snap_window(window, 'output/screenshots/SNAP_02_input_update.png')
window.close()
