#!/usr/bin/env python
"""
iD880 Setup - connect to the iD880 thermal printer, line up your two rolls, test, and send printer commands

    1. Connection: USB (pick the iD880 in the Windows printer list) or Ethernet (type its IP address)
    2. Load a roll and click its Test print.  The box should sit right at the paper's edges - use Nudge if it's off.
    3. "Set continuous mode" once, so the printer doesn't look for gaps between labels (both of your rolls are continuous)
    Everything is saved for the other iD880 programs.   Ctrl+Enter sends the commands box.   Esc closes.
    Up/Down, PgUp/PgDn, Home/End scroll the log.

Needs id880_lib.py in the same folder.  USB needs pywin32:  python -m pip install pywin32

CHANGE LOG (newest first, 1 line per change):
2026-11-07  Receipt paper width combo (3-1/8" or 4") - the receipt_width setting in id880_lib
"""
import datetime

import PySimpleGUI as sg
from PIL import Image, ImageDraw

import id880_lib as lib

K_CONNECTION = '-CONNECTION-'
KT_CONNECTION = lambda kind: (K_CONNECTION, kind)
K_PRINTER = '-PRINTER-'
K_REFRESH = '-REFRESH-'
K_IP = '-IP-'
K_PORT = '-PORT-'
K_LANGUAGE = '-LANGUAGE-'
K_SPEED = '-SPEED-'
K_DARKNESS = '-DARKNESS-'
K_RECEIPT_NUDGE = '-RECEIPT NUDGE-'
K_LABEL_NUDGE = '-LABEL NUDGE-'
K_LABEL_WIDTH = '-LABEL WIDTH-'
K_RECEIPT_WIDTH = '-RECEIPT WIDTH-'
K_TEST = '-TEST-'
KT_TEST = lambda media: (K_TEST, media)
K_FEED = '-FEED-'
K_CONTINUOUS = '-CONTINUOUS-'
K_CONFIG = '-CONFIG-'
K_READ_STATUS = '-READ STATUS-'
K_SNIPPET = '-SNIPPET-'
K_INSERT = '-INSERT-'
K_RAW = '-RAW-'
K_SEND = '-SEND-'
K_LOG = '-LOG-'
K_ESCAPE = '-ESCAPE-'

FIELD_SETTINGS = {K_PRINTER: 'win_printer', K_IP: 'ip', K_PORT: 'port', K_LANGUAGE: 'language', K_SPEED: 'speed', K_DARKNESS: 'darkness',
                  K_RECEIPT_NUDGE: 'receipt_nudge', K_LABEL_NUDGE: 'label_nudge', K_LABEL_WIDTH: 'label_width', K_RECEIPT_WIDTH: 'receipt_width'}

# Each tool button's commands in both printer languages
TOOL_COMMANDS = {K_FEED: {'ZPL': f'^XA^MNN^PW{lib.HEAD_DOTS}^LL203^FO0,0^GB8,1,1,W^FS^XZ', 'TSPL': 'FEED 203'},
                 K_CONTINUOUS: {'ZPL': '^XA^MNN^MMT^MTD^JUS^XZ', 'TSPL': 'GAP 0 mm,0 mm\nSET TEAR ON'},
                 K_CONFIG: {'ZPL': '~WC', 'TSPL': 'SELFTEST'},
                 K_READ_STATUS: {'ZPL': '~HS', 'TSPL': '<ESC>!?'}}

SNIPPETS = {'ZPL': {'Configuration page   ~WC': '~WC',
                    'Continuous paper, tear-off, saved   ^MNN ^MMT ^JUS': '^XA^MNN^MMT^JUS^XZ',
                    'Text test': '^XA^PW832^LL180^FO120,50^A0N,48,48^FDHello from PySimpleGUI^FS^XZ',
                    'Barcode test (Code 128)': '^XA^PW832^LL240^FO140,40^BY3^BCN,120,Y,N,N^FD123456789^FS^XZ',
                    'QR code test': '^XA^PW832^LL280^FO300,30^BQN,2,8^FDQA,Hello from the iD880^FS^XZ',
                    'Darkness 20 (0-30)   ~SD': '~SD20',
                    'Host status (Ethernet only)   ~HS': '~HS'},
            'TSPL': {'Self-test page   SELFTEST': 'SELFTEST',
                     'Feed 1 inch   FEED': 'FEED 203',
                     'Text test': 'SIZE 104 mm,23 mm\nGAP 0 mm,0 mm\nCLS\nTEXT 120,50,"3",0,1,1,"Hello from PySimpleGUI"\nPRINT 1,1',
                     'Barcode test (Code 128)': 'SIZE 104 mm,30 mm\nGAP 0 mm,0 mm\nCLS\nBARCODE 140,40,"128",120,1,0,3,3,"123456789"\nPRINT 1,1',
                     'QR code test': 'SIZE 104 mm,35 mm\nGAP 0 mm,0 mm\nCLS\nQRCODE 300,30,L,8,A,0,"Hello from the iD880"\nPRINT 1,1',
                     'Darkness 10 (0-15)   DENSITY': 'DENSITY 10',
                     'Status byte (Ethernet only)   <ESC>!?': '<ESC>!?'}}


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Helpers
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def to_bytes(text, language):
    """Commands typed in the box -> bytes.  TSPL wants CR LF line ends.  <ESC> becomes the escape character."""
    text = text.strip().replace('<ESC>', '\x1b')
    if language == 'TSPL':
        text = '\r\n'.join(text.splitlines()) + '\r\n'
    return text.encode('latin-1', errors='replace')


def test_pattern(media):
    """Box at the paper's edges, a millimeter ruler and a center line"""
    width = lib.media_width(media)
    height = lib.mm_dots(30)
    img = Image.new('L', (width, height), 255)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, width - 1, height - 1], outline=0, width=4)
    numbers = lib.font('Sans', 9)
    for mm in range(width // lib.DOTS_PER_MM + 1):
        x = mm * lib.DOTS_PER_MM
        d.line([(x, 4), (x, 4 + (40 if mm % 10 == 0 else 26 if mm % 5 == 0 else 16))], fill=0, width=2 if mm % 10 == 0 else 1)
        if mm % 10 == 0 and 0 < mm < width // lib.DOTS_PER_MM - 6:
            d.text((x + 4, 28), str(mm), font=numbers, fill=0)
    d.line([(width // 2, 64), (width // 2, height - 8)], fill=0, width=2)
    text = lib.font('Sans', 10, bold=True)
    nudge = lib.setting(lib.NUDGE_SETTING[media])
    lines = [f'{media}  -  {width} dots = {width / lib.DOTS_PER_MM:.0f} mm wide', f'Nudge {nudge}   {lib.setting("language")}   darkness {lib.setting("darkness")}',
             'The box should sit right at the paper edges']
    for i, line in enumerate(lines):
        d.text(((width - text.getlength(line)) / 2, 76 + i * lib.line_height(text)), line, font=text, fill=0)
    return img


def log(window, text, color=None):
    window[K_LOG].print(f'{datetime.datetime.now():%H:%M:%S}  {text}', text_color=color)


def save_fields(values):
    """Save every field (Spin and Input boxes don't always send an event when typed into)"""
    for key, name in FIELD_SETTINGS.items():
        value = values.get(key)
        if value in (None, ''):
            continue
        if key in (K_PORT, K_SPEED, K_DARKNESS, K_RECEIPT_NUDGE, K_LABEL_NUDGE):
            try:
                value = int(float(value))
            except ValueError:
                continue
        lib.save_setting(name, value)


def send(window, data, what):
    try:
        log(window, f'{what}: {lib.send_raw(data)}', '#9CCC65')
    except Exception as e:
        log(window, f'{what} FAILED: {e}', '#FF8A65')


def read_status(window, language):
    request = to_bytes(TOOL_COMMANDS[K_READ_STATUS][language], language)
    try:
        reply = lib.query_network(request)
        log(window, f'Printer answered {len(reply)} bytes: {reply!r}' if reply else 'No answer (the printer may not support this request)', '#9CCC65' if reply else lib.ORANGE)
    except Exception as e:
        log(window, f'Read status FAILED: {e}', '#FF8A65')


# ----------------------------------------------------------------------------------------------------------------------------------------------------
#  Window
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def make_window(printers):
    sg.theme(lib.THEME)
    usb = lib.setting('connection') != 'network'
    language = lib.setting('language')
    hint = dict(font=lib.SMALL_FONT, text_color=lib.HINT_COLOR)
    usb_row = [sg.Radio('USB  -  Windows printer', 'CONNECTION', usb, key=KT_CONNECTION('windows'), enable_events=True, size=(20, 1)),
               sg.Combo(printers, lib.setting('win_printer'), key=K_PRINTER, size=(36, 1), readonly=True, enable_events=True), sg.Button('Refresh', key=K_REFRESH)]
    net_row = [sg.Radio('Ethernet', 'CONNECTION', not usb, key=KT_CONNECTION('network'), enable_events=True, size=(20, 1)),
               sg.Text('IP address'), sg.Input(str(lib.setting('ip')), key=K_IP, size=(16, 1), enable_events=True),
               sg.Text('Port'), sg.Input(str(lib.setting('port')), key=K_PORT, size=(6, 1), enable_events=True)]
    connection = sg.Frame('Connection', [usb_row, net_row], expand_x=True)
    quality_row = [sg.Text('Language'), sg.Combo(['ZPL', 'TSPL'], language, key=K_LANGUAGE, readonly=True, enable_events=True, size=(6, 1)),
                   sg.Text('     Speed'), sg.Combo([2, 3, 4, 5, 6], lib.setting('speed'), key=K_SPEED, readonly=True, enable_events=True, size=(3, 1)), sg.Text('inches / second'),
                   sg.Text('     Darkness'), sg.Slider((0, 30), lib.setting('darkness'), orientation='h', key=K_DARKNESS, enable_events=True, size=(18, 15))]
    quality = sg.Frame('Printer language and print quality', [quality_row], expand_x=True)
    nudges = list(range(-100, 101))
    receipt_row = [sg.Text('Receipt paper', size=(19, 1)), sg.Text('Nudge'),
                   sg.Spin(nudges, initial_value=lib.setting('receipt_nudge'), key=K_RECEIPT_NUDGE, size=(4, 1), enable_events=True), sg.Text('dots'),
                   sg.Button('Test print', key=KT_TEST(lib.RECEIPT)), sg.Text('   Width'),
                   sg.Combo(list(lib.RECEIPT_WIDTHS), lib.setting('receipt_width'), key=K_RECEIPT_WIDTH, readonly=True, enable_events=True, size=(14, 1))]
    label_row = [sg.Text('Continuous labels', size=(19, 1)), sg.Text('Nudge'),
                 sg.Spin(nudges, initial_value=lib.setting('label_nudge'), key=K_LABEL_NUDGE, size=(4, 1), enable_events=True), sg.Text('dots'),
                 sg.Button('Test print', key=KT_TEST(lib.LABELS)), sg.Text('   Width'),
                 sg.Combo(list(lib.LABEL_WIDTHS), lib.setting('label_width'), key=K_LABEL_WIDTH, readonly=True, enable_events=True, size=(14, 1))]
    nudge_hint = [sg.Text('Box cut off on the left: nudge up (+).  Cut off on the right: nudge down (-).   8 dots = 1 mm', **hint)]
    rolls = sg.Frame('Your two rolls  (both continuous)', [receipt_row, label_row, nudge_hint], expand_x=True)
    tool_row = [sg.Button('Set continuous mode  (do once)', key=K_CONTINUOUS, button_color=('white', lib.BLUE)), sg.Button('Feed 1 inch', key=K_FEED),
                sg.Button('Print config page', key=K_CONFIG), sg.Button('Read status  (Ethernet)', key=K_READ_STATUS)]
    tools = sg.Frame('Printer tools', [tool_row], expand_x=True)
    snippet_row = [sg.Combo(list(SNIPPETS[language]), key=K_SNIPPET, readonly=True, size=(46, 1)), sg.Button('Insert', key=K_INSERT)]
    send_row = [sg.Button('Send', key=K_SEND, size=(8, 1), button_color=('white', lib.GREEN)),
                sg.Text('ZPL:  ^XA ... ^XZ        TSPL:  one command per line        Ctrl+Enter sends', **hint)]
    commands = sg.Frame('Send printer commands', [snippet_row, [sg.Multiline('', key=K_RAW, size=(80, 4), font=('Consolas', 10), expand_x=True)], send_row], expand_x=True)
    log_box = sg.Multiline('', key=K_LOG, size=(80, 8), font=('Consolas', 10), disabled=True, autoscroll=True, expand_x=True, expand_y=True)
    layout = [[connection], [quality], [rolls], [tools], [commands], [log_box]]
    window = sg.Window('iD880 Setup', layout, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, finalize=True, resizable=True)
    lib.bind_scroll_keys(window)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-Return>', K_SEND)
    return window


def main():
    printers = lib.list_windows_printers()
    if not lib.setting('win_printer'):
        guess = next((p for p in printers if 'id880' in p.lower() or 'idprt' in p.lower()), '')
        if guess:
            lib.save_setting('win_printer', guess)
    window = make_window(printers)
    log(window, f'Settings file: {sg.user_settings_filename()}')
    if not printers:
        log(window, 'No Windows printers found  (not on Windows, or pywin32 missing:  python -m pip install pywin32)', lib.ORANGE)
    log(window, lib.printer_summary())
    while True:
        event, values = window.read()
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        if event == K_ESCAPE:
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70,10))
            continue
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
            continue
        elif lib.is_scroll_key(event):
            lib.scroll_with_key(window, K_LOG, event)
            continue
        save_fields(values)
        language = values[K_LANGUAGE]
        if isinstance(event, tuple) and event[0] == K_CONNECTION:
            lib.save_setting('connection', event[1])
            log(window, lib.printer_summary())
        elif event in (K_PRINTER, K_LANGUAGE):
            log(window, lib.printer_summary())
            if event == K_LANGUAGE:
                window[K_SNIPPET].update(values=list(SNIPPETS[language]))
        elif event == K_REFRESH:
            printers = lib.list_windows_printers()
            window[K_PRINTER].update(values=printers, value=lib.setting('win_printer'))
            log(window, f'{len(printers)} Windows printers found')
        elif isinstance(event, tuple) and event[0] == K_TEST:
            send(window, lib.build_job(lib.to_1bit(test_pattern(event[1])), event[1]), f'Test print, {event[1].lower()}')
        elif event in (K_FEED, K_CONTINUOUS, K_CONFIG):
            send(window, to_bytes(TOOL_COMMANDS[event][language], language), window[event].get_text().strip())
        elif event == K_READ_STATUS:
            read_status(window, language)
        elif event == K_INSERT and values[K_SNIPPET]:
            window[K_RAW].update(SNIPPETS[language][values[K_SNIPPET]])
        elif event == K_SEND:
            if values[K_RAW].strip():
                send(window, to_bytes(values[K_RAW], language), f'Sent your {language} commands')
    window.close()


if __name__ == '__main__':
    main()
