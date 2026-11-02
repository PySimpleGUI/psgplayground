"""
SNAPSHOT TEST 5b - Listbox.update() (14 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Covered:
values (replace list, replace clears prior selection, non-string items,
sequential last wins), set_to_index (int, list of ints in MULTIPLE
mode, replacing a prior selection), scroll_to_index, select_mode
(smoke - mode itself has no resting visual), disabled (True and
re-enable), visible (hide and hide->restore), and no-arg update as a
no-op.

Pattern: each element is CREATED in a "before" state, then update() is
called after finalize, so the snapshot captures the "after" state.
Variants marked [ref v] sit above a reference element constructed
directly in the target state - the pair should render identically.

NOTE: PySimpleGUI creates listboxes with exportselection off, so
selection highlights in multiple listboxes persist simultaneously in
one screenshot. Unfocused selections may render with the "inactive"
highlight color - both members of a ref pair are unfocused, so pairs
still match.

Small listboxes use size=(14, 4) so scroll_to_index has room to work.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Listbox.update() - 14 variants (verified against 6.3.2 source)"

DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr']
SZ = (14, 4)

col_a = [
    [sg.Text('--- values, indexes, scrolling ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 values replaced (months)'), sg.Listbox(DAYS, size=SZ, key='-L1-')],
    [sg.Text('2 values clears prior selection'), sg.Listbox(DAYS, default_values=['Tue'], size=SZ, key='-L2-'), sg.Text('<- none selected')],
    [sg.Text('3 values non-string ints'), sg.Listbox(DAYS, size=SZ, key='-L3-')],
    [sg.Text('4 sequential, last wins'), sg.Listbox(DAYS, size=SZ, key='-L4-'), sg.Text('<- months, not ints')],
    [sg.Text('5 set_to_index=2 (Wed) [ref v]'), sg.Listbox(DAYS, size=SZ, key='-L5-')],
    [sg.Text('   reference'), sg.Listbox(DAYS, default_values=['Wed'], size=SZ)],
    [sg.Text('6 set_to_index=[1,3] MULTIPLE [ref v]'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, size=SZ, key='-L6-')],
    [sg.Text('   reference'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, default_values=['Tue', 'Thu'], size=SZ)],
    [sg.Text('7 set_to_index replaces selection'), sg.Listbox(DAYS, default_values=['Mon'], size=SZ, key='-L7-'), sg.Text('<- Fri only')],
]

col_b = [
    [sg.Text('--- scrolling, state, visibility ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('8 scroll_to_index=6 (Sun visible)'), sg.Listbox(DAYS, size=SZ, key='-L8-')],
    [sg.Text('9 select_mode EXTENDED (smoke)'), sg.Listbox(DAYS, select_mode=sg.LISTBOX_SELECT_MODE_SINGLE, size=SZ, key='-L9-')],
    [sg.Text('10 disabled=True [ref v]'), sg.Listbox(DAYS, text_color='red', size=SZ, key='-L10-')],
    [sg.Text('   reference'), sg.Listbox(DAYS, text_color='red', disabled=True, size=SZ)],
    [sg.Text('11 disabled True->False (re-enabled)'), sg.Listbox(DAYS, text_color='red', disabled=True, size=SZ, key='-L11-')],
    [sg.Text('12 update() no args'), sg.Listbox(DAYS, default_values=['Sat'], size=SZ, key='-L12-'), sg.Text('<- Sat kept')],
    [sg.Text('13 visible=False ->'), sg.Listbox(DAYS, size=SZ, key='-L13-'), sg.Text('<-')],
    [sg.Text('14 visible False->True ->'), sg.Listbox(DAYS, size=SZ, key='-L14-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 05 - Listbox.update() (14)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

# ---- perform the updates (the snapshot captures the AFTER state) ----
window['-L1-'].update(values=MONTHS)                                            # 1
window['-L2-'].update(values=MONTHS)                                            # 2  Tue selection gone
window['-L3-'].update(values=[1, 22, 333, 4444])                                # 3
window['-L4-'].update(values=[9, 8, 7])                                         # 4
window['-L4-'].update(values=MONTHS)                                            #    last wins
window['-L5-'].update(set_to_index=2)                                           # 5
window['-L6-'].update(set_to_index=[1, 3])                                      # 6
window['-L7-'].update(set_to_index=4, scroll_to_index=4)                        # 7  Mon -> Fri (+scroll)
window['-L8-'].update(scroll_to_index=6)                                        # 8
window['-L9-'].update(select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED)              # 9
window['-L10-'].update(disabled=True)                                           # 10
window['-L11-'].update(disabled=False)                                          # 11
window['-L12-'].update()                                                        # 12
window['-L13-'].update(visible=False)                                           # 13
window['-L14-'].update(visible=False)                                           # 14
window['-L14-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_05_listbox_update.png')
window.close()
