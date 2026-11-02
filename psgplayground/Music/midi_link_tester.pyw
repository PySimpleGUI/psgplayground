"""
MIDI Link Tester  (midi_link_tester.pyw)  -  how well a MIDI connection to the piano keeps time: USB against Bluetooth (BT-MIDI Bridge).

LISTEN (what the piano plays): pick the piano's port under "Piano out", then
    Chords          a 4-note chord 6 times - every note is sent at the same moment: it should sound as ONE chord, never rolled
    Chords + extras the same with what a recording carries along with each note (Milka's files: high-resolution velocity, aftertouch) -
                    four messages per note; if this rolls and plain Chords does not, the link chokes on traffic
    Steady notes    a scale, 8 notes a second: the notes should come out perfectly even
    Bigger chords   2, 4, 6, 8, 10 notes at once: where does it start to sound rolled?
    The log says how long the computer took to hand each chord to the port.  It cannot hear the piano: listen.
PLAY (what the piano sends): pick "Piano in", tap Start listening and play chords - 4 notes or more, hands firmly together.  Each chord
    shows how spread its notes arrived (first to last).  USB: a few ms.  Bluetooth: often 10 - 40 ms, the gaps in steps of its
    connection interval (7.5, 15, 30 ms).  Tens of ms more than USB means the coach's timing over Bluetooth is that much less sure.
TWO INPUTS (only if the piano can be on USB and Bluetooth at the same time): put the USB port in "Piano in" and the Bluetooth one in
    "Second in": every note you play shows how much later it arrived over Bluetooth.
ECHO (only if the piano sends back what it is sent - most do not): sends a note, waits for it to come back, shows the round trip.
Save log… writes everything to a text file (send it to whoever helps you).
Keys: Up / Down, PgUp / PgDn, Home / End scroll the log, Esc exits.  Right-click: Edit Me, Version, Exit.
Requires:  pip install PySimpleGUI mido python-rtmidi

CHANGE LOG (newest first, 1 line per change):
2026-11-01  Icon: the Playground's gold Music icon, kept on one line so PSG Dock can read it (it showed the Python logo)
"""
import statistics
import threading
import time

import PySimpleGUI as sg

ICON = b'iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAMAAAD04JH5AAABgFBMVEUeGxcAAAD+xDz49vL/00AiHhnv7Of/yzP/xDxoUyQOCgkkIRtK1WwpJiKuq6a4trJXVFD/qlVN5XSLh4P/AAD/uzpNSkVsaWXzvTv//wDEwb3HxcH/xTyDgHxVRSH/fwA6OTKmo50pRis71nBHymd+e3aVko7S0Mz/xzs0eUJAq1k2hEg7llBANR2YeiyphC7ImzTKoDT/qjH/wjz/yD7/1yf/10D//1Dl4t0sVjJjYFzAvbjHyktiX1r/mTP/qgD/vzv/wjz/zUD+0D7/0kH/4Tz//38vYjg+pldmTSGEy1qH1F7i39o5x2mhnpoYOSglb0FDuF9Q8XpqYCp7qkx5zl682lb/4kMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD/qdIuAAAAgHRSTlP/AP7//v//Baz//////////wP//wEG////Af//df//Av//////////Ov///////////weDwwZWBv///////wUDOEz//6wRAv//////////////////////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAItX8/UAAAfnSURBVHja7ZsJV9s4EIBlO3KIhGIn5CDhTAhHuEsp0LLdbUuv7bX37v//JzsaSY4dEpBdG3ffVq99LyiO55M0MxqNJOKUXMh3gPlftXrVnEqvlR6g0c63oe1GGoBWo+o4G5fVhZxK9XLDcaqNliVATzZ+72LBdSs5FddduNiT3dCzAYCH2quvXfhVnqXivl5t48vvA2g47Qv3Vc7iEeGVe9F2GvcA9BrOm/MCpGuG8zdOo3cXAPA9Lkw8Ijx2pjohAbDhnK0WKh8IVs9AzByAn5wX04/nZASJ8gIEzQRonO3Fn60su6frtRzK+qm7nHjx3lljFkDrrZMQf8I5ZSSHwijnJwkE521rBkDDWY09c3wkhdNcioQ4Oo69fDWmiBFA+3Ki/5VHnBBOcizyfY8m73982Z4GaDntCWGNE+TOscD7eG0ioe20kgC9RvU8+nadkZzFIwJh65GI86pxSMTMlhMHsM54AfKBgE8IKqtmvid6ACILqNQYJwUVzmpRMx09CAqgvRFZAOgfLQoA9OBRZAkb7RjAE2fBoBUoHwlMRy+A0AigsWF8YOW4SPmS4NhI2ttoRAA/Oi919fJR0QBHyxrgJYjVAK3ekwVde1KcBho9PNFtXXiCwTICOFU9MssFi0cE3QVu1bkN4D4EgHsLoBrZwCktHoCeRnZQnQaorLPCCShbr8wHqJHiAUjtPw1AuYoxsk9XXwMAoRVhuhCekSErAAUDBbmi+/wZlOddISFIBoiMANB0TtaCwYqny8ogWAO3lj5wywIA4RTrhIEvBfu64Ocg7LC0wVsGAGik+GKkmx4wDF9EyvA1NQAEUps7UtQsAPl/ZzNVCJcWQPZ+JD45BBFCJ00QmxKAEtH1pRSUVgfFE4JzIUAh65oBvu4Ke4J0APDXCrYS/l11QzA9WK0JUH5pkmH3yny3QqwJUgGgfCVidxsXeZSE14AiiFo4bu9qBHuCNAAT+dDJaG+UrKEK9rm2TjNA9gQpAIx8zws6yuNQFuphH6jQDfxTJ0CjsCZIA8D7qnVLctxV1bUi8vwOPkm5IGxJPdXnOQNwNjDyoa+VxxPGC3hdJgcEZyVDMLAKaK0BKOsoO4f2y1lAyErxyQCETAJhvSaAXrGJp2wBKOmg9kn5SAIfQPG7SpQXgHwW1SMB/NGxUANbAM4CfOkOI5va8W5DF4s+eh9QAR6rF2wHHw4sBsESAPVdtnWTkB3d6l3p7/jAR6uAAYjVk03fDExuOhAoN0+o8GOKJzsePKJ8LF7P9YQR3BHKaSOxAwCHp19IE4Iomj7qX7KeauBwlhZQ9NxMfbIDMBoQTnW1sn2q3hqvV0M2RwsY54eHh+/HMLDUDgCavSJ1Tb6OJpQw3qxEPSKDPxS351P+brTYhLK4uD+UPWgBwNlz9C1oVjFzm1rixOspGqvvPb/VBXwfROvSHNv2gHItRiEiRzQ9tPF6qtzW9Hw6XkyU0ZDZ6ICIXgZrAapc7u3g09TjEsFAT4HypPzF5r4VAPeVVfOEjDkLJTVRaM/h86n+j0v/TQ7Grz/b9AACPJOuT8b/d3hY+CYMglDqzTMEEAk1edeMNf6ASJzPf9zcB8BZXWp0HZ383bMM1PcxQon9KvYsH8U7ALzqcLS49cG1BmDb2tI25/dBHwNlIJhgx0pc/hBMUADAR3sAsat9zc4cAOkxfT0/E/Ormrtsyoct1fny/zsYUHYAH7d+sAboesbdink5r8AABCwCmOxNfJQAzZEUuy992liiPCQA9sD+kIFgDg8PUSVTAGQcghuTiHP/2gLdl1HbwYH0ycom7QFINiWs/XOjt8tu/kbfZ/z7obZJC4BA90AGMwzYZmzHTJufnMbZUNmkhRVQtoaRvpzZrB2RmkE9D56O9toYeY8OCDwqJ0NtjVt/uhYRka8jHe2K794M0q4YVdaPb7WBVLTAMTzB3qsBaH62d8UywqP3J6P0ZKTnAjFjMmyOnz6NZsVfrACu5MBep0p98Gv5m6tpgx1hH2A8IsvvhzazoenOVNkf6kdxY7wLhon5cHRgFRGZoHzbfveAS5OdGZiz8aJuflOGI5ZRsTLEXWG/6pdOC1dMt80EQlI5BqPDMWYW7aLiOga5XdvsuRo0nAtnbV+Tp1CGLM3CRK2DP9mrgFq2zp4zYFGJ6+g0SzMd9a/ZZh3W7pwziN5ETwMQrfa4jQZGK0ma3+p4gIPapzbvpH18eJDf6lgiqJfen/vRuSRfpa7yy5AQsmtFEMnftUpTpckRbU8ycPSOucjk8rbzzRGRSfapLwwBJGlN4Ua+iHJpnOSdqDQEmKjiOuTQyWrpcuQuypI3yaXln6qNCCDkYFywuhcViJcgZxwGKeWnTVZHDUQEdNA6LQLLlol4e/mp0/UTAi+okzgAqQdeevkZtmykkukNg8mGiRev64sCt2yoinunxccR+iTNxlX6HsC419O7M0kCzKSH9psVGXfNZPPC69mbVtdhquZn3biEnTOYcOtXyQ64qsNknfrQU+adU/A5kCNd0p7IWwq7HUbIw+ycRrvHYPrGE8vPmbavv3L3nM76/L86wFA0QNmHWMo6xlP6Qabyj3KVfZit9ON85R9oLP1IZ/mHWks/1lv6webyj3aXfri9/OP95V9wKP+KR+mXXMq/5lP+Rafyr3qVf9mt/Ot+38CFx/KvfJZ/6fUbuPb7LVx8/n73/MHKv7FE6Pk2geehAAAAAElFTkSuQmCC'      # 128 px PNG app icon (title bar / task bar / PSG Dock), base64 - the Playground's gold Music icon

try:
    import mido
except ImportError:                                     # shown in the window
    mido = None

APP_TITLE = 'MIDI Link Tester'
FONT, FONT_BIG, FONT_BTN, FONT_HEAD = ('Segoe UI', 12), ('Segoe UI', 26, 'bold'), ('Segoe UI', 13, 'bold'), ('Segoe UI', 13, 'bold')
C_OK, C_WARN, C_BAD, C_DIM, C_HEAD = '#4ADE80', '#FBBF24', '#F87171', '#9AA6B2', '#93C5FD'
CHORD = (60, 64, 67, 72)                                # C4 E4 G4 C5
SCALE = (60, 62, 64, 65, 67, 69, 71, 72, 71, 69, 67, 65, 64, 62)
CHORD_GAP = 0.12                                        # s: incoming notes this close to the first form one chord
CHORD_DONE = 0.25                                       # s of quiet after which a chord is complete

K_OUT, K_IN, K_IN2, K_REFRESH = '-OUT-', '-IN-', '-IN2-', '-REFRESH-'
K_CHORDS, K_EXTRAS, K_STEADY, K_BIGGER, K_STOP_OUT = '-CHORDS-', '-EXTRAS-', '-STEADY-', '-BIGGER-', '-STOP OUT-'
K_LISTEN, K_STOP_IN, K_ECHO = '-LISTEN-', '-STOP IN-', '-ECHO-'
K_LAST, K_SUMMARY, K_LOG, K_SAVE, K_CLEAR, K_COPY = '-LAST-', '-SUMMARY-', '-LOG-', '-SAVE-', '-CLEAR-', '-COPY-'
K_LOGLINE, K_NOTE, K_OUT_DONE, K_ECHO_EV = '-LOGLINE-', '-NOTE-', '-OUT DONE-', '-ECHO EV-'          # posted by the threads
K_SCROLL = '-SCROLL-'
KT_SCROLL = lambda what: (K_SCROLL, what)
NONE = '(none)'


class G:                                                # program-wide state
    window = None
    out = None                                          # the open output port
    ins = {}                                            # port name -> open input port
    tester = None                                       # the running output test (thread)
    chord = []                                          # (time, pitch, port) of the chord being played
    spreads, gaps = [], []                              # every chord's spread and every gap between its notes (ms)
    pending2 = {}                                       # two inputs: (port, pitch) -> times not matched yet
    delays = []                                         # two inputs: how much later the second input had each note (ms)
    echo = None                                         # the echo test waiting: (pitch, time sent)
    echo_times, echo_lost = [], 0
    log_text = []


def log(text, color=None):
    G.log_text.append(text)
    G.window[K_LOG].print(text, text_color=color)


def post_log(text, color=None):
    """From a thread: a line for the log"""
    G.window.write_event_value(K_LOGLINE, (text, color))


def ports():
    if mido is None:
        return [], []
    try:
        return mido.get_output_names(), mido.get_input_names()
    except Exception:
        return [], []


# ---------------------------------------------------------------------------------------------------------------- LISTEN: output tests
class OutTest(threading.Thread):
    """Sends a test pattern to the piano at exact times and measures how long the port took to take each burst of messages"""
    def __init__(self, port, kind):
        super().__init__(daemon=True)
        self.port, self.kind, self.stop_flag = port, kind, False

    def send_all(self, msgs):
        """Send messages back to back -> ms it took (a port that cannot keep up makes send() wait)"""
        t0 = time.perf_counter()
        for msg in msgs:
            self.port.send(msg)
        return 1000 * (time.perf_counter() - t0)

    def wait_until(self, t):
        while not self.stop_flag:
            left = t - time.perf_counter()
            if left <= 0:
                return
            time.sleep(min(left, 0.01))

    def chord_msgs(self, notes, extras, on=True):
        out = []
        for n in notes:
            if on:
                if extras:                              # what a recording carries along: high-resolution velocity first ...
                    out.append(mido.Message('control_change', control=88, value=40))
                out.append(mido.Message('note_on', note=n, velocity=70))
                if extras:                              # ... aftertouch and another controller after
                    out.append(mido.Message('polytouch', note=n, value=0))
                    out.append(mido.Message('control_change', control=19, value=n))
            else:
                out.append(mido.Message('note_off', note=n, velocity=0))
        return out

    def run(self):
        try:
            if self.kind in (K_CHORDS, K_EXTRAS):
                extras = self.kind == K_EXTRAS
                post_log(f'LISTEN  Chords{" + extras" if extras else ""}: 6 times C-E-G-C, every note sent at the same moment - it should sound as ONE chord',
                         C_HEAD)
                took = []
                start = time.perf_counter() + 0.3
                for i in range(6):
                    self.wait_until(start + i * 1.2)
                    if self.stop_flag:
                        break
                    ms = self.send_all(self.chord_msgs(CHORD, extras))
                    took.append(ms)
                    post_log(f'   chord {i + 1}: {len(CHORD) * (4 if extras else 1)} messages handed over in {ms:.1f} ms')
                    self.wait_until(start + i * 1.2 + 0.7)
                    self.send_all(self.chord_msgs(CHORD, False, on=False))
                if took:
                    post_log(f'   the port took up to {max(took):.1f} ms for a chord' + ('  - it waits: the link is slow' if max(took) > 5 else '  - no waiting'),
                             C_BAD if max(took) > 20 else C_WARN if max(took) > 5 else C_OK)
            elif self.kind == K_STEADY:
                post_log('LISTEN  Steady notes: a scale, 8 notes a second - every note should come exactly on time', C_HEAD)
                late, start = [], time.perf_counter() + 0.3
                for i, n in enumerate(SCALE * 2):
                    t = start + i * 0.125
                    self.wait_until(t)
                    if self.stop_flag:
                        break
                    self.port.send(mido.Message('note_on', note=n, velocity=60))
                    late.append(1000 * (time.perf_counter() - t))
                    self.wait_until(t + 0.1)
                    self.port.send(mido.Message('note_off', note=n, velocity=0))
                if late:
                    post_log(f'   handed over at most {max(late):.1f} ms late (average {statistics.mean(late):.1f} ms)' +
                             ('  - so if the notes sound uneven, it is the link, not the computer' if max(late) <= 20 else '  - the port makes the computer wait'),
                             C_BAD if max(late) > 20 else C_OK)
            elif self.kind == K_BIGGER:
                post_log('LISTEN  Bigger chords: 2, 4, 6, 8, 10 notes at once - where does it start to sound rolled?', C_HEAD)
                start = time.perf_counter() + 0.3
                for i, size in enumerate((2, 4, 6, 8, 10)):
                    notes = [48 + 4 * k - (k // 3) for k in range(size)]
                    self.wait_until(start + i * 1.5)
                    if self.stop_flag:
                        break
                    ms = self.send_all(self.chord_msgs(notes, False))
                    post_log(f'   {size:2d} notes handed over in {ms:.1f} ms')
                    self.wait_until(start + i * 1.5 + 1.0)
                    self.send_all(self.chord_msgs(notes, False, on=False))
            elif self.kind == K_ECHO:
                post_log('ECHO  10 notes, waiting for each to come back on "Piano in" (most pianos do not send back what they are sent)', C_HEAD)
                start = time.perf_counter() + 0.3
                for i in range(10):
                    self.wait_until(start + i * 0.6)
                    if self.stop_flag:
                        break
                    G.window.write_event_value(K_ECHO_EV, ('sent', 84, time.perf_counter()))
                    self.port.send(mido.Message('note_on', note=84, velocity=40))
                    self.wait_until(start + i * 0.6 + 0.3)
                    self.port.send(mido.Message('note_off', note=84, velocity=0))
                self.wait_until(time.perf_counter() + 0.4)
                G.window.write_event_value(K_ECHO_EV, ('done', 0, 0))
        except Exception as e:
            post_log(f'   the test stopped: {e}', C_BAD)
        finally:
            try:
                self.port.send(mido.Message('control_change', control=123, value=0))      # all notes off
            except Exception:
                pass
            G.window.write_event_value(K_OUT_DONE, None)


# ---------------------------------------------------------------------------------------------------------------- PLAY: input tests
def make_callback(name):
    def callback(msg):
        if msg.type == 'note_on' and msg.velocity > 0:
            G.window.write_event_value(K_NOTE, (time.perf_counter(), msg.note, name))  # stamped here, the moment it arrived
    return callback


def note_in(t, pitch, name, first_in):
    """A note arrived: the chord test (first input), two inputs (both), the echo test"""
    if G.echo is not None and name == first_in and pitch == G.echo[0]:
        G.echo_times.append(1000 * (t - G.echo[1]))
        G.echo = None
        return
    if len(G.ins) > 1:                                  # two inputs: the same key on the other port - how much later did the second have it?
        other = [n for n in G.ins if n != name][0]
        waiting = [w for w in G.pending2.get((other, pitch), []) if t - w < 1.0]
        if waiting:
            first = waiting.pop(0)
            G.delays.append(1000 * (t - first) if name != first_in else -1000 * (t - first))
            G.pending2[(other, pitch)] = waiting
            log(f'   note {pitch}: the second input had it {G.delays[-1]:+.1f} ms later', C_WARN if abs(G.delays[-1]) > 15 else C_OK)
            show_two()
        else:
            G.pending2.setdefault((name, pitch), []).append(t)
    if name == first_in and len(G.ins) == 1:            # the chord test (one input)
        if G.chord and t - G.chord[0][0] > CHORD_GAP:
            chord_done()
        G.chord.append((t, pitch, name))


def chord_done():
    """A chord is complete: how spread its notes arrived"""
    notes, G.chord = sorted(G.chord), []
    if len(notes) < 2:
        return
    spread = 1000 * (notes[-1][0] - notes[0][0])
    gaps = [1000 * (b[0] - a[0]) for a, b in zip(notes, notes[1:])]
    G.spreads.append(spread)
    G.gaps += gaps
    color = C_OK if spread <= 10 else C_WARN if spread <= 30 else C_BAD
    G.window[K_LAST].update(f'{len(notes)} notes  ·  spread {spread:.0f} ms', text_color=color)
    log(f'   chord {len(G.spreads)}: {len(notes)} notes, spread {spread:.1f} ms   gaps ' + ', '.join(f'{g:.1f}' for g in gaps) + ' ms', color)
    s = sorted(G.spreads)
    bins = ((0, 2), (2, 10), (10, 20), (20, 40), (40, 1e9))
    hist = '   '.join(f'{lo:g}-{hi:g} ms: {sum(lo <= g < hi for g in G.gaps)}' if hi < 1e9 else f'{lo:g}+ ms: {sum(g >= lo for g in G.gaps)}' for lo, hi in bins)
    G.window[K_SUMMARY].update(f'{len(s)} chords: median spread {statistics.median(s):.0f} ms, worst {s[-1]:.0f} ms        gaps between notes -  {hist}')


def show_two():
    d = sorted(G.delays)
    G.window[K_LAST].update(f'second input: {d[len(d) // 2]:+.0f} ms', text_color=C_WARN if abs(d[len(d) // 2]) > 15 else C_OK)
    G.window[K_SUMMARY].update(f'{len(d)} notes on both inputs: the second one had them {d[len(d) // 2]:+.0f} ms later (median), from {d[0]:+.0f} to {d[-1]:+.0f} ms')


# ---------------------------------------------------------------------------------------------------------------- window
def make_window(outs, ins, settings):
    pick = lambda key, names, default: sg.Combo([NONE] + names, default_value=default if default in names else (names[0] if names and key != K_IN2 else NONE),
                                               key=key, size=(34, 1), readonly=True, font=FONT)
    btn = lambda text, key, tip='': sg.Button(text, key=key, font=FONT_BTN, size=(14, 2), tooltip=tip)
    head = lambda text: sg.Text(text, font=FONT_HEAD, text_color=C_HEAD, pad=(4, (10, 2)))
    note = lambda text: sg.Text(text, font=FONT, text_color=C_DIM, pad=(4, (0, 4)))
    layout = [[sg.Text(APP_TITLE, font=('Segoe UI', 18, 'bold')), sg.Text('how well a MIDI connection keeps time - try USB, then Bluetooth', font=FONT, text_color=C_DIM)],
              [sg.Text('Piano out', font=FONT), pick(K_OUT, outs, settings.get('out')), sg.Text('Piano in', font=FONT, pad=((16, 4), 0)),
               pick(K_IN, ins, settings.get('in')), sg.Text('Second in', font=FONT, pad=((16, 4), 0)), pick(K_IN2, ins, settings.get('in2')),
               sg.Button('Refresh', key=K_REFRESH, font=FONT_BTN, pad=((16, 0), 0))],
              [head('LISTEN  -  what the piano plays (Piano out)')],
              [btn('Chords', K_CHORDS, '4 notes sent at the same moment, 6 times'), btn('Chords + extras', K_EXTRAS, 'The same, with 4 messages per note'),
               btn('Steady notes', K_STEADY, 'A scale, 8 notes a second'), btn('Bigger chords', K_BIGGER, '2 to 10 notes at once'), btn('Stop', K_STOP_OUT)],
              [note('A chord must sound as ONE chord, never rolled; steady notes must come out even.  If Chords + extras rolls and Chords does not, the link chokes on traffic.')],
              [head('PLAY  -  what the piano sends (Piano in)')],
              [btn('Start listening', K_LISTEN, 'Then play chords - 4 notes or more, hands firmly together'), btn('Stop', K_STOP_IN),
               btn('Echo test', K_ECHO, 'Only if the piano sends back what it is sent'),
               sg.Text('play chords: 4 notes or more, firmly together', key=K_LAST, font=FONT_BIG, text_color=C_DIM, pad=((20, 0), 0))],
              [sg.Text('', key=K_SUMMARY, font=FONT, size=(150, 1))],
              [note('USB: a chord arrives within a few ms.  Bluetooth: often 10 - 40 ms, gaps in steps of its connection interval.  Second in: how late Bluetooth had each note.')],
              [sg.Multiline('', key=K_LOG, font=('Consolas', 11), expand_x=True, expand_y=True, autoscroll=True, disabled=True, background_color='#111317',
                            text_color='#E6E8EE', size=(150, 18))],
              [sg.Button('Save log…', key=K_SAVE, font=FONT_BTN), sg.Button('Copy', key=K_COPY, font=FONT_BTN), sg.Button('Clear', key=K_CLEAR, font=FONT_BTN),
               sg.Push(), sg.Text('Esc exits  ·  right-click: Edit Me, Version', font=FONT, text_color=C_DIM)]]
    window = sg.Window(APP_TITLE, layout, resizable=True, finalize=True, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT, enable_close_attempted_event=False)
    for key, what in (('<Escape>', 'esc'), ('<Up>', 'up'), ('<Down>', 'down'), ('<Prior>', 'pgup'), ('<Next>', 'pgdn'), ('<Home>', 'home'), ('<End>', 'end')):
        window.bind(key, KT_SCROLL(what))
    return window


def scroll_log(what):
    w = G.window[K_LOG].Widget
    if what == 'up':
        w.yview_scroll(-1, 'units')
    elif what == 'down':
        w.yview_scroll(1, 'units')
    elif what == 'pgup':
        w.yview_scroll(-1, 'pages')
    elif what == 'pgdn':
        w.yview_scroll(1, 'pages')
    elif what == 'home':
        w.yview_moveto(0)
    elif what == 'end':
        w.yview_moveto(1)


def open_out(name):
    if G.out is not None and getattr(G.out, 'name', None) == name:
        return G.out
    close_out()
    if name and name != NONE:
        try:
            G.out = mido.open_output(name)
        except Exception as e:
            log(f'Could not open "{name}": {e}', C_BAD)
    return G.out


def close_out():
    if G.out is not None:
        try:
            G.out.close()
        except Exception:
            pass
    G.out = None


def open_ins(names):
    close_ins()
    for name in names:
        if name and name != NONE and name not in G.ins:
            try:
                G.ins[name] = mido.open_input(name, callback=make_callback(name))
            except Exception as e:
                log(f'Could not open "{name}": {e}', C_BAD)


def close_ins():
    for port in G.ins.values():
        try:
            port.close()
        except Exception:
            pass
    G.ins = {}


def start_out(values, kind):
    if G.tester is not None:
        log('A test is running - Stop it first', C_WARN)
        return
    port = open_out(values[K_OUT])
    if port is None:
        log('Pick the piano under "Piano out" first', C_WARN)
        return
    log(f'--- {time.strftime("%H:%M:%S")}  out: {values[K_OUT]}', C_DIM)
    G.tester = OutTest(port, kind)
    G.tester.start()


def main():
    sg.theme('DarkGrey13')
    sg.set_options(font=FONT, dpi_awareness=True, icon=ICON)
    settings = {k: sg.user_settings_get_entry(f'-{k}-', None) for k in ('out', 'in', 'in2')}
    outs, ins = ports()
    G.window = window = make_window(outs, ins, settings)
    if mido is None:
        log('mido is not installed:  pip install mido python-rtmidi', C_BAD)
    elif not outs and not ins:
        log('No MIDI ports found - is the piano connected (USB cable, or Perfect Bluetooth MIDI running)?  Then tap Refresh.', C_WARN)
    else:
        log('Ports:  out ' + ', '.join(outs) + '   ·   in ' + ', '.join(ins), C_DIM)
    first_in = None
    while True:
        event, values = window.read(timeout=50)
        if event in ('Exit', sg.WINDOW_CLOSED) or event == KT_SCROLL('esc'):
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif isinstance(event, tuple) and event[0] == K_SCROLL:
            scroll_log(event[1])
        elif event == K_REFRESH:
            outs, ins = ports()
            window[K_OUT].update(values=[NONE] + outs, value=values[K_OUT] if values[K_OUT] in outs else (outs[0] if outs else NONE))
            window[K_IN].update(values=[NONE] + ins, value=values[K_IN] if values[K_IN] in ins else (ins[0] if ins else NONE))
            window[K_IN2].update(values=[NONE] + ins, value=values[K_IN2] if values[K_IN2] in ins else NONE)
            log('Ports:  out ' + (', '.join(outs) or 'none') + '   ·   in ' + (', '.join(ins) or 'none'), C_DIM)
        elif event in (K_CHORDS, K_EXTRAS, K_STEADY, K_BIGGER):
            start_out(values, event)
        elif event == K_STOP_OUT:
            if G.tester is not None:
                G.tester.stop_flag = True
        elif event == K_OUT_DONE:
            G.tester = None
        elif event == K_LOGLINE:
            log(*values[K_LOGLINE])
        elif event == K_LISTEN:
            names = [n for n in (values[K_IN], values[K_IN2]) if n and n != NONE]
            if not names:
                log('Pick the piano under "Piano in" first', C_WARN)
                continue
            open_ins(dict.fromkeys(names))
            first_in = values[K_IN]
            G.chord, G.spreads, G.gaps, G.pending2, G.delays = [], [], [], {}, []
            log(f'--- {time.strftime("%H:%M:%S")}  PLAY  in: ' + '  +  '.join(G.ins) + '  -  play chords, 4 notes or more, firmly together', C_HEAD)
            window[K_LAST].update('listening - play chords', text_color=C_DIM)
        elif event == K_STOP_IN:
            if G.chord:
                chord_done()
            if G.delays:
                d = sorted(G.delays)
                log(f'   {len(d)} notes on both inputs: the second had them {d[len(d) // 2]:+.0f} ms later (median), from {d[0]:+.0f} to {d[-1]:+.0f} ms',
                    C_WARN if abs(d[len(d) // 2]) > 15 else C_OK)
            elif G.spreads:
                s_ = sorted(G.spreads)
                log(f'   {len(s_)} chords: median spread {statistics.median(s_):.0f} ms, worst {s_[-1]:.0f} ms', C_OK if s_[-1] <= 10 else C_WARN if s_[-1] <= 30 else C_BAD)
            close_ins()
            window[K_LAST].update('stopped', text_color=C_DIM)
            log('   stopped listening', C_DIM)
        elif event == K_NOTE:
            note_in(*values[K_NOTE], first_in)
        elif event == K_ECHO:
            if values[K_IN] in (NONE, '') or values[K_OUT] in (NONE, ''):
                log('The echo test needs both "Piano out" and "Piano in"', C_WARN)
                continue
            if values[K_IN] not in G.ins:
                open_ins({values[K_IN]: None})
            first_in = values[K_IN]
            G.echo_times, G.echo_lost = [], 0
            start_out(values, K_ECHO)
        elif event == K_ECHO_EV:                                                # from the echo test: a note went out / the test ended
            what, pitch, t = values[K_ECHO_EV]
            if what == 'sent':
                if G.echo is not None:
                    G.echo_lost += 1
                G.echo = (pitch, t)
            else:
                if G.echo is not None:
                    G.echo_lost += 1
                    G.echo = None
                if G.echo_times:
                    e = sorted(G.echo_times)
                    log(f'   came back {len(e)} of {len(e) + G.echo_lost}: round trip {e[len(e) // 2]:.0f} ms (median), {e[0]:.0f} - {e[-1]:.0f} ms', C_OK)
                else:
                    log('   nothing came back - this piano does not send back what it is sent (most do not).  Use the LISTEN tests.', C_WARN)
        elif event == K_SAVE:
            path = sg.popup_get_file('Save the log', save_as=True, default_extension='.txt', file_types=(('Text', '*.txt'),), no_window=True)
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(f'{APP_TITLE}  {time.strftime("%Y-%m-%d %H:%M")}\n' + '\n'.join(G.log_text) + '\n')
                log(f'Saved {path}', C_OK)
        elif event == K_COPY:
            sg.clipboard_set('\n'.join(G.log_text))
            log('Log copied to the clipboard', C_DIM)
        elif event == K_CLEAR:
            G.log_text = []
            window[K_LOG].update('')
        if G.chord and time.perf_counter() - G.chord[-1][0] > CHORD_DONE:      # a chord is complete once it has gone quiet
            chord_done()
        for key, name in (('out', values.get(K_OUT) if values else None), ('in', values.get(K_IN) if values else None), ('in2', values.get(K_IN2) if values else None)):
            if name and settings.get(key) != name:
                settings[key] = name
                sg.user_settings_set_entry(f'-{key}-', name)
    if G.tester is not None:
        G.tester.stop_flag = True
    close_ins()
    close_out()
    window.close()


if __name__ == '__main__':
    main()
