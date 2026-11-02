"""
SNAPSHOT TEST 6b - Checkbox.update() (15) + Radio.update() (15) = 30
variants, non-interactive.

Parameter lists verified against the PySimpleGUI 6.3.2 source.
Checkbox covered: value (check, uncheck, sequential toggle last wins),
text, text_color, background_color, checkbox_color, disabled (True,
True while checked, re-enable), visible (hide and hide->restore),
no-arg no-op, text+value+colors combo.
Radio covered: value=True (select, and stealing selection from a
sibling in the same group), value=False (deselect self, and no-op on
an unselected sibling), text, text_color, background_color,
circle_color, disabled (True, True while selected, re-enable),
visible (hide and hide->restore), no-arg no-op.

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref->] sit next to a reference element constructed
directly in the target state - the pair should render identically.

Radio group ids: each variant uses its own group (RG1, RG2, ...) so
variants stay independent; group-interaction variants R2/R3/R4 place
two radios of the SAME group on one row on purpose.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Checkbox.update()(15) + Radio.update()(15) - 30 variants (verified against 6.3.2 source)"

col_cb = [
    [sg.Text('--- Checkbox.update() ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('CB1 value=True [ref->]'), sg.Checkbox('updated', key='-CB1-'), sg.Checkbox('constructed', default=True)],
    [sg.Text('CB2 value=False [ref->]'), sg.Checkbox('updated', default=True, key='-CB2-'), sg.Checkbox('constructed')],
    [sg.Text('CB3 toggle F->T->F, last wins'), sg.Checkbox('ends unchecked', key='-CB3-')],
    [sg.Text('CB4 text changed'), sg.Checkbox('BEFORE', key='-CB4-')],
    [sg.Text('CB5 text keeps checked state'), sg.Checkbox('BEFORE', default=True, key='-CB5-'), sg.Text('<- still checked')],
    [sg.Text('CB6 update() no args'), sg.Checkbox('unchanged', default=True, key='-CB6-')],
    [sg.Text('CB7 text+value+colors combo'), sg.Checkbox('BEFORE', key='-CB7-')],
    [sg.Text('CB8 text_color red [ref->]'), sg.Checkbox('updated', key='-CB8-'), sg.Checkbox('constructed', text_color='red')],
    [sg.Text('CB9 background_color purple [ref->]'), sg.Checkbox('updated', text_color='white', key='-CB9-'),
     sg.Checkbox('constructed', text_color='white', background_color='purple')],
    [sg.Text('CB10 checkbox_color orange [ref->]'), sg.Checkbox('updated', default=True, key='-CB10-'),
     sg.Checkbox('constructed', default=True, checkbox_color='orange')],
    [sg.Text('CB11 disabled=True [ref->]'), sg.Checkbox('updated', text_color='red', key='-CB11-'), sg.Checkbox('constructed', text_color='red', disabled=True)],
    [sg.Text('CB12 disabled + checked [ref->]'), sg.Checkbox('updated', default=True, text_color='red', key='-CB12-'),
     sg.Checkbox('constructed', default=True, text_color='red', disabled=True)],
    [sg.Text('CB13 disabled True->False (re-enabled)'), sg.Checkbox('enabled again', disabled=True, key='-CB13-')],
    [sg.Text('CB14 visible=False ->'), sg.Checkbox('hidden', key='-CB14-'), sg.Text('<-')],
    [sg.Text('CB15 visible False->True ->'), sg.Checkbox('restored', key='-CB15-'), sg.Text('<-')],
]

col_r = [
    [sg.Text('--- Radio.update() ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('R1 value=True selects [ref->]'), sg.Radio('updated', 'RG1', key='-R1-'), sg.Radio('constructed', 'RG1X', default=True)],
    [sg.Text('R2 value=True steals from sibling'), sg.Radio('now selected', 'RG2', key='-R2-'),
     sg.Radio('was selected', 'RG2', default=True)],
    [sg.Text('R3 value=False deselects self'), sg.Radio('deselected', 'RG3', default=True, key='-R3-'),
     sg.Radio('sibling', 'RG3'), sg.Text('<- none selected')],
    [sg.Text('R4 value=False on UNselected'), sg.Radio('stays off', 'RG4', key='-R4-'),
     sg.Radio('stays selected', 'RG4', default=True), sg.Text('<- kept')],
    [sg.Text('R5 text changed'), sg.Radio('BEFORE', 'RG5', key='-R5-')],
    [sg.Text('R6 text keeps selected state'), sg.Radio('BEFORE', 'RG6', default=True, key='-R6-'), sg.Text('<- still selected')],
    [sg.Text('R7 update() no args'), sg.Radio('unchanged', 'RG7', default=True, key='-R7-')],
    [sg.Text('R8 text_color red [ref->]'), sg.Radio('updated', 'RG8', key='-R8-'), sg.Radio('constructed', 'RG8X', text_color='red')],
    [sg.Text('R9 background_color maroon [ref->]'), sg.Radio('updated', 'RG9', text_color='white', key='-R9-'),
     sg.Radio('constructed', 'RG9X', text_color='white', background_color='maroon')],
    [sg.Text('R10 circle_color orange [ref->]'), sg.Radio('updated', 'RG10', default=True, key='-R10-'),
     sg.Radio('constructed', 'RG10X', default=True, circle_color='orange')],
    [sg.Text('R11 disabled=True [ref->]'), sg.Radio('updated', 'RG11', text_color='red', key='-R11-'), sg.Radio('constructed', 'RG11X', text_color='red', disabled=True)],
    [sg.Text('R12 disabled + selected [ref->]'), sg.Radio('updated', 'RG12', default=True, text_color='red', key='-R12-'),
     sg.Radio('constructed', 'RG12X', default=True, text_color='red', disabled=True)],
    [sg.Text('R13 disabled True->False (re-enabled)'), sg.Radio('enabled again', 'RG13', disabled=True, key='-R13-')],
    [sg.Text('R14 visible=False ->'), sg.Radio('hidden', 'RG14', key='-R14-'), sg.Text('<-')],
    [sg.Text('R15 visible False->True ->'), sg.Radio('restored', 'RG15', key='-R15-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_cb, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_r, vertical_alignment='top')],
]

window = sg.Window('SNAP 06 - Checkbox/Radio update() (30)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

# ---- perform the updates (the snapshot captures the AFTER state) ----
# Checkboxes
window['-CB1-'].update(value=True)                                              # CB1
window['-CB2-'].update(value=False)                                             # CB2
window['-CB3-'].update(value=True)                                              # CB3
window['-CB3-'].update(value=False)                                             #     last wins
window['-CB4-'].update(text='AFTER')                                            # CB4
window['-CB5-'].update(text='AFTER')                                            # CB5  state untouched
window['-CB6-'].update()                                                        # CB6
window['-CB7-'].update(text='COMBO', value=True,                                # CB7
                       text_color='yellow', background_color='maroon')
window['-CB8-'].update(text_color='red')                                        # CB8
window['-CB9-'].update(background_color='purple')                                 # CB9
window['-CB10-'].update(checkbox_color='orange')                                # CB10
window['-CB11-'].update(disabled=True)                                          # CB11
window['-CB12-'].update(disabled=True)                                          # CB12
window['-CB13-'].update(disabled=False)                                         # CB13
window['-CB14-'].update(visible=False)                                          # CB14
window['-CB15-'].update(visible=False)                                          # CB15
window['-CB15-'].update(visible=True)

# Radios
window['-R1-'].update(value=True)                                               # R1
window['-R2-'].update(value=True)                                               # R2  sibling deselected
window['-R3-'].update(value=False)                                              # R3  group -> none selected
window['-R4-'].update(value=False)                                              # R4  sibling selection kept
window['-R5-'].update(text='AFTER')                                             # R5
window['-R6-'].update(text='AFTER')                                             # R6  state untouched
window['-R7-'].update()                                                         # R7
window['-R8-'].update(text_color='red')                                         # R8
window['-R9-'].update(background_color='maroon')                                # R9
window['-R10-'].update(circle_color='orange')                                   # R10
window['-R11-'].update(disabled=True)                                           # R11
window['-R12-'].update(disabled=True)                                           # R12
window['-R13-'].update(disabled=False)                                          # R13
window['-R14-'].update(visible=False)                                           # R14
window['-R15-'].update(visible=False)                                           # R15
window['-R15-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_06_checkbox_radio_update.png')
window.close()
