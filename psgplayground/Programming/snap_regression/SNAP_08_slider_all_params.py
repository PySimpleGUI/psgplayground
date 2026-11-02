"""
SNAPSHOT TEST 8 - Slider Element (24 variants), non-interactive.

Parameter list verified against the PySimpleGUI 6.3.2 source. Original
variants 1-18 kept with identical parameters (reflowed into columns);
19-24 appended. Covered: range (int/float/negative), default_value,
resolution, tick_interval (horizontal AND vertical), orientation,
disable_number_display, border_width, relief (sunken/raised/ridge/
flat), disabled, size/s, font, background/text/trough colors, pad/p,
tooltip, expand_x. NOT covered: change_submits/enable_events
(behavioral - kept from original as smoke test), visible (would just be
a gap), key/k/setting/metadata.

APPEND ONLY - never renumber existing variants, or baselines break.
"""
import PySimpleGUI as sg
from screenshot_utils import snap_window

sg.theme('Dark Blue 3')   # pinned - PySimpleGUI default; do not change or baselines break

header = "Slider Element - 24 parameter variants (verified against 6.3.2 source)"

def HS(key, **kwargs):
    kw = dict(range=(0, 100), default_value=50, orientation='h', key=key)
    kw.update(kwargs)
    return sg.Slider(**kw)

col_a = [
    [sg.Text('1 Horizontal 0-100 res1'), HS('-SL1-')],
    [sg.Text('2 res10 tick25'), HS('-SL2-', resolution=10, tick_interval=25)],
    [sg.Text('4 disable_number_display'), HS('-SL4-', disable_number_display=True)],
    [sg.Text('5 Custom trough/colors'), HS('-SL5-', trough_color='orange', background_color='black', text_color='white')],
    [sg.Text('6 Sunken relief thick border'), HS('-SL6-', relief=sg.RELIEF_SUNKEN, border_width=5)],
    [sg.Text('7 Disabled'), HS('-SL7-', disabled=True)],
    [sg.Text('8 Tooltip'), HS('-SL8-', tooltip='Slider tooltip!')],
    [sg.Text('9 Float range res 0.1'), HS('-SL9-', range=(0.0, 10.0), default_value=5.0, resolution=0.1)],
    [sg.Text('10 Large range 0-1000'), HS('-SL10-', range=(0, 1000), default_value=500)],
]

col_b = [
    [sg.Text('11 Raised relief'), HS('-SL11-', relief=sg.RELIEF_RAISED)],
    [sg.Text('12 Ridge relief'), HS('-SL12-', relief=sg.RELIEF_RIDGE)],
    [sg.Text('13 enable_events'), HS('-SL13-', enable_events=True)],
    [sg.Text('14 Bold font'), HS('-SL14-', font=('Helvetica', 12, 'bold'))],
    [sg.Text('15 pad=(20,20)'), HS('-SL15-', pad=(20, 20))],
    [sg.Text('16 Small size 10,10'), HS('-SL16-', size=(10, 10))],
    [sg.Text('17 Wide size 40,20'), HS('-SL17-', size=(40, 20))],
    [sg.Text('18 Negative range -50 to 50'), HS('-SL18-', range=(-50, 50), default_value=0)],
    [sg.Text('19 relief flat + border 5'), HS('-SL19-', relief=sg.RELIEF_FLAT, border_width=5)],
    [sg.Text('20 s= alias + p= alias'), HS('-SL20-', s=(25, 15), p=((40, 5), (15, 0)))],
    [sg.Text('21 expand_x=True'), HS('-SL21-', expand_x=True)],
]

col_v = [
    [sg.Text('--- Verticals ---', font=('Helvetica', 11, 'bold'))],
    [sg.Text('3 Vert -10..10'), sg.Slider(range=(-10, 10), default_value=0, orientation='v', key='-SL3-'),
     sg.Text('22 Vert tick5'), sg.Slider(range=(0, 20), default_value=10, tick_interval=5, orientation='v', key='-SL22-'),
     sg.Text('23 Vert colors'), sg.Slider(range=(0, 100), default_value=50, orientation='v',
                                          trough_color='light blue', background_color='navy', text_color='yellow', key='-SL23-'),
     sg.Text('24 Vert no number'), sg.Slider(range=(0, 100), default_value=75, orientation='v',
                                             disable_number_display=True, size=(8, 15), key='-SL24-')],
]

layout = [
    [sg.Text(header, font=('Helvetica', 14, 'bold'))],
    [sg.Column(col_a, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_b, vertical_alignment='top'),
     sg.VerticalSeparator(),
     sg.Column(col_v, vertical_alignment='top')],
]

window = sg.Window('SNAP 08 - Slider Element All Params (24)', layout,
                   finalize=True, resizable=True, keep_on_top=True)
snap_window(window, 'output/screenshots/SNAP_08_slider_all_params.png')
window.close()
