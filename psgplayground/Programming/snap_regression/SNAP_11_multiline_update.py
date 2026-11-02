"""
SNAPSHOT TEST 11b - Multiline.update() (14 variants), non-interactive.

Signature: update(value, disabled, append, font, text_color,
background_color, text_color_for_value, background_color_for_value,
visible, autoscroll, justification). Covered: value (replace,
multi-line, non-string), append=True (twice, proving accumulation),
per-insert colors via *_for_value (mixed-color content in one box),
font, text_color, background_color [ref pairs], justification,
autoscroll=True with overflow content, disabled [ref, red text so the
gray-out shows], visible round trip, no-arg no-op.

Pattern: created "before", update() after finalize, snapshot = "after".
[ref v] refs sit below their updated element.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Multiline.update() - 14 variants"

SZ = (28, 3)

def ML(txt, key=None, **kwargs):
    kw = dict(size=SZ)
    if key is not None:
        kw['key'] = key
    kw.update(kwargs)
    return sg.Multiline(txt, **kw)

col_a = [
    [sg.Text('--- value & append ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 value replaced'), ML('BEFORE', '-M1-')],
    [sg.Text('2 value multi-line'), ML('BEFORE', '-M2-')],
    [sg.Text('3 value non-string int'), ML('BEFORE', '-M3-')],
    [sg.Text('4 append twice (3 lines total)'), ML('line 1\n', '-M4-')],
    [sg.Text('5 per-insert colors (red then lime)'), ML('', '-M5-')],
    [sg.Text('6 update() no args'), ML('unchanged', '-M6-')],
    [sg.Text('7 autoscroll: last line visible'), ML('', '-M7-')],
]

col_b = [
    [sg.Text('--- style, state, visibility ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('8 font Courier 12 [ref v]'), ML('updated', '-M8-')],
    [sg.Text('   reference'), ML('constructed', font=('Courier', 12))],
    [sg.Text('9 text_color red [ref v]'), ML('updated', '-M9-')],
    [sg.Text('   reference'), ML('constructed', text_color='red')],
    [sg.Text('10 background_color purple [ref v]'), ML('updated', '-M10-', text_color='white')],
    [sg.Text('   reference'), ML('constructed', text_color='white', background_color='purple')],
    [sg.Text('11 justification right'), ML('', '-M11-')],
    [sg.Text('12 disabled=True [ref v]'), ML('updated', '-M12-', text_color='red')],
    [sg.Text('   reference'), ML('constructed', text_color='red', disabled=True)],
    [sg.Text('13 visible=False ->'), ML('hidden', '-M13-'), sg.Text('<-')],
    [sg.Text('14 visible False->True ->'), ML('restored', '-M14-'), sg.Text('<-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top')],
]

window = sg.Window('SNAP 11 - Multiline.update() (14)', layout,
                   finalize=True, resizable=True, keep_on_top=True, use_default_focus=False)

window['-M1-'].update(value='AFTER')                                            # 1
window['-M2-'].update(value='line one\nline two\nline three')                   # 2
window['-M3-'].update(value=12345)                                              # 3
window['-M4-'].update('line 2\n', append=True)                                  # 4
window['-M4-'].update('line 3', append=True)
window['-M5-'].update('red text\n', text_color_for_value='red', append=True)    # 5
window['-M5-'].update('lime on black', text_color_for_value='lime',
                      background_color_for_value='black', append=True)
window['-M6-'].update()                                                         # 6
window['-M7-'].update(value='\n'.join(f'row {i}' for i in range(1, 9)),         # 7
                      autoscroll=True)
window['-M8-'].update(font=('Courier', 12))                                     # 8
window['-M9-'].update(text_color='red')                                         # 9
window['-M10-'].update(background_color='purple')                               # 10
window['-M11-'].update(value='pushed right', justification='right')             # 11
window['-M12-'].update(disabled=True)                                           # 12
window['-M13-'].update(visible=False)                                           # 13
window['-M14-'].update(visible=False)                                           # 14
window['-M14-'].update(visible=True)

window.refresh()
snap_window(window, 'output/screenshots/SNAP_11_multiline_update.png')
window.close()
