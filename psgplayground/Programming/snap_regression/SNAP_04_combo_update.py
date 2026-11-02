"""
SNAPSHOT TEST 4b - Combo.update() (20 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
value (in list, NOT in list, cleared with ''), values (replace list,
replace + value, replace-alone clears the shown value), set_to_index,
disabled (True and re-enable), readonly (set and clear), font, size,
text_color, background_color, visible (hide and hide->restore), plus
no-arg update as a no-op and sequential updates (last wins).
select=True is a parameter smoke test only - selection highlight needs
focus to render, so the window uses use_default_focus=False and it just
must not error.

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically.

NOTE: variant 6 documents known behavior - update(values=...) WITHOUT
a value clears the displayed text; the snapshot should show it empty.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Combo.update() - 20 variants (verified against 6.3.2 source)"

FRUIT = ['Apple', 'Banana', 'Cherry', 'Date', 'Elderberry']
VEG = ['Asparagus', 'Broccoli', 'Carrot']

col_a = [
    [sg.Text('--- value, values, index ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 value in list'), sg.Combo(FRUIT, default_value='Apple', key='-C1-')],
    [sg.Text('2 value NOT in list'), sg.Combo(FRUIT, default_value='Apple', key='-C2-')],
    [sg.Text('3 value cleared with empty string'), sg.Combo(FRUIT, default_value='Cherry', key='-C3-')],
    [sg.Text('4 values replaced (shows Carrot)'), sg.Combo(FRUIT, default_value='Apple', key='-C4-')],
    [sg.Text('5 values + value together'), sg.Combo(FRUIT, default_value='Apple', key='-C5-')],
    [sg.Text('6 values alone clears shown text'), sg.Combo(FRUIT, default_value='Apple', key='-C6-'), sg.Text('<- empty')],
    [sg.Text('7 set_to_index=2 (Cherry)'), sg.Combo(FRUIT, default_value='Apple', key='-C7-')],
    [sg.Text('8 update() no args'), sg.Combo(FRUIT, default_value='Banana', key='-C8-')],
    [sg.Text('9 sequential, last wins'), sg.Combo(FRUIT, default_value='Apple', key='-C9-')],
    [sg.Text('10 select=True (smoke)'), sg.Combo(FRUIT, default_value='Date', key='-C10-')],
]

col_b = [
    [sg.Text('--- state, style, visibility ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('11 disabled=True [ref v]'), sg.Combo(FRUIT, default_value='Apple', text_color='red', key='-C11-')],
    [sg.Text('   reference'), sg.Combo(FRUIT, default_value='Apple', text_color='red', disabled=True)],
    [sg.Text('12 disabled True->False (re-enabled)'), sg.Combo(FRUIT, default_value='Apple', text_color='red', disabled=True, key='-C12-')],
    [sg.Text('13 readonly=True [ref v]'), sg.Combo(FRUIT, default_value='Banana', text_color='red', key='-C13-')],
    [sg.Text('   reference'), sg.Combo(FRUIT, default_value='Banana', text_color='red', readonly=True)],
    [sg.Text('14 readonly True->False'), sg.Combo(FRUIT, default_value='Banana', readonly=True, key='-C14-')],
    [sg.Text('15 font Courier 14 [ref v]'), sg.Combo(FRUIT, default_value='Cherry', key='-C15-')],
    [sg.Text('   reference'), sg.Combo(FRUIT, default_value='Cherry', font=('Courier', 14))],
    [sg.Text('16 size=(30,1) wide'), sg.Combo(FRUIT, default_value='Date', size=(8, 1), key='-C16-')],
    [sg.Text('17 text_color red [ref v]'), sg.Combo(FRUIT, default_value='Apple', key='-C17-')],
    [sg.Text('   reference'), sg.Combo(FRUIT, default_value='Apple', text_color='red')],
    [sg.Text('18 both colors lime/black [ref v]'), sg.Combo(FRUIT, default_value='Apple', key='-C18-')],
    [sg.Text('   reference'), sg.Combo(FRUIT, default_value='Apple', text_color='lime', background_color='black')],
    [sg.Text('19 visible=False ->'), sg.Combo(FRUIT, default_value='Apple', key='-C19-'), sg.Text('<-')],
    [sg.Text('20 visible False->True ->'), sg.Combo(FRUIT, default_value='Apple', key='-C20-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 04 - Combo.update() (20)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-C1-'].update(value='Elderberry')                                       # 1
window['-C2-'].update(value='Custom typed text')                                # 2
window['-C3-'].update(value='')                                                 # 3
window['-C4-'].update(values=VEG, value='Carrot')                               # 4
window['-C5-'].update(values=VEG, value='Broccoli')                             # 5
window['-C6-'].update(values=VEG)                                               # 6  no value -> empty
window['-C7-'].update(set_to_index=2)                                           # 7
window['-C8-'].update()                                                         # 8
window['-C9-'].update(value='Banana')                                           # 9
window['-C9-'].update(value='Date')                                             #    last wins
window['-C10-'].update(select=True)                                             # 10
window['-C11-'].update(disabled=True)                                           # 11
window['-C12-'].update(disabled=False)                                          # 12
window['-C13-'].update(readonly=True)                                           # 13
window['-C14-'].update(readonly=True)                                           # 14
window['-C14-'].update(readonly=False)
window['-C15-'].update(font=('Courier', 14))                                    # 15
window['-C16-'].update(size=(30, 1))                                            # 16
window['-C17-'].update(text_color='red')                                        # 17
window['-C18-'].update(text_color='lime', background_color='black')             # 18
window['-C19-'].update(visible=False)                                           # 19
window['-C20-'].update(visible=False)                                           # 20
window['-C20-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_04_combo_update.png')
window.close()
