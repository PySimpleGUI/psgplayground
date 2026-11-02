#!/usr/bin/env python3
"""
claude_chat_search.pyw - Full-text search of all your Claude chats, using Claude's own data export.

    Get your data:  claude.ai -> Settings -> Privacy -> Export data.  The email links to a small manifest-....json - save it into your Downloads folder.
    The program sees the manifest, opens its download links in your browser, and loads the export ZIPs as soon as they land.
    The newest export in the folder is used (or pick a folder / ZIP at the bottom of the window).
    Searches every message, every tool step (commands, file paths, program output) and every attached file - across all Projects.

    Search:  every word must appear somewhere in the chat, in any order.   "quoted words" must appear exactly as typed.
    Keys:    Enter = search / open chat    Up Down PgUp PgDn Home End = move through results    Ctrl+F = search box    F5 = reload    Esc = exit

CHANGE LOG (newest first, 1 line per change):
2026-10-31  v1.4  Finished exports are moved out of Downloads into an archive folder (one dated subfolder each; the newest 3 kept) and loaded from there
2026-10-31  v1.4  Archive… button picks that folder - put it in Dropbox and the other PCs can search the same export
2026-10-31  v1.3  "New export…" button: opens claude.ai's Privacy settings page in the browser and shows the 3 steps to get a fresh export
2026-10-30  v1.2  Amber sash (Pane) between the results and the preview - drag it to resize the two areas; position remembered
2026-10-30  v1.1  New export format: a manifest-....json lists the ZIPs - their links open in the browser (once per export, or Download export button)
2026-10-30  v1.1  Reads conversations-000.zip / projects-000.zip (one JSON per project) / light_metadata; browser repeat names like "conversations-000 (1).zip"
2026-10-30  v1.1  Watches the export folder - a new export (or the last of its ZIPs) is loaded by itself, no F5 needed
2026-10-30  v1.0  First version: loads newest export (ZIP, folder, batch ZIPs), AND + "phrase" search, highlighted snippets, filters, open / copy chat link
"""
import datetime
import json
import os
import re
import shutil
import threading
import time
import traceback
import webbrowser
import zipfile

import PySimpleGUI as sg

VERSION = '1.4'                     # bump with every change, alongside the CHANGE LOG
APP_NAME = 'Claude Chat Search'
SETTINGS_FILE = 'claude_chat_search.json'
DEFAULT_SOURCE = os.path.join(os.path.expanduser('~'), 'Downloads')
CHAT_URL = 'https://claude.ai/chat/{}'
PROJECT_URL = 'https://claude.ai/project/{}'
EXPORT_PAGE = 'https://claude.ai/settings/privacy'
KEEP_EXPORTS = 3                    # archived exports kept; older ones are deleted when a new one is archived
MAX_ROWS = 500                      # most result rows shown in the table
MAX_PREVIEW_PARTS = 150             # most messages / tool steps shown in the preview
MAX_SNIPPETS_PER_PART = 6           # most snippets shown from one message
CONTEXT = 110                       # characters shown either side of a match
BROWSE_PARTS, BROWSE_CHARS, BROWSE_LINES = 60, 700, 12     # how much of a chat is shown when there's nothing searched
PAGE = 10                           # rows moved by PgUp / PgDn
DAYS = {'Any time': 0, 'Last 7 days': 7, 'Last 30 days': 30, 'Last 90 days': 90, 'Last year': 365}
SORTS = ('Newest first', 'Most matches')
ALL_PROJECTS, NO_PROJECT = 'All projects', '(no project)'
SKIP_CATEGORIES = {'memories', 'feedback'}      # export parts this program doesn't use - their links aren't opened
LINK_HOURS = 24                     # export download links stop working this many hours after the export is made
OPEN_GAP = 1.5                      # seconds between opening download links, so the browser takes each one
WATCH_EVERY = 3.0                   # seconds between checks of the export folder for a new export

ICON = b'iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAAkFBMVEWRZysYFxZBMBxizvxuUCXOiC81WGlVsuC4ciXgrFOfsp3GhjBKk7e+hzXxfQiqqlXHhC7/qlXEgi1CeJH//wB/fwCFvMVidG6qVVWymRmgwbD/AADLfyT/f38sO0C9fyuglmqGy9r/AP/TfRkaGRYhHRgAAADpozzalDYuJhrjlzRbyP1bQiDDgi71rEDIgy434xxQAAAAMHRSTlP+//v+/fX//xH//i3//w8DlANM/gEC//0DCf8BZQL/Rv//Acz//gD///7+/vt7/6sRqH4dAAACnUlEQVR42pWWh3brIAyGhUGeqZs0abpv78AYTOK8/9tdAc7yPP3PybL1RWhYAMppl6pFbZ79B7i3Uqm0OM7qqVDq8QykKl2jbuaF61RtAvCqCmwQhDhMSwA0+OQIUF9kr8HIBVUC8ZNWBbvyDbWgCwuSMkIsdl+QqnUD0l2QE4adh0qK5qRK+EgRjaykvN67X0p1/QKYUgypBm8vpRmTvxMIcnEk4NgI+l5JA3pMEJ2JSkZ67YGDc2d0W49LdATZ4OkMSIl1MwHUnQ/n4Qoc/K12IHcRhoCR4G7BUJou4zjQtMAku5dkgoCHKQ86GmYV5oApzQDDMswCyH60JB90Xy7o9uEnac3aybT26pZR0bL3P5zz99+hAUfTeqkALb7JbacVC/08jOFGpt5bbi2nl+UJ8w1920uuojUNgoswJ/t9Rso5EYPmM/q++eqM7PNQuJfE8phVd0DnIoimkA9g39QUWQYs5jbpe6AG1zfd0Na09szZ04SQJrGW9QDHRBCs4UAzLbGJn2z+oV5xHvcBWhYTbXgkXYkTl5owLSYAeqPcUjH8fDIJt7+k6QYT/RgFHqgNTFdV+tMt8wPUSBc0Gy6JUptBdYbJyMbMzzFGad3KagiwGq5ji1wQ4VzEtKAkHgMO4mYwurCpwqtV4pojIW+mH4PL7HW+BoJ6yWFUB0rTAJB347hyi3HNl2xj17LUHQOgN7cljZk4psh9BogwHSDGgYtHKqkn7Iufrd8apoCwx7iPQPD80+0PeE7+3A4XiLxUsKEtSywCgcj//S3heVcgRot7YmXYNsdCvQLtpE+IQi7qALRhPbqNfUNEAyIy0aRMJEDjMWzsSr2p8oSNnlWDdBBIz4cTOnUUx/VpTsfbw4lSz+Xy8ecjHJH+A4ICH9AkRepeAAAAAElFTkSuQmCC'

carbon_molasses = {"BACKGROUND": '#121110', "TEXT": '#d0c7b8', "INPUT": '#1f1c18', "TEXT_INPUT": '#e0dbcf', "SCROLL": '#1f1c18', "BUTTON": ('#f5ecd8', '#6b4a1e'),
                   "PROGRESS": ('#6b4a1e', '#1f1c18'), "BORDER": 1, "SLIDER_DEPTH": 0, "PROGRESS_DEPTH": 0}
sg.theme_add_new('CarbonMolasses', carbon_molasses)
sg.theme('CarbonMolasses')

FONT, FONT_BOLD, FONT_BIG, FONT_SMALL = ('Segoe UI', 11), ('Segoe UI', 11, 'bold'), ('Segoe UI', 13), ('Segoe UI', 10)
FONT_TITLE, FONT_MONO = ('Segoe UI', 14, 'bold'), ('Consolas', 10)

# Colors - each kind of text has one color, used the same way in the legend and the preview (always next to a text label)
C_TITLE, C_META, C_LINK, C_BODY, C_DIM, C_PREVIEW_BG = '#e8a33d', '#9c9385', '#6fb3ff', '#d0c7b8', '#857c70', '#1a1816'
C_HIT_BG, C_HIT_FG = '#ffd54a', '#000000'
KIND_COLOR = {'you': '#5ec8ff', 'claude': '#e8a33d', 'tool': '#c48cff', 'file': '#7bd88f', 'doc': '#7bd88f', 'summary': '#9c9385', 'project': '#9c9385'}
KIND_NAME = {'you': 'You', 'claude': 'Claude', 'tool': 'Tool step', 'file': 'File', 'doc': 'Project doc', 'summary': 'Summary', 'project': 'Project'}

K_QUERY = '-QUERY-'
K_SEARCH = '-SEARCH-'
K_TOOLS = '-TOOLS-'
K_CASE = '-CASE-'
K_DAYS = '-DAYS-'
K_PROJECT = '-PROJECT-'
K_SORT = '-SORT-'
K_RESULTS = '-RESULTS-'
K_PANE = '-PANE-'
K_RESULTS_OPEN = K_RESULTS + '+OPEN'          # Enter or double-click on a result
K_PREVIEW = '-PREVIEW-'
K_OPEN = '-OPEN-'
K_COPY_LINK = '-COPY LINK-'
K_COPY_TITLE = '-COPY TITLE-'
K_SOURCE = '-SOURCE-'
K_RELOAD = '-RELOAD-'
K_DOWNLOAD = '-DOWNLOAD-'
K_NEW_EXPORT = '-NEW EXPORT-'
K_ARCHIVE = '-ARCHIVE-'
K_STATUS = '-STATUS-'
K_EXPORT_INFO = '-EXPORT INFO-'
K_ESCAPE = '-ESCAPE-'
K_FOCUS_SEARCH = '-FOCUS SEARCH-'
K_LOAD_PROGRESS = '-LOAD PROGRESS-'
K_LOAD_DONE = '-LOAD DONE-'
K_LOAD_FAILED = '-LOAD FAILED-'
K_SEARCH_DONE = '-SEARCH DONE-'
K_THREAD_ERROR = '-THREAD ERROR-'


# ------------------------------------------------------------------------------------------------------------------------------------------------
#   Reading Claude's data export
# ------------------------------------------------------------------------------------------------------------------------------------------------

ISO_RE = re.compile(r'(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d)(?::(\d\d))?')
BATCH_RE = re.compile(r'^(.*)-batch-\d+\.zip$', re.IGNORECASE)
MANIFEST_RE = re.compile(r'^manifest-.*\.json$', re.IGNORECASE)
ARCHIVE_RE = re.compile(r'^\d{4}-\d\d-\d\d_\d{4}$')                                   # archive subfolder: 2026-10-30_1354
PART_RE = re.compile(r'^[a-z_]+-\d{3}(?: \(\d+\))?\.zip$', re.IGNORECASE)           # conversations-000.zip, projects-000 (1).zip ...
SKIP_KEYS = {'uuid', 'id', 'type', 'start_timestamp', 'stop_timestamp', 'created_at', 'updated_at', 'signature', 'media_type', 'data', 'sender', 'index',
             'is_error', 'stop_reason', 'truncated', 'flags', 'citations', 'tool_use_id', 'icon_name', 'integration_icon_url', 'integration_name'}


def iso_to_ts(iso):
    """'2026-10-29T22:17:15.82Z' (export times are UTC) -> seconds since the epoch, 0 if missing"""
    m = ISO_RE.match(iso) if isinstance(iso, str) else None
    if not m:
        return 0.0
    try:
        return datetime.datetime(*(int(g or 0) for g in m.groups()), tzinfo=datetime.timezone.utc).timestamp()
    except (ValueError, OverflowError):
        return 0.0


def fmt_ts(ts, with_time=True):
    return time.strftime('%Y-%m-%d %H:%M' if with_time else '%Y-%m-%d', time.localtime(ts)) if ts else ''


def gather_strings(obj, out, depth=0):
    """Collects the readable strings inside a JSON value - skips ids, timestamps and base64 blobs"""
    if isinstance(obj, str):
        if obj.strip() and not (len(obj) > 2000 and ' ' not in obj[:2000] and '\n' not in obj[:2000]):
            out.append(obj)
    elif depth > 40:
        return
    elif isinstance(obj, dict):
        if obj.get('type') != 'base64':
            for k, v in obj.items():
                if k not in SKIP_KEYS:
                    gather_strings(v, out, depth + 1)
    elif isinstance(obj, list):
        for v in obj:
            gather_strings(v, out, depth + 1)


def strings_of(obj):
    out = []
    gather_strings(obj, out)
    return '\n'.join(out)


def message_parts(msg):
    """One chat message -> list of parts (kind, label, time, text).  Kinds: you, claude, tool, file"""
    who = 'you' if msg.get('sender') == 'human' else 'claude'
    ts = iso_to_ts(msg.get('created_at'))
    parts, has_text = [], False
    content = msg.get('content')
    for block in content if isinstance(content, list) else []:
        if not isinstance(block, dict):
            continue
        btype = block.get('type') or ''
        if btype == 'text':
            if isinstance(block.get('text'), str) and block['text'].strip():
                parts.append((who, '', ts, block['text']))
                has_text = True
        elif btype in ('thinking', 'redacted_thinking'):
            continue
        elif btype == 'tool_use':
            parts.append(('tool', str(block.get('name') or 'tool'), ts, strings_of(block.get('input'))))
        elif btype == 'tool_result':
            parts.append(('tool', str(block.get('name') or 'tool') + ' result', ts, strings_of(block.get('content'))))
        else:
            parts.append(('tool', btype or 'item', ts, strings_of(block)))
    if not has_text and isinstance(msg.get('text'), str) and msg['text'].strip():
        parts.append((who, '', ts, msg['text']))
    file_names = set()
    for att in msg.get('attachments') or []:
        if isinstance(att, dict):
            name = str(att.get('file_name') or 'attachment')
            body = att.get('extracted_content') if isinstance(att.get('extracted_content'), str) else ''
            file_names.add(name)
            parts.append(('file', name, ts, name + ('\n' + body if body else '')))
    for key in ('files', 'files_v2'):
        for f in msg.get(key) or []:
            if isinstance(f, dict) and f.get('file_name') and f['file_name'] not in file_names:
                file_names.add(f['file_name'])
                parts.append(('file', str(f['file_name']), ts, str(f['file_name'])))
    return [p for p in parts if p[3]]


class Chat:
    """One searchable item - a chat, or a project's instructions / knowledge doc"""
    __slots__ = ('uuid', 'title', 'project', 'created', 'updated', 'url', 'parts', 'blob', 'blob_tools')

    def __init__(self, uuid, title, project, created, updated, url, parts):
        self.uuid, self.title, self.project, self.created, self.updated, self.url, self.parts = uuid, title, project, created, updated, url, parts
        self.blob = '\n\0\n'.join([title] + [p[3] for p in parts if p[0] != 'tool']).lower()        # lower-case copies for fast matching
        self.blob_tools = '\n\0\n'.join(p[3] for p in parts if p[0] == 'tool').lower()


def conversation_project(conv, project_names, project_of):
    """A chat's project name - from the chat itself, or from the export's light metadata (project_of: chat uuid -> (project uuid, name))"""
    proj = conv.get('project')
    puuid = conv.get('project_uuid') or (proj.get('uuid') if isinstance(proj, dict) else None)
    name = proj.get('name') if isinstance(proj, dict) else None
    if not puuid and conv.get('uuid') in project_of:
        puuid, name = project_of[conv['uuid']]
    if puuid in project_names:
        return project_names[puuid]
    return ' '.join(str(name).split()) if name else ''


def chat_from_conversation(conv, project_names, project_of):
    uuid = str(conv.get('uuid') or '')
    title = ' '.join(str(conv.get('name') or '').split()) or '(untitled)'
    parts = [('summary', '', 0, conv['summary'])] if isinstance(conv.get('summary'), str) and conv['summary'].strip() else []
    for msg in conv.get('chat_messages') or []:
        if isinstance(msg, dict):
            parts.extend(message_parts(msg))
    created = iso_to_ts(conv.get('created_at'))
    return Chat(uuid, title, conversation_project(conv, project_names, project_of), created, iso_to_ts(conv.get('updated_at')) or created, CHAT_URL.format(uuid), parts)


def items_from_project(p):
    """A project's instructions and each of its knowledge docs become searchable items too"""
    puuid = str(p.get('uuid') or '')
    name = ' '.join(str(p.get('name') or '').split()) or '(unnamed project)'
    created = iso_to_ts(p.get('created_at'))
    updated = iso_to_ts(p.get('updated_at')) or created
    items = []
    text = '\n'.join(t for t in (p.get('description'), p.get('prompt_template')) if isinstance(t, str) and t.strip())
    if text:
        items.append(Chat('project:' + puuid, '[project] ' + name, name, created, updated, PROJECT_URL.format(puuid), [('project', 'description & instructions', updated, text)]))
    for d in p.get('docs') or []:
        if isinstance(d, dict):
            fname = str(d.get('filename') or 'doc')
            ts = iso_to_ts(d.get('created_at')) or updated
            content = d['content'] if isinstance(d.get('content'), str) else ''
            doc_id = 'doc:' + str(d.get('uuid') or puuid + fname)
            items.append(Chat(doc_id, '[doc] ' + fname, name, ts, ts, PROJECT_URL.format(puuid), [('doc', fname, ts, fname + '\n' + content)]))
    return items


def zip_has_export(path):
    """True for a Claude export ZIP.  A ChatGPT export also has a conversations.json, but it comes with chat.html"""
    try:
        with zipfile.ZipFile(path) as zf:
            names = {os.path.basename(n) for n in zf.namelist()}
        return 'conversations.json' in names and 'chat.html' not in names
    except (zipfile.BadZipFile, OSError):
        return False


def batch_group(zip_path):
    """An export can arrive split into ...-batch-0000.zip, ...-batch-0001.zip - load all the parts"""
    m = BATCH_RE.match(os.path.basename(zip_path))
    if not m:
        return [zip_path]
    folder = os.path.dirname(zip_path)
    group = [os.path.join(folder, f) for f in os.listdir(folder) if BATCH_RE.match(f) and BATCH_RE.match(f).group(1).lower() == m.group(1).lower()]
    return sorted(group) or [zip_path]


def read_manifest(path):
    """A manifest-....json from Claude's export email -> {'path', 'created', 'files'}, or None if the file isn't one"""
    try:
        with open(path, 'rb') as f:
            m = json.loads(f.read().decode('utf-8-sig'))
        created = iso_to_ts(m.get('created_at')) or os.path.getmtime(path)
    except (OSError, ValueError, AttributeError):
        return None
    files = [d for d in m.get('data_files') or [] if isinstance(d, dict) and d.get('filename') and d.get('export_url')]
    return {'path': path, 'created': created, 'files': files} if files else None


def find_download(folder, names, filename, not_before):
    """The newest complete download of filename in folder, saved after not_before.  Browsers save repeat downloads as 'name (1).zip'"""
    stem, ext = os.path.splitext(filename)
    rx = re.compile(re.escape(stem) + r'(?: \(\d+\))?' + re.escape(ext) + '$', re.IGNORECASE)
    best = None
    for name in names:
        if rx.match(name):
            full = os.path.join(folder, name)
            try:
                mtime = os.path.getmtime(full)
            except OSError:
                continue
            if mtime >= not_before and (best is None or mtime > best[0]) and zipfile.is_zipfile(full):    # is_zipfile is False while downloading
                best = (mtime, full)
    return best[1] if best else None


def manifest_status(m, folder, names):
    """Which of a manifest's files are downloaded -> ({category: [paths]}, [missing file entries]).  Skipped categories are left out"""
    found, missing = {}, []
    for d in m['files']:
        if d.get('category') in SKIP_CATEGORIES:
            continue
        full = find_download(folder, names, d['filename'], m['created'] - 300)
        if full:
            found.setdefault(d.get('category') or d['filename'], []).append(full)
        else:
            missing.append(d)
    return found, missing


def archive_folder():
    """Where finished exports live.  Default: a claude_exports folder next to this program (or in Documents if the program is installed in site-packages)"""
    saved = sg.user_settings_get_entry('-archive-', None)
    if saved:
        return saved
    here = os.path.dirname(os.path.abspath(__file__))
    if 'site-packages' in here.lower() or 'dist-packages' in here.lower():
        return os.path.join(os.path.expanduser('~'), 'Documents', 'claude_exports')
    return os.path.join(here, 'claude_exports')


def archive_finished_exports(inbox):
    """A manifest in the inbox whose files have all arrived is moved, with its ZIPs, into archive/<date-time of the export>/.  Returns the folders made"""
    archive = archive_folder()
    if not os.path.isdir(inbox) or os.path.normcase(os.path.abspath(inbox)) == os.path.normcase(os.path.abspath(archive)):
        return []
    made = []
    try:
        names = os.listdir(inbox)
    except OSError:
        return []
    for name in names:
        if not MANIFEST_RE.match(name):
            continue
        m = read_manifest(os.path.join(inbox, name))
        if not m:
            continue
        found, missing = manifest_status(m, inbox, names)
        if missing or 'conversations' not in found:
            continue
        dest = os.path.join(archive, time.strftime('%Y-%m-%d_%H%M', time.localtime(m['created'])))
        try:
            os.makedirs(dest, exist_ok=True)
            files = [os.path.join(inbox, name)] + [p for ps in found.values() for p in ps]
            for d in m['files']:                                                # files of skipped categories, if they were downloaded anyway
                if d.get('category') in SKIP_CATEGORIES:
                    extra = find_download(inbox, names, d['filename'], m['created'] - 300)
                    if extra:
                        files.append(extra)
            for src in files:
                shutil.move(src, os.path.join(dest, os.path.basename(src)))
            made.append(dest)
        except OSError:
            continue
    if made:
        prune_archive(archive)
    return made


def prune_archive(archive):
    """Keeps the newest KEEP_EXPORTS dated folders"""
    try:
        folders = sorted(f for f in os.listdir(archive) if ARCHIVE_RE.match(f) and os.path.isdir(os.path.join(archive, f)))
    except OSError:
        return
    for f in folders[:-KEEP_EXPORTS]:
        shutil.rmtree(os.path.join(archive, f), ignore_errors=True)


def find_archived_export():
    """The newest complete export in the archive -> the same dict find_newest_export returns, or None"""
    archive = archive_folder()
    try:
        folders = sorted((f for f in os.listdir(archive) if ARCHIVE_RE.match(f) and os.path.isdir(os.path.join(archive, f))), reverse=True)
    except OSError:
        return None
    for f in folders:
        found = find_newest_export(os.path.join(archive, f))
        if found.get('sources') and not found.get('todo'):
            return found
    return None


def find_export(path):
    """Finds the newest Claude export at path - a folder, an export ZIP, a manifest-....json or a conversations.json.
    Returns {'sources': ZIPs / folders to load, 'label', 'when', 'todo': (manifest, missing files) of a newer export still to download, 'sig'}"""
    result = {'sources': [], 'label': '', 'when': 0, 'todo': None}
    path = os.path.expanduser(path.strip().strip('"'))
    try:
        if os.path.isfile(path):
            m = read_manifest(path) if path.lower().endswith('.json') else None
            if m:
                found, missing = manifest_status(m, os.path.dirname(path), os.listdir(os.path.dirname(path)))
                result.update(sources=[p for ps in found.values() for p in ps], label='Export of ' + fmt_ts(m['created']), when=m['created'])
                result['todo'] = (m, missing) if missing else None
            elif path.lower().endswith('.zip'):
                result.update(sources=batch_group(path), label=os.path.basename(path), when=os.path.getmtime(path))
            else:
                result.update(sources=[os.path.dirname(path)], label=os.path.dirname(path), when=os.path.getmtime(path))
        elif os.path.isfile(os.path.join(path, 'conversations.json')):
            result.update(sources=[path], label=os.path.basename(path), when=os.path.getmtime(os.path.join(path, 'conversations.json')))
        elif os.path.isdir(path):
            archive_finished_exports(path)                                  # a complete export in the inbox moves to the archive first
            result.update(find_newest_export(path))
            archived = find_archived_export()
            if archived and archived['when'] > (result.get('when') or 0):
                result.update(sources=archived['sources'], label=archived['label'], when=archived['when'])
                if result['todo'] and result['todo'][0]['created'] <= archived['when']:
                    result['todo'] = None
    except OSError:
        pass
    result['sig'] = (tuple((p, os.path.getmtime(p), os.path.getsize(p)) for p in result['sources'] if os.path.exists(p)),
                     tuple(d['filename'] for d in result['todo'][1]) if result['todo'] else ())
    return result


def find_newest_export(folder):
    """Newest export in a folder: a manifest whose conversations ZIP has been downloaded, or an older-style single export ZIP / unzipped folder"""
    names = os.listdir(folder)
    manifests = sorted((m for m in (read_manifest(os.path.join(folder, n)) for n in names if MANIFEST_RE.match(n)) if m), key=lambda m: m['created'], reverse=True)
    best, todo = None, None                                         # best = (time, sources, label)
    for m in manifests:
        found, missing = manifest_status(m, folder, names)
        if missing and m is manifests[0]:
            todo = (m, missing)
        if 'conversations' in found:
            best = (m['created'], [p for ps in found.values() for p in ps], 'Export of ' + fmt_ts(m['created']))
            break
    older = []
    for name in names:
        full = os.path.join(folder, name)
        try:
            if name.lower().endswith('.zip') and not (manifests and PART_RE.match(name)) and os.path.isfile(full):
                older.append((os.path.getmtime(full), full))
            elif os.path.isfile(os.path.join(full, 'conversations.json')) and not os.path.isfile(os.path.join(full, 'chat.html')):
                older.append((os.path.getmtime(os.path.join(full, 'conversations.json')), full))
        except OSError:
            pass
    for mtime, full in sorted(older, reverse=True):                 # newest first; ZIPs that aren't Claude exports are skipped
        if best and mtime <= best[0]:
            break
        if os.path.isdir(full) or zip_has_export(full):
            best = (mtime, [full] if os.path.isdir(full) else batch_group(full), os.path.basename(full))
            break
    if todo and best and best[0] > todo[0]['created']:              # something newer than that manifest is already here
        todo = None
    return {'sources': best[1], 'label': best[2], 'when': best[0], 'todo': todo} if best else {'todo': todo}


def json_documents(source, progress):
    """Yields every JSON document in an export ZIP (all .json / .jsonl files) or unzipped export folder (conversations.json, projects.json)"""
    def parse(text, name):                                          # text, not bytes: the bytes are freed before parsing (big files)
        if name.lower().endswith('.jsonl'):
            return [json.loads(line) for line in text.splitlines() if line.strip()]
        return json.loads(text)

    if os.path.isdir(source):
        folders = [source] + [os.path.join(source, d) for d in sorted(os.listdir(source)) if os.path.isdir(os.path.join(source, d))]
        for full in (os.path.join(f, n) for f in folders for n in ('projects.json', 'conversations.json')):
            if os.path.isfile(full):
                progress(f'Reading {os.path.basename(full)}  ({os.path.getsize(full) / 1e6:,.1f} MB)…')
                with open(full, 'rb') as f:
                    yield parse(f.read().decode('utf-8-sig'), full)
    else:
        with zipfile.ZipFile(source) as zf:
            for info in zf.infolist():
                if info.filename.lower().endswith(('.json', '.jsonl')):
                    if info.file_size > 1e6:
                        progress(f'Reading {os.path.basename(source)} → {os.path.basename(info.filename)}  ({info.file_size / 1e6:,.1f} MB)…')
                    with zf.open(info) as f:
                        yield parse(f.read().decode('utf-8-sig'), info.filename)


def sort_document(doc, convs, projects, project_of, depth=0):
    """Sorts what an export file holds into conversations, projects and chat -> project links (light metadata)"""
    for item in doc if isinstance(doc, list) else [doc]:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get('chat_messages'), list):
            convs.append(item)
            continue
        if item.get('uuid') and ('prompt_template' in item or isinstance(item.get('docs'), list)):
            projects.append(item)
            continue
        proj = item.get('project')
        puuid = item.get('project_uuid') or (proj.get('uuid') if isinstance(proj, dict) else None)
        if item.get('uuid') and puuid:
            project_of[item['uuid']] = (puuid, proj.get('name') if isinstance(proj, dict) else None)
        if depth < 2:                                               # e.g. {"conversations": [...]}
            for v in item.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    sort_document(v, convs, projects, project_of, depth + 1)


def load_export(path, progress):
    """Loads the newest Claude export at path.  Returns (items, info)"""
    found = find_export(path)
    info = dict(found, path=path, chats=0, newest=0)
    convs, projects, project_of = [], [], {}
    for src in found['sources']:
        progress(f'Reading {os.path.basename(src)}…')
        for doc in json_documents(src, progress):
            sort_document(doc, convs, projects, project_of)
    project_names = {p['uuid']: ' '.join(str(p.get('name') or '').split()) or '(unnamed project)' for p in projects}
    items = {}
    for i, conv in enumerate(convs):
        if i % 250 == 0:
            progress(f'Indexing chats…  {i:,} of {len(convs):,}')
        chat = chat_from_conversation(conv, project_names, project_of)
        old = items.get(chat.uuid)
        if old is None or chat.updated >= old.updated:          # same chat in two files -> keep the newer copy
            items[chat.uuid] = chat
    convs.clear()
    info['chats'] = len(items)
    info['newest'] = max((c.updated for c in items.values()), default=0)
    for p in projects:
        for item in items_from_project(p):
            items[item.uuid] = item
    return list(items.values()), info


# ------------------------------------------------------------------------------------------------------------------------------------------------
#   Searching
# ------------------------------------------------------------------------------------------------------------------------------------------------

def parse_terms(query):
    """'psg_work "copy plan"' -> ['psg_work', 'copy plan']"""
    return [t for t in ((a or b).strip('"') for a, b in re.findall(r'"([^"]+)"|(\S+)', query)) if t.strip()]


def case_sensitive_matches(chat, terms, tools):
    texts = [chat.title] + [p[3] for p in chat.parts if tools or p[0] != 'tool']
    total = 0
    for t in terms:
        count = sum(x.count(t) for x in texts)
        if not count:
            return 0
        total += count
    return total


def search_chats(chats, terms, match_case, tools, days, project, cancelled):
    """Every term must appear somewhere in the chat.  Returns [(chat, number of matches)], or None if a newer search replaced this one"""
    cutoff = time.time() - days * 86400 if days else 0
    lower = [t.lower() for t in terms]
    results = []
    for n, chat in enumerate(chats):
        if n % 500 == 0 and cancelled():
            return None
        if cutoff and chat.updated < cutoff:
            continue
        if (project == NO_PROJECT and chat.project) or (project not in (ALL_PROJECTS, NO_PROJECT) and chat.project != project):
            continue
        if not terms and chat.uuid.startswith(('project:', 'doc:')):             # nothing searched = list of chats only
            continue
        matches = 0
        for t in lower:
            count = chat.blob.count(t) + (chat.blob_tools.count(t) if tools else 0)
            if not count:
                break
            matches += count
        else:
            if match_case and terms:
                matches = case_sensitive_matches(chat, terms, tools)
                if not matches:
                    continue
            results.append((chat, matches))
    return results


def sort_results(results, how):
    if how == SORTS[1]:
        results.sort(key=lambda r: (r[1], r[0].updated), reverse=True)
    else:
        results.sort(key=lambda r: r[0].updated, reverse=True)


def term_regex(terms, match_case):
    if not terms:
        return None
    return re.compile('|'.join(re.escape(t) for t in sorted(terms, key=len, reverse=True)), 0 if match_case else re.IGNORECASE)


def snippet_windows(spans, length):
    """Match spans -> [start, end, [spans]] windows with CONTEXT characters either side; overlapping windows merge"""
    windows = []
    for s, e in spans:
        ws, we = max(0, s - CONTEXT), min(length, e + CONTEXT)
        if windows and ws <= windows[-1][1]:
            windows[-1][1] = max(windows[-1][1], we)
            windows[-1][2].append((s, e))
        else:
            windows.append([ws, we, [(s, e)]])
    return windows


def flat(text):
    """Snippet text on one line - line breaks shown as ↵"""
    text = re.sub(r'\s*\n\s*', ' ↵ ', text.replace('\r\n', '\n').replace('\r', '\n').replace('\t', ' '))
    return re.sub(r' {3,}', '  ', text)


# ------------------------------------------------------------------------------------------------------------------------------------------------
#   Preview pane - writes straight into the Multiline's tk Text widget with color tags
# ------------------------------------------------------------------------------------------------------------------------------------------------

class Preview:
    def __init__(self, element, on_link_click):
        self.t = t = element.Widget
        t.configure(wrap='word', padx=12, pady=8, spacing1=1, spacing3=1, insertwidth=0)
        t.tag_configure('title', foreground=C_TITLE, font=FONT_TITLE)
        t.tag_configure('meta', foreground=C_META, font=FONT_SMALL)
        t.tag_configure('link', foreground=C_LINK, font=FONT_SMALL, underline=True)
        t.tag_configure('time', foreground=C_DIM, font=FONT_SMALL, spacing1=9)
        for kind, color in KIND_COLOR.items():
            t.tag_configure('h_' + kind, foreground=color, font=FONT_BOLD, spacing1=9)
        t.tag_configure('body', foreground=C_BODY, font=FONT, lmargin1=24, lmargin2=24)
        t.tag_configure('mono', foreground=C_BODY, font=FONT_MONO, lmargin1=24, lmargin2=24)
        t.tag_configure('faint', foreground=C_DIM)
        t.tag_configure('hit', background=C_HIT_BG, foreground=C_HIT_FG)
        try:
            t.tag_configure('hit', lmargincolor=C_PREVIEW_BG)          # a match that starts a line doesn't paint the left margin yellow (Tk 8.6.6+)
        except Exception:
            pass
        t.tag_raise('faint')
        t.tag_raise('hit')
        t.tag_bind('link', '<Button-1>', lambda e: on_link_click())
        t.tag_bind('link', '<Enter>', lambda e: t.configure(cursor='hand2'))
        t.tag_bind('link', '<Leave>', lambda e: t.configure(cursor='xterm'))

    def show(self, chat=None, rx=None, tools=True, message=''):
        t = self.t
        t.configure(state='normal')
        t.delete('1.0', 'end')
        if chat is None:
            t.insert('end', message, 'body')
        else:
            t.insert('end', chat.title + '\n', 'title')
            meta = 'Updated ' + fmt_ts(chat.updated)
            if chat.created and fmt_ts(chat.created) != fmt_ts(chat.updated):
                meta += '      Created ' + fmt_ts(chat.created)
            if chat.project:
                meta += '      Project: ' + chat.project
            t.insert('end', meta + '\n', 'meta')
            t.insert('end', chat.url, 'link')
            t.insert('end', '\n')
            t.mark_set('summary', 'end-1c')
            t.mark_gravity('summary', 'left')
            if rx is None:
                self._beginning(chat, tools)
            else:
                self._matches(chat, rx, tools)
        t.configure(state='disabled')
        t.yview_moveto(0)

    def _header(self, kind, label, ts):
        name = KIND_NAME.get(kind, kind) + (' · ' + label if label and kind in ('tool', 'file', 'doc', 'project') else '')
        if ts:
            self.t.insert('end', fmt_ts(ts) + '    ', 'time')
        self.t.insert('end', name + '\n', 'h_' + kind)

    def _matches(self, chat, rx, tools):
        t = self.t
        total = places = shown = 0
        for kind, label, ts, text in chat.parts:
            if kind == 'tool' and not tools:
                continue
            spans = []
            for m in rx.finditer(text):
                spans.append(m.span())
                if len(spans) >= 300:
                    break
            if not spans:
                continue
            total += len(spans)
            places += 1
            if shown >= MAX_PREVIEW_PARTS:
                continue
            shown += 1
            self._header(kind, label, ts)
            body = 'mono' if kind == 'tool' else 'body'
            windows = snippet_windows(spans, len(text))
            for ws, we, hits in windows[:MAX_SNIPPETS_PER_PART]:
                t.insert('end', '…' if ws else '', (body, 'faint'))
                pos = ws
                for s, e in hits:
                    t.insert('end', flat(text[pos:s]), body)
                    t.insert('end', flat(text[s:e]), (body, 'hit'))
                    pos = e
                t.insert('end', flat(text[pos:we]), body)
                t.insert('end', ('…' if we < len(text) else '') + '\n', (body, 'faint'))
            if len(windows) > MAX_SNIPPETS_PER_PART:
                more = sum(len(w[2]) for w in windows[MAX_SNIPPETS_PER_PART:])
                t.insert('end', f'+{more:,} more matches here\n', (body, 'faint'))
        summary = f'{total:,} match{"es" if total != 1 else ""} in {places:,} message{"s" if places != 1 else ""}' if total else 'Only the title matches'
        if shown < places:
            summary += f'  -  showing the first {shown:,}'
        t.insert('summary', summary + '\n', 'meta')

    def _beginning(self, chat, tools):
        t = self.t
        parts = [p for p in chat.parts if tools or p[0] != 'tool']
        for kind, label, ts, text in parts[:BROWSE_PARTS]:
            self._header(kind, label, ts)
            text = text.strip()
            short = '\n'.join(text.splitlines()[:BROWSE_LINES])[:BROWSE_CHARS]
            t.insert('end', short, 'mono' if kind == 'tool' else 'body')
            t.insert('end', ' …\n' if len(short) < len(text) else '\n', ('body', 'faint'))
        if len(parts) > BROWSE_PARTS:
            t.insert('end', f'\n+{len(parts) - BROWSE_PARTS:,} more - open the chat to read it all\n', ('body', 'faint'))
        t.insert('summary', f'{len(parts):,} message{"s" if len(parts) != 1 else ""}' + ('' if tools else '  (tool steps hidden)') + '\n', 'meta')


def no_export_text(path):
    return (f'No Claude export found in:\n      {path}\n\n'
            'To get one:\n'
            '      1.   claude.ai  →  Settings  →  Privacy  →  Export data\n'
            '      2.   Click the link in the email - your browser saves a small manifest-….json file\n'
            '      3.   Make sure it lands in the folder above  (Downloads, unless you changed it)\n'
            '      4.   This program then opens the manifest’s download links and loads the export by itself\n\n'
            'Or point "Export" at the bottom of this window at another folder, ZIP or manifest.')


def links_expired(todo):
    return time.time() > todo[0]['created'] + LINK_HOURS * 3600


def downloading_text(todo):
    m, missing = todo
    if links_expired(todo):
        return (f'The download links of your Claude export from {fmt_ts(m["created"])} have expired.\n\n'
                'Ask for a new one:   claude.ai  →  Settings  →  Privacy  →  Export data,  then click the link in the email.')
    return (f'Your Claude export from {fmt_ts(m["created"])} is downloading - its links were opened in your browser.\n\n'
            'Still to arrive:\n' + ''.join(f'      {d["filename"]}\n' for d in missing) +
            '\nThe chats load by themselves as soon as the files land.\n'
            'If the browser asks whether claude.ai may download multiple files, click Allow.    If a file never arrives, click Download export.')


# ------------------------------------------------------------------------------------------------------------------------------------------------
#   Window
# ------------------------------------------------------------------------------------------------------------------------------------------------

class State:
    def __init__(self):
        self.chats = []                 # everything loaded from the export
        self.results = []               # [(chat, matches)] shown in the table
        self.rx = None                  # regex of the current search words, None when nothing is searched
        self.tools = True
        self.load_id = 0
        self.loaded = False
        self.loaded_path = None
        self.search_gen = 0
        self.search_pending = 0.0       # time of the last keystroke in the search box
        self.source_pending = 0.0       # time the Export path was last edited
        self.shown_chat = None
        self.selected_uuid = None
        self.empty_text = ''
        self.size = None
        self.preview = None
        self.loading = False
        self.newest = 0                 # time of the newest chat loaded
        self.export_sig = None          # what the export looked like when it was loaded
        self.pending_sig = None         # a change seen in the export folder, loaded once it holds still for one more check
        self.last_watch = 0.0
        self.open_queue = []            # download links still to open in the browser
        self.next_open = 0.0
        self.links_opened_at = 0.0


def make_window():
    s = sg.user_settings_get_entry
    legend = [sg.Text(KIND_NAME[k], text_color=KIND_COLOR[k], font=FONT_BOLD, pad=(6, 0)) for k in ('you', 'claude', 'tool', 'file')]
    table = sg.Table([], headings=['Updated', 'Chat', 'Project', 'Matches'], key=K_RESULTS, col_widths=[11, 54, 22, 8], auto_size_columns=False,
                     cols_justification=('l', 'l', 'l', 'r'), num_rows=11, enable_events=True, expand_x=True, expand_y=True, select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                     font=FONT, header_font=FONT_BOLD, background_color='#1f1c18', text_color='#e0dbcf', alternating_row_color='#282420',
                     header_background_color='#6b4a1e', header_text_color='#f5ecd8', selected_row_colors=('#121110', '#e8a33d'))
    preview = sg.Multiline('', key=K_PREVIEW, disabled=True, expand_x=True, expand_y=True, size=(100, 17), font=FONT, background_color=C_PREVIEW_BG, text_color=C_BODY,
                           border_width=0)
    top_pane = sg.Column([[table]], expand_x=True, expand_y=True, pad=(0, 0))
    bottom_pane = sg.Column([[preview]], expand_x=True, expand_y=True, pad=(0, 0))
    layout = [[sg.Text('Search', font=FONT_BOLD), sg.Input(key=K_QUERY, enable_events=True, expand_x=True, font=FONT_BIG, focus=True,
                tooltip=' Every word must appear somewhere in the chat.   Put "quotes" around an exact phrase. '),
               sg.Button('Search', key=K_SEARCH, bind_return_key=True)],
              [sg.Checkbox('Tool steps', key=K_TOOLS, default=s('-tools-', True), enable_events=True,
                           tooltip=' Also search the commands, file paths and program output from Claude’s work steps '),
               sg.Checkbox('Match case', key=K_CASE, default=s('-case-', False), enable_events=True),
               sg.Text('Updated'), sg.Combo(list(DAYS), default_value=s('-days-', 'Any time'), key=K_DAYS, readonly=True, enable_events=True, size=(12, 1)),
               sg.Text('Project'), sg.Combo([ALL_PROJECTS], default_value=ALL_PROJECTS, key=K_PROJECT, readonly=True, enable_events=True, size=(30, 1), auto_size_text=False),
               sg.Text('Sort'), sg.Combo(SORTS, default_value=s('-sort-', SORTS[0]), key=K_SORT, readonly=True, enable_events=True, size=(13, 1)),
               sg.Push()] + legend,
              [sg.Pane([top_pane, bottom_pane], orientation='vertical', show_handle=True, handle_size=10, relief=sg.RELIEF_FLAT, key=K_PANE, expand_x=True, expand_y=True,
                       pad=(0, 4))],
              [sg.Button('Open chat', key=K_OPEN), sg.Button('Copy link', key=K_COPY_LINK), sg.Button('Copy title', key=K_COPY_TITLE), sg.Push(),
               sg.Text('Export'), sg.Input(s('-source-', DEFAULT_SOURCE), key=K_SOURCE, size=(40, 1), enable_events=True, font=FONT_SMALL),
               sg.FolderBrowse('Folder…', target=K_SOURCE), sg.FileBrowse('File…', target=K_SOURCE, file_types=(('Claude export (ZIP or manifest)', '*.zip *.json'),)),
               sg.Button('New export…', key=K_NEW_EXPORT, tooltip=' Ask claude.ai for a fresh export of all your chats (opens the Privacy settings page) '),
               sg.Button('Download export', key=K_DOWNLOAD, disabled=True, tooltip=' Opens the export’s download links in your browser again '),
               sg.Button('Archive…', key=K_ARCHIVE, tooltip=' Where finished exports are kept (one dated folder each) - put it in Dropbox to share it between PCs '),
               sg.Button('Reload', key=K_RELOAD, tooltip=' F5 ')],
              [sg.Text('', key=K_STATUS, expand_x=True, font=FONT_SMALL), sg.Text('', key=K_EXPORT_INFO, font=FONT_SMALL, text_color=C_META),
               sg.Text(f'v{VERSION}', font=FONT_SMALL, text_color=C_DIM)]]
    size = tuple(s('-size-', (None, None)) or (None, None))
    window = sg.Window(APP_NAME, layout, resizable=True, finalize=True, font=FONT, icon=ICON, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT,
                       auto_save_location=True, size=size)
    pw = window[K_PANE].PanedWindow                 # wide amber sash, raised, resize cursor, big grab handle - same as the SNAP test runner
    pw.configure(sashwidth=8, sashrelief=sg.RELIEF_RAISED, bg='#c9852f', sashcursor='sb_v_double_arrow', showhandle=True, handlesize=14, bd=0)
    for member in (window[K_RESULTS], window[K_PREVIEW]):
        pw.paneconfigure(member.ParentContainer.TKColFrame, stretch='always', minsize=60)      # both halves share window growth; neither can vanish
    sash_y = s('-sash-', None)
    if sash_y:
        window.refresh()
        pw.sash_place(0, 0, int(sash_y))
    return window


def move_selection(window, state, delta=0, to=None):
    """Moves the selected result (Up/Down/PgUp/PgDn/Home/End).  Returns 'break' so tk doesn't also handle the key"""
    n = len(state.results)
    if n:
        sel = window[K_RESULTS].Widget.selection()
        cur = int(sel[0]) - 1 if sel else -1
        row = 0 if to == 'first' else n - 1 if to == 'last' else max(0, min(n - 1, cur + delta)) if cur >= 0 else 0
        select_row(window, row)
    return 'break'


def select_row(window, row):
    window[K_RESULTS].update(select_rows=[row])
    window[K_RESULTS].Widget.see(row + 1)


def bind_keys(window, state):
    window.bind('<Escape>', K_ESCAPE)
    window.bind('<Control-f>', K_FOCUS_SEARCH)
    window.bind('<Control-F>', K_FOCUS_SEARCH)
    window.bind('<F5>', K_RELOAD)
    window[K_RESULTS].bind('<Return>', '+OPEN', propagate=False)
    window[K_RESULTS].bind('<Double-Button-1>', '+OPEN')
    move = lambda delta=0, to=None: move_selection(window, state, delta, to)
    tree, entry, text = window[K_RESULTS].Widget, window[K_QUERY].Widget, window[K_PREVIEW].Widget
    for seq, delta, to in (('<Prior>', -PAGE, None), ('<Next>', PAGE, None), ('<Home>', 0, 'first'), ('<End>', 0, 'last')):
        tree.bind(seq, lambda e, d=delta, t=to: move(d, t))
    for seq, delta in (('<Down>', 1), ('<Up>', -1), ('<Next>', PAGE), ('<Prior>', -PAGE)):          # arrows in the search box move through the results
        entry.bind(seq, lambda e, d=delta: move(d))
    text.bind('<Button-1>', lambda e: text.focus_set(), add='+')                                      # read-only text still takes focus so its keys work
    for seq, amount, unit in (('<Up>', -1, 'units'), ('<Down>', 1, 'units'), ('<Prior>', -1, 'pages'), ('<Next>', 1, 'pages')):
        text.bind(seq, lambda e, a=amount, u=unit: (text.yview_scroll(a, u), 'break')[1])
    text.bind('<Home>', lambda e: (text.yview_moveto(0), 'break')[1])
    text.bind('<End>', lambda e: (text.yview_moveto(1), 'break')[1])
    window.TKroot.bind('<Configure>', lambda e: setattr(state, 'size', window.size) if e.widget is window.TKroot else None, add='+')


def start_load(window, state, path):
    state.load_id += 1
    state.loaded_path = path
    state.loading = True
    load_id = state.load_id
    window[K_STATUS].update('Loading your Claude export…')

    def run():
        try:
            items, info = load_export(path, lambda msg: window.write_event_value(K_LOAD_PROGRESS, (load_id, msg)))
            window.write_event_value(K_LOAD_DONE, (load_id, items, info))
        except Exception:
            window.write_event_value(K_LOAD_FAILED, (load_id, path, traceback.format_exc()))

    threading.Thread(target=run, daemon=True).start()


def start_search(window, state, values):
    state.search_pending = 0
    if not state.chats and not state.loaded:            # first load still running - it searches when it finishes
        return
    state.search_gen += 1
    gen, chats = state.search_gen, state.chats
    terms, case, tools = parse_terms(values[K_QUERY]), values[K_CASE], values[K_TOOLS]
    days, project, sort = DAYS.get(values[K_DAYS], 0), values[K_PROJECT], values[K_SORT]

    def run():
        try:
            t0 = time.perf_counter()
            results = search_chats(chats, terms, case, tools, days, project, lambda: state.search_gen != gen)
            if results is not None:
                sort_results(results, sort)
                window.write_event_value(K_SEARCH_DONE, (gen, terms, case, tools, results, time.perf_counter() - t0))
        except Exception:
            window.write_event_value(K_THREAD_ERROR, ('Search failed', traceback.format_exc()))

    threading.Thread(target=run, daemon=True).start()


def show_results(window, state, terms, case, tools, results, seconds):
    state.results, state.rx, state.tools = results[:MAX_ROWS], term_regex(terms, case), tools
    window[K_RESULTS].update(values=[[fmt_ts(c.updated, False), c.title, c.project, f'{n:,}' if n else ''] for c, n in state.results])
    if not state.chats:
        status = 'No chats loaded'
    elif terms:
        status = f'{len(results):,} of {len(state.chats):,} chats match      ({seconds:.2f} s)'
    else:
        status = f'{len(results):,} chats      ({seconds:.2f} s)'
    if len(results) > MAX_ROWS:
        status += f'   -   showing the first {MAX_ROWS:,}'
    window[K_STATUS].update(status)
    state.shown_chat = None
    if state.results:
        uuids = [c.uuid for c, n in state.results]
        select_row(window, uuids.index(state.selected_uuid) if state.selected_uuid in uuids else 0)
    else:
        state.preview.show(message=state.empty_text or 'No chats match.\n\nTry fewer words, turn on "Tool steps", or set Updated to "Any time" and Project to "All projects".')


def update_projects_combo(window, items, current):
    names = sorted({c.project for c in items if c.project}, key=str.lower)
    choices = [ALL_PROJECTS] + names + ([NO_PROJECT] if names and any(not c.project for c in items) else [])
    value = current if current in choices else ALL_PROJECTS
    window[K_PROJECT].update(value=value, values=choices)
    return value


def show_export_status(window, state, found):
    """The export line at the bottom right, and whether Download export can be clicked"""
    todo, attention = found.get('todo'), True
    files = lambda n: f'{n} export file{"s" if n != 1 else ""}'
    if todo and links_expired(todo):
        text = 'Export links expired - ask claude.ai for a new export'
    elif todo and time.time() - state.links_opened_at < 180:
        text = f'Downloading {files(len(todo[1]))} in your browser…'
    elif todo:
        text = f'{files(len(todo[1]))} not downloaded yet - click Download export'
    elif found.get('sources'):
        text, attention = f'{found["label"]}      newest chat {fmt_ts(state.newest)}', False
    else:
        text, attention = 'No export found', False
    window[K_EXPORT_INFO].update(text, text_color=C_TITLE if attention else C_META)
    window[K_DOWNLOAD].update(disabled=not todo or links_expired(todo))


def open_export_links(window, state, found):
    """Opens the download links of the export's missing files in the browser, which saves the ZIPs into Downloads"""
    todo = found.get('todo')
    if not todo or links_expired(todo):
        return
    state.open_queue = [d['export_url'] for d in todo[1]]           # opened one at a time from the event loop
    state.next_open = 0
    state.links_opened_at = time.time()
    opened, name = sg.user_settings_get_entry('-opened exports-', []), os.path.basename(todo[0]['path'])
    if name not in opened:
        sg.user_settings_set_entry('-opened exports-', (opened + [name])[-30:])
    show_export_status(window, state, found)


def selected_chat(window, state):
    sel = window[K_RESULTS].Widget.selection()
    row = int(sel[0]) - 1 if sel else -1
    return state.results[row][0] if 0 <= row < len(state.results) else None


def main():
    sg.user_settings_filename(filename=SETTINGS_FILE)
    window = make_window()
    state = State()
    state.preview = Preview(window[K_PREVIEW], lambda: state.shown_chat and webbrowser.open(state.shown_chat.url))
    bind_keys(window, state)
    start_load(window, state, window[K_SOURCE].get().strip() or DEFAULT_SOURCE)

    while True:
        event, values = window.read(timeout=100)
        if event in ('Exit', sg.WINDOW_CLOSED, K_ESCAPE):
            break
        if event == 'Version':
            sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event == K_THREAD_ERROR:
            sg.popup_error_with_traceback(*values[event])
        elif event == K_LOAD_PROGRESS:
            if values[event][0] == state.load_id:
                window[K_STATUS].update(values[event][1])
        elif event == K_LOAD_DONE:
            load_id, items, info = values[event]
            if load_id == state.load_id:
                state.chats, state.loaded, state.loading = items, True, False
                state.export_sig, state.pending_sig, state.newest = info['sig'], None, info['newest']
                todo = info['todo']
                if todo and os.path.basename(todo[0]['path']) not in sg.user_settings_get_entry('-opened exports-', []):
                    open_export_links(window, state, info)              # a new export's manifest - its links open once, by themselves
                state.empty_text = '' if info['sources'] else downloading_text(todo) if todo else no_export_text(info['path'])
                show_export_status(window, state, info)
                values = dict(values)
                values[K_PROJECT] = update_projects_combo(window, items, sg.user_settings_get_entry('-project-', ALL_PROJECTS))
                start_search(window, state, values)
        elif event == K_LOAD_FAILED:
            load_id, path, tb = values[event]
            if load_id == state.load_id:
                state.loaded, state.loading = True, False
                state.export_sig, state.pending_sig = find_export(path)['sig'], None          # don't retry until the files change
                window[K_STATUS].update('Could not read the export' + (' - still showing the chats loaded before' if state.chats else ''))
                if not state.chats:
                    last_line = tb.strip().splitlines()[-1]
                    state.preview.show(message=f'Could not read the Claude export in:\n      {path}\n\n      {last_line}\n\n'
                                               'The ZIP may be damaged or only partly downloaded - try downloading the export again, then press F5.')
                sg.popup_error_with_traceback(f'Could not read the Claude export in {path}', tb)
        elif event == K_SEARCH_DONE:
            if values[event][0] == state.search_gen:
                show_results(window, state, *values[event][1:])
        elif event == K_QUERY:
            state.search_pending = time.time()
        elif event == K_SEARCH:
            start_search(window, state, values)
        elif event in (K_TOOLS, K_CASE, K_DAYS, K_PROJECT, K_SORT):
            for key, name in ((K_TOOLS, '-tools-'), (K_CASE, '-case-'), (K_DAYS, '-days-'), (K_PROJECT, '-project-'), (K_SORT, '-sort-')):
                sg.user_settings_set_entry(name, values[key])
            start_search(window, state, values)
        elif event == K_RESULTS:
            chat = selected_chat(window, state)
            if chat is not None and chat is not state.shown_chat:
                state.shown_chat, state.selected_uuid = chat, chat.uuid
                state.preview.show(chat, state.rx, state.tools)
        elif event in (K_RESULTS_OPEN, K_OPEN, K_COPY_LINK, K_COPY_TITLE):
            chat = selected_chat(window, state)
            if chat is None:
                window[K_STATUS].update('Pick a chat first')
            elif event == K_COPY_LINK:
                sg.clipboard_set(chat.url)
                window[K_STATUS].update('Link copied:  ' + chat.url)
            elif event == K_COPY_TITLE:
                sg.clipboard_set(chat.title)
                window[K_STATUS].update('Title copied:  ' + chat.title)
            else:
                webbrowser.open(chat.url)
        elif event == K_FOCUS_SEARCH:
            window[K_QUERY].set_focus()
            window[K_QUERY].Widget.select_range(0, 'end')
        elif event == K_SOURCE:
            state.source_pending = time.time()
        elif event == K_DOWNLOAD:
            open_export_links(window, state, find_export(state.loaded_path or DEFAULT_SOURCE))
        elif event == K_NEW_EXPORT:
            webbrowser.open(EXPORT_PAGE)
            sg.popup('The claude.ai Privacy settings page is opening in your browser.\n\n'
                     '1.   Click  Export data  on that page.\n'
                     '2.   When the email arrives (minutes to an hour), click its link - a small manifest-….json saves to Downloads.\n'
                     f'3.   This program sees it, opens the download links, and loads the chats by itself.\n\n'
                     f'Watching:  {state.loaded_path or DEFAULT_SOURCE}\nArchive:  {archive_folder()}',
                     title='Getting a new export', keep_on_top=True, non_blocking=True, font=FONT)
        elif event == K_ARCHIVE:
            folder = sg.popup_get_folder('Folder where finished exports are kept (each in its own dated subfolder)', default_path=archive_folder(),
                                         keep_on_top=True, no_window=True)
            if folder:
                sg.user_settings_set_entry('-archive-', os.path.normpath(folder))
                start_load(window, state, state.loaded_path or DEFAULT_SOURCE)
        elif event == K_RELOAD:
            path = values[K_SOURCE].strip() or DEFAULT_SOURCE
            sg.user_settings_set_entry('-source-', path)
            start_load(window, state, path)

        now = time.time()
        if state.open_queue and now >= state.next_open:                               # export download links, one at a time
            webbrowser.open(state.open_queue.pop(0))
            state.next_open = now + OPEN_GAP
        if state.loaded and not state.loading and now - state.last_watch >= WATCH_EVERY:   # watch for a new export, or more of its ZIPs
            state.last_watch = now
            found = find_export(state.loaded_path)
            if found['sig'] == state.export_sig:
                state.pending_sig = None
            elif found['sig'] == state.pending_sig:                                   # changed, then held still for one check -> load it
                state.pending_sig = None
                start_load(window, state, state.loaded_path)
            else:
                state.pending_sig = found['sig']
            show_export_status(window, state, found)
        if state.search_pending and time.time() - state.search_pending > 0.3:          # search once typing pauses
            start_search(window, state, values)
        if state.source_pending and time.time() - state.source_pending > 1.0:          # Export path changed (typed or browsed)
            state.source_pending = 0
            path = values[K_SOURCE].strip()
            if path != state.loaded_path and os.path.exists(path):
                sg.user_settings_set_entry('-source-', path)
                start_load(window, state, path)

    if state.size:
        sg.user_settings_set_entry('-size-', state.size)
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
