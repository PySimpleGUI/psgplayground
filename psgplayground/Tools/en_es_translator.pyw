#!/usr/bin/env python3
"""
en_es_translator.pyw  -  English <-> Spanish translator (PySimpleGUI)

Moving text around is the whole point, so there are 3 ways in and 3 ways out:
  CLIPBOARD   Paste / Paste+Translate / Copy / Copy+Swap buttons, "Watch clipboard" mode (anything you copy anywhere gets translated),
              "Auto-copy result" (translation lands on the clipboard the moment it's done)
  DRAG & DROP Drop text or .txt files from ANY application onto either box (psgdnd module, same as the desktop drop-icon program).
              Drag the  grip of either box OUT to another application, or onto the other box (in-app).
  KEYBOARD    Ctrl+Enter translate   Ctrl+Shift+V paste+translate   Ctrl+Shift+C copy result   Ctrl+Shift+S swap   Esc close
              Result box (read-only): Up/Down 1 line, PgUp/PgDn 1 page, Home/End top/bottom

Translation engines, tried in this order (right-click > Settings to configure):
    1. Argos offline translator  - unlimited, no network.  pip install argostranslate  (big: pulls in torch, ~2 GB) then install the en<->es packages
    2. DeepL                     - free API key, 500,000 chars/month, excellent quality.  https://www.deepl.com/pro-api  (deep-translator)
    3. MyMemory                  - no key: 5,000 chars/day;  with your email in Settings: 50,000 chars/day  (deep-translator)
    4. Google public endpoint    - last resort via urllib; rate-limits (HTTP 429) your IP for a while if used heavily
Every translation is cached, so repeats never cost quota.     pip install deep-translator
Drag & drop from other applications:   pip install psgdnd      (PyPI 6.0.4 or the newer GitHub version both work; it brings in tkinterdnd2)
"""
import json
import sys
import threading
import urllib.parse
import urllib.request
import PySimpleGUI as sg

__version__ = '1.3'

# ---------------------------------------------------------------- optional packages ----------------------------------------------------------------
try:
    from deep_translator import MyMemoryTranslator, DeeplTranslator
    HAVE_DEEP = True
except Exception:
    HAVE_DEEP = False

try:
    import argostranslate.translate
    HAVE_ARGOS = True
except Exception:
    HAVE_ARGOS = False

try:
    import tkinter as tk
    from tkinterdnd2 import TkinterDnD, DND_TEXT, COPY
    if not hasattr(tk.BaseWidget, 'drop_target_register'):                       # some tkinterdnd2 versions don't mix DnDWrapper into tkinter widgets; psgdnd needs it
        tk.BaseWidget.__bases__ = (TkinterDnD.DnDWrapper,) + tk.BaseWidget.__bases__
    import psgdnd
    HAVE_DND = True
except Exception:
    HAVE_DND = False

# ---------------------------------------------------------------- keys ----------------------------------------------------------------
K_SRC = '-SRC-'
K_DST = '-DST-'
K_SRC_LABEL = '-SRC LABEL-'
K_DST_LABEL = '-DST LABEL-'
K_DIRECTION = '-DIRECTION-'
K_SWAP = '-SWAP-'
K_TRANSLATE = '-TRANSLATE-'
K_PASTE = '-PASTE-'
K_PASTE_TRANSLATE = '-PASTE TRANSLATE-'
K_CLEAR_SRC = '-CLEAR SRC-'
K_COPY = '-COPY-'
K_COPY_SWAP = '-COPY SWAP-'
K_CLEAR_DST = '-CLEAR DST-'
K_GRIP_SRC = '-GRIP SRC-'
K_GRIP_DST = '-GRIP DST-'
K_AUTO_PASTE = '-AUTO TRANSLATE ON PASTE-'
K_AUTO_COPY = '-AUTO COPY RESULT-'
K_WATCH = '-WATCH CLIPBOARD-'
K_STATUS = '-STATUS-'
K_RESULT = '-RESULT-'                       # thread -> GUI:  (text, detected_lang, error)
K_GRIP_DROPPED = '-GRIP DROPPED-'           # in-app drag:  (from_key, to_key)
K_KEY_TRANSLATE = '-KEY TRANSLATE-'
K_KEY_PASTE = '-KEY PASTE-'
K_KEY_COPY = '-KEY COPY-'
K_KEY_SWAP = '-KEY SWAP-'
K_KEY_ESC = '-KEY ESC-'
K_SET_EMAIL = '-SET MYMEMORY EMAIL-'          # settings window
K_SET_DEEPL = '-SET DEEPL KEY-'
K_SET_USE_ARGOS = '-SET USE ARGOS-'
K_SET_USE_GOOGLE = '-SET USE GOOGLE-'
K_SET_USE_CACHE = '-SET USE CACHE-'
K_SET_WATCH_MAX = '-SET WATCH MAX CHARS-'
K_SET_CLEAR_CACHE = '-SET CLEAR CACHE-'
K_SET_INSTALL_ARGOS = '-SET INSTALL ARGOS-'
SETTING_CACHE = '-cache-'                       # user-settings key holding the translation cache
CACHE_MAX = 1000

# ---------------------------------------------------------------- theme (TokyoDusk, from the dark theme showcase) ----------------------------------------------------------------
tokyo_dusk = {
    "BACKGROUND": '#1a1b26',
    "TEXT": '#c0caf5',
    "INPUT": '#24283b',
    "TEXT_INPUT": '#d5ddf8',
    "SCROLL": '#24283b',
    "BUTTON": ('#1a1b26', '#7aa2f7'),
    "PROGRESS": ('#bb9af7', '#24283b'),
    "BORDER": 1,
    "SLIDER_DEPTH": 0,
    "PROGRESS_DEPTH": 0,
}
sg.theme_add_new('TokyoDusk', tokyo_dusk)
THEME = 'TokyoDusk'
RESULT_BG, RESULT_FG = '#1f2335', '#e0e6ff'                                       # result box: a shade off the input box so it reads as output
GRIP_COLORS = ('#ffffff', '#414868')                                               # drag grip text / background
TRANSLATE_COLORS = ('#1a1b26', '#9ece6a')                                          # green go-button

# ---------------------------------------------------------------- languages & colors ----------------------------------------------------------------
LANGS = {'en': 'English', 'es': 'Spanish'}
LANG_COLOR = {'en': '#7aa2f7', 'es': '#f7768e', 'auto': '#bb9af7'}                # English blue, Spanish red/coral, Auto-detect purple -- the same colour follows the language everywhere
DIR_EN_ES = 'English  →  Spanish'
DIR_ES_EN = 'Spanish  →  English'
DIR_AUTO = 'Auto-detect  →  other language'
DIRECTIONS = (DIR_EN_ES, DIR_ES_EN, DIR_AUTO)
STATUS_OK, STATUS_WORK, STATUS_ERR = '#9ece6a', '#e0af68', '#f7768e'              # green / amber / red on the dark background

GRIP = '⠿  drag'
UA = {'User-Agent': 'Mozilla/5.0'}
MYMEMORY_CODES = {'en': 'en-US', 'es': 'es-ES'}                                     # MyMemory wants region-qualified codes
SPANISH_HINTS = {'el', 'la', 'los', 'las', 'de', 'del', 'que', 'y', 'es', 'en', 'un', 'una', 'por', 'para', 'con', 'no', 'se', 'su', 'al', 'lo', 'como', 'más', 'pero', 'hola', 'gracias', 'usted', 'está', 'son', 'este', 'esta'}


def direction_to_codes(direction, detected=None):
    """Return (source_code, target_code).  For auto-detect, use the detected code (default English) to pick the other language."""
    if direction == DIR_EN_ES:
        return 'en', 'es'
    if direction == DIR_ES_EN:
        return 'es', 'en'
    src = 'es' if detected == 'es' else 'en'
    return src, ('en' if src == 'es' else 'es')


def detect_language(text):
    """Cheap local English/Spanish guess (MyMemory has no auto-detect): Spanish-only characters or a high share of common Spanish words."""
    if any(ch in text for ch in '¿¡ñÑáéíóúÁÉÍÓÚ'):
        return 'es'
    words = [w.strip('.,;:!?"\'()').lower() for w in text.split()]
    hits = sum(1 for w in words if w in SPANISH_HINTS)
    return 'es' if words and hits / len(words) >= 0.2 else 'en'


def translate_google(text, src, dst):
    """Fallback: Google's public endpoint through urllib.  Returns (translation, detected_source_code)."""
    url = 'https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl={}&tl={}&q={}'.format(src, dst, urllib.parse.quote(text))
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    return ''.join(seg[0] for seg in data[0] if seg and seg[0]), (data[2] if len(data) > 2 else src)


def _short_error(e):
    """Turn an exception into one readable line, naming quota problems."""
    msg = str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__
    if '429' in msg or 'too many' in msg.lower() or 'quota' in msg.lower() or 'limit' in msg.lower():
        return 'quota / rate limit (' + msg[:60] + ')'
    return msg[:90]


def translate_text(text, src, dst):
    """Translate text (src/dst are 'en'/'es').  Returns (translation, engine_name).  Tries the engines in order; raises with all failures listed if none work."""
    cache = sg.user_settings_get_entry(SETTING_CACHE, {}) if sg.user_settings_get_entry(K_SET_USE_CACHE, True) else {}
    cache_key = src + '>' + dst + '|' + text
    if cache_key in cache:
        return cache[cache_key], 'cache'
    errors = []
    engines = []
    if HAVE_ARGOS and sg.user_settings_get_entry(K_SET_USE_ARGOS, True):
        engines.append(('Argos (offline)', lambda: argostranslate.translate.translate(text, src, dst)))
    deepl_key = (sg.user_settings_get_entry(K_SET_DEEPL, '') or '').strip()
    if HAVE_DEEP and deepl_key:
        engines.append(('DeepL', lambda: DeeplTranslator(source=src, target=dst, api_key=deepl_key, use_free_api=not deepl_key.endswith(':pro')).translate(text)))
    if HAVE_DEEP:
        email = (sg.user_settings_get_entry(K_SET_EMAIL, '') or '').strip()
        engines.append(('MyMemory', lambda: MyMemoryTranslator(source=MYMEMORY_CODES[src], target=MYMEMORY_CODES[dst], email=email or None).translate(text)))
    if sg.user_settings_get_entry(K_SET_USE_GOOGLE, True):
        engines.append(('Google', lambda: translate_google(text, src, dst)[0]))
    if not engines:
        raise RuntimeError('No translation engine available - pip install deep-translator, or enable one in Settings')
    for name, func in engines:
        try:
            result = func()
            if not result or not str(result).strip():
                raise RuntimeError('empty result')
            result = str(result)
            if result.upper() == text.upper() and src != dst and len(text) > 3:           # MyMemory returns the input unchanged (uppercased) when its quota is gone
                raise RuntimeError('returned the input unchanged - probably out of quota')
            if sg.user_settings_get_entry(K_SET_USE_CACHE, True):
                if len(cache) >= CACHE_MAX:
                    cache = dict(list(cache.items())[CACHE_MAX // 2:])
                cache[cache_key] = result
                sg.user_settings_set_entry(SETTING_CACHE, cache)
            return result, name
        except Exception as e:
            errors.append('{}: {}'.format(name, _short_error(e)))
            print('Translation engine failed -', errors[-1])
    raise RuntimeError('   |   '.join(errors))


def translate_thread(window, text, direction):
    """Background worker so the window never freezes on a slow network."""
    try:
        src, dst = direction_to_codes(direction, detect_language(text) if direction == DIR_AUTO else None)
        result, engine = translate_text(text, src, dst)
        window.write_event_value(K_RESULT, (result, src, dst, engine, None))
    except Exception as e:
        window.write_event_value(K_RESULT, ('', None, None, None, str(e)))


# ---------------------------------------------------------------- window ----------------------------------------------------------------
def make_window():
    sg.theme(THEME)
    font = ('Segoe UI', 11)
    label_font = ('Segoe UI', 12, 'bold')
    box_font = ('Segoe UI', 12)
    tip_grip = 'Drag me and drop on the other box.' + ('\nYou can also drag me into other programs.' if HAVE_DND else '')
    tip_box = 'Type or paste here.  Drag & drop the other box\'s grip onto me.' + ('\nText or .txt files from other programs can be dropped here too.' if HAVE_DND else '\n(pip install psgdnd to drop text from other programs)')

    src_col = [[sg.Text('English', key=K_SRC_LABEL, font=label_font, text_color=LANG_COLOR['en'], expand_x=True), sg.Text(GRIP, key=K_GRIP_SRC, font=font, text_color=GRIP_COLORS[0], background_color=GRIP_COLORS[1], relief=sg.RELIEF_RAISED, pad=(6, 2), tooltip=tip_grip)],
               [sg.Multiline(size=(44, 12), key=K_SRC, font=box_font, expand_x=True, expand_y=True, focus=True, tooltip=tip_box)],
               [sg.Button('Paste', key=K_PASTE, tooltip='Clipboard → this box'), sg.Button('Paste + Translate', key=K_PASTE_TRANSLATE, tooltip='Ctrl+Shift+V'), sg.Push(), sg.Button('Clear', key=K_CLEAR_SRC)]]
    dst_col = [[sg.Text('Spanish', key=K_DST_LABEL, font=label_font, text_color=LANG_COLOR['es'], expand_x=True), sg.Text(GRIP, key=K_GRIP_DST, font=font, text_color=GRIP_COLORS[0], background_color=GRIP_COLORS[1], relief=sg.RELIEF_RAISED, pad=(6, 2), tooltip=tip_grip)],
               [sg.Multiline(size=(44, 12), key=K_DST, font=box_font, expand_x=True, expand_y=True, disabled=True, background_color=RESULT_BG, text_color=RESULT_FG, tooltip='Translation appears here (read-only).  Drag my grip onto the left box to translate it back.')],
               [sg.Button('Copy', key=K_COPY, tooltip='Result → clipboard   (Ctrl+Shift+C)'), sg.Button('Copy + Use as Input', key=K_COPY_SWAP, tooltip='Copy result, swap languages, and put it in the input box'), sg.Push(), sg.Button('Clear', key=K_CLEAR_DST)]]
    mid_col = [[sg.VPush()], [sg.Button('⇄  Swap', key=K_SWAP, size=(10, 1), tooltip='Swap languages (Ctrl+Shift+S)')], [sg.Button('Translate', key=K_TRANSLATE, size=(10, 2), font=label_font, button_color=TRANSLATE_COLORS, bind_return_key=False, tooltip='Ctrl+Enter')], [sg.VPush()]]

    layout = [[sg.Text('Direction:', font=font), sg.Combo(DIRECTIONS, default_value=DIR_EN_ES, key=K_DIRECTION, readonly=True, enable_events=True, font=font, size=(32, 1), setting=DIR_EN_ES),
               sg.Push(), sg.Checkbox('Auto-translate on paste', key=K_AUTO_PASTE, default=True, setting=True, font=font), sg.Checkbox('Auto-copy result', key=K_AUTO_COPY, default=False, setting=False, font=font),
               sg.Checkbox('Watch clipboard', key=K_WATCH, default=False, setting=False, enable_events=True, font=font, tooltip='Translate anything you copy in any program')],
              [sg.Column(src_col, expand_x=True, expand_y=True), sg.Column(mid_col, expand_y=True, element_justification='c'), sg.Column(dst_col, expand_x=True, expand_y=True)],
              [sg.Text('Ready', key=K_STATUS, font=font, text_color=STATUS_OK, expand_x=True), sg.Sizegrip()]]

    window = sg.Window('English ↔ Spanish Translator', layout, resizable=True, finalize=True, enable_close_attempted_event=True, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_SETTINGS_EXIT, margins=(8, 8))
    window.set_min_size((760, 380))
    # keyboard shortcuts
    window.bind('<Control-Return>', K_KEY_TRANSLATE)
    window.bind('<Control-Shift-V>', K_KEY_PASTE)
    window.bind('<Control-Shift-C>', K_KEY_COPY)
    window.bind('<Control-Shift-S>', K_KEY_SWAP)
    window.bind('<Escape>', K_KEY_ESC)
    for seq, what in (('<Up>', 'up'), ('<Down>', 'down'), ('<Prior>', 'pgup'), ('<Next>', 'pgdn'), ('<Home>', 'home'), ('<End>', 'end')):
        window[K_DST].Widget.bind(seq, lambda e, w=what: (scroll_result(window, w), 'break')[1])      # result box is read-only, so arrows/paging scroll it directly
    setup_inapp_drag(window)
    setup_external_dnd(window)
    return window


def scroll_result(window, what):
    w = window[K_DST].Widget
    if what == 'up': w.yview_scroll(-1, 'units')
    elif what == 'down': w.yview_scroll(1, 'units')
    elif what == 'pgup': w.yview_scroll(-1, 'pages')
    elif what == 'pgdn': w.yview_scroll(1, 'pages')
    elif what == 'home': w.yview_moveto(0)
    elif what == 'end': w.yview_moveto(1)


# ---------------------------------------------------------------- drag & drop ----------------------------------------------------------------
def setup_inapp_drag(window):
    """Pure-tkinter drag: press on a grip, release over the other Multiline.  Works everywhere, no packages."""
    boxes = {window[K_SRC].Widget: K_SRC, window[K_DST].Widget: K_DST}

    def press(event, from_key):
        event.widget.configure(cursor='hand2')

    def release(event, from_key):
        event.widget.configure(cursor='')
        target = window.TKroot.winfo_containing(event.x_root, event.y_root)
        to_key = boxes.get(target)
        if to_key and to_key != from_key:
            window.write_event_value(K_GRIP_DROPPED, (from_key, to_key))

    for grip_key, box_key in ((K_GRIP_SRC, K_SRC), (K_GRIP_DST, K_DST)):
        w = window[grip_key].Widget
        w.configure(cursor='hand2')
        w.bind('<ButtonPress-1>', lambda e, k=box_key: press(e, k))
        w.bind('<ButtonRelease-1>', lambda e, k=box_key: release(e, k))


def setup_external_dnd(window):
    """psgdnd (optional): drop text/files from other apps onto either box.  Drop events arrive through window.read() as psgdnd.DropEvent objects.
    The grips are also registered (plain tkinterdnd2) as drag SOURCES so a translation can be dragged out into another application."""
    if not HAVE_DND:
        return
    try:
        if hasattr(psgdnd, 'register_element_dnd'):                                 # PyPI 6.0.x API
            for key in (K_SRC, K_DST):
                psgdnd.register_element_dnd(window[key], window, psgdnd.DROP_TYPE_ALL)
        else:                                                                       # newer GitHub API:  psgdnd.enable(window, rules={...})
            psgdnd.enable(window, rules={K_SRC: psgdnd.Rule(), K_DST: psgdnd.Rule()})
    except Exception as e:
        print('External drag & drop not available:', e)
    try:
        for grip_key, box_key in ((K_GRIP_SRC, K_SRC), (K_GRIP_DST, K_DST)):
            w = window[grip_key].Widget
            w.drag_source_register(1, DND_TEXT)
            w.dnd_bind('<<DragInitCmd>>', lambda e, k=box_key: (COPY, DND_TEXT, window[k].get()))
    except Exception as e:
        print('Drag-out of grips not available:', e)


def dropped_text(drop_event, data):
    """Turn a psgdnd drop into text: dropped files are read (comma-separated paths from psgdnd), dropped text is used as-is."""
    if drop_event.drop_type == psgdnd.DROP_TYPE_FILES:
        chunks = []
        for path in data.split(','):
            try:
                chunks.append(open(path.strip(), encoding='utf-8', errors='replace').read())
            except Exception:
                chunks.append(path.strip())                                         # unreadable / binary file: just show its name
        return '\n'.join(chunks)
    return str(data)


# ---------------------------------------------------------------- helpers ----------------------------------------------------------------
def set_status(window, text, color=STATUS_OK):
    window[K_STATUS].update(text, text_color=color)


def set_labels(window, direction, detected=None):
    if direction == DIR_AUTO and detected is None:
        window[K_SRC_LABEL].update('Auto-detect', text_color=LANG_COLOR['auto'])
        window[K_DST_LABEL].update('Translation', text_color=LANG_COLOR['auto'])
        return
    src, dst = direction_to_codes(direction, detected)
    window[K_SRC_LABEL].update(LANGS[src] + (' (detected)' if direction == DIR_AUTO else ''), text_color=LANG_COLOR[src])
    window[K_DST_LABEL].update(LANGS[dst], text_color=LANG_COLOR[dst])


def swap_languages(window, direction):
    new_dir = DIR_ES_EN if direction == DIR_EN_ES else DIR_EN_ES if direction == DIR_ES_EN else DIR_AUTO
    window[K_DIRECTION].update(new_dir)
    set_labels(window, new_dir)
    return new_dir


def start_translate(window, text, direction, busy):
    text = text.strip()
    if not text:
        set_status(window, 'Nothing to translate', STATUS_ERR)
        return False
    if busy:
        set_status(window, 'Still translating previous text...', STATUS_WORK)
        return False
    set_status(window, 'Translating...', STATUS_WORK)
    window[K_TRANSLATE].update(disabled=True)
    threading.Thread(target=translate_thread, args=(window, text, direction), daemon=True).start()
    return True


def clipboard_text():
    try:
        return sg.clipboard_get() or ''
    except Exception:
        return ''


# ---------------------------------------------------------------- settings window ----------------------------------------------------------------
def settings_window():
    """Engine configuration.  Everything is stored with the setting= mechanism, read live by translate_text, so no restart needed."""
    font = ('Segoe UI', 11)
    engines = 'Engines available now:   Argos offline: {}    DeepL / MyMemory (deep-translator): {}'.format('YES' if HAVE_ARGOS else 'no', 'YES' if HAVE_DEEP else 'no - pip install deep-translator')
    cache_size = len(sg.user_settings_get_entry(SETTING_CACHE, {}))
    layout = [[sg.Text('Translation engine settings', font=('Segoe UI', 13, 'bold'))],
              [sg.Text(engines, font=font, text_color=STATUS_WORK)],
              [sg.Text('MyMemory email (raises free quota 5,000 \u2192 50,000 chars/day):', font=font)],
              [sg.Input(setting='', key=K_SET_EMAIL, size=(50, 1), font=font, placeholder='you@example.com')],
              [sg.Text('DeepL API key (free plan = 500,000 chars/month; add  :pro  after a paid key):', font=font)],
              [sg.Input(setting='', key=K_SET_DEEPL, size=(50, 1), font=font, placeholder='xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx:fx')],
              [sg.Checkbox('Use Argos offline translator first (if installed)', setting=True, key=K_SET_USE_ARGOS, font=font)],
              [sg.Checkbox('Allow Google public endpoint as last resort (can get your IP rate-limited)', setting=True, key=K_SET_USE_GOOGLE, font=font)],
              [sg.Checkbox('Cache translations (repeats cost no quota)   -   {} cached'.format(cache_size), setting=True, key=K_SET_USE_CACHE, font=font), sg.Button('Clear cache', key=K_SET_CLEAR_CACHE, font=font)],
              [sg.Text('Watch-clipboard: ignore copied text longer than', font=font), sg.Input(setting='1000', key=K_SET_WATCH_MAX, size=(6, 1), font=font, justification='r'), sg.Text('characters (protects your quota)', font=font)],
              [sg.Button('How to install the offline translator', key=K_SET_INSTALL_ARGOS, font=font), sg.Push(), sg.Button('Save', font=font, bind_return_key=True), sg.Button('Cancel', font=font)]]
    window = sg.Window('Settings', layout, modal=True, keep_on_top=True, finalize=True, margins=(10, 10))
    window.bind('<Escape>', 'Cancel')
    while True:
        event, values = window.read()
        if event in (sg.WINDOW_CLOSED, 'Cancel'):
            break
        if event == 'Save':
            window.settings_save(values)
            break
        if event == K_SET_CLEAR_CACHE:
            sg.user_settings_set_entry(SETTING_CACHE, {})
            sg.popup_quick_message('Cache cleared', keep_on_top=True, background_color=STATUS_OK, text_color='black')
        elif event == K_SET_INSTALL_ARGOS:
            sg.popup_scrolled('Offline, unlimited English<->Spanish translation (no quotas, no network after setup).  It is a big install because it pulls in PyTorch (~2 GB):',
                              '    python -m pip install argostranslate',
                              'Then run this once in Python to download the two language packages (~100 MB each):',
                              '    import argostranslate.package as p; p.update_package_index()',
                              "    for pk in p.get_available_packages():\n        if {pk.from_code, pk.to_code} == {'en', 'es'}: p.install_from_path(pk.download())",
                              'Restart this program and the status line will show "Argos (offline)" as the engine.', title='Offline translator', size=(100, 14), keep_on_top=True, font=('Consolas', 10))
    window.close()


# ---------------------------------------------------------------- main ----------------------------------------------------------------
def main():
    sg.user_settings_filename(filename='en_es_translator.json')
    window = make_window()
    direction = window[K_DIRECTION].get()
    set_labels(window, direction)
    busy = False
    last_clip = clipboard_text()
    engines = [n for n, ok in (('Argos offline', HAVE_ARGOS), ('DeepL', HAVE_DEEP and sg.user_settings_get_entry(K_SET_DEEPL, '')), ('MyMemory', HAVE_DEEP), ('Google', sg.user_settings_get_entry(K_SET_USE_GOOGLE, True))) if ok]
    set_status(window, 'Ready.   Ctrl+Enter = translate   |   Engines: ' + (' > '.join(engines) or 'NONE - pip install deep-translator') + '   |   Drop from other apps: ' + ('ON' if HAVE_DND else 'off  (pip install psgdnd)'))

    while True:
        event, values = window.read(timeout=800 if values_watch(window) else None)
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        if event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            window.settings_save(values)
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == 'Settings':
            settings_window()
        elif event == sg.TIMEOUT_EVENT:                                            # clipboard watcher
            clip = clipboard_text()
            if clip != last_clip and clip.strip() and clip != window[K_DST].get() and clip != window[K_SRC].get():
                last_clip = clip
                try:
                    watch_max = int(sg.user_settings_get_entry(K_SET_WATCH_MAX, '1000'))
                except Exception:
                    watch_max = 1000
                if len(clip) > watch_max:
                    set_status(window, 'Clipboard text ignored: {} characters is over the watch limit of {} (see Settings)'.format(len(clip), watch_max), STATUS_WORK)
                else:
                    window[K_SRC].update(clip)
                    if start_translate(window, clip, direction, busy):
                        busy = True
        elif event in (K_KEY_ESC,):
            window.settings_save(values)
            break
        elif event == K_DIRECTION:
            direction = values[K_DIRECTION]
            set_labels(window, direction)
        elif event in (K_SWAP, K_KEY_SWAP):
            direction = swap_languages(window, direction)
        elif event in (K_TRANSLATE, K_KEY_TRANSLATE):
            if start_translate(window, values[K_SRC], direction, busy):
                busy = True
        elif event in (K_PASTE, K_PASTE_TRANSLATE, K_KEY_PASTE):
            clip = clipboard_text()
            last_clip = clip
            window[K_SRC].update(clip)
            if event != K_PASTE or values[K_AUTO_PASTE]:
                if start_translate(window, clip, direction, busy):
                    busy = True
            else:
                set_status(window, 'Pasted {} characters'.format(len(clip)))
        elif event in (K_COPY, K_KEY_COPY):
            result = window[K_DST].get()
            if result:
                sg.clipboard_set(result)
                last_clip = result
                set_status(window, 'Result copied to clipboard ({} characters)'.format(len(result)))
            else:
                set_status(window, 'Nothing to copy', STATUS_ERR)
        elif event == K_COPY_SWAP:
            result = window[K_DST].get()
            if result:
                sg.clipboard_set(result)
                last_clip = result
                direction = swap_languages(window, direction)
                window[K_SRC].update(result)
                window[K_DST].update('')
                set_status(window, 'Copied, swapped languages, and moved result to the input box')
        elif event == K_CLEAR_SRC:
            window[K_SRC].update('')
            window[K_SRC].set_focus()
        elif event == K_CLEAR_DST:
            window[K_DST].update('')
        elif event == K_GRIP_DROPPED:                                              # in-app drag of one box onto the other
            from_key, to_key = values[K_GRIP_DROPPED]
            text = window[from_key].get()
            if not text.strip():
                set_status(window, 'That box is empty', STATUS_ERR)
            elif to_key == K_SRC:                                                   # result dragged back to input: swap languages & translate back
                direction = swap_languages(window, direction)
                window[K_SRC].update(text)
                if start_translate(window, text, direction, busy):
                    busy = True
            else:                                                                   # input dragged onto result box: just translate
                if start_translate(window, text, direction, busy):
                    busy = True
        elif HAVE_DND and psgdnd.is_drop_event(event):                             # text / file dropped from another application (psgdnd)
            text = dropped_text(event, values[event])
            if event.key == K_DST:                                                  # dropped on the RIGHT box: treat it as that language, translate back the other way
                direction = swap_languages(window, direction)
            window[K_SRC].update(text)
            if start_translate(window, text, direction, busy):
                busy = True
        elif event == K_RESULT:
            busy = False
            window[K_TRANSLATE].update(disabled=False)
            result, src, dst, engine, err = values[K_RESULT]
            if err:
                window[K_DST].update('')
                set_status(window, 'Translation failed - ' + err + '   (right-click > Settings for more engines)', STATUS_ERR)
            else:
                window[K_DST].update(result)
                set_labels(window, direction, src)
                msg = 'Translated {} → {}   via {}'.format(LANGS[src], LANGS[dst], engine)
                if values[K_AUTO_COPY]:
                    sg.clipboard_set(result)
                    last_clip = result
                    msg += '   (copied to clipboard)'
                set_status(window, msg)
    window.close()


def values_watch(window):
    try:
        return window[K_WATCH].get()
    except Exception:
        return False


if __name__ == '__main__':
    main()
