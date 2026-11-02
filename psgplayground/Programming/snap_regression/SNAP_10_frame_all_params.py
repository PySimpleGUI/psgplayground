"""
SNAPSHOT TEST 10 - Frame Element (18 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-10 kept with identical parameters (reflowed into columns);
11-18 appended. Covered: title, layout, title_color, background_color,
title_location (bottom, top-left, top-right, bottom-right), relief
(raised/sunken/ridge/groove), border_width, border_width_no_relief,
border_color, size/s, font (title font), pad/p, expand_x,
element_justification, vertical_alignment, grab, tooltip, visible.
NOT covered: enable_events (behavioral), right_click_menu, key/k/
metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Frame Element - 18 parameter variants (verified against 6.3.2 source)"

def inner():
    return [[sg.Text('Inner Text')], [sg.Button('Inner Btn')]]

col_a = [
    [sg.Frame('1 Default', inner())],
    [sg.Frame('2 Blue title', inner(), title_color='blue')],
    [sg.Frame('3 Grey bg', inner(), background_color='light grey')],
    [sg.Frame('4 Title bottom', inner(), title_location=sg.TITLE_LOCATION_BOTTOM)],
    [sg.Frame('5 Raised', inner(), relief=sg.RELIEF_RAISED)],
    [sg.Frame('6 Sunken', inner(), relief=sg.RELIEF_SUNKEN)],
]

col_b = [
    [sg.Frame('7 Ridge thick', inner(), relief=sg.RELIEF_RIDGE, border_width=6)],
    [sg.Frame('8 Purple border no relief', inner(), border_width_no_relief=4, border_color='purple')],
    [sg.Frame('9 Fixed size', inner(), size=(200, 80))],
    [sg.Frame('10 Right justified', inner(), element_justification='right')],
    [sg.Frame('11 Title font Courier bold', inner(), font=('Courier', 12, 'bold'))],
    [sg.Frame('12 Groove border 4', inner(), relief=sg.RELIEF_GROOVE, border_width=4)],
]

col_c = [
    [sg.Frame('13 Title top-right', inner(), title_location=sg.TITLE_LOCATION_TOP_RIGHT)],
    [sg.Frame('14 Title bottom-right', inner(), title_location=sg.TITLE_LOCATION_BOTTOM_RIGHT)],
    [sg.Frame('15 s= alias (220,90)', inner(), s=(220, 90))],
    [sg.Frame('16 pad p= asymmetric', inner(), p=((40, 5), (15, 0)), background_color='light yellow')],
    [sg.Frame('17 expand_x pad 20,10', inner(), expand_x=True, pad=(20, 10), background_color='light green')],
    [sg.Frame('18 grab + tooltip', inner(), grab=True, tooltip='Frame tooltip!'),
     sg.Frame('hidden', inner(), visible=False, k='-F19-'), sg.Text('<- hidden frame'),
     sg.Frame('valign bottom', [[sg.Text('B')]], vertical_alignment='bottom')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_c, vertical_alignment='top')],
]

window = sg.Window('SNAP 10 - Frame Element All Params (18)', layout,
                   finalize=True, resizable=True, keep_on_top=True)
snap_window(window, 'output/screenshots/SNAP_10_frame_all_params.png')
window.close()
