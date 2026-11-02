"""
SNAPSHOT TEST 17b - Menu.update() (3) + ButtonMenu.update() (4) = 7
variants, non-interactive.

Menu signature: update(menu_definition, visible). ButtonMenu signature:
update(menu_definition, visible, image_source, image_size,
image_subsample, image_zoom, button_text) - exact optional-image kwargs
vary by version, so only menu_definition, visible, and button_text are
exercised; if button_text raises a TypeError on your build, that's a
finding to note.

Menu covered: menu_definition replaced (bar shows File2/Help2), visible
False (bar gone), no-arg no-op - the window-level menu bar can only
exist once per window, so each Menu variant is its OWN small window
snapshotted separately. ButtonMenu covered: menu_definition replaced
(dropdown content - resting visual unchanged, smoke), button_text
changed, visible round trip, no-arg no-op.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import os
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

OUT = 'output/screenshots'

# ---------- Menu: one small window per variant ----------
MENU1 = [['File', ['Open', 'Save']], ['Help', ['About']]]
MENU2 = [['File2', ['New']], ['Help2', ['Docs']]]

menu_variants = [
    ('1_def_replaced', 'M1: menu_definition replaced (File2/Help2)',
     lambda w: w['-MENU-'].update(menu_definition=MENU2)),
    ('2_hidden', 'M2: visible=False (no menu bar)',
     lambda w: w['-MENU-'].update(visible=False)),
    ('3_noop', 'M3: update() no args (File/Help kept)',
     lambda w: w['-MENU-'].update()),
]

for suffix, label, do_update in menu_variants:
    layout = [[sg.Menu(MENU1, key='-MENU-')],
              [sg.Text(label, size=(45, 1))]]
    w = sg.Window(f'SNAP 17 Menu {suffix}', layout,
                  finalize=True, resizable=True, keep_on_top=True)
    do_update(w)
    w.refresh()
    snap_window(w, os.path.join(OUT, f'SNAP_17_menu_update_{suffix}.png'))
    w.close()

# ---------- ButtonMenu: normal multi-variant window ----------
BM_DEF = ['', ['Choice 1', 'Choice 2']]
BM_DEF2 = ['', ['New A', 'New B', 'New C']]

layout = [
    [sg.Text('ButtonMenu.update() - 4 variants', font=('Helvetica', 14, 'bold'))],
    [sg.Text('B1 menu_definition replaced (smoke)'), sg.ButtonMenu('B1 menu', BM_DEF, key='-BM1-')],
    [sg.Text('B2 button_text changed'), sg.ButtonMenu('BEFORE', BM_DEF, key='-BM2-')],
    [sg.Text('B3 update() no args'), sg.ButtonMenu('unchanged', BM_DEF, key='-BM3-')],
    [sg.Text('B4 visible False->True ->'), sg.ButtonMenu('restored', BM_DEF, key='-BM4-'), sg.Text('<-')],
]

window = sg.Window('SNAP 17 - ButtonMenu.update() (4)', layout,
                   finalize=True, resizable=True, keep_on_top=True)

window['-BM1-'].update(menu_definition=BM_DEF2)                                 # B1
window['-BM2-'].update(button_text='AFTER')                                     # B2
window['-BM3-'].update()                                                        # B3
window['-BM4-'].update(visible=False)                                           # B4
window['-BM4-'].update(visible=True)

window.refresh()
snap_window(window, os.path.join(OUT, 'SNAP_17_buttonmenu_update.png'))
window.close()
