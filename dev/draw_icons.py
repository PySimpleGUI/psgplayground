"""draw_icons.py - draws the Playground's hand-made icons (the ones that have no PNG in any working folder) with Pillow.

    python dev/draw_icons.py            writes dev/icons_out/*.png (48 px) and a contact sheet dev/icons_out/_sheet.png
    python dev/draw_icons.py --print    also prints the icons as a base64 dict

sync_from_sources.py imports this module and draws the icons on the fly (needs Pillow), so nothing is embedded anywhere.
Style matches the chat-search icon: dark rounded tile, coloured border in the section colour, flat bright glyph.
"""
import base64
import io
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

S = 4                                   # draw at 4x then downsample for clean anti-aliasing
PX = 48
BIG = PX * S
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icons_out')

TILE = '#1f1c18'
MUSIC = '#ffc53d'                       # Music section colour (border) - gold
TEMPLATE = '#9aa5b1'                    # Templates section colour - neutral slate
WHITE = '#f4f1ec'
BLUE = '#49b4ff'
GREEN = '#4ad66d'
YEL = '#ffd166'
RED = '#ff5c5c'
DIM = '#5a544c'


def tile(border):
    im = Image.new('RGBA', (BIG, BIG), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2 * S, 2 * S, BIG - 2 * S - 1, BIG - 2 * S - 1), radius=10 * S, fill=TILE, outline=border, width=3 * S)
    return im, d


def ellipse_rot(im, cx, cy, rx, ry, angle, fill):
    """ rotated filled ellipse (note heads) """
    layer = Image.new('RGBA', (BIG, BIG), (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill)
    layer = layer.rotate(angle, center=(cx, cy), resample=Image.BICUBIC)
    im.alpha_composite(layer)


def note(im, d, x, y, color, stem=True, head=5, flag=False):
    """ a note head at (x, y) in px units with an upward stem on its right """
    ellipse_rot(im, x * S, y * S, head * S, head * 0.72 * S, 25, color)
    if stem:
        sx = (x + head * 0.85) * S
        d.line((sx, y * S, sx, (y - 14) * S), fill=color, width=int(2.2 * S))
        if flag:
            d.line((sx, (y - 14) * S, sx + 6 * S, (y - 8) * S), fill=color, width=int(2.2 * S))


def png_bytes(im):
    """ the finished palette PNG (a third of the size of RGBA, no visible loss) - sync_from_sources.py calls this to write the icons.  App icons are drawn at 4x and shrunk to 48 px here """
    small = (im.resize((PX, PX), Image.LANCZOS) if im.size == (BIG, BIG) else im).quantize(colors=128, method=Image.FASTOCTREE)
    bio = io.BytesIO()
    small.save(bio, format='PNG', optimize=True)
    return bio.getvalue()


def save(name, im):
    data = png_bytes(im)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name + '.png'), 'wb') as f:
        f.write(data)
    return base64.b64encode(data).decode()


def piano_dynamics_monitor():
    im, d = tile(MUSIC)
    x0, y0, h = 9, 24, 16                            # white keys
    for i in range(5):
        d.rounded_rectangle(((x0 + i * 5) * S, y0 * S, (x0 + i * 5 + 4.4) * S, (y0 + h) * S), radius=S, fill=WHITE)
    for i in (0, 1, 3):                              # black keys
        d.rectangle(((x0 + i * 5 + 3.2) * S, y0 * S, (x0 + i * 5 + 6.2) * S, (y0 + h * 0.6) * S), fill=TILE)
    bx = 36                                          # level bar: green -> yellow -> red
    segs = [(GREEN, 4), (GREEN, 4), (YEL, 4), (YEL, 4), (RED, 4), (RED, 4)]
    y = 40
    for i, (c, hh) in enumerate(segs):
        y -= hh + 1
        d.rectangle((bx * S, y * S, (bx + 4) * S, (y + hh) * S), fill=c if i < 4 else DIM)
    d.line((11 * S, 15 * S, 32 * S, 9.5 * S), fill=MUSIC, width=int(2.2 * S))                           # crescendo hairpin
    d.line((11 * S, 15 * S, 32 * S, 20.5 * S), fill=MUSIC, width=int(2.2 * S))
    return im


def tempo_widget():
    im, d = tile(MUSIC)
    d.polygon([(16 * S, 40 * S), (32 * S, 40 * S), (28 * S, 10 * S), (20 * S, 10 * S)], fill=MUSIC)     # metronome body
    d.polygon([(19.5 * S, 37 * S), (28.5 * S, 37 * S), (26.6 * S, 13 * S), (21.4 * S, 13 * S)], fill=TILE)
    d.line((24 * S, 36 * S, 31 * S, 13 * S), fill=WHITE, width=int(2 * S))                             # pendulum
    d.rectangle((27.5 * S, 20 * S, 32.5 * S, 24 * S), fill=BLUE)                                        # weight
    d.rectangle((14 * S, 39 * S, 34 * S, 42 * S), fill=MUSIC)
    return im


def note_roll():
    im, d = tile(MUSIC)
    for i in range(5):                                                                                  # faint lanes
        y = 11 + i * 6
        d.line((8 * S, y * S, 40 * S, y * S), fill='#2d2924', width=S)
    bars = [(9, 9, 10, BLUE), (14, 15, 8, GREEN), (22, 21, 6, YEL), (18, 27, 12, BLUE), (30, 33, 9, MUSIC), (24, 9, 14, MUSIC)]
    for x, y, w, c in bars:
        d.rounded_rectangle((x * S, (y - 2) * S, (x + w) * S, (y + 2) * S), radius=int(1.5 * S), fill=c)
    d.line((20 * S, 8 * S, 20 * S, 40 * S), fill=WHITE, width=int(1.5 * S))                             # playhead
    d.polygon([(17 * S, 7 * S), (23 * S, 7 * S), (20 * S, 11 * S)], fill=WHITE)
    return im


def groove_lane():
    im, d = tile(MUSIC)
    d.rounded_rectangle((7 * S, 18 * S, 41 * S, 30 * S), radius=3 * S, fill='#2d2924')                  # the lane
    for i in range(8):                                                                                  # beat ticks
        x = 9.5 + i * 4.2
        d.line((x * S, 30 * S, x * S, 33 * S), fill=DIM if i % 2 else MUSIC, width=S)
    hits = [(9.5, BLUE), (18, GREEN), (22.2, GREEN), (26.4, BLUE), (34.8, YEL), (39, BLUE)]
    for x, c in hits:
        d.ellipse(((x - 2.4) * S, 21.6 * S, (x + 2.4) * S, 26.4 * S), fill=c)
    d.line((9.5 * S, 12 * S, 39 * S, 12 * S), fill=MUSIC, width=int(2 * S))                             # timeline
    for i in range(4):
        d.ellipse(((9.5 + i * 9.8 - 1.5) * S, 10.5 * S, (9.5 + i * 9.8 + 1.5) * S, 13.5 * S), fill=MUSIC)
    return im


def run_tachometer():
    im, d = tile(MUSIC)
    cx, cy, r = 24, 29, 16
    box = ((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S)
    d.arc(box, 180, 300, fill=GREEN, width=4 * S)
    d.arc(box, 300, 330, fill=YEL, width=4 * S)
    d.arc(box, 330, 360, fill=RED, width=4 * S)
    for a in (180, 210, 240, 270, 300, 330, 360):                                                       # ticks
        ax, ay = math.radians(a), math.radians(a)
        d.line(((cx + math.cos(ax) * (r - 5)) * S, (cy + math.sin(ay) * (r - 5)) * S, (cx + math.cos(ax) * (r - 3)) * S, (cy + math.sin(ay) * (r - 3)) * S), fill=WHITE, width=S)
    a = math.radians(312)
    d.line((cx * S, cy * S, (cx + math.cos(a) * (r - 4)) * S, (cy + math.sin(a) * (r - 4)) * S), fill=WHITE, width=int(2.5 * S))
    d.ellipse(((cx - 3) * S, (cy - 3) * S, (cx + 3) * S, (cy + 3) * S), fill=MUSIC)
    return im


def harmony_wheel():
    im, d = tile(MUSIC)
    cx, cy, r = 24, 24, 16
    cols = [MUSIC, YEL, GREEN, BLUE, '#b48cff', RED] * 2
    for i in range(12):
        d.pieslice(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), i * 30 - 90, i * 30 - 60, fill=cols[i], outline=TILE, width=int(1.5 * S))
    d.ellipse(((cx - 9) * S, (cy - 9) * S, (cx + 9) * S, (cy + 9) * S), fill=TILE)
    pts = [(cx + 8 * math.cos(math.radians(a)), cy + 8 * math.sin(math.radians(a))) for a in (-90, 30, 150)]                # triad
    d.polygon([(x * S, y * S) for x, y in pts], outline=WHITE, width=int(1.8 * S))
    for x, y in pts:
        d.ellipse(((x - 2) * S, (y - 2) * S, (x + 2) * S, (y + 2) * S), fill=WHITE)
    return im


def staff_trainer():
    im, d = tile(MUSIC)
    for i in range(5):
        y = 15 + i * 5
        d.line((8 * S, y * S, 40 * S, y * S), fill=WHITE, width=int(1.3 * S))
    d.line((8 * S, 15 * S, 8 * S, 35 * S), fill=WHITE, width=int(2 * S))
    note(im, d, 18, 30, MUSIC, head=3.6)
    note(im, d, 28, 22.5, BLUE, head=3.6)
    d.ellipse((34 * S, 22 * S, 40 * S, 28 * S), fill=GREEN)                                             # check mark
    d.line((35.5 * S, 25 * S, 36.8 * S, 26.5 * S, 38.8 * S, 23.5 * S), fill=TILE, width=int(1.4 * S), joint='curve')
    return im


def call_response():
    im, d = tile(MUSIC)
    d.rounded_rectangle((7 * S, 9 * S, 29 * S, 23 * S), radius=4 * S, fill=MUSIC)                       # call bubble
    d.polygon([(10 * S, 22 * S), (10 * S, 27 * S), (15 * S, 22 * S)], fill=MUSIC)
    note(im, d, 15, 18, TILE, head=2.6)
    d.rounded_rectangle((19 * S, 25 * S, 41 * S, 39 * S), radius=4 * S, fill=BLUE)                      # response bubble
    d.polygon([(38 * S, 38 * S), (38 * S, 43 * S), (33 * S, 38 * S)], fill=BLUE)
    note(im, d, 27, 34, TILE, head=2.6)
    return im


def duet_partner():
    im, d = tile(MUSIC)
    note(im, d, 14, 33, MUSIC, head=4, stem=True)
    note(im, d, 30, 29, BLUE, head=4, stem=True)
    d.line((17.4 * S, 19 * S, 33.4 * S, 15 * S), fill=WHITE, width=int(3 * S))                           # beam joining the pair
    d.line((17.4 * S, 23 * S, 33.4 * S, 19 * S), fill=WHITE, width=int(3 * S))
    return im


def ripples():
    im, d = tile(MUSIC)
    cx, cy = 24, 25
    for r, c, w in ((17, DIM, 1.5), (13, MUSIC, 2), (9, BLUE, 2), (5, WHITE, 2)):
        d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=c, width=int(w * S))
    d.ellipse(((cx - 2) * S, (cy - 2) * S, (cx + 2) * S, (cy + 2) * S), fill=YEL)
    return im


def midi_link_tester():
    im, d = tile(MUSIC)
    cx, cy, r = 19, 24, 11
    d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), outline=WHITE, width=int(2.2 * S))      # 5-pin DIN
    for a in (180, 225, 270, 315, 360):
        ax = math.radians(a)
        px, py = cx + math.cos(ax) * 6.5, cy + math.sin(ax) * 6.5
        d.ellipse(((px - 1.6) * S, (py - 1.6) * S, (px + 1.6) * S, (py + 1.6) * S), fill=WHITE)
    d.rectangle(((cx - 2) * S, (cy + 7.5) * S, (cx + 2) * S, (cy + 10.5) * S), fill=WHITE)
    d.line((31 * S, 24 * S, 37 * S, 24 * S), fill=MUSIC, width=int(2 * S))                              # cable + green ok light
    d.ellipse((35 * S, 20 * S, 43 * S, 28 * S), fill=GREEN)
    d.line((37 * S, 24 * S, 38.6 * S, 25.8 * S, 41.2 * S, 22.4 * S), fill=TILE, width=int(1.5 * S), joint='curve')
    return im


def template():
    im, d = tile(TEMPLATE)
    d.polygon([(13 * S, 9 * S), (29 * S, 9 * S), (35 * S, 15 * S), (35 * S, 39 * S), (13 * S, 39 * S)], outline=TEMPLATE, width=int(2 * S))   # page
    d.polygon([(29 * S, 9 * S), (29 * S, 15 * S), (35 * S, 15 * S)], fill=TEMPLATE)
    for i, w in enumerate((12, 16, 9, 14)):
        y = 19 + i * 5
        d.rounded_rectangle((17 * S, y * S, (17 + w) * S, (y + 2.2) * S), radius=S, fill=TEMPLATE if i else BLUE)
    return im


# ------------------------------------------------------------ Toybox buttons ------------------------------------------------------------
# Each button is a picture: an icon everyone recognises plus its label, so nothing needs a tooltip.  Two layouts - wide (icon left, label right)
# for roomy panes and tall (icon above a small label) for narrow ones - and an "off" (disabled) version of each.

BTN_FACE, BTN_FACE_OFF, BTN_EDGE, BTN_TEXT, BTN_TEXT_OFF, BTN_BG = '#243352', '#1a2130', '#30415f', '#e6eaf2', '#5b6577', '#141821'
BTN_GREEN, BTN_BLUE, BTN_YELLOW, BTN_ORANGE, BTN_GREY = '#3ddc84', '#49b4ff', '#ffc53d', '#ff9f43', '#aab4c3'
WIDE, TALL = (118, 34), (54, 50)


def _font(px):
    for name in ('segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf', 'LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(name, px)
        except OSError:
            continue
    return ImageFont.load_default()


def _glyph(d, kind, cx, cy, r, color, s):
    """ the icon part, centred on (cx, cy) with "radius" r, all coordinates already scaled by s """
    if kind == 'run':                                                                                   # green disc, white play
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
        d.polygon([(cx - r * 0.35, cy - r * 0.5), (cx - r * 0.35, cy + r * 0.5), (cx + r * 0.55, cy)], fill=BTN_BG)
    elif kind == 'demo':                                                                                # green ring, play, small "sample" dots
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=color, width=max(2, int(2.2 * s)))
        d.polygon([(cx - r * 0.35, cy - r * 0.5), (cx - r * 0.35, cy + r * 0.5), (cx + r * 0.55, cy)], fill=color)
    elif kind == 'edit':                                                                                # pencil
        d.line((cx - r * 0.7, cy + r * 0.7, cx + r * 0.5, cy - r * 0.5), fill=color, width=max(3, int(5 * s)))
        d.polygon([(cx + r * 0.5, cy - r * 0.5), (cx + r * 0.85, cy - r * 0.85), (cx + r, cy - r * 0.55)], fill=color)
        d.polygon([(cx - r * 0.7, cy + r * 0.7), (cx - r * 1.0, cy + r * 1.0), (cx - r * 0.45, cy + r * 0.95)], fill=BTN_YELLOW)
    elif kind == 'folder':                                                                              # folder with tab
        d.rounded_rectangle((cx - r, cy - r * 0.55, cx + r, cy + r * 0.75), radius=int(2 * s), fill=color)
        d.rounded_rectangle((cx - r, cy - r * 0.9, cx - r * 0.1, cy - r * 0.3), radius=int(2 * s), fill=color)
        d.rectangle((cx - r, cy - r * 0.2, cx + r, cy - r * 0.05), fill=BTN_FACE)
    elif kind == 'install':                                                                             # arrow down into a tray
        d.line((cx, cy - r, cx, cy + r * 0.35), fill=color, width=max(3, int(4.5 * s)))
        d.polygon([(cx - r * 0.6, cy - r * 0.05), (cx + r * 0.6, cy - r * 0.05), (cx, cy + r * 0.55)], fill=color)
        d.line((cx - r, cy + r * 0.9, cx + r, cy + r * 0.9), fill=color, width=max(3, int(4 * s)))
        d.line((cx - r, cy + r * 0.45, cx - r, cy + r * 0.9), fill=color, width=max(2, int(3 * s)))
        d.line((cx + r, cy + r * 0.45, cx + r, cy + r * 0.9), fill=color, width=max(2, int(3 * s)))
    elif kind == 'github':                                                                              # box with an arrow leaving it (open on the web)
        d.rounded_rectangle((cx - r, cy - r * 0.5, cx + r * 0.5, cy + r), radius=int(2 * s), outline=color, width=max(2, int(2.5 * s)))
        d.line((cx - r * 0.1, cy + r * 0.1, cx + r, cy - r), fill=color, width=max(3, int(3.5 * s)))
        d.polygon([(cx + r * 0.3, cy - r), (cx + r, cy - r), (cx + r, cy - r * 0.3)], fill=color)


BUTTON_SPEC = [('run', 'Run', BTN_GREEN), ('demo', 'Run demo', BTN_GREEN), ('edit', 'Edit', BTN_BLUE), ('folder', 'Open folder', BTN_YELLOW),
               ('install', 'Install', BTN_ORANGE), ('github', 'GitHub', BTN_GREY)]


def button_image(kind, label, color, layout, enabled):
    s = 3                                                                                               # drawn at 3x, downsampled
    w, h = (WIDE if layout == 'wide' else TALL)
    im = Image.new('RGBA', (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    face, text = (BTN_FACE, BTN_TEXT) if enabled else (BTN_FACE_OFF, BTN_TEXT_OFF)
    d.rounded_rectangle((0, 0, w * s - 1, h * s - 1), radius=6 * s, fill=face, outline=BTN_EDGE if enabled else BTN_FACE_OFF, width=s)
    col = color if enabled else '#4b5566'
    if layout == 'wide':
        _glyph(d, kind, 17 * s, h * s // 2, 9 * s, col, s)
        font = _font(13 * s)
        d.text((31 * s, h * s // 2), label, fill=text, font=font, anchor='lm')
    else:
        _glyph(d, kind, w * s // 2, 16 * s, 9 * s, col, s)
        font = _font(12 * s)
        d.text((w * s // 2, 39 * s), (lambda t: t[0].upper() + t[1:])(label.split()[-1]) if kind != 'demo' else 'Demo', fill=text, font=font, anchor='mm')
    return im.resize((w, h), Image.LANCZOS)


def button_icons():
    """ name -> drawing function, for every button / layout / state """
    out = {}
    for kind, label, color in BUTTON_SPEC:
        for layout in ('wide', 'tall'):
            for enabled in (True, False):
                name = f'btn_{kind}_{layout}' + ('' if enabled else '_off')
                out[name] = (lambda k=kind, l=label, c=color, lay=layout, en=enabled: button_image(k, l, c, lay, en))
    return out


ICONS = {'piano_dynamics_monitor': piano_dynamics_monitor, 'tempo_widget': tempo_widget, 'note_roll': note_roll, 'groove_lane': groove_lane, 'run_tachometer': run_tachometer,
         'harmony_wheel': harmony_wheel, 'staff_trainer': staff_trainer, 'call_response': call_response, 'duet_partner': duet_partner, 'ripples': ripples,
         'midi_link_tester': midi_link_tester, 'template': template}
ICONS.update(button_icons())


def main():
    b64 = {name: save(name, fn()) for name, fn in ICONS.items()}
    sheet = Image.new('RGBA', (len(b64) * (PX * 3 + 8) + 8, PX * 3 + 16), (40, 40, 40, 255))
    for i, name in enumerate(b64):
        sheet.paste(Image.open(os.path.join(OUT, name + '.png')).resize((PX * 3, PX * 3), Image.NEAREST), (8 + i * (PX * 3 + 8), 8))
    sheet.save(os.path.join(OUT, '_sheet.png'))
    if '--print' in sys.argv:
        print('ICONS = {')
        for name, data in b64.items():
            print(f"    '{name}': b'{data}',")
        print('}')


if __name__ == '__main__':
    main()
