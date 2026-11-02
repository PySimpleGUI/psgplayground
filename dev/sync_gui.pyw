"""
sync_gui.pyw - one-button front end for sync_from_sources.py: copy the apps' working copies into the Playground repo and update README.md's program tables.

    The table shows what a sync WOULD do (computed on start and after every sync; Refresh recomputes):
        new / changed = will be copied (green)    icon = an icon will be written, embed = Toybox button pictures go into playground.py (blue)
        remove = a stray file goes, readme = README.md's program tables will be updated (amber)
        same = up to date (grey)    MISSING = source not found (red)
        EDITED = README.md's program tables were edited by hand since the last sync (red): Sync asks first, and keeps a copy in dev\\readme_copies
    Sync now      does exactly that list;  README only   just updates README.md's program tables from catalog.json
    Open repo     opens the repo folder;   Edit sources opens sync_sources.json in your editor
    GitHub Desktop opens GitHub Desktop with this repo selected, ready to commit
    The log shows what was written (green), what was unchanged (count) and what couldn't be found (red).  Then commit in GitHub Desktop.
    Keys:  Enter = Sync now    F5 = Refresh    Up/Down PgUp/PgDn Home/End scroll the table or log (whichever was clicked)    Esc = close

CHANGE LOG (newest first, 1 line per change):
2026-11-02  v1.7  README.md tables edited by hand show as EDITED (red) and Sync asks before replacing them - a copy goes to dev\\readme_copies either way
2026-11-01  v1.6  README.md is hand-written now - a sync only updates its program tables (wording here: 'update', not 'rebuild')
2026-11-01  v1.5  Repo renamed to psgplayground (GitHub Desktop fallback message)
2026-11-01  v1.4  GitHub Desktop button: opens GitHub Desktop on this repo (its x-github-client:// link; plain launch if that isn't registered)
2026-10-31  v1.3  embed / remove rows in the preview
2026-10-31  v1.2  Preview table of what the sync will do, shown before you press Sync (F5 / Refresh recomputes); table and log in a Pane
2026-10-31  v1.1  Window / launcher icon
2026-10-31  v1.0  First version
"""
import io
import os
import subprocess
import sys
import threading
import traceback
import urllib.parse
from contextlib import redirect_stdout

import PySimpleGUI as sg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sync_from_sources as sync

VERSION = '1.7'
APP_NAME = 'Playground Sync'
ICON = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAkFBMVEUZtGQnnFsh2WMVLksbesUz6YAdXEAA/wAtzXFf/18A//8Af38em/BV/6oSDyEYT4AUGCEAAAATERsSDBow2XctyXAy5n4dmfoYOS8sx24cWDwty3Aeo/4VJiwchdYtxm8WOFYaSDYhd0skiFIrt2cXR3AgbEYaa60YVYcbc7oA/38pqmIsxW1VqlUtynAeZUNRPuT/AAAAMHRSTlMF/g7////7Ac8CAQL/A////gD///3+/v/7e/ur//7/MP/9/f3+//3///8C/0wDlPs54QN+AAACiElEQVR42r2W2XqjMAxGIUubbjO2JcwSm30pSZq8/9uNbKCTACWZm/lv/GF0LGQkyw43enb4XX282cFaHmhMwkWdVpx/DYDDnTPKO8Jzwlcd8MWTnfTcS7Sgp8KTeOIvBnjhCWKh4Y5YjkR8cef1sNphDYLdE2SIyevBcfhZFsAeENRyzw/O88rztGAPqcSEYkikO3EgBICYrAL5NiQglJdbQIDQQZYFmo0ig0yeLRDBjXlQHz0PEb1jHtwgIsD9BABdkLFnRZAbwDIAkYeDcTfUYgmAujcry2PZecLCEMcM5oDOHss804zpoC57AgrpihkAImuQU5p04bOL+UCsaR7JaAwIbb8+u96CoBw2oNQTAAqzXHbzU6BbxDqGEUCPaKZHfzfCAQlgBOic/OtJlpQSO7kwjgFYFE3TMKrzonCPtM1ZICf/YSbPbflQJmrN5lJjsSD+FRD/EfglTImZ0GZq9e/cAGyjdRy3TfP5WaXp1F6noi+jbw9P0KpePhv7EBu1qbpT4grQfi/1exSPSGnyvYJR0OJTDcj6hhDsnebimV2Ke0LF+rqK2YbmVQUTQKyVrxrjR/lVv1k0pGYd1YgZD6JVMRONsk4oSAOlbffIZoG1n4qBUH7cthszXtuP//TazFP0Nhi7xXZsmPghNbp5SDfqe8cUfZ0Qd3KJIm06D8pvKwZzufQ0OowpGyqTJ1qMXnQVd5r2ky4XJ5kIF3vcU0NhD6a3axrKB7Ws/LGWFeHu+eC8va5wdHr9VNGeceBQJz3Roc5s+fwoeht5MjRtl1OjPqE85lmwpIsrMewaO6cbQbLH7XDAzUpucXfq7xnc3jqS8LxfUphcXU7oOnO4f/3pr0h/AAftsix2AjHLAAAAAElFTkSuQmCC'      # 48 px PNG, base64 - also the icon the launcher shows
FONT, FONT_MONO = ('Segoe UI', 11), ('Consolas', 10)
C_OK, C_BAD, C_DIM, C_ICON, C_README = '#2ecc71', '#ff6b6b', '#8a93a3', '#49b4ff', '#e8a33d'
STATUS_COLORS = {'new': C_OK, 'changed': C_OK, 'icon': C_ICON, 'embed': C_ICON, 'remove': C_README, 'readme': C_README, 'same': C_DIM, 'MISSING': C_BAD, 'EDITED': C_BAD}
sg.theme('DarkGrey13')

K_SYNC = '-SYNC-'
K_README = '-README-'
K_OPEN = '-OPEN-'
K_EDIT_SOURCES = '-EDIT SOURCES-'
K_GITHUB_DESKTOP = '-GITHUB DESKTOP-'
K_LOG = '-LOG-'
K_STATUS = '-STATUS-'
K_ESCAPE = '-ESCAPE-'
K_LINE = '-LINE-'
K_DONE = '-DONE-'
K_FAILED = '-FAILED-'
K_REFRESH = '-REFRESH-'
K_PLAN = '-PLAN-'
K_PLAN_FAILED = '-PLAN FAILED-'
K_TABLE = '-TABLE-'
K_PANE = '-PANE-'


def run_sync(window, readme_only):
    """Thread: runs the sync script's main() with --readme when asked, streaming its printed lines to the window"""
    class Stream(io.TextIOBase):                       # print() writes a line in pieces - collect until the newline
        buf = ''

        def write(self, text):
            self.buf += text
            while '\n' in self.buf:
                line, self.buf = self.buf.split('\n', 1)
                if line.strip():
                    window.write_event_value(K_LINE, line)
            return len(text)
    try:
        sys.argv = [sync.__file__] + (['--readme'] if readme_only else [])
        with redirect_stdout(Stream()):
            code = sync.main()
        window.write_event_value(K_DONE, code)
    except Exception:
        window.write_event_value(K_FAILED, traceback.format_exc())


def run_plan(window):
    """Thread: works out what a sync would do and hands the list to the window"""
    try:
        window.write_event_value(K_PLAN, sync.plan(sync.load_catalog()))
    except Exception:
        window.write_event_value(K_PLAN_FAILED, traceback.format_exc())


def show_plan(window, steps):
    """Fill the preview table; returns the one-line summary"""
    rows = [[st['status'], st['rel'], st['src'] if st['status'] != 'same' else '', st['note']] for st in steps]
    colors = [(i, STATUS_COLORS.get(st['status'], sg.theme_text_color()), window[K_TABLE].BackgroundColor) for i, st in enumerate(steps)]      # coloured text, normal background
    window[K_TABLE].update(values=rows, row_colors=colors)
    counts = {k: sum(1 for st in steps if st['status'] == k) for k in STATUS_COLORS}
    todo = counts['new'] + counts['changed']
    parts = [f'{todo} file(s) to copy'] + ([f'{counts["icon"]} icon(s) to write'] if counts['icon'] else []) + (['button pictures to embed'] if counts['embed'] else []) \
        + ([f'{counts["remove"]} file(s) to remove'] if counts['remove'] else []) + (['README.md tables to update'] if counts['readme'] else []) \
        + (['README.md tables EDITED BY HAND'] if counts['EDITED'] else []) + [f'{counts["same"]} up to date']
    if counts['MISSING']:
        parts.append(f'{counts["MISSING"]} MISSING')
    return ',  '.join(parts), counts['MISSING'] > 0 or counts['EDITED'] > 0


def open_github_desktop(repo):
    """ GitHub Desktop with this repo selected - the same x-github-client:// link its 'github' command uses.  Falls back to just starting it.  Returns a line for the log """
    if sys.platform != 'win32':
        return 'GitHub Desktop button is Windows only'
    try:
        os.startfile('x-github-client://openLocalRepo/' + urllib.parse.quote(repo, safe=''))
        return 'Opened GitHub Desktop on ' + repo
    except OSError:
        exe = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GitHubDesktop', 'GitHubDesktop.exe')
        if os.path.isfile(exe):
            subprocess.Popen([exe])
            return 'Started GitHub Desktop (pick the psgplayground repo)'
        return 'GitHub Desktop not found - is it installed?'


def make_window():
    sash = sg.user_settings_get_entry('-sash-', 330)
    table = sg.Table([], headings=['Status', 'File in repo', 'From', 'Note'], key=K_TABLE, col_widths=[9, 42, 62, 36], auto_size_columns=False, justification='left',
                     font=FONT_MONO, num_rows=14, expand_x=True, expand_y=True, enable_events=False, select_mode=sg.TABLE_SELECT_MODE_BROWSE, vertical_scroll_only=False)
    log = sg.Multiline('', key=K_LOG, size=(110, 10), font=FONT_MONO, disabled=True, autoscroll=True, expand_x=True, expand_y=True)
    layout = [[sg.Text('PySimpleGUI Playground', font=('Segoe UI', 14, 'bold'), text_color='#1e9bff'), sg.Text(f'sync v{VERSION}', text_color=C_DIM), sg.Push(),
               sg.Text(sync.ROOT, text_color=C_DIM, font=('Segoe UI', 10))],
              [sg.Button('Sync now', key=K_SYNC, button_color=('white', '#2a62a8')), sg.Button('Refresh', key=K_REFRESH), sg.Button('README only', key=K_README),
               sg.Button('Open repo', key=K_OPEN), sg.Button('Edit sources', key=K_EDIT_SOURCES), sg.Button('GitHub Desktop', key=K_GITHUB_DESKTOP),
               sg.Push(), sg.Text('Enter = sync   F5 = refresh   Esc = close', text_color=C_DIM, font=('Segoe UI', 9))],
              [sg.Text('What Sync now will do', font=('Segoe UI', 10, 'bold')), sg.Text('', key=K_STATUS, expand_x=True)],
              [sg.Pane([sg.Column([[table]], expand_x=True, expand_y=True, pad=0), sg.Column([[log]], expand_x=True, expand_y=True, pad=0)], key=K_PANE, orientation='v',
                       expand_x=True, expand_y=True, show_handle=True, relief=sg.RELIEF_FLAT, border_width=0)]]
    window = sg.Window(APP_NAME, layout, font=FONT, finalize=True, resizable=True, auto_save_location=True, icon=ICON, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT)
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Return>', K_SYNC)
    window.bind('<F5>', K_REFRESH)
    pane = window[K_PANE].PanedWindow
    pane.configure(sashwidth=8, sashrelief=sg.RELIEF_RAISED, bg='#c9852f', sashcursor='sb_v_double_arrow', showhandle=True, handlesize=14, bd=0)
    for child in pane.panes():
        pane.paneconfigure(child, stretch='always', minsize=60)
    window.refresh()
    pane.sash_place(0, 0, sash)
    for widget in (window[K_LOG].Widget, window[K_TABLE].Widget):
        widget.bind('<Button-1>', lambda e, w=widget: w.focus_set(), add='+')
        widget.bind('<Home>', lambda e, w=widget: (w.yview_moveto(0), 'break')[1])
        widget.bind('<End>', lambda e, w=widget: (w.yview_moveto(1), 'break')[1])
    text = window[K_LOG].Widget
    for seq, amount, unit in (('<Up>', -1, 'units'), ('<Down>', 1, 'units'), ('<Prior>', -1, 'pages'), ('<Next>', 1, 'pages')):
        text.bind(seq, lambda e, a=amount, u=unit: (text.yview_scroll(a, u), 'break')[1])
    return window


def main():
    sg.user_settings_filename(filename='playground_sync.json')
    window = make_window()
    busy = False
    window[K_STATUS].update('working out what a sync would do…', text_color=C_DIM)
    threading.Thread(target=run_plan, args=(window,), daemon=True).start()
    while True:
        event, values = window.read()
        if event in ('Exit', sg.WINDOW_CLOSED, K_ESCAPE):
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event in (K_SYNC, K_README) and not busy:
            if sync.readme_edited() and sg.popup_yes_no('README.md\'s program tables were edited by hand since the last sync.',
                                                         'A sync replaces them with the tables from catalog.json - your version is copied to dev\\readme_copies first.',
                                                         'Section text belongs in catalog.json, anything else below the PROGRAMS END comment.', '', 'Sync anyway?',
                                                         title=APP_NAME, keep_on_top=True, font=FONT) != 'Yes':
                window[K_LOG].print('Sync cancelled - nothing was changed', text_color=C_README)
                continue
            busy = True
            window[K_LOG].update('')
            window[K_STATUS].update('Working…', text_color=C_DIM)
            for k in (K_SYNC, K_README, K_REFRESH):
                window[k].update(disabled=True)
            threading.Thread(target=run_sync, args=(window, event == K_README), daemon=True).start()
        elif event == K_REFRESH and not busy:
            window[K_STATUS].update('working out what a sync would do…', text_color=C_DIM)
            threading.Thread(target=run_plan, args=(window,), daemon=True).start()
        elif event == K_PLAN:
            summary, missing = show_plan(window, values[event])
            window[K_STATUS].update(summary, text_color=C_BAD if missing else C_OK)
        elif event == K_PLAN_FAILED:
            window[K_STATUS].update('Could not work out the plan', text_color=C_BAD)
            sg.popup_error_with_traceback('Plan failed', values[event])
        elif event == K_LINE:
            line = values[event]
            color = C_OK if line.startswith('   wrote') else C_BAD if line.startswith(('   MISSING', '   WARNING')) else None
            window[K_LOG].print(line, text_color=color)
        elif event in (K_DONE, K_FAILED):
            busy = False
            for k in (K_SYNC, K_README, K_REFRESH):
                window[k].update(disabled=False)
            if event == K_FAILED:
                window[K_STATUS].update('Failed', text_color=C_BAD)
                sg.popup_error_with_traceback('Sync failed', values[event])
            else:
                ok = values[event] == 0
                window[K_LOG].print('Done - nothing missing.  Commit in GitHub Desktop.' if ok else 'Done, but some sources were not found (red lines)', text_color=C_OK if ok else C_BAD)
            threading.Thread(target=run_plan, args=(window,), daemon=True).start()                 # the table now shows what is left (normally: everything up to date)
        elif event == K_OPEN:
            os.startfile(sync.ROOT) if sys.platform == 'win32' else subprocess.Popen(['xdg-open', sync.ROOT])
        elif event == K_EDIT_SOURCES:
            sg.execute_editor(sync.SOURCES)
        elif event == K_GITHUB_DESKTOP:
            window[K_LOG].print(open_github_desktop(sync.ROOT), text_color=C_DIM)
    try:
        sg.user_settings_set_entry('-sash-', window[K_PANE].PanedWindow.sash_coord(0)[1])
    except Exception:
        pass
    window.close()


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
