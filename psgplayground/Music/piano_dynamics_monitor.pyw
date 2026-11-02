"""
Piano Dynamics Monitor  (piano_dynamics_monitor.pyw)  -  shows how hard the piano keys are being hit (MIDI velocity) as a 1-10 loudness
value on a scrolling line graph, overall and per voice (BASS / MIDDLE / TOP), so dynamics can be practised by eye.

GRAPH selector (top row) picks what is drawn on the graph (all on a 1-10 scale, newest note at the right edge, time flows left):
  Overall           - RAW / BEAT AVG / NOTE AVG lines described below
  Voices (raw)      - three lines, one per voice: BASS blue-violet, MIDDLE green, TOP peach; each joins the raw notes of that voice
  Voices (beat avg) - the same three voices, but each line is that voice's average over the last N beats (smoother)
  In every mode the dots are the raw notes.  The DOTS selector picks their color:
    Loudness - gradient color of the note's loudness (blue .. red)
    Voice    - the note's voice color (BASS blue-violet, MIDDLE green, TOP peach) so each part is easy to follow; the bottom voice
               tiles still show the loudness color of that part
Overall-mode lines:
  RAW       cyan   - every note as it is played (a chord shows as several dots at the same instant)
  BEAT AVG  white  - average of all notes played in the last N beats (N beats x 60/BPM seconds)
  NOTE AVG  pink   - average of the last N notes (optional, checkbox)
  PEAK      red    - thin horizontal line at the loudest note since Reset
Loudness = 1 + 9 * (velocity - Vel@1) / (Vel@10 - Vel@1), clipped to 1..10.  Raise "Vel@1" so your softest touch reads 1 and lower
"Vel@10" if your piano never sends velocity 127; the graph then uses the whole 1-10 range for YOUR dynamic range.
LEVEL COLORS (glance at the color = know how loud), a smooth gradient through 5 anchor colors:  1-2 pp blue   3-4 p green   5-6 mf yellow   7-8 f orange   9-10 ff red
  Used for: the raw dots on the graph, the graph background (vertical gradient), and the background of every big number (NOW / avg / peak / session).
  Tile backgrounds ease toward their new color over a few frames so the display feels smooth rather than flickery.

VOICES row (for pieces like the Moonlight Sonata: bass octaves / triplets / melody):
  Every note is sorted into BASS (pitch <= "Bass <=" setting), TOP (pitch >= "Top >=" setting) or MIDDLE (everything between).
  Each voice tile shows the loudness of the last note in that voice (big, gradient background), its note name (in the label,
  so a wrong split is easy to spot) and the average of that voice over the last N beats.  Defaults Bass <= E3, Top >= F#4.

LAYOUT: the graph fills the window; the three voice tiles run along the bottom in keyboard order (BASS left, MIDDLE, TOP right) with
large numbers, and the overall tiles (NOW / averages / PEAK / SESSION), the MIDI status and the Demo checkbox form a row under them.
F10 (or the small arrow button at the right of the stats row) hides/shows the control rows; Pause, Reset and Exit sit beside the voice
tiles and stay visible.  F11 fullscreen + F10 hidden = maximum graph.
The window opens at 85% of the screen (it was designed on a 2880 x 1920 tablet); line widths and markers scale with the screen DPI.

BIN (second control row, in beats) smooths the graph the way a "loudness over the piece" chart does:
  0     - every note is a dot, lines join the notes (jerky for arpeggiated pieces such as the Moonlight Sonata)
  1..16 - time is cut into bins of N beats (at the BPM setting); each voice (or all notes in Overall mode) becomes ONE dot per bin,
          the average loudness of its notes in that bin, and the lines join those dots.  4 beats = one bar of 4/4, 8 = two bars, etc.
          Bin boundaries are drawn as vertical lines.  The right-most bin is still filling, so its dot moves until the bin is complete.
Y TOP (second control row) sets the top of the loudness axis so quiet pieces use the whole graph height:
  Peak  - the axis top follows the loudest note since Reset (rounded up, never below 3)
  3..10 - fixed top value
PAUSE (button or F9) freezes the graph and tiles and ignores notes until Resume; on resume the pause gap is removed so the graph
continues seamlessly.  Handy for taking a screenshot.

PRESETS (third control row): Save stores every setting on the second row plus Graph/Dots under a name (popup keyboard friendly), e.g. one per
piece; picking a name in the Preset list applies it instantly; Delete removes the selected one.  Presets live in the user settings file.

TOUCH: every numeric setting is a read-only value box followed by a small pencil mark; tapping the box or the pencil opens a big picker:
a slider plus +/- step buttons (or one button per choice for short lists), OK/Cancel.

TEXT SIZE (top row): one multiplier for every font in the program (70% .. 130%).  tkinter already scales point sizes with the Windows
display scaling, so on a 200% tablet the base sizes are smaller than they were; pick the size that reads best and it is remembered.
Changing it rebuilds the window in place (notes, averages and the MIDI connection are kept).

FULL button (top row) or F11 toggles full screen: the window covers the whole screen with no title bar; remembered between runs.
Same design as Follow Me: tk's -fullscreen attribute, immediately followed by -topmost False (both on and off), so the window is never
left pinned above other windows.
MIN button (bottom-left corner) minimises the window to the taskbar.  If it was in full screen it drops out of full screen first and
goes back to full screen by itself when the window is restored.

TEMPO (bottom row, as in Follow Me): the tempo is estimated from the note onsets - notes closer together than 40 ms count as one chord,
the median gap between the last few onsets times "Notes/beat" (3 for the Moonlight triplets, 1 for one note per beat) gives the beat,
smoothed a little.  The TARGET is the BPM setting; "Tempo +-" is the percent bracket that counts as on tempo.  The dial is centred on
the target, the needle falls when you are slow and rises when fast; tile, needle and sub text turn blue (slow) or coral (fast) outside
the bracket and teal inside it.  A pause of more than 4 s restarts the estimate.  The average tempo goes into the saved PNG header.
TEMPO STRIP (checkbox, second control row): a band a quarter of the plot height along the bottom of the graph shows the tempo estimate
over the same time window as the graph - a line coloured by state (blue slow / teal on target / coral fast) drawn over the teal
on-target bracket, with the target as a thin white line and its bpm at the right.  The strip spans the target +- 25% (STRIP_RANGE),
tempos beyond that sit on the edge.  The saved PNG carries the same strip.
MIDI FILE PLAYBACK (fourth control row): Open... a .mid / .midi (a teacher's recording, say), pick the MIDI OUT port (the piano itself
for a Disklavier, or a soft synth) and press Play.  The file is sent to that port at the chosen Speed (percent of the file's tempo)
and every note-on is fed into the monitor exactly as if it had been played live, so the graph, voices, tempo and PNG all describe the
recording.  Play first does a Reset so the session is the recording alone.  Live MIDI input is ignored while a file plays (a
Disklavier echoes what it plays, which would double every note).  Pause / F9 also pauses the playback (sounding notes are silenced,
the rest carries on after Resume); Stop or the end of the file sends all notes off.  The last file reopens at start.
WINDOW ("Win" box, second control row): how much time the graph and the tempo strip show - 5 s to 20 minutes, picked with a slider
and -1 min / -5 s / +5 s / +1 min buttons.  A long window is redrawn less often (every 0.5 s at 10 min); with thousands of dots on
screen the binned modes (Bin > 0) are the readable ones.
DOT LABELS ("Dot vel" box, fourth control row): the raw velocity written beside every dot on the graph.  The popup sets the position
(Off / Above / Below / Left / Right) for BASS, MIDDLE and TOP dots and for the all-notes dots of Overall mode; the box shows it as
B M T A with an arrow each (- = off).  A chord - notes of one voice within 40 ms - gets ONE label, the velocity of its highest note;
a binned dot (Bin > 0) shows the average velocity of its notes, which is what the dot's height is.  Colour follows the Vel setting.
VELOCITY (Vel setting, top row): the raw MIDI velocity is shown beside every loudness number - under the number in the stats tiles,
beside it in the voice tiles, and after the voice "avg" - in a slightly smaller font, so the Vel@1 / Vel@10 mapping is easy to judge.
Averages show the average velocity of the same notes; PEAK shows the velocity of the peak note.  Colour: Loudness (the gradient colour
of the value it belongs to), White, Grey or Amber; Off hides it.
SAVE PNG (top row) or F12 renders everything played since the last Reset - the same graph style, the full time span, plus a header with
the session numbers and settings - to a PNG file (a file dialog asks where).  Needs the Pillow package:  pip install pillow
All notes since Reset are kept in memory for this (roughly 10 MB per hour of playing).

Keys:  ESC = exit    F9 = pause/resume    F11 = fullscreen on/off    F10 = hide/show controls    F12 = save PNG    HOME = reset stats + graph
Demo checkbox generates fake notes so the display can be checked without a piano.
Requires:  pip install PySimpleGUI mido python-rtmidi
Settings persist in SETTINGS_FILE (piano_dynamics_monitor.json in the PySimpleGUI settings folder, whatever this script file is called):
every control with a setting= parameter (BPM, beats, note avg on/off + count,
window seconds, Vel@10, Bass/Top splits, Y top, Graph mode, Dots mode) is written by Window.settings_save() when the program is closed
(X button via enable_close_attempted_event, Exit button or ESC).  MIDI port, fullscreen, hidden controls and window location are saved
as they change.  "Demo notes" is deliberately not saved so a real session never starts with fake notes.

CHANGE LOG (newest first, 1 line per change):
2026-11-01  v35  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""

import glob
import itertools
import math
import os
import shutil
import statistics
import tkinter as tk
import tkinter.font as tkfont
import random
import threading
import time

import PySimpleGUI as sg

try:
    import mido
except ImportError:
    mido = None

__version__ = '35'
APP_TITLE = 'Piano Dynamics Monitor'
SETTINGS_FILE = 'piano_dynamics_monitor.json'   # fixed name so renaming / versioning the script never loses the settings and presets
OLD_SETTINGS_GLOB = 'piano_loudness_graph*.json'  # earlier versions of this program; the newest one is copied on first run
# Program icon: 128 px PNG, base64 (drawn by make_icon.py in the same flat dark style as the other MIDI-tool icons)
ICON = b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAABgFBMVEUdGhcAAAD+xDz28+8hHhn+00Dt6uVoUyUOCw7/yzP/xDxaVEwpJiImIhpJ1Wz+02dkYV1saWT4y2SbmJTxvDrb2NNWRiNN43OviS//qlX/0D//AAD/uzotWTT/4WxIzWn//wC2lDI8mlGWdyy3l03/xTxhXVfHmzPOojX/fwA0MSlEOB3/xzseIRrk4dxJRkKIayn/qjH/wjz/yD7/1yf/10D//1B2cm6hnpmnpKC6urf/mTP/qgD/vzv/wjz/zUD/0kH/4Tz//39R9HsoRSu4olIvYTg/pFZMPiBdUSNAp1hiTyPCv7v/8HMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYjRhkAAAAgHRSTlP/AP7///7///8FrP//////////////////A/8BBv///wH/////df///wL//zr/////B4PDBlYG/////wUDOEz/rBEC//////////////8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJE+CXkAAAY4SURBVHja7Zttf6I4EMADBokuqaVFVpTd6nlabXu6fd7du33ee777/l/nQhJCgKCCYen+znlVIM38Z0gmE5wAo2EBB4DiR6NxR5OMR+UBglCvoWFQBmAUdAxj+dDpapLOw9IwOsFoR4BxZPzVfdc0LU1imt37q8gN410ASKNw9tEk/6VTLPPjLKSdbwMIjPDe/KBZPUX4YN6HRrAFYBwYn25r0M4Zbj8ZwXgTAOG7qU09RbgxMk5IASyN61mt+gnB7JqoKQD4xXiXba5pEqTkHVGkBAiur+S2lmee+7YG8c9NL9Xx1XWgAhh9NlLqBxhDBDQIghgPUgjG55ECIDBmUpvpZaQcapEI4nIqdT6TBqIACB+S8W8tMAAYaJSov0XS/81DmAUYGWFCaGNAuTUK6Q/biYbQGKUBxkHnVjz1EdCsniIA5AsVt504IIF4tUwCgI9wDfoJAU4IrFm83gP+AsQMsGyEQU2CkS3MNPhLYADhUswAMv7gvr4uGkBkHCzETFiGEsCd0Y3R9tTPZh0oJogd3SVKBUCwjGOgNd1DPzEdA0SmnO0XE0xjTVfLQAD8bLznt73LqgBxwLFtzzMlM9IBCYJLjwO8J2o5wGh81+V3B1VGYGQ5pKa/mnjWkL3IwnE44LZ272iyTAGMDn8zHq5qOXH71PTiRM5LHjtCLljnmLvA7Bh5ABOX184sHwxTC554B/DZ/BmXuUNvxsNQAuiIOXAOq1o+lLQPBxMJIBEGAM/FPOhkASwfwR21k+FOl9lJ2nJyMfVtkMTyHABEvlUMYO8wB9hER5gmGkPJ8iHJISZ+5BWYxPI8ALCrA0BmemT5YCGnWuRvz7PtS4REKNIPwF86+oNabuUspzEoF4T1AHDLiQ5/kk6uyOCLLc+YrhGAW85iXNrxiwHJHLnlat/tCcBiXGx5aqrRnBkXWq7PAwj8nbXcZJZDpHrpxQDz8gAwF+PI32Sp+ZNavtl0DR6AJH/Jx7hXBcN9w+SRl8NSAFL+Ei0wPMbtZrkOAGnppAt1NBUwLpkx7TUIIRhIDiDBBpbz/r6DMGo63CXc1jYIwbYFB9b+CjYvubt4Yr9AtDnpYBNyC4OGtaAg7WIhaasnNK2GqsSTe2KyOShrywcUqTf3hLQsKTyhOSOSNx+KhZl5AsDaAOTt144LdC4t3xdATs4iT5iZKbrgyZnIii8SwWXXgu3pKcilpyaLl8nuFCXCtgV6AGRP8HiZopjEGwz8o5BffV2vQL1FkT2R7DFx72WPy0sb1QCQDDnmCTOzO8YnvRMuvboAZE+weGkle0wCwOXkZa0AqXg5sMUe81sC8DyWxUvQFEA2HjcBkP4k8/0CwN2CcvFHSbjfNCRDiX1aSn1tEsqc+KG6HRG+HFQNRBA47qpNZOXwXdK81W635nx6OfRZu3XqgwtFu+ja5Z+kKoZiiNwWlXbc8XF0dRwDtNnD1j/oUdUuEpe1rboYOatcx8TiDAAhcPv5duwO8wmUfr26KLMYCRWVAdgdMga49P4tNQi1AVSdBRoBqsWBA8AB4ACgH6DXFMBJs4GI7J2ElPpMpw3gp0RAEwD47OiMy9GLRsbAkZDnzQCcHQAOAN89AN/oxvsCvuHKA0jtNHsAOw7GDnAjADfaEkFyS+GBpJ1WgBbdAJ1G2tlFu++2VuKhAEi3kwPR81i+VAOIhHScSN9N/pYAcu0YAHwh5LeLKmsB1RJZJgO0lQCZdnxYyluzJgDwD0L++gpgAwAaxsB+AHvPgv8ZQFLEUh/ApiIWqYynNgBVGY+qkKk+AEUhk6qUq0YARSmXopitLgBlMZuqnK+mQKQu51MVNDryivPmjdTx6lEGeFwVtWtlQ/HvXwsLGvMlnRCcsg+O0SrbWq9bydUp7icXfVzcDuS+ExaWdOaLWiHw3wrLXgPwWlj2do0ehdv7j2hd1I7/cEZ+QOCCNxS15st6yTfg+TEVd01eHVq77IokZRg5Ln02dx3StrAdLFHWqyhsJp3FnqOF5vFVVKMNpEcb2pUobFaWdnPnYdmTqYsNjxS12ZtLuxsvbm++vL/5Aw7NH/Fo/JBL88d8mj/o1PxRr+YPuzV/3O8JHHhs/shn84den8Cx36dw8Plw9vybyX/gbTBwygKRswAAAABJRU5ErkJggg=='      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

# ---------- Keys ----------
K_GRAPH = '-GRAPH-'
K_PORT = '-PORT-'
K_REFRESH = '-REFRESH-'
K_BPM = '-BPM-'
K_BEATS = '-BEATS-'
K_NOTES = '-NOTES-'
K_SHOW_NOTE_AVG = '-SHOW NOTE AVG-'
K_WINDOW_SEC = '-WINDOW SEC-'
K_VEL_MAX = '-VEL MAX-'
K_VEL_MIN = '-VEL MIN-'
K_Y_TOP = '-Y TOP-'
K_BIN = '-BIN-'
K_NPB = '-NOTES PER BEAT-'              # notes per beat for the tempo estimate
K_TEMPO_TOL = '-TEMPO TOL-'             # +- % around the target that counts as on tempo
K_TEMPO = '-TEMPO-'
K_TEMPO_LABEL = '-TEMPO LABEL-'
K_TEMPO_STRIP = '-TEMPO STRIP-'         # checkbox: tempo band along the bottom of the graph
K_GAUGE = '-GAUGE-'
K_DEMO = '-DEMO-'
K_GRAPH_MODE = '-GRAPH MODE-'
K_TEXT_SIZE = '-TEXT SIZE-'
K_VEL_COLOR = '-VEL COLOR-'            # colour (or Off) of the raw velocity shown beside every loudness number
K_DOT_VEL = '-DOT VEL-'                # where the velocity goes beside the graph dots, per voice: e.g. 'B\u2193 M\u2191 T\u2191 A\u2191'
K_DV = '-DV-'
KT_DV = lambda voice, pos: (K_DV, voice, pos)          # popup button: one position for one voice
K_DV_OK = '-DV OK-'
K_DV_CANCEL = '-DV CANCEL-'
K_VEL = '-VEL-'
KT_VEL = lambda value_key: (K_VEL, value_key)          # velocity text beside a big number
K_REBUILD = '-REBUILD-'                # internal event: fonts changed, rebuild the window
K_DOT_MODE = '-DOT MODE-'
K_RESET = '-RESET-'
K_SAVE_PNG = '-SAVE PNG-'
K_KEY_F12 = '-KEY F12-'
K_MIDI_OUT = '-MIDI OUT-'              # output port combo (playback goes here)
K_OPEN_MIDI = '-OPEN MIDI-'
K_MIDI_FILE = '-MIDI FILE-'            # file name text
K_PLAY = '-PLAY-'                      # Play / Stop button
K_SPEED = '-SPEED-'                    # playback speed, percent
K_PLAY_STATUS = '-PLAY STATUS-'        # 'name  1:23 / 4:56'
K_PLAY_DONE = '-PLAY DONE-'            # event from the playback thread when the file ends
K_LAST_MIDI_FILE = '-LAST MIDI FILE-'  # settings-file entry only
K_PAUSE = '-PAUSE-'
K_FULL = '-FULL-'
K_MINIMIZE = '-MINIMIZE-'
K_MAPPED = '-MAPPED-'                  # tk <Map> event: the window was shown / restored
K_KEY_F9 = '-KEY F9-'
K_PRESET = '-PRESET-'
K_PRESET_SAVE = '-PRESET SAVE-'
K_PRESET_DELETE = '-PRESET DELETE-'
K_PRESETS = '-PRESETS-'                # settings-file entry: {name: {setting key: value}}
K_RECALC = '-RECALC-'                  # internal event: settings were changed programmatically, recompute everything
TAP = ' TAP'                           # suffix added to a field's key when its value is tapped/clicked
K_PICK_VAL = '-PICK VAL-'
K_PICK_OK = '-PICK OK-'
K_PICK_CANCEL = '-PICK CANCEL-'
K_PICK_SLIDER = '-PICK SLIDER-'
K_EDIT = '-EDIT-'
K_STATUS = '-STATUS-'                  # MIDI connection status text under the right-hand tiles
KT_EDIT = lambda key: (K_EDIT, key)                    # "..." button beside a value box: opens the picker for that setting
K_PICK = '-PICK-'
KT_PICK = lambda choice: (K_PICK, choice)              # picker: one button per choice
K_STEP = '-STEP-'
KT_STEP = lambda delta: (K_STEP, delta)                # picker: +/- step button
K_EXIT = '-EXIT-'
K_NOW = '-NOW-'
K_NOW_LABEL = '-NOW LABEL-'
K_BEAT_AVG = '-BEAT AVG-'
K_BEAT_AVG_LABEL = '-BEAT AVG LABEL-'
K_NOTE_AVG = '-NOTE AVG-'
K_NOTE_AVG_LABEL = '-NOTE AVG LABEL-'
K_NOTE_AVG_COL = '-NOTE AVG COL-'
K_PEAK = '-PEAK-'
K_SESSION = '-SESSION-'
K_SESSION_LABEL = '-SESSION LABEL-'
K_BASS_MAX = '-BASS MAX-'              # highest note still counted as BASS
K_TOP_MIN = '-TOP MIN-'                # lowest note counted as TOP
K_VOICE = '-VOICE-'
KT_VOICE = lambda voice: (K_VOICE, voice)              # big number tile of a voice
K_VOICE_LABEL = '-VOICE LABEL-'
KT_VOICE_LABEL = lambda voice: (K_VOICE_LABEL, voice)  # label above a voice tile
K_LEVEL = '-LEVEL-'
KT_LEVEL = lambda value_key: (K_LEVEL, value_key)     # level-name text under each big number
K_MIDI_NOTE = '-MIDI NOTE-'            # event sent from the MIDI callback thread, value = (time, note, velocity)
K_KEY_ESC = '-KEY ESC-'
K_KEY_F11 = '-KEY F11-'
K_KEY_HOME = '-KEY HOME-'
K_FULLSCREEN = '-FULLSCREEN-'          # settings-file entry only
K_CONTROLS = '-CONTROLS-'              # column holding the two control rows
K_CONTROLS_HIDDEN = '-CONTROLS HIDDEN-'   # settings-file entry only
K_EXTRAS = '-EXTRAS-'                  # status text + Demo checkbox under the tiles; hidden together with the control rows
K_TOGGLE_CONTROLS = '-TOGGLE CONTROLS-'
K_KEY_F10 = '-KEY F10-'

# ---------- Colors (dark background, high contrast; every color is paired with a text label) ----------
C_BG = '#101418'
C_RAW = '#00E5FF'            # cyan  - raw loudness of each note
C_BEAT_AVG = '#FFFFFF'       # white - average over the last N beats (white stays visible over every level band)
C_NOTE_AVG = '#FF4FC3'       # pink  - average over the last N notes
C_PEAK = '#FF5252'           # red   - peak since reset
C_SESSION = '#B0BEC5'        # grey  - whole-session numbers
C_GRID = '#2C343C'
C_AXIS_TEXT = '#9AA6B2'
C_STATUS_OK = '#69F0AE'
C_STATUS_BAD = '#FF8A65'
C_PAUSED = '#FFB300'
C_EDIT = '#4DD0E1'           # pencil mark beside each value box
C_TEXT = '#E0E6EC'           # title text in the saved PNG
C_SLOW, C_ON_TEMPO, C_FAST = '#4AA3FF', '#2DD4BF', '#FF8A4C'     # tempo gauge / tile: below, inside and above the target bracket
C_TILE_NEUTRAL = '#2C343C'
C_STRIP_BG = '#0B0E12'       # background of the tempo strip under the plot
STRIP_FRACTION = 1 / 4       # height of the tempo strip as a fraction of the plot height
STRIP_RANGE = 0.25           # the strip spans target +- this fraction (the dial spans +- 0.5)
LEVELS = [(1, 2, '#448AFF', 'pp'), (3, 4, '#00E676', 'p'), (5, 6, '#FFEA00', 'mf'), (7, 8, '#FF9100', 'f'), (9, 10, '#FF1744', 'ff')]   # (low, high, color, name)
C_ON_LEVEL = '#000000'       # text color used on top of a level color
TILE_EASE = 0.35             # fraction of the remaining color difference a tile moves per 100 ms tick (1.0 = instant)

FONT_FAMILY = 'Segoe UI'
BASE_FONTS = {'FONT_UI': 12,             # all controls, axis numbers, time labels, peak text, PAUSED banner
              'FONT_LEGEND': 22,         # graph legend (top-left)
              'FONT_DYNAMICS': 12,       # dynamics labels (pp .. ff) down the right of the graph - same size as the "peak x.x" label (FONT_UI)
              'FONT_LABEL': 11,          # right-hand tile labels and the status / Demo line
              'FONT_BIG': 24,            # right-hand tile numbers
              'FONT_VEL': 17,            # raw velocity under a tile number
              'FONT_VVEL': 44,           # raw velocity beside a voice tile number
              'FONT_DOTVEL': 10,         # raw velocity beside a graph dot
              'FONT_VLABEL': 16,         # voice tile label
              'FONT_HUGE': 64,           # voice tile number
              'FONT_VSUB': 16,           # voice tile "avg x.x  f" line
              'FONT_PICK': 20,           # touch picker buttons
              'FONT_PICK_VALUE': 48}     # touch picker current value
TEXT_SIZE_CHOICES = ['70%', '85%', '100%', '115%', '130%']
VC_OFF, VC_LOUDNESS, VC_WHITE, VC_GREY, VC_AMBER = 'Off', 'Loudness', 'White', 'Grey', 'Amber'
VEL_COLOR_CHOICES = [VC_OFF, VC_LOUDNESS, VC_WHITE, VC_GREY, VC_AMBER]
DV_ALL = 'ALL'                                                     # the all-notes dots of Overall mode
DV_POSITIONS = [('off', 'Off', '\u2013'), ('above', 'Above', '\u2191'), ('below', 'Below', '\u2193'), ('left', 'Left', '\u2190'), ('right', 'Right', '\u2192')]
DV_ARROW = {pos: arrow for pos, _, arrow in DV_POSITIONS}
DV_FROM_ARROW = {arrow: pos for pos, _, arrow in DV_POSITIONS}
DV_DEFAULT = 'B\u2193 M\u2191 T\u2191 A\u2191'


def set_fonts(text_size):
    """Define every FONT_* global from the base point sizes times the Text size setting ('100%' etc.); all fonts are bold"""
    try:
        mult = int(str(text_size).rstrip('%')) / 100
    except ValueError:
        mult = 1.0
    for name, size in BASE_FONTS.items():
        globals()[name] = (FONT_FAMILY, max(5, round(size * mult)), 'bold')
    globals()['FONT_AXIS'] = globals()['FONT_PAUSED'] = globals()['FONT_UI']


set_fonts('100%')
W_RAW, W_BEAT_AVG, W_NOTE_AVG, W_VOICE, W_VOICE_AVG, W_PEAK = 2, 5, 4, 4, 5, 2     # line widths in pixels at 96 dpi (multiplied by G.scale)
DOT_PX = 14                                                                        # raw-note marker diameter in pixels at 96 dpi
WINDOW_FRACTION = 0.85                                                             # initial window size as a fraction of the screen

NOTE_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
V_BASS, V_MIDDLE, V_TOP = 'BASS', 'MIDDLE', 'TOP'
VOICES = (V_BASS, V_MIDDLE, V_TOP)
DV_VOICES = (V_BASS, V_MIDDLE, V_TOP, 'ALL')                          # voices with their own dot-label position; 'ALL' = Overall dots
VOICE_COLORS = {V_BASS: '#8C9EFF', V_MIDDLE: '#A5D6A7', V_TOP: '#FFCC80'}     # voice line + label colors; tile backgrounds use the loudness gradient
M_OVERALL, M_VOICES, M_VOICES_AVG = 'Overall', 'Voices (raw)', 'Voices (beat avg)'
GRAPH_MODES = (M_OVERALL, M_VOICES, M_VOICES_AVG)
D_LOUDNESS, D_VOICE = 'Loudness', 'Voice'
DOT_MODES = (D_LOUDNESS, D_VOICE)
PNG_PX_PER_SEC, PNG_MIN_W, PNG_MAX_W, PNG_H = 40, 1600, 8000, 1000   # size of the saved session image
TT_VEL = 'MIDI velocity that counts as loudness 10 (lower it if your piano never reaches 127)'
TT_VEL_MIN = 'MIDI velocity that counts as loudness 1 (raise it so your softest notes read 1; anything softer is clipped to 1)'
TT_BASS = 'Notes at or below this pitch are BASS'
TT_TOP = 'Notes at or above this pitch are TOP  (notes between the two splits are MIDDLE)'
TT_Y_TOP = 'Top of the loudness axis:  Peak = follow the loudest note since Reset, or a fixed value 3-10'
Y_TOP_PEAK = 'Peak'
TT_BIN = 'Smoothing: 0 = every note.  N = one dot per N beats (average of the notes in that bin), lines join the bin dots.  4 = one bar of 4/4'
BIN_CHOICES = [0, 1, 2, 3, 4, 6, 8, 12, 16]
NPB_CHOICES = [1, 2, 3, 4, 6, 8]                                   # notes per beat for the tempo estimate
TEMPO_TOL_CHOICES = list(range(2, 31))                             # +- % bracket
ONSET_GAP = 0.04                                                   # notes closer than this (s) are one chord / onset
TT_NPB = 'Notes per beat for the tempo estimate: 3 for triplets (Moonlight), 1 for one note per beat, 2 for eighths'
TT_TEMPO_TOL = 'How far from the target BPM (percent) still counts as on tempo (teal); slower = blue, faster = coral'
BPM_CHOICES = list(range(30, 301))
BEATS_CHOICES = list(range(1, 33))
NOTES_CHOICES = list(range(2, 65))
WINDOW_CHOICES = list(range(5, 1201, 5))                          # graph window: 5 s .. 20 min in 5 s steps
STEPS_WINDOW = [(-12, '-1 min'), (-1, '-5 s'), (1, '+5 s'), (12, '+1 min')]
VEL_MIN_CHOICES = list(range(1, 100))
VEL_MAX_CHOICES = list(range(40, 128))
Y_TOP_CHOICES = [Y_TOP_PEAK] + list(range(3, 11))
STEPS_1_10 = [(-10, '-10'), (-1, '-1'), (1, '+1'), (10, '+10')]
STEPS_1_4 = [(-4, '-4'), (-1, '-1'), (1, '+1'), (4, '+4')]
STEPS_1 = [(-1, '-1'), (1, '+1')]
SPEED_CHOICES = list(range(25, 201, 5))                            # playback speed, percent of the file's tempo
STEPS_SPEED = [(-4, '-20'), (-1, '-5'), (1, '+5'), (4, '+20')]
TT_SPEED = 'Playback speed as a percent of the MIDI file tempo (100 = as recorded)'
STEPS_NOTE = [(-12, '-oct'), (-1, '-1'), (1, '+1'), (12, '+oct')]
C_BIN_LINE = '#4A5560'                                         # vertical lines at bin boundaries


class Note:
    __slots__ = ('t', 'note', 'vel', 'raw', 'beat_avg', 'note_avg', 'voice', 'voice_avg', 'beat_vel', 'note_vel', 'voice_vel')

    def __init__(self, t, note, vel, raw, beat_avg, note_avg, voice, voice_avg, beat_vel, note_vel, voice_vel):
        self.t, self.note, self.vel, self.raw, self.beat_avg, self.note_avg, self.voice, self.voice_avg = t, note, vel, raw, beat_avg, note_avg, voice, voice_avg
        self.beat_vel, self.note_vel, self.voice_vel = beat_vel, note_vel, voice_vel       # average MIDI velocity of the same notes as the three averages


class G:                                # program-wide state
    window = None
    port = None
    status = ''
    status_ok = False
    notes = []                          # every note since the last Reset, in time order
    session_start = time.time()         # wall-clock time of the last Reset (for the PNG header)
    tempo_onsets = []                   # real times of the last few chord onsets, for the tempo estimate
    bpm = None                          # smoothed tempo estimate
    tempo_samples = []                  # every estimate since Reset, for the session average
    tempo_hist = []                     # (real time, bpm) for every estimate since Reset, for the tempo strip
    target, tempo_tol, npb = 120, 5, 3  # target tempo (= the BPM setting), +- % bracket, notes per beat
    peak = 0.0
    peak_vel = 0                        # velocity of the peak note
    total_vel = 0.0                     # sum of velocities since Reset (session average velocity)
    vel_color = 'Loudness'              # the Vel setting
    count = 0
    total = 0.0
    last_note = ''
    fullscreen = False
    restore_full = False                # go back to full screen when the window is restored from the taskbar
    demo_next_t = 0.0
    demo_phase = 0.0
    scale = 1.0                         # screen dpi / 96, applied to pixel-based drawing sizes
    paused = False
    pause_t = 0.0                       # time the pause started; the graph is drawn as of this moment while paused
    text_px = {}                        # (text, font) -> measured pixel width, for laying out the legend
    tick = 0                            # timer ticks, for redrawing a long window less often
    out_port = None                     # MIDI output port for playback
    play_path = ''                      # MIDI file chosen for playback
    playing = False
    play_stop = threading.Event()
    play_thread = None
    play_pos, play_len = 0.0, 0.0       # seconds into the file / file length
    play_speed = 1.0
    held = set()                        # (channel, note) currently sounding from playback, silenced on pause / stop
    tile_target = {}                    # value_key -> rgb the tile background is heading to
    tile_now = {}                       # value_key -> rgb the tile background currently shows


# ---------- Helpers ----------
def note_name(n):
    return f'{NOTE_NAMES[n % 12]}{n // 12 - 1}'


NOTE_LIST = [note_name(n) for n in range(24, 97)]          # C1 .. C7 for the split-point spinners
NOTE_NUM = {name: n for n, name in zip(range(24, 97), NOTE_LIST)}


def classify(note, bass_max, top_min):
    return V_BASS if note <= bass_max else V_TOP if note >= top_min else V_MIDDLE


def loudness(vel, vel_range):
    """Map a MIDI velocity onto 1..10 using the (Vel@1, Vel@10) floor and ceiling"""
    vel_min, vel_max = vel_range
    return round(max(1.0, min(10.0, 1 + 9 * (vel - vel_min) / max(1, vel_max - vel_min))), 2)


def level_of(value):
    """(low, high, color, name) of the 5-step level a 1-10 loudness value falls in (used for the level NAME only)"""
    return LEVELS[min(4, max(0, (round(value) - 1) // 2))]


def rgb(color):
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))


def hexcolor(rgb_tuple):
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(round(c)))) for c in rgb_tuple)


def mix(c1, c2, f):
    """Blend two rgb tuples, f=0 -> c1, f=1 -> c2"""
    return tuple(a + (b - a) * f for a, b in zip(c1, c2))


STOPS = [((lo + hi) / 2, rgb(color)) for lo, hi, color, name in LEVELS]     # gradient anchors at the middle of each level


def level_rgb(value):
    """Smooth gradient color (rgb tuple) for a 1-10 loudness value"""
    if value <= STOPS[0][0]:
        return STOPS[0][1]
    for (v0, c0), (v1, c1) in zip(STOPS, STOPS[1:]):
        if value <= v1:
            return mix(c0, c1, (value - v0) / (v1 - v0))
    return STOPS[-1][1]


def level_color(value):
    return hexcolor(level_rgb(value))


def dim(color, amount=0.18):
    """Mix a level color into the graph background so it can be used as a background fill"""
    return hexcolor(mix(rgb(C_BG), rgb(color), amount))


def ival(values, key, default):
    try:
        return int(values[key])
    except (TypeError, ValueError, KeyError):
        return default


def midi_ports():
    try:
        return mido.get_input_names() if mido else []
    except Exception:
        return []


def midi_callback(msg):
    if msg.type == 'note_on' and msg.velocity > 0 and G.window is not None and not G.playing:
        G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), msg.note, msg.velocity))


def close_port():
    if G.port is not None:
        try:
            G.port.close()
        except Exception:
            pass
    G.port = None


def midi_out_ports():
    try:
        return mido.get_output_names() if mido else []
    except Exception:
        return []


def close_out_port():
    if G.out_port is not None:
        try:
            G.out_port.close()
        except Exception:
            pass
    G.out_port = None


def open_out_port(name):
    close_out_port()
    if mido is not None and name:
        try:
            G.out_port = mido.open_output(name)
        except Exception as e:
            sg.popup_error(f'Cannot open MIDI output {name}:\n{e}', title='MIDI out', font=FONT_PICK, keep_on_top=True)


def send_out(msg):
    if G.out_port is not None:
        try:
            G.out_port.send(msg)
        except Exception:
            pass


def silence():
    """Note-off for everything playback is holding, plus all-notes-off and sustain-off on every channel"""
    for channel, note in list(G.held):
        send_out(mido.Message('note_off', channel=channel, note=note, velocity=0))
    G.held.clear()
    for channel in range(16):
        send_out(mido.Message('control_change', channel=channel, control=64, value=0))
        send_out(mido.Message('control_change', channel=channel, control=123, value=0))


def play_worker(mid):
    """Playback thread: send the file to the output port in real time (scaled by the speed) and feed note-ons to the monitor"""
    pos, paused_now = 0.0, False
    for msg in mid:                                             # msg.time = seconds since the previous message, tempo map applied
        end = time.monotonic() + msg.time / G.play_speed
        while True:
            if G.play_stop.is_set():
                break
            if G.paused:                                        # the monitor is paused: silence, wait, then carry on where we were
                remaining = end - time.monotonic()
                if not paused_now:
                    silence()
                    paused_now = True
                time.sleep(0.05)
                end = time.monotonic() + max(0.0, remaining)
                continue
            paused_now = False
            remaining = end - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(remaining, 0.05))
        if G.play_stop.is_set():
            break
        pos += msg.time
        G.play_pos = pos
        if msg.is_meta:
            continue
        if msg.type == 'note_on' and msg.velocity > 0:
            G.held.add((msg.channel, msg.note))
            send_out(msg)
            if G.window is not None:
                G.window.write_event_value(K_MIDI_NOTE, (time.monotonic(), msg.note, msg.velocity))
        elif msg.type in ('note_off', 'note_on'):
            G.held.discard((msg.channel, msg.note))
            send_out(msg)
        elif msg.type in ('control_change', 'program_change', 'pitchwheel', 'aftertouch', 'polytouch'):
            send_out(msg)
    silence()
    G.playing = False
    if G.window is not None:
        G.window.write_event_value(K_PLAY_DONE, None)


def start_playback(window, path):
    if mido is None:
        sg.popup_error('Playback needs mido:  pip install mido python-rtmidi', title='Play', font=FONT_PICK, keep_on_top=True)
        return
    if not path or not os.path.isfile(path):
        sg.popup_quick_message('Open a MIDI file first', font=FONT_PICK, background_color=C_PAUSED, text_color=C_ON_LEVEL, auto_close_duration=3)
        return
    stop_playback(window)
    try:
        mid = mido.MidiFile(path)
    except Exception as e:
        sg.popup_error(f'Cannot read {path}:\n{e}', title='Play', font=FONT_PICK, keep_on_top=True)
        return
    reset(window)                                               # the session is the recording alone
    G.play_len, G.play_pos, G.playing = mid.length, 0.0, True
    G.play_stop.clear()
    G.play_thread = threading.Thread(target=play_worker, args=(mid,), daemon=True)
    G.play_thread.start()
    window[K_PLAY].update('Stop', button_color=(C_ON_LEVEL, C_PAUSED))


def stop_playback(window):
    if G.play_thread is not None and G.play_thread.is_alive():
        G.play_stop.set()
        G.play_thread.join(timeout=1.0)
    G.play_thread, G.playing = None, False
    silence()
    if window is not None:
        window[K_PLAY].update('Play', button_color=sg.theme_button_color())
        window[K_PLAY_STATUS].update(f'{os.path.basename(G.play_path)}  stopped' if G.play_path else '')


def mmss(seconds):
    return f'{int(seconds) // 60}:{int(seconds) % 60:02d}'


def open_port(name):
    close_port()
    if mido is None:
        G.status, G.status_ok = 'mido not installed:  pip install mido python-rtmidi', False
    elif not name:
        G.status, G.status_ok = 'No MIDI - plug in piano, Refresh', False
    else:
        try:
            G.port = mido.open_input(name, callback=midi_callback)
            G.status, G.status_ok = f'Listening on {name}', True
        except Exception as e:
            G.status, G.status_ok = f'Cannot open {name}: {e}', False
    if G.window is not None:
        G.window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)


# ---------- Data ----------
def add_note(t, note, vel, vel_range, beat_sec, n_notes, bass_max, top_min):
    raw = loudness(vel, vel_range)
    voice = classify(note, bass_max, top_min)
    beat_sum, beat_cnt, v_sum, v_cnt = raw, 1, raw, 1
    beat_vel, v_vel = vel, vel
    for n in reversed(G.notes):                               # notes inside the trailing beat window (all voices, and this voice only)
        if n.t < t - beat_sec:
            break
        beat_sum, beat_cnt, beat_vel = beat_sum + n.raw, beat_cnt + 1, beat_vel + n.vel
        if n.voice == voice:
            v_sum, v_cnt, v_vel = v_sum + n.raw, v_cnt + 1, v_vel + n.vel
    last = list(itertools.islice(reversed(G.notes), max(0, n_notes - 1)))
    note_avg = (sum(n.raw for n in last) + raw) / (len(last) + 1)
    note_vel = (sum(n.vel for n in last) + vel) / (len(last) + 1)
    G.notes.append(Note(t, note, vel, raw, beat_sum / beat_cnt, note_avg, voice, v_sum / v_cnt, beat_vel / beat_cnt, note_vel, v_vel / v_cnt))
    return G.notes[-1]


def last_note_of(voice):
    return next((n for n in reversed(G.notes) if n.voice == voice), None)


def handle_note(window, t, note, vel, vel_range, beat_sec, n_notes, bass_max, top_min):
    n = add_note(t, note, vel, vel_range, beat_sec, n_notes, bass_max, top_min)
    G.count += 1
    G.total += n.raw
    G.total_vel += vel
    if n.raw > G.peak:
        G.peak, G.peak_vel = n.raw, vel
    G.last_note = f'{note_name(note)} v{vel}'
    refresh_stats(window)
    refresh_voices(window, n.voice)
    if note_onset(t):
        refresh_tempo(window)


def recompute(vel_range, beat_sec, n_notes, bass_max, top_min):
    old = list(G.notes)
    G.notes.clear()
    G.peak, G.total, G.peak_vel, G.total_vel = 0.0, 0.0, 0, 0.0
    for n in old:
        m = add_note(n.t, n.note, n.vel, vel_range, beat_sec, n_notes, bass_max, top_min)
        G.total, G.total_vel = G.total + m.raw, G.total_vel + m.vel
        if m.raw > G.peak:
            G.peak, G.peak_vel = m.raw, m.vel


def first_index_at(t):
    """Index of the first note with time >= t (notes are kept in time order, so a binary search will do)"""
    lo, hi = 0, len(G.notes)
    while lo < hi:
        mid = (lo + hi) // 2
        if G.notes[mid].t < t:
            lo = mid + 1
        else:
            hi = mid
    return lo


def reset(window):
    G.notes.clear()
    G.peak, G.count, G.total, G.last_note, G.peak_vel, G.total_vel = 0.0, 0, 0.0, '', 0, 0.0
    G.session_start = time.time()
    G.tempo_onsets, G.bpm, G.tempo_samples, G.tempo_hist = [], None, [], []
    refresh_stats(window)
    refresh_voices(window)


def demo_tick(window, now, bpm, vel_range, beat_sec, n_notes, bass_max, top_min):
    if now < G.demo_next_t:
        return
    G.demo_next_t = now + 60 / bpm * random.choice((0.5, 0.5, 1, 1, 1, 1, 2))
    G.demo_phase += 0.12
    vel = 64 + 40 * math.sin(G.demo_phase) + random.gauss(0, 8)
    for _ in range(random.choice((1, 1, 1, 1, 2, 3))):
        handle_note(window, now, random.randint(36, 84), max(1, min(127, int(vel + random.randint(-6, 6)))), vel_range, beat_sec, n_notes, bass_max, top_min)


# ---------- Display ----------
def note_onset(t):
    """A note arrived at real time t.  Returns True when it started a new onset (chord) and the tempo estimate was updated"""
    if G.tempo_onsets and t - G.tempo_onsets[-1] < ONSET_GAP:   # same chord as the previous note
        return False
    if G.tempo_onsets and t - G.tempo_onsets[-1] > 4.0:         # a long pause: start the estimate afresh
        G.tempo_onsets = []
    G.tempo_onsets.append(t)
    del G.tempo_onsets[:-9]
    if len(G.tempo_onsets) >= 3:
        ioi = statistics.median(b - a for a, b in zip(G.tempo_onsets, G.tempo_onsets[1:]))     # median gap between onsets, robust to the odd extra note
        if ioi > 0.02:
            bpm = 60.0 / (ioi * G.npb)
            G.bpm = bpm if G.bpm is None else 0.6 * G.bpm + 0.4 * bpm
            G.tempo_samples.append(G.bpm)
            G.tempo_hist.append((t, G.bpm))
    return True


def tempo_state(bpm):
    """'slow' / 'ok' / 'fast' against the target bracket, or None without an estimate"""
    if bpm is None:
        return None
    lo, hi = G.target * (1 - G.tempo_tol / 100), G.target * (1 + G.tempo_tol / 100)
    return 'slow' if bpm < lo else 'fast' if bpm > hi else 'ok'


def tempo_color(state):
    return {'slow': C_SLOW, 'ok': C_ON_TEMPO, 'fast': C_FAST}.get(state, C_AXIS_TEXT)


def gauge_frac(bpm):
    """Needle position 0..1: the target sits at the top (0.5); half the target to the left, one and a half times it to the right"""
    return max(0.0, min(1.0, 0.5 + (bpm - G.target) / G.target * 0.5))


def draw_gauge(graph, bpm):
    """A little dial centred on the target tempo: the bracket (on tempo) is marked, the needle falls when slow and rises when fast"""
    w, h = graph.get_size()
    if not w or w < 10:
        return
    graph.CanvasSize = (w, h)
    graph.change_coordinates((0, 0), (w, h))
    graph.erase()
    cx, cy, r = w / 2, h * 0.12, min(w / 2, h * 0.86) - 2
    thick = max(2, int(r * 0.14))
    graph.draw_arc((cx - r, cy + r), (cx + r, cy - r), extent=180, start_angle=0, style='arc', arc_color=C_AXIS_TEXT, line_width=thick)
    f_lo, f_hi = gauge_frac(G.target * (1 - G.tempo_tol / 100)), gauge_frac(G.target * (1 + G.tempo_tol / 100))
    graph.draw_arc((cx - r, cy + r), (cx + r, cy - r), extent=-180 * (f_hi - f_lo), start_angle=180 * (1 - f_lo), style='arc', arc_color=C_ON_TEMPO, line_width=thick)
    graph.draw_line((cx, cy + r * 0.8), (cx, cy + r * 1.15), color='#FFFFFF', width=2)                  # the target mark
    state = tempo_state(bpm)
    color = tempo_color(state)
    if bpm is not None:
        a = math.pi * (1 - gauge_frac(bpm))
        graph.draw_line((cx, cy), (cx + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a)), color=color, width=max(2, int(r * 0.09)))
    graph.draw_circle((cx, cy), max(2, r * 0.1), fill_color=color, line_color=color)


def paint_color(window, value_key, text, color, sub):
    """Like paint(), but with an explicit color (hex) instead of the loudness gradient; None = neutral tile"""
    if color is None:
        window[value_key].update(text, background_color=C_TILE_NEUTRAL, text_color=C_AXIS_TEXT)
        window[KT_LEVEL(value_key)].update(sub, text_color=C_AXIS_TEXT)
        G.tile_target.pop(value_key, None)
        G.tile_now.pop(value_key, None)
        return
    target = rgb(color)
    G.tile_target[value_key] = target
    if value_key not in G.tile_now:
        G.tile_now[value_key] = target
        window[value_key].update(text, background_color=color, text_color=C_ON_LEVEL)
    else:
        window[value_key].update(text, text_color=C_ON_LEVEL)
    window[KT_LEVEL(value_key)].update(sub, text_color=color)


def refresh_tempo(window):
    """TEMPO tile: bpm estimate, state colour, sub text and the dial"""
    state = tempo_state(G.bpm)
    sub = {'slow': f'slow \u00b7 target {G.target}', 'fast': f'fast \u00b7 target {G.target}', 'ok': f'on target {G.target}'}.get(state, f'target {G.target} \u00b1{G.tempo_tol}%')
    paint_color(window, K_TEMPO, f'{G.bpm:.0f}' if G.bpm else '-', tempo_color(state) if state else None, sub)
    draw_gauge(window[K_GAUGE], G.bpm)


def vel_text(vel):
    return '' if vel is None or G.vel_color == VC_OFF else f'v{vel:.0f}'


def dv_parse(text):
    """'B\u2193 M\u2191 T\u2191 A\u2191' -> {voice: position}; anything unreadable counts as off"""
    positions = {v: 'off' for v in DV_VOICES}
    for token, voice in zip(str(text).split(), DV_VOICES):
        positions[voice] = DV_FROM_ARROW.get(token[-1:], 'off')
    return positions


def dv_format(positions):
    return ' '.join(f'{letter}{DV_ARROW[positions[v]]}' for letter, v in zip('BMTA', DV_VOICES))


def chord_leaders(notes, by_voice):
    """The dots that carry a velocity label: one per chord (notes within ONSET_GAP, per voice when by_voice).
    Returns (highest note of the chord, lowest loudness in it, highest loudness in it) so the label can sit clear of every dot of the chord"""
    leaders, group_start, best, lo, hi = [], {}, {}, {}, {}
    for n in notes:
        key = n.voice if by_voice else DV_ALL
        if key in best and n.t - group_start[key] < ONSET_GAP:
            if n.note > best[key].note:
                best[key] = n
            lo[key], hi[key] = min(lo[key], n.raw), max(hi[key], n.raw)
        else:
            if key in best:
                leaders.append((best[key], lo[key], hi[key]))
            group_start[key], best[key], lo[key], hi[key] = n.t, n, n.raw, n.raw
    leaders.extend((best[k], lo[k], hi[k]) for k in best)
    return leaders


def chord_label_y(pos, leader, lo, hi):
    """Loudness at which a chord's label is anchored: the top dot for 'above', the bottom dot for 'below', the highest note otherwise"""
    return hi if pos == 'above' else lo if pos == 'below' else leader.raw


def dot_label(graph, x, y, vel, value, pos, r_px, xu, upp):
    """Write a velocity beside a dot at graph coordinates (x, y); r_px is the dot radius in pixels"""
    gap_x, gap_y = (r_px + 4 * G.scale) * xu, (r_px + 3 * G.scale) * upp
    where = {'above': ((x, y + gap_y), sg.TEXT_LOCATION_BOTTOM), 'below': ((x, y - gap_y), sg.TEXT_LOCATION_TOP),
             'left': ((x - gap_x, y), sg.TEXT_LOCATION_RIGHT), 'right': ((x + gap_x, y), sg.TEXT_LOCATION_LEFT)}.get(pos)
    if where:
        graph.draw_text(f'{vel:.0f}', where[0], color=vel_color_for(value), font=FONT_DOTVEL, text_location=where[1])


def dot_vel_popup(current):
    """Big-button popup: where the velocity number goes beside the dots of each voice (and of the all-notes dots in Overall mode)"""
    sel = dv_parse(current)
    names = {V_BASS: 'BASS', V_MIDDLE: 'MIDDLE', V_TOP: 'TOP', DV_ALL: 'Overall dots'}
    colors = {V_BASS: VOICE_COLORS[V_BASS], V_MIDDLE: VOICE_COLORS[V_MIDDLE], V_TOP: VOICE_COLORS[V_TOP], DV_ALL: C_RAW}
    on, off = (C_ON_LEVEL, C_STATUS_OK), sg.theme_button_color()
    rows = [[sg.Text('Velocity number beside each dot', font=FONT_PICK)]]
    for v in DV_VOICES:
        rows.append([sg.Text(names[v], size=(12, 1), font=FONT_PICK, text_color=colors[v])] +
                    [sg.Button(label, key=KT_DV(v, pos), size=(7, 2), font=FONT_PICK, button_color=on if sel[v] == pos else off) for pos, label, _ in DV_POSITIONS])
    rows.append([sg.Button('OK', key=K_DV_OK, size=(8, 2), font=FONT_PICK, button_color=(C_ON_LEVEL, C_STATUS_OK)),
                 sg.Button('Cancel', key=K_DV_CANCEL, size=(8, 2), font=FONT_PICK)])
    win = sg.Window('Dot velocity labels', rows, modal=True, keep_on_top=True, finalize=True, element_justification='c', margins=(20, 16))
    win.bind('<Escape>', K_DV_CANCEL)
    result = None
    while True:
        event, _ = win.read()
        if event in (sg.WIN_CLOSED, K_DV_CANCEL):
            break
        if event == K_DV_OK:
            result = dv_format(sel)
            break
        if isinstance(event, tuple) and event[0] == K_DV:
            _, v, pos = event
            if pos != sel[v]:                                  # recolour only the two buttons that change
                win[KT_DV(v, sel[v])].update(button_color=off)
                win[KT_DV(v, pos)].update(button_color=on)
                sel[v] = pos
    win.close()
    return result


def vel_color_for(value):
    """Colour of the velocity text for a loudness value, per the Vel setting"""
    return {VC_WHITE: '#FFFFFF', VC_GREY: C_AXIS_TEXT, VC_AMBER: C_PAUSED}.get(G.vel_color, level_color(value))


def paint(window, value_key, text, value, sub=None, vel=None):
    """Show a big number; its background heads toward the gradient color of the value (eased in ease_tiles), level name (or sub text) underneath,
    the raw MIDI velocity beside it"""
    if value is None:
        window[value_key].update('-', background_color=sg.theme_background_color(), text_color=C_AXIS_TEXT)
        window[KT_LEVEL(value_key)].update('')
        window[KT_VEL(value_key)].update('')
        G.tile_target.pop(value_key, None)
        G.tile_now.pop(value_key, None)
        return
    lo, hi, _, name = level_of(value)
    color = level_rgb(value)
    G.tile_target[value_key] = color
    if value_key not in G.tile_now:                            # first value: show the color immediately, no easing
        G.tile_now[value_key] = color
        window[value_key].update(text, background_color=hexcolor(color), text_color=C_ON_LEVEL)
    else:
        window[value_key].update(text, text_color=C_ON_LEVEL)
    window[KT_LEVEL(value_key)].update(sub if sub is not None else f'{name}  ({lo}-{hi})', text_color=hexcolor(color))
    window[KT_VEL(value_key)].update(vel_text(vel), text_color=vel_color_for(value))


def refresh_voices(window, only_voice=None):
    """Update the BASS / MIDDLE / TOP tiles (all of them, or just the voice that received a note)"""
    for voice in VOICES if only_voice is None else (only_voice,):
        last = last_note_of(voice)
        window[KT_VOICE_LABEL(voice)].update(f'{voice}  {note_name(last.note)}' if last else voice)
        sub = (f'avg {last.voice_avg:.1f}' + (f' {vel_text(last.voice_vel)}' if vel_text(last.voice_vel) else '') + f'   {level_of(last.raw)[3]}') if last else None
        paint(window, KT_VOICE(voice), f'{round(last.raw)}' if last else '', last.raw if last else None, sub=sub, vel=last.vel if last else None)


def ease_tiles(window):
    """Called every timer tick: move each tile background part of the way toward its target color"""
    for key, target in G.tile_target.items():
        cur = G.tile_now.get(key, target)
        if cur == target:
            continue
        new = target if all(abs(c - t) < 1.5 for c, t in zip(cur, target)) else mix(cur, target, TILE_EASE)
        G.tile_now[key] = new
        window[key].update(background_color=hexcolor(new))


def refresh_stats(window):
    n = G.notes[-1] if G.notes else None
    paint(window, K_NOW, f'{round(n.raw)}' if n else '', n.raw if n else None, vel=n.vel if n else None)
    window[K_NOW_LABEL].update(f'NOW {G.last_note}' if G.last_note else 'NOW')
    paint(window, K_BEAT_AVG, f'{n.beat_avg:.1f}' if n else '', n.beat_avg if n else None, vel=n.beat_vel if n else None)
    paint(window, K_NOTE_AVG, f'{n.note_avg:.1f}' if n else '', n.note_avg if n else None, vel=n.note_vel if n else None)
    paint(window, K_PEAK, f'{round(G.peak)}' if G.count else '', G.peak if G.count else None, vel=G.peak_vel if G.count else None)
    paint(window, K_SESSION, f'{G.total / G.count:.1f}' if G.count else '', G.total / G.count if G.count else None,
          sub=f'{level_of(G.total / G.count)[3]}  {G.count} notes' if G.count else None, vel=G.total_vel / G.count if G.count else None)


def update_labels(window, beats, bpm, n_notes):
    window[K_BEAT_AVG_LABEL].update(f'{beats}-BEAT AVG')
    window[K_NOTE_AVG_LABEL].update(f'{n_notes}-NOTE AVG')


def text_px(window, text, font):
    """Pixel width of text in a font at the current screen dpi (cached)"""
    if (text, font) not in G.text_px:
        G.text_px[(text, font)] = tkfont.Font(root=window.TKroot, font=font).measure(text)
    return G.text_px[(text, font)]


def text_height_px(window, font):
    """Line height of a font in pixels at the current screen dpi (cached under an empty-text key)"""
    if ('', font) not in G.text_px:
        G.text_px[('', font)] = tkfont.Font(root=window.TKroot, font=font).metrics('linespace')
    return G.text_px[('', font)]


def set_paused(window, on, now):
    if on == G.paused:
        return
    G.paused = on
    if on:
        G.pause_t = now
        window[K_PAUSE].update('Resume', button_color=(C_ON_LEVEL, C_PAUSED))
    else:
        shift = now - G.pause_t                                # close the gap so the graph carries on where it stopped
        for n in G.notes:
            n.t += shift
        G.tempo_hist = [(t + shift, b) for t, b in G.tempo_hist]
        G.tempo_onsets = [t + shift for t in G.tempo_onsets]
        G.demo_next_t += shift
        window[K_PAUSE].update('Pause', button_color=sg.theme_button_color())


# ---------- Touch picker & presets ----------
def touch_pick(title, choices, current, steps, fmt=str):
    """Big picker for a touch screen.  steps=None: one button per choice (tap = choose).  Otherwise a slider and +/- buttons step through choices; OK/Cancel.
    fmt turns a choice into the text shown (e.g. seconds -> m:ss)"""
    idx = choices.index(current) if current in choices else 0
    if steps is None:
        per_row = 5
        rows = [[sg.Button(str(c), key=KT_PICK(c), size=(6, 2), font=FONT_PICK) for c in choices[i:i + per_row]] for i in range(0, len(choices), per_row)]
        layout = [[sg.Text(title, font=FONT_PICK)]] + rows + [[sg.Button('Cancel', key=K_PICK_CANCEL, size=(8, 2), font=FONT_PICK)]]
    else:
        slider = sg.Slider((0, len(choices) - 1), default_value=idx, orientation='h', size=(40, 36), enable_events=True, disable_number_display=True, key=K_PICK_SLIDER)
        layout = [[sg.Text(title, font=FONT_PICK)], [sg.Text(fmt(choices[idx]), key=K_PICK_VAL, font=FONT_PICK_VALUE, size=(6, 1), justification='c')],
                  [sg.Text(fmt(choices[0]), font=FONT_PICK), slider, sg.Text(fmt(choices[-1]), font=FONT_PICK)],
                  [sg.Button(label, key=KT_STEP(delta), size=(max(5, len(label) + 1), 2), font=FONT_PICK) for delta, label in steps],
                  [sg.Button('OK', key=K_PICK_OK, size=(8, 2), font=FONT_PICK, button_color=(C_ON_LEVEL, C_STATUS_OK)),
                   sg.Button('Cancel', key=K_PICK_CANCEL, size=(8, 2), font=FONT_PICK)]]
    win = sg.Window(title, layout, modal=True, keep_on_top=True, finalize=True, element_justification='c', margins=(20, 16))
    win.bind('<Escape>', K_PICK_CANCEL)
    if steps is not None:
        win[K_PICK_SLIDER].TKScale.configure(sliderlength=int(50 * G.scale))                       # fat handle for a finger
    result = None
    while True:
        event, _ = win.read()
        if event in (sg.WIN_CLOSED, K_PICK_CANCEL):
            break
        if event == K_PICK_OK:
            result = choices[idx]
            break
        if isinstance(event, tuple) and event[0] == K_PICK:
            result = event[1]
            break
        if event == K_PICK_SLIDER:                             # slider dragged: show the value it points at
            idx = int(float(win[K_PICK_SLIDER].TKScale.get()))
            win[K_PICK_VAL].update(fmt(choices[idx]))
        if isinstance(event, tuple) and event[0] == K_STEP:    # +/- button: move the value and the slider together
            idx = max(0, min(len(choices) - 1, idx + event[1]))
            win[K_PICK_VAL].update(fmt(choices[idx]))
            win[K_PICK_SLIDER].update(idx)
    win.close()
    return result


PICKERS = {K_BPM: ('BPM', BPM_CHOICES, STEPS_1_10),                                  # key: (picker title, allowed values, +/- steps or None for a button grid)
           K_BEATS: ('Beats in the beat average', BEATS_CHOICES, STEPS_1_4),
           K_NOTES: ('Notes in the note average', NOTES_CHOICES, STEPS_1_4),
           K_WINDOW_SEC: ('Graph window (time shown)', WINDOW_CHOICES, STEPS_WINDOW),
           K_VEL_MIN: ('Velocity that counts as loudness 1', VEL_MIN_CHOICES, STEPS_1_10),
           K_VEL_MAX: ('Velocity that counts as loudness 10', VEL_MAX_CHOICES, STEPS_1_10),
           K_BASS_MAX: ('BASS: highest note', NOTE_LIST, STEPS_NOTE),
           K_TOP_MIN: ('TOP: lowest note', NOTE_LIST, STEPS_NOTE),
           K_Y_TOP: ('Top of the loudness axis', Y_TOP_CHOICES, None),
           K_BIN: ('Bin beats (smoothing)', BIN_CHOICES, None),
           K_NPB: ('Notes per beat (tempo estimate)', NPB_CHOICES, None),
           K_TEMPO_TOL: ('On-tempo bracket (+- %)', TEMPO_TOL_CHOICES, STEPS_1),
           K_SPEED: ('Playback speed (%)', SPEED_CHOICES, STEPS_SPEED),
           K_TEXT_SIZE: ('Text size', TEXT_SIZE_CHOICES, None),
           K_VEL_COLOR: ('Velocity text colour', VEL_COLOR_CHOICES, None)}
def edit_value(window, key, values):
    """Open the touch picker for one setting and, if a new value was chosen, put it in the value box and recompute"""
    if key == K_DOT_VEL:                                       # its own popup: a position for each voice
        chosen = dot_vel_popup(values.get(K_DOT_VEL, DV_DEFAULT))
        if chosen is not None:
            window[key].update(chosen)
        return
    title, choices, steps = PICKERS[key]
    current = next((c for c in choices if str(c) == str(values.get(key))), choices[0])   # value boxes hold strings; find the matching choice
    chosen = touch_pick(title, choices, current, steps, fmt=mmss if key == K_WINDOW_SEC else str)
    if chosen is not None and chosen != current:
        window[key].update(str(chosen))
        window.write_event_value(K_REBUILD if key == K_TEXT_SIZE else K_RECALC, key)


PRESET_KEYS = (K_BPM, K_BEATS, K_SHOW_NOTE_AVG, K_NOTES, K_WINDOW_SEC, K_VEL_MIN, K_VEL_MAX, K_BASS_MAX, K_TOP_MIN, K_Y_TOP, K_BIN, K_NPB, K_TEMPO_TOL,
               K_TEMPO_STRIP, K_GRAPH_MODE, K_DOT_MODE, K_VEL_COLOR, K_DOT_VEL)


def presets():
    return sg.user_settings_get_entry(K_PRESETS, {})


def preset_names():
    return sorted(presets().keys(), key=str.lower)


def preset_save(window, values):
    """Ask for a name (popup keyboard friendly) and store the current settings under it; an existing name is overwritten"""
    name = sg.popup_get_text('Preset name', title='Save preset', default_text=values[K_PRESET] or '', font=FONT_PICK, keep_on_top=True, modal=True)
    name = (name or '').strip()
    if not name:
        return
    all_presets = presets()
    all_presets[name] = {k: values[k] for k in PRESET_KEYS}
    sg.user_settings_set_entry(K_PRESETS, all_presets)
    window[K_PRESET].update(values=preset_names(), value=name)


def preset_delete(window, name):
    if name and name in presets() and sg.popup_yes_no(f'Delete preset "{name}"?', title='Delete preset', font=FONT_PICK, keep_on_top=True, modal=True) == 'Yes':
        all_presets = presets()
        del all_presets[name]
        sg.user_settings_set_entry(K_PRESETS, all_presets)
        window[K_PRESET].update(values=preset_names(), value='')


def preset_apply(window, name):
    """Push a stored preset into the controls, then ask the main loop to recompute with the new values"""
    for key, value in presets().get(name, {}).items():
        if key in window.key_dict:
            window[key].update(value)
    window.write_event_value(K_RECALC, name)


def save_settings(window, values):
    """Write every element that was created with setting= to the user settings file (skips timer / thread-event keys that are not elements)"""
    window.settings_save({k: v for k, v in values.items() if k in window.key_dict})


def set_fullscreen(window, on, save=True):
    """Full screen the Follow Me way: tk's -fullscreen attribute, then -topmost False so the window is never left pinned on top"""
    G.fullscreen = on
    window.TKroot.attributes('-fullscreen', on)
    try:
        window.TKroot.attributes('-topmost', False)         # full screen must not pin the window above other windows or its own dialogs
    except Exception:
        pass
    window[K_FULL].update('Windowed' if on else 'Full', button_color=(C_ON_LEVEL, C_PAUSED) if on else sg.theme_button_color())
    if save:
        sg.user_settings_set_entry(K_FULLSCREEN, on)


def show_controls(window, on):
    window[K_CONTROLS].update(visible=on)
    window[K_EXTRAS].update(visible=on)
    window[K_TOGGLE_CONTROLS].update('▲' if on else '▼')
    sg.user_settings_set_entry(K_CONTROLS_HIDDEN, not on)


def axis_top(y_top_setting):
    """Top loudness value shown on the graph: the rounded-up peak (3..10) or the fixed value chosen by the user"""
    if y_top_setting == Y_TOP_PEAK:
        return min(10, max(3, math.ceil(G.peak))) if G.count else 10
    try:
        return min(10, max(3, int(y_top_setting)))
    except (TypeError, ValueError):
        return 10


def binned(notes, bin_sec, now, attr='raw', voice=None, with_vel=False):
    """One (x, mean) point per time bin for one voice (or all notes): bins are aligned to absolute time, x is the bin center.
    with_vel adds the bin's mean MIDI velocity as a third item"""
    sums = {}
    for n in notes:
        if voice is None or n.voice == voice:
            acc = sums.setdefault(math.floor(n.t / bin_sec), [0.0, 0, 0.0])
            acc[0], acc[1], acc[2] = acc[0] + getattr(n, attr), acc[1] + 1, acc[2] + n.vel
    if with_vel:
        return [((b + 0.5) * bin_sec - now, total / cnt, vel / cnt) for b, (total, cnt, vel) in sorted(sums.items())]
    return [((b + 0.5) * bin_sec - now, total / cnt) for b, (total, cnt, vel) in sorted(sums.items())]


def tempo_runs(pts):
    """Split a tempo line [(x, y, bpm), ...] into runs of one colour [(colour, [(x, y), ...]), ...]: a segment takes the state of the point it ends at"""
    runs, cur, color = [], [], None
    for x, y, bpm in pts:
        c = tempo_color(tempo_state(bpm))
        if color is not None and c != color:
            runs.append((color, cur))
            cur = [cur[-1]]
        cur.append((x, y))
        color = c
    if cur:
        runs.append((color, cur))
    return runs


def strip_bpm_frac(bpm):
    """Vertical position of a bpm inside the tempo strip: 0 = bottom (target - STRIP_RANGE), 0.5 = target, 1 = top (target + STRIP_RANGE)"""
    return max(0.0, min(1.0, 0.5 + (bpm - G.target) / G.target * 0.5 / STRIP_RANGE))


def draw_tempo_strip(graph, now, win_sec, pad, ybot, ytop_strip, xu):
    """Tempo band under the plot: bracket, target line + bpm, and the tempo line coloured by state over the graph's time window"""
    sh = ytop_strip - ybot
    graph.draw_rectangle((-win_sec, ytop_strip), (pad, ybot), fill_color=C_STRIP_BG, line_color=C_STRIP_BG)
    lo, hi = strip_bpm_frac(G.target * (1 - G.tempo_tol / 100)), strip_bpm_frac(G.target * (1 + G.tempo_tol / 100))
    band = dim(C_ON_TEMPO, 0.35)
    graph.draw_rectangle((-win_sec, ybot + sh * hi), (0, ybot + sh * lo), fill_color=band, line_color=band)
    graph.draw_line((-win_sec, ybot + sh * 0.5), (0, ybot + sh * 0.5), color='#FFFFFF')
    graph.draw_line((-win_sec, ytop_strip), (pad, ytop_strip), color=C_AXIS_TEXT)
    graph.draw_text(f'{G.target}', (pad / 2, ybot + sh * 0.5), color='#FFFFFF', font=FONT_DYNAMICS)
    graph.draw_text('tempo', (-win_sec + 6 * xu, ytop_strip - sh * 0.02), color=C_AXIS_TEXT, font=FONT_DYNAMICS, text_location=sg.TEXT_LOCATION_TOP_LEFT)
    start = next((i for i, (t, b) in enumerate(G.tempo_hist) if t >= now - win_sec), len(G.tempo_hist))
    pts = G.tempo_hist[max(0, start - 1):]
    for color, run in tempo_runs([(t - now, ybot + sh * strip_bpm_frac(b), b) for t, b in pts]):
        if len(run) > 1:
            graph.draw_lines(run, color=color, width=W_VOICE * G.scale)
    if pts:
        t, b = pts[-1]
        graph.draw_point((t - now, ybot + sh * strip_bpm_frac(b)), size=DOT_PX * 0.7 * G.scale * xu, color=tempo_color(tempo_state(b)))


def redraw(graph, now, win_sec, show_note_avg, mode, dot_mode, y_top, bin_sec, tempo_strip, dot_vel):
    window = graph.ParentForm
    w, h = graph.get_size()
    if not w or w < 40 or h < 40:
        return
    graph.CanvasSize = (w, h)                                  # Graph does not track its own size when it expands with the window
    band_px = text_height_px(window, FONT_LEGEND) * 1.25                        # top band holding the legend
    line_px = text_height_px(window, FONT_DYNAMICS)
    level_px = 2 * (h - band_px) / max(1, y_top)                                # pixel height of one 2-unit dynamics band
    two_lines = level_px >= 2.3 * line_px                                       # "ff" over "9-10" if it fits, else "ff 9-10" on one line
    labels = [f'{name}\n{lo}-{hi}' if two_lines else f'{name} {lo}-{hi}' for lo, hi, color, name in LEVELS]
    pad_px = max(text_px(window, t, FONT_DYNAMICS) for t in [x.split('\n')[-1] for x in labels] + ['mf']) + 16 * G.scale   # right-hand margin
    pad = pad_px * win_sec / max(1, w - pad_px)                                 # ... expressed in graph x-units (seconds)
    strip_px = (h - band_px) * STRIP_FRACTION / (1 + STRIP_FRACTION) if tempo_strip else 0   # tempo strip: 1/8 of the plot height
    upp = y_top / max(1, h - band_px - strip_px)                                # loudness units per pixel inside the plot area
    ytop = y_top + 0.4 + band_px * upp                                          # graph coordinate of the top edge
    y_band = y_top + 0.4 + band_px * upp / 2                                    # vertical center of the top band
    ybot = 0.4 - strip_px * upp                                                 # graph coordinate of the bottom edge (below the strip)
    graph.change_coordinates((-win_sec, ybot), (pad, ytop))
    graph.erase()
    for i in range(4, int(round(ytop * 10))):                 # vertical gradient background: one thin strip per 0.1 loudness
        y0, y1 = i / 10, min(ytop, i / 10 + 0.1)
        fill = dim(level_color((y0 + y1) / 2))
        graph.draw_rectangle((-win_sec, y1), (pad, y0), fill_color=fill, line_color=fill)
    for (lo, hi, color, name), label in zip(LEVELS, labels):  # level names down the right-hand margin (only the levels that are on screen)
        if lo <= y_top:
            graph.draw_text(label, (pad / 2, (lo + min(hi, y_top)) / 2), color=color, font=FONT_DYNAMICS)
    step = next(s for s in (1, 2, 5, 10, 15, 30, 60, 120, 300, 600) if win_sec / s <= 12)     # time grid: at most ~12 labels
    for s in range(step, int(win_sec), step):
        graph.draw_line((-s, 0.4), (-s, ytop), color=C_GRID)
        graph.draw_text(f'-{s}s' if win_sec < 120 else f'-{mmss(s)}', (-s, 0.65), color=C_AXIS_TEXT, font=FONT_AXIS)
    for y in range(1, y_top + 1):
        graph.draw_line((-win_sec, y), (0, y), color=C_GRID)
        graph.draw_text(str(y), (-win_sec + win_sec * 0.006, y), color=C_AXIS_TEXT, font=FONT_AXIS, text_location=sg.TEXT_LOCATION_LEFT)
    graph.draw_line((0, 0.4), (0, ytop), color=C_AXIS_TEXT, width=2)
    xu = (win_sec + pad) / w                                   # graph x-units per pixel
    dv = dv_parse(dot_vel)                                     # where the velocity labels go, per voice
    if tempo_strip:
        draw_tempo_strip(graph, now, win_sec, pad, ybot, 0.4, xu)
    if mode == M_OVERALL:                                     # legend, top-left: line name in its line color
        legend = [('RAW', C_RAW), ('BEAT AVG', C_BEAT_AVG)] + ([('NOTE AVG', C_NOTE_AVG)] if show_note_avg else [])
    else:
        legend = [(v + (' avg' if mode == M_VOICES_AVG else ''), VOICE_COLORS[v]) for v in VOICES]
    x = -win_sec + (text_px(window, '10', FONT_AXIS) + 16 * G.scale) * xu    # start right of the "10" axis label
    for text, color in legend:
        graph.draw_text(text, (x, y_band), color=color, font=FONT_LEGEND, text_location=sg.TEXT_LOCATION_LEFT)
        x += (text_px(window, text, FONT_LEGEND) + 30 * G.scale) * xu         # measured width, so labels never overlap at any dpi
    if G.paused:
        graph.draw_text('❚❚  PAUSED   (F9 / Resume)', (-win_sec / 2, 1.5), color=C_PAUSED, font=FONT_PAUSED)
    if G.count:
        graph.draw_line((-win_sec, G.peak), (0, G.peak), color=C_PEAK, width=W_PEAK * G.scale)
        label_y = G.peak - 0.3 if G.peak > y_top - 0.3 else G.peak + 0.3                  # keep the label inside the plot area
        graph.draw_text(f'peak {G.peak:.1f}', (-win_sec * 0.01, label_y), color=C_PEAK, font=FONT_AXIS, text_location=sg.TEXT_LOCATION_RIGHT)
    dot = DOT_PX * G.scale * (win_sec + pad) / w               # marker diameter expressed in graph x-units
    if bin_sec and bin_sec / xu >= 8 * G.scale:                # vertical lines at the bin boundaries (unless they would be a few pixels apart)
        for b in range(math.floor((now - win_sec) / bin_sec), math.floor(now / bin_sec) + 1):
            graph.draw_line((b * bin_sec - now, 0.4), (b * bin_sec - now, ytop), color=C_BIN_LINE)
    vis = G.notes[first_index_at(now - win_sec - bin_sec):]                       # include the notes that complete the left-most bin
    if not vis:
        return
    if mode == M_OVERALL:
        if len(vis) > 1 and show_note_avg:
            graph.draw_lines([(n.t - now, n.note_avg) for n in vis], color=C_NOTE_AVG, width=W_NOTE_AVG * G.scale)
        if len(vis) > 1:
            graph.draw_lines([(n.t - now, n.beat_avg) for n in vis], color=C_BEAT_AVG, width=W_BEAT_AVG * G.scale)
        if bin_sec:                                            # one dot per bin for all notes, colored by the bin's loudness
            pts3 = binned(vis, bin_sec, now, with_vel=True)
            pts = [(x, y) for x, y, _ in pts3]
            if len(pts) > 1:
                graph.draw_lines(pts, color=C_RAW, width=W_VOICE * G.scale)
            for x, y, v in pts3:
                graph.draw_point((x, y), size=dot * 1.3, color=level_color(y))
                dot_label(graph, x, y, v, y, dv[DV_ALL], DOT_PX * 0.65 * G.scale, xu, upp)
        elif len(vis) > 1:
            graph.draw_lines([(n.t - now, n.raw) for n in vis], color=C_RAW, width=W_RAW * G.scale)
    else:                                                      # one line per voice: raw notes or the voice's beat average, or binned means
        attr = 'raw' if mode == M_VOICES else 'voice_avg'
        for voice in VOICES:
            pts3 = binned(vis, bin_sec, now, attr, voice, with_vel=True) if bin_sec else []
            pts = [(x, y) for x, y, _ in pts3] if bin_sec else [(n.t - now, getattr(n, attr)) for n in vis if n.voice == voice]
            if len(pts) > 1:
                graph.draw_lines(pts, color=VOICE_COLORS[voice], width=(W_VOICE if attr == 'raw' and not bin_sec else W_VOICE_AVG) * G.scale)
            if bin_sec:                                        # one dot per bin per voice
                for x, y, v in pts3:
                    graph.draw_point((x, y), size=dot * 1.3, color=VOICE_COLORS[voice] if dot_mode == D_VOICE else level_color(y))
                    dot_label(graph, x, y, v, y, dv[voice], DOT_PX * 0.65 * G.scale, xu, upp)
    if not bin_sec:                                            # every note is a dot: loudness gradient, or the note's voice color
        for n in vis:
            graph.draw_point((n.t - now, n.raw), size=dot, color=VOICE_COLORS[n.voice] if dot_mode == D_VOICE else level_color(n.raw))
        for n, lo, hi in chord_leaders(vis, by_voice=mode != M_OVERALL):     # one velocity label per chord: its highest note's velocity
            pos = dv[DV_ALL if mode == M_OVERALL else n.voice]
            dot_label(graph, n.t - now, chord_label_y(pos, n, lo, hi), n.vel, n.raw, pos, DOT_PX * 0.5 * G.scale, xu, upp)


def _png_font(size):
    """Bold TrueType font for the PNG at a pixel size; falls back to Pillow's default font when none of the usual files exist"""
    from PIL import ImageFont
    for name in ('segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf', 'LiberationSans-Bold.ttf'):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def save_session_png(values, mode, dot_mode, bin_sec, y_top, beats, bpm, n_notes):
    """Render every note since the last Reset - same style as the live graph, full time span, header with the session numbers - and save it as a PNG"""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        sg.popup_error('Saving a PNG needs the Pillow package:\n\n    pip install pillow', title='Save PNG', font=FONT_PICK, keep_on_top=True)
        return
    if not G.notes:
        sg.popup_quick_message('Nothing to save yet - play something first', font=FONT_PICK, background_color=C_PAUSED, text_color=C_ON_LEVEL, auto_close_duration=3)
        return
    stamp = time.strftime('%Y-%m-%d_%H%M', time.localtime(G.session_start))
    pictures = os.path.join(os.path.expanduser('~'), 'Pictures')
    default = os.path.join(pictures if os.path.isdir(pictures) else os.path.expanduser('~'), f'piano_dynamics_{stamp}.png')
    path = sg.popup_get_file('Save the session as', title='Save PNG', save_as=True, default_path=default, default_extension='.png', no_window=True,
                             file_types=(('PNG image', '*.png'),), keep_on_top=True)
    if not path:
        return
    notes = list(G.notes)
    t0, t1 = notes[0].t, max(notes[-1].t, notes[0].t + 1)
    duration = t1 - t0
    W = int(min(PNG_MAX_W, max(PNG_MIN_W, duration * PNG_PX_PER_SEC)))
    H = PNG_H
    f_title, f_stats, f_legend, f_axis = _png_font(30), _png_font(22), _png_font(30), _png_font(20)
    left, right, top, bottom = 90, 140, 185, 70
    strip_h = int((H - top - bottom) * STRIP_FRACTION / (1 + STRIP_FRACTION)) if values.get(K_TEMPO_STRIP) else 0
    pw, ph = W - left - right, H - top - bottom - strip_h
    img = Image.new('RGB', (W, H), C_BG)
    d = ImageDraw.Draw(img)
    y_lo, y_hi = 0.4, y_top + 0.4

    def X(t):
        return left + (t - t0) / duration * pw

    def Y(v):
        return top + (y_hi - v) / (y_hi - y_lo) * ph

    for py in range(top, top + ph):                            # vertical loudness gradient, one image row at a time
        v = y_hi - (py - top) / ph * (y_hi - y_lo)
        d.line([(left, py), (left + pw, py)], fill=dim(level_color(v)))
    for lo, hi, color, name in LEVELS:                         # dynamics labels down the right, same font as the axis / peak label
        if lo <= y_top:
            d.text((left + pw + right / 2, (Y(lo) + Y(min(hi, y_top))) / 2), f'{name}\n{lo}-{hi}', fill=color, font=f_axis, anchor='mm', align='center')
    for v in range(1, y_top + 1):                              # horizontal grid + loudness numbers
        d.line([(left, Y(v)), (left + pw, Y(v))], fill=C_GRID)
        d.text((left - 12, Y(v)), str(v), fill=C_AXIS_TEXT, font=f_axis, anchor='rm')
    step = next(s for s in (1, 2, 5, 10, 15, 30, 60, 120, 300, 600) if duration / s <= 16)   # time grid every 'step' seconds, mm:ss labels
    for s in range(0, int(duration) + 1, step):
        d.line([(X(t0 + s), top), (X(t0 + s), top + ph)], fill=C_GRID)
        d.text((X(t0 + s), top + ph + strip_h + 10), f'{s // 60}:{s % 60:02d}', fill=C_AXIS_TEXT, font=f_axis, anchor='mt')
    if bin_sec:                                                # bin boundaries
        for b in range(math.floor(t0 / bin_sec), math.floor(t1 / bin_sec) + 1):
            d.line([(X(b * bin_sec), top), (X(b * bin_sec), top + ph)], fill=C_BIN_LINE)
    if strip_h:                                                # tempo strip under the plot
        sy0, sy1 = top + ph, top + ph + strip_h
        d.rectangle([left, sy0, left + pw + right, sy1], fill=C_STRIP_BG)
        d.line([(left, sy0), (left + pw + right, sy0)], fill=C_AXIS_TEXT)
        lo, hi = strip_bpm_frac(G.target * (1 - G.tempo_tol / 100)), strip_bpm_frac(G.target * (1 + G.tempo_tol / 100))
        d.rectangle([left, sy1 - strip_h * hi, left + pw, sy1 - strip_h * lo], fill=dim(C_ON_TEMPO, 0.35))
        d.line([(left, sy1 - strip_h * 0.5), (left + pw, sy1 - strip_h * 0.5)], fill='#FFFFFF')
        d.text((left + pw + right / 2, sy1 - strip_h * 0.5), f'{G.target}', fill='#FFFFFF', font=f_axis, anchor='mm')
        d.text((left + 6, sy0 + 4), 'tempo', fill=C_AXIS_TEXT, font=f_axis, anchor='lt')
        for color, run in tempo_runs([(X(t), sy1 - strip_h * strip_bpm_frac(b), b) for t, b in G.tempo_hist]):
            if len(run) > 1:
                d.line(run, fill=color, width=4, joint='curve')
    d.line([(left, Y(G.peak)), (left + pw, Y(G.peak))], fill=C_PEAK, width=2)
    d.text((left + pw - 8, Y(G.peak) - 6), f'peak {G.peak:.1f}', fill=C_PEAK, font=f_axis, anchor='rb')

    def poly(pts, color, width):
        if len(pts) > 1:
            d.line([(X(t), Y(v)) for t, v in pts], fill=color, width=width, joint='curve')

    def dots(pts, color_fn, r):
        for t, v in pts:
            d.ellipse([X(t) - r, Y(v) - r, X(t) + r, Y(v) + r], fill=color_fn(v))

    dv, f_dot = dv_parse(values.get(K_DOT_VEL, DV_DEFAULT)), _png_font(14)

    def label(t, value, vel, pos, r):                          # velocity beside a dot, anchored at loudness 'value'
        where = {'above': ((X(t), Y(value) - r - 3), 'ms'), 'below': ((X(t), Y(value) + r + 3), 'mt'),
                 'left': ((X(t) - r - 4, Y(value)), 'rm'), 'right': ((X(t) + r + 4, Y(value)), 'lm')}.get(pos)
        if where:
            d.text(where[0], f'{vel:.0f}', fill=vel_color_for(value), font=f_dot, anchor=where[1])

    if mode == M_OVERALL:
        if values[K_SHOW_NOTE_AVG]:
            poly([(n.t, n.note_avg) for n in notes], C_NOTE_AVG, 4)
        poly([(n.t, n.beat_avg) for n in notes], C_BEAT_AVG, 5)
        if bin_sec:
            pts3 = binned(notes, bin_sec, 0, with_vel=True)
            pts = [(t, v) for t, v, _ in pts3]
            poly(pts, C_RAW, 4)
            dots(pts, level_color, 7)
            for t, v, vel in pts3:
                label(t, v, vel, dv[DV_ALL], 7)
        else:
            poly([(n.t, n.raw) for n in notes], C_RAW, 2)
            dots([(n.t, n.raw) for n in notes], level_color, 5)
            for n, lo, hi in chord_leaders(notes, by_voice=False):
                label(n.t, chord_label_y(dv[DV_ALL], n, lo, hi), n.vel, dv[DV_ALL], 5)
        legend = [('RAW', C_RAW), ('BEAT AVG', C_BEAT_AVG)] + ([('NOTE AVG', C_NOTE_AVG)] if values[K_SHOW_NOTE_AVG] else [])
    else:
        attr = 'raw' if mode == M_VOICES else 'voice_avg'
        for voice in VOICES:
            pts3 = binned(notes, bin_sec, 0, attr, voice, with_vel=True) if bin_sec else []
            pts = [(t, v) for t, v, _ in pts3] if bin_sec else [(n.t, getattr(n, attr)) for n in notes if n.voice == voice]
            poly(pts, VOICE_COLORS[voice], 5 if bin_sec or attr != 'raw' else 4)
            if bin_sec:
                dots(pts, (lambda v, c=VOICE_COLORS[voice]: c) if dot_mode == D_VOICE else level_color, 7)
                for t, v, vel in pts3:
                    label(t, v, vel, dv[voice], 7)
        if not bin_sec:
            for n in notes:
                r = 5
                d.ellipse([X(n.t) - r, Y(n.raw) - r, X(n.t) + r, Y(n.raw) + r], fill=VOICE_COLORS[n.voice] if dot_mode == D_VOICE else level_color(n.raw))
            for n, lo, hi in chord_leaders(notes, by_voice=True):
                label(n.t, chord_label_y(dv[n.voice], n, lo, hi), n.vel, dv[n.voice], 5)
        legend = [(v + (' avg' if mode == M_VOICES_AVG else ''), VOICE_COLORS[v]) for v in VOICES]

    x = left
    for text, color in legend:                                 # legend just above the plot
        d.text((x, top - 12), text, fill=color, font=f_legend, anchor='ls')
        x += d.textlength(text, font=f_legend) + 40
    voice_avgs = {v: [n.raw for n in notes if n.voice == v] for v in VOICES}
    started = time.strftime('%Y-%m-%d %H:%M', time.localtime(G.session_start))
    title = f"{APP_TITLE}   -   {values.get(K_PRESET) or 'no preset'}   -   started {started}   -   {int(duration) // 60}:{int(duration) % 60:02d} played"
    tempo = f"      tempo avg {statistics.mean(G.tempo_samples):.0f} bpm (target {G.target} \u00b1{G.tempo_tol}%)" if G.tempo_samples else ''
    stats = (f"session avg {G.total / G.count:.1f}   peak {G.peak:.1f}   {G.count} notes      " +
             '   '.join(f"{v} avg {sum(a) / len(a):.1f}" if a else f'{v} -' for v, a in voice_avgs.items()) + tempo)
    settings = (f"BPM {bpm}   beat avg {beats} beats   note avg {n_notes}   bin {values.get(K_BIN)} beats   "
                f"vel {values.get(K_VEL_MIN)}-{values.get(K_VEL_MAX)}   bass <= {values.get(K_BASS_MAX)}   top >= {values.get(K_TOP_MIN)}")
    d.text((left, 20), title, fill=C_TEXT, font=f_title, anchor='lt')
    d.text((left, 66), stats, fill=C_AXIS_TEXT, font=f_stats, anchor='lt')
    d.text((left, 96), settings, fill=C_AXIS_TEXT, font=f_stats, anchor='lt')
    try:
        img.save(path)
        sg.popup_quick_message(f'Saved  {path}', font=FONT_PICK, background_color=C_STATUS_OK, text_color=C_ON_LEVEL, auto_close_duration=4)
    except OSError as e:
        sg.popup_error(f'Could not save {path}\n\n{e}', title='Save PNG', font=FONT_PICK, keep_on_top=True)


def stat_tile(label, label_key, value_key, color, key=None, visible=True):
    """Compact tile for the right-hand column: big number (gradient background) with the colored label and the level/avg text stacked beside it"""
    right = [[sg.Text(label, key=label_key, font=FONT_LABEL, text_color=color, size=(12, 1), pad=(0, 0))],
             [sg.Text('', key=KT_LEVEL(value_key), font=FONT_LABEL, size=(13, 1), pad=(0, 0))]]
    number = [[sg.Text('-', key=value_key, font=FONT_BIG, text_color=C_AXIS_TEXT, size=(3, 1), justification='c', pad=(0, 0))],
              [sg.Text('', key=KT_VEL(value_key), font=FONT_VEL, size=(4, 1), justification='c', pad=(0, 0))]]      # raw velocity under the number
    row = [sg.Column(number, element_justification='c', pad=(0, 0)), sg.Column(right, vertical_alignment='top', pad=((6, 0), 0))]
    return sg.Column([row], key=key, visible=visible, pad=(0, (0, 4)))


def tempo_tile():
    """TEMPO tile: big bpm number, the little dial beside it, label and state text stacked on the right (as in Follow Me)"""
    right = [[sg.Text('TEMPO', key=K_TEMPO_LABEL, font=FONT_LABEL, text_color=C_AXIS_TEXT, size=(13, 1), pad=(0, 0))],
             [sg.Text('', key=KT_LEVEL(K_TEMPO), font=FONT_LABEL, size=(16, 1), pad=(0, 0))]]
    gw, gh = int(60 * G.scale), int(34 * G.scale)
    gauge = sg.Graph((gw, gh), (0, 0), (gw, gh), key=K_GAUGE, background_color=sg.theme_background_color(), pad=((4, 0), 0), tooltip='Tempo dial: target at the top')
    row = [sg.Text('-', key=K_TEMPO, font=FONT_BIG, text_color=C_AXIS_TEXT, size=(3, 1), justification='c', pad=(0, 0), background_color=C_TILE_NEUTRAL), gauge,
           sg.Column(right, pad=((6, 0), 0))]
    return sg.Column([row], pad=(0, (0, 4)))


def voice_tile(voice):
    """Large tile for the bottom row: voice label, huge number (gradient background), avg + level text, all centered"""
    value_key = KT_VOICE(voice)
    col = [[sg.Text(voice, key=KT_VOICE_LABEL(voice), font=FONT_VLABEL, text_color=VOICE_COLORS[voice], size=(16, 1), justification='c')],
           [sg.Text('-', key=value_key, font=FONT_HUGE, text_color=C_AXIS_TEXT, size=(3, 1), justification='c', pad=(0, 2)),
            sg.Text('', key=KT_VEL(value_key), font=FONT_VVEL, size=(4, 1), pad=((6, 0), 2))],                  # raw velocity beside the number
           [sg.Text('', key=KT_LEVEL(value_key), font=FONT_VSUB, size=(16, 1), justification='c')]]
    return sg.Column(col, element_justification='c', pad=(0, 0))


def init_settings():
    """Use the fixed settings file; on the very first run adopt the newest settings file written by an earlier version of this program"""
    sg.user_settings_filename(filename=SETTINGS_FILE)
    if not sg.user_settings_file_exists():
        old = sorted(glob.glob(os.path.join(os.path.dirname(sg.user_settings_filename()), OLD_SETTINGS_GLOB)), key=os.path.getmtime)
        if old:
            shutil.copyfile(old[-1], sg.user_settings_filename())
            sg.user_settings_load()


def build_window(ports, port):
    """Create the main window from the current FONT_* globals and the saved settings, size it, bind keys and restore the display state"""
    sg.set_options(font=FONT_UI)
    show_note_avg = sg.user_settings_get_entry(K_SHOW_NOTE_AVG, True)

    P = ((10, 4), 0)                                                                                    # left/right pad that separates the control groups
    TAP_TT = '  (tap the value or the pencil for a big picker)'

    def field(default, key, width, tooltip):                                                          # read-only value box + clickable pencil mark, both open the picker
        return [sg.Input(str(default), key=key, size=(width, 1), readonly=True, setting=default, justification='c', tooltip=tooltip + TAP_TT),
                sg.Text('\u270E', key=KT_EDIT(key), enable_events=True, text_color=C_EDIT, pad=((0, 4), 0), tooltip='Change: ' + tooltip)]

    top = [sg.Text('MIDI in'), sg.Combo(ports, default_value=port, key=K_PORT, size=(16, 1), readonly=True, enable_events=True), sg.Button('Refresh', key=K_REFRESH),
           sg.Text('Graph', pad=P), sg.Combo(GRAPH_MODES, default_value=M_OVERALL, key=K_GRAPH_MODE, size=(16, 1), readonly=True, enable_events=True, setting=M_OVERALL),
           sg.Text('Dots', pad=P), sg.Combo(DOT_MODES, default_value=D_LOUDNESS, key=K_DOT_MODE, size=(9, 1), readonly=True, enable_events=True, setting=D_LOUDNESS),
           sg.Text('Text', pad=P), *field('100%', K_TEXT_SIZE, 5, 'Size of all text in the program'),
           sg.Text('Vel', pad=P), *field(VC_LOUDNESS, K_VEL_COLOR, 8, 'Raw MIDI velocity beside every loudness number: its colour, or Off'),
           sg.Push(),
           sg.Button('Full', key=K_FULL, size=(8, 1), tooltip='Full screen on / off (F11): whole screen, no title bar'),
           sg.Button('PNG', key=K_SAVE_PNG, tooltip='Save everything since the last Reset as a PNG image (F12)')]
    opts = [sg.Text('BPM'), *field(120, K_BPM, 4, 'Tempo'),
            sg.Text('Beats', pad=P), *field(4, K_BEATS, 3, 'Beats in the beat average'),
            sg.Checkbox('Note avg', default=show_note_avg, key=K_SHOW_NOTE_AVG, enable_events=True, setting=True, pad=P),
            *field(8, K_NOTES, 3, 'Notes in the note average'),
            sg.Text('Win s', pad=P), *field(15, K_WINDOW_SEC, 4, 'Graph window in seconds'),
            sg.Text('Vel@1', pad=P), *field(1, K_VEL_MIN, 4, TT_VEL_MIN),
            sg.Text('Vel@10', pad=P), *field(127, K_VEL_MAX, 4, TT_VEL),
            sg.Text('Notes/beat', pad=P), *field(3, K_NPB, 3, TT_NPB), sg.Text('Tempo \u00b1', pad=P), *field(5, K_TEMPO_TOL, 3, TT_TEMPO_TOL), sg.Text('%', pad=(0, 0)),
            sg.Checkbox('Tempo strip', default=True, key=K_TEMPO_STRIP, enable_events=True, setting=True, pad=P, tooltip='Tempo band along the bottom of the graph')]
    pre = [sg.Text('Bass \u2264'), *field('E3', K_BASS_MAX, 4, TT_BASS),
           sg.Text('Top \u2265', pad=P), *field('F#4', K_TOP_MIN, 4, TT_TOP),
           sg.Text('Y top', pad=P), *field(10, K_Y_TOP, 5, TT_Y_TOP),
           sg.Text('Bin', pad=P), *field(0, K_BIN, 3, TT_BIN),
           sg.Text('Preset', pad=((30, 4), 0)),
           sg.Combo(preset_names(), default_value='', key=K_PRESET, size=(12, 1), readonly=True, enable_events=True, tooltip='Pick a saved preset to apply it'),
           sg.Button('Save', key=K_PRESET_SAVE, tooltip='Save the current settings under a name (new or existing)'),
           sg.Button('Delete', key=K_PRESET_DELETE, tooltip='Delete the selected preset'),
           sg.pin(sg.Column([[sg.Checkbox('Demo notes', key=K_DEMO, enable_events=True, pad=((30, 4), 0)), sg.Text('', key=K_STATUS, font=FONT_LABEL, size=(34, 1))]],
                            key=K_EXTRAS, pad=(0, 0)))]                                                     # Demo + MIDI status live in the control rows
    stats = [sg.Button('Min', key=K_MINIMIZE, font=FONT_LABEL, tooltip='Minimise to the taskbar (comes back in full screen if it was)'), sg.Push(),
             stat_tile('NOW', K_NOW_LABEL, K_NOW, C_RAW), sg.Push(), stat_tile('4-BEAT AVG', K_BEAT_AVG_LABEL, K_BEAT_AVG, C_BEAT_AVG), sg.Push(),
             sg.pin(stat_tile('8-NOTE AVG', K_NOTE_AVG_LABEL, K_NOTE_AVG, C_NOTE_AVG, key=K_NOTE_AVG_COL, visible=show_note_avg)), sg.Push(),
             stat_tile('PEAK', None, K_PEAK, C_PEAK), sg.Push(), stat_tile('SESSION AVG', K_SESSION_LABEL, K_SESSION, C_SESSION), sg.Push(), tempo_tile(), sg.Push(),
             sg.Button('\u25B2', key=K_TOGGLE_CONTROLS, font=FONT_LABEL, tooltip='Hide / show the control rows (F10)')]     # stats row along the bottom
    out_ports = midi_out_ports()
    saved_out = sg.user_settings_get_entry(K_MIDI_OUT, '')
    play = [sg.Button('Open\u2026', key=K_OPEN_MIDI, tooltip='Open a MIDI file (.mid / .midi) to play on the piano and analyse'),
            sg.Text(os.path.basename(G.play_path), key=K_MIDI_FILE, size=(22, 1)),
            sg.Text('MIDI out', pad=P),
            sg.Combo(out_ports, default_value=saved_out if saved_out in out_ports else '', key=K_MIDI_OUT, size=(16, 1), readonly=True, enable_events=True,
                     tooltip='Port the file is played to (the piano itself, or a synth)'),
            sg.Button('Play', key=K_PLAY, size=(6, 1), tooltip='Play the file on the MIDI out port and analyse it (Reset first); press again to stop'),
            sg.Text('Speed', pad=P), *field(100, K_SPEED, 4, TT_SPEED), sg.Text('%', pad=(0, 0)),
            sg.Text('', key=K_PLAY_STATUS, font=FONT_LABEL, size=(34, 1), pad=((16, 0), 0)),
            sg.Text('Dot vel', pad=P), *field(DV_DEFAULT, K_DOT_VEL, 11, 'Velocity number beside the graph dots: position per voice (B M T, A = Overall dots)')]
    controls = sg.pin(sg.Column([top, opts, pre, play], key=K_CONTROLS, expand_x=True, pad=(0, 0)), expand_x=True)
    always = sg.Column([[sg.Button('Pause', key=K_PAUSE, size=(7, 1))], [sg.Button('Reset', key=K_RESET, size=(7, 1))], [sg.Button('Exit', key=K_EXIT, size=(7, 1))]],
                       pad=((0, 4), 0))                                                              # stays visible when the control rows are hidden
    voice_row = [sg.Push()] + sum([[voice_tile(v), sg.Push()] for v in VOICES], []) + [always]            # BASS  MIDDLE  TOP, evenly spread
    layout = [[controls], [sg.Graph((880, 420), (0, 0), (1, 1), key=K_GRAPH, background_color=C_BG, expand_x=True, expand_y=True, pad=(0, 6))],
              [sg.Column([voice_row], expand_x=True, pad=(0, (8, 0)))], [sg.Column([stats], expand_x=True, pad=(0, (6, 0)))]]

    window = sg.Window(APP_TITLE, layout, resizable=True, finalize=True, margins=(8, 6), auto_save_location=True, enable_close_attempted_event=True, icon=ICON)
    G.window = window
    G.scale = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)                                        # 2.0 on a 200% Windows display
    G.text_px.clear()
    sw, sh = sg.Window.get_screen_size()
    window.refresh()
    cw, ch = window.size
    nw, nh = max(cw, int(sw * WINDOW_FRACTION)), max(ch, int(sh * WINDOW_FRACTION))                    # grow to most of the screen, never shrink below natural size
    if (nw, nh) != (cw, ch):
        window.size = (nw, nh)
        window.move((sw - nw) // 2, max(0, (sh - nh) // 2 - 20))                                       # re-center so the enlarged window stays on screen
    window.bind('<Escape>', K_KEY_ESC)
    window.bind('<F11>', K_KEY_F11)
    window.bind('<F12>', K_KEY_F12)
    window.bind('<Map>', K_MAPPED)
    window.bind('<Home>', K_KEY_HOME)
    window.bind('<F10>', K_KEY_F10)
    window.bind('<F9>', K_KEY_F9)
    for key in list(PICKERS) + [K_DOT_VEL]:                    # tapping a value box opens the touch picker; dark read-only background keeps the text readable
        window[key].bind('<Button-1>', TAP)
        window[key].widget.configure(readonlybackground=sg.theme_input_background_color())
    if sg.user_settings_get_entry(K_FULLSCREEN, False):
        set_fullscreen(window, True)
    if sg.user_settings_get_entry(K_CONTROLS_HIDDEN, False):
        show_controls(window, False)
    window[K_STATUS].update(G.status, text_color=C_STATUS_OK if G.status_ok else C_STATUS_BAD)
    if G.paused:
        window[K_PAUSE].update('Resume', button_color=(C_ON_LEVEL, C_PAUSED))
    if G.playing:
        window[K_PLAY].update('Stop', button_color=(C_ON_LEVEL, C_PAUSED))
    G.tile_now.clear()                                         # new tiles start blank: paint them straight away, no easing
    G.tile_target.clear()
    refresh_stats(window)
    refresh_voices(window)
    refresh_tempo(window)
    window.timer_start(100)
    return window


def main():
    init_settings()
    sg.theme('DarkGrey13')
    sg.set_options(font=FONT_UI, dpi_awareness=True, icon=ICON)                                      # icon is used by the main window and every popup
    set_fonts(sg.user_settings_get_entry(K_TEXT_SIZE, '100%'))
    ports = midi_ports()
    saved_port = sg.user_settings_get_entry(K_PORT, '')
    port = saved_port if saved_port in ports else (ports[0] if ports else '')
    open_port(port)
    G.play_path = sg.user_settings_get_entry(K_LAST_MIDI_FILE, '')
    if not os.path.isfile(G.play_path):
        G.play_path = ''
    saved_out = sg.user_settings_get_entry(K_MIDI_OUT, '')
    if saved_out in midi_out_ports():
        open_out_port(saved_out)
    probe = tk.Tk()                                                                                 # screen dpi before the first build (sizes the tempo dial)
    G.scale = max(1.0, probe.winfo_fpixels('1i') / 96)
    probe.destroy()
    G.target, G.tempo_tol, G.npb = sg.user_settings_get_entry(K_BPM, 120), sg.user_settings_get_entry(K_TEMPO_TOL, 5), sg.user_settings_get_entry(K_NPB, 3)
    G.target, G.tempo_tol, G.npb = (int(x) if str(x).isdigit() else d for x, d in ((G.target, 120), (G.tempo_tol, 5), (G.npb, 3)))
    window = build_window(ports, port)
    labels_done = False

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in (sg.WINDOW_CLOSE_ATTEMPTED_EVENT, K_EXIT, K_KEY_ESC):        # X button (close attempt), Exit or ESC: save settings, then close
            save_settings(window, values)
            break
        bpm, beats, n_notes = ival(values, K_BPM, 120), ival(values, K_BEATS, 4), ival(values, K_NOTES, 8)
        win_sec, vel_min, vel_max = ival(values, K_WINDOW_SEC, 15), ival(values, K_VEL_MIN, 1), ival(values, K_VEL_MAX, 127)
        vel_range = (vel_min, max(vel_min + 9, vel_max))                                                # keep at least 9 velocity steps between 1 and 10
        bass_max, top_min = NOTE_NUM.get(values.get(K_BASS_MAX), 52), NOTE_NUM.get(values.get(K_TOP_MIN), 66)
        bin_sec = ival(values, K_BIN, 0) * 60 / bpm                                                     # 0 = no binning
        beat_sec = beats * 60 / bpm
        if (bpm, ival(values, K_TEMPO_TOL, 5), ival(values, K_NPB, 3)) != (G.target, G.tempo_tol, G.npb):
            G.target, G.tempo_tol, G.npb = bpm, ival(values, K_TEMPO_TOL, 5), ival(values, K_NPB, 3)
            refresh_tempo(window)
        now = time.monotonic()
        if not labels_done:
            update_labels(window, beats, bpm, n_notes)
            labels_done = True
        G.play_speed = ival(values, K_SPEED, 100) / 100
        if values.get(K_VEL_COLOR) in VEL_COLOR_CHOICES and values[K_VEL_COLOR] != G.vel_color:
            G.vel_color = values[K_VEL_COLOR]
            refresh_stats(window)
            refresh_voices(window)
        if event == sg.EVENT_TIMER:
            if G.playing:
                progress = f'{os.path.basename(G.play_path)}  {mmss(G.play_pos)} / {mmss(G.play_len)}'
                window[K_PLAY_STATUS].update(progress + ('  paused' if G.paused else ''))
            if values[K_DEMO] and not G.paused:
                demo_tick(window, now, bpm, vel_range, beat_sec, n_notes, bass_max, top_min)
            ease_tiles(window)
            G.tick += 1
            if G.tick % max(1, round(win_sec / 120)) == 0:                                            # long windows: redraw every 2nd .. 10th tick
                redraw(window[K_GRAPH], G.pause_t if G.paused else now, win_sec, values[K_SHOW_NOTE_AVG], values[K_GRAPH_MODE], values[K_DOT_MODE], axis_top(values[K_Y_TOP]),
                       bin_sec, values[K_TEMPO_STRIP], values.get(K_DOT_VEL, DV_DEFAULT))
        elif event == K_MIDI_NOTE:
            t, note, vel = values[K_MIDI_NOTE]
            if not G.paused:
                handle_note(window, t, note, vel, vel_range, beat_sec, n_notes, bass_max, top_min)
        elif event in (K_PAUSE, K_KEY_F9):
            set_paused(window, not G.paused, now)
        elif event in (K_BPM, K_BEATS, K_NOTES, K_VEL_MIN, K_VEL_MAX, K_BASS_MAX, K_TOP_MIN, K_RECALC):
            recompute(vel_range, beat_sec, n_notes, bass_max, top_min)
            update_labels(window, beats, bpm, n_notes)
            refresh_stats(window)
            refresh_voices(window)
            refresh_tempo(window)
            window[K_NOTE_AVG_COL].update(visible=values[K_SHOW_NOTE_AVG])
        elif event == K_REBUILD:                                                                        # Text size changed: same window, new fonts
            save_settings(window, values)
            set_fonts(values[K_TEXT_SIZE])
            window.timer_stop_all()
            window.close()
            window = build_window(ports, values[K_PORT])
            labels_done = False
        elif event == K_SHOW_NOTE_AVG:
            window[K_NOTE_AVG_COL].update(visible=values[K_SHOW_NOTE_AVG])
        elif isinstance(event, str) and event.endswith(TAP) and (event[:-len(TAP)] in PICKERS or event[:-len(TAP)] == K_DOT_VEL):   # tap on a value box
            edit_value(window, event[:-len(TAP)], values)
        elif isinstance(event, tuple) and event[0] == K_EDIT:                                          # pencil mark
            edit_value(window, event[1], values)
        elif event == K_PRESET:
            preset_apply(window, values[K_PRESET])
        elif event == K_PRESET_SAVE:
            preset_save(window, values)
        elif event == K_PRESET_DELETE:
            preset_delete(window, values[K_PRESET])
        elif event == K_PORT:
            open_port(values[K_PORT])
            sg.user_settings_set_entry(K_PORT, values[K_PORT])
        elif event == K_REFRESH:
            ports = midi_ports()
            port = values[K_PORT] if values[K_PORT] in ports else (ports[0] if ports else '')
            window[K_PORT].update(values=ports, value=port)
            open_port(port)
            out_ports = midi_out_ports()
            out = values[K_MIDI_OUT] if values[K_MIDI_OUT] in out_ports else ''
            window[K_MIDI_OUT].update(values=out_ports, value=out)
            open_out_port(out)
        elif event == K_MIDI_OUT:
            open_out_port(values[K_MIDI_OUT])
            sg.user_settings_set_entry(K_MIDI_OUT, values[K_MIDI_OUT])
        elif event == K_OPEN_MIDI:
            path = sg.popup_get_file('MIDI file to play', title='Open MIDI file', file_types=(('MIDI files', '*.mid *.midi'), ('All files', '*.*')), no_window=True,
                                     keep_on_top=True, default_path=G.play_path)
            if path:
                G.play_path = path
                sg.user_settings_set_entry(K_LAST_MIDI_FILE, path)
                window[K_MIDI_FILE].update(os.path.basename(path))
                window[K_PLAY_STATUS].update('')
        elif event == K_PLAY:
            if G.playing:
                stop_playback(window)
            else:
                start_playback(window, G.play_path)
        elif event == K_PLAY_DONE:                                                                      # the file ran to its end (a manual Stop was reported already)
            if not G.play_stop.is_set():
                G.play_thread = None
                window[K_PLAY].update('Play', button_color=sg.theme_button_color())
                window[K_PLAY_STATUS].update(f'{os.path.basename(G.play_path)}  done  {mmss(G.play_len)}')
        elif event in (K_SAVE_PNG, K_KEY_F12):
            save_session_png(values, values[K_GRAPH_MODE], values[K_DOT_MODE], bin_sec, axis_top(values[K_Y_TOP]), beats, bpm, n_notes)
        elif event in (K_RESET, K_KEY_HOME):
            reset(window)
        elif event == K_MINIMIZE:
            G.restore_full = G.fullscreen
            if G.fullscreen:                                                                        # a minimised full-screen window does not restore cleanly
                set_fullscreen(window, False, save=False)
            window.TKroot.iconify()
        elif event == K_MAPPED:                                                                     # shown / restored from the taskbar
            if G.restore_full and window.TKroot.state() == 'normal':
                G.restore_full = False
                set_fullscreen(window, True)
        elif event in (K_FULL, K_KEY_F11):
            set_fullscreen(window, not G.fullscreen)
        elif event in (K_TOGGLE_CONTROLS, K_KEY_F10):
            show_controls(window, not window[K_CONTROLS].visible)

    window.timer_stop_all()
    stop_playback(None)
    close_out_port()
    close_port()
    window.close()


if __name__ == '__main__':
    main()
