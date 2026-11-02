"""
SNAPSHOT TEST 1 - Text Element (66 variants), non-interactive.
Parameter list verified against the PySimpleGUI 6.3.2 source: every
keyword in Text.__init__ is exercised except key/metadata (no visual
effect; k= alias included as an API smoke test).

Expanded from the original 24-variant version. Variants are grouped into
three side-by-side columns (Fonts/Styles, Colors/Justification/Size,
Relief/Border/Pad/Behavior) so everything fits in one window well under
2500x1500.

IMPORTANT: This version renumbers and adds variants, so the screenshot
will NOT match baselines captured with the old 24-variant script. After
adopting this file, re-capture your baseline with the old PySimpleGUI
release before comparing. Going forward, only APPEND new variants to the
end of a column - never renumber or reorder existing ones - so baselines
stay comparable across suite revisions.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Text Element - 66 parameter variants (verified against PySimpleGUI 6.3.2 source)"

col_fonts = [
    [sg.Text('--- Fonts & Styles ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('1 Plain default')],
    [sg.Text('2 Bold', font=('Helvetica', 12, 'bold'))],
    [sg.Text('3 Italic', font=('Helvetica', 12, 'italic'))],
    [sg.Text('4 Underline', font=('Helvetica', 12, 'underline'))],
    [sg.Text('5 Overstrike', font=('Helvetica', 12, 'overstrike'))],
    [sg.Text('6 Bold Italic', font=('Helvetica', 12, 'bold italic'))],
    [sg.Text('7 Bold Underline', font=('Helvetica', 12, 'bold underline'))],
    [sg.Text('8 Italic Overstrike', font=('Helvetica', 12, 'italic overstrike'))],
    [sg.Text('9 All four styles', font=('Helvetica', 12, 'bold italic underline overstrike'))],
    [sg.Text('10 Tiny 7pt', font=('Helvetica', 7))],
    [sg.Text('11 Large 20pt', font=('Helvetica', 20))],
    [sg.Text('12 Huge 32pt', font=('Helvetica', 32))],
    [sg.Text('13 Courier', font=('Courier', 12))],
    [sg.Text('14 Times', font=('Times', 12))],
    [sg.Text('15 Arial', font=('Arial', 12))],
    [sg.Text('16 Font as single string', font='Helvetica 14 bold')],
    [sg.Text('17 Courier bold italic', font=('Courier', 12, 'bold italic'))],
    [sg.Text('18 Unicode: Ünïcödé Ω ≈ → 中文')],
    [sg.Text('19 Integer passed as text:'), sg.Text(12345)],
    [sg.Text('20 Tab\tseparated\ttext')],
]

col_colors = [
    [sg.Text('--- Colors, Justification, Size ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('21 Red text', text_color='red')],
    [sg.Text('22 Green text', text_color='green')],
    [sg.Text('23 Hex text color #8000FF', text_color='#8000FF')],
    [sg.Text('24 Blue on yellow bg', text_color='blue', background_color='yellow')],
    [sg.Text('25 White on navy bg', text_color='white', background_color='navy')],
    [sg.Text('26 Yellow on black bg', text_color='yellow', background_color='black')],
    [sg.Text('27 Hex on hex #00FF88/#222244', text_color='#00FF88', background_color='#222244')],
    [sg.Text('28 Background color only', background_color='light blue')],
    [sg.Text('29 Left justified', justification='left', size=(30, 1))],
    [sg.Text('30 Center justified', justification='center', size=(30, 1))],
    [sg.Text('31 Right justified', justification='right', size=(30, 1))],
    [sg.Text('32 Fixed size 15,2', size=(15, 2))],
    [sg.Text('33 auto_size_text=False size 10,1 gets clipped', auto_size_text=False, size=(10, 1))],
    [sg.Text('34 s= size alias, centered w/ bg', s=(30, 1), justification='center', background_color='light grey')],
    [sg.Text('35 Multiline via \\n\nsecond line\nthird line')],
    [sg.Text('36 Multiline centered\nline two\nlonger third line here', justification='center', size=(30, 3))],
    [sg.Text('37 Multiline right\nline two\nlonger third line here', justification='right', size=(30, 3))],
    [sg.Text('38 Very long single line: ' + 'abcdefghij ' * 8)],
    [sg.Text('', size=(20, 1), background_color='pink'), sg.Text('<- 39 empty string with size + bg')],
    [sg.Text('40 expand_x=True with bg', expand_x=True, background_color='light green')],
]

col_misc = [
    [sg.Text('--- Relief, Border, Pad, Behavior ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('41 Relief SOLID', relief='solid', border_width=3)],
    [sg.Text('42 Relief SUNKEN', relief='sunken', border_width=3)],
    [sg.Text('43 Relief RAISED', relief='raised', border_width=3)],
    [sg.Text('44 Relief RIDGE', relief='ridge', border_width=3)],
    [sg.Text('45 Relief GROOVE', relief='groove', border_width=3)],
    [sg.Text('46 Relief FLAT', relief='flat', border_width=3)],
    [sg.Text('47 SOLID border_width=1', relief='solid', border_width=1)],
    [sg.Text('48 RAISED border_width=8', relief='raised', border_width=8)],
    [sg.Text('49 GROOVE + colors', relief='groove', border_width=5, text_color='white', background_color='maroon')],
    [sg.Text('50 pad=(0,0)', pad=(0, 0), background_color='light yellow')],
    [sg.Text('51 pad=(30,10)', pad=(30, 10), background_color='light yellow')],
    [sg.Text('52 pad=((40,5),(15,0)) asymmetric', pad=((40, 5), (15, 0)), background_color='light yellow')],
    [sg.Text('53 p= pad alias (15,15)', p=(15, 15), background_color='light yellow')],
    [sg.Text('54 Tooltip (hover)', tooltip='Text tooltip!')],
    [sg.Text('55 click_submits=True', click_submits=True, key='-T55-')],
    [sg.Text('56 enable_events=True', enable_events=True, key='-T56-')],
    [sg.Text('57 grab=True (dragging moves window)', grab=True)],
    [sg.Text('58 Right-click menu attached', right_click_menu=['', ['Item A', 'Item B']])],
    [sg.Text('59 visible=False between arrows ->'), sg.Text('59 hidden', visible=False), sg.Text('<-')],
    [sg.Text('60 border_width=5 with no relief', border_width=5)],
    [sg.Text('61 colors=tuple white/green', colors=('white', 'green'))],
    [sg.Text('62 colors=single string red', colors='red')],
    [sg.Text('63 size=30 as bare int', size=30, justification='center', background_color='light grey')],
    [sg.Text('64 pad=20 as bare int', pad=20, background_color='light yellow')],
    [sg.Text('65 k= key alias', k='-T65-')],
    [sg.Text('66 expand_y=True ->', background_color='light blue', expand_y=True),
     sg.Text('tall\nneighbor\nrow', background_color='light grey')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_fonts, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_colors, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_misc, vertical_alignment='top')],
]

window = sg.Window('SNAP 01 - Text Element All Params (66)', layout, finalize=True, resizable=True)
snap_window(window, 'output/screenshots/SNAP_01_text_all_params.png')
window.close()
