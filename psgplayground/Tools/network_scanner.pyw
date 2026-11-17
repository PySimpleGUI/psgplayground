"""
network_scanner.pyw - Network Scanner: every device on your local network, as tiles or as a list.

It finds every device on the local subnet and shows, for each one: a name (the best of mDNS / DNS / NetBIOS / UPnP), its .local name, the IP
address, the MAC address and its maker, the ping time, what it offers (open ports, mDNS services), its UPnP server, and a guessed kind of device -
every kind with its own color AND its name.

How it finds them (Python's standard library, plus PySimpleGUI and Pillow):
    a ping sweep of the subnet, in parallel          -> the devices that answer, and how fast
    the ARP table (arp -a)                           -> MAC addresses, and devices that ignore ping
    reverse DNS                                      -> the names your router hands out
    an mDNS name question sent to each device        -> names like "EPSON-ET-8550.local"
    the mDNS service list (multicast)                -> _ipp, _airplay, _googlecast ...
    an SSDP / UPnP search (multicast)                -> routers, TVs, speakers
    a NetBIOS name question (Windows)                -> Windows computer names
    a quick try of common ports                      -> what each device offers
    an online MAC maker lookup (api.macvendors.com)  -> the maker - only while Vendor lookup is on

Using it
    Scan (F5) looks at the subnet in the box (your own /24 to start).  Devices appear as they are found; Stop ends a scan early.
    Tiles / List (Ctrl+1 / Ctrl+2): tiles that fill the window, or one line per device - click a column heading to sort by it, again to reverse.
    Click a device to pick it: everything found about it shows in the Details panel on the right (Ctrl+D shows / hides the panel;
    Enter or a double-click shows it).  Open, on a tile or in Details, opens the device's web page.  Ctrl+C copies the picked device's IP.
    The colored kinds above the tiles: click one to hide / show that kind, double-click one to see only that kind.  All / None at the start
    show or hide every kind - None, then a click on Printer, shows just the printers.  Remembered for next time.
    Search (Ctrl+F): a name, IP, MAC, maker, service or kind - the devices narrow down as you type.  Esc clears it.
    Diagnose saves what the network commands say (ipconfig, route, ping, arp, firewall) - for a scan that finds nothing.

Keys and mouse
    The mouse wheel anywhere over the devices, the scroll bar, Up / Down / Left / Right (move the pick), PgUp / PgDn, Home / End.
    Ctrl + mouse wheel: bigger / smaller tiles and rows (Small, Medium, Large, Huge) around the mouse; Ctrl+= / Ctrl+- / Ctrl+0 from the keys.
    Back: the mouse's Back button, Alt+Left or the < at the top left - to the device, view or search you had before (Alt+Right: forward again).
    F5 scans.  Esc clears the search, then closes.  Right-click anywhere: all of the above, plus Theme (32 of them), Brightness, Accent,
    What's new, Edit Me, Version.

--demo   a made-up home network instead of a scan - for screenshots, or to try it: 192.168.1.x addresses and made-up names, nothing goes out
         on the network, and its settings live in a temporary file that is removed when it closes.

What it writes, and where
    Its settings: network_scanner.json in PySimpleGUI's settings folder (right-click > Version shows the full path).
    network_scanner_diag.txt next to this file - only when you click Diagnose.
    network_scanner_hang.txt next to this file - only if it ever stops answering: what each part of it was doing then, so it can be fixed.
    (While it runs, a small file in the temp folder stands ready to catch that report; it is removed when it closes.)
    Nothing else.  It needs Pillow to draw; if Pillow is missing it offers to install it (pip) and says so first.

New versions: it watches its own file.  Right-click > New versions decides what happens when a newer copy is saved over it - by default it only
says so in the right-click menu.

CHANGE LOG (newest first, 1 line per change):
2026-11-17  v3.0.3  Fixed: the arrow after Open showed as an empty box on Windows.  It is drawn now, not a letter of the font (Segoe UI has no ↗).
2026-11-16  v3.0.2  Fixed: switching to List, picking a device or changing the size could freeze the window for a long time on Windows.
                    The right-click menu is remade only when it changes, and lining up its sub-menu arrows measures each label once, with one font
                    (a new font each time made Windows search every installed font for the check mark).  The stuck-window report waits 10 s, not 20.
2026-11-16  v3.0.1  Fixed: the window could stop answering during a scan or while the makers were looked up.
                    New: All and None at the start of the kinds, and a double-click on a kind shows only that kind.  The bottom line now
                    says when the maker lookup is done.  If it ever stops answering again, it saves a report (network_scanner_hang.txt)
2026-11-16  v3.0.0  A new look: tiles that fill the window and move into place as you resize it, and Ctrl + wheel sets their size.
                    Also new: a list view you can sort, a Details panel, search, scrolling from anywhere, 32 themes with Brightness and Accent,
                    Back and Forward.  Now one file named network_scanner.pyw (was network_scanner_v2.pyw); needs Python 3.8 or newer
2026-11-01  v2.1  --demo: a made-up network (every kind of device) instead of a scan - nothing of yours ends up in a screenshot; version shown
"""
import base64
import faulthandler
import gc
import io
import ipaddress
import math
import os
import queue
import re
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.request
import uuid
import webbrowser
from concurrent.futures import ThreadPoolExecutor
import tkinter as tk
import tkinter.font
from tkinter import colorchooser

import PySimpleGUI as sg

try:
    from PIL import Image, ImageDraw, ImageFont
    try:
        from PIL import ImageTk
    except ImportError:                                           # Pillow without its tk part: pictures go over as PNG instead
        ImageTk = None
except ImportError:                                               # main() offers to install Pillow
    Image = ImageDraw = ImageFont = ImageTk = None

APP_NAME = 'Network Scanner'
VERSION = '3.0.3'
DEMO = '--demo' in sys.argv                                       # made-up devices, nothing is scanned - see the top of the file
DEMO_SUBNET = '192.168.1.0/24'
ICON = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAQEUlEQVR42u2ba5BdVZXHf2vvfe/t++xnnuQBkpAXEEgA8UUsUJEaS+cDLQoiNeMUlI7lCKPOjOVUmylHfOBjHBGVGWcYEyxIOeI4DwWHMoLyEDQQ0gmQkHQkISGP7k6n093nnL3XfDi3O93p9O3udFqganbV/nLvOWfttfba6/XfSxhntNJqN7AhADr42+o5Nxb6Gn2dPdqnPsTCKz0qFTK9SXiq466u4T+vWbPGbdy40Q9f+4mj1uIlfU8U4LxFN1zqCW8HfQPIUpSSEhDklRZAukjRxGDaQTaB+cUA++7fvv2nA+kjbQbWhkkI4PgLyxd/8P0CHwO51BiHakA11BLqKzZELCJmcI3Pqob1ZPu/2N6+IYJWCxv8uAKoqrxfMv99c10u809i3FUAIUSqihcRARVe+Z0/2QiqKIIYsdYYSwh+Cz6+acsLd/+qeiSSMQUwyPyKs667GOd+bMTOSULkqw9ZXlNDgyrB2oxT1URD/JH2HXffOcjj4FN2uNq3862w/Kz3X4LL/MyIzPA+SkTEAYbX3BARERM0eMAam313S8PyvRs773milVbbTrsO1wADbSxfuGsmWX3KiJnpQ+LlNbfrY2qDggnGOJvE8Tu27Vz3wKBNqO5sG7A2qIvvssbN9D5OTsq8HJ8iMqk5ub07cU6VjggEUfVqnHz/vAXXNsK9ARC3hjVuI2uTZWdfe421uXckx9V+tKVIjlv+hMl4AiGTST8ZQqjJOEA8zFaLhnQDZap0xAT13tm6WUlm4HMgf95Kq5VUFe4NyxZd/4Q1mVU+xCNVX4BYUVVMU3aI57w4LCZ1wrUcNKCqvPxyJ8YIhUIdIehJmY+S9KXmiqKh+q6rQ8UhNYQ9CToqIigaEdkz2zvu2udggz9/8fWv99gLQoiCIKOYl4qj8pmluOVlJIY+YtaW38nq7DyOaYTU2B6p+qZt7Tv57rd+xNO/e45CMT9ihwaZbywot117jPMXePAGCcfoWdVGPGMlxP0gZkp0AAkhJM7V5bzruw74igOIg17lnDNJkiQiwy2+oBqo/O1SclfMJHRGmKJBFMqVAg3ZEhmNMePqp3L521bz5stW8pE/+yIP/3ITpVJhxOIU4evX9vKGCyPoMWAVEsXW54kai0iUqSmAidJBRNJAzlwFbV8zKZtykWpghBURIAmYpixuWZnQGYGv2oFESRJfnQlJkhDHY88k8XR29mKt5eZPfYB8PkcIfmj3Yw8zyoELFnhCjyEoqE9nkgSSWKdMZxhbRtWj6IpFi7aXzJLmd5eBFaoBOZm/1/QYYKSmF8hk3JjTGME5S2/vAIvPmc+K886mry/CGDPCUUUJGFMlMYYXmCodQFSDitjmOg0rnORMVqFSy8jU0nBjDFYM3d1HUgXSke+FECiVimQyjoGBGGsNhUIOHcMQ1qIjxp4WOtWTkPFBGpwxGSVV7lMet335Dh595LfU1eVQ1eFEiOOE2bNn0Lb2FhobG1DVk3qBicQGp5uONSZxE0iLxzA3irWGo929PPjgr+np7iGTzYyQuALWCi+8sJtdO19k1qwZ1UxysnSgZxroKHpCwDOZHUFIEk99Q5kbb7yOXz38OLm6kSonRoiimIVnzmPFuYvp6xsgn8+eAh2or58eOo6ppRvEcUzre9/F1a1/xDCtHDJe6fmF/v6YJPGTDouHPEWcTAudKQlgcERRjHOWNBVP9837QBQlQ8p2giV+1dBxU02yjDW8tPcge/e8jLUpce8DDQ1lXnf2vKqxkjE1CAQRHTeXc9aw96VTozN9R8AYkmiA+3/6CIcOdeGcBa3G5gLvu/adzJ7dTBwnI1TSGDNkuVUDAZMyJWaUQ1LSECSOkknTmXYBqCouY1m1eim7d+/D2TSN8CFQX1+ioaGM92HEohQ42nOMOE6YM7cZ1UBndz/dXT3oQA8+X6dghxISqb7j3OTo/GGOABCCcsGFS1h54ZJUV6tLNsZUd1iPZ2wiBB9zy6euIZ/PcuZZcwDl4IFu9nTsIZv/NfbQo8JAL4HsiLB0onSmRwA6vnEa+4xX6zFGKJUc1sCb3nzuiOeamiqcs2Q+cCl3ddy3+6JN369fESf1ekLyMx6dE7VzIkIZXwBGwArUiKpqqZ4qZJyhXEpjdYCenmM8+ustbNvagSrMmtuol1+2Wg7UH+u51b+4u2XlVZm25x8764p922YEMUOB2kRU3PtANuvYv/8wz27dRV0+W1MQtQVgBe2JCZ0xbmYO7YrTdEkVDUoIgTDmxxURwRihXM4MFTTW3fUz7rj9Pva+eJAoTobO+YIFs8MZ37lo96wZxh3o606+sOyKjvNzLZVS3JsbUMWEMIFKvJLNZmioOG77wo95eX8n9Q0lvA+nIICq+dU+z9Fbt1G59VzM7BySAATqijmKWQdqT1oPEIEo8uTrBKkKo+0z3+M7t99HfUOJcqWQ7qhF6QnStzx7ePv8vsPaGbnrG1fO/JOWN82bNe+9dfHhQxTrBJMtjOvmVJWX9x/iti/8hHvX30+pXKjJ/PgaEBTJW+LNR+j60G+xi4rglYDyJbefiuTwQ0HJyMzt6NFjvOWylfzFLVcjAneve4Bv334fc+Y0kyQeVUh8gvapmIpL+Oic7auYWbxx3kUL3lJ6XQvA0xw49O3//p/kyA87ZkneKqoyHiry7NYODuw/TKlcOE1GMChSdITOCP9Q/9AmPK0H8Ck2OEpxnLMcOtTN1e9dg0jq9r71jR/R0FCqhqnQ29tHqVLQjDHou1r2ffLid83443DOwrzL2sPJseg7Bx/t2JA8sz8ud5WOPrZ55gifWKMuWFeXHVftJ+8FgoITpHz88QKZmpXdbLaFlRcsAuDRR9p58cUDVCoFVFPmL1x9Dl/6yoclX65TXzYt801jHSg/6Wrfd8ehR/bsSY4MNGeLWVk6IzELG6JwIMqRAcL4sclEmZ9cHKBVkz4oE7RGgpTQ3FxhzpxmALa2dxDHCcYIUZRQLOb56jc+ysKFswf3ta6D7iNf7PrFzoeO7TpSKeRsEyXp6u4NlF3km2w/e3xOraSA9GkcDqYNmBpKTIa7oRCUQiFLU1Olagc8GWf5m4/fYTduembB3MYmd+hIr55/4SJu/9yfYqzRzzYcKj2ebKEoeQmE07pOc6qQTS1kxjlLT08fBw+m9xXmzm3GWkMIkM06Dh7s4vN/92/4KvM/WPcAv7lnU7F5p2kceKqr3Pvk4cripKmyvG5WZamZUR91RVasVGuFpw+BmrgGDEZ0/jiy7HWY5TnhqFhnOXiwi+3P7+HsRWdw2VsvoKmpQhTFGGMolfL8YP3/suWZnZRKBR5/tJ1sKYM3qs45tM7wtvdcQiCw96WDPPf878VaU017dcoI1OQEIIImaQiaKdWnQRCQc2mAeDIZDKarjz+2lSuvuoSZsxq5+pq38s2v/5C5Z7QwMBBTLhfY8swuQggUS3k0KBnrpPNQD6+/ZBmXXrocg+F3m3agCi0zGgneTxmBmpwAqsy7QplF13yY8oJFaOKJgnDTxcqymUpfPDpAG+6tvFeMgZs/cQ1P/W47D/3yaWbObACEUimfJkghIM7Q2dlDc0s9t375JvL5HBolXLxkMT958B+wOt7eTwgZGv3e8nmtTeRyz4oxLZoW2mS4IQtxzLIP/RXNKy8g7kkw1jCQwMffqJw7WzkWpenCSVekiohSKWURgSPdvbR95p+5798fJokTrDNAKgBV5eJLlvH5L93I0mULUzhiwzP0LWiCVXPRY/GEQuF8PkMUJWMjQ0MYoRU0udLV2v3gE1y5ntL8xcQ9CahHfagiNlpFbFIBnCwlkOrvvccSigVLpb7I1/7xY1x/w5U8cP8TbN2yCwXmzG3miret5vLLV2EzlgCEx35P/PMd+A+3EKIEkiTVSK1tqjo7IyqVAjd/6gM8+ZutVWRIpmADVNEkRnJ51FcTEhmN4Ttnx1xU/4DHh0CpmMEKrLpoCasuWnLymCv2JP/1HNGDO5CsHbL8g4TGopMaPj8KGXryN1sp1jgKk/ICJ82XjGDN+MiQqqWrOyJfZ+nu7KZcKVAq5dP7AFHCgf2dNOzuxTz8e5KOLqSYgYFkqPRljUGMOW3I0GkIhHTITkwEsfns2luob2zAB8Nff/K7PP9sB8uWn4lqYN/LnfTsO8I9l7ydpkIBiplq5DkcO54eBMpNhX1nLYe6j04Isdm580VeX0VsvPd07NrPvpcOoyGgVphZKmOKWcg4CP547KGKs5aenp5pQaCmiAwlp4TYiAi5XIZKfRENgTh47GDV6QQrJzK9CNRpQIZODbEZzNq0WlWqbd2nD4H6f2RoqriAtZaXpgGxGU3HTAudKXkBMULcPz2IzSg78OpDhgRVJePctCA2ozxOxk0nMqRyaiJIFzEdiM2oRGc66GgQZ01GE6R228c4Hz9diI3CH4TO8dvkNjabd9/dJcI2EYuerOQoBrG25scmUp3xPpDJ2DERGyOCFakBtJweOmkmaCSE0O3ofcZUr+FsEjGjRCbG4PuOEh3txuYsGnz6yBAyNNEZqohNhu99N0VsMhk3RM6K4Ug0wOGBfgqZDL4aGwQ9/v7poFO9F6SSwm3PN75w+LBLAwj9uap+XEbg2IqIxUd9bL/3Dpbe8JfkGppAwVioK0CxCBKPUQ+YIGKj1d0/lsR8+omH+eYbr2BuvogHxAuZQo5QzIB149YDJoQMKUHEGpFk40Y2JgJt5tJ57bnuuly7EbswaKIy7E6qiOAH+sk2tFCcM78auQnz65ViNq0NygT6WMZDbIwIvXHMnEKRJfVNJBqQoIS5FShkaoKzk0SGQtpX5M9r376+XdLr8huTZWdf92nn6v4+SfpHXZcXMQQfE+JoyPpGXggTYH44YpPJupqghREhCp5+749/Nw5ICOPjghOgo+CtyVjvowe27lj/DtLr8gi0yfLl7Y4o94wxbvFJu0VOMDhyCtHcRFyVVAWhI4L9ibcm1KCjIAERbOxXbN61/tk22owZ/HR7+4YooB9UDSpDxawTKkMhDM0wyTlRP62AHzSAWjWAfup0VDVxLmeD+k9s3rX+WWi1a1kbqmd9bWil1W7bvv5RH5KbjHEGTIBJXuvkVdowpBo7l8/ESf+d27av/3rrsB7CITVvp13XsMY92fmfT7Q0LN9rbPY91ZvViQzeZ3vttUp5ESTj8jbx/Xdu3b7uxmp3nJ4UGtvIxmQNa1z7jrvvVN//TpS9zuUciKhqoukdNn0185xGeJqkAE3GitjY+4Gbt25fd2Nb2hE7otg2qsTaQUdopdX+ovOe58sN561zhLyIWW5ttk7EmOM9xRPuZPpDtQ8jYsQYJ9ZmTXp89Wfeh6u37lj3H9BmNp7A/DjG/Pg5Wbz4g2dkgl6D4UpVPV9gtogdAxx85YSgGg4h5jngIevNus0v/Ovm4R2xk+0er/7faoY3Ha9ceEPDgAvLrEjZE9SeYiZ5eodFQ0iyJrN50/Z/OTA87IfPylid4wD/B5OnY0YdNH8jAAAAAElFTkSuQmCC'

# --- UPDATE: Restart, and a newer version of this file (program standards, 11-Nov-2026, block 3.1 of 15-Nov) - paste unchanged ---
# Right-click > Restart starts a fresh copy of this file (same arguments) and this one ends.  While it runs, the program watches its own file:
# a NEWER VERSION saved over it counts once it has sat UPDATE_SETTLE seconds unchanged and compiles (a half-saved or broken file never counts).
# Then right-click > New versions decides (remembered, -NEW VERSIONS-; the program sets Update.default for its kind):
#   'auto'  By itself - hidden in the tray at once, showing once the mouse has been off the window UPDATE_QUIET seconds and nothing of it is open
#   'ask'   Ask me first - a small pop-up, Restart now / Later (Later by itself after 30 s); hidden in the tray it goes by itself
#   'menu'  Only say so here - never by itself; the menu reads "Restart - x.y.z is ready"
# Not the internet: the file itself - whatever put the newer copy there (a synced folder, pip, a download).
# Block 3: at each start the program compares its VERSION with the one that last ran on this PC (-RAN VERSION-).  Newer = it was updated - by
# itself, from the menu or by hand.  Update.was holds the old version; update_tag() is the version it was updated from until the user has looked
# (-UPDATED FROM-, kept across restarts) - the program shows an UPDATED tag by its version, and clicking it shows update_news(update_tag()) (the
# change-log lines since then) and calls update_tag_seen().  If this PC already has a card-log folder (a notifications program reads it), one line
# goes into it as well - nothing is created on a PC that doesn't have one.
# Wiring (update_block.md):  main() start: Update.default = 'auto' / 'ask' / 'menu';   menu, just above Exit: *update_menu(tick)
#   each event: if update_event(event): end the loop if Update.restart, else remake the menu
#   timer (every 2-5 s): if update_tick(window, hidden, busy, colors): remake the menu;  if Update.restart: end the loop
#   the very end of main(), after the window, tray icon and sockets are closed:  if Update.restart: restart_self(['--tray'] if hidden else [])
UPDATE_SETTLE = 60
UPDATE_QUIET = 10
UPDATE_CHOICES = (('auto', "By itself, while I'm not using it"), ('ask', 'Ask me first'), ('menu', 'Only say so in this menu'))


class Update:
    default = 'ask'                   # the program's kind: 'auto' widgets + tray apps, 'ask' other programs that run all day, 'menu' open-and-close
    seen = None                       # (mtime of this file when last looked at, when it changed - None while it is the file this copy started from)
    ready = ''                        # a newer VERSION saved over this file (settled, compiles)
    asked = ''                        # the version the pop-up already asked about - not asked again
    away = None                       # when the mouse left the window (for 'auto')
    restart = False                   # set -> the main loop ends, then restart_self()
    was = ''                          # block 3: the version that ran before on this PC, when this start is a newer one ('' = not updated)


def update_mode():
    mode = sg.user_settings_get_entry('-NEW VERSIONS-', Update.default)
    return mode if mode in dict(UPDATE_CHOICES) else Update.default


def update_check():
    """ Returns a newer VERSION the first time one is ready, else ''.  Cheap: one stat() a call, the file is read only after it changed and settled """
    try:
        mtime = os.path.getmtime(os.path.abspath(__file__))
    except OSError:
        return ''
    if Update.seen is None:
        Update.seen = (mtime, None)
        update_noted()                                                    # block 3: the first look - an update since the last run?
    if mtime != Update.seen[0]:
        Update.seen = (mtime, time.time())
        return ''
    if Update.seen[1] is None or time.time() - Update.seen[1] < UPDATE_SETTLE:
        return ''
    Update.seen = (mtime, None)                                           # looked at: wait for the next change
    try:
        with open(os.path.abspath(__file__), encoding='utf-8') as f:
            text = f.read()
        compile(text, __file__, 'exec')
        found = re.search(r"^VERSION = '([0-9.]+)'", text, re.M)
    except (OSError, SyntaxError, ValueError):
        return ''
    newer = found and tuple(int(x) for x in found.group(1).split('.')) > tuple(int(x) for x in VERSION.split('.'))
    if newer and found.group(1) != Update.ready:
        Update.ready = found.group(1)
        return Update.ready
    return ''


def update_noted():
    """ Block 3, once per start: this VERSION against the one that last ran on this PC (-RAN VERSION-).  Newer: Update.was = the old version, the
        UPDATED tag is set, and - only where a card-log folder already exists - one line goes into it.  Never raises """
    try:
        ran_before = bool(sg.user_settings())                             # a settings file with something in it: it ran here before
        last = str(sg.user_settings_get_entry('-RAN VERSION-', '') or '')
        sg.user_settings_set_entry('-RAN VERSION-', VERSION)
        if not last and not ran_before:                                   # its first run on this PC
            return
        if last and tuple(int(x) for x in last.split('.')) >= tuple(int(x) for x in VERSION.split('.')):
            return
        last = last or 'an earlier version'                               # it ran here before block 3 kept the version
        Update.was = last
        if not sg.user_settings_get_entry('-UPDATED FROM-'):              # not looked at yet since an earlier update: keep the oldest
            sg.user_settings_set_entry('-UPDATED FROM-', last)
        import datetime, json, uuid
        name = globals().get('APP_NAME') or os.path.splitext(os.path.basename(__file__))[0]
        new = next((re.sub(r'^\s*\d{4}-\d\d-\d\d\s+v?' + re.escape(VERSION) + r'\s*(Claude:\s*)?', '', line).strip()
                    for line in (globals().get('__doc__') or '').splitlines() if re.match(r'\s*\d{4}-\d\d-\d\d\s+v?' + re.escape(VERSION) + r'\b', line)), '')
        base = sg.DEFAULT_USER_SETTINGS_WIN_PATH if sys.platform.startswith('win') else sg.DEFAULT_USER_SETTINGS_MAC_PATH if sys.platform == 'darwin' \
            else sg.DEFAULT_USER_SETTINGS_LINUX_PATH
        folder = os.path.join(os.path.expanduser(base), 'Notifications')
        if not os.path.isdir(folder):                                     # no notifications program on this PC: nothing is written
            return
        now = datetime.datetime.now()
        line = {'v': 1, 'id': uuid.uuid4().hex[:12], 'at': now.strftime('%Y-%m-%d %H:%M:%S'), 'program': str(name)[:60], 'title': f'Updated to {VERSION}',
                'text': (f'Was {last}.  ' + new[:1].upper() + new[1:])[:2000].strip(), 'click': None, 'private': False}
        with open(os.path.join(folder, f'cards_{now:%Y-%m}.jsonl'), 'a', encoding='utf-8') as f:
            f.write(json.dumps(line, ensure_ascii=False) + '\n')
    except Exception:
        pass


def update_tag():
    """ Block 3: the version this program was updated from, until the user has looked ('' = nothing to show).  The program shows an UPDATED tag """
    return str(sg.user_settings_get_entry('-UPDATED FROM-', '') or '')


def update_tag_seen():
    """ Block 3: the user looked (clicked the tag) - the tag goes away """
    sg.user_settings_set_entry('-UPDATED FROM-', '')


def update_news(since=''):
    """ Block 3: the change-log lines of the versions after since, up to this one, newest first, each 'x.y.z  what changed' (a line that goes on
        is joined on).  since = '' or 'an earlier version': all of them """
    try:
        floor = tuple(int(x) for x in since.split('.'))
    except ValueError:
        floor = ()
    top, out, keep = tuple(int(x) for x in VERSION.split('.')), [], False
    for line in (globals().get('__doc__') or '').splitlines():
        found = re.match(r'\s*\d{4}-\d\d-\d\d\s+v?([0-9]+(?:\.[0-9]+)+)\s+(?:Claude:\s*)?(.*)', line)
        if found:
            ver = tuple(int(x) for x in found.group(1).split('.'))
            keep = floor < ver <= top
            if keep:
                out.append(f'{found.group(1)}  {found.group(2).strip()}')
        elif keep and line.startswith((' ', '\t')) and line.strip():
            out[-1] += ' ' + line.strip()
        else:
            keep = False
    return out


def restart_label():
    """ The right-click item: 'Restart', or 'Restart - 1.2.3 is ready' once a newer version waits """
    return f'Restart  -  {Update.ready} is ready' if Update.ready else 'Restart'


def update_menu(tick=None, indent='    '):
    """ The right-click items to put just above Exit: the New versions sub-menu (its choice ticked) and Restart.  tick(on) = the program's own
        check-mark prefix, so the items line up with its other ones """
    tick = tick or (lambda on: '✓ ' if on else indent)
    mode = update_mode()
    return [f'{indent}New versions', [f'{tick(k == mode)}{text}::-NEW VERSIONS {k}-' for k, text in UPDATE_CHOICES], f'{indent}{restart_label()}::Restart']


def update_event(event):
    """ True when the event was one of this block's: Restart (sets Update.restart) or a New versions choice (saved - remake the menu) """
    key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event
    if key == 'Restart':
        Update.restart = True
        return True
    for k, _ in UPDATE_CHOICES:
        if key == f'-NEW VERSIONS {k}-':
            sg.user_settings_set_entry('-NEW VERSIONS-', k)
            return True
    return False


def mouse_away(window):
    """ True once the mouse has been off the window UPDATE_QUIET seconds in a row """
    try:
        root = window.TKroot
        px, py = root.winfo_pointerxy()
        x, y, w, h = root.winfo_rootx(), root.winfo_rooty(), root.winfo_width(), root.winfo_height()
        inside = x <= px < x + w and y <= py < y + h
    except Exception:
        inside = False
    if inside:
        Update.away = None
        return False
    Update.away = Update.away or time.time()
    return time.time() - Update.away >= UPDATE_QUIET


def update_tick(window, hidden=False, busy=False, colors=('#1e2430', '#e6eaf2', '#2a62a8')):
    """ Call on the timer.  hidden = the window is hidden in the tray;  busy = a dialog, panel or edit of the program is open (nothing happens
        then);  colors = (background, text, button) of the pop-up - the program's own theme.  Sets Update.restart when it is time.
        Returns True when the menu should be remade (a version became ready, or the pop-up was answered Later) """
    new = update_check()
    if not Update.ready or Update.restart:
        return bool(new)
    mode = update_mode()
    if mode == 'menu':
        return bool(new)
    if hidden:
        Update.restart = True
        return False
    quiet = mouse_away(window) and not busy
    if mode == 'auto':
        Update.restart = quiet
        return bool(new)
    if Update.asked != Update.ready and not busy:
        Update.asked = Update.ready                                       # once per version
        update_offer(window, Update.ready, colors)
        return not Update.restart
    return bool(new)


def update_offer(window, new, colors=('#1e2430', '#e6eaf2', '#2a62a8')):
    """ Ask once per version: Restart now / Later (Later by itself after 30 s, so a program never waits long).  Sets Update.restart """
    Update.asked = new
    bg, fg, button = colors
    try:
        x, y = window.current_location()
        spot = (x + 20, y + 20)
    except Exception:
        spot = (None, None)
    name = globals().get('APP_NAME') or os.path.splitext(os.path.basename(__file__))[0]
    answer = sg.popup(f'{name} {new} is here  (you run {VERSION})', 'Restart now to use it?', '(Right-click > New versions: by itself, ask, or only say so)',
                      title='New version', custom_text=('Restart now', 'Later'), keep_on_top=True, auto_close=True, auto_close_duration=30, location=spot,
                      background_color=bg, text_color=fg, button_color=('#ffffff', button), font=('Segoe UI', 11), icon=globals().get('ICON'))
    Update.restart = answer == 'Restart now'


def restart_self(extra=()):
    """ Start this file again with the same arguments (pythonw on Windows - no console).  Call it LAST: after the window, the tray icon and any
        socket this program listens on are closed, so a one-copy-at-a-time program's new copy finds the way clear """
    exe = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    exe = exe if sys.platform.startswith('win') and os.path.isfile(exe) else sys.executable
    args = [a for a in sys.argv[1:] if a != '--tray'] + list(extra)
    subprocess.Popen([exe, os.path.abspath(__file__)] + args, cwd=os.path.dirname(os.path.abspath(__file__)))
# --- end UPDATE ---

# --- BACK: one step back, and forward again (program standards, 13-Nov-2026) - paste unchanged ---
# The mouse's Back button, Alt+Left and the on-screen Back button all send ONE event, K_BACK; the mouse's Forward button and Alt+Right send K_FORWARD.
# A PLACE is what the program is showing: a small dict of the state you MOVED to (view, picked item, open thing, search) - never data.
# KEEP is what travels with a place without being a step of its own (scroll position, a graph's zoom) - restored when you come back to it.
# Wiring (back_block.md):
#   after finalize:            back_bind(window);  back_here(place(), name(), keep())   - the place it opens on (else the first Back has nowhere to go)
#   end of EVERY loop pass:    back_here(place(), name(), keep(), kind)     - kind names a run of small moves ('zoom', 'rows') that is ONE step; else None
#   event K_BACK / K_FORWARD:  got = back_step(-1 / +1, ok)  -> if got: show(*got)  else: say 'Nothing to go back to'
#   after either:              back_button(window)  - greys the on-screen Back button out at the start and names where it goes in its hover hint
BACK_MAX = 50                                                                        # places kept to go back through
BACK_MERGE = 1.5                                                                     # seconds: moves of the same kind closer than this are one step
K_BACK, K_FORWARD = '-BACK-', '-FORWARD-'


class Back:
    here = None                                                                      # [place, name, keep] shown now
    before = []                                                                      # places to go back to, newest last
    after = []                                                                       # places Back has left, for Forward - emptied by a new move
    kind = None                                                                      # kind of the last move, and when it was
    when = 0.0


def back_bind(window):
    """ The mouse's Back / Forward buttons and Alt+Left / Alt+Right, anywhere over the window, send K_BACK / K_FORWARD """
    root = window.TKroot
    x11 = root.tk.call('tk', 'windowingsystem') == 'x11'
    back, forward = ((8,), (9,)) if x11 else ((4, 8), (5, 9))                        # Windows tk 8.6: 4 / 5 (tested 10-Nov); X11: 8 / 9, as 4 / 5 are the wheel

    def press(e):
        if e.num in back:
            window.write_event_value(K_BACK, None)
        elif e.num in forward:
            window.write_event_value(K_FORWARD, None)

    def key(e, event):
        if not e.state & 0x4:                                                        # Ctrl+Alt+arrow belongs to Windows / the graphics driver
            window.write_event_value(event, None)
        return 'break'
    root.bind('<ButtonPress>', press, add='+')
    root.bind('<Alt-Left>', lambda e: key(e, K_BACK), add='+')
    root.bind('<Alt-Right>', lambda e: key(e, K_FORWARD), add='+')


def back_here(place, name='', keep=None, kind=None):
    """ Call at the end of every pass of the event loop.  A place that differs from the one shown is a step: the old one goes on the Back list.
        The same place only refreshes its keep.  A run of moves of the same kind within BACK_MERGE seconds is one step. """
    now = time.monotonic()
    if Back.here is None:
        Back.here = [place, name, keep]
    elif place == Back.here[0]:
        Back.here[1:] = [name, keep]
        return False
    elif kind and kind == Back.kind and now - Back.when < BACK_MERGE:
        Back.here = [place, name, keep]
    else:
        Back.before = (Back.before + [Back.here])[-BACK_MAX:]
        Back.here = [place, name, keep]
        Back.after = []
    Back.kind, Back.when = kind, now
    return True


def back_step(step=-1, ok=None):
    """ One step back (-1) or forward (+1): returns (place, name, keep) to show, or None at the end.  ok(place) False = gone, skipped. """
    take, give = (Back.before, Back.after) if step < 0 else (Back.after, Back.before)
    while take:
        entry = take.pop()
        if ok is None or ok(entry[0]):
            give.append(Back.here)
            Back.here = entry
            Back.kind = None
            return tuple(entry)
    return None


def back_name(step=-1):
    """ The name of the place one step back (-1) or forward (+1), '' when there is none """
    entries = Back.before if step < 0 else Back.after
    return entries[-1][1] if entries else ''


def back_button(window, key=K_BACK):
    """ The on-screen Back button: greyed out when there is nowhere to go back to; its hover hint says where it goes """
    if key in window.key_dict:
        where = back_name(-1)
        window[key].update(disabled=not where)
        window[key].set_tooltip(f'Back to {where}  (Alt+Left, the mouse\'s Back button)' if where else 'Nothing to go back to')
# --- end of BACK ---

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Keys and settings
# ----------------------------------------------------------------------------------------------------------------------------------------------------
K_HEAD, K_MAIN, K_FOOT = '-HEAD-', '-MAIN-', '-FOOT-'             # the three drawn parts: header, devices (+ Details), bottom line
K_SUBNET, K_SEARCH = '-SUBNET-', '-SEARCH-'                       # the two boxes (the subnet's setting keeps 2.1's name)
K_MAIL = '-MAIL-'                                                 # doorbell: there is mail from a worker thread (rung by mail_poll, on the window's thread)
K_REDRAW = '-REDRAW-'                                             # the window changed size: draw everything again
K_TICK = '-TICK-'                                                 # once a second (a tk timer, not a thread): messages that time out, the version check
K_ZOOM = '-ZOOM-'                                                 # Ctrl + mouse wheel: (step, x_root, y_root)
K_RIGHT_PICK = '-RIGHT PICK-'                                     # a right-click on a device picked it - the menu names it
K_KEY = '-KEY-'                                                   # keys: K_KEY + 'Up', K_KEY + 'Return' ...
K_FOUND, K_DONE, K_PHASE, K_VENDOR_UPDATE, K_DIAG_DONE = '-FOUND-', '-DONE-', '-PHASE-', '-VENDOR UPDATE-', '-DIAG DONE-'   # thread -> window
K_VENDOR_DONE = '-VENDOR DONE-'                                   # thread -> window: the online maker lookup has finished
K_EXIT = 'Exit'
M_SCAN, M_STOP, M_DIAG, M_TILES, M_LIST, M_DETAILS, M_VENDOR = '-M SCAN-', '-M STOP-', '-M DIAG-', '-M TILES-', '-M LIST-', '-M DETAILS-', '-M VENDOR-'
M_COPY, M_COPY_ALL, M_OPEN, M_NEWS, M_FIND = '-M COPY-', '-M COPY ALL-', '-M OPEN-', '-M NEWS-', '-M FIND-'
KT_THEME = lambda name: f'-THEME {name}-'
KT_ZOOM_TO = lambda name: f'-ZOOM TO {name}-'
S_THEME, S_VIEW, S_ZOOM, S_DETAILS, S_SORT = '-THEME-', '-VIEW-', '-TILE SIZE-', '-DETAILS-', '-SORT-'
S_HIDDEN, S_VENDOR, S_GEOMETRY = '-HIDDEN KINDS-', '-VENDOR-', '-GEOMETRY-'    # hidden kinds, vendor lookup and the subnet keep 2.1's names

# ----------------------------------------------------------------------------------------------------------------------------------------------------
# The look
# ----------------------------------------------------------------------------------------------------------------------------------------------------
# --- WIDGET THEMES: the same block in every card widget (master copy in modern_widget_recipe.md) - change it in all of them at once ---
# card = background, border = outline, track = gauge track / lines, text = main text, dim = labels.   16 dark first, then 16 light: the Theme menu
# shows them as two columns of color chips.  ForestFloor and CrimsonVelvet come from Mike's dark themes; the other colored darks follow their lead.
THEMES = {'Toybox':        {'card': '#141821', 'border': '#2f3a4e', 'track': '#1e2430', 'text': '#e6eaf2', 'dim': '#8a93a3'},
          'Carbon':        {'card': '#121212', 'border': '#2e2e2e', 'track': '#1f1f1f', 'text': '#e0e0e0', 'dim': '#8c8c8c'},
          'Slate':         {'card': '#2a3140', 'border': '#48526a', 'track': '#363e50', 'text': '#eef1f6', 'dim': '#a3acbd'},
          'CrimsonVelvet': {'card': '#5e0d1f', 'border': '#8f1530', 'track': '#781429', 'text': '#f9d276', 'dim': '#d6a7a0'},
          'Ember':         {'card': '#451f11', 'border': '#773c27', 'track': '#5c2f1e', 'text': '#f1e4df', 'dim': '#bd9f93'},
          'Espresso':      {'card': '#2c2016', 'border': '#594331', 'track': '#423224', 'text': '#f1e7df', 'dim': '#bda693'},
          'Bronze':        {'card': '#48310f', 'border': '#7b5823', 'track': '#60441b', 'text': '#f1eadf', 'dim': '#bdac93'},
          'Olive':         {'card': '#2a3013', 'border': '#545f2b', 'track': '#3e4620', 'text': '#eef1df', 'dim': '#b5bd93'},
          'ForestFloor':   {'card': '#101c0e', 'border': '#2a4424', 'track': '#1b2e18', 'text': '#d0e0c8', 'dim': '#83977d'},
          'Jade':          {'card': '#113124', 'border': '#29614a', 'track': '#1e4836', 'text': '#dff1ea', 'dim': '#93bdac'},
          'Lagoon':        {'card': '#0e3434', 'border': '#236767', 'track': '#1a4c4c', 'text': '#dff1f1', 'dim': '#93bdbd'},
          'Petrol':        {'card': '#0f303e', 'border': '#235a71', 'track': '#1b4456', 'text': '#dfecf1', 'dim': '#93b1bd'},
          'Cobalt':        {'card': '#132949', 'border': '#294a7a', 'track': '#20395f', 'text': '#dfe6f1', 'dim': '#93a4bd'},
          'Indigo':        {'card': '#1e1e48', 'border': '#383876', 'track': '#2c2c5d', 'text': '#dfdff1', 'dim': '#9393bd'},
          'Plum':          {'card': '#341c3f', 'border': '#5a376c', 'track': '#472b54', 'text': '#ebdff1', 'dim': '#af93bd'},
          'Mulberry':      {'card': '#3f1731', 'border': '#6e3057', 'track': '#552544', 'text': '#f1dfea', 'dim': '#bd93ae'},
          'Paper':         {'card': '#f5f7fb', 'border': '#c9d1dc', 'track': '#dadfe8', 'text': '#1b2130', 'dim': '#5c6676'},
          'Fog':           {'card': '#dde2e8', 'border': '#b8c0ca', 'track': '#c5ccd5', 'text': '#1b2028', 'dim': '#545d69'},
          'Stone':         {'card': '#e1dedb', 'border': '#b9b5b1', 'track': '#c5c2be', 'text': '#2b2117', 'dim': '#63574b'},
          'Sand':          {'card': '#e7dfcf', 'border': '#c1b6a4', 'track': '#cbc2b3', 'text': '#2b2417', 'dim': '#675942'},
          'Linen':         {'card': '#f7f2e8', 'border': '#dcd1bd', 'track': '#e4dac9', 'text': '#2b2620', 'dim': '#73685a'},
          'Butter':        {'card': '#fbf5dc', 'border': '#e3d7a6', 'track': '#e8ddb1', 'text': '#2e2a18', 'dim': '#766c4c'},
          'Peach':         {'card': '#fce9df', 'border': '#dfbdaa', 'track': '#e6ccbc', 'text': '#2b1e17', 'dim': '#705d51'},
          'Blush':         {'card': '#faedf0', 'border': '#eccad2', 'track': '#efd1d8', 'text': '#321c22', 'dim': '#80606a'},
          'Rose':          {'card': '#ecd5dd', 'border': '#c7a9b3', 'track': '#d1b8c0', 'text': '#2b171e', 'dim': '#70515c'},
          'Orchid':        {'card': '#f4e5f5', 'border': '#d1b6d3', 'track': '#dbc6dc', 'text': '#2a172b', 'dim': '#6e5170'},
          'Lavender':      {'card': '#f0ecfa', 'border': '#d2c9ec', 'track': '#dad3f0', 'text': '#231e33', 'dim': '#665e80'},
          'Periwinkle':    {'card': '#e3e6f7', 'border': '#b2b7d6', 'track': '#c3c7df', 'text': '#171a2b', 'dim': '#515670'},
          'Sky':           {'card': '#e7f0fa', 'border': '#bdd2ea', 'track': '#c7daee', 'text': '#18222f', 'dim': '#53667d'},
          'Aqua':          {'card': '#ddf2f3', 'border': '#aecfd0', 'track': '#bfd9d9', 'text': '#172a2b', 'dim': '#516f70'},
          'Mint':          {'card': '#e8f5ee', 'border': '#bcdccb', 'track': '#c5e1d2', 'text': '#1b2a22', 'dim': '#557064'},
          'Pistachio':     {'card': '#ebf3dd', 'border': '#c4cfaf', 'track': '#cfd9bf', 'text': '#242b17', 'dim': '#657051'}}
OLD_THEME_NAMES = {'Midnight': 'Carbon', 'VoidBlue': 'Carbon', 'DarkSlate': 'Slate', 'MidnightPurple': 'Plum', 'DeepOceanTeal': 'Lagoon'}   # saved by older versions
# --- end WIDGET THEMES ---

KIND_COLORS = {'This PC': '#3ddc97', 'Gateway': '#c084fc', 'Printer': '#ffa94d', 'Windows PC': '#60a5fa', 'Apple': '#f1f5f9', 'Linux / NAS': '#fbbf24',
               'Media / TV': '#f472b6', 'IoT / Camera': '#2dd4bf', 'Unknown': '#9ca3af'}     # a color per kind - always shown with its name
ACCENTS = {'Scanner green': '#3ddc97', 'Blue': '#1e9bff', 'Green': '#2ecc71', 'Teal': '#2ad4c8', 'Purple': '#c48cff', 'Orange': '#ff7f50', 'Gold': '#e8a33d'}
ACCENT_DEFAULT = '#3ddc97'
ZOOMS = {'Small': (196, 0.88), 'Medium': (262, 1.0), 'Large': (320, 1.14), 'Huge': (396, 1.32)}    # tile width (design pixels), text size factor
ROLES = {'name': (True, 15.0), 'sub': (False, 11.5), 'ip': (False, 13.0), 'dim': (False, 11.5), 'kind': (True, 12.0)}   # tile lines: bold, px
LIST_COLS = [('dot', '', 24, 0), ('name', 'Name', 176, 4), ('ip', 'IP address', 112, 0), ('mac', 'MAC address', 136, 0), ('vendor', 'Maker', 110, 2),
             ('kind', 'Kind', 104, 0), ('rtt', 'Ping', 70, 0), ('ports', 'Services', 132, 3)]    # key, heading, width (design px), share of extra room
LIST_DROP = ('ports', 'vendor', 'mac', 'rtt', 'kind')             # columns left out first when the list is narrow
SORTS = {'name': 'Name', 'ip': 'IP address', 'mac': 'MAC address', 'vendor': 'Maker', 'kind': 'Kind', 'rtt': 'Ping', 'ports': 'Services'}
HEAD_H, FOOT_H, GAP, RADIUS = 46, 30, 12, 12                      # design pixels at 96 dpi
TRANSPARENT = '#010203'                                           # used by the Brightness panel's rounded corners (Windows)
SS = 2                                                            # shapes are drawn at twice the size and shrunk: smooth edges (screens under 150 %)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # bold / regular: Windows, then Linux
FONT_MENU = ('Segoe UI', 10)
C_MENU_SEL, C_SWATCH_EDGE, C_TAG, C_TAG_TEXT = '#2a62a8', '#7c8594', '#f5c542', '#241a02'
COMMON_PORTS = {21: 'ftp', 22: 'ssh', 23: 'telnet', 53: 'dns', 80: 'http', 135: 'rpc', 139: 'netbios', 443: 'https', 445: 'smb', 515: 'lpd', 548: 'afp',
                554: 'rtsp', 631: 'ipp', 1883: 'mqtt', 3389: 'rdp', 5000: 'upnp/synology', 5353: 'mdns', 5900: 'vnc', 7000: 'airplay', 8008: 'cast', 8080: 'http-alt',
                8443: 'https-alt', 8883: 'mqtts', 9100: 'jetdirect', 32400: 'plex', 62078: 'iphone-sync'}
CREATE_NO_WINDOW = 0x08000000 if sys.platform.startswith('win') else 0      # keeps ping / arp / nbtstat from flashing console windows

stop_flag = threading.Event()


class G:                                                          # program-wide state
    window = None
    devices = []                                                  # one dict per device (scan_thread / demo_devices)
    rev = {}                                                      # ip -> a number bumped whenever that device's facts change (its pictures are drawn again)
    seen = set()                                                  # ips the scan running now has found - the others are drawn dim until it ends
    scanning = False
    progress = 0.0
    status = 'Ready - press Scan (F5) to look for the devices on your network.'
    note = ('', 0.0)                                              # a short message for the bottom line, and when it goes away
    view = 'tiles'                                                # 'tiles' / 'list'
    zoom = 'Medium'                                               # tile / row size
    details = True                                                # the Details panel is shown
    sort = ('ip', False)                                          # column, reversed
    search = ''
    hidden = set()                                                # kinds not shown
    vendor = True                                                 # online MAC maker lookup
    picked = None                                                 # the picked device's ip
    scroll = 0                                                    # how far the devices are scrolled (pixels)
    panel_scroll = 0
    hover = (None, None)                                          # (graph key, part) under the mouse
    hint = ''                                                     # what the part under the mouse does - the bottom line shows it
    hits = {}                                                     # graph key -> [(x0, y0, x1, y1, action, value, hint)] - drawn last = on top
    down = None                                                   # (graph key, x, y, action, value) where the left button went down
    dragged = False
    drag_from = 0                                                 # the scroll position when a drag of the scroll bar began
    boxes = {}                                                    # the last layout of the devices part (draw_main)
    head_lines = 1
    pics = {}                                                     # picture key -> tk image, so a picture is drawn only once
    on_canvas = {}                                                # graph key -> the tk images shown now (tk drops images nobody holds)
    redraw_job = None
    busy = False                                                  # a popup or the Brightness panel is open
    in_panel = False
    scale = 1.0                                                   # screen dpi / 96
    theme = 'Toybox'
    bright = 0
    tuned = {}
    accent = ACCENT_DEFAULT
    fonts = {}
    swatches = {}
    menu_font = None                                              # ONE tk font for measuring menu labels (menu_arrows)
    label_w = {}                                                  # menu label -> its width in that font, measured once
    menu_made = None                                              # the right-click menu now on the window - apply_menu skips an unchanged one
    icon_pic = None
    links = {}                                                    # tile picture key -> where its Open link is
    backs = {}                                                    # tile cards without words, by look (tile_back)
    dots = {}                                                     # small dots by size and color (Pic.dot)
    back_kind = None                                              # a run of small moves (typing, arrow keys) that Back takes back as ONE step
    diag_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'network_scanner_diag.txt')
    hang_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'network_scanner_hang.txt')
    watch_path = os.path.join(tempfile.gettempdir(), 'network_scanner_watch_demo.txt' if DEMO else 'network_scanner_watch.txt')
    watch = None                                                  # the open watch file (faulthandler writes into it only if the window gets stuck)
    watch_armed = 0.0                                             # when the watch was last started over
    workers = []                                                  # the worker threads started (scan, diagnostics) - mail is looked for often while one runs
    rung = False                                                  # K_MAIL is on its way - don't ring again
    jobs = {}                                                     # the tk timers: 'mail', 'tick'
    solo = None                                                   # a kind double-clicked: the click that ends the double-click shows only it
    ticks = 0


# --- BRIGHTNESS: the same block in every card widget (master copy in modern_widget_recipe.md) - the program darkens or lightens its own theme ---
# Right-click > Brightness... opens a small panel under the card with a slider, and the card changes as the knob moves.  theme_colors() is what the card,
# its menu and the Theme chips are drawn with: the theme at the chosen level, its text kept readable.  The program supplies redraw(window),
# font(bold, px), is_light(), RADIUS, TRANSPARENT, THEMES and G.theme / G.scale / G.bright / G.tuned.
BRIGHT_LEVELS = list(range(-80, 51, 5))                           # the slider's stops, darkest first: -80 = much darker, 0 = as designed, 50 = lighter
K_BRIGHT = '-BRIGHTNESS-'                                         # settings-file entry, and the right-click item that opens the panel
K_PANEL_IMAGE, K_PANEL_VALUE, K_PANEL_STEP = '-PANEL IMAGE-', '-PANEL VALUE-', '-PANEL STEP-'      # values: the new level / +1 or -1 stop
K_PANEL_HOVER, K_PANEL_CLICK = '-PANEL HOVER-', '-PANEL CLICK-'   # values: 'track' | 'reset' | 'done' | None
K_PANEL_DONE, K_PANEL_CANCEL = '-PANEL DONE-', '-PANEL CANCEL-'   # Enter / Escape
PANEL_W, PANEL_H = 270, 114                                       # the panel, in design pixels
TRACK_X0, TRACK_X1, TRACK_Y, TRACK_H = 20, PANEL_W - 20, 52, 10
PILL_W, PILL_H, PILL_Y = 70, 24, 90                               # Reset (left) and Done (right); PILL_Y is their middle
C_PANEL_DONE = '#2a62a8'                                          # the Done button


def channels(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def shade(c1, c2, f):
    """c1 moved f of the way toward c2"""
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(channels(c1), channels(c2)))


def tune(color, level, light, line=False):
    """A card / border / track color at a Brightness level.  Dark themes: the brightness is scaled - darker is deeper, lighter more vivid, the hue kept;
       lines darken less, so the border and the gauge track still show at -80.  Light themes: darker turns gently gray (at most 32%), lighter fades to white"""
    if light and level > 0:
        return shade(color, '#ffffff', level / 100)
    f = 1 + level / (250 if light else 100)
    if line and level < 0 and not light:
        f **= 0.6
    return '#%02x%02x%02x' % tuple(min(255, round(v * f)) for v in channels(color))


def luminance(color):
    """WCAG relative luminance, 0 = black .. 1 = white"""
    return sum(w * (v / 3294.6 if v <= 10.31 else ((v / 255 + 0.055) / 1.055) ** 2.4) for w, v in zip((0.2126, 0.7152, 0.0722), channels(color)))


def readable(fg, bg, ratio, pole):
    """fg moved toward pole (white on a dark card, black on a light one) just far enough to have ratio contrast with bg"""
    lb = luminance(bg)
    for i in range(26):
        c = shade(fg, pole, i / 25)
        lf = luminance(c)
        if (max(lf, lb) + 0.05) / (min(lf, lb) + 0.05) >= ratio:
            return c
    return pole


def theme_colors(name=None):
    """A theme's five colors at the Brightness setting (the chosen theme if no name) - text keeps 7:1 contrast with the card, dim 4.5:1"""
    name = name if name in THEMES else G.theme if G.theme in THEMES else 'Toybox'
    if (name, G.bright) not in G.tuned:
        T = THEMES[name]
        if G.bright:
            light, level = is_light(T['card']), G.bright
            card, pole = tune(T['card'], level, light), '#000000' if light else '#ffffff'
            T = {'card': card, 'border': tune(T['border'], level, light, True), 'track': tune(T['track'], level, light, True),
                 'text': readable(T['text'], card, 7, pole), 'dim': readable(T['dim'], card, 4.5, pole)}
        G.tuned[(name, G.bright)] = T
    return G.tuned[(name, G.bright)]


def bright_text(level):
    return 'as designed' if level == 0 else f'{level:+d}%'.replace('-', '\u2212')


def knob_x(level):
    """Design-pixel x of the knob at a level: the middle of that level's band on the track"""
    return TRACK_X0 + (BRIGHT_LEVELS.index(level) + 0.5) * (TRACK_X1 - TRACK_X0) / len(BRIGHT_LEVELS)


def level_at(x):
    """The level whose band is under panel pixel x"""
    i = int((x / G.scale - TRACK_X0) / (TRACK_X1 - TRACK_X0) * len(BRIGHT_LEVELS))
    return BRIGHT_LEVELS[max(0, min(len(BRIGHT_LEVELS) - 1, i))]


def panel_part(x, y):
    """'track', 'reset', 'done' or None at panel pixel (x, y)"""
    x, y = x / G.scale, y / G.scale
    if TRACK_X0 - 10 <= x <= TRACK_X1 + 10 and abs(y - TRACK_Y) <= 14:
        return 'track'
    if abs(y - PILL_Y) <= PILL_H / 2:
        if 18 <= x <= 18 + PILL_W:
            return 'reset'
        if PANEL_W - 18 - PILL_W <= x <= PANEL_W - 18:
            return 'done'
    return None


def render_panel(hover):
    """The Brightness panel, drawn like the card and in its colors (so it changes too).  The track shows the card's own color at every level, darkest
       on the left; the knob sits on the one in use, the tick under the track marks 'as designed'"""
    s = G.scale
    k = s * 2
    T, base = theme_colors(), THEMES.get(G.theme, THEMES['Toybox'])
    light = is_light(base['card'])
    W, H = round(PANEL_W * k), round(PANEL_H * k)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=(RADIUS if sg.running_windows() else 0) * k, fill=T['card'], outline=T['border'], width=max(1, round(k)))
    d.text((18 * k, 20 * k), 'BRIGHTNESS', font=font(True, round(13 * k)), fill=T['dim'], anchor='lm')
    d.text(((PANEL_W - 18) * k, 20 * k), bright_text(G.bright), font=font(True, round(13 * k)), fill=T['text'], anchor='rm')
    x0, x1, y0, y1 = TRACK_X0 * k, TRACK_X1 * k, (TRACK_Y - TRACK_H / 2) * k, (TRACK_Y + TRACK_H / 2) * k
    strip = Image.new('RGBA', (round(x1 - x0), round(y1 - y0)))                       # a band per level, in the card color at that level
    band = strip.width / len(BRIGHT_LEVELS)
    for i, level in enumerate(BRIGHT_LEVELS):
        ImageDraw.Draw(strip).rectangle((round(i * band), 0, round((i + 1) * band), strip.height), fill=tune(base['card'], level, light))
    mask = Image.new('L', strip.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, strip.width - 1, strip.height - 1), radius=strip.height / 2, fill=255)
    im.paste(strip, (round(x0), round(y0)), mask)
    d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) / 2, outline=T['dim'] if hover == 'track' else T['border'], width=max(1, round(k)))
    zx = knob_x(0) * k
    d.line((zx, y1 + 3 * k, zx, y1 + 7 * k), fill=T['dim'], width=max(1, round(1.2 * k)))
    kx, ky, r = knob_x(G.bright) * k, TRACK_Y * k, 9 * k                                # the knob, filled with the color in use
    d.ellipse((kx - r, ky - r, kx + r, ky + r), fill=T['card'], outline=T['text'], width=max(1, round(2 * k)))
    small = font(False, round(11 * k))
    d.text((x0, (TRACK_Y + 17) * k), 'darker', font=small, fill=T['dim'], anchor='lm')
    d.text((x1, (TRACK_Y + 17) * k), 'lighter', font=small, fill=T['dim'], anchor='rm')
    for part, px, fill, color in (('reset', 18, T['track'], T['text'] if G.bright else T['dim']), ('done', PANEL_W - 18 - PILL_W, C_PANEL_DONE, '#ffffff')):
        if hover == part:
            fill = shade(fill, '#ffffff', 0.15) if part == 'done' else shade(T['text'], T['card'], 0.78)
        d.rounded_rectangle((px * k, (PILL_Y - PILL_H / 2) * k, (px + PILL_W) * k, (PILL_Y + PILL_H / 2) * k), radius=PILL_H / 2 * k, fill=fill)
        d.text(((px + PILL_W / 2) * k, PILL_Y * k), part.capitalize(), font=font(True, round(12 * k)), fill=color, anchor='mm')
    im = im.resize((round(PANEL_W * s), round(PANEL_H * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return buf.getvalue()


def brightness_panel(card, keep_going):
    """Right-click > Brightness...: the panel under the card.  The card and the panel change as the knob moves (drag, click, arrow keys, mouse wheel,
       Home / End).  Done or Enter keeps the level, Escape puts back the one it had.  keep_going(card, event, values) handles the card's own events
       meanwhile (its timer, hover...) and returns False for one that should close the panel - a menu choice, the close x.  That event is returned so the
       main loop can handle it; None otherwise"""
    start = G.bright
    x, y = card.current_location()
    below, height = y + card.size[1] + 6, round(PANEL_H * G.scale)
    py = below if below + height <= card.TKroot.winfo_screenheight() else max(0, y - height - 6)    # under the card, or above it near the bottom
    panel = sg.Window('Brightness', [[sg.Image(data=render_panel(None), key=K_PANEL_IMAGE, background_color=TRANSPARENT, pad=(0, 0))]], no_titlebar=True,
                      keep_on_top=True, margins=(0, 0), element_padding=(0, 0), background_color=TRANSPARENT, location=(x, py), finalize=True,
                      transparent_color=TRANSPARENT if sg.running_windows() else None)  # no grab_anywhere: it would move the panel as the knob is dragged
    widget, mouse = panel[K_PANEL_IMAGE].Widget, {'drag': False, 'press': None, 'hover': None}

    def press(e):
        part = panel_part(e.x, e.y)
        if part == 'track':                                                             # the knob jumps to the mouse and follows it
            mouse['drag'] = True
            panel.write_event_value(K_PANEL_VALUE, level_at(e.x))
        else:
            mouse['press'] = (e.x_root, e.y_root, part, panel.TKroot.winfo_x(), panel.TKroot.winfo_y())

    def drag(e):
        p = mouse['press']
        if mouse['drag']:
            panel.write_event_value(K_PANEL_VALUE, level_at(e.x))
        elif p:                                                                         # anywhere off the track drags the panel
            panel.TKroot.geometry(f'+{p[3] + e.x_root - p[0]}+{p[4] + e.y_root - p[1]}')

    def release(e):
        if mouse['drag']:
            mouse['drag'] = False
            return
        p, mouse['press'] = mouse['press'], None
        if p and p[2] in ('reset', 'done') and math.hypot(e.x_root - p[0], e.y_root - p[1]) < 4:        # a click, not a drag of the panel
            panel.write_event_value(K_PANEL_CLICK, p[2])

    def hover(part):
        if part != mouse['hover']:
            mouse['hover'] = part
            panel.write_event_value(K_PANEL_HOVER, part)

    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<B1-Motion>', drag, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')
    widget.bind('<Motion>', lambda e: hover(panel_part(e.x, e.y)), add='+')
    widget.bind('<Leave>', lambda e: hover(None), add='+')
    widget.bind('<MouseWheel>', lambda e: panel.write_event_value(K_PANEL_STEP, 1 if e.delta > 0 else -1), add='+')   # Windows
    widget.bind('<Button-4>', lambda e: panel.write_event_value(K_PANEL_STEP, 1), add='+')                            # Linux wheel
    widget.bind('<Button-5>', lambda e: panel.write_event_value(K_PANEL_STEP, -1), add='+')
    for seq, n in (('<Left>', -1), ('<Down>', -1), ('<Right>', 1), ('<Up>', 1)):
        panel.TKroot.bind(seq, lambda e, n=n: panel.write_event_value(K_PANEL_STEP, n))
    panel.TKroot.bind('<Home>', lambda e: panel.write_event_value(K_PANEL_VALUE, BRIGHT_LEVELS[0]))
    panel.TKroot.bind('<End>', lambda e: panel.write_event_value(K_PANEL_VALUE, BRIGHT_LEVELS[-1]))
    panel.bind('<Return>', K_PANEL_DONE)
    panel.bind('<Escape>', K_PANEL_CANCEL)
    panel.force_focus()
    pending = None
    while True:
        win, event, values = sg.read_all_windows()
        if win is card:                                                                 # the card keeps going while the panel is open
            if keep_going(card, event, values):
                continue
            pending = (event, values)
            break
        if event in (sg.WINDOW_CLOSED, K_PANEL_CANCEL):
            G.bright = start
            break
        if event == K_PANEL_DONE or (event == K_PANEL_CLICK and values[event] == 'done'):
            break
        level = G.bright
        if event == K_PANEL_VALUE:
            level = values[event]
        elif event == K_PANEL_STEP:
            level = BRIGHT_LEVELS[max(0, min(len(BRIGHT_LEVELS) - 1, BRIGHT_LEVELS.index(G.bright) + values[event]))]
        elif event == K_PANEL_CLICK and values[event] == 'reset':
            level = 0
        if level != G.bright:
            G.bright = level
            redraw(card)
        panel[K_PANEL_IMAGE].update(data=render_panel(mouse['hover']))
    panel.close()
    redraw(card)
    return pending
# --- end BRIGHTNESS ---

# --- ACCENT: the same block in every card widget (master copy in modern_widget_recipe.md) - right-click > Accent, remembered (-ACCENT-) ---
# The accent colors the dot by the title and the widget's main bar / ring / line; colors that carry meaning (load, status, warnings) stay as they are.
# The program supplies ACCENTS (name -> '#rrggbb', its default first; None = 'Follows load', only where the color can follow a load), ACCENT_DEFAULT,
# G.accent, mix() and is_light(), and imports colorchooser (from tkinter import colorchooser).
ACCENT_ANY = 'Any...'                                             # the last Accent item: the color dialog
K_ACCENT = '-ACCENT-'                                             # settings-file entry ('#rrggbb', None = follows the load), and the start of the Accent menu's keys
KT_ACCENT = lambda name: f'{K_ACCENT}{name}'


def load_accent():
    """The saved accent - ACCENT_DEFAULT the first time, or if what was saved is not a color"""
    c = sg.user_settings_get_entry(K_ACCENT, ACCENT_DEFAULT)
    if c is None:
        return None if None in ACCENTS.values() else ACCENT_DEFAULT
    ok = isinstance(c, str) and len(c) == 7 and c[0] == '#' and all(ch in '0123456789abcdefABCDEF' for ch in c[1:])
    return c if ok else ACCENT_DEFAULT


def accent_on(card, color=None):
    """The accent as drawn on a card of color card (color = what it is right now when it follows the load): a preset - or the load color - a shade
       darker on a light card, like the other status colors; a color picked in the Any... dialog exactly as picked"""
    color = color or G.accent
    return mix(color, '#000000', 0.18) if is_light(card) and G.accent in ACCENTS.values() else color


def accent_menu(tick):
    """The Accent sub-menu for make_menu(): its label and its items - the presets, then Any..., a tick on the one in use"""
    current = next((n for n, c in ACCENTS.items() if c == G.accent), ACCENT_ANY)
    return ['    Accent', [f'{tick(n == current)}{n}::{KT_ACCENT(n)}' for n in list(ACCENTS) + [ACCENT_ANY]]]


def choose_accent(window, menu_key, now):
    """Right-click > Accent > an item: G.accent set and saved.  Any... opens the color dialog on now (the color shown at the moment).  False if cancelled"""
    name = menu_key[len(K_ACCENT):]
    if name == ACCENT_ANY:
        picked = colorchooser.askcolor(color=now, parent=window.TKroot, title='Accent color')[1]
        if not picked:
            return False
        G.accent = picked
    else:
        G.accent = ACCENTS.get(name, ACCENT_DEFAULT)
    sg.user_settings_set_entry(K_ACCENT, G.accent)
    return True
# --- end ACCENT ---


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Thread -> window messages.  Worker threads never touch tk: they only put a message in the mailbox.  The window's own thread looks in the mailbox
# (mail_poll, a tk timer) and rings K_MAIL itself.  3.0.0 rang from the worker threads, and a worker in a tk call waits for the window's thread -
# if that thread was waiting too (Python's garbage collector can free a tk image or variable in any thread), both waited forever: Not Responding.
# ----------------------------------------------------------------------------------------------------------------------------------------------------
mailbox = queue.Queue()


def post(key, value=None):
    """ Worker threads call this instead of window.write_event_value - no tk call from a worker thread, ever """
    mailbox.put((key, value))


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Local network info
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))                                # no packet is sent - this only picks the interface
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def default_gateway():
    """ Best-effort gateway: ipconfig on Windows, 'ip route' elsewhere.  Falls back to x.x.x.1 """
    try:
        if sys.platform.startswith('win'):
            out = run_text(['ipconfig'], 5)[1]
            m = re.search(r'Default Gateway[ .]*:\s*(\d+\.\d+\.\d+\.\d+)', out)
        else:
            out = run_text(['sh', '-c', 'ip route 2>/dev/null || route -n'], 5)[1]
            m = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', out) or re.search(r'^0\.0\.0\.0\s+(\d+\.\d+\.\d+\.\d+)', out, re.M)
        if m:
            return m.group(1)
    except Exception:
        pass
    return '.'.join(local_ip().split('.')[:3]) + '.1'


def run_text(cmd, timeout):
    """ (exit code, stdout, stderr) as text; odd console code-page bytes become replacement characters instead of raising """
    r = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout, creationflags=CREATE_NO_WINDOW)
    return r.returncode, r.stdout.decode(errors='replace'), r.stderr.decode(errors='replace')


def local_mac():
    n = uuid.getnode()
    return ':'.join(f'{(n >> (8 * i)) & 0xff:02X}' for i in reversed(range(6)))


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Discovery
# ----------------------------------------------------------------------------------------------------------------------------------------------------
ping_errors = []          # exceptions raised trying to RUN ping (not "no reply") - shown on the bottom line, so a broken ping is obvious


def ping(ip):
    """ Round-trip ms (float) if the host answered, else None """
    cmd = ['ping', '-n', '1', '-w', '700', ip] if sys.platform.startswith('win') else ['ping', '-c', '1', '-W', '1', ip]
    try:
        out = run_text(cmd, 12)[1]
    except Exception as e:
        ping_errors.append(repr(e))
        return None
    if re.search(r'ttl[=:]', out, re.I):                          # a real echo reply (not "destination unreachable", which also exits 0 on Windows)
        m = re.search(r'(?:time|zeit|temps|tiempo)\s*[=<]\s*([\d.]+)\s*ms', out, re.I)
        return float(m.group(1)) if m else 0.0
    return None


def arp_prime(ips):
    """ A UDP datagram to each host makes the OS ARP for it, so hosts whose firewall drops ping still show up in the ARP table afterwards """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(False)
    for ip in ips:
        if stop_flag.is_set():
            break
        try:
            s.sendto(b'\x00', (ip, 9))
        except Exception:
            pass
        time.sleep(0.003)                                         # about 0.8 s for a /24 - keeps the ARP cache from thrashing
    s.close()
    time.sleep(1.5)


def arp_table():
    """ {ip: 'AA:BB:CC:DD:EE:FF'} from the OS ARP cache """
    table = {}
    try:
        out = run_text(['arp', '-a'] if sys.platform.startswith('win') else ['sh', '-c', 'ip neigh 2>/dev/null || arp -an'], 10)[1]
    except Exception:
        return table
    for m in re.finditer(r'(\d+\.\d+\.\d+\.\d+)\D+?([0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2}[-:][0-9a-fA-F]{2})', out):
        mac = m.group(2).replace('-', ':').upper()
        if mac not in ('FF:FF:FF:FF:FF:FF', '00:00:00:00:00:00') and not mac.startswith('01:00:5E'):
            table[m.group(1)] = mac
    return table


def reverse_dns(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ''


def netbios_name(ip):
    """ Windows only: nbtstat -A ip -> the computer name (the <00> UNIQUE entry) """
    if not sys.platform.startswith('win'):
        return ''
    try:
        out = run_text(['nbtstat', '-A', ip], 6)[1]
        m = re.search(r'^\s*(\S+)\s+<00>\s+UNIQUE', out, re.M)
        return m.group(1) if m else ''
    except Exception:
        return ''


def dns_encode_name(name):
    return b''.join(bytes([len(p)]) + p.encode() for p in name.strip('.').split('.')) + b'\x00'


def dns_decode_name(data, off):
    """ A (possibly compressed) DNS name: (name, next offset) """
    labels, jumped, next_off, hops = [], False, 0, 0
    while True:
        if off >= len(data):
            break
        ln = data[off]
        if ln == 0:
            off += 1
            break
        if ln & 0xC0 == 0xC0:
            if not jumped:
                next_off = off + 2
            off = ((ln & 0x3F) << 8) | data[off + 1]
            jumped = True
            hops += 1
            if hops > 20:
                break
            continue
        labels.append(data[off + 1:off + 1 + ln].decode(errors='replace'))
        off += 1 + ln
    return '.'.join(labels), (next_off if jumped else off)


def dns_parse_answers(data):
    """ [(name, rtype, rdata)] for every answer / authority / additional record, PTR / A / TXT decoded """
    recs = []
    try:
        qd, an, ns, ar = struct.unpack('!HHHH', data[4:12])
        off = 12
        for _ in range(qd):
            _, off = dns_decode_name(data, off)
            off += 4
        for _ in range(an + ns + ar):
            name, off = dns_decode_name(data, off)
            rtype, _, _, rdlen = struct.unpack('!HHIH', data[off:off + 10])
            off += 10
            rdata = data[off:off + rdlen]
            if rtype == 12:                                       # PTR
                target, _ = dns_decode_name(data, off)
                recs.append((name, 'PTR', target))
            elif rtype == 1 and rdlen == 4:                       # A
                recs.append((name, 'A', socket.inet_ntoa(rdata)))
            elif rtype == 16:                                     # TXT
                txt, p = [], 0
                while p < len(rdata):
                    n = rdata[p]
                    txt.append(rdata[p + 1:p + 1 + n].decode(errors='replace'))
                    p += 1 + n
                recs.append((name, 'TXT', txt))
            off += rdlen
    except Exception:
        pass
    return recs


def mdns_reverse_name(ip, timeout=1.2):
    """ Ask the host itself (a unicast mDNS question) for its .local name """
    rev = '.'.join(reversed(ip.split('.'))) + '.in-addr.arpa'
    pkt = struct.pack('!HHHHHH', 0x1234, 0, 1, 0, 0, 0) + dns_encode_name(rev) + struct.pack('!HH', 12, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(timeout)
        s.sendto(pkt, (ip, 5353))
        data, _ = s.recvfrom(4096)
        s.close()
        for name, rtype, rdata in dns_parse_answers(data):
            if rtype == 'PTR':
                return rdata
    except Exception:
        pass
    return ''


def mdns_browse_services(listen_time=2.5):
    """ A multicast '_services._dns-sd._udp.local' question: {ip: set(service types)} by the source of each answer """
    found = {}
    pkt = struct.pack('!HHHHHH', 0, 0, 1, 0, 0, 0) + dns_encode_name('_services._dns-sd._udp.local') + struct.pack('!HH', 12, 1)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.settimeout(0.3)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
        s.sendto(pkt, ('224.0.0.251', 5353))
        end = time.time() + listen_time
        while time.time() < end:
            try:
                data, (src, _) = s.recvfrom(9000)
            except socket.timeout:
                continue
            for name, rtype, rdata in dns_parse_answers(data):
                if rtype == 'PTR' and name.startswith('_services._dns-sd'):
                    found.setdefault(src, set()).add(rdata.replace('.local', ''))
        s.close()
    except Exception:
        pass
    return found


def ssdp_search(listen_time=2.5):
    """ A UPnP M-SEARCH: {ip: {'server': ..., 'location': ...}} """
    found = {}
    msg = 'M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: "ssdp:discover"\r\nMX: 2\r\nST: ssdp:all\r\n\r\n'.encode()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        s.settimeout(0.3)
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        s.sendto(msg, ('239.255.255.250', 1900))
        end = time.time() + listen_time
        while time.time() < end:
            try:
                data, (src, _) = s.recvfrom(4096)
            except socket.timeout:
                continue
            hdrs = {}
            for line in data.decode(errors='replace').split('\r\n')[1:]:
                if ':' in line:
                    k, v = line.split(':', 1)
                    hdrs[k.strip().lower()] = v.strip()
            d = found.setdefault(src, {'server': '', 'location': ''})
            d['server'] = d['server'] or hdrs.get('server', '')
            d['location'] = d['location'] or hdrs.get('location', '')
        s.close()
    except Exception:
        pass
    return found


def probe_ports(ip, timeout=0.6):
    open_ports = []
    for port in COMMON_PORTS:
        if stop_flag.is_set():
            break
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            if s.connect_ex((ip, port)) == 0:
                open_ports.append(port)
            s.close()
        except Exception:
            pass
    return open_ports


def vendor_lookup(mac):
    """ The free online OUI lookup (1 request a second).  '' on any failure """
    try:
        req = urllib.request.Request(f'https://api.macvendors.com/{mac}', headers={'User-Agent': 'network_scanner'})
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.read().decode(errors='replace').strip()[:40]
    except Exception:
        return ''


def run_cmd(cmd, timeout=15):
    t0 = time.time()
    try:
        code, so, se = run_text(cmd, timeout)
        return f'$ {" ".join(cmd)}    (exit {code}, {time.time() - t0:.2f} s)\n{(so + se).strip()}\n'
    except Exception as e:
        return f'$ {" ".join(cmd)}    FAILED after {time.time() - t0:.2f} s: {e!r}\n'


def diagnostics():
    """ Everything needed to see WHY a scan found nothing: the raw output of the network commands, no interpretation """
    my, gw = local_ip(), default_gateway()
    win = sys.platform.startswith('win')
    parts = [f'network_scanner {VERSION} diagnostics  {time.strftime("%Y-%m-%d %H:%M:%S")}', f'Python {sys.version.split()[0]}  on  {sys.platform}  host {socket.gethostname()}',
             f'local_ip() = {my}    default_gateway() = {gw}    local_mac() = {local_mac()}', '']
    parts.append(run_cmd(['ipconfig', '/all'] if win else ['sh', '-c', 'ip addr; ip route']))
    parts.append(run_cmd(['route', 'print', '0.0.0.0'] if win else ['sh', '-c', 'ip route show default']))
    parts.append(run_cmd(['ping', '-n', '2', '-w', '1000', gw] if win else ['ping', '-c', '2', '-W', '1', gw]))
    parts.append(run_cmd(['ping', '-n', '1', '-w', '1000', '8.8.8.8'] if win else ['ping', '-c', '1', '-W', '1', '8.8.8.8']))
    parts.append(f'ping() helper on gateway {gw} -> {ping(gw)!r}   errors: {ping_errors[-1:] or "none"}\n')
    arp_prime([gw, my])
    parts.append(run_cmd(['arp', '-a'] if win else ['sh', '-c', 'ip neigh || arp -an']))
    parts.append(f'arp_table() parsed -> {arp_table()}\n')
    parts.append(run_cmd(['netsh', 'advfirewall', 'show', 'currentprofile'] if win else ['sh', '-c', 'echo no firewall query on this OS']))
    parts.append(run_cmd(['netsh', 'interface', 'ipv4', 'show', 'interfaces'] if win else ['sh', '-c', 'echo -']))
    parts.append(f'mDNS reverse lookup of gateway -> {mdns_reverse_name(gw)!r}')
    parts.append(f'mDNS services seen -> {mdns_browse_services(1.5)}')
    parts.append(f'SSDP responders -> {list(ssdp_search(1.5))}')
    parts.append(f'TCP probe of gateway -> open ports {probe_ports(gw)}')
    return '\n'.join(parts)


def guess_kind(dev, my_ip, gateway):
    ports, services, vendor = set(dev['ports']), ' '.join(dev['services']).lower(), dev['vendor'].lower()
    names = (dev['name'] + ' ' + dev['mdns'] + ' ' + dev['upnp']).lower()
    if dev['ip'] == my_ip:
        return 'This PC'
    if dev['ip'] == gateway:
        return 'Gateway'
    if ports & {9100, 631, 515} or '_ipp' in services or '_printer' in services or any(w in names + vendor for w in ('epson', 'brother', 'canon', 'hp ', 'hewlett', 'lexmark')):
        return 'Printer'
    if '_airplay' in services or '_companion-link' in services or '_raop' in services or 62078 in ports or 'apple' in vendor or 7000 in ports:
        return 'Apple'
    if '_afpovertcp' in services or (5000 in ports and 445 in ports) or any(w in names + vendor for w in ('synology', 'qnap', 'nas', 'ubiquiti', 'unifi')):
        return 'Linux / NAS'
    if '_googlecast' in services or 8008 in ports or 32400 in ports or any(w in names + vendor for w in ('roku', 'sonos', 'samsung', 'lg ', 'vizio', 'tv', 'chromecast', 'fire')):
        return 'Media / TV'
    if ports & {3389} or (445 in ports and 135 in ports) or dev['netbios']:
        return 'Windows PC'
    if 22 in ports or '_ssh' in services or any(w in names + vendor for w in ('raspberry', 'linux', 'debian', 'ubuntu')):
        return 'Linux / NAS'
    if ports & {554, 1883, 8883} or any(w in names + vendor for w in ('espressif', 'tuya', 'ring', 'nest', 'wyze', 'amazon', 'camera', 'hikvision', 'dahua')):
        return 'IoT / Camera'
    return 'Unknown'


def best_name(dev):
    upnp = re.search(r'UPnP/[\d.]+\s+(.+)', dev['upnp'])                 # "Linux/4.9 UPnP/1.0 Chromecast/1.0" -> "Chromecast/1.0"
    for n in (dev['mdns'].replace('.local', ''), dev['netbios'], dev['dns'].split('.')[0], upnp.group(1).strip() if upnp else ''):
        if n and n != dev['ip']:
            return n
    return dev['ip']


def scan_thread(subnet, want_vendor):
    """ The scan, in a worker thread: K_PHASE (words, fraction done), K_FOUND (a device), K_DONE, then K_VENDOR_UPDATE as makers come in """
    my_ip, gateway = local_ip(), default_gateway()
    try:
        net = ipaddress.ip_network(subnet, strict=False)
        hosts = [str(h) for h in net.hosts()] if net.num_addresses > 2 else [str(net.network_address)]
    except Exception as e:
        post(K_PHASE, (f'That subnet won\'t do: "{subnet}" - {e}', 0))
        post(K_DONE, [])
        return
    hosts = hosts[:1024]
    ping_errors.clear()
    post(K_PHASE, (f'Pinging {len(hosts)} addresses on {net} ...', 0.05))
    alive, services, upnp = {}, {}, {}
    disc = threading.Thread(target=lambda: (services.update(mdns_browse_services()), upnp.update(ssdp_search())), daemon=True)
    disc.start()
    with ThreadPoolExecutor(max_workers=48 if sys.platform.startswith('win') else 96) as pool:
        futures = {pool.submit(ping, ip): ip for ip in hosts}
        for i, f in enumerate(futures):
            if stop_flag.is_set():
                break
            rtt = f.result()
            if rtt is not None:
                alive[futures[f]] = rtt
            if i % 16 == 0:
                post(K_PHASE, (f'Pinging ... {i + 1} of {len(hosts)}  ({len(alive)} answered)', 0.05 + 0.45 * i / len(hosts)))
    disc.join(timeout=4)
    post(K_PHASE, (f'{len(alive)} answered the ping.  Looking in the ARP table for devices that ignore ping ...', 0.48))
    arp_prime(hosts)
    arp = arp_table()
    if ping_errors:
        post(K_PHASE, (f'Ping could not be run ({len(ping_errors)} times) - {ping_errors[0][:80]}.  Try Diagnose.', 0.48))
        time.sleep(2)
    for ip in list(arp) + list(services) + list(upnp):
        if ipaddress.ip_address(ip) in net and ip not in alive:
            alive[ip] = None                                      # in ARP / mDNS / SSDP but no ping reply
    if my_ip not in alive and ipaddress.ip_address(my_ip) in net:
        alive[my_ip] = 0.0
    ips = sorted(alive, key=lambda s: ipaddress.ip_address(s))
    post(K_PHASE, (f'Identifying {len(ips)} devices ...', 0.5))

    def identify(ip):
        if stop_flag.is_set():
            return None
        dev = {'ip': ip, 'rtt': alive[ip], 'mac': arp.get(ip, local_mac() if ip == my_ip else ''), 'vendor': '', 'dns': reverse_dns(ip),
               'mdns': socket.gethostname() + '.local' if ip == my_ip else mdns_reverse_name(ip), 'netbios': '' if ip == my_ip else netbios_name(ip),
               'services': sorted(services.get(ip, [])), 'upnp': upnp.get(ip, {}).get('server', ''), 'location': upnp.get(ip, {}).get('location', ''),
               'ports': probe_ports(ip)}
        dev['name'] = best_name(dev)
        dev['kind'] = guess_kind(dev, my_ip, gateway)
        return dev

    devices = []
    with ThreadPoolExecutor(max_workers=32) as pool:
        for i, dev in enumerate(pool.map(identify, ips)):
            if dev is None or stop_flag.is_set():
                break
            devices.append(dev)
            post(K_FOUND, dev)
            post(K_PHASE, (f'Identified {i + 1} of {len(ips)}: {dev["name"]}', 0.5 + 0.5 * (i + 1) / max(1, len(ips))))
    post(K_DONE, devices)
    if want_vendor:                                               # the slow online maker lookup (1 a second) - makers trickle in afterwards
        todo, makers = [d for d in devices if d['mac']], 0
        for i, dev in enumerate(todo):
            if stop_flag.is_set():
                return
            v = vendor_lookup(dev['mac'])
            makers += bool(v)
            post(K_VENDOR_UPDATE, (dev['ip'], v, i + 1, len(todo)))
            time.sleep(1.1)
        post(K_VENDOR_DONE, (makers, len(todo)))


def demo_devices():
    """ A made-up home network with every kind of device, so every color shows.  192.168.1.x addresses, locally administered MACs (02:...) """
    def dev(last, name, kind, ports=(), mdns='', dns='', netbios='', services=(), upnp='', vendor='', rtt=1.0):
        return {'ip': f'192.168.1.{last}', 'rtt': rtt, 'mac': f'02:5F:3A:{last:02X}:{last * 37 % 256:02X}:{last * 91 % 256:02X}', 'vendor': vendor, 'dns': dns,
                'mdns': mdns, 'netbios': netbios, 'services': sorted(services), 'upnp': upnp, 'location': '', 'ports': sorted(ports), 'name': name, 'kind': kind}
    return [dev(1, 'router', 'Gateway', (53, 80, 443), dns='router.lan', upnp='Linux/5.4 UPnP/1.0 MiniUPnPd/2.2', vendor='Netgear', rtt=1.2),
            dev(20, 'WORKSTATION', 'This PC', (135, 139, 445, 3389), mdns='workstation.local', netbios='WORKSTATION', vendor='ASUSTek', rtt=0.0),
            dev(21, 'LAPTOP-OFFICE', 'Windows PC', (135, 139, 445), netbios='LAPTOP-OFFICE', dns='laptop-office.lan', vendor='Intel', rtt=2.2),
            dev(22, 'SURFACE-TABLET', 'Windows PC', (135, 445), netbios='SURFACE-TABLET', vendor='Microsoft', rtt=4.0),
            dev(30, 'EPSON-ET-8550', 'Printer', (80, 443, 631, 9100), mdns='EPSON-ET-8550.local', services=('_ipp._tcp', '_printer._tcp'), vendor='Seiko Epson', rtt=3.8),
            dev(31, 'HP-OfficeJet', 'Printer', (80, 631, 9100), mdns='HP-OfficeJet.local', services=('_ipp._tcp',), vendor='HP', rtt=5.1),
            dev(40, 'Kitchen-iPad', 'Apple', (62078,), mdns='Kitchen-iPad.local', services=('_companion-link._tcp',), vendor='Apple', rtt=12.4),
            dev(41, 'Living-Room-Apple-TV', 'Apple', (7000,), mdns='Living-Room-Apple-TV.local', services=('_airplay._tcp', '_raop._tcp'), vendor='Apple', rtt=6.1),
            dev(50, 'nas', 'Linux / NAS', (22, 80, 443, 445, 5000), mdns='nas.local', services=('_afpovertcp._tcp', '_smb._tcp'), vendor='Synology', rtt=0.9),
            dev(51, 'raspberrypi', 'Linux / NAS', (22,), mdns='raspberrypi.local', services=('_ssh._tcp',), vendor='Raspberry Pi Trading', rtt=1.6),
            dev(60, 'Samsung-TV', 'Media / TV', (8008, 8080), upnp='Linux UPnP/1.0 Samsung TV/1.0', vendor='Samsung', rtt=7.3),
            dev(61, 'Chromecast-Bedroom', 'Media / TV', (8008, 8443), mdns='Chromecast-Bedroom.local', services=('_googlecast._tcp',), vendor='Google', rtt=9.8),
            dev(62, 'Sonos-Kitchen', 'Media / TV', (80,), upnp='Linux UPnP/1.0 Sonos/80.1', vendor='Sonos', rtt=4.4),
            dev(70, 'Front-Door-Camera', 'IoT / Camera', (80, 554), vendor='Hikvision', rtt=8.7),
            dev(71, 'ESP-Thermostat', 'IoT / Camera', (80, 1883), vendor='Espressif', rtt=15.2),
            dev(72, 'Tuya-Plug', 'IoT / Camera', (), vendor='Tuya', rtt=18.0),
            dev(90, '192.168.1.90', 'Unknown', (), rtt=None)]


def demo_scan_thread(subnet, want_vendor):
    """ The demo's 'scan': the same messages a real scan posts, paced so it looks alive - nothing goes out on the network """
    for i in range(10):
        if stop_flag.is_set():
            break
        post(K_PHASE, (f'Pinging 254 addresses on {DEMO_SUBNET} ...  (demo - made-up devices)', 0.05 + 0.045 * i))
        time.sleep(0.08)
    found, devices = [], demo_devices()
    for i, dev in enumerate(devices):
        if stop_flag.is_set():
            break
        found.append(dev)
        post(K_FOUND, dev)
        post(K_PHASE, (f'Identified {i + 1} of {len(devices)}: {dev["name"]}', 0.5 + 0.5 * (i + 1) / len(devices)))
        time.sleep(0.06)
    post(K_DONE, found)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# What a device says about itself
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def rtt_text(dev):
    return 'no ping reply' if dev['rtt'] is None else ('this PC' if dev['kind'] == 'This PC' else f'{dev["rtt"]:.0f} ms')


def ports_text(dev):
    return ', '.join(COMMON_PORTS.get(p, str(p)) for p in dev['ports']) if dev['ports'] else 'no open ports found'


def found_by(dev):
    ways = [w for w, yes in (('ping', dev['rtt'] is not None), ('ARP', dev['mac']), ('DNS', dev['dns']), ('mDNS', dev['mdns'] or dev['services']),
                             ('SSDP / UPnP', dev['upnp']), ('NetBIOS', dev['netbios']), ('open ports', dev['ports'])) if yes]
    return ', '.join(ways) or '-'


def web_url(dev):
    """ The device's web page, or '' when it offers none (and always '' in the demo - its addresses are made up) """
    ports = set(dev['ports'])
    if DEMO or not ports & {80, 443, 8080, 8443}:
        return ''
    if 80 in ports:
        return f'http://{dev["ip"]}'
    if 443 in ports:
        return f'https://{dev["ip"]}'
    return f'http://{dev["ip"]}:8080' if 8080 in ports else f'https://{dev["ip"]}:8443'


def details_text(dev):
    rows = [('Name', dev['name']), ('Kind', dev['kind']), ('IP', dev['ip']), ('Ping', 'no reply' if dev['rtt'] is None else f'{dev["rtt"]:.1f} ms'),
            ('MAC', dev['mac'] or 'unknown'), ('Maker', dev['vendor'] or 'unknown'), ('mDNS name', dev['mdns'] or '-'), ('DNS name', dev['dns'] or '-'),
            ('NetBIOS', dev['netbios'] or '-'), ('UPnP server', dev['upnp'] or '-'), ('UPnP URL', dev['location'] or '-'),
            ('mDNS services', ', '.join(dev['services']) or '-'),
            ('Open ports', ', '.join(f'{p} ({COMMON_PORTS.get(p, "?")})' for p in dev['ports']) or 'none of the common ports'), ('Found by', found_by(dev))]
    return '\n'.join(f'{name + ":":<15}{value}' for name, value in rows)


def haystack(dev):
    return ' '.join([dev['name'], dev['ip'], dev['mac'], dev['vendor'], dev['mdns'], dev['dns'], dev['netbios'], dev['upnp'], dev['kind'], *dev['services'],
                     *[COMMON_PORTS.get(p, str(p)) for p in dev['ports']]]).lower()


def sort_key(dev):
    col = G.sort[0]
    if col == 'ip':
        return int(ipaddress.ip_address(dev['ip']))
    if col == 'rtt':
        return (dev['rtt'] is None, dev['rtt'] or 0, int(ipaddress.ip_address(dev['ip'])))
    if col == 'ports':
        return (-len(dev['ports']), int(ipaddress.ip_address(dev['ip'])))
    return (str(dev.get(col, '')).lower() or '￿', int(ipaddress.ip_address(dev['ip'])))


def shown_devices():
    """ The devices on screen: the kinds not hidden, matching every word of the search, in the sort order """
    words = G.search.lower().split()
    shown = [d for d in G.devices if d['kind'] not in G.hidden and all(w in haystack(d) for w in words)]
    return sorted(shown, key=sort_key, reverse=G.sort[1])


def device(ip):
    return next((d for d in G.devices if d['ip'] == ip), None)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Colors, fonts, words
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def mix(c1, c2, f):
    """ Blend two hex colors, f=0 -> c1, f=1 -> c2 """
    return '#%02x%02x%02x' % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c1), rgb(c2)))


def is_light(color):
    r, g, b = rgb(color)
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def colors():
    """ Everything is drawn with these: the theme at its Brightness, and the accent """
    key = (G.theme, G.bright, G.accent)
    if G.tuned.get('_colors_key') != key:
        T = theme_colors()
        dark = not is_light(T['card'])
        c = dict(T, dark=dark, page=T['card'], line=T['border'], input=T['track'])
        c['tile'] = mix(T['card'], T['text'], 0.065) if dark else mix(T['card'], '#ffffff', 0.7)
        c['tile_hover'] = mix(c['tile'], T['text'], 0.05)
        c['chip'] = mix(T['card'], T['text'], 0.11 if dark else 0.07)
        c['chip_hover'] = mix(T['card'], T['text'], 0.2 if dark else 0.14)
        c['stripe'] = mix(T['card'], T['text'], 0.025)
        c['accent'] = accent_on(T['card'])
        c['on_accent'] = '#0d1117' if is_light(c['accent']) else '#ffffff'
        c['pick'] = mix(c['tile'], c['accent'], 0.16)
        c['link'] = readable(c['accent'], c['tile'], 3.2, '#000000' if not dark else '#ffffff')
        G.tuned['_colors'], G.tuned['_colors_key'], G.tuned['_kinds'] = c, key, {}
    return G.tuned['_colors']


def kind_color(kind, bg, ratio=3.0):
    """ A kind's color, moved just far enough from bg to read - so pale kinds still show on a light theme """
    kinds = colors() and G.tuned['_kinds']
    if (kind, bg, ratio) not in kinds:
        kinds[(kind, bg, ratio)] = readable(KIND_COLORS.get(kind, KIND_COLORS['Unknown']), bg, ratio, '#000000' if is_light(bg) else '#ffffff')
    return kinds[(kind, bg, ratio)]


def font(bold, px):
    """ A Segoe UI (Windows) / DejaVu (Linux) font of px pixels, cached """
    px = max(6, int(round(px)))
    if (bold, px) not in G.fonts:
        f = None
        for name in FONT_NAMES[bold]:
            try:
                f = ImageFont.truetype(name, px)
                break
            except OSError:
                continue
        if f is None:
            try:
                f = ImageFont.load_default(size=px)
            except TypeError:
                f = ImageFont.load_default()
        G.fonts[(bold, px)] = f
    return G.fonts[(bold, px)]


def fit(text, f, width):
    """ text cut with ... to fit width pixels in font f """
    text = str(text)
    if f.getlength(text) <= width:
        return text
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if f.getlength(text[:mid].rstrip() + '…') <= width:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo].rstrip() + '…' if lo else ''


def wrap(text, f, width, lines=99):
    """ text in lines that fit width (long words such as addresses are broken anywhere); the last line cut with ... when there are more """
    out, line = [], ''
    for word in str(text).split(' '):
        while f.getlength(word) > width and len(word) > 1:          # a word longer than the line: as much as fits, then the rest
            cut = max(1, len(fit(word, f, width).rstrip('…')))
            if line:
                out.append(line)
                line = ''
            out.append(word[:cut])
            word = word[cut:]
        trial = f'{line} {word}' if line else word
        if f.getlength(trial) <= width:
            line = trial
        else:
            out.append(line)
            line = word
    out.append(line)
    if len(out) > lines:
        out = out[:lines]
        out[-1] = fit(out[-1] + ' …', f, width) if not out[-1].endswith('…') else out[-1]
    return out


class Pic:
    """ A picture drawn in two passes: shapes at twice the size (smooth edges once shrunk), then the words at the real size (sharp) """

    def __init__(self, w, h, bg=None, base=None):
        self.w, self.h, self.bg, self.base = max(1, int(w)), max(1, int(h)), bg, base     # base: a ready picture to draw on instead of bg
        self.shapes, self.words, self.dots, self.marks = [], [], [], []

    def dot(self, center, r, color):
        """ A small round dot, smooth at any screen size (drawn once per size and color, then kept) """
        self.dots.append((center, r, color))

    def link_mark(self, xy, size, color):
        """ The "opens in your browser" mark (a box with an arrow out of it), left edge at x, centered on y.  Drawn, not a letter: Pillow has no
            font fallback, and Segoe UI has no ↗ - it came out as an empty box """
        self.marks.append((xy, size, color))

    def rect(self, box, radius=0, fill=None, outline=None, width=1, bar=None):
        """ A (rounded) rectangle; bar = (width, color): a stripe down its left side, inside its rounded corners """
        self.shapes.append(('rect', box, radius, fill, outline, width, bar))

    def ellipse(self, box, fill=None, outline=None, width=1):
        self.shapes.append(('ellipse', box, fill, outline, width))

    def line(self, points, fill, width=1):
        self.shapes.append(('line', points, fill, width))

    def text(self, xy, words, f, fill, anchor='lm'):
        self.words.append((xy, words, f, fill, anchor))

    def render(self):
        k = SS if G.scale < 1.5 else 1                            # a dense screen (150 % and up) needs no supersampling - and it is 4x less work
        if self.base is not None and not self.shapes:
            im = self.base.copy()
            self.paste_dots(im)
            d = ImageDraw.Draw(im)
            for xy, words, f, fill, anchor in self.words:
                d.text(xy, words, font=f, fill=fill, anchor=anchor)
            return im
        im = Image.new('RGBA', (self.w * k, self.h * k), self.bg or (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for shape in self.shapes:
            if shape[0] == 'rect':
                _, box, radius, fill, outline, width, bar = shape
                x0, y0, x1, y1 = [v * k for v in box]
                if bar:
                    layer = Image.new('RGBA', (round(x1 - x0) + 1, round(y1 - y0) + 1), fill)
                    ImageDraw.Draw(layer).rectangle((0, 0, round(bar[0] * k), layer.height), fill=bar[1])
                    mask = Image.new('L', layer.size, 0)
                    ImageDraw.Draw(mask).rounded_rectangle((0, 0, layer.width - 1, layer.height - 1), radius=radius * k, fill=255)
                    im.paste(layer, (round(x0), round(y0)), mask)
                    if outline:
                        d.rounded_rectangle((x0, y0, x1, y1), radius=radius * k, outline=outline, width=max(1, round(width * k)))
                else:
                    d.rounded_rectangle((x0, y0, x1, y1), radius=radius * k, fill=fill, outline=outline, width=max(1, round(width * k)))
            elif shape[0] == 'ellipse':
                _, box, fill, outline, width = shape
                d.ellipse([v * k for v in box], fill=fill, outline=outline, width=max(1, round(width * k)))
            elif shape[0] == 'line':
                _, points, fill, width = shape
                d.line([v * k for v in points], fill=fill, width=max(1, round(width * k)), joint='curve')
        if k != 1:
            im = im.resize((self.w, self.h), Image.LANCZOS)
        self.paste_dots(im)
        d = ImageDraw.Draw(im)
        for xy, words, f, fill, anchor in self.words:
            d.text(xy, words, font=f, fill=fill, anchor=anchor)
        return im

    def paste_dots(self, im):
        for (cx, cy), r, color in self.dots:
            size = max(2, round(2 * r))
            key = (size, color)
            if key not in G.dots:
                big = Image.new('RGBA', (size * 4, size * 4), (0, 0, 0, 0))
                ImageDraw.Draw(big).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=color)
                G.dots[key] = big.resize((size, size), Image.LANCZOS)
            im.alpha_composite(G.dots[key], (max(0, round(cx - size / 2)), max(0, round(cy - size / 2))))
        for (x, cy), size, color in self.marks:
            size = max(6, round(size))
            key = ('link', size, color)
            if key not in G.dots:
                n = size * 4
                big = Image.new('RGBA', (n, n), (0, 0, 0, 0))
                d, w = ImageDraw.Draw(big), max(4, round(n * 0.11))
                at = lambda *xy: [v * (n - 1) for v in xy]
                d.line(at(0.46, 0.2, 0.1, 0.2, 0.1, 0.9, 0.8, 0.9, 0.8, 0.54), fill=color, width=w, joint='curve')    # the box, open at the top right
                d.line(at(0.42, 0.58, 0.9, 0.1), fill=color, width=w)                                               # the arrow
                d.line(at(0.54, 0.1, 0.9, 0.1, 0.9, 0.46), fill=color, width=w, joint='curve')                       # its head
                G.dots[key] = big.resize((size, size), Image.LANCZOS)
            im.alpha_composite(G.dots[key], (max(0, round(x)), max(0, round(cy - size / 2))))


def photo(key, make):
    """ The tk image for key - made by make() (a PIL image) the first time, then kept """
    if key not in G.pics:
        if len(G.pics) > 900:                                     # a long session at many sizes: start over (the ones on screen are held elsewhere)
            G.pics.clear()
        im = make()
        if ImageTk is not None:
            G.pics[key] = ImageTk.PhotoImage(im, master=G.window.TKroot)
        else:
            buf = io.BytesIO()
            im.save(buf, 'PNG')
            G.pics[key] = tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.pics[key]


def fresh(im):
    """ A tk image of a PIL image that is drawn new every time (the header, the bottom line) """
    if ImageTk is not None:
        return ImageTk.PhotoImage(im, master=G.window.TKroot)
    buf = io.BytesIO()
    im.save(buf, 'PNG')
    return tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue()))


def look_key():
    return (G.theme, G.bright, G.accent, G.scale)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Tiles and list rows
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def tile_lines(dev):
    """ What a tile shows at the size that is set: [(role, words)] - the role picks the font and the color """
    z = G.zoom
    mac = (dev['mac'] + ('  ' + dev['vendor'] if dev['vendor'] else '')) if dev['mac'] else 'MAC unknown'
    lines = [('name', dev['name'])]
    if z != 'Small':
        lines.append(('sub', dev['mdns'] or dev['dns'] or dev['netbios'] or ' '))
    lines.append(('ip', dev['ip']))
    if z != 'Small':
        lines += [('dim', mac), ('dim', ports_text(dev))]
    if z in ('Large', 'Huge'):
        lines.append(('dim', 'mDNS: ' + (', '.join(s.split('.')[0] for s in dev['services']) or 'nothing announced')))
    if z == 'Huge':
        lines.append(('dim', 'UPnP: ' + (dev['upnp'] or '-')))
    lines.append(('kind', dev['kind']))
    return lines


def line_px(role):
    bold, px = ROLES[role]
    return bold, px * ZOOMS[G.zoom][1] * G.scale


def tile_height():
    s, f = G.scale, ZOOMS[G.zoom][1]
    roles = [role for role, _ in tile_lines({'name': '', 'mdns': '', 'dns': '', 'netbios': '', 'ip': '', 'mac': '', 'vendor': '', 'ports': [], 'services': [],
                                              'upnp': '', 'kind': '', 'rtt': None})]
    return round(sum(line_px(r)[1] * 1.5 for r in roles) + (20 + 6) * s * f)


def tile_picture(dev, w, h, picked, hover, stale):
    """ One device as a tile: a rounded card with its kind's color down the left side; the name, addresses, what it offers; its kind and Open """
    c, s, f = colors(), G.scale, ZOOMS[G.zoom][1]
    bar = round(5 * s * f)
    fill = c['pick'] if picked else c['tile_hover'] if hover else c['tile']
    edge = c['accent'] if picked else mix(c['line'], c['text'], 0.35) if hover else c['line']
    p = Pic(w, h, base=tile_back(w, h, fill, edge, (2 if picked else 1) * s, bar, kind_color(dev['kind'], fill, 1.6)))
    x, right, y = bar + round(11 * s * f), w - round(11 * s * f), round(10 * s * f)
    fade = (lambda col: mix(col, fill, 0.5)) if stale else (lambda col: col)
    link = None
    for role, words in tile_lines(dev):
        bold, px = line_px(role)
        fnt, lh = font(bold, px), round(px * 1.5)
        if role == 'kind':
            y = h - round(10 * s * f) - lh
            kc = kind_color(dev['kind'], fill, 3.0)
            r = px * 0.32
            p.dot((x + r, y + lh / 2), r, fade(kind_color(dev['kind'], fill, 1.6)))
            url = web_url(dev)
            mark = px * 0.8
            open_w = font(True, px).getlength('Open') + px * 0.35 + mark if url else 0
            p.text((x + 2 * r + 6 * s, y + lh / 2), fit(words, fnt, right - x - 2 * r - 6 * s - open_w - 8 * s), fnt, fade(kc))
            if url:
                p.text((right - mark - px * 0.35, y + lh / 2), 'Open', font(True, px), fade(c['link']), 'rm')
                p.link_mark((right - mark, y + lh / 2 - px * 0.06), mark, fade(c['link']))
                link = (right - open_w - 4 * s, y, right + 2 * s, y + lh)
            continue
        if role == 'ip':
            rtt_f = font(False, px * 0.88)
            rtt = rtt_text(dev)
            p.text((right, y + lh / 2), rtt, rtt_f, fade(c['dim']), 'rm')
            p.text((x, y + lh / 2), fit(words, fnt, right - x - rtt_f.getlength(rtt) - 8 * s), fnt, fade(c['text']))
        else:
            color = kind_color(dev['kind'], fill, 3.0) if role == 'name' else c['dim']
            p.text((x, y + lh / 2), fit(words, fnt, right - x), fnt, fade(color))
        y += lh
    return p.render(), link


def tile_back(w, h, fill, edge, edge_w, bar, bar_color):
    """ The card of a tile without its words: rounded, the kind's color down its left side - drawn once for each look and kept """
    key = ('tile back', w, h, fill, edge, edge_w, bar, bar_color, G.scale)
    if key not in G.backs:
        if len(G.backs) > 200:
            G.backs.clear()
        p = Pic(w, h)
        p.rect((0.5, 0.5, w - 1, h - 1), round(RADIUS * G.scale), fill=fill, outline=edge, width=edge_w, bar=(bar, bar_color))
        G.backs[key] = p.render()
    return G.backs[key]


def list_columns(width):
    """ The list's columns for this width: [(key, heading, x0, x1)] - narrow lists leave out Services, Maker, MAC, Ping, Kind in that order """
    s, f = G.scale, ZOOMS[G.zoom][1]
    cols = [list(col) for col in LIST_COLS]
    drop = list(LIST_DROP)
    while sum(col[2] * s * f for col in cols) > width and drop:
        gone = drop.pop(0)
        cols = [col for col in cols if col[0] != gone]
    extra = max(0, width - sum(col[2] * s * f for col in cols))
    shares = sum(col[3] for col in cols) or 1
    out, x = [], 0
    for key, head, w, share in cols:
        cw = w * s * f + extra * share / shares
        out.append((key, head, round(x), round(x + cw)))
        x += cw
    return out


def row_height():
    return round(30 * G.scale * ZOOMS[G.zoom][1])


def cell_text(dev, key):
    return {'name': dev['name'], 'ip': dev['ip'], 'mac': dev['mac'] or '-', 'vendor': dev['vendor'] or '-', 'kind': dev['kind'],
            'rtt': 'no reply' if dev['rtt'] is None else rtt_text(dev),
            'ports': ', '.join(COMMON_PORTS.get(p, str(p)) for p in dev['ports']) or '-'}.get(key, '')


def row_picture(dev, w, h, cols, picked, hover, stale, odd):
    """ One device as a line of the list """
    c, s, f = colors(), G.scale, ZOOMS[G.zoom][1]
    fill = c['pick'] if picked else c['tile_hover'] if hover else c['stripe'] if odd else c['page']
    base = Image.new('RGBA', (w, h), fill)
    d = ImageDraw.Draw(base)
    if picked:
        d.rectangle((0, 0, round(3 * s) - 1, h), fill=c['accent'])
    d.line((0, h - 1, w, h - 1), fill=mix(c['line'], fill, 0.5), width=1)
    p = Pic(w, h, base=base)
    fade = (lambda col: mix(col, fill, 0.5)) if stale else (lambda col: col)
    px = 13 * s * f
    for key, head, x0, x1 in cols:
        pad = 8 * s
        if key == 'dot':
            p.dot(((x0 + x1) / 2, h / 2), px * 0.32, fade(kind_color(dev['kind'], fill, 1.6)))
            continue
        bold = key == 'name'
        fnt = font(bold, px if key in ('name', 'ip') else px * 0.92)
        color = kind_color(dev['kind'], fill, 3.0) if key == 'kind' else c['text'] if key in ('name', 'ip') else c['dim']
        words = fit(cell_text(dev, key), fnt, x1 - x0 - 2 * pad)
        if key == 'rtt':
            p.text((x1 - pad, h / 2), words, fnt, fade(color), 'rm')
        else:
            p.text((x0 + pad, h / 2), words, fnt, fade(color))
    return p.render()


def list_head_picture(w, h, cols, hover):
    c, s, f = colors(), G.scale, ZOOMS[G.zoom][1]
    p = Pic(w, h, c['page'])
    fnt = font(True, 11 * s * f)
    for key, head, x0, x1 in cols:
        if not head:
            continue
        if hover == key:
            p.rect((x0 + 2 * s, 3 * s, x1 - 2 * s, h - 3 * s), 6 * s, fill=c['chip'])
        arrow = (' ▼' if G.sort[1] else ' ▲') if G.sort[0] == key else ''
        color = c['text'] if G.sort[0] == key else c['dim']
        if key == 'rtt':
            p.text((x1 - 8 * s, h / 2), fit(head.upper() + arrow, fnt, x1 - x0 - 16 * s), fnt, color, 'rm')
        else:
            p.text((x0 + 8 * s, h / 2), fit(head.upper() + arrow, fnt, x1 - x0 - 16 * s), fnt, color)
    p.line((0, h - 1, w, h - 1), c['line'], 1)
    return p.render()


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# The kinds strip above the devices
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def legend_layout(width):
    """ The kinds as chips that wrap to more rows when narrow: (height, [(kind, x0, y0, x1, y1)]) """
    s = G.scale
    fnt, small = font(False, 12 * s), font(False, 11 * s)
    counts = {}
    for d in G.devices:
        counts[d['kind']] = counts.get(d['kind'], 0) + 1
    x, y, chip_h, m = GAP * s, 7 * s, 24 * s, GAP * s
    chips, rows = [], 1
    for kind in ('*All', '*None', *KIND_COLORS):                  # '*' = a button that sets every kind: All shows them, None hides them
        count = f'  {counts.get(kind, 0)}' if G.devices and kind[0] != '*' else ''
        w = (12 * s + fnt.getlength(kind[1:]) + 12 * s) if kind[0] == '*' else (9 * s + 8 * s + fnt.getlength(kind) + small.getlength(count) + 10 * s)
        if x + w > width - m and chips:
            x, y, rows = m, y + chip_h + 5 * s, rows + 1
        chips.append((kind, x, y, x + w, y + chip_h, count))
        x += w + (13 * s if kind == '*None' else 5 * s)
    return round(y + chip_h + 7 * s), chips, rows


def legend_picture(w, h, chips, hover):
    c, s = colors(), G.scale
    p = Pic(w, h, c['page'])
    fnt, small = font(False, 12 * s), font(False, 11 * s)
    for kind, x0, y0, x1, y1, count in chips:
        if kind[0] == '*':                                        # All / None: lit while it is what you see
            lit = not G.hidden if kind == '*All' else G.hidden >= set(KIND_COLORS)
            if hover == kind or lit:
                p.rect((x0, y0, x1, y1), (y1 - y0) / 2, fill=c['chip_hover'] if hover == kind else c['chip'])
            else:
                p.rect((x0, y0, x1, y1), (y1 - y0) / 2, outline=c['line'], width=1 * s)
            p.text((x0 + 12 * s, (y0 + y1) / 2), kind[1:], fnt, c['text'] if lit or hover == kind else c['dim'])
            continue
        on = kind not in G.hidden
        if hover == kind:
            p.rect((x0, y0, x1, y1), (y1 - y0) / 2, fill=c['chip_hover'])
        elif on:
            p.rect((x0, y0, x1, y1), (y1 - y0) / 2, fill=c['chip'])
        else:
            p.rect((x0, y0, x1, y1), (y1 - y0) / 2, outline=c['line'], width=1 * s)
        r, cy = 5 * s, (y0 + y1) / 2
        dot = (x0 + 9 * s, cy - r, x0 + 9 * s + 2 * r, cy + r)
        if on:
            p.ellipse(dot, fill=kind_color(kind, c['chip'], 1.6))
        else:
            p.ellipse(dot, outline=c['dim'], width=1.4 * s)
        tx = x0 + 9 * s + 2 * r + 6 * s
        p.text((tx, cy), kind, fnt, kind_color(kind, c['chip'] if on else c['page'], 3.0) if on else c['dim'])
        if count:
            p.text((tx + fnt.getlength(kind), cy), count, small, c['dim'])
    return p.render()


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# The Details panel
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def panel_picture(dev, pw, ph, hover):
    """ The whole Details panel, as tall as its words need (at least ph): (picture, hits in panel pixels, height) """
    c, s = colors(), G.scale
    pad, inner = round(16 * s), pw - round(32 * s)
    hits, plan = [], []                                           # plan: what to draw, worked out first so the picture can be as tall as it needs
    close = (pw - 34 * s, 10 * s, pw - 10 * s, 34 * s)
    if dev is None:
        title_f, small = font(True, 15 * s), font(False, 12 * s)
        height = max(ph, round(200 * s))
        p = Pic(pw, height, c['page'])
        p.text((pw / 2, ph * 0.38), 'Details', title_f, c['dim'], 'mm')
        for i, line in enumerate(wrap('Pick a device to see everything found about it - click it, or use the arrow keys.', small, inner, 4)):
            p.text((pw / 2, ph * 0.38 + (28 + 18 * i) * s), line, small, c['dim'], 'mm')
        p.line((0.5, 0, 0.5, height), c['line'], 1)
        draw_close(p, close, hover == 'close', c, s)
        hits.append((*close, 'details', None, 'Hide the Details panel  (Ctrl+D)'))
        return p.render(), hits, height
    name_f, label_f, value_f, button_f = font(True, 18 * s), font(True, 10.5 * s), font(False, 13 * s), font(True, 12 * s)
    y = pad + 4 * s
    for line in wrap(dev['name'], name_f, inner - 30 * s, 3):
        plan.append(('text', (pad, y + 12 * s), line, name_f, ('kind', dev['kind'])))
        y += 26 * s
    y += 4 * s
    plan.append(('kind', y))
    y += 28 * s
    buttons = [('copy', 'Copy IP', 'Copy the IP address  (Ctrl+C)'), ('copy_all', 'Copy all', 'Copy everything found about it')]
    url = web_url(dev)
    if url:
        buttons.insert(0, ('popen', 'Open', f'Open {url} in your browser'))
    bx = pad
    for action, words, tip in buttons:
        bw = button_f.getlength(words) + 26 * s + (17 * s if action == 'popen' else 0)       # Open has its drawn mark after the word
        if bx + bw > pw - pad and bx > pad:
            bx, y = pad, y + 36 * s
        plan.append(('button', (bx, y, bx + bw, y + 28 * s), words, action, tip))
        bx += bw + 8 * s
    y += 46 * s
    rows = [('IP address', dev['ip']), ('Ping', 'no reply' if dev['rtt'] is None else f'{dev["rtt"]:.1f} ms'), ('MAC address', dev['mac']),
            ('Maker', dev['vendor'] or ('' if G.vendor or DEMO else 'turn on Vendor lookup to look it up')), ('mDNS name', dev['mdns']), ('DNS name', dev['dns']),
            ('NetBIOS name', dev['netbios']), ('UPnP server', dev['upnp']), ('UPnP address', dev['location']), ('mDNS services', ', '.join(dev['services'])),
            ('Open ports', ', '.join(f'{p} {COMMON_PORTS.get(p, "")}'.strip() for p in dev['ports'])), ('Found by', found_by(dev))]
    for label, value in rows:
        plan.append(('label', y, label.upper()))
        y += 17 * s
        for line in wrap(value or '-', value_f, inner, 8):
            plan.append(('value', y, line, bool(value)))
            y += 19 * s
        y += 9 * s
    height = max(ph, round(y + pad))
    p = Pic(pw, height, c['page'])
    p.line((0.5, 0, 0.5, height), c['line'], 1)
    for item in plan:
        if item[0] == 'text':
            _, xy, words, fnt, (_, kind) = item
            p.text(xy, words, fnt, kind_color(kind, c['page'], 3.0))
        elif item[0] == 'kind':
            ky = item[1]
            r = 5 * s
            p.rect((pad, ky, pad + 12 * s + 2 * r + font(True, 12 * s).getlength(dev['kind']) + 14 * s, ky + 22 * s), 11 * s, fill=c['chip'])
            p.ellipse((pad + 10 * s, ky + 11 * s - r, pad + 10 * s + 2 * r, ky + 11 * s + r), fill=kind_color(dev['kind'], c['chip'], 1.6))
            p.text((pad + 10 * s + 2 * r + 6 * s, ky + 11 * s), dev['kind'], font(True, 12 * s), kind_color(dev['kind'], c['chip'], 3.0))
            p.text((pad + 12 * s + 2 * r + font(True, 12 * s).getlength(dev['kind']) + 26 * s, ky + 11 * s), rtt_text(dev), font(False, 12 * s), c['dim'])
        elif item[0] == 'button':
            _, box, words, action, tip = item
            main = action == 'popen'
            lit = hover == action
            fill = (mix(c['accent'], '#ffffff', 0.15) if lit else c['accent']) if main else (c['chip_hover'] if lit else c['chip'])
            p.rect(box, (box[3] - box[1]) / 2, fill=fill)
            ink = c['on_accent'] if main else c['text']
            if main:                                              # Open + the drawn "opens in your browser" mark, centered together
                left = (box[0] + box[2]) / 2 - (button_f.getlength(words) + 17 * s) / 2
                p.text((left, (box[1] + box[3]) / 2), words, button_f, ink, 'lm')
                p.link_mark((left + button_f.getlength(words) + 5 * s, (box[1] + box[3]) / 2 - 0.5 * s), 12 * s, ink)
            else:
                p.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), words, button_f, ink, 'mm')
            hits.append((*box, action, dev['ip'], tip))
        elif item[0] == 'label':
            p.text((pad, item[1] + 7 * s), item[2], label_f, c['dim'])
        elif item[0] == 'value':
            p.text((pad, item[1] + 9 * s), item[2], value_f, c['text'] if item[3] else mix(c['dim'], c['page'], 0.3))
    draw_close(p, close, hover == 'close', c, s)
    hits.append((*close, 'details', None, 'Hide the Details panel  (Ctrl+D)'))
    return p.render(), hits, height


def draw_close(p, box, lit, c, s):
    x0, y0, x1, y1 = box
    if lit:
        p.ellipse(box, fill='#c0392b')
    m = 8 * s
    color = '#ffffff' if lit else c['dim']
    p.line((x0 + m, y0 + m, x1 - m, y1 - m), color, 1.6 * s)
    p.line((x0 + m, y1 - m, x1 - m, y0 + m), color, 1.6 * s)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Drawing the devices part: the kinds strip, tiles or list, the scroll bar, the Details panel
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def start_graph(window, key):
    """ A Graph ready to draw on: its real size now, one unit = one pixel, y down (the first mouse rule: tell the Graph its real size) """
    graph = window[key]
    canvas = graph.Widget
    w, h = max(1, canvas.winfo_width()), max(1, canvas.winfo_height())
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, h), (w, 0))
    canvas.delete('all')
    G.hits[key] = []
    G.on_canvas[key] = []
    return canvas, w, h


def show(canvas, key, pic, x, y):
    G.on_canvas[key].append(pic)
    canvas.create_image(round(x), round(y), image=pic, anchor='nw')


def hit(key, x0, y0, x1, y1, action, value=None, hint=''):
    G.hits[key].append((x0, y0, x1, y1, action, value, hint))


def main_layout(w, h):
    """ Where everything goes in the devices part for a Graph of w x h: the panel, the kinds strip, the devices and their positions """
    s = G.scale
    panel_w = 0
    if G.details:
        panel_w = round(min(360 * s, max(260 * s, w * 0.3)))
        if w - panel_w < 300 * s:
            panel_w = round(max(230 * s, w - 300 * s))
        if panel_w < 230 * s or w - panel_w < 220 * s:
            panel_w = 0                                           # too narrow for both: the devices get it all (Ctrl+D or Enter still shows the panel then)
    cw = w - panel_w
    legend_h, chips, legend_rows = legend_layout(cw)
    fixed = legend_rows <= 2                                      # more rows than that (a narrow window): the kinds scroll away with the devices
    lead = 0 if fixed else legend_h                               # where the devices start in the scrolled part
    sb = round(14 * s)
    shown = shown_devices()
    items, extra = [], {}
    if G.view == 'tiles':
        base, gap = ZOOMS[G.zoom][0] * s, round(GAP * s)
        usable = cw - sb - gap
        cols = max(1, int((usable) // (base + gap)))
        tile_w = int((usable - gap * cols) // cols)
        tile_w = max(round(140 * s), tile_w - tile_w % 4)         # in steps of 4 pixels, so a small resize uses the pictures already made
        left = gap + max(0, (usable - cols * (tile_w + gap)) // 2)
        tile_h = tile_height()
        for i, d in enumerate(shown):
            r, col = divmod(i, cols)
            x0, y0 = left + col * (tile_w + gap), lead + gap + r * (tile_h + gap)
            items.append((d, x0, y0, x0 + tile_w, y0 + tile_h))
        rows = (len(shown) + cols - 1) // cols
        content_h = lead + gap + rows * (tile_h + gap)
        top = legend_h if fixed else 0
        head_at = None
        extra = dict(cols=cols, tile_w=tile_w, tile_h=tile_h)
    else:
        rh = row_height()
        cols = list_columns(cw - sb)
        head_h = round(rh * 1.05)
        lead += 0 if fixed else head_h
        for i, d in enumerate(shown):
            items.append((d, 0, lead + i * rh, cw - sb, lead + (i + 1) * rh))
        content_h = lead + len(shown) * rh
        top = legend_h + head_h if fixed else 0
        head_at = legend_h if fixed else None                     # None: the heading scrolls too, just under the kinds
        extra = dict(cols=cols, row_h=rh, head_h=head_h)
    view = (0, top, cw - sb, h)
    return dict(w=w, h=h, panel_w=panel_w, cw=cw, sb=sb, legend_h=legend_h, chips=chips, fixed=fixed, head_at=head_at, shown=shown, items=items,
                content_h=content_h, view=view, **extra)


def clamp_scroll(lay):
    room = max(0, lay['content_h'] - (lay['view'][3] - lay['view'][1]))
    G.scroll = max(0, min(G.scroll, room))
    return room


def draw_main(window):
    canvas, w, h = start_graph(window, K_MAIN)
    c, s = colors(), G.scale
    lay = G.boxes = main_layout(w, h)
    room = clamp_scroll(lay)
    vx0, vy0, vx1, vy1 = lay['view']
    hover = G.hover[1] if G.hover[0] == K_MAIN else None
    look = look_key()
    for i, (d, x0, y0, x1, y1) in enumerate(lay['items']):
        top, bottom = vy0 + y0 - G.scroll, vy0 + y1 - G.scroll
        if bottom < vy0 or top > vy1:
            continue
        ip = d['ip']
        picked, lit = ip == G.picked, hover == ('pick', ip) or hover == ('open', ip)
        stale = G.scanning and ip not in G.seen
        rev = G.rev.get(ip, 0)
        if G.view == 'tiles':
            key = ('tile', ip, rev, x1 - x0, y1 - y0, picked, lit, stale, G.zoom, look)
            if key not in G.pics:
                im, G.links[key] = tile_picture(d, x1 - x0, y1 - y0, picked, lit, stale)
                photo(key, lambda im=im: im)
            pic, link = G.pics[key], G.links.get(key)
            show(canvas, K_MAIN, pic, x0, top)
            hit(K_MAIN, x0, max(top, vy0), x1, min(bottom, vy1), 'pick', ip, f'{d["name"]}  -  click: details,  double-click / Enter: show the Details panel')
            if link and top + link[3] > vy0:
                hit(K_MAIN, x0 + link[0], max(top + link[1], vy0), x0 + link[2], top + link[3], 'open', ip, f'Open {web_url(d)} in your browser')
        else:
            pic = photo(('row', ip, rev, x1 - x0, y1 - y0, tuple(lay['cols']), picked, lit, stale, i % 2, G.zoom, look),
                        lambda: row_picture(d, x1 - x0, y1 - y0, lay['cols'], picked, lit, stale, i % 2))
            show(canvas, K_MAIN, pic, x0, top)
            hit(K_MAIN, x0, max(top, vy0), x1, min(bottom, vy1), 'pick', ip, f'{d["name"]}  {d["ip"]}  -  double-click / Enter: show the Details panel')
    if not lay['items']:                                          # nothing to show: say why
        if not G.devices:
            words = 'Scanning - devices appear here as they are found ...' if G.scanning else 'No devices yet - press Scan (F5)'
        elif G.search:
            words = f'Nothing matches "{G.search}" - Esc clears the search'
        else:
            words = 'Nothing to show - click the kinds you want above, or All to show every kind'
        canvas.create_text((vx0 + vx1) / 2, vy0 + 60 * s, text=words, fill=c['dim'], font=('Segoe UI', 13), anchor='n', width=max(100, vx1 - vx0 - 40 * s))
    if G.view == 'list':                                          # the list's heading line, on top of the rows scrolled under it
        hk = hover[1] if isinstance(hover, tuple) and hover[0] == 'sort' else None
        pic = photo(('head', lay['cw'] - lay['sb'], lay['head_h'], tuple(lay['cols']), G.sort, hk, look),
                    lambda: list_head_picture(lay['cw'] - lay['sb'], lay['head_h'], lay['cols'], hk))
        hy = lay['head_at'] if lay['fixed'] else vy0 + lay['legend_h'] - G.scroll
        show(canvas, K_MAIN, pic, 0, hy)
        hit(K_MAIN, 0, hy, lay['cw'], hy + lay['head_h'], None)
        for key, head, x0, x1 in lay['cols']:
            if head:
                again = '  (click again: the other way round)' if G.sort[0] == key else ''
                hit(K_MAIN, x0, hy, x1, hy + lay['head_h'], 'sort', key, f'Sort by {head}{again}')
    hk = hover[1] if isinstance(hover, tuple) and hover[0] == 'kind' else None   # the kinds strip, on top of anything scrolled under it
    pic = photo(('legend', lay['cw'], lay['legend_h'], tuple(sorted(G.hidden)), tuple(ch[5] for ch in lay['chips']), hk, look),
                lambda: legend_picture(lay['cw'], lay['legend_h'], lay['chips'], hk))
    ly = 0 if lay['fixed'] else vy0 - G.scroll
    show(canvas, K_MAIN, pic, 0, ly)
    hit(K_MAIN, 0, ly, lay['cw'] - (0 if lay['fixed'] else lay['sb']), ly + lay['legend_h'], None)
    for kind, x0, y0, x1, y1, count in lay['chips']:
        if kind == '*All':
            hit(K_MAIN, x0, ly + y0, x1, ly + y1, 'kinds', 'all', 'Show every kind of device')
        elif kind == '*None':
            hit(K_MAIN, x0, ly + y0, x1, ly + y1, 'kinds', 'none', 'Hide every kind - then click the kinds you want to see')
        else:
            hit(K_MAIN, x0, ly + y0, x1, ly + y1, 'kind', kind,
                f'{"Hide" if kind not in G.hidden else "Show"} the {kind} devices  ({count.strip() or 0} found)  -  double-click: only {kind}')
    draw_scrollbar(canvas, lay, room, hover)
    if lay['panel_w']:
        draw_panel(canvas, lay, hover)


def draw_scrollbar(canvas, lay, room, hover):
    c, s = colors(), G.scale
    vx0, vy0, vx1, vy1 = lay['view']
    x = vx1 + lay['sb'] / 2
    if room <= 0:
        return
    track = (vy0 + 4 * s, vy1 - 4 * s)
    span = track[1] - track[0]
    view_h = vy1 - vy0
    thumb_h = max(36 * s, span * view_h / lay['content_h'])
    t0 = track[0] + (span - thumb_h) * G.scroll / room
    lit = hover and hover[0] in ('thumb', 'track') or (G.down and G.down[3] == 'thumb')
    width = (8 if lit else 6) * s
    canvas.create_line(x, track[0] + width / 2, x, track[1] - width / 2, fill=mix(c['page'], c['text'], 0.07), width=width, capstyle='round')
    canvas.create_line(x, t0 + width / 2, x, t0 + thumb_h - width / 2, fill=mix(c['page'], c['text'], 0.45 if lit else 0.3), width=width, capstyle='round')
    hit(K_MAIN, x - 8 * s, track[0], x + 8 * s, t0, 'track', -1, 'Page up')
    hit(K_MAIN, x - 8 * s, t0 + thumb_h, x + 8 * s, track[1], 'track', 1, 'Page down')
    hit(K_MAIN, x - 8 * s, t0, x + 8 * s, t0 + thumb_h, 'thumb', None, 'Drag to scroll  (or the mouse wheel anywhere over the devices)')
    G.boxes['thumb'] = (t0, thumb_h, span, room)


def draw_panel(canvas, lay, hover):
    x0, pw, ph = lay['cw'], lay['panel_w'], lay['h']
    dev = device(G.picked)
    hv = hover[0] if isinstance(hover, tuple) and hover[0] in ('copy', 'copy_all', 'popen') else 'close' if hover == ('details', None) else None
    key = ('panel', G.picked, G.rev.get(G.picked, 0), pw, ph, hv, G.vendor, look_key())
    if key not in G.pics:
        im, hits, height = panel_picture(dev, pw, ph, hv)
        G.pics[('panel hits',) + key] = (im, hits, height)
    im, hits, height = G.pics[('panel hits',) + key]
    G.panel_scroll = max(0, min(G.panel_scroll, height - ph))
    crop_key = key + (G.panel_scroll,)
    pic = photo(('panel crop',) + crop_key, lambda: im.crop((0, G.panel_scroll, pw, G.panel_scroll + ph)))
    show(canvas, K_MAIN, pic, x0, 0)
    hit(K_MAIN, x0, 0, x0 + pw, ph, 'panel', None, 'Details  -  the mouse wheel scrolls them' if height > ph else '')
    for hx0, hy0, hx1, hy1, action, value, tip in hits:
        y0, y1 = hy0 - G.panel_scroll, hy1 - G.panel_scroll
        if y1 > 0 and y0 < ph:
            hit(K_MAIN, x0 + hx0, y0, x0 + hx1, y1, action, value, tip)
    G.boxes['panel_room'] = height - ph


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# The header and the bottom line
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def head_buttons():
    """ The header's buttons: (id, words, kind, on, enabled, hint) - kind 'main' (accent), 'push', 'seg' (Tiles | List), 'toggle' """
    must = [('scan', 'Scan', 'main', False, not G.scanning, 'Look for the devices on the subnet  (F5)'),
            ('stop', 'Stop', 'push', False, G.scanning, 'End the scan now'),
            ('diag', 'Diagnose', 'push', False, not DEMO, 'Save what the network commands say - for a scan that finds nothing' if not DEMO else 'Not in the demo')]
    more = [('tiles', 'Tiles', 'seg', G.view == 'tiles', True, 'Tiles  (Ctrl+1)'), ('list', 'List', 'seg', G.view == 'list', True, 'One line per device  (Ctrl+2)'),
            ('details', 'Details', 'toggle', G.details, True, f'{"Hide" if G.details else "Show"} the Details panel  (Ctrl+D)'),
            ('vendor', 'Vendor lookup', 'toggle', G.vendor, not DEMO,
             'Look up each MAC address\'s maker online (api.macvendors.com) after a scan' if not DEMO else 'Not in the demo')]
    return must, more


def head_layout(w):
    """ Where the header's parts go: everything on one line when it fits, else the view buttons on a second line.  The title gets shorter (...) first """
    s = G.scale
    bf = font(True, 12.5 * s)
    m, gap = 10 * s, 8 * s
    must, more = head_buttons()

    def width(b):
        return bf.getlength(b[1]) + (34 if b[2] == 'toggle' else 26) * s

    def place(group, right):
        out, x = [], right
        for b in reversed(group):
            bw = width(b)
            out.insert(0, (b, x - bw, x))
            x -= bw + (0 if b[2] == 'seg' and b[0] == 'list' else gap)
        return out, x
    left_min = m + 34 * s + 8 * s + 24 * s + 12 * s               # Back, the icon
    one, x = place(more + must, w - m)
    if x >= left_min + 60 * s:
        return 1, one, x
    line1, x1 = place(must, w - m)
    line2, _ = place(more, w - m)
    return 2, line1 + [(b, a, z, 2) for b, a, z in line2], x1


def draw_head(window):
    canvas, w, h = start_graph(window, K_HEAD)
    c, s = colors(), G.scale
    lines, placed, title_right = head_layout(w)
    if lines != G.head_lines:                                     # one line more or less: the header changes height, and is drawn again after that
        G.head_lines = lines
        canvas.configure(height=round(HEAD_H * s * lines))
        window.TKroot.update_idletasks()                          # the new sizes, without handling other events in the middle of a drawing
        canvas, w, h = start_graph(window, K_HEAD)
    hover = G.hover[1] if G.hover[0] == K_HEAD else None
    p = Pic(w, h, c['page'])
    line_h = HEAD_H * s
    cy = line_h / 2
    m = 10 * s
    back = back_name(-1)                                          # the < button: grey when there is nowhere to go back to
    bx0, bx1 = m, m + 30 * s
    lit = hover == 'back' and back
    p.ellipse((bx0, cy - 15 * s, bx1, cy + 15 * s), fill=c['chip_hover'] if lit else c['chip'] if back else None,
              outline=None if back else mix(c['line'], c['page'], 0.3), width=1 * s)
    color = c['text'] if back else mix(c['dim'], c['page'], 0.45)
    p.line((bx0 + 17 * s, cy - 7 * s, bx0 + 11 * s, cy, bx0 + 17 * s, cy + 7 * s), color, 2.2 * s)
    hit(K_HEAD, bx0, cy - 15 * s, bx1, cy + 15 * s, 'back', None, f'Back to {back}  (Alt+Left, the mouse\'s Back button)' if back else 'Nothing to go back to')
    x = bx1 + 10 * s
    if G.icon_pic is None or G.icon_pic.width != round(24 * s):
        G.icon_pic = Image.open(io.BytesIO(base64.b64decode(ICON))).convert('RGBA').resize((round(24 * s), round(24 * s)), Image.LANCZOS)
    icon_at = (round(x), round(cy - 12 * s))
    x += 24 * s + 10 * s
    room = title_right - 12 * s - x
    title_f, ver_f, tag_f = font(True, 13 * s), font(False, 11 * s), font(True, 11 * s)
    tags = []
    if update_tag():
        tags.append(('news', 'UPDATED', C_TAG, C_TAG_TEXT, f'Updated from {update_tag()} - click UPDATED to see what changed'))
    if DEMO:
        tags.append(('demo', 'DEMO', c['chip'], c['dim'], 'Made-up devices - nothing on your network is scanned'))
    tags_w = sum(tag_f.getlength(t[1]) + 18 * s + 6 * s for t in tags)
    ver = VERSION
    name = fit('NETWORK SCANNER', title_f, max(0, room - ver_f.getlength(ver) - 8 * s - tags_w))
    if name:
        p.text((x, cy), name, title_f, c['dim'])
        x += title_f.getlength(name) + 8 * s
        if x + ver_f.getlength(ver) + tags_w <= title_right:
            p.text((x, cy + 1 * s), ver, ver_f, mix(c['dim'], c['page'], 0.25))
            x += ver_f.getlength(ver) + 8 * s
    for tag, words, fill, ink, tip in tags:
        tw = tag_f.getlength(words) + 18 * s
        if x + tw > title_right:
            break
        p.rect((x, cy - 10 * s, x + tw, cy + 10 * s), 10 * s, fill=fill)
        p.text((x + tw / 2, cy), words, tag_f, ink, 'mm')
        hit(K_HEAD, x, cy - 10 * s, x + tw, cy + 10 * s, tag if tag == 'news' else None, None, tip)
        x += tw + 6 * s
    bf = font(True, 12.5 * s)
    for item in placed:
        b, x0, x1 = item[:3]
        row = item[3] if len(item) > 3 else 1
        bid, words, kind, on, enabled, tip = b
        by = (row - 1) * line_h + line_h / 2
        box = (x0, by - 15 * s, x1, by + 15 * s)
        lit = hover == bid and enabled
        if kind == 'main':
            fill, ink = (mix(c['accent'], '#ffffff', 0.15) if lit else c['accent']) if enabled else c['chip'], c['on_accent'] if enabled else mix(c['dim'], c['page'], 0.3)
        elif kind == 'seg':
            fill = c['accent'] if on else c['chip_hover'] if lit else c['chip']
            ink = c['on_accent'] if on else c['text']
        else:
            fill = c['chip_hover'] if lit else c['chip']
            ink = c['text'] if enabled else mix(c['dim'], c['page'], 0.35)
        if kind == 'seg':                                         # Tiles | List: one pill in two halves
            left = bid == 'tiles'
            r = 15 * s
            p.rect((x0, box[1], x1 + r, box[3]) if left else box, r, fill=c['chip'])
            if on or lit:
                p.rect(box, r, fill=fill)
        else:
            p.rect(box, 15 * s, fill=fill)
        tx = (x0 + x1) / 2
        if kind == 'toggle':                                      # a tick box drawn in the pill
            bxl = x0 + 10 * s
            p.rect((bxl, by - 6 * s, bxl + 12 * s, by + 6 * s), 3 * s, fill=c['accent'] if on else None, outline=None if on else c['dim'], width=1.3 * s)
            if on:
                p.line((bxl + 2.5 * s, by, bxl + 5 * s, by + 3 * s, bxl + 9.5 * s, by - 3.5 * s), c['on_accent'], 1.8 * s)
            tx = bxl + 12 * s + (x1 - bxl - 12 * s) / 2
        p.text((tx, by), words, bf, ink, 'mm')
        hit(K_HEAD, x0, box[1], x1, box[3], bid if enabled else None, None, tip)
    p.line((0, h - 0.5, w, h - 0.5), c['line'], 1)
    im = p.render()
    im.alpha_composite(G.icon_pic, icon_at)
    show(canvas, K_HEAD, fresh(im), 0, 0)


def bottom_words():
    """ The bottom line: what the part under the mouse does, else the last message, else the scan's state """
    if G.hint:
        return G.hint, 'hint'
    if G.note[0] and time.monotonic() < G.note[1]:
        return G.note[0], 'note'
    return G.status, 'status'


def count_words():
    if not G.devices:
        return ''
    shown = len(shown_devices())
    return f'{shown} devices' if shown == len(G.devices) else f'{shown} of {len(G.devices)} devices shown'


def draw_foot(window):
    canvas, w, h = start_graph(window, K_FOOT)
    c, s = colors(), G.scale
    p = Pic(w, h, c['page'])
    p.line((0, 0.5, w, 0.5), c['line'], 1)
    if G.scanning or 0 < G.progress < 1:
        p.rect((0, 0, w, 3 * s), 0, fill=mix(c['page'], c['text'], 0.08))
        p.rect((0, 0, max(3 * s, w * G.progress), 3 * s), 0, fill=c['accent'])
    fnt = font(False, 12 * s)
    right = count_words()
    rw = fnt.getlength(right) + 14 * s if right else 0
    words, kind = bottom_words()
    p.text((12 * s, h / 2 + 1 * s), fit(words, fnt, w - 24 * s - rw), fnt, c['text'] if kind == 'note' else c['dim'])
    if right:
        p.text((w - 12 * s, h / 2 + 1 * s), right, fnt, c['dim'], 'rm')
    show(canvas, K_FOOT, fresh(p.render()), 0, 0)


def draw(window, parts=(K_HEAD, K_MAIN, K_FOOT)):
    for key in parts:
        try:
            {K_HEAD: draw_head, K_MAIN: draw_main, K_FOOT: draw_foot}[key](window)
        except tk.TclError:                                       # the window is going away
            pass


def note(window, words, seconds=4):
    G.note = (words, time.monotonic() + seconds)
    draw(window, (K_FOOT,))


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Window, look, menu
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def window_title():
    return f'{APP_NAME} {VERSION}' + ('  -  demo, made-up devices' if DEMO else '') + ('  -  UPDATED' if update_tag() else '')


def paint(window):
    """ The theme on everything that isn't drawn: the window, the labels, the two boxes - and the title bar on Windows """
    c = colors()

    def walk(widget):
        cls = widget.winfo_class()
        try:
            if cls in ('Frame', 'Toplevel', 'Tk', 'Canvas', 'Labelframe'):
                widget.configure(bg=c['page'])
                if cls == 'Canvas':
                    widget.configure(highlightthickness=0, bd=0)
            elif cls == 'Label':
                widget.configure(bg=c['page'], fg=c['dim'])
            elif cls == 'Entry':
                widget.configure(bg=c['input'], fg=c['text'], insertbackground=c['text'], selectbackground=c['accent'], selectforeground=c['on_accent'],
                                 relief='flat', bd=0, highlightthickness=1, highlightbackground=c['line'], highlightcolor=c['accent'],
                                 disabledbackground=c['input'], readonlybackground=c['input'], disabledforeground=c['dim'])
        except tk.TclError:
            pass
        for child in widget.winfo_children():
            if child.winfo_class() != 'Menu':
                walk(child)
    walk(window.TKroot)
    title_bar(window, c)


def title_bar(window, c):
    """ Windows: a dark title bar on a dark theme, and on Windows 11 the title bar in the window's own colors """
    if not sg.running_windows():
        return
    try:
        import ctypes
        root = window.TKroot
        root.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root.winfo_id())
        dwm = ctypes.windll.dwmapi
        ref = lambda color: ctypes.c_int(int(color[5:7], 16) << 16 | int(color[3:5], 16) << 8 | int(color[1:3], 16))
        dwm.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(1 if c['dark'] else 0)), 4)     # dark mode title bar
        for attribute, color in ((34, c['line']), (35, c['page']), (36, c['text'])):                    # border, caption, caption text (Windows 11)
            dwm.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(ref(color)), 4)
        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x27)                                     # draw the frame again
    except Exception:
        pass


def tick(on):
    return '✓ ' if on else '    '


def make_menu():
    dev = device(G.picked)
    mine = []
    if dev:
        name = dev['name'] if len(dev['name']) < 32 else dev['name'][:30] + '…'
        mine = [f'    Copy {dev["ip"]}   (Ctrl+C)::{M_COPY}', f'    Copy all about {name}::{M_COPY_ALL}']
        mine += [f'    Open {web_url(dev)}::{M_OPEN}'] if web_url(dev) else []
        mine += ['---']
    theme = lambda n: f'{tick(n == G.theme)}{n}::{KT_THEME(n)}'
    return ['', [f'    Scan   (F5)::{M_SCAN}', f'    Stop::{M_STOP}', *([f'    Diagnose::{M_DIAG}'] if not DEMO else []), '---', *mine,
                 f'{tick(G.view == "tiles")}Tiles   (Ctrl+1)::{M_TILES}', f'{tick(G.view == "list")}List   (Ctrl+2)::{M_LIST}',
                 f'{tick(G.details)}Details panel   (Ctrl+D)::{M_DETAILS}', f'    Search   (Ctrl+F)::{M_FIND}',
                 '    Size   (Ctrl + wheel)', [f'{tick(z == G.zoom)}{z}::{KT_ZOOM_TO(z)}' for z in ZOOMS],
                 *([f'{tick(G.vendor)}Online MAC vendor lookup::{M_VENDOR}'] if not DEMO else []), '---',
                 '    Theme', [theme(n) for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],
                 f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}', *accent_menu(tick), '---',
                 f"    What's new...::{M_NEWS}", '    Edit Me::Edit Me', f'    Version {VERSION}::Version', *update_menu(tick), f'    Exit::{K_EXIT}']]


def menu_colors():
    c = colors()
    return mix(c['page'], c['text'], 0.04), c['text']


def theme_swatch(name):
    """ A tiny card in a theme's colors, beside its name in the Theme menu.  Made once and kept - tk drops images nobody holds """
    if (name, G.bright) not in G.swatches:
        T, z = theme_colors(name), G.scale * 4
        im = Image.new('RGBA', (round(34 * z), round(20 * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=5 * z, fill=T['card'], outline=C_SWATCH_EDGE, width=round(z))
        d.rounded_rectangle((6 * z, 5.5 * z, 25 * z, 9 * z), radius=1.5 * z, fill=T['text'])
        d.rounded_rectangle((6 * z, 12 * z, 17 * z, 14.5 * z), radius=1.2 * z, fill=T['dim'])
        buf = io.BytesIO()
        im.resize((round(im.width / 4), round(im.height / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[(name, G.bright)] = tk.PhotoImage(master=G.window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[(name, G.bright)]


def menu_arrows(menu, dark):
    """ Windows draws a sub-menu's arrow in Windows' own menu-text color (black, white only on the lit row) whatever the menu's colors, so on a
        dark menu it can't be seen.  This puts a › in the menu's own text color at the right end of each sub-menu's label instead.  Windows
        and dark menus only - a light menu shows Windows' arrow, and Linux / Mac draw theirs in the menu's colors.  Safe to call again.
        3.0.2: one font for all the measuring (menu_font) and each label measured once (label_width), the spaces worked out, not tried one by one.
        3.0.1 made a new font per menu and measured ~1200 times per menu change - with no ✓ in Segoe UI, Windows Tk then looks through the
        installed fonts for one that has it, for each new font: many fonts installed = the window froze for many seconds """
    if not (dark and sg.running_windows()) or menu.index('end') is None:
        return
    labels = {}
    for i in range(menu.index('end') + 1):
        if menu.type(i) in ('command', 'cascade', 'checkbutton', 'radiobutton'):
            label = menu.entrycget(i, 'label')
            labels[i] = label.rstrip(' \u2009\u203a') if menu.type(i) == 'cascade' and label.endswith('\u203a') else label
    cascades = [i for i in labels if menu.type(i) == 'cascade']
    if not cascades:
        return
    end = max(label_width(text) for text in labels.values()) + label_width('      \u203a')     # the arrows line up a little past the longest label
    space, thin = max(1, label_width(' ')), max(1, label_width('\u2009'))
    for i in cascades:
        label = labels[i] + '  '
        room = max(0, end - label_width(label + '\u203a'))
        spaces = min(200, int(room // space))
        thins = min(20, int((room - spaces * space) // thin))
        menu.entryconfigure(i, label=label + ' ' * spaces + '\u2009' * thins + '\u203a')


def label_width(text):
    """ A menu label's width in the menu font - measured once per label, with the one menu font """
    if text not in G.label_w:
        if G.menu_font is None:
            G.menu_font = tk.font.Font(root=G.window.TKroot, font=FONT_MENU)
        G.label_w[text] = G.menu_font.measure(text)
    return G.label_w[text]


def style_menus(window):
    """ tk draws menus Windows-gray: recolor every right-click menu and its sub-menus in the theme's colors, flat and compact, a chip beside each theme """
    bg, fg = menu_colors()

    def style(menu):
        menu.configure(bg=bg, fg=fg, activebackground=C_MENU_SEL, activeforeground='#ffffff', disabledforeground=mix(fg, bg, 0.55), bd=0, activeborderwidth=1,
                       relief='flat', font=FONT_MENU)
        first_light = True
        for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0):
            name = menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None
            if name in THEMES:
                menu.entryconfigure(i, image=theme_swatch(name), compound='left')
                if first_light and is_light(THEMES[name]['card']):
                    menu.entryconfigure(i, columnbreak=1)                     # the light themes get a column of their own
                    first_light = False
        menu_arrows(menu, not is_light(bg))
        for child in menu.winfo_children():
            if isinstance(child, tk.Menu):
                style(child)
    menus = {id(m): m for m in [window.TKRightClickMenu] + [e.TKRightClickMenu for e in window.element_list()] if m is not None}
    for menu in menus.values():
        try:
            style(menu)
        except tk.TclError:
            pass


def apply_menu(window, force=False):
    """ The right-click menu again (a tick moved, another device picked), on every part of the window.  Only when it changed (or force: new colors) -
        each time makes a menu per part of the window, its sub-menus and their pictures """
    menu = make_menu()
    if menu == G.menu_made and not force:
        return
    G.menu_made = menu
    first = True
    for element in window.element_list():
        try:
            element.set_right_click_menu(menu, propogate_to_window=first)
            first = False
        except Exception:
            pass
    style_menus(window)


def apply_look(window):
    """ After a theme, Brightness or accent change: everything in the new colors """
    paint(window)
    apply_menu(window, True)
    draw(window)


def redraw(window):                                               # the Brightness panel calls this as its knob moves
    paint(window)
    draw(window)


def make_window():
    c = colors()
    subnet = DEMO_SUBNET if DEMO else sg.user_settings_get_entry(K_SUBNET, '') or (local_ip() + '/24')
    geometry = sg.user_settings_get_entry(S_GEOMETRY, None)
    size, location = (1280, 860), (None, None)
    if isinstance(geometry, (list, tuple)) and len(geometry) == 4 and not DEMO:
        size, location = (geometry[0], geometry[1]), (geometry[2], geometry[3])
    graph = dict(enable_events=True, drag_submits=True, motion_events=True, expand_x=True, pad=(0, 0), background_color=c['page'])
    boxes = [sg.Text('Subnet', pad=((12, 6), (6, 6)), background_color=c['page'], text_color=c['dim']),
             sg.Input(subnet, key=K_SUBNET, size=(18, 1), border_width=0, font=('Segoe UI', 11), background_color=c['input'], text_color=c['text'],
                      tooltip=' The addresses to scan - Enter scans them ', disabled=DEMO),
             sg.Text('Search', pad=((18, 6), (6, 6)), background_color=c['page'], text_color=c['dim']),
             sg.Input('', key=K_SEARCH, size=(16, 1), expand_x=True, enable_events=True, border_width=0, font=('Segoe UI', 11), pad=((0, 12), (6, 6)),
                      background_color=c['input'], text_color=c['text'], tooltip=' Names, IPs, MACs, makers, services, kinds  (Ctrl+F)   Esc clears it ')]
    layout = [[sg.Graph((300, HEAD_H), (0, HEAD_H), (300, 0), key=K_HEAD, **graph)],
              boxes,
              [sg.Graph((420, 240), (0, 240), (420, 0), key=K_MAIN, expand_y=True, **graph)],
              [sg.Graph((300, FOOT_H), (0, FOOT_H), (300, 0), key=K_FOOT, **graph)]]
    window = sg.Window(window_title(), layout, size=size, location=location, resizable=True, finalize=True, margins=(0, 0), element_padding=(0, 0),
                       font=('Segoe UI', 10), icon=ICON, enable_close_attempted_event=True, background_color=c['page'], right_click_menu=make_menu(),
                       right_click_menu_background_color=menu_colors()[0], right_click_menu_text_color=menu_colors()[1],
                       right_click_menu_selected_colors=('#ffffff', C_MENU_SEL), right_click_menu_font=FONT_MENU)
    G.window = window
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)
    window[K_HEAD].Widget.configure(height=round(HEAD_H * G.scale))
    window[K_FOOT].Widget.configure(height=round(FOOT_H * G.scale))
    bind_all(window)
    paint(window)
    apply_menu(window)
    fit_min_size(window)
    return window


def fit_min_size(window):
    """ The smallest the window may get: what its rows need at their layout size - so its bottom rows are never cut off """
    root = window.TKroot
    root.update_idletasks()
    window.set_min_size((min(max(root.winfo_reqwidth(), round(560 * G.scale)), root.winfo_screenwidth() - 40),
                         min(max(root.winfo_reqheight(), round(400 * G.scale)), root.winfo_screenheight() - 80)))


def bind_all(window):
    """ The mouse and keys.  Graph events come from PySimpleGUI (drag_submits: press / drag, +UP, +MOVE); the rest are bound here """
    root = window.TKroot
    for key in (K_HEAD, K_MAIN, K_FOOT):
        window[key].bind('<Leave>', '+LEAVE')
        window[key].Widget.bind('<Configure>', lambda e: schedule_redraw(window), add='+')
    window[K_MAIN].bind('<Double-Button-1>', '+DOUBLE')
    window[K_MAIN].bind('<MouseWheel>', '+WHEEL')
    if not sg.running_windows():                                  # the wheel arrives as buttons 4 / 5 on Linux (on Windows those are Back / Forward)
        window[K_MAIN].bind('<Button-4>', '+WHEELUP')
        window[K_MAIN].bind('<Button-5>', '+WHEELDOWN')
        root.bind('<Control-Button-4>', lambda e: zoom_wheel(window, e, 1), add='+')
        root.bind('<Control-Button-5>', lambda e: zoom_wheel(window, e, -1), add='+')
    root.bind('<Control-MouseWheel>', lambda e: zoom_wheel(window, e, 1 if e.delta > 0 else -1), add='+')
    window[K_MAIN].Widget.bind('<ButtonPress-3>', lambda e: right_pick(window, e), add='+')
    for name in ('Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End', 'Return', 'Escape', 'F5'):
        window.bind(f'<{name}>', K_KEY + name)
    for seq, name in (('<Control-f>', 'find'), ('<Control-F>', 'find'), ('<Control-d>', 'details'), ('<Control-D>', 'details'),
                      ('<Control-C>', 'copy'), ('<Control-Key-1>', 'tiles'), ('<Control-Key-2>', 'list'), ('<Control-c>', 'copy'),
                      ('<Control-equal>', 'bigger'), ('<Control-plus>', 'bigger'), ('<Control-KP_Add>', 'bigger'), ('<Control-minus>', 'smaller'),
                      ('<Control-KP_Subtract>', 'smaller'), ('<Control-Key-0>', 'normal')):
        window.bind(seq, K_KEY + name)
    back_bind(window)


def schedule_redraw(window):
    """ A part changed size: draw again a moment after the LAST change, not at every pixel of a drag """
    if G.redraw_job:
        window.TKroot.after_cancel(G.redraw_job)
    G.redraw_job = window.TKroot.after(90, lambda: window.write_event_value(K_REDRAW, None))


def zoom_wheel(window, e, step):
    alt = e.state & (0x20000 if sg.running_windows() else 0x8)    # Ctrl+Alt belongs to system hotkeys
    if not alt:
        window.write_event_value(K_ZOOM, (step, e.x_root, e.y_root))


def right_pick(window, e):
    """ A right-click on a device picks it first, so the menu that opens names it """
    xy = (e.x, e.y)
    part = part_at(K_MAIN, xy)
    if part and part[0] in ('pick', 'open') and part[1] != G.picked:
        G.picked = part[1]
        draw(window, (K_MAIN,))
        apply_menu(window)
        window.write_event_value(K_RIGHT_PICK, None)


def part_at(key, xy):
    """ (action, value, hint) of the topmost box under the spot, or None """
    if xy is None or xy[0] is None:
        return None
    x, y = xy
    for x0, y0, x1, y1, action, value, hint_words in reversed(G.hits.get(key, [])):
        if x0 <= x <= x1 and y0 <= y <= y1:
            return action, value, hint_words
    return None


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Moving around
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def item_box(ip):
    """ (x0, y0, x1, y1) of a device in the scrolled part (unscrolled pixels), or None when it isn't shown """
    for d, x0, y0, x1, y1 in G.boxes.get('items', []):
        if d['ip'] == ip:
            return x0, y0, x1, y1
    return None


def keep_in_view(ip):
    box = item_box(ip)
    if not box or not G.boxes:
        return
    vy0, vy1 = G.boxes['view'][1], G.boxes['view'][3]
    view_h, gap = vy1 - vy0, GAP * G.scale if G.view == 'tiles' else 0
    if box[1] - gap < G.scroll:
        G.scroll = max(0, box[1] - gap)
    elif box[3] + gap > G.scroll + view_h:
        G.scroll = box[3] + gap - view_h


def move_pick(window, how):
    """ The arrow keys, PgUp / PgDn, Home / End: another device picked, kept in view """
    lay = G.boxes or main_layout(*graph_size(window))
    shown = [d['ip'] for d in lay['shown']]
    if not shown:
        return
    view_h = lay['view'][3] - lay['view'][1]
    across = lay.get('cols', 1) if G.view == 'tiles' else 1
    per_page = max(1, int(view_h // ((lay.get('tile_h', 0) + GAP * G.scale) if G.view == 'tiles' else lay['row_h']))) * across
    step = {'Left': -1, 'Right': 1, 'Up': -across, 'Down': across, 'Prior': -per_page, 'Next': per_page, 'Home': -len(shown), 'End': len(shown)}[how]
    if G.view == 'list' and how in ('Left', 'Right'):
        return
    i = shown.index(G.picked) if G.picked in shown else (-1 if step > 0 else len(shown))
    G.picked = shown[max(0, min(len(shown) - 1, i + step))]
    G.boxes = main_layout(lay['w'], lay['h'])
    keep_in_view(G.picked)


def set_zoom(window, name, anchor=None):
    """ Bigger / smaller tiles and rows.  anchor = a spot on the devices (Graph pixels): the device under it stays under it """
    if name not in ZOOMS or name == G.zoom:
        return False
    lay = G.boxes
    keep = None
    if lay and lay.get('items'):
        vy0 = lay['view'][1]
        if anchor is None:
            box = item_box(G.picked) if G.picked else None
            anchor = (0, vy0 + ((box[1] + box[3]) / 2 - G.scroll if box else 0))
        y = anchor[1] - vy0 + G.scroll
        def distance(it):                                         # 0 for the device under the spot, else how far it is (across counts less)
            inside = it[2] <= y <= it[4] and it[1] <= anchor[0] <= it[3]
            return 0 if inside else abs((it[2] + it[4]) / 2 - y) + abs((it[1] + it[3]) / 2 - anchor[0]) / 4
        hit_item = min(lay['items'], key=distance)
        frac = (y - hit_item[2]) / max(1, hit_item[4] - hit_item[2])
        keep = (hit_item[0]['ip'], frac, anchor[1] - vy0)
    G.zoom = name
    sg.user_settings_set_entry(S_ZOOM, name)
    if keep and lay:
        G.boxes = main_layout(lay['w'], lay['h'])
        box = item_box(keep[0])
        if box:
            G.scroll = round(box[1] + keep[1] * (box[3] - box[1]) - keep[2])
            clamp_scroll(G.boxes)
    return True


def zoom_step(step):
    names = list(ZOOMS)
    return names[max(0, min(len(names) - 1, names.index(G.zoom) + step))]


def scroll_by(window, pixels):
    G.scroll += pixels
    if G.boxes:
        clamp_scroll(G.boxes)
    draw(window, (K_MAIN,))


def set_view(window, view):
    if view != G.view:
        G.view = view
        sg.user_settings_set_entry(S_VIEW, view)
        G.scroll = 0
        G.boxes = {}
        if G.picked:
            G.boxes = main_layout(*graph_size(window))
            keep_in_view(G.picked)
        draw(window)
        apply_menu(window)


def graph_size(window):
    canvas = window[K_MAIN].Widget
    return max(1, canvas.winfo_width()), max(1, canvas.winfo_height())


def set_details(window, on):
    G.details = on
    sg.user_settings_set_entry(S_DETAILS, on)
    draw(window)
    apply_menu(window)


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Places for Back and Forward
# ----------------------------------------------------------------------------------------------------------------------------------------------------
PLACE = ('view', 'picked', 'search')


def place():
    return dict((name, getattr(G, name)) for name in PLACE)


def place_name():
    dev = device(G.picked)
    return ' - '.join(x for x in ('Tiles' if G.view == 'tiles' else 'List', dev and dev['name'], G.search and f'"{G.search}"') if x)


def show_place(window, where, name, keep):
    for key in PLACE:
        setattr(G, key, where[key])
    window[K_SEARCH].update(G.search)
    G.scroll = keep or 0
    G.boxes = {}
    draw(window)
    apply_menu(window)
    note(window, f'Back to {name}' if name else '')


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Doing things
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def start_scan(window):
    if G.scanning:
        return
    subnet = window[K_SUBNET].get().strip()
    if not DEMO:
        sg.user_settings_set_entry(K_SUBNET, subnet)
    G.scanning, G.progress, G.seen = True, 0.0, set()
    stop_flag.clear()
    G.status = 'Starting the scan ...'
    worker(demo_scan_thread if DEMO else scan_thread, subnet, G.vendor and not DEMO)
    draw(window)
    apply_menu(window)


def found(window, dev):
    """ A device the scan found: new, or the same IP again with what is known now (a maker found earlier is kept) """
    old = device(dev['ip'])
    if old:
        if not dev['vendor'] and old['vendor']:
            dev['vendor'] = old['vendor']
        G.devices[G.devices.index(old)] = dev
    else:
        G.devices.append(dev)
    G.rev[dev['ip']] = G.rev.get(dev['ip'], 0) + 1
    G.seen.add(dev['ip'])


def scan_done(window, devices):
    stopped = stop_flag.is_set()
    G.scanning, G.progress = False, 1.0
    if not stopped:                                               # a full scan: devices it didn't find again are gone
        G.devices = [d for d in G.devices if d['ip'] in G.seen]
    if DEMO:
        G.status = f'Demo: {len(G.devices)} made-up devices - nothing on your network was scanned.'
    elif stopped:
        G.status = f'Stopped - {len(G.seen)} devices found before that.  Devices from the scan before are still shown.'
    else:
        G.status = f'Scan complete: {len(G.devices)} devices.' + ('  Looking up the makers online ...' if G.vendor and G.devices else '')
    window.TKroot.after(1500, lambda: setattr(G, 'progress', 0.0) or draw(window, (K_FOOT,)))
    draw(window)
    apply_menu(window)


def copy_text(window, words, what):
    sg.clipboard_set(words)
    note(window, f'Copied {what}')


def open_device(window, ip):
    dev = device(ip)
    url = web_url(dev) if dev else ''
    if url:
        webbrowser.open(url)
        note(window, f'Opened {url}')
    else:
        note(window, 'It offers no web page' + (' (demo addresses are made up)' if DEMO else ''))


def diagnose(window):
    if DEMO:
        note(window, 'Diagnose is off in the demo - it would show your real network')
        return
    G.status = 'Running diagnostics (about 10 seconds) ...'
    draw(window, (K_FOOT,))
    worker(lambda: post(K_DIAG_DONE, diagnostics()))


def diagnose_done(window, report):
    try:
        with open(G.diag_path, 'w', encoding='utf-8') as f:
            f.write(report)
        G.status = f'Diagnostics saved to {G.diag_path}'
    except Exception as e:
        G.status = f'Could not save the diagnostics: {e}'
    draw(window, (K_FOOT,))
    c = colors()
    sg.popup_scrolled(report, title=f'Network diagnostics - saved to {G.diag_path}', font=('Consolas', 9), size=(120, 40), keep_on_top=True, non_blocking=True,
                      background_color=c['page'], text_color=c['text'], icon=ICON)


def show_news(window):
    c = colors()
    since = update_tag()
    lines = update_news(since) if since else update_news('')
    G.busy = True
    sg.popup_scrolled('\n'.join(lines) or 'No change-log lines found.', title=f"{APP_NAME} - what's new" + (f' since {since}' if since else ''), size=(100, 16),
                      font=('Segoe UI', 10), keep_on_top=True, background_color=c['page'], text_color=c['text'], icon=ICON, button_color=('#ffffff', C_MENU_SEL))
    G.busy = False
    update_tag_seen()
    window.set_title(window_title())
    draw(window, (K_HEAD,))


def show_version(window):
    c = colors()
    settings = f'   settings: {sg.user_settings_filename()}' + ('  (temporary - removed on close)' if DEMO else '')
    sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', '', 'What it writes:', settings,
                      f'   diagnostics: {G.diag_path}  (only when you click Diagnose)', '', f'New versions:  {dict(UPDATE_CHOICES)[update_mode()]}', '', sg.get_versions(),
                      title=f'{APP_NAME} {VERSION}', keep_on_top=True, non_blocking=True, size=(100, 14), background_color=c['page'], text_color=c['text'], icon=ICON)


def act(window, action, value):
    """ A click on a drawn part """
    if action == 'pick':
        G.picked = value
        apply_menu(window)
    elif action in ('open', 'popen'):
        open_device(window, value)
        return
    elif action == 'kind':
        if G.solo == value:                                       # the end of a double-click on it: only this kind
            G.hidden = set(KIND_COLORS) - {value}
        else:
            G.hidden.symmetric_difference_update({value})
        G.solo = None
        sg.user_settings_set_entry(S_HIDDEN, sorted(G.hidden))
    elif action == 'kinds':                                       # All / None
        G.hidden = set() if value == 'all' else set(KIND_COLORS)
        sg.user_settings_set_entry(S_HIDDEN, sorted(G.hidden))
    elif action == 'sort':
        G.sort = (value, not G.sort[1]) if G.sort[0] == value else (value, False)
        sg.user_settings_set_entry(S_SORT, list(G.sort))
    elif action == 'track':
        scroll_by(window, value * (G.boxes['view'][3] - G.boxes['view'][1]) * 0.9)
        return
    elif action == 'details':
        set_details(window, not G.details)
        return
    elif action == 'copy':
        dev = device(value)
        if dev:
            copy_text(window, dev['ip'], dev['ip'])
        return
    elif action == 'copy_all':
        dev = device(value)
        if dev:
            copy_text(window, details_text(dev), f'everything about {dev["name"]}')
        return
    elif action == 'back':
        window.write_event_value(K_BACK, None)
        return
    elif action == 'news':
        show_news(window)
        return
    elif action == 'scan':
        start_scan(window)
        return
    elif action == 'stop':
        stop_flag.set()
        G.status = 'Stopping ...'
    elif action == 'diag':
        diagnose(window)
        return
    elif action in ('tiles', 'list'):
        set_view(window, action)
        return
    elif action == 'vendor':
        G.vendor = not G.vendor
        sg.user_settings_set_entry(S_VENDOR, G.vendor)
        apply_menu(window)
    draw(window)


def mouse(window, event, values):
    """ Press / drag / release / hover / leave / double-click / wheel on the three drawn parts.  True when it was one of those """
    key, _, kind = event.partition('+')
    if key not in (K_HEAD, K_MAIN, K_FOOT):
        return False
    xy = values.get(key) if isinstance(values, dict) else None
    if kind == '':                                                # second mouse rule: with drag_submits this is "button down" or "moved while down"
        if not xy or xy[0] is None:
            return True
        if G.down is None:
            part = part_at(key, xy)
            G.down, G.dragged = (key, xy[0], xy[1], part[0] if part else None, part[1] if part else None), False
            G.solo = None
            G.drag_from = G.scroll
            if key == K_MAIN:
                window[K_MAIN].Widget.focus_set()                 # the keys go to the devices, not to a box
            if G.down[3] == 'thumb':
                draw(window, (K_MAIN,))
        elif G.down[3] == 'thumb':                                # pulling the scroll bar's thumb
            t0, thumb_h, span, room = G.boxes.get('thumb', (0, 1, 1, 0))
            G.dragged = True
            G.scroll = G.drag_from + (xy[1] - G.down[2]) * room / max(1, span - thumb_h)
            clamp_scroll(G.boxes)
            draw(window, (K_MAIN,))
        elif abs(xy[1] - G.down[2]) > 4 * G.scale or abs(xy[0] - G.down[1]) > 4 * G.scale:
            G.dragged = True
    elif kind == 'UP':                                            # third mouse rule: a click is acted on when the button comes UP, if it didn't move
        down, G.down = G.down, None
        if down and not G.dragged and down[3]:
            part = part_at(key, xy) if xy and xy[0] is not None else None
            if part and part[0] == down[3] and part[1] == down[4]:
                act(window, down[3], down[4])
                if down[3] in ('kind', 'kinds'):
                    hover(window, key, xy)                        # its hint says Show / Hide the other way round now
        elif down and down[3] == 'thumb':
            draw(window, (K_MAIN,))
        G.dragged = False
    elif kind == 'MOVE':
        G.down, G.dragged = None, False
        hover(window, key, xy)
    elif kind == 'LEAVE':
        hover(window, None, None)
    elif kind == 'DOUBLE':                                        # tk sends a quick second press only as this - it is a press as well
        part = part_at(K_MAIN, xy)
        G.down, G.dragged = (key, xy[0], xy[1], part[0] if part else None, part[1] if part else None), False
        if part and part[0] == 'pick':
            G.picked = part[1]
            if not G.details or not G.boxes.get('panel_w'):
                set_details(window, True)
            draw(window, (K_MAIN,))
        elif part and part[0] == 'kind':                          # the button coming up shows only this kind (act)
            G.solo = part[1]
    elif kind in ('WHEEL', 'WHEELUP', 'WHEELDOWN'):
        e = window[K_MAIN].user_bind_event
        if getattr(e, 'state', 0) & 0x4:                          # Ctrl: that is the size - the window's own binding does it
            return True
        up = getattr(e, 'delta', 0) > 0 if kind == 'WHEEL' else kind == 'WHEELUP'
        notch = round(70 * G.scale * ZOOMS[G.zoom][1])
        if G.boxes.get('panel_w') and getattr(e, 'x', 0) >= G.boxes['cw']:
            G.panel_scroll = max(0, min(G.boxes.get('panel_room', 0), G.panel_scroll + (-notch if up else notch)))
            draw(window, (K_MAIN,))
        else:
            scroll_by(window, -notch if up else notch)
    return True


def hover(window, key, xy):
    part = part_at(key, xy) if key else None
    now = (key, (part[0], part[1]) if part and part[0] else None)
    words = part[2] if part else ''
    if now != G.hover:
        old = G.hover[0]
        G.hover = now
        for k in {old, key} - {None, K_FOOT}:
            draw(window, (k,))
    if words != G.hint:
        G.hint = words
        draw(window, (K_FOOT,))


def keys(window, name):
    """ A key from the window's bindings.  Keys that a box uses itself (arrows, Home / End in the boxes) are left to the box """
    focus = window.find_element_with_focus()
    in_box = isinstance(focus, sg.Input)
    e = window.user_bind_event
    alt = e is not None and getattr(e, 'state', 0) & (0x20000 if sg.running_windows() else 0x8)
    if name in ('find', 'details', 'tiles', 'list', 'copy', 'bigger', 'smaller', 'normal') and alt:
        return                                                    # Ctrl+Alt+... is a system hotkey
    if name == 'Escape':
        if G.search or focus is window[K_SEARCH]:
            window[K_SEARCH].update('')
            G.search, G.scroll = '', 0
            window[K_MAIN].Widget.focus_set()
            draw(window)
            return
        window.write_event_value(K_EXIT, None)
    elif name == 'F5':
        start_scan(window)
    elif name == 'find':
        window[K_SEARCH].set_focus()
        window[K_SEARCH].Widget.select_range(0, 'end')
        window[K_SEARCH].Widget.icursor('end')
    elif name == 'details':
        set_details(window, not G.details)
    elif name in ('tiles', 'list'):
        set_view(window, name)
    elif name == 'copy':
        if not in_box and device(G.picked):
            copy_text(window, G.picked, G.picked)
    elif name in ('bigger', 'smaller', 'normal'):
        if set_zoom(window, 'Medium' if name == 'normal' else zoom_step(1 if name == 'bigger' else -1)):
            draw(window)
            apply_menu(window)
    elif name == 'Return':
        if focus is window[K_SUBNET]:
            start_scan(window)
        elif focus is window[K_SEARCH]:
            shown = shown_devices()
            if shown:
                G.picked = G.picked if any(d['ip'] == G.picked for d in shown) else shown[0]['ip']
                window[K_MAIN].Widget.focus_set()
                keep_in_view(G.picked)
                draw(window)
        elif G.picked:
            if not G.details or not G.boxes.get('panel_w'):
                set_details(window, True)
    elif name in ('Up', 'Down', 'Left', 'Right', 'Prior', 'Next', 'Home', 'End'):
        if in_box:
            if focus is window[K_SEARCH] and name == 'Down':      # Down in the search box goes into the results
                window[K_MAIN].Widget.focus_set()
            else:
                return
        if not G.devices:
            scroll_by(window, {'Up': -40, 'Down': 40, 'Prior': -400, 'Next': 400, 'Home': -10 ** 6, 'End': 10 ** 6}.get(name, 0) * G.scale)
            return
        move_pick(window, name)
        G.back_kind = 'rows'
        draw(window, (K_MAIN,))
        apply_menu(window)


def menu_event(window, event):
    """ A right-click menu choice.  True when it was one """
    key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event
    if key == M_SCAN:
        start_scan(window)
    elif key == M_STOP:
        act(window, 'stop', None)
    elif key == M_DIAG:
        diagnose(window)
    elif key in (M_TILES, M_LIST):
        set_view(window, 'tiles' if key == M_TILES else 'list')
    elif key == M_DETAILS:
        set_details(window, not G.details)
    elif key == M_FIND:
        keys(window, 'find')
    elif key == M_VENDOR:
        act(window, 'vendor', None)
    elif key == M_COPY:
        act(window, 'copy', G.picked)
    elif key == M_COPY_ALL:
        act(window, 'copy_all', G.picked)
    elif key == M_OPEN:
        open_device(window, G.picked)
    elif key == M_NEWS:
        show_news(window)
    elif isinstance(key, str) and key.startswith('-ZOOM TO '):
        if set_zoom(window, key[len('-ZOOM TO '):-1]):
            draw(window)
            apply_menu(window)
    elif isinstance(key, str) and key.startswith('-THEME '):
        G.theme = key[len('-THEME '):-1]
        sg.user_settings_set_entry(S_THEME, G.theme)
        apply_look(window)
    elif isinstance(key, str) and key.startswith(K_ACCENT):
        G.busy = True
        watch_pause()                                             # the color dialog waits for you
        changed = choose_accent(window, key, G.accent)
        G.busy = False
        if changed:
            apply_look(window)
    elif key == 'Edit Me':
        sg.execute_editor(__file__)
    elif key == 'Version':
        show_version(window)
    else:
        return False
    return True


def worker(target, *args):
    """ A worker thread - it talks to the window only through post() """
    G.workers = [t for t in G.workers if t.is_alive()]
    t = threading.Thread(target=target, args=args, daemon=True)
    G.workers.append(t)
    t.start()


def mail_poll(window):
    """ A tk timer on the window's own thread: mail waiting -> ring K_MAIL (once until it is read).  Every 40 ms while a worker runs, else 250 ms.
        Being on the window's thread, it rings while a dialog or the Brightness panel is open too """
    try:
        if not G.rung and not mailbox.empty():
            G.rung = True
            window.write_event_value(K_MAIL, None)
        G.jobs['mail'] = window.TKroot.after(40 if any(t.is_alive() for t in G.workers) else 250, lambda: mail_poll(window))
    except Exception:                                             # the window is closing
        pass


def tick_timer(window):
    """ K_TICK once a second from a tk timer (PySimpleGUI's timer_start uses a thread, and threads stay away from tk here) """
    try:
        window.write_event_value(K_TICK, None)
        G.jobs['tick'] = window.TKroot.after(1000, lambda: tick_timer(window))
    except Exception:
        pass


def stop_timers(window):
    for job in G.jobs.values():
        try:
            window.TKroot.after_cancel(job)
        except Exception:
            pass
    G.jobs = {}


def drain_mail(window):
    """ K_MAIL: the waiting messages for up to 60 ms, then ONE drawing of what they changed.  More waiting: mail_poll rings again """
    G.rung = False
    parts, end = set(), time.monotonic() + 0.06
    while time.monotonic() < end:
        try:
            event, value = mailbox.get_nowait()
        except queue.Empty:
            break
        parts |= mail(window, event, value)
    if parts:
        draw(window, tuple(p for p in (K_HEAD, K_MAIN, K_FOOT) if p in parts))


def mail(window, event, value):
    """ A message from a worker thread.  Returns the parts to draw again (drain_mail draws them once for all the messages) """
    if event == K_PHASE:
        G.status, G.progress = value[0], value[1]
        return {K_FOOT}
    if event == K_FOUND:
        found(window, value)
        return {K_MAIN, K_FOOT}
    if event == K_DONE:
        scan_done(window, value)
    elif event == K_VENDOR_UPDATE:
        ip, maker, done, count = value
        dev = device(ip)
        if dev and maker:
            dev['vendor'] = maker
            G.rev[ip] = G.rev.get(ip, 0) + 1
        if not G.scanning:
            G.status = f'Scan complete: {len(G.devices)} devices.  Looking up the makers online ... {done} of {count}'
        return {K_MAIN, K_FOOT} if dev and maker else {K_FOOT}
    elif event == K_VENDOR_DONE:
        if not G.scanning:
            G.status = f'Scan complete: {len(G.devices)} devices.  Makers found online for {value[0]} of the {value[1]} with a MAC address.'
            return {K_FOOT}
    elif event == K_DIAG_DONE:
        diagnose_done(window, value)
    return set()


def watch_start():
    """ The stuck-window watch.  If the last run got stuck and was ended, its report is kept as network_scanner_hang.txt (returns words that say so).
        Then a fresh watch file for this run: faulthandler writes what every thread is doing into it if the window's thread doesn't come round for
        10 s - from a thread of its own, so it works when the window is stuck.  A normal close removes the file (watch_end) """
    said = ''
    try:
        if os.path.getsize(G.watch_path) > 0:
            shutil.copyfile(G.watch_path, G.hang_path)
            said = f'Last time it stopped answering - a report of why is in {G.hang_path}'
    except OSError:
        pass
    try:
        G.watch = open(G.watch_path, 'w', encoding='utf-8')
    except OSError:
        G.watch = None
    return said


def watch_again(seconds=10):
    """ The window's thread came round: the watch starts over (at most once a second - each start is a new watch thread) """
    now = time.monotonic()
    if G.watch and now - G.watch_armed >= 1:
        G.watch_armed = now
        faulthandler.dump_traceback_later(seconds, file=G.watch)


def watch_pause():
    """ Before something that may rightly take long (a dialog) - the next pass through the loop watches again """
    if G.watch:
        faulthandler.cancel_dump_traceback_later()
        G.watch_armed = 0.0


def watch_end():
    """ A normal close: the watch file goes - but a report in it (the window was stuck for a while and came back) is kept first """
    if G.watch:
        faulthandler.cancel_dump_traceback_later()
        G.watch.close()
        G.watch = None
        try:
            if os.path.getsize(G.watch_path) > 0:
                shutil.copyfile(G.watch_path, G.hang_path)
            os.remove(G.watch_path)
        except OSError:
            pass


def every_second(window):
    """ Once a second.  The garbage collector runs here, on the window's thread only (it is switched off in main): it frees tk images and variables,
        and tk must only ever be called from this thread """
    G.ticks += 1
    gc.collect(1)
    if G.ticks % 30 == 0:
        gc.collect()


def keep_going(window, event, values):
    """ While the Brightness panel is open: the window's own events that should not close it """
    if event == K_MAIL:
        drain_mail(window)
        return True
    if event in (K_REDRAW, K_TICK) or (isinstance(event, str) and event.endswith(('+MOVE', '+LEAVE'))):
        if event == K_REDRAW:
            draw(window)
        elif event == K_TICK:
            every_second(window)
            watch_again()
        else:
            mouse(window, event, values)
        return True
    return False


def save_geometry(window):
    if DEMO:
        return
    try:
        (w, h), (x, y) = window.size, window.current_location()
        sg.user_settings_set_entry(S_GEOMETRY, [w, h, x, y])
    except Exception:
        pass


def load_settings():
    G.theme = sg.user_settings_get_entry(S_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    G.accent = load_accent()
    G.view = sg.user_settings_get_entry(S_VIEW, 'tiles') if sg.user_settings_get_entry(S_VIEW, 'tiles') in ('tiles', 'list') else 'tiles'
    G.zoom = sg.user_settings_get_entry(S_ZOOM, 'Medium') if sg.user_settings_get_entry(S_ZOOM, 'Medium') in ZOOMS else 'Medium'
    G.details = bool(sg.user_settings_get_entry(S_DETAILS, True))
    sort = sg.user_settings_get_entry(S_SORT, ['ip', False])
    G.sort = (sort[0], bool(sort[1])) if isinstance(sort, (list, tuple)) and len(sort) == 2 and sort[0] in SORTS else ('ip', False)
    G.hidden = set(k for k in sg.user_settings_get_entry(S_HIDDEN, []) or [] if k in KIND_COLORS)
    G.vendor = bool(sg.user_settings_get_entry(S_VENDOR, True)) and not DEMO


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Pillow missing: offer to install it
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def pillow_window():
    """ Network Scanner draws with Pillow.  Without it: a small window that says so and offers to install it with pip.  True = installed """
    bg, fg, dim = '#141821', '#e6eaf2', '#8a93a3'
    exe = sys.executable
    if exe.lower().endswith('pythonw.exe') and os.path.isfile(exe[:-5] + '.exe'):
        exe = exe[:-5] + '.exe'                                   # pip from python.exe (no window shows - see creationflags)
    command = [exe, '-m', 'pip', 'install', '--upgrade', 'Pillow']
    layout = [[sg.Text(f'{APP_NAME} {VERSION} draws its window with Pillow, which is not installed for this Python.', background_color=bg, text_color=fg, font=('Segoe UI', 11))],
              [sg.Text('Install it now?  This runs:', background_color=bg, text_color=dim)],
              [sg.Text(' '.join(command), background_color=bg, text_color=fg, font=('Consolas', 10))],
              [sg.Multiline('', key='-OUT-', size=(90, 12), font=('Consolas', 9), background_color='#0f131a', text_color=fg, disabled=True, autoscroll=True)],
              [sg.Button('Install Pillow', key='-INSTALL-', button_color=('#ffffff', '#1f8a55')), sg.Push(background_color=bg), sg.Button('Close', key='-CLOSE-')]]
    window = sg.Window(f'{APP_NAME} needs Pillow', layout, background_color=bg, icon=ICON, finalize=True, font=('Segoe UI', 10))
    window.bind('<Escape>', '-CLOSE-')
    installed = False

    def run():
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
            for line in proc.stdout:
                window.write_event_value('-LINE-', line.decode(errors='replace').rstrip())
            window.write_event_value('-END-', proc.wait())
        except Exception as e:
            window.write_event_value('-END-', f'{e.__class__.__name__}: {e}')
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, '-CLOSE-'):
            break
        if event == '-INSTALL-':
            window['-INSTALL-'].update(disabled=True)
            threading.Thread(target=run, daemon=True).start()
        elif event == '-LINE-':
            window['-OUT-'].print(values[event])
        elif event == '-END-':
            installed = values[event] == 0
            window['-OUT-'].print('Installed - starting Network Scanner ...' if installed else f'pip did not finish ({values[event]}) - see above.')
            if installed:
                window.refresh()
                time.sleep(1)
                break
            window['-INSTALL-'].update(disabled=False)
    window.close()
    return installed


# ----------------------------------------------------------------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------------------------------------------------------------
def main():
    Update.default = 'menu'                                       # a program you open and close: a newer version is only named in the menu
    sg.set_options(dpi_awareness=True, icon=ICON)
    if Image is None:
        if pillow_window():
            restart_self()
        return
    gc.disable()                                                  # the garbage collector runs on the window's thread only - see every_second()
    said = watch_start()
    demo_file = None
    if DEMO:                                                      # the demo starts from the defaults and leaves nothing behind
        demo_file = os.path.join(tempfile.gettempdir(), f'network_scanner_demo_{os.getpid()}.json')
        sg.user_settings_filename(filename=os.path.basename(demo_file), path=os.path.dirname(demo_file))
        sg.user_settings_set_entry('-RAN VERSION-', VERSION)
    else:
        sg.user_settings_filename(filename='network_scanner.json')
    load_settings()
    window = make_window()
    window.refresh()
    window[K_MAIN].Widget.focus_set()
    draw(window)
    mail_poll(window)                                             # tk timers on the window's own thread: mail, and a tick a second
    G.jobs['tick'] = window.TKroot.after(1000, lambda: tick_timer(window))
    if said:
        note(window, said, 20)
    if DEMO:
        window.write_event_value(M_SCAN, None)                    # the demo starts by itself
    while True:
        if back_here(place(), place_name(), G.scroll, getattr(G, 'back_kind', None)):     # every pass, before the read: a changed place is a step
            draw(window, (K_HEAD,))
        G.back_kind = None
        watch_again()                                             # the window's thread came round
        event, values = window.read()
        if isinstance(event, str) and '::' in event:              # a right-click menu choice: 'label::KEY'
            event = event.split('::')[-1]
        if event == K_MAIL:
            drain_mail(window)
            continue
        if event in (K_EXIT, sg.WINDOW_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT):
            stop_flag.set()
            if event != sg.WINDOW_CLOSED:
                save_geometry(window)
            break
        if update_event(event):                                   # right-click > Restart, or a New versions choice
            if Update.restart:
                save_geometry(window)
                break
            apply_menu(window)
            continue
        if event == K_TICK:
            every_second(window)
            if G.note[0] and time.monotonic() >= G.note[1]:
                G.note = ('', 0.0)
                draw(window, (K_FOOT,))
            if G.ticks % 3 == 0:
                c = colors()
                watch_pause()                                     # it may ask about a new version in a pop-up
                if update_tick(window, False, G.busy, (c['page'], c['text'], C_MENU_SEL)):
                    apply_menu(window)
                if Update.restart:
                    save_geometry(window)
                    break
                if update_tag() and '-  UPDATED' not in window.TKroot.title():
                    window.set_title(window_title())
                    draw(window, (K_HEAD,))
            continue
        if event == K_REDRAW:
            G.redraw_job = None
            draw(window)
        elif event == K_ZOOM:
            step, x_root, y_root = values[event]
            canvas = window[K_MAIN].Widget
            anchor = (x_root - canvas.winfo_rootx(), y_root - canvas.winfo_rooty())
            if not (0 <= anchor[0] < canvas.winfo_width() and 0 <= anchor[1] < canvas.winfo_height()):
                anchor = None
            if set_zoom(window, zoom_step(step), anchor):
                draw(window)
                apply_menu(window)
        elif event == K_RIGHT_PICK:
            pass
        elif event in (K_BACK, K_FORWARD):
            got = back_step(-1 if event == K_BACK else 1, ok=lambda where: where['picked'] is None or device(where['picked']) is not None)
            if got:
                show_place(window, *got)
            else:
                note(window, 'Nothing to go back to' if event == K_BACK else 'Nothing to go forward to')
            draw(window, (K_HEAD,))
        elif event == K_SEARCH:
            G.search = values[K_SEARCH].strip()
            G.scroll = 0
            G.back_kind = 'typing'
            draw(window, (K_MAIN, K_FOOT))
        elif isinstance(event, str) and event.startswith(K_KEY):
            keys(window, event[len(K_KEY):])
        elif isinstance(event, str) and mouse(window, event, values):
            pass
        elif event == K_BRIGHT:
            G.busy = G.in_panel = True
            pending = brightness_panel(window, keep_going)
            G.busy = G.in_panel = False
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            apply_look(window)
            if pending and str(pending[0]).split('::')[-1] not in (K_EXIT, sg.WINDOW_CLOSED, sg.WINDOW_CLOSE_ATTEMPTED_EVENT):
                if not update_event(pending[0]):
                    menu_event(window, pending[0])
                elif Update.restart:
                    save_geometry(window)
                    break
            elif pending:
                stop_flag.set()
                save_geometry(window)
                break
        else:
            menu_event(window, event)
    stop_timers(window)
    window.close()
    watch_end()
    if demo_file:
        try:
            os.remove(demo_file)
        except OSError:
            pass
    if Update.restart:
        restart_self()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        watch_pause()
        sg.popup_error_with_traceback(f'{APP_NAME} {VERSION} - error', e, traceback.format_exc())
    finally:
        watch_end()
