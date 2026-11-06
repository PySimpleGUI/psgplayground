import PySimpleGUI as sg
import os
import io
import base64
import re
from typing import Dict
import ast
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops, ImageTk
from typing import List, Any
import psgdnd
import sys
import struct
import math
import time
import subprocess
import urllib.parse
import json


"""
    PSG Dock  -  a dock that launches your programs.   (was MiniLauncher2)

    Two styles - the switch button on the dock flips between them:  Panel - a card with names and versions in columns,  Bar - a Mac-style
    row of icons that grow under the mouse, each section marked in its own colour (or one stack per section, which flies out when clicked).
    Each style keeps its own place - floating anywhere, or docked to the bottom / top / left / right edge of a screen, auto-hidden if you
    like - and its own size:  S M L on the dock, or drag across them for any size between.  Drop programs from Explorer onto the dock - they
    land where you drop them.  Right-click a program for its own menu (open its folder, edit its source, rename, remove...).  Windows: an
    optional Glass look - see-through, with soft shadows.  Rearrange in the Panel: drag a program, or a heading to move its whole section
    (the Bar shows the same order).  The Programs window edits the whole list: drag entries by their ☰ grip.

    Changelog
    2.1     29-Oct-2026     Claude: single file (settings window merged in), toolbar + OK/Apply/Cancel settings window, drag-and-drop of
                            images and programs onto entries (icon pulled from the program), drag ☰ to reorder, 3-column layout fix,
                            version number added.
    2.1.1   29-Oct-2026     Claude: drag-to-reorder lifts the entry out as a floating replica (icon, name, path, icon string) with an orange
                            outline and leaves a grey slot where it will land; settings list widens to fit its entries so the trash cans
                            aren't cut off; size grip in the status bar for resizing the (titlebar-less) settings window.
    2.1.2   30-Oct-2026     Claude: the drop slot shown while dragging takes its colour from the theme (lighter shade of the background with a
                            faint outline) instead of fixed grey.
    2.1.3   30-Oct-2026     Claude: "Settings..." added to the right-click menu.
    2.2.42  06-Nov-2026     Claude: Ctrl+A in the search box selects what's typed (highlighted, as in a real text box): then a letter or a paste
                            replaces it, Backspace or Delete clears it, Ctrl+C copies it, Ctrl+X cuts it; a click in the box or an arrow
                            key lets go of it. The Panel's box and the Bar's search fly-out both.
    2.2.41  06-Nov-2026     Claude: search. The Panel has a search box under its title strip (the magnifier beside T S M L shows or hides
                            it): type, and only the programs whose names match show, as you type - a heading that matches brings its whole
                            section, and first letters work too (pdm finds Piano Dynamics Monitor). The matching letters are marked; the
                            arrows move the blue pick, Enter opens it, Esc clears. Right-click > Search: Hide what doesn't match (the card
                            keeps its size) or Dim it. The Bar has a search button: its matches fly out like a stack (every program while
                            nothing is typed), and with Dim the bar's other icons fade. Click the dock and type to search. Each dock keeps
                            its own setting; a dock with 12 or more programs starts with search on.
    2.2.40  05-Nov-2026     Claude: right-click a heading > Colour - Automatic (the palette's colour for its place, as before), one of the 11
                            section colours, or Custom... (the colour picker, any colour). It colours the heading and its programs' rail,
                            and on the Bar its section name and stack. Each dock keeps its own, by the heading's name - Rename keeps it
                            (in the Programs window too, one rename at a time). Picking a colour turns Colored sections on. A custom
                            colour too dark (or too light) to read on the card is moved just far enough to read.
    2.2.39  05-Nov-2026     Claude: right-click > Handle colour > Custom... - any colour for the hidden dock's handle (or its name tag), from the
                            colour picker. The picker starts at the colour you picked there last, and the menu's chip shows it (a rainbow
                            until you pick one). Each dock keeps its own.
    2.2.38  04-Nov-2026     Claude: a side bar's bubble no longer cuts a program's name to a few letters (it shortened the name to fit beside the
                            section's name, then left the section out for lack of room). Bar: right-click > Section name in the bubble -
                            turn it off to see just the program's name (with Section names under the bar you can see the sections anyway).
    2.2.37  04-Nov-2026     Claude: fixed - the Panel's switch button changed the size instead of switching to the Bar (since T was added, the
                            L part of the size control reached over it). Right-click > Handle colour: the hidden dock's handle (or name tag)
                            in a colour of its own - each dock its own, so several on one side are easy to tell apart.
    2.2.36  04-Nov-2026     Claude: the hide button is on every docked dock now: with Auto-hide off it tucks the dock away by hand and its
                            handle stays (above other windows) until you click it - then the dock stays out. Right-click > Fly out (with
                            Auto-hide on): at once, after a moment (0.3 s, as before), half a second or a second.
    2.2.35  04-Nov-2026     Claude: a T (Tiny, 65%) on the size control - T S M L on the Panel and the Bar.
    2.2.34  04-Nov-2026     Claude: the Panel's hide button moved to the bottom line, alone in the corner away from its edge (lower left on a
                            Panel docked on the right) - easy to find, and no longer among the buttons where you look for the close x.
    2.2.33  04-Nov-2026     Claude: where a dock goes is all dragging now - the Position menu is gone. Push a Panel into an edge (or bring the
                            mouse to one) and it docks there, with the blue highlight, like the Bar; pull a docked Panel or Bar off its edge
                            and let go and it floats there (a Bar pulled off a side keeps running up and down). Auto-hide is one click in
                            the right-click menu; Floating vertically too, for a floating Bar. A hide button (an arrow toward the edge) on a
                            docked, auto-hidden Panel's title strip and at the end of the Bar tucks it away at once. Name on the handle: the
                            hidden dock's handle becomes a tag with its name - handy with several docks on one side.
    2.2.32  04-Nov-2026     Claude: drag a Bar to another edge: near an edge (any monitor's) a blue highlight shows where it will dock - let go
                            and it is docked there, at that spot along the edge, turned across or up and down to fit. A docked Bar pulled
                            away from its edge (or its hidden handle pulled away) does the same; let go away from every edge and it goes back.
                            A floating Bar dragged to the very edge docks there too (anywhere else it stays floating).
    2.2.31  04-Nov-2026     Claude: Bar - Position > Floating vertically: a floating bar that runs up and down, opening toward the middle of
                            the screen. A docked bar slides along its edge when you drag it (anywhere on it) - the spot is kept. A docked
                            Panel slides along its edge by its title strip.
    2.2.30  04-Nov-2026     Claude: drag an auto-hidden dock's handle along its edge (up and down on a side, along the top or bottom) - the
                            dock flies out there, and the spot is kept for that dock and style, so two docks can share one side. The dock now
                            flies out after the mouse rests on the handle a moment (a click opens it at once); Position > an edge centres it.
    2.2.29  04-Nov-2026     Claude: several docks, each with its own programs and settings - start one with  psgdock.pyw --dock "Claude chats"
                            (the dock started without a name keeps its files, nothing changes for it). Right-click > Docks: open another
                            dock, New dock..., Rename this dock..., Desktop shortcut for this dock. Each shows its name (the Panel's title
                            strip - a narrow Panel widens for it - the window title, the gear's bubble on the Bar); one dock never runs twice
                            (starting it again says it's already open). Links as entries: a web page, a Claude chat (https://claude.ai/...
                            opens in the Claude app), claude://, mailto: ... - right-click > Add a link... (a heading's: Add a link here...),
                            or type one in the Programs window's path; the icon is the app that opens it.
    2.2.28  03-Nov-2026     Claude: Programs window - dragging an entry near the list's top or bottom scrolls much faster: faster the
                            closer to the edge, faster still past it (move the mouse beyond the list), and it speeds up while you hold
                            it there; the mouse wheel scrolls too while dragging. The dock says where to rearrange: the Panel's bottom
                            line (drag to rearrange), the Programs window's hint, and a docked Bar shows a tip the first time an icon
                            is dragged (rearranging is done in the Panel - the Bar shows the same order).
    2.2.27  03-Nov-2026     Claude: Panel - drag a program to a new place in the dock (another section or column too), or drag a heading
                            to move its whole section. A copy follows the mouse, a blue line shows where it lands, it is saved at once;
                            let go outside the dock and nothing moves. A floating dock now moves by its title strip or an empty spot -
                            dragging a program moves the program. Also fixed: 2.2.25's safety net for a dock already gone when it saves
                            where it was used tk, which isn't defined here (sg.tk now).
    2.2.26  03-Nov-2026     Claude: Panel - right-click > Columns goes up to 8 (it stopped at 3). Auto uses as many columns as it takes
                            to keep the Panel wider than it is tall - a long list was growing tall in 3 columns. Never more columns
                            than fit across the screen; a Panel on a side edge still gets one tall column when it fits.
    2.2.25  03-Nov-2026     Claude: Alt-F4 no longer crashes the dock. The dock ignores Alt-F4 now (close it with right-click > Exit, or the
                            Panel's x) - it is often the focused window, so Alt-F4 meant for another window closed it, and a floating dock
                            then crashed saving where it was. Alt-F4 on the Programs window works like its x: it asks first when there
                            are unsaved changes (they were thrown away without asking).
    2.2.24  03-Nov-2026     Claude: Section names under the bar no longer crowd together: a section narrower than its name gets room either
                            side of its icons (like the stacks do), so every name sits under its own section.
    2.2.23  03-Nov-2026     Claude: Bar - right-click > Section names under the bar: each section's name in its colour under its line
                            (made lighter or darker where it wouldn't read on the bar), under its stack in the Stacks layout. A long name
                            borrows room from its neighbours. Point at one for the section's bubble, right-click it for its menu.
    2.2.22  03-Nov-2026     Claude: versions beside every program that has one - VERSION = / __version__ = / version = at the top level of
                            its source (only lowercase version = was found before, so most of your programs showed none), and for a
                            pip-installed program's .exe (psgshortcut.exe) the version of its package. A version="1.0" inside a string no
                            longer counts (GitHub Traffic showed 1.0 from its XML). Right-click > Versions turns them off.
    2.2.21  03-Nov-2026     Claude: the window that adds, removes and orders the programs is called Programs now - right-click >
                            Programs..., the gear's label and the window's title (Settings was the wrong name for it).
    2.2.20  02-Nov-2026     Claude: dragging the dock never starts a program - the drag is the dock's own now: it moves after 5 pixels, and
                            a press that moved it is never a click. Each style keeps its own place and size: the Panel floats where you
                            left it, the Bar sits at the bottom centre - switching no longer leaves it half off the screen, and a
                            floating dock is kept on the screen (when it changes size it keeps its corner, or its centre). On the dock:
                            S M L - one click for a size, drag across them for any size between (snaps to S, M or L when close) - and a
                            switch button for Panel / Bar. Text size (Small .. Extra large) for all of the dock's text, headings bigger
                            than names. Colored sections: each heading in its own colour, with a rail beside / under its programs.
                            Bar: a section's name shows big on the line before it, a program's bubble names its section; Layout: Icons,
                            or Stacks - a tile per section that flies out into its programs (arrow keys + Enter work too). Auto-hide
                            leaves a small handle at the edge. Show in the Bar, per program or section (Hidden from the Bar brings them
                            back). Settings opens where you left it (else in the middle of the dock's screen) and moves only by its title
                            strip. Rename / Remove and the other questions open by the mouse. Sharper icon no longer swaps a program's
                            picture for the Python logo when the program has no icon of its own.
    2.2.19  02-Nov-2026     Claude: the next level. Style: Panel (as before) or Bar - a Mac-style icon bar that magnifies under the mouse,
                            with a name bubble, a line between headings' groups, a gear, and a bounce when a program starts. Position:
                            Floating, or docked to the Bottom / Top / Left / Right of the screen it's on (centred, clear of the taskbar),
                            with Auto-hide (slides away; comes back when the mouse rests at that edge, also while dragging a file).
                            Drop programs from Explorer onto the dock: a gap / line shows where they land - under a heading or between two.
                            Right-click a program: open, open its folder, edit its source, copy its path, rename, sharper icon, remove;
                            a heading: add a program here, rename, remove. Add programs... in the menu. Icons are now kept sharp (saved up
                            to 128 px; Sharper icons for all fetches big ones for older entries). Glass look (Windows, optional): truly
                            see-through with soft shadows and smooth edges - it switches itself back if it can't show. Programs launch with
                            the shell, so paths with spaces, shortcuts and documents work.
    2.2.18  02-Nov-2026     Claude: Python programs with no icon of their own get one on every system: their icon from the Playground's
                            catalog (a Playground program), else a picture beside them with their name (x.png, x_icon.png, x.ico), else
                            Python's icon on Windows and PySimpleGUI's on Linux / Mac - on Mint they stayed blank (Linux has no program
                            icons to ask for).
    2.2.17  02-Nov-2026     Claude: a drop that arrives without a file name (some Linux drag sources send none) no longer blanks the entry - it
                            says to paste the path instead.
    2.2.16  02-Nov-2026     Claude: a program's icon is pulled out when its path is typed or pasted too, not only when the program is dropped,
                            and Settings fills in the icons of entries that have a path but no icon (OK keeps them) - on Linux they stayed
                            blank.  file:// paths (Linux file managers paste and drop those) and quotes / braces / line ends around a
                            dropped path are cleaned up first.
    2.2.15  02-Nov-2026     Claude: Linux: dragging an entry in Settings no longer makes the whole window jump away from it.
    2.2.14  02-Nov-2026     Claude: Linux / Mac: the Brightness panel has square corners like the dock - only Windows can make corners see-through.
    2.2.13  02-Nov-2026     Claude: faster auto-scroll while dragging an entry in Settings - it was counted in screen pixels, so on a 200%
                            display it moved half as fast as meant; it now grows with the display scaling, and the top speed (pointer at the
                            very edge of the list) is a third higher.
    2.2.12  01-Nov-2026     Claude: right-click > Brightness... - a slider makes any theme darker (down to -80%) or lighter (+50%); the dock and
                            its Settings window follow. The dock changes as you drag; Done or Enter keeps it, Escape puts it back.
    2.2.11  01-Nov-2026     Claude: the 32 themes the new widgets use - 16 dark (colorful, like ForestFloor and CrimsonVelvet) and 16 light - in a
                            two-column Theme menu with a color chip beside each name. The title strip, heading gold and menu colors are worked out
                            from each theme. A theme saved by an older version carries over (Midnight is now Carbon).
    2.2.10  01-Nov-2026     Claude: finds the icon in programs that split it over several lines - b''.join((b'iVBOR...', b'...')) as
                            Player Coach and anything made by make_icons.py do; those got the Python logo. The pieces are joined back up.
    2.2.9   01-Nov-2026     Claude: Settings window no wider than its entries - the status bar showed the whole settings-file path, which made
                            the window wide; it now shows the file name, with the full path in its tooltip. Shorter hint line too.
    2.2.8   01-Nov-2026     Claude: the dock fills a column top to bottom (up to 10 rows) before starting the next one - a short list was being
                            spread over 3 columns of 2, which read left to right. Right-click > Columns: Auto (that), or always 1, 2 or 3.
    2.2.7   01-Nov-2026     Claude: the new widgets' look. The dock is one rounded card drawn with Pillow: a title strip (icon, name, version,
                            gear, x that turns red), rows with each program's icon, name and version, headings in gold, and a bottom line
                            that shows the path of the program under the mouse. A click launches - dragging the dock never does.
                            Right-click: Theme (now 32 - see 2.2.11), Size, Opacity (was Alpha 1-10), Keep on top - remembered.
                            The Settings window has the same title strip as the widgets' Settings and follows the theme. The crimson theme
                            is retired. Sharp on high-DPI displays (dpi aware; Settings pictures are enlarged to match). Linux / Mac:
                            square corners, as only Windows can make the corners see-through.
    2.2.6   01-Nov-2026     Claude: slower, steadier auto-scroll while dragging an entry near the top/bottom of the Settings list - it used to
                            jump a tenth of the list on every mouse movement; now it glides on a timer, faster the closer the pointer is to
                            the edge (about 2 entries a second at the very edge).
    2.2.5   01-Nov-2026     Claude: right-click menus compact and flat (bd=0, activeborderwidth=1) in the dock's own colours, sub-menus too -
                            tk drew the Alpha sub-menu Windows-gray.
    2.2.4   01-Nov-2026     Claude: Headings - "+ Heading" in Settings adds a heading entry (drag it into place like any entry); the dock shows
                            each heading as a gold label with a line under it above the programs that follow it, and never leaves a
                            heading alone at the bottom of a column. + Add / + Heading put the new entry above the first checked one
                            (or at the end), scroll to it and select its name. The check box moved up beside the trash can.
    2.2.3   31-Oct-2026     Claude: Refresh button removed from the title bar (Settings refreshes the dock itself; Refresh stays in the
                            right-click menu for the rare case of a program's version number changing on disk).
    2.2.2   31-Oct-2026     Claude: PSG Dock's own icon - three app tiles on a reflective shelf - beside the title and as the window / taskbar icon
                            of both windows (the old title image was the refresh arrows).
    2.2.1   31-Oct-2026     Claude: right-click menu broke after changing Alpha - the Alpha / Keep-on-top updates used fixed menu positions and
                            "Settings..." had shifted them; they now find their entries by name.
    2.2.0   31-Oct-2026     Claude: renamed PSG Dock (file psgdock.pyw). Settings move to psgdock_entries.json (the app list) and psgdock.json
                            (window settings) - both are copied from the old launcher2.json / MiniLauncher2.json the first time it runs.
    2.1.4   30-Oct-2026     Claude: a dragged entry could be slid off the top/bottom of the window and get stuck floating - the mouse-release
                            landed on the floating copy instead of the grip. The copy now stays inside the list, forwards its own
                            mouse events, and the drop always cleans up.

    Single file - the Programs window (list of applications) is in the PROGRAMS WINDOW section below.
    Drop an image file onto an entry in the Programs window to use it as that entry's icon.
    Drop a program (.exe, .pyw, .lnk, ...) onto an entry and the path, name and icon are filled in from it.
    Drag an entry by its ☰ grip to change the order - it lifts out and floats with the mouse, the orange slot shows where it will land.
    Requires:  PySimpleGUI, pillow, psgdnd  (pip install psgdnd)

    Copyright 2026_PySimpleGUI
"""

version = '2.2.42'
APP_NAME = 'PSG Dock'
ENTRIES_FILENAME = 'psgdock_entries.json'                       # the list of programs (was launcher2.json)
WINDOW_SETTINGS_FILENAME = 'psgdock.json'                       # alpha, keep-on-top, window position (was MiniLauncher2.json, named after the old file)
MAIN_SETTINGS_FILENAME = WINDOW_SETTINGS_FILENAME               # the dock started without a name keeps these two files.  A named dock (--dock "Claude chats") has its own:
DOCK_PREFIX = 'psgdock_dock_'                                   #   psgdock_dock_claude_chats.json and psgdock_dock_claude_chats_entries.json - set by use_dock()


def migrate_settings():
    """ First run after the rename: copy the old settings files to their new names so nothing is lost """
    import shutil
    for old, new in (('launcher2.json', ENTRIES_FILENAME), ('MiniLauncher2.json', WINDOW_SETTINGS_FILENAME)):
        old_path, new_path = sg.UserSettings(old).get_filename(), sg.UserSettings(new).get_filename()
        if os.path.exists(old_path) and not os.path.exists(new_path):
            shutil.copyfile(old_path, new_path)
__version__ = version.split()[0]


KIND_APP, KIND_HEADING = 'app', 'heading'                          # an entry is a program to launch, or a heading over the programs that follow it


class Block:
    active_blocks = {}  # type:  Dict[int, Block]
    def __init__(self, block_num, name, path, iconb64, kind=KIND_APP, bar=True):
        self.block_num = block_num
        self.name = name
        self.path= path
        self.iconb64 = iconb64
        self.kind = kind
        self.bar = bar                                  # shown in the Bar style (the Panel shows everything)

class G:
    right_click_menu = []
    block_number = 0
    launcher_settings : sg.UserSettings = None
    dirty = False                                       # True while the Programs window has unsaved changes
    auto_icon = {}                                      # Programs window: block number -> the path its icon was pulled from (a newly typed path may replace that icon)
    theme, size, opacity, on_top = 'Toybox', 1.0, 90, False                             # right-click choices, saved in psgdock.json (size: each style its own)
    columns = 'Auto'                                    # right-click > Columns: 'Auto' or '1' .. '8'
    scale = 1.0                                         # dock drawing scale = display scaling x Size
    dpi = 1.0                                           # display scaling (2.0 on a 200% Windows display)
    hover = None                                        # the part of the dock under the mouse: 'gear', 'close', ('app', block_num) or None
    press = None                                        # a mouse press on the dock: where (on the screen), on what, where the dock was, dragging it yet
    hits = []                                           # [(x0, y0, x1, y1, part)] in window pixels, filled by render_panel()
    fonts = {}
    icon_cache = {}
    swatches = {}                                       # (theme name, brightness) -> PhotoImage of its chip in the Theme menu
    bright = 0                                          # Brightness: -80 (much darker) .. 50 (lighter), 0 = the theme as designed
    tuned = {}                                          # (theme name, brightness) -> the theme's colors at that brightness
    versions = {}                                       # block_num -> version found in the program's source
    show_versions, scripts = True, None                 # right-click > Versions;  pip script name -> its package's version (made once, when needed)
    bar_labels, label_spans = False, []                 # Bar: right-click > Section names under the bar;  where each name is: [(m0, m1, heading block_num)]
    style, place, autohide, magnify, glass = 'Panel', 'Floating', False, 'Large', False      # right-click > Style / Position / Auto-hide / Magnify / Glass look
    monitor_pt = None                                   # docked: a point on the monitor the dock lives on
    mon, work, shown_pos, fit_rows = (0, 0, 1, 1), (0, 0, 1, 1), (0, 0), 10                    # that monitor, its work area (no taskbar), where the dock shows
    window = None                                       # the dock window now - timers of a closed one see it isn't theirs and stop
    win_size = None                                     # the picture's (= the window's) size in pixels
    hidden, anim, out_since, edge_since = False, None, None, None                             # auto-hide state
    mag, pointer, tracking, last_signature = [], None, False, None                            # Bar: magnification of each item, the mouse, the 60 Hz loop
    bar_geo, spans, bar_extent = None, [], (0, 0)                                             # Bar: sizes, what is where along the bar, the bar's ends
    bounce, flash = {}, {}                                                                    # block_num -> launch bounce start / accent glow end
    drop_index, drop_item, drop_line, drop_open, drop_rows, panel_off = None, None, None, 0.0, [], 0     # programs being dragged over the dock
    menu_target, menu_at = None, None                   # the program / heading a right-click menu was opened on, and where (screen point)
    api, layered, last_image, keep = None, None, None, {}                                     # Glass (UpdateLayeredWindow), the shown picture, tk images in use
    text, sections, bar_layout = 'Medium', True, 'Icons'                                      # right-click > Text size / Colored sections / Layout (Bar)
    location, legacy_style, default_pt = None, 'Panel', None                                  # this style's floating spot; the style 2.2.19 showed; where the last dock was
    full_size, sliding = None, False                    # the whole dock's size (the window is only its handle while auto-hidden); sliding in / out
    scrub = None                                        # dragging across S M L
    tip_shown, scroll_since = False, None               # the Bar's 'rearrange in the Panel' tip was shown; Programs window: held at an edge since
    drag_item = None                                    # Panel: a program / section being dragged to a new place (its list positions, the copy that follows the mouse...)
    stacks_hover, rest = True, None                     # Stacks open when the mouse rests on them; (the stack it rests on, since, opened yet)
    stack_open, stack_closed, drop_stack = None, None, None                                   # Bar Stacks: the one flown out, the last closed (num, time), a drop aimed at one
    dock_slug, dock_title, mutex = '', APP_NAME, None   # which dock this is: '' = the one started without a name;  its name as shown;  the handle that says it's running
    dock_ready = False                                  # dock_title is this dock's own name now (read from its settings)
    link_icons = {}                                     # a link's scheme -> the icon of the app that opens it (made once)
    along = None                                        # docked: where along its edge the dock's middle is (0 .. 1 of the edge) - None = centred.  Saved per style
    float_vertical, float_side = False, 'Left'          # Bar: Floating vertically;  which way it opens (its bubble, stacks) - away from the nearer side of the screen
    handle_since = None                                 # auto-hidden: since when the mouse rests on the handle (-1: it was just dragged - wait until the mouse leaves it)
    edge_target, preview, preview_size = None, None, None                                     # a dock dragged near an edge: where it would dock, the highlight showing it
    handle_name = False                                 # right-click > Name on the handle: an auto-hidden dock's handle is a tag with its name
    bubble_section = True                               # Bar: right-click > Section name in the bubble
    flyout = 0.3                                        # right-click > Fly out: seconds the mouse rests on the handle before an auto-hidden dock comes out
    handle_color = None                                 # right-click > Handle colour: '#rrggbb', or None = the theme's
    handle_custom = None                                # right-click > Handle colour > Custom...: the colour last picked there ('#rrggbb') - its chip in the menu
    head_colors = {}                                    # a heading's right-click > Colour: {heading name: '#rrggbb'} - not in it = Automatic (the palette's)
    heads_at_load = []                                  # the Programs window: the heading names it opened with (a renamed heading keeps its Colour)
    search, search_sel = '', 0                          # the search: what's typed (not saved), and which match is the pick - the one Enter opens
    search_pref, search_mode = None, 'Hide'             # right-click > Search: on / off (None = on for a dock with SEARCH_AUTO programs or more);  Hide or Dim
    focus = False                                       # the dock has the keyboard (its search box shows the caret)
    search_spots = []                                   # Panel: where each match is drawn [(block_num, x, y)] - the Left / Right arrows go to the column beside
    redraw_due = False                                  # redraw_soon(): a redraw waits for tk to be idle (a burst of typing makes one picture)
    search_all = False                                  # Ctrl+A: what's in the Panel's search box is selected (drawn highlighted)



# Keys using tuples instead of strings... could migrate all keys to this format to make parsing much easier
K_CBOX = '-CBOX-'
K_B_CBOX = lambda num: (K_CBOX, num)
K_DEL = '-DELETE-'                              # Fixed part of key for block deletes
K_B_DEL = lambda num: (K_DEL, num)              # Block delete key

K_BUTTON = '-BUTTON-'
K_B_BUTTON = lambda num: (K_BUTTON, num)

K_PROGRAMS = '-PROGRAMS-'                       # open the Programs window: the list of programs and headings

K_KEEP_ON_TOP = '-keep on top-'
K_THEME = '-THEME-'                             # settings-file entry, and the prefix of the Theme menu keys
KT_THEME = lambda name: f'{K_THEME}{name}'
K_SIZE = '-SIZE-'
KT_SIZE = lambda name: f'{K_SIZE}{name}'
K_OPACITY = '-OPACITY-'
KT_OPACITY = lambda pct: f'{K_OPACITY}{pct}'
K_COLUMNS = '-COLUMNS-'
KT_COLUMNS = lambda choice: f'{K_COLUMNS}{choice}'
K_REFRESH = '-REFRESH-'
K_IMAGE = '-IMAGE-'                             # the dock is one Image the whole card is drawn into
K_HOVER = '-HOVER-'                             # the mouse moved onto another part of the dock, value = that part
K_CLICK = '-CLICK-'                             # a click (not a drag of the dock) on a part of the dock, value = that part
K_STYLE = '-STYLE-'                             # right-click > Style: Panel or Bar (settings entry, and the prefix of the menu keys)
KT_STYLE = lambda name: f'{K_STYLE}{name}'
K_PLACE = '-PLACE-'                             # right-click > Position: Floating, Bottom, Top, Left, Right
K_AUTOHIDE = '-AUTOHIDE-'
K_MAGNIFY = '-MAGNIFY-'
KT_MAGNIFY = lambda name: f'{K_MAGNIFY}{name}'
K_GLASS = '-GLASS-'
K_MONITOR = '-MONITOR-'                         # settings entry: a point on the monitor a docked dock lives on
K_ADD = '-ADD PROGRAMS-'
K_SHARPEN_ALL = '-SHARPEN ALL-'
K_DROP = '-DROP-'                               # files dropped on the dock, value = (files, x_root, y_root)
K_REBUILD = '-REBUILD-'                         # Glass couldn't show the picture: make the window again without it
K_DOCK = '-DOCK AT-'                            # a dock dragged to an edge and let go there, value = (edge, its monitor, where along the edge, the floating spot it came from)
K_FLOAT = '-FLOAT AT-'                          # a docked dock pulled off its edge and let go away from every edge, value = (where it was on the screen, up and down?)
K_FLOAT_VERTICAL = '-FLOAT VERTICAL-'           # right-click > Floating vertically (a floating Bar)
K_HANDLE_NAME = '-HANDLE NAME-'                 # right-click > Name on the handle (settings entry too)
K_BUBBLE_SECTION = '-BUBBLE SECTION-'           # right-click > Section name in the bubble (Bar): a program's bubble names its section too (settings entry too)
K_FLYOUT = '-FLY OUT-'                          # right-click > Fly out: how soon an auto-hidden dock comes out (settings entry, and the prefix of the menu keys)
K_HANDLE_COLOR = '-HANDLE COLOR-'               # right-click > Handle colour (settings entry: '#rrggbb' or None = the theme's;  the prefix of the menu keys + the colour's name)
K_HANDLE_CUSTOM = '-HANDLE CUSTOM-'             # right-click > Handle colour > Custom... (settings entry too: the colour last picked there)
K_HEAD_COLORS = '-HEADING COLORS-'              # settings entry: {heading name: '#rrggbb'} from a heading's right-click > Colour (each dock its own)
K_E_OPEN, K_E_FOLDER, K_E_EDIT, K_E_COPY = '-E OPEN-', '-E FOLDER-', '-E EDIT-', '-E COPY-'                  # a program's / heading's right-click menu
K_E_RENAME, K_E_REMOVE, K_E_SHARPEN, K_E_ADD_HERE = '-E RENAME-', '-E REMOVE-', '-E SHARPEN-', '-E ADD HERE-'
K_E_BAR = '-E IN BAR-'                          # a program's / heading's menu: Show in the Bar
K_E_COLOR = '-E COLOR-'                         # a heading's menu: Colour > ... (the prefix of the menu keys + Automatic, a palette colour's name or Custom...)
K_MOVED = '-MOVED-'                             # the floating dock was dragged to a new place
K_REORDER = '-REORDER-'                         # Panel: a program / section dragged to a new place, value = (start, end, list position)
K_TIP = '-TIP-'                                 # a short tip to show beside the mouse, value = its text
K_TEXT = '-TEXT SIZE-'                          # right-click > Text size (settings entry, and the prefix of the menu keys)
KT_TEXT = lambda name: f'{K_TEXT}{name}'
K_SECTIONS = '-SECTION COLORS-'                 # right-click > Colored sections
K_VERSIONS = '-SHOW VERSIONS-'                  # right-click > Versions: show programs' versions (settings entry too)
K_BAR_LABELS = '-BAR LABELS-'                   # right-click > Section names under the bar (Bar style; settings entry too)
K_LAYOUT = '-BAR LAYOUT-'                       # right-click > Layout (Bar): Icons or Stacks
KT_LAYOUT = lambda name: f'{K_LAYOUT}{name}'
K_UNHIDE = '-UNHIDE-'                           # right-click > Hidden from the Bar > Show ...
KT_UNHIDE = lambda num: f'{K_UNHIDE}{num}'
K_PROGRAMS_SPOT = '-PROGRAMS LOCATION-'         # settings entry: where the Programs window was left
K_STRIP = '-TITLE STRIP-'                       # the title strip of the Programs window (and the question cards) - drag the window by it
K_DOCK_NAME = '-DOCK NAME-'                     # settings entry: this dock's name as shown (title strip, window title, the gear's bubble)
K_OPEN_DOCK = '-OPEN DOCK-'                     # right-click > Docks > a dock: the prefix of the keys, + its file name part ('' = the dock started without a name)
K_NEW_DOCK = '-NEW DOCK-'                       # right-click > Docks > New dock...
K_RENAME_DOCK = '-RENAME DOCK-'                 # right-click > Docks > Rename this dock...
K_DOCK_SHORTCUT = '-DOCK SHORTCUT-'             # right-click > Docks > Desktop shortcut for this dock
K_ADD_LINK = '-ADD LINK-'                       # right-click > Add a link... (a web page, a claude:// chat ...)
K_E_ADD_LINK = '-E ADD LINK-'                   # a heading's menu: Add a link here...
K_SEARCH = '-SEARCH-'                           # right-click > Search > Search box / Search button (settings entry too: True / False - not there = by itself)
K_SEARCH_MODE = '-SEARCH MODE-'                 # right-click > Search > Hide / Dim (settings entry, and the prefix of the menu keys)
K_FIND_OPEN = '-FIND OPEN-'                     # a letter typed while the Bar has the keyboard: its search flies out with it, value = the letter
K_FIND_KEY = '-FIND KEY-'                       # a key in the Bar's search fly-out, value = (keysym, char, state)


ICON_SIZE = (30,30)
ICON_STORE = 128                                # icons are saved up to this size, so they stay sharp when the Bar shows them big
MAX_COLUMNS = 8                                 # right-click > Columns: Auto or 1 .. 8 - never more than fit across the screen
AUTO_ROWS = 10                                  # a Panel on a side edge: a column holds at least this many rows
COLUMN_CHOICES = ('Auto',) + tuple(str(n) for n in range(1, MAX_COLUMNS + 1))

# ---------- Look: the themes the new card widgets share (right-click > Theme) ----------
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
C_HEADING, C_HEADING_LIGHT = '#e8a33d', '#8a5412'   # gold headings - a darker gold on light themes
C_SWATCH_EDGE = '#7c8594'                       # outline of the color chips in the Theme menu - mid gray shows on dark and light menus
C_SELECT = '#2a62a8'                            # menu highlight and the buttons
C_CHECKED = '#1e9bff'                           # outline of a checked entry in the Programs window
C_CLOSE = '#c0392b'                             # the x becomes a red disc under the mouse
SIZES = {'Tiny': 0.65, 'Small': 0.8, 'Medium': 1.0, 'Large': 1.3, 'Huge': 1.6}     # right-click > Size;  S M L on the dock are Small, Medium, Large
OPACITIES = (100, 90, 80, 70, 60)
FONT_MENU = ('Segoe UI', 10)
FONT_NAMES = {True: ('segoeuib.ttf', 'DejaVuSans-Bold.ttf'), False: ('segoeui.ttf', 'DejaVuSans.ttf')}     # bold / regular: Windows first, then Linux
TRANSPARENT = '#010203'                         # Windows colour key: every pixel this colour is see-through and click-through (the rounded corners)
RADIUS, PAD, HEAD_H, FOOT_H = 18, 10, 42, 30    # dock geometry in design pixels (96 dpi, Medium size) - multiplied by the scale when drawn
COL_W, COL_GAP, ROW_H, ICON_PX = 232, 6, 34, 26
BTN_Y, BTN_R, BTN_GAP = 21, 11, 27              # gear and x: center height, click radius, from one button to the next


def T():
    """ The colours of the chosen theme: the five every card widget shares, plus the dock's own worked out from them - title strip, headings, menu """
    t = theme_colors()                                                  # the theme at the Brightness setting
    light = is_light(t['card'])
    return dict(t, light=light, strip=mix_hex(t['card'], t['border'], 0.4 if light else 0.3), heading=C_HEADING_LIGHT if light else C_HEADING,
                menu=(mix_hex(t['card'], t['text'], 0.04), t['text']))


def is_light(color):
    """ True for a light colour ('#rrggbb') - a light theme gets dark text, a white input background and a darker gold """
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.299 * r + 0.587 * g + 0.114 * b > 140


def apply_theme():
    """ The chosen theme as the PySimpleGUI theme (Programs window, popups), and the Programs window's entry outline colours from it """
    global FRAME_BORDER_COLOR_NOT_SELECTED, FRAME_BORDER_COLOR_SELECTED, COLOR_DIRTY_TEXT
    t = T()
    light = t.get('light', False)
    sg.theme_add_new(f'PSGDock{G.theme}', {'BACKGROUND': t['card'], 'TEXT': mix_hex(t['text'], t['card'], 0.08), 'INPUT': '#ffffff' if light else t['track'], 'TEXT_INPUT': t['text'],
                                          'SCROLL': t['border'] if light else t['track'], 'BUTTON': ('#ffffff', C_SELECT), 'PROGRESS': (C_CHECKED, t['track']), 'BORDER': 1,
                                          'SLIDER_DEPTH': 0, 'PROGRESS_DEPTH': 0})
    sg.theme(f'PSGDock{G.theme}')
    FRAME_BORDER_COLOR_NOT_SELECTED, FRAME_BORDER_COLOR_SELECTED = t['border'], C_CHECKED
    COLOR_DIRTY_TEXT = '#9a6f00' if light else '#ffc107'                 # the gold 'unsaved' text needs to be darker on white


def menu_colors():
    bg, fg = T()['menu']
    return {'bg': bg, 'fg': fg, 'activebackground': C_SELECT, 'activeforeground': '#ffffff', 'font': FONT_MENU}


def menu_label(text):
    """ A name made safe for a menu label: no '&' (underline marker), '::' (key separator) or leading '!' (disabled) """
    return text.replace('&', '+').replace('::', ':').lstrip('!')


def make_menu():
    """ The dock's right-click menu, with check marks on the current choices """
    tick = lambda on: '✓ ' if on else '    '                          # every label starts with a tick or the same width of spaces, so they line up
    place = [f'{tick(G.autohide)}Auto-hide::{K_AUTOHIDE}' if G.place != 'Floating' else '!    Auto-hide  (drag the dock to an edge first)',
             f'{tick(G.handle_name)}Name on the handle::{K_HANDLE_NAME}',             # where it goes: drag it - to an edge to dock it, off one to float it
             '    Handle colour', [f'{tick(c == G.handle_color)}{n}::{K_HANDLE_COLOR}{n}' for n, c in HANDLE_COLORS.items()] +
                                 ['---', f'{tick(G.handle_color is not None and G.handle_color not in HANDLE_COLORS.values())}{HANDLE_CUSTOM}::{K_HANDLE_CUSTOM}']]
    if G.autohide and G.place != 'Floating':
        place[1:1] = ['    Fly out', [f'{tick(abs(G.flyout - v) < 0.01)}{n}::{K_FLYOUT}{v}' for n, v in FLYOUTS.items()]]
    if G.style == 'Bar' and G.place == 'Floating':
        place.append(f'{tick(G.float_vertical)}Floating vertically::{K_FLOAT_VERTICAL}')
    sizes = [f'{tick(abs(G.size - v) < 0.005)}{n}  ({round(v * 100)}%)::{KT_SIZE(n)}' for n, v in SIZES.items()]
    if not any(abs(G.size - v) < 0.005 for v in SIZES.values()):
        sizes += ['---', f'!✓ {round(G.size * 100)}%  (dragged across S M L)']
    other = 'Bar' if G.style == 'Panel' else 'Panel'
    docks = [f'{tick(slug == G.dock_slug)}{menu_label(name)}{"  (open)" if slug != G.dock_slug and dock_running(slug) else ""}::{K_OPEN_DOCK}{slug}' for slug, name in list_docks()]
    docks += ['---', f'    New dock...::{K_NEW_DOCK}', f'    Rename this dock...::{K_RENAME_DOCK}']
    if sg.running_windows():
        docks.append(f'    Desktop shortcut for this dock::{K_DOCK_SHORTCUT}')
    search = ([f'{tick(search_on())}Search {"button" if G.style == "Bar" else "box"}::{K_SEARCH}', '---'] +
              [f'{tick(m == G.search_mode)}{label}::{K_SEARCH_MODE}{m}' for m, label in SEARCH_MODES.items()])
    items = [f'    Programs...::{K_PROGRAMS}', f'    Add programs...::{K_ADD}', f'    Add a link...::{K_ADD_LINK}', '    Docks', docks, '    Search', search, '---',
             f'    Switch to the {other}::{KT_STYLE(other)}'] + place + ['---',
             '    Size', sizes,
             '    Text size', [f'{tick(n == G.text)}{n}::{KT_TEXT(n)}' for n in TEXT_SIZES]]
    if G.style == 'Bar':
        items += ['    Layout', [f'{tick(k == G.bar_layout)}{label}::{KT_LAYOUT(k)}' for k, label in LAYOUTS.items()] +
                  ['---', f'{tick(G.stacks_hover)}Stacks open when the mouse rests on them::{K_STACKS_HOVER}' if G.bar_layout == 'Stacks' else
                   f'!{tick(G.stacks_hover)}Stacks open when the mouse rests on them'],
                  '    Magnify', [f'{tick(m == G.magnify)}{m}::{KT_MAGNIFY(m)}' for m in MAGNIFIES],
                  f'{tick(G.bar_labels)}Section names under the bar::{K_BAR_LABELS}',
                  f'{tick(G.bubble_section)}Section name in the bubble  (with a program\'s name)::{K_BUBBLE_SECTION}']
        hidden = [b for b in Block.active_blocks.values() if not b.bar]
        if hidden:
            items += ['    Hidden from the Bar', [f'    Show {menu_label(b.name or "(no name)")}{"  (section)" if b.kind == KIND_HEADING else ""}::{KT_UNHIDE(b.block_num)}'
                                                  for b in hidden]]
    else:
        items += ['    Columns', [f'{tick(c == G.columns)}{c}::{KT_COLUMNS(c)}' for c in COLUMN_CHOICES]]
    items += ['---', '    Theme', [f'{tick(n == G.theme)}{n}::{KT_THEME(n)}' for n in sorted(THEMES, key=lambda n: is_light(THEMES[n]['card']))],   # dark, then light
              f'    Brightness{f" ({bright_text(G.bright)})" if G.bright else ""}...::{K_BRIGHT}',
              f'{tick(G.sections)}Colored sections::{K_SECTIONS}', f'{tick(G.show_versions)}Versions::{K_VERSIONS}',
              '    Opacity', [f'{tick(p == G.opacity)}{p}%::{KT_OPACITY(p)}' for p in OPACITIES]]
    if sg.running_windows():
        items += [f'{tick(G.glass)}Glass look::{K_GLASS}']
    items += [f'{tick(G.on_top)}Keep on top::{K_KEEP_ON_TOP}', '---', f'    Sharper icons - fetch them again...::{K_SHARPEN_ALL}', f'    Refresh::{K_REFRESH}',
              '    Edit Me::Edit Me', '    Version::Version', '---', '    Exit::Exit']
    return ['', items]


def set_right_click_menu(window:sg.Window, menu):
    for elem in window.element_list():
        elem.set_right_click_menu(menu, propogate_to_window=True)
    style_menus(window)


def style_menus(window:sg.Window):
    """ Compact, flat right-click menus (bd=0, activeborderwidth=1) in the theme's menu colours - sub-menus included, which tk would
        otherwise draw Windows-gray.  Run again after every set_right_click_menu() """
    tk = sg.tk
    colors = menu_colors()
    menus = {id(m): m for m in [window.TKRightClickMenu] + [e.TKRightClickMenu for e in window.element_list()] if m is not None}

    def style(menu):
        try:
            menu.configure(bd=0, relief='flat', activeborderwidth=1, **colors)
        except tk.TclError:                                             # a menu PySimpleGUI has already replaced and destroyed
            return
        first_light = True
        names = [menu.entrycget(i, 'label').lstrip('✓ ') if menu.type(i) == 'command' else None for i in range(menu.index('end') + 1 if menu.index('end') is not None else 0)]
        handle_menu = "The theme's" in names                           # the Handle colour menu (its Periwinkle is not the theme)
        head_menu = HEAD_AUTO in names                                  # a heading's Colour menu (nor is its Periwinkle)
        for i, name in enumerate(names):                                # Theme menu: a color chip beside each name, light ones in a 2nd column
            if name in THEMES and not handle_menu and not head_menu:
                menu.entryconfigure(i, image=theme_swatch(window, name), compound='left')
                if first_light and is_light(THEMES[name]['card']):
                    menu.entryconfigure(i, columnbreak=1)
                    first_light = False
            elif name in HANDLE_COLORS and handle_menu:                 # Handle colour: a chip of each colour
                menu.entryconfigure(i, image=color_chip(window, HANDLE_COLORS[name] or T()['dim']), compound='left')
            elif name == HANDLE_CUSTOM and handle_menu:                 # Custom...: the colour picked there last, or a rainbow
                menu.entryconfigure(i, image=custom_chip(window), compound='left')
            elif head_menu and (name in (HEAD_AUTO, HANDLE_CUSTOM) or name in SECTION_NAMES):      # a heading's Colour: each choice as the dock shows it
                menu.entryconfigure(i, image=heading_chip(window, name), compound='left')
        for child in menu.winfo_children():
            if isinstance(child, tk.Menu):
                style(child)

    for top in menus.values():
        style(top)


def color_chip(window, color):
    """ A small rounded chip of one colour beside its name in the Handle colour menu.  Made once and kept """
    key = ('chip', color)
    if key not in G.swatches:
        z = G.dpi * 4
        im = Image.new('RGBA', (round(34 * z), round(20 * z)), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((3 * z, 5 * z, 31 * z, 15 * z), radius=5 * z, fill=color, outline=C_SWATCH_EDGE, width=round(z))
        buf = io.BytesIO()
        im.resize((round(im.width / 4), round(im.height / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[key] = sg.tk.PhotoImage(master=window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[key]


def rainbow_chip(window):
    """ A rainbow chip (any colour) - beside a Custom... that has no colour picked yet.  Made once and kept """
    key = ('chip', 'rainbow')
    if key not in G.swatches:
        import colorsys
        z = G.dpi * 4
        w, h = round(34 * z), round(20 * z)
        x0, x1 = 3 * z, 31 * z
        hues = Image.new('RGB', (w, 1))
        for x in range(w):
            r, g, b = colorsys.hsv_to_rgb(min(1.0, max(0.0, (x - x0) / (x1 - x0))) * 0.9, 0.7, 1.0)
            hues.putpixel((x, 0), (round(r * 255), round(g * 255), round(b * 255)))
        mask = Image.new('L', (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((x0, 5 * z, x1, 15 * z), radius=5 * z, fill=255)
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        im.paste(hues.resize((w, h)), (0, 0), mask)
        ImageDraw.Draw(im).rounded_rectangle((x0, 5 * z, x1, 15 * z), radius=5 * z, outline=C_SWATCH_EDGE, width=round(z))
        buf = io.BytesIO()
        im.resize((round(w / 4), round(h / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[key] = sg.tk.PhotoImage(master=window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[key]


def custom_chip(window):
    """ The chip beside Custom... in the Handle colour menu: the colour last picked there, else a rainbow (any colour) """
    return color_chip(window, G.handle_custom) if G.handle_custom else rainbow_chip(window)


def heading_chip(window, name):
    """ The chip beside a choice in a heading's Colour menu (the heading right-clicked: G.menu_target), in the colour the dock would show it:
        Automatic = the palette's colour for its place, a palette colour by name, Custom... = its own colour, or a rainbow if it has none """
    b = Block.active_blocks.get(G.menu_target)
    chosen = G.head_colors.get(b.name) if b is not None else None
    if name == HANDLE_CUSTOM:
        return color_chip(window, section_color(chosen)) if chosen and chosen not in SECTION_PALETTE else rainbow_chip(window)
    if name == HEAD_AUTO:
        heads = [o.block_num for o in Block.active_blocks.values() if o.kind == KIND_HEADING]
        n = heads.index(b.block_num) if b is not None and b.block_num in heads else 0
        return color_chip(window, section_color(SECTION_PALETTE[n % len(SECTION_PALETTE)]))
    return color_chip(window, section_color(SECTION_PALETTE[SECTION_NAMES.index(name)]))


def hex_color(value):
    """ value as a '#rrggbb' colour (lower case), or None when it isn't one """
    return value.lower() if isinstance(value, str) and re.fullmatch(r'#[0-9a-fA-F]{6}', value) else None


def pick_handle_color(window):
    """ Right-click > Handle colour > Custom...: any colour, from the colour picker - it starts at the colour last picked there (else the
        handle's colour now).  The pick becomes this dock's handle colour and its Custom... colour.  False when cancelled """
    from tkinter import colorchooser
    start = G.handle_custom or G.handle_color or T()['dim']
    try:
        rgb = colorchooser.askcolor(color=start, parent=window.TKroot, title=f'Handle colour - {G.dock_title}')[0]
    except Exception:
        rgb = None
    if not rgb:
        return False
    G.handle_color = G.handle_custom = '#{:02x}{:02x}{:02x}'.format(*(max(0, min(255, int(v))) for v in rgb[:3]))
    sg.user_settings_set_entry(K_HANDLE_COLOR, G.handle_color)
    sg.user_settings_set_entry(K_HANDLE_CUSTOM, G.handle_custom)
    return True


def theme_swatch(window, name):
    """ A little card in a theme's colours (card, a line of text, a dim line) beside its name in the Theme menu.  Made once and kept - tk drops images nobody holds """
    if (name, G.bright) not in G.swatches:                              # a set per Brightness level: the chips show what you'd get
        t, z = theme_colors(name), G.dpi * 4                            # drawn 4x and shrunk, so the edges are smooth
        im = Image.new('RGBA', (round(34 * z), round(20 * z)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=5 * z, fill=t['card'], outline=C_SWATCH_EDGE, width=round(z))
        d.rounded_rectangle((6 * z, 5.5 * z, 25 * z, 9 * z), radius=1.5 * z, fill=t['text'])
        d.rounded_rectangle((6 * z, 12 * z, 17 * z, 14.5 * z), radius=1.2 * z, fill=t['dim'])
        buf = io.BytesIO()
        im.resize((round(im.width / 4), round(im.height / 4)), Image.LANCZOS).save(buf, 'PNG')
        G.swatches[(name, G.bright)] = sg.tk.PhotoImage(master=window.TKroot, data=base64.b64encode(buf.getvalue()))
    return G.swatches[(name, G.bright)]


def load_blocks():
    Block.active_blocks = {}
    saved_blocks = G.launcher_settings.load()
    try:
        for key in saved_blocks.keys():
            if key[0] == K_NAME:
                # saved_block_num = int(key.replace('-NAME', '')[:-1])
                saved_block_num = key[1]
                block_num = G.block_number
                G.block_number += 1
                block = Block(block_num=block_num, name=saved_blocks[K_B_NAME(saved_block_num)], path=saved_blocks[K_B_PATH(saved_block_num)], iconb64=saved_blocks[K_B_ICON64(saved_block_num)],
                              kind=saved_blocks.get(K_B_KIND(saved_block_num), KIND_APP), bar=saved_blocks.get(K_B_BARVIS(saved_block_num), True))
                if is_link(block.path) and not block.iconb64.strip():  # a link typed in without an icon: the icon of the app that opens it
                    try:
                        block.iconb64 = image_to_icon_b64(link_icon_image(block.path))
                    except Exception:
                        pass
                Block.active_blocks[block_num] = block
    except Exception as e:
        sg.popup_error_with_traceback('Error loading saved blocks', e)

VERSION_LINE = re.compile(r"""^(?:VERSION|version|__version__)\s*=\s*(?:__version__\s*=\s*)?['"]v?(\d+(?:\.\d+)*)""")    # at the top level of a source


def get_version(filename):
    """ A program's version: the first  VERSION = '1.2' / __version__ = '1.2' / version = '1.2'  line at the top level of its source (not indented,
        so a version="1.0" inside a string or a function doesn't count) - or, for a pip-installed program's .exe (psgshortcut.exe), its
        package's version.  '' when there is none """
    path = filename.strip().strip('"')
    if is_link(path):
        return ''
    if path.lower().endswith(('.py', '.pyw')):
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                for n, line in enumerate(f):
                    m = VERSION_LINE.match(line)
                    if m:
                        return m.group(1)
                    if n > 2000:                                        # versions live near the top
                        break
        except OSError:
            pass
        return ''
    if path.lower().endswith('.exe'):
        return pip_script_version(os.path.splitext(re.split(r'[\\/]', path)[-1])[0])
    return ''


def pip_script_version(name):
    """ The version of the pip package whose console / gui script is name (psgshortcut, psgmain...) - '' if no installed package has one """
    if G.scripts is None:
        G.scripts = {}
        try:
            import importlib.metadata
            for dist in importlib.metadata.distributions():
                try:
                    for ep in dist.entry_points:
                        if ep.group in ('console_scripts', 'gui_scripts'):
                            G.scripts.setdefault(ep.name.lower(), dist.version)
                except Exception:
                    continue
        except Exception:
            pass
    return G.scripts.get(name.lower(), '')



def resize_canvas_no_distort_b64(b64_png: str, target_size=ICON_SIZE, fill_color=(0, 0, 0, 0)):
    """
    Decodes a base64 PNG string, pads it onto a target_size canvas without
    resizing/distorting the original image, and returns both the PIL Image
    and a new base64-encoded PNG string.
    """
    img_bytes = base64.b64decode(b64_png)
    img = Image.open(io.BytesIO(img_bytes))

    if img.mode != 'RGBA' and len(fill_color) == 4:
        img = img.convert('RGBA')

    target_w, target_h = target_size
    new_img = Image.new(img.mode, (target_w, target_h), fill_color)

    paste_x = (target_w - img.width) // 2
    paste_y = (target_h - img.height) // 2
    new_img.paste(img, (paste_x, paste_y))

    buffer = io.BytesIO()
    new_img.save(buffer, format='PNG')
    new_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return new_b64



def encode_image_base64(pil_image=None):
    """
    takes either a fjlename or a PIL image.  Image is converted
    to a base64 encoded PNG

    :param pil_image:      PIL Image object.
    :type pil_image:       PIL.Image.Image
    :return:               The base64-encoded PNG bytes of the image.
    :rtype:                bytes
    """
    # Always encode as PNG in memory
    with io.BytesIO() as bio:
        pil_image.save(bio, format="PNG")
        contents = bio.getvalue()
        encoded = base64.b64encode(contents)

    return encoded


#  ██████╗ ██████╗  ██████╗  ██████╗ ██████╗  █████╗ ███╗   ███╗███████╗    ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗    ██╗
#  ██╔══██╗██╔══██╗██╔═══██╗██╔════╝ ██╔══██╗██╔══██╗████╗ ████║██╔════╝    ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║    ██║
#  ██████╔╝██████╔╝██║   ██║██║  ███╗██████╔╝███████║██╔████╔██║███████╗    ██║ █╗ ██║██║██╔██╗ ██║██║  ██║██║   ██║██║ █╗ ██║
#  ██╔═══╝ ██╔══██╗██║   ██║██║   ██║██╔══██╗██╔══██║██║╚██╔╝██║╚════██║    ██║███╗██║██║██║╚██╗██║██║  ██║██║   ██║██║███╗██║
#  ██║     ██║  ██║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██║ ╚═╝ ██║███████║    ╚███╔███╔╝██║██║ ╚████║██████╔╝╚██████╔╝╚███╔███╔╝
#  ╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚══╝╚══╝
#
#   The Programs window - a scrollable list of "blocks", one per application, each with name / path / base64 icon.
#   Toolbar:   + Add  − Delete | ▲ Up  ▼ Down | ☑ All  ☐ None ......... Save  Reload  Clear all
#   Drop an image file anywhere on a block to make it that entry's icon (fitted to ICON_SIZE, stored as base64 PNG).
#   Keys:  Up/Down = move checked     PgUp/PgDn = scroll a page     Home/End = top/bottom     Ctrl+S = save     Escape = close

SCROLLABLE_COLUMN_SIZE = (None, 800)
FRAME_BORDER_COLOR_NOT_SELECTED = 'gray30'
FRAME_BORDER_COLOR_SELECTED = 'chartreuse'
DRAG_SOURCE_COLOR = '#1E88E5'                                                   # the entry being dragged
DRAG_TARGET_COLOR = '#FFA726'                                                   # outline of the floating copy while dragging


def blend(color, toward, amount):
    """ Mix a colour toward another ('#rrggbb' or a tk colour name) - used to derive the drop-slot shade from the theme background """
    import tkinter as tk
    root = tk._default_root
    def rgb(c):
        r, g, b = root.winfo_rgb(c)
        return r // 256, g // 256, b // 256
    a, b = rgb(color), rgb(toward)
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def slot_colors():
    """ (fill, outline) for the drop slot: a lighter shade of the theme background, outlined faintly in the theme's text colour """
    bg = sg.theme_background_color()
    return blend(bg, 'black' if T().get('light') else 'white', 0.07 if T().get('light') else 0.18), blend(bg, sg.theme_text_color(), 0.45)
DRAG_START = 6                                                                  # pixels the mouse moves before a press on the grip becomes a drag
AUTOSCROLL_EDGE = 50                                                            # dragging within this many pixels of the list's top/bottom scrolls it
AUTOSCROLL_MS = 25                                                              # auto-scroll tick while the pointer is in that edge zone
AUTOSCROLL_MIN_PX, AUTOSCROLL_MAX_PX = 2.5, 10                                  # pixels per tick inside the zone - slow at its inner side, faster at the very edge
AUTOSCROLL_PAST, AUTOSCROLL_PAST_PX = 120, 32                                   # the mouse past the list's edge: up to this much further = up to this many more per tick
AUTOSCROLL_RAMP = 1.5                                                           # held in the zone for this many seconds: it scrolls twice as fast
                                                                                # (all three in 96-dpi pixels - multiplied by the display scaling, G.dpi)
FILENAME_INPUT_LENGTH = 80

# Toolbar colours - green = safe/save, gold = unsaved changes, red = destructive
COLOR_SAVE = 'white on #2e7d32'
COLOR_SAVE_DIRTY = 'black on #ffc107'
COLOR_DANGER = 'white on #b71c1c'
COLOR_DIRTY_TEXT = '#ffc107'

# Keys saved in the settings file (one set per application, numbered)
K_BLOCK = '-BLOCK-'
K_B_BLOCK = lambda num: (K_BLOCK, num)
K_ICON64 = '-ICON64-'
K_B_ICON64 = lambda num:  (K_ICON64, num)
K_ICON = '-ICON-'
K_B_ICON = lambda num: (K_ICON, num)
K_NAME = '-NAME-'
K_B_NAME = lambda num:  (K_NAME, num)
K_PATH = '-PATH-'
K_B_PATH = lambda num: (K_PATH, num)
K_KIND = '-KIND-'                               # saved: 'app' or 'heading' (missing = app, so older settings files load unchanged)
K_B_KIND = lambda num: (K_KIND, num)
K_BARVIS = '-IN BAR-'                           # saved: False = left out of the Bar style (missing = shown)
K_B_BARVIS = lambda num: (K_BARVIS, num)
K_DETAILS = '-DETAILS-'                         # the path + icon rows of an entry - hidden for a heading
K_B_DETAILS = lambda num: (K_DETAILS, num)
K_COLUMN = '-COLUMN-'
K_B_COLUMN = lambda num: (K_COLUMN, num)        # Column elem containing the block's elements. Not used

# Programs window keys
K_ALL_COLS = '-ALL COLS-'
K_MOVE_UP = '-MOVE UP-'
K_MOVE_DOWN = '-MOVE DOWN-'
K_PAGE_UP = '-PAGE UP-'
K_PAGE_DOWN = '-PAGE DOWN-'
K_HOME = '-HOME-'
K_END = '-END-'
K_ESCAPE = '-ESCAPE-'
K_OK = '-OK-'
K_APPLY = '-APPLY-'
K_CANCEL = '-CANCEL-'
K_SEL_ALL = '-SELECT ALL-'
K_ADD_HEADING = '-ADD HEADING-'
K_SEL_NONE = '-SELECT NONE-'
K_STATUS = '-STATUS-'
K_GRIP = '-GRIP-'                               # the ☰ drag handle on each block
K_B_GRIP = lambda num: (K_GRIP, num)
K_DRAG_PRESS = '-DRAG PRESS-'                   # events from the grip's mouse bindings, value = (block_num, x_root, y_root)
K_DRAG_MOTION = '-DRAG MOTION-'
K_DRAG_RELEASE = '-DRAG RELEASE-'


def image_to_icon_b64(img, size=None) -> str:
    """ Fit a PIL image into a square transparent PNG (aspect kept, centered) - at most ICON_STORE pixels and never enlarged, so icons stay sharp
        when the dock shows them big - and return its base64 as the b'...' string the Base64 PNG Icon field expects (same format as the settings) """
    img = img.convert('RGBA')
    side = size[0] if size else min(ICON_STORE, max(img.size))
    img.thumbnail((side, side), Image.LANCZOS)
    canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    with io.BytesIO() as bio:
        canvas.save(bio, format='PNG')
        return repr(base64.b64encode(bio.getvalue()))


def image_file_to_icon_b64(filename, size=None) -> str:
    """ Load an image file and return it as a fitted base64 PNG icon string """
    return image_to_icon_b64(Image.open(filename), size)


IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.webp', '.tif', '.tiff')


# ------------------------------------------------------------ Getting an icon out of a program ------------------------------------------------------------

PNG_START = re.compile(r"""b(['"])iVBORw0KGgo""")                  # where a base64 PNG literal begins
B64_PIECE = re.compile(r"""b(['"])([A-Za-z0-9+/=\s]*)\1""")       # one bytes literal of base64
PIECE_GAP = re.compile(r"""(?:[\s,]|#[^\n]*)*""")                  # what may sit between the pieces of a split icon


def base64_pngs_in_source(source):
    """ (position, base64) for every PNG in the source written as a bytes literal - on one line, or split over several lines the way
        icon makers write them:  b''.join((b'iVBOR...', b'...'))  or  (b'iVBOR...' b'...').  The pieces are joined while only whitespace,
        commas and comments sit between them; a piece that starts with a new PNG header starts a new image """
    found = []
    for m in PNG_START.finditer(source):
        pieces, pos = [], m.start()
        while True:
            piece = B64_PIECE.match(source, pos)
            if not piece:
                break
            pieces.append(piece.group(2))
            pos = PIECE_GAP.match(source, piece.end()).end()
            if not source.startswith(('b"', "b'"), pos) or PNG_START.match(source, pos):
                break
        found.append((m.start(), ''.join(''.join(pieces).split())))
        if len(found) >= 40:
            break
    return found


def icon_from_python_source(filename):
    """ PySimpleGUI programs usually carry their icon as a base64 PNG in the source (window_icon(), launcher_icon = b'...', etc).
        Returns the first one found as a PIL image (one whose name mentions "icon" is preferred), or None """
    try:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
    except Exception:
        return None
    widget_words = ('trash', 'arrow', 'refresh', 'blank', 'button', 'check', 'close', 'cursor')      # small images that are toolbar bits, not the program's icon
    best, best_score = None, None
    for start, b64 in base64_pngs_in_source(source):
        before = source[max(0, start - 60):start].lower()
        line_start = source.rfind('\n', 0, start) + 1
        if not source[line_start:start].strip():                       # a split icon's pieces start their own lines - its name is on the line above
            before = source[source.rfind('\n', 0, max(0, line_start - 1)) + 1:line_start].lower() + before
        try:
            img = Image.open(io.BytesIO(base64.b64decode(b64)))
            img.load()
        except Exception:
            continue
        score = ('icon' in before and not any(w in before for w in widget_words), img.width * img.height)      # icon-named first, then the biggest
        if best_score is None or score > best_score:
            best, best_score = img, score
    return best


def resolve_shortcut(filename):
    """ Path a Windows .lnk shortcut points at (via the shell if pywin32 is installed, else a minimal parse of the .lnk file). Returns the .lnk itself if it can't be resolved """
    try:
        import win32com.client                                  # pywin32 - optional
        target = win32com.client.Dispatch('WScript.Shell').CreateShortCut(filename).TargetPath
        if target and os.path.exists(target):
            return target
    except Exception:
        pass
    try:                                                        # minimal .lnk parse: LinkInfo -> LocalBasePath   (MS-SHLLINK)
        with open(filename, 'rb') as f:
            data = f.read()
        flags = struct.unpack_from('<I', data, 0x14)[0]
        pos = 0x4C
        if flags & 0x01:                                        # HasLinkTargetIDList
            pos += 2 + struct.unpack_from('<H', data, pos)[0]
        if flags & 0x02:                                        # HasLinkInfo
            link_info_size, header_size, link_flags = struct.unpack_from('<III', data, pos)
            if link_flags & 0x01:                               # VolumeIDAndLocalBasePath
                if header_size >= 0x24:                         # unicode path offset present
                    off = struct.unpack_from('<I', data, pos + 0x1C)[0]
                    end = data.index(b'\x00\x00', pos + off)
                    end += (end - pos - off) % 2
                    target = data[pos + off:end].decode('utf-16-le', errors='ignore')
                else:
                    off = struct.unpack_from('<I', data, pos + 0x10)[0]
                    target = data[pos + off:data.index(b'\x00', pos + off)].decode('mbcs' if sys.platform == 'win32' else 'latin-1', errors='ignore')
                if target and os.path.exists(target):
                    return target
    except Exception:
        pass
    return filename


def hicon_to_image(hicon):
    """ Windows HICON -> PIL RGBA image (alpha kept), ctypes only.  Returns None if anything goes wrong """
    import ctypes
    from ctypes import wintypes
    user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32

    class ICONINFO(ctypes.Structure):
        _fields_ = [('fIcon', wintypes.BOOL), ('xHotspot', wintypes.DWORD), ('yHotspot', wintypes.DWORD), ('hbmMask', wintypes.HBITMAP), ('hbmColor', wintypes.HBITMAP)]

    class BITMAP(ctypes.Structure):
        _fields_ = [('bmType', wintypes.LONG), ('bmWidth', wintypes.LONG), ('bmHeight', wintypes.LONG), ('bmWidthBytes', wintypes.LONG), ('bmPlanes', wintypes.WORD), ('bmBitsPixel', wintypes.WORD), ('bmBits', wintypes.LPVOID)]

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG), ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG), ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [('bmiHeader', BITMAPINFOHEADER), ('bmiColors', wintypes.DWORD * 3)]

    user32.GetIconInfo.argtypes = [wintypes.HICON, ctypes.POINTER(ICONINFO)]
    user32.GetDC.restype = wintypes.HDC
    user32.GetDC.argtypes = [wintypes.HWND]
    user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
    gdi32.GetObjectW.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID]
    gdi32.GetDIBits.argtypes = [wintypes.HDC, wintypes.HBITMAP, wintypes.UINT, wintypes.UINT, wintypes.LPVOID, ctypes.POINTER(BITMAPINFO), wintypes.UINT]
    gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]

    def bitmap_pixels(hbitmap):
        """ 32-bit BGRA pixels of a bitmap, top-down.  Returns (width, height, bytes) """
        bm = BITMAP()
        gdi32.GetObjectW(hbitmap, ctypes.sizeof(BITMAP), ctypes.pointer(bm))
        w, h = bm.bmWidth, bm.bmHeight
        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth, bmi.bmiHeader.biHeight, bmi.bmiHeader.biPlanes, bmi.bmiHeader.biBitCount, bmi.bmiHeader.biCompression = w, -h, 1, 32, 0
        buf = ctypes.create_string_buffer(w * h * 4)
        hdc = user32.GetDC(None)
        try:
            lines = gdi32.GetDIBits(hdc, hbitmap, 0, h, buf, ctypes.byref(bmi), 0)
        finally:
            user32.ReleaseDC(None, hdc)
        return (w, h, buf.raw) if lines else (0, 0, b'')

    info = ICONINFO()
    if not user32.GetIconInfo(hicon, ctypes.byref(info)):
        return None
    try:
        if not info.hbmColor:
            return None
        w, h, pixels = bitmap_pixels(info.hbmColor)
        if not w:
            return None
        img = Image.frombuffer('RGBA', (w, h), pixels, 'raw', 'BGRA', 0, 1).copy()
        if not any(img.getdata(band=3)):                        # no alpha channel in this icon -> build it from the AND mask (white = transparent)
            mw, mh, mpixels = bitmap_pixels(info.hbmMask)
            if mw == w and mh >= h:
                mask = Image.frombuffer('L', (w, h), mpixels[:w * h * 4:4], 'raw', 'L', 0, 1).point(lambda v: 0 if v else 255)
                img.putalpha(mask)
        return img
    finally:
        gdi32.DeleteObject(info.hbmColor)
        gdi32.DeleteObject(info.hbmMask)


def big_file_icon(filename, size=256):
    """ An exe's / dll's / ico's own icon at up to size pixels (PrivateExtractIconsW) as a PIL image, or None """
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    user32.PrivateExtractIconsW.restype = wintypes.UINT
    user32.PrivateExtractIconsW.argtypes = [wintypes.LPCWSTR, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(wintypes.HICON), ctypes.POINTER(wintypes.UINT), wintypes.UINT, wintypes.UINT]
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    hicon, icon_id = wintypes.HICON(), wintypes.UINT()
    count = user32.PrivateExtractIconsW(filename, 0, size, size, ctypes.byref(hicon), ctypes.byref(icon_id), 1, 0)
    if count in (0, 0xFFFFFFFF) or not hicon:
        return None
    try:
        return hicon_to_image(hicon)
    finally:
        user32.DestroyIcon(hicon)


def shell_icon_image(filename):
    """ The icon Windows Explorer shows for a file (exe, document, shortcut...) as a PIL image, or None.  Programs give their big icon """
    if sys.platform != 'win32':
        return None
    if os.path.splitext(filename)[1].lower() in ('.exe', '.dll', '.ico', '.cpl', '.scr'):
        try:
            img = big_file_icon(filename)
            if img is not None:
                return img
        except Exception:
            pass
    import ctypes
    from ctypes import wintypes

    class SHFILEINFOW(ctypes.Structure):
        _fields_ = [('hIcon', wintypes.HICON), ('iIcon', ctypes.c_int), ('dwAttributes', wintypes.DWORD), ('szDisplayName', wintypes.WCHAR * 260), ('szTypeName', wintypes.WCHAR * 80)]

    SHGFI_ICON, SHGFI_LARGEICON = 0x100, 0x0
    shell32, user32 = ctypes.windll.shell32, ctypes.windll.user32
    shell32.SHGetFileInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(SHFILEINFOW), wintypes.UINT, wintypes.UINT]
    shell32.SHGetFileInfoW.restype = ctypes.c_void_p
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    ctypes.windll.ole32.CoInitialize(None)                      # shortcuts need COM
    info = SHFILEINFOW()
    if not shell32.SHGetFileInfoW(filename, 0, ctypes.byref(info), ctypes.sizeof(info), SHGFI_ICON | SHGFI_LARGEICON) or not info.hIcon:
        return None
    try:
        return hicon_to_image(info.hIcon)
    finally:
        user32.DestroyIcon(info.hIcon)


def playground_catalog_icon(filename):
    """ A PySimpleGUI Playground program: its icon from the Playground's catalog.json and icons folder (a few folders up), or None """
    folder = os.path.dirname(os.path.abspath(filename))
    for _ in range(4):
        catalog = os.path.join(folder, 'catalog.json')
        if os.path.isfile(catalog):
            try:
                with open(catalog, encoding='utf-8') as f:
                    apps = json.load(f).get('apps', [])
                name = os.path.basename(filename).lower()
                app = next((a for a in apps if (a.get('file') or '').lower() == name and a.get('icon')), None)
                if app:
                    img = Image.open(os.path.join(folder, 'icons', app['icon']))
                    img.load()
                    return img
            except Exception:
                pass
            return None
        folder, below = os.path.dirname(folder), folder
        if folder == below:
            break
    return None


def icon_file_beside(filename):
    """ A picture next to the program named after it: x.png, x_icon.png, x.ico or x_icon.ico for x.pyw """
    stem = os.path.splitext(filename)[0]
    for candidate in (stem + '.png', stem + '_icon.png', stem + '.ico', stem + '_icon.ico'):
        if os.path.isfile(candidate):
            try:
                img = Image.open(candidate)
                img.load()
                return img
            except Exception:
                pass
    return None


def program_icon_image(filename, fallback=True):
    """ Best icon for a program file as a PIL image, or None.
        .py/.pyw -> a base64 PNG embedded in the source, else its icon in the Playground's catalog, else a picture beside it named after it, else
                    the Python interpreter's icon (Windows) or PySimpleGUI's (Linux / Mac have no program icons to ask the system for).
        .lnk -> the target's icon.   A link -> the icon of the app that opens it.   else -> the shell icon """
    if is_link(filename):
        return link_icon_image(filename)
    ext = os.path.splitext(filename)[1].lower()
    if ext in ('.py', '.pyw'):
        for find in (icon_from_python_source, playground_catalog_icon, icon_file_beside):
            img = find(filename)
            if img is not None:
                return img
        if not fallback:                                                # Sharper icon: only the program's own icon, never the logo below
            return None
        if sys.platform == 'win32':
            return shell_icon_image(sys.executable)
        return Image.open(io.BytesIO(base64.b64decode(sg.DEFAULT_BASE64_ICON)))
    if not fallback and ext not in ('.exe', '.dll', '.ico', '.cpl', '.scr'):     # a document / script: Windows would give its generic file icon
        return None
    return shell_icon_image(filename)


def clean_path(text):
    """ A path as typed, pasted or dropped: spaces, quotes and braces off its ends; a file:// URI (Linux file managers paste and drop those)
        made into a plain path """
    path = text.strip().strip('"\'{}').strip()
    if path.lower().startswith('file://'):
        path = urllib.parse.unquote(urllib.parse.urlparse(path).path)
        if sys.platform == 'win32' and re.match(r'/[A-Za-z]:', path):                  # file:///C:/x.pyw -> C:/x.pyw
            path = path[1:]
    return path


def icon_for_typed_path(window:sg.Window, block_num, text):
    """ A path typed or pasted into an entry (or one already saved without an icon): once it names a program that exists, the path is cleaned up,
        the name filled in if it's empty and the program's icon pulled out - what a drop does.  An icon you dropped, pasted or saved yourself is
        kept; one pulled from an earlier path is replaced.  Returns True when an icon was put in """
    block = Block.active_blocks[block_num]
    path = clean_path(text) if not is_link(text.strip()) or text.strip().lower().startswith('file://') else text.strip()
    link = is_link(path)
    if link and (len(path) < 10 or path.lower() in ('https://', 'http://', 'claude://')):     # a link still being typed
        return False
    if not link and os.path.splitext(path)[1].lower() == '.lnk':
        path = resolve_shortcut(path)
    if not link and (not os.path.isfile(path) or os.path.splitext(path)[1].lower() in IMAGE_EXTENSIONS):
        return False
    if path != text:
        window[K_B_PATH(block_num)].update(path)
    block.path = path
    if not block.name.strip():
        block.name = link_name(path) if link else os.path.splitext(os.path.basename(path))[0].replace('_', ' ')
        window[K_B_NAME(block_num)].update(block.name)
    if (block.iconb64.strip() and block_num not in G.auto_icon) or G.auto_icon.get(block_num) == path:
        return False
    try:
        img = program_icon_image(path)
    except Exception:
        img = None
    if img is None:
        return False
    icon_string = image_to_icon_b64(img)
    window[K_B_ICON64(block_num)].update(icon_string)
    window[K_B_ICON(block_num)].update(data=ui_icon(ast.literal_eval(icon_string)))
    block.iconb64 = icon_string
    G.auto_icon[block_num] = path
    return True


def fill_block_from_dropped_file(window:sg.Window, block_num, filename):
    """ A file was dropped on a block.  Image -> just the icon.  Program -> path, name (if empty) and the program's icon. """
    block = Block.active_blocks[block_num]
    ext = os.path.splitext(filename)[1].lower()
    if ext in IMAGE_EXTENSIONS:
        icon_string = image_file_to_icon_b64(filename)
        G.auto_icon.pop(block_num, None)                        # a picture you chose - a path typed later won't replace it
    else:
        if ext == '.lnk':
            filename = resolve_shortcut(filename)
        block.path = filename
        window[K_B_PATH(block_num)].update(filename)
        if not block.name.strip():
            block.name = os.path.splitext(os.path.basename(filename))[0].replace('_', ' ')
            window[K_B_NAME(block_num)].update(block.name)
        try:
            img = program_icon_image(filename)
        except Exception as e:
            print(f'Icon extraction failed for {filename}: {e}')
            img = None
        if img is None:
            return                                              # path/name are filled in - the icon can still be dropped or pasted
        icon_string = image_to_icon_b64(img)
        G.auto_icon[block_num] = filename
    window[K_B_ICON64(block_num)].update(icon_string)
    window[K_B_ICON(block_num)].update(data=ui_icon(ast.literal_eval(icon_string)))
    block.iconb64 = icon_string


# ------------------------------------------------------------ Blocks (one per application) ------------------------------------------------------------

def make_a_block(image=None) -> sg.Frame:
    block_num = G.block_number
    Block.active_blocks[G.block_number] = Block(block_num=G.block_number, name='', path='', iconb64='')
    G.block_number += 1

    block_layout = [[sg.T('☰', k=K_B_GRIP(block_num), font='_ 14', text_color=T()['dim'], p=((2, 6), 0), tooltip='Drag to change the order'), sg.Image(data=image, k=K_B_ICON(block_num), enable_events=True, p=0, tooltip='Drop the program here (path, name and icon fill in) or an image file (icon only)'), sg.Push(), sg.Input(k=K_B_NAME(block_num), justification='c',enable_events=True, placeholder='Application name', placeholder_justification='c', placeholder_background_color=sg.theme_input_background_color(), font='_ 12 bold', s=FILENAME_INPUT_LENGTH-20, p=0), sg.Checkbox('', k=K_B_CBOX(block_num), enable_events=True, tooltip='Check to delete, or to choose where + Add / + Heading put the new entry'), sg.B(image_source=ui_icon(trash), mouseover_image_source=ui_icon(trash_red), button_color=f'red on {sg.theme_background_color()}', border_width=0, k=K_B_DEL(block_num), tooltip='Delete this entry')],
                   [sg.pin(sg.Column([[sg.Input(k=K_B_PATH(block_num), justification='r', enable_events=True,  placeholder='Path to application', placeholder_background_color=sg.theme_input_background_color(), placeholder_justification='c', p=0, s=FILENAME_INPUT_LENGTH)],
                                      [sg.Input(k=K_B_ICON64(block_num), justification='r', change_submits=True, placeholder='Base64 PNG Icon   (or drop the program / an image file on this entry)', placeholder_justification='c', placeholder_background_color=sg.theme_input_background_color(), p=0, s=FILENAME_INPUT_LENGTH)]], k=K_B_DETAILS(block_num), pad=0), shrink=True)],
                    ]

    block =sg.Frame('', [[sg.Column(block_layout, k=K_B_COLUMN(block_num), expand_x=False, pad=0 )]], k=K_B_BLOCK(block_num), border_width_no_relief=3, border_color=FRAME_BORDER_COLOR_NOT_SELECTED, expand_x=True, p=0)
    return block


def add_block(window):
    window.extend_layout(window[K_ALL_COLS], [[make_a_block()]])
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()
    block_num = G.block_number - 1
    for key in (K_B_BLOCK(block_num), K_B_ICON(block_num), K_B_ICON64(block_num)):          # drop an image file anywhere on the block
        psgdnd.register_element_dnd(window[key], window, psgdnd.DROP_TYPE_FILES)
    grip = window[K_B_GRIP(block_num)].Widget
    def grip_event(key, n):                                # 'break' stops the window's grab_anywhere binding from also dragging the window
        def handler(e):
            window.write_event_value(key, (n, e.x_root, e.y_root))
            return 'break'
        return handler
    grip.bind('<ButtonPress-1>', grip_event(K_DRAG_PRESS, block_num))
    grip.bind('<B1-Motion>', grip_event(K_DRAG_MOTION, block_num))
    grip.bind('<ButtonRelease-1>', grip_event(K_DRAG_RELEASE, block_num))
    grip.configure(cursor='hand2')

    return  block_num


def del_block(window, block_num):
    try:
        block_to_delete = int(block_num)
        key_to_delete = K_B_BLOCK(block_to_delete)
    except Exception:
        return None
    if key_to_delete in window.key_dict.keys():
        del_an_elem(window, window[key_to_delete])
        window.refresh()
        window[K_ALL_COLS].contents_changed()
    try:
        del Block.active_blocks[block_to_delete]
    except Exception as e:
        sg.popup_error_with_traceback(f'Error deleting block {block_to_delete}', e)

    return key_to_delete


def del_all_blocks(window:sg.Window):
    for key in list(Block.active_blocks.keys()):
        del_block(window, key)


def del_checked_blocks(window:sg.Window):
    for key in list(Block.active_blocks.keys()):
        if window[K_B_CBOX(key)].get():
            del_block(window, key)


def check_all_blocks(window:sg.Window, checked):
    for key in Block.active_blocks:
        window[K_B_CBOX(key)].update(checked)
        set_block_border(window, key)


def num_checked_blocks(window:sg.Window):
    return sum(1 for key in Block.active_blocks if window[K_B_CBOX(key)].get())


def update_status(window:sg.Window):
    """ Refresh the status bar and the Save button colour (gold = unsaved changes) """
    headings = sum(1 for b in Block.active_blocks.values() if b.kind == KIND_HEADING)
    num = len(Block.active_blocks) - headings
    state = 'UNSAVED CHANGES' if G.dirty else 'saved'
    window[K_STATUS].update(f'{num} application{"s" if num != 1 else ""}  ·  {headings} heading{"s" if headings != 1 else ""}  ·  {num_checked_blocks(window)} checked  ·  {state}',
                            text_color=COLOR_DIRTY_TEXT if G.dirty else sg.theme_text_color())
    window[K_APPLY].update(button_color=COLOR_SAVE_DIRTY if G.dirty else sg.theme_button_color())


def name_style(elem:sg.Input, heading):
    """ (text colour, background colour, font) for an entry's name field - a heading's is left-aligned, theme-coloured text on the window
        background so it reads as a heading.  Also sets the field's placeholder text and justification to match. """
    if not hasattr(elem, 'app_style'):                                  # remember how an application entry's name field looks, to switch back
        elem.app_style = (elem.placeholder, elem.TextColor, elem.BackgroundColor, elem.tk_justify, elem.Widget.cget('font'))
    placeholder, text_color, background_color, justify, font = elem.app_style
    if heading:                                                         # same font and width, so the check boxes and trash cans stay lined up
        placeholder, text_color, background_color, justify = 'Heading name', T()['heading'], sg.theme_background_color(), 'left'
    elem.placeholder, elem.tk_justify = placeholder, justify
    return text_color, background_color, font


def update_block_elements(window:sg.Window, b:Block):
    heading = b.kind == KIND_HEADING
    name_elem = window[K_B_NAME(b.block_num)]
    text_color, background_color, font = name_style(name_elem, heading)
    name_elem.update(b.name, text_color=text_color, background_color=background_color, font=font)
    window[K_B_DETAILS(b.block_num)].update(visible=not heading)        # a heading has no path or icon
    window[K_B_PATH(b.block_num)].update(b.path)
    window[K_B_ICON64(b.block_num)].update(b.iconb64)
    try:
        base64_icon = ast.literal_eval(b.iconb64) if b.iconb64 else None
    except:
        base64_icon = None
    if heading or base64_icon is None:
        base64_icon = blank_image_30x30                                 # an empty 30x30 keeps a heading's (or an icon-less program's) row as wide as the others
    window[K_B_ICON(b.block_num)].update(ui_icon(base64_icon))


def move_blocks(window:sg.Window, move_up=True):
    block_keys_to_move = [key for key in Block.active_blocks.keys() if window[K_B_CBOX(key)].get()]
    prev_key = None
    keys = Block.active_blocks.keys() if move_up else reversed(Block.active_blocks.keys())
    for key in keys:
        value = Block.active_blocks[key]
        if key in block_keys_to_move:
            if prev_key is not None:            # if can move higher
                b = Block.active_blocks[prev_key]
                prev_cb = window[K_B_CBOX(prev_key)].get()
                # Swap the blocks values except for the block number (this will automatically renumber the items)
                b.name, value.name = value.name, b.name
                b.path, value.path = value.path, b.path
                b.iconb64, value.iconb64 = value.iconb64, b.iconb64
                update_block_elements(window, b)
                update_block_elements(window, value)
                window[K_B_CBOX(b.block_num)].update(True)                # Set checkbox on the item moved up
                window[K_B_CBOX(value.block_num)].update(prev_cb)         # Copy over the checkbox value when moving
                prev_key = value.block_num
        else:
            prev_key = key
    first_checked_block_position = None
    last_checked_blocked_position = None
    for position, key in enumerate(Block.active_blocks.keys()):
        block_num = Block.active_blocks[key].block_num
        if window[K_B_CBOX(block_num)].get():
            window[K_B_BLOCK(block_num)].update(border_color=FRAME_BORDER_COLOR_SELECTED)
            if first_checked_block_position is None:
                last_checked_blocked_position = position
            first_checked_block_position = position
        else:
            window[K_B_BLOCK(block_num)].update(border_color=FRAME_BORDER_COLOR_NOT_SELECTED)

    if last_checked_blocked_position is not None:
        desired_visible_area_start = last_checked_blocked_position/len(Block.active_blocks.keys())
        top_fraction, bottom_fraction = window[K_ALL_COLS].widget.canvas.yview()
        if not top_fraction < desired_visible_area_start < bottom_fraction:
            window[K_ALL_COLS].set_vscroll_position(desired_visible_area_start)

    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()


# ------------------------------------------------------------ Programs window load / save ------------------------------------------------------------

# ------------------------------------------------------------ Drag to reorder ------------------------------------------------------------

def drag_lift(window:sg.Window, drag, y_root):
    """ The press has become a drag: lift the entry out of the list as a floating copy that follows the mouse, and leave an orange slot where it was """
    tk = sg.tk
    src_row = window[K_B_BLOCK(drag['src'])].Widget.master                  # the row frame PySimpleGUI packed the block into
    parent = src_row.master
    siblings = parent.pack_slaves()
    drag['row'], drag['parent'] = src_row, parent
    drag['next_row'] = siblings[siblings.index(src_row) + 1] if siblings.index(src_row) + 1 < len(siblings) else None
    info = src_row.pack_info()
    info.pop('in', None)
    drag['pack_info'] = info
    drag['pads'] = {'padx': info.get('padx', 0), 'pady': info.get('pady', 0)}
    w, h = src_row.winfo_width(), src_row.winfo_height()
    drag['grab_dy'] = y_root - src_row.winfo_rooty()
    drag['x'] = src_row.winfo_rootx()
    fill, outline = slot_colors()
    gap = tk.Frame(parent, width=w, height=h, bg=fill, highlightthickness=2, highlightbackground=outline, highlightcolor=outline)      # the slot the entry will land in - starts where it was
    gap.pack_propagate(False)
    gap.pack(before=src_row, fill='x', **drag['pads'])
    window.grab_any_where_off()                                             # the window stays put while an entry is dragged (back on at the drop)
    src_row.pack_forget()
    drag['gap'], drag['index'] = gap, None
    b = Block.active_blocks[drag['src']]
    top = tk.Toplevel(window.TKroot)                                        # the floating copy
    top.overrideredirect(True)
    top.attributes('-topmost', True)
    try:
        top.attributes('-alpha', 0.9)
    except tk.TclError:
        pass
    icon = window[K_B_ICON(drag['src'])].Widget.cget('image')
    bg, fg, field_bg, field_fg = sg.theme_background_color(), sg.theme_text_color(), sg.theme_input_background_color(), sg.theme_input_text_color()
    body = tk.Frame(top, bg=bg, highlightthickness=3, highlightbackground=DRAG_TARGET_COLOR, highlightcolor=DRAG_TARGET_COLOR)      # a replica of the entry with an orange outline
    body.pack(fill='both', expand=True)
    row1 = tk.Frame(body, bg=bg)
    row1.pack(fill='x', padx=4, pady=(3, 0))
    (tk.Label(row1, image=icon, bg=bg, width=round(30 * G.dpi), height=round(30 * G.dpi)) if icon else tk.Label(row1, text='   ', bg=bg)).pack(side='left')      # pixels with an image, characters without
    if b.kind == KIND_HEADING:                                              # a heading: just its name, styled like it is in the list
        tk.Label(row1, text=b.name.strip() or '(heading)', bg=bg, fg=fg, font=('Helvetica', 12, 'bold'), anchor='w').pack(side='left', fill='x', expand=True, padx=(8, 0), pady=(0, 3))
    else:
        tk.Label(row1, text=b.name.strip() or '(no name)', bg=field_bg, fg=field_fg, font=('Helvetica', 12, 'bold')).pack(side='left', fill='x', expand=True, padx=(8, 0))
        tk.Label(body, text=b.path, bg=field_bg, fg=field_fg, anchor='e', font=('Helvetica', 9)).pack(fill='x', padx=4, pady=2)
        tk.Label(body, text=(b.iconb64[:90] + '…') if len(b.iconb64) > 90 else (b.iconb64 or 'Base64 PNG Icon'), bg=field_bg, fg=field_fg, anchor='w', font=('Helvetica', 9)).pack(fill='x', padx=4, pady=(0, 3))
    top.update_idletasks()
    top.geometry(f'{w}x{body.winfo_reqheight()}+{drag["x"]}+{y_root - drag["grab_dy"]}')       # as wide as the entry, as tall as the replica needs
    drag['top'] = top
    n = drag['src']                                                         # the copy sits under the pointer, so it may get the mouse events instead of the grip
    top.bind('<B1-Motion>', lambda e: window.write_event_value(K_DRAG_MOTION, (n, e.x_root, e.y_root)))
    top.bind('<ButtonRelease-1>', lambda e: window.write_event_value(K_DRAG_RELEASE, (n, e.x_root, e.y_root)))
    for seq in ('<MouseWheel>', '<Button-4>', '<Button-5>'):                # the wheel scrolls the list while an entry is dragged (Windows / Linux)
        top.bind(seq, lambda e: wheel_while_dragging(window, drag, e))
    try:                                                                    # Linux: unmapping the grip's row ended its hold on the mouse, so the moves went to the
        top.update()                                                        # window instead (it jumped away, and the drop was lost) - the copy takes every mouse event
        top.grab_set()
    except tk.TclError:
        pass
    window.set_cursor('fleur')
    drag_motion(window, drag, drag['x'], y_root)


def drag_motion(window:sg.Window, drag, x_root, y_root):
    """ Every mouse movement while the grip is held: move the floating copy, move the slot to where the entry would land, scroll near the edges """
    if not drag['moved']:
        if abs(y_root - drag['y']) < DRAG_START:
            return
        drag['moved'] = True
        drag_lift(window, drag, y_root)
        return
    column = window[K_ALL_COLS].widget
    low, high = column.winfo_rooty(), column.winfo_rooty() + column.winfo_height() - drag['top'].winfo_height()
    drag['top'].geometry(f'+{drag["x"]}+{min(max(y_root - drag["grab_dy"], low), high)}')         # the copy never leaves the list area
    drag['pointer_y'] = y_root
    if autoscroll_speed(window, y_root) and drag.get('after') is None:      # in the edge zone: start the scroll timer (it stops itself)
        autoscroll_tick(window, drag)
    move_slot(window, drag, y_root)


def autoscroll_speed(window:sg.Window, y_root):
    """ Pixels to scroll per tick for a pointer at y_root: 0 away from the edges, negative = up.  Gets faster the deeper into the edge zone,
        much faster with the mouse past the list's edge, and up to twice as fast once it has been held there AUTOSCROLL_RAMP seconds """
    column = window[K_ALL_COLS].widget
    top, bottom = column.winfo_rooty(), column.winfo_rooty() + column.winfo_height()
    edge, past = AUTOSCROLL_EDGE * G.dpi, AUTOSCROLL_PAST * G.dpi       # the list is drawn G.dpi times bigger on a scaled display
    if y_root < top + edge:
        depth, direction = top + edge - y_root, -1
    elif y_root > bottom - edge:
        depth, direction = y_root - (bottom - edge), 1
    else:
        return 0
    inside, beyond = min(1.0, depth / edge), min(1.0, max(0.0, depth - edge) / past)
    held = time.time() - G.scroll_since if G.scroll_since else 0
    ramp = 1 + min(1.0, held / AUTOSCROLL_RAMP)
    return direction * ((AUTOSCROLL_MIN_PX + (AUTOSCROLL_MAX_PX - AUTOSCROLL_MIN_PX) * inside ** 2) * ramp + AUTOSCROLL_PAST_PX * beyond) * G.dpi


def autoscroll_tick(window:sg.Window, drag):
    """ Timer: scroll the list a few pixels while the pointer stays near its top/bottom edge, moving the slot along with it """
    drag['after'] = None
    if drag.get('done'):
        return
    G.scroll_since = G.scroll_since or time.time()                      # how long it has been held in the edge zone - it speeds up
    speed = autoscroll_speed(window, drag['pointer_y'])
    if not speed:
        G.scroll_since = None
        return
    column = window[K_ALL_COLS].widget
    first = column.canvas.yview()[0]
    column.canvas.yview_moveto(first + speed / max(1, column.TKFrame.winfo_height()))
    move_slot(window, drag, drag['pointer_y'])
    drag['after'] = window.TKroot.after(AUTOSCROLL_MS, lambda: autoscroll_tick(window, drag))


def wheel_while_dragging(window:sg.Window, drag, e):
    """ The mouse wheel turned while an entry is dragged: scroll the list (3 lines a notch) and move the slot along """
    if drag.get('done'):
        return
    notches = (e.delta / 120 if e.delta else 0) or (1 if getattr(e, 'num', 0) == 4 else -1 if getattr(e, 'num', 0) == 5 else 0)
    if notches:
        window[K_ALL_COLS].widget.canvas.yview_scroll(-round(notches * 3) or (-1 if notches > 0 else 1), 'units')
        move_slot(window, drag, drag.get('pointer_y', e.y_root))


def move_slot(window:sg.Window, drag, y_root):
    """ Put the slot where the dragged entry would land if dropped with the pointer at y_root """
    entry_rows = {window[K_B_BLOCK(k)].Widget.master for k in Block.active_blocks if K_B_BLOCK(k) in window.key_dict}
    rows = [r for r in drag['parent'].pack_slaves() if r in entry_rows]              # the other entries, top to bottom (skips the gap and any empty spacer rows)
    index = len(rows)
    for i, row in enumerate(rows):
        if y_root < row.winfo_rooty() + row.winfo_height() / 2:
            index = i
            break
    if index != drag['index']:
        drag['gap'].pack_forget()
        if index < len(rows):
            drag['gap'].pack(before=rows[index], fill='x', **drag['pads'])
        else:
            drag['gap'].pack(fill='x', **drag['pads'])
        drag['index'] = index
        window[K_ALL_COLS].contents_changed()


def drag_release(window:sg.Window, drag):
    """ Drop: put the entry's row back, then move its contents to the slot's position.  Returns True if the order changed """
    drag['done'] = True                                                     # stops the auto-scroll timer
    if drag.get('after') is not None:
        window.TKroot.after_cancel(drag['after'])
        drag['after'] = None
    if not drag['moved']:
        return False
    try:
        window.set_cursor('')
        next_row = drag['next_row']
        if next_row is not None and next_row.winfo_exists():
            drag['row'].pack(before=next_row, **drag['pack_info'])
        else:
            drag['row'].pack(**drag['pack_info'])
    finally:                                                                # whatever happens, the floating copy and the slot go away
        window.grab_any_where_on()
        for key in ('top', 'gap'):
            try:
                drag[key].destroy()
            except Exception:
                pass
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    keys = list(Block.active_blocks.keys())
    src_index = keys.index(drag['src'])
    if drag['index'] is None or drag['index'] == src_index:
        return False
    move_block_to_index(window, drag['src'], drag['index'])
    return True


def set_block_border(window:sg.Window, block_num):
    """ Border colour from the checkbox - and a heading is outlined in the theme's text colour """
    if window[K_B_CBOX(block_num)].get():
        color = FRAME_BORDER_COLOR_SELECTED
    else:
        color = mix_hex(T()['heading'], T()['card'], 0.35) if Block.active_blocks[block_num].kind == KIND_HEADING else FRAME_BORDER_COLOR_NOT_SELECTED
    window[K_B_BLOCK(block_num)].update(border_color=color)


def move_block_to_index(window:sg.Window, src, index):
    """ Move entry `src` so it becomes entry number `index` (counting the other entries only); the entries in between shift.
        The blocks keep their numbers, their CONTENTS move - same trick the old Up/Down buttons used """
    keys = list(Block.active_blocks.keys())
    contents = [(Block.active_blocks[k].name, Block.active_blocks[k].path, Block.active_blocks[k].iconb64, Block.active_blocks[k].kind, Block.active_blocks[k].bar,
                 window[K_B_CBOX(k)].get()) for k in keys]
    item = contents.pop(keys.index(src))
    contents.insert(index, item)
    for key, (name, path, iconb64, kind, bar, checked) in zip(keys, contents):
        b = Block.active_blocks[key]
        b.name, b.path, b.iconb64, b.kind, b.bar = name, path, iconb64, kind, bar
        update_block_elements(window, b)
        window[K_B_CBOX(key)].update(checked)
        set_block_border(window, key)
    window.refresh()


def load_blocks_into_window(window:sg.Window):
    saved_blocks = G.launcher_settings.load()
    del_all_blocks(window)
    try:
        for key in saved_blocks.keys():
            if key[0] == K_NAME:
                saved_block_num = key[1]
                block_num = add_block(window)
                b = Block.active_blocks[block_num]
                b.name = saved_blocks[K_B_NAME(saved_block_num)]
                b.path = saved_blocks[K_B_PATH(saved_block_num)].strip('"')
                b.iconb64 = saved_blocks[K_B_ICON64(saved_block_num)].strip('"')
                b.kind = saved_blocks.get(K_B_KIND(saved_block_num), KIND_APP)
                b.bar = saved_blocks.get(K_B_BARVIS(saved_block_num), True)
                update_block_elements(window, b)
                set_block_border(window, block_num)
    except Exception as e:
        sg.popup_error_with_traceback('Error loading saved blocks - erasing saved data', e)
    G.heads_at_load = [b.name for b in Block.active_blocks.values() if b.kind == KIND_HEADING]     # so save_blocks can carry a renamed heading's Colour
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()


def carry_heading_colors(before, after):
    """ The Programs window renamed a heading: its Colour goes with it - only when it is clear which (one heading name gone, one new one) """
    gone, new = [n for n in before if n not in after], [n for n in after if n not in before]
    if len(gone) == 1 and len(new) == 1 and gone[0] in G.head_colors:
        G.head_colors[new[0]] = G.head_colors.pop(gone[0])
        sg.user_settings_set_entry(K_HEAD_COLORS, G.head_colors)


def save_blocks(window:sg.Window):
    G.launcher_settings.write_new_dictionary({})
    for key in Block.active_blocks.keys():
        if K_B_BLOCK(key) in window.key_dict.keys():
            G.launcher_settings.set(K_B_ICON64(key), window[K_B_ICON64(key)].get().strip('"'))
            G.launcher_settings.set(K_B_NAME(key), window[K_B_NAME(key)].get().strip('"'))
            G.launcher_settings.set(K_B_PATH(key), window[K_B_PATH(key)].get().strip('"'))
            G.launcher_settings.set(K_B_KIND(key), Block.active_blocks[key].kind)
            G.launcher_settings.set(K_B_BARVIS(key), Block.active_blocks[key].bar)
    after = [window[K_B_NAME(k)].get().strip('"') for k, b in Block.active_blocks.items() if b.kind == KIND_HEADING and K_B_BLOCK(k) in window.key_dict.keys()]
    carry_heading_colors(G.heads_at_load, after)
    G.heads_at_load = after
    headings = sum(1 for b in Block.active_blocks.values() if b.kind == KIND_HEADING)
    sg.popup_quick_message(f'Saved {len(Block.active_blocks) - headings} applications and {headings} headings', font='_ 20', text_color='white', background_color='dark green')


# ------------------------------------------------------------ Delete an element from a window ------------------------------------------------------------

def del_an_elem(window:sg.Window, elem:sg.Element):
    elem.update(visible=False)
    widget = elem.Widget
    widget.pack_forget()
    widget.destroy()
    if hasattr(widget, 'image'):
        del widget.image
    del widget

    if elem.TKStringVar is not None:
        del elem.TKStringVar
    if elem.TKIntVar is not None:
        del elem.TKIntVar
    if elem.TKText is not None:
        del elem.TKText
    if elem.TKEntry is not None:
        del elem.TKEntry
    if elem.TKImage is not None:
        del elem.TKImage

    rowframe_children = elem.ParentRowFrame.winfo_children()
    if len(rowframe_children) == 0:
        elem.ParentRowFrame.destroy()
        del elem.ParentRowFrame
    remove_elem_from_nested(elem.ParentContainer.Rows, elem)
    del elem.ParentContainer
    del window.AllKeysDict[elem.key]


def remove_elem_from_nested(container, target):
    if isinstance(container, list):
        i = 0
        while i < len(container):
            item = container[i]
            if item is target:
                del container[i]          # remove this slot
                continue                  # don't advance i; next item shifts here
            remove_elem_from_nested(item, target)  # recurse into nested lists/tuples
            i += 1


# ------------------------------------------------------------ Programs window title strip (same as the new widgets' windows) ------------------------------------------------------------

def title_strip(title, close_key, with_version=True):
    """ The strip across the top:  [icon] title  v1.0 ............ x   (drag the window by it).  The x turns red under the mouse (bound after finalize) """
    t = T()
    row = [sg.Image(data=ui_icon(launcher_icon), background_color=t['strip'], p=((10, 6), 6)),
           sg.Text(title, font=('Segoe UI', 13, 'bold'), text_color=t['text'], background_color=t['strip'], p=(0, 6)),
           sg.Text(f'v{version}' if with_version else '', font=('Segoe UI', 9), text_color=t['dim'], background_color=t['strip'], p=((6, 0), (10, 4))),
           sg.Push(background_color=t['strip']),
           sg.Text('  ✕  ', key=close_key, font=('Segoe UI', 12), text_color=t['dim'], background_color=t['strip'], enable_events=True, p=0, tooltip='Close (Escape)')]
    return [sg.Column([row], key=K_STRIP, background_color=t['strip'], expand_x=True, p=0)]


def drag_by_strip(window, strip, skip=None, save_key=None):
    """ Move a window by dragging its title strip (any of it but `skip`, the close x) - the rest of the window stays put, so clicking into
        an entry never moves it.  save_key: where it is left is saved under this settings entry """
    start = {}

    def press(e):
        start['p'] = (e.x_root, e.y_root, window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty())

    def motion(e):
        p = start.get('p')
        if p:
            move_to(window, p[2] + e.x_root - p[0], p[3] + e.y_root - p[1])

    def release(e):
        p = start.pop('p', None)
        if p and save_key:                                              # (worked out, not asked: the window manager may not have moved it yet)
            sg.user_settings_set_entry(save_key, [p[2] + e.x_root - p[0], p[3] + e.y_root - p[1]])

    def bind(w):
        if w is skip:
            return
        w.bind('<ButtonPress-1>', press, add='+')
        w.bind('<B1-Motion>', motion, add='+')
        w.bind('<ButtonRelease-1>', release, add='+')
        for child in w.winfo_children():
            bind(child)

    bind(strip)


def place_programs_window(window, near):
    """ Where the Programs window opens: where you left it last time if that is still on a screen, else in the middle of the screen the
        dock is on (near = the dock's x, y, width, height) - and always all of it on that screen """
    window.refresh()
    w, h = window.TKroot.winfo_width(), window.TKroot.winfo_height()
    spot = sg.user_settings_get_entry(K_PROGRAMS_SPOT, None)
    if isinstance(spot, (list, tuple)) and len(spot) == 2 and on_a_screen(spot[0] + 40, spot[1] + 15):
        x, y = spot
    else:
        cx, cy = (near[0] + near[2] // 2, near[1] + near[3] // 2) if near else (window.TKroot.winfo_screenwidth() // 2, window.TKroot.winfo_screenheight() // 2)
        mon, work = monitor_area(cx, cy)
        x, y = (work[0] + work[2] - w) // 2, (work[1] + work[3] - h) // 2
    move_to(window, *onto_screen(x, y, w, h), firmly=True)
    window.set_alpha(1)
    window.bring_to_front()


def ui_icon(b64):
    """ A picture for the Programs window: fitted in a 30 x 30 square times the display scaling - icons are saved up to 128 px, and the program
        is dpi aware, so tk shows pictures pixel for pixel.  base64 in, base64 out """
    if not b64:
        return b64
    side = round(30 * G.dpi)
    key = ('ui', b64, side)
    if key not in G.icon_cache:
        try:
            im = Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGBA')
            if im.size == (side, side):
                G.icon_cache[key] = b64
            else:
                f = side / max(im.size)
                im = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)
                canvas = Image.new('RGBA', (side, side), (0, 0, 0, 0))
                canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2), im)
                buf = io.BytesIO()
                canvas.save(buf, 'PNG')
                G.icon_cache[key] = base64.b64encode(buf.getvalue())
        except Exception:
            G.icon_cache[key] = b64
    return G.icon_cache[key]


# ------------------------------------------------------------ The Programs window ------------------------------------------------------------

def confirm(window:sg.Window, question, title='Confirm') -> bool:
    """ Yes/No question that is guaranteed to appear ON TOP of the Programs window.  The Programs window is keep-on-top, so a plain popup
        can come up behind it and look as if the button did nothing.  Drops keep-on-top for the moment and places the popup over the window. """
    window.keep_on_top_clear()
    x, y = window.current_location()
    answer = sg.popup_yes_no(question, title=title, keep_on_top=True, modal=True, location=(x + 120, y + 120))
    window.keep_on_top_set()
    window.bring_to_front()
    return answer == 'Yes'


def insert_new_block(window:sg.Window, kind):
    """ + Add / + Heading: a new entry goes above the first checked entry (or at the end if none is checked); the list scrolls to it and its
        name is selected, ready to type over """
    checked = [k for k in Block.active_blocks if window[K_B_CBOX(k)].get()]
    new = add_block(window)
    b = Block.active_blocks[new]
    b.kind = kind
    b.name = 'New heading' if kind == KIND_HEADING else ''
    update_block_elements(window, b)
    set_block_border(window, new)
    keys = list(Block.active_blocks.keys())
    target = new
    if checked:
        index = keys.index(checked[0])
        move_block_to_index(window, new, index)
        target = keys[index]                                            # the contents moved there - the block numbers stay put
    window.refresh()
    window[K_ALL_COLS].contents_changed()
    window.refresh()
    inner = window[K_ALL_COLS].widget.TKFrame
    row = window[K_B_BLOCK(target)].Widget.master
    window[K_ALL_COLS].widget.canvas.yview_moveto(max(0, row.winfo_y() - 40) / max(1, inner.winfo_height()))
    window[K_B_NAME(target)].set_focus()
    window[K_B_NAME(target)].update(select=True)
    style_menus(window)                                                 # the new entry's elements came with their own menus


def fit_list_width(window:sg.Window):
    """ Make the scrolling list as wide as its entries need, so nothing (the trash cans!) is cut off on the right.  Measured from the widgets, so it follows font and DPI """
    column = window[K_ALL_COLS].widget
    window.refresh()
    needed = column.TKFrame.winfo_reqwidth()
    if needed > column.canvas.winfo_width():
        column.canvas.configure(width=needed)
        window.refresh()
        window[K_ALL_COLS].contents_changed()


def programs_window(near=None):
    """ The Programs window: the list of programs and headings - add, remove, order them.  Opens where it was left last time (if that is on a screen), else in the middle of the dock's
        screen - near = the dock's (x, y, width, height).  Moved by its title strip only.  Returns when the window is closed. """
    if G.launcher_settings is None:
        G.launcher_settings = sg.UserSettings(ENTRIES_FILENAME)
    Block.active_blocks = {}
    G.auto_icon = {}
    col_layouts = [[]]
    col_layouts += [[make_a_block()]]       # add a dummy block so that the column width is set correctly

    #  Toolbar - grouped left to right:  list editing | ordering | selection ......... file
    toolbar = [sg.B('+ Add', k='Add', tooltip='Add a program - above the first checked entry, or at the end'),
               sg.B('+ Heading', k=K_ADD_HEADING, tooltip='Add a heading to group the programs under it - above the first checked entry, or at the end'),
               sg.B('− Delete', k='Delete', button_color=COLOR_DANGER, tooltip='Delete the checked entries'),
               sg.B('Clear all', k='Clear', button_color=COLOR_DANGER, tooltip='Remove every entry from the list   (nothing is written until OK or Apply)'),
               sg.VerticalSeparator(p=(8, 2)),
               sg.B('☑ All', k=K_SEL_ALL, tooltip='Check every entry'),
               sg.B('☐ None', k=K_SEL_NONE, tooltip='Uncheck every entry'),
               sg.Push(),
               sg.B('OK', k=K_OK, button_color=COLOR_SAVE, s=7, tooltip='Save and close   (Enter, Ctrl+S)'),
               sg.B('Apply', k=K_APPLY, s=7, tooltip='Save but stay open'),
               sg.B('Cancel', k=K_CANCEL, s=7, tooltip='Close without saving   (Escape)')]
    list_height = min(round(SCROLLABLE_COLUMN_SIZE[1] * G.dpi), sg.Window.get_screen_size()[1] - round(260 * G.dpi))
    all_columns = sg.Column(col_layouts, size=(None, list_height), k=K_ALL_COLS, vertical_scroll_only=True, scrollable=True, expand_y=True, expand_x=True, p=(6, 2))
    status_bar = [sg.T('', k=K_STATUS, font='_ 10'), sg.Push(),                                  # file name only - the full path is in its tooltip, so the bar stays narrow
                  sg.T(os.path.basename(G.launcher_settings.get_filename()), font='_ 9', text_color=T()['dim'], tooltip=f'The list is saved in\n{G.launcher_settings.get_filename()}'), sg.Sizegrip()]
    hint = 'Drag ☰ to reorder - or drag them right on the dock, in the Panel.   Drop a program or a picture onto an entry.'
    body = [title_strip(f'{G.dock_title} Programs', 'Exit'),                                        # the strip's x sends 'Exit', handled like Cancel
            [sg.Column([toolbar], expand_x=True, p=(8, (8, 2)))],
            [sg.Text(hint, font='_ 9', text_color=T()['dim'], p=(12, (2, 4)))],
            [all_columns],
            [sg.Column([status_bar], expand_x=True, p=(8, (2, 4)))]]
    layout = [[sg.Frame('', body, border_width_no_relief=1, border_color=T()['border'], p=0, expand_x=True, expand_y=True)]]
    m_bg, m_fg = T()['menu']
    window = sg.Window(f'{window_title()} Programs  v{version}', layout, no_titlebar=True, grab_anywhere=False, keep_on_top=True, finalize=True, margins=(0, 0), icon=dock_icon_64, resizable=True,
                       use_min_size=True, alpha_channel=0, enable_close_attempted_event=True, right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT,
                       right_click_menu_background_color=m_bg,
                       right_click_menu_text_color=m_fg, right_click_menu_selected_colors=('#ffffff', C_SELECT), right_click_menu_font=FONT_MENU)
    close = window['Exit'].Widget
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=T()['strip'], fg=T()['dim']))

    del col_layouts
    load_blocks_into_window(window)
    fit_list_width(window)
    style_menus(window)
    drag_by_strip(window, window[K_STRIP].Widget, skip=close, save_key=K_PROGRAMS_SPOT)
    place_programs_window(window, near)

    drag = None                                                         # state of a grip drag in progress
    window.bind('<Prior>', K_PAGE_UP)
    window.bind('<Next>', K_PAGE_DOWN)
    window.bind('<Home>', K_HOME)
    window.bind('<End>', K_END)
    window.bind('<Escape>', K_CANCEL)
    window.bind('<Return>', K_OK)
    window.bind('<Control-s>', K_OK)
    scroll_canvas = window[K_ALL_COLS].widget.canvas
    G.dirty = any([icon_for_typed_path(window, n, b.path) for n, b in list(Block.active_blocks.items())          # entries saved with a path but
                   if b.kind == KIND_APP and b.path.strip() and not b.iconb64.strip()])                       # no icon get it now - OK saves
    update_status(window)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event in ('Exit', K_CANCEL, sg.WIN_CLOSE_ATTEMPTED_EVENT):    # the strip's x, Escape, Alt-F4
            if not G.dirty or confirm(window, 'Discard your unsaved changes?', 'Unsaved changes'):
                break
            continue
        if event == K_OK:
            save_blocks(window)
            break
        window.refresh()

        if psgdnd.is_drop_event(event):                 # file dropped onto a block: image -> icon,  program -> path + name + its icon
            block_num = event.key[1]
            if block_num in Block.active_blocks and Block.active_blocks[block_num].kind == KIND_HEADING:
                sg.popup_quick_message('Drop programs onto an application entry - this one is a heading', font='_ 14', text_color='white', background_color='#b71c1c')
            elif event.drop_type == psgdnd.DROP_TYPE_FILES and block_num in Block.active_blocks:
                filename = clean_path(values[event].split(',')[0])
                if not filename:                        # the drop came without a file name - don't blank the entry, say what to do instead
                    sg.popup_quick_message('That drop came without the file\'s name.\nCopy the program in your file manager, then paste it\n'
                                           'into the path box - its name and icon fill in.', font='_ 13', text_color='white', background_color='#b71c1c', keep_on_top=True,
                                           auto_close_duration=6)
                    continue
                try:
                    fill_block_from_dropped_file(window, block_num, filename)
                    G.dirty = True
                except Exception as e:
                    sg.popup_error(f'Could not use that file:\n{filename}', e, keep_on_top=True)
        elif event == 'Version':
            sg.popup_scrolled(f'{__file__}\n{APP_NAME} version {version}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
        elif event == 'Edit Me':
            sg.execute_editor(__file__)
        elif event in ('Add', K_ADD_HEADING):
            insert_new_block(window, KIND_HEADING if event == K_ADD_HEADING else KIND_APP)
            G.dirty = True
        elif event == 'Delete':
            if num_checked_blocks(window):
                del_checked_blocks(window)
                G.dirty = True
        elif event == K_APPLY:
            save_blocks(window)
            G.dirty = False
        elif event == 'Clear':
            if Block.active_blocks and confirm(window, 'Remove every entry from the list?'):
                del_all_blocks(window)
                G.dirty = True
        elif event == K_DRAG_PRESS:
            block_num, x_root, y_root = values[event]
            if block_num in Block.active_blocks:
                drag = {'src': block_num, 'y': y_root, 'moved': False}
        elif event == K_DRAG_MOTION:
            if drag is not None:
                drag_motion(window, drag, *values[event][1:])
        elif event == K_DRAG_RELEASE:
            if drag is not None:
                if drag_release(window, drag):
                    G.dirty = True
                drag = None
        elif event in (K_SEL_ALL, K_SEL_NONE):
            check_all_blocks(window, event == K_SEL_ALL)
        elif event == K_PAGE_UP:
            scroll_canvas.yview_scroll(-1, 'pages')
        elif event == K_PAGE_DOWN:
            scroll_canvas.yview_scroll(1, 'pages')
        elif event == K_HOME:
            scroll_canvas.yview_moveto(0)
        elif event == K_END:
            scroll_canvas.yview_moveto(1)
        elif isinstance(event, tuple):              # events from the elements inside a block
            block_num = event[1]
            if block_num not in Block.active_blocks:    # a stale event from a block that's been deleted
                continue
            if event[0] == K_DEL:
                del_block(window, block_num)
                window.refresh()
                window[K_ALL_COLS].contents_changed()
                G.dirty = True
            elif event[0] == K_ICON64:
                G.auto_icon.pop(block_num, None)                # an icon string you typed or pasted - a new path won't replace it
                try:
                    image_bytes = ast.literal_eval(values[event])
                except:
                    image_bytes = None
                window[K_B_ICON(block_num)].update(data=ui_icon(image_bytes) if isinstance(image_bytes, bytes) else ui_icon(blank_image_30x30))
                Block.active_blocks[block_num].iconb64 = values[event]
                G.dirty = True
            elif event[0] == K_NAME:
                Block.active_blocks[block_num].name = values[event]
                G.dirty = True
            elif event[0] == K_PATH:
                Block.active_blocks[block_num].path = values[event]
                G.dirty = True
                icon_for_typed_path(window, block_num, values[event])          # typed or pasted: the icon comes in like a drop
            elif event[0] == K_CBOX:
                set_block_border(window, block_num)
            elif event[0] == K_ICON:                # click the icon = launch it (handy for testing the path)
                launch_file = Block.active_blocks[block_num].path
                if not launch_file:
                    continue
                if launch_file.endswith(('.py', '.pyw')):
                    sg.execute_py_file(launch_file, cwd=os.path.dirname(launch_file))
                else:
                    sg.execute_command_subprocess(launch_file)
        update_status(window)
    window.close()


# Programs window images - 25 x 25
trash_red = b'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAMAAADzN3VRAAAASFBMVEUAAAD/AAD/AADrAAD/AAD/AADcAAD/AADtAAD3AADYAAD/AAD/AADwAADuAADuAAD6AADrAAD/AADOAAD/AACmAACtAAD/AADCW8QwAAAAF3RSTlMA/fnH2GWN3bGkhVru1Mq6uZOISjcaGe/TegUAAACDSURBVHiczZHtCsMgDEWTOKvWfrfbff83HYngHF3/bbCDYLjHqCjRb9huyvYeLiGEIFBEy6WawUJWrBqqOUZLuUgej9d2DmWxtcI1BzkIkp8x+wQ5mUw9esofjKcOHfm/NPny1useEff1ZK5eZ2JhHWWaGpNqh5Iac4/2oYX4aMy3eALVGAyXRSQ2kQAAAABJRU5ErkJggg=='

trash_amber = b'iVBORw0KGgoAAAANSUhEUgAAABkAAAAZCAMAAADzN3VRAAAAXVBMVEUAAADJoibJoifJoSbJoibIoiXKoCXJoibKoCbOpijIoibJoSfJoibJoibJoibIoSbWrSrIoSbJoSfNpijHoSXIoCjEnCfMoyjTqSnYrSrQqCjPpijmuSzJoifesytghzcEAAAAGHRSTlMA+cf92I1lhVjQzaOVy/Lf2LKvq0ozGhkawlE6AAAAnklEQVR4nM2RSQ6DMAxFbRLIwDy1xia5/zERSAUK6q6V+qR44SfFyTfAbzCN1rox783cld5XJCxUeV+6fDd1FKagVgKxxHo3oxPc2mtBceNxXUIqMIkS4qAoOQ1KCKmwbWxtQXg1kwUzG7DT3WSQzilkf2nsp1dTMXSxG+4/VUFItnNJh1HhGiqiQi7PC4rCLyQe6wF49Pqgf57Mt1gAAwEOREh/iwwAAAAASUVORK5CYII='

trash = trash_amber


#  ███╗   ███╗ █████╗ ██╗  ██╗███████╗    ██╗    ██╗██╗███╗   ██╗██████╗  ██████╗ ██╗    ██╗
#  ████╗ ████║██╔══██╗██║ ██╔╝██╔════╝    ██║    ██║██║████╗  ██║██╔══██╗██╔═══██╗██║    ██║
#  ██╔████╔██║███████║█████╔╝ █████╗      ██║ █╗ ██║██║██╔██╗ ██║██║  ██║██║   ██║██║ █╗ ██║
#  ██║╚██╔╝██║██╔══██║██╔═██╗ ██╔══╝      ██║███╗██║██║██║╚██╗██║██║  ██║██║   ██║██║███╗██║
#  ██║ ╚═╝ ██║██║  ██║██║  ██╗███████╗    ╚███╔███╔╝██║██║ ╚████║██████╔╝╚██████╔╝╚███╔███╔╝
#  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═════╝  ╚═════╝  ╚══╝╚══╝
sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT


def mix_hex(color, toward, amount):
    """ Mix two '#rrggbb' colours (no Tk needed - the dock builds its layout before any window exists).  Anything else comes back unchanged """
    try:
        a = [int(color[i:i + 2], 16) for i in (1, 3, 5)]
        b = [int(toward[i:i + 2], 16) for i in (1, 3, 5)]
    except (ValueError, TypeError, IndexError):
        return color
    return '#%02x%02x%02x' % tuple(int(a[i] + (b[i] - a[i]) * amount) for i in range(3))


def dock_columns(entries, num_columns, per_col=None):
    """ Split the entries (programs and headings) into at most num_columns columns, filled top to bottom - per_col rows each, or by default
        columns of about equal height.  A heading is never left as the last row of a column - it moves to the top of the next one, with its programs """
    per_col = per_col or max(1, -(-len(entries) // num_columns))
    columns = [[]]
    for entry in entries:
        current = columns[-1]
        full = len(current) >= per_col
        orphan = entry.kind == KIND_HEADING and current and len(current) >= per_col - 1
        if (full or orphan) and len(columns) < num_columns:
            columns.append([])
        columns[-1].append(entry)
    return [c for c in columns if c]


def column_height(column, row_h, head_h):
    """ How tall a Panel column is, in design pixels """
    return sum(head_h + (8 if i else 0) if b.kind == KIND_HEADING else row_h for i, b in enumerate(column))


def panel_columns(entries, row_h, head_h, col_w):
    """ The Panel's columns.  Columns 1 .. 8: that many, of about equal height.  Auto: the fewest that keep the card wider than it is tall (and
        no taller than the screen); a Panel on a side edge: one tall column if it fits, more beside it if not.  Never more than fit across the screen """
    most = max(1, int(((G.work[2] - G.work[0]) / G.scale - 2 * PAD - 40 + COL_GAP) // (col_w + COL_GAP)))
    if G.columns != 'Auto':
        return dock_columns(entries, min(int(G.columns), most))
    if G.place in ('Left', 'Right'):
        return dock_columns(entries, most, G.fit_rows)
    tall = (G.work[3] - G.work[1]) / G.scale - 40
    for n in range(1, most + 1):
        columns = dock_columns(entries, n)
        height = HEAD_H + 12 + search_row_h() + FOOT_H + max((column_height(c, row_h, head_h) for c in columns), default=row_h)
        width = max(2 * PAD + len(columns) * col_w + (len(columns) - 1) * COL_GAP, 340)
        if height <= min(width, tall):
            break
    return columns


# ======================================================================================================================================================
#   THE DOCK WINDOW
#   Everything in it is drawn with Pillow into one picture, in one of two styles:
#       Panel - a card with a title strip and the programs in columns (icon, name, version), each section's heading in its own colour
#       Bar   - a Mac-style row of icons that grow under the mouse, with a name bubble.  Layout: every icon (sections marked by a coloured rail
#               and a thin line), or Stacks - one tile per section that flies out into its programs when clicked (or when the mouse rests on it)
#   Each style remembers its own position (Floating anywhere, or docked to the Bottom / Top / Left / Right of a monitor, optionally auto-hidden
#   behind a small handle), its own floating spot and its own size.  S M L on the dock changes the size with one click; dragging across them
#   gives any size between.  The switch button flips between the two styles.
#   Glass (Windows): the picture becomes the window itself, with per-pixel transparency (UpdateLayeredWindow) - see-through glass,
#   soft shadows, smooth edges.  Otherwise it sits on a colour key: every pixel of the TRANSPARENT colour is see-through.
# ======================================================================================================================================================
STYLES = {'Panel': 'Panel  -  names and versions', 'Bar': 'Bar  -  icons, Mac style'}
PLACES = ('Floating', 'Bottom', 'Top', 'Left', 'Right')
MAGNIFIES = {'Off': 1.0, 'Small': 1.45, 'Large': 1.9}
LAYOUTS = {'Icons': 'Icons  -  every program, sections side by side', 'Stacks': 'Stacks  -  one per section, it flies out into its programs'}
SIZE_PRESETS = {'T': 0.65, 'S': 0.8, 'M': 1.0, 'L': 1.3}               # one click on the dock's T S M L;  dragging across them: any size SIZE_MIN .. SIZE_MAX
SIZE_MIN, SIZE_MAX = 0.55, 1.75
DOCK_DRAG = 5                                                          # pixels the mouse moves before a press drags the floating dock
TEXT_SIZES = {'Small': 0.88, 'Medium': 1.0, 'Large': 1.2, 'Extra large': 1.45}
SECTION_PALETTE = ('#e8a33d', '#1e9bff', '#2ecc71', '#c48cff', '#ff7f50', '#2ad4c8', '#ff6b9a', '#d9c63a', '#a6e22e', '#8c9eff', '#c0c7d1')
#                  gold,      blue,      green,     purple,    coral,     teal,      pink,      yellow,    lime,      periwinkle, silver
SECTION_NAMES = ('Gold', 'Blue', 'Green', 'Purple', 'Coral', 'Teal', 'Pink', 'Yellow', 'Lime', 'Periwinkle', 'Silver')     # SECTION_PALETTE's colours by name
HEAD_AUTO = 'Automatic'                                                # a heading's Colour menu: the palette's colour for its place (no colour of its own)
BAR_ICON, BAR_GAP, BAR_PAD, BAR_SEP, BAR_TOOL = 48, 8, 9, 17, 0.62     # Bar style, design pixels at 96 dpi / Medium size.  The switch and the gear are 62% of an icon
BAR_LABEL, BAR_LABEL_SIDE = 54, 260                                    # room for the name bubble: above / below a horizontal bar, beside a vertical one (x text size)
BAR_EDGE, BAR_SIDE = 10, 18                                            # room around the bar for its shadow: on the screen-edge side, at the ends
PANEL_SHADOW = 18                                                      # Glass: room around the Panel card for its shadow
AUTOHIDE_POLL_MS, AUTOHIDE_DWELL, AUTOHIDE_DELAY, SLIDE_MS = 90, 0.25, 0.7, 170    # auto-hide: pointer check, rest at the edge before showing, wait before hiding, slide time
HANDLE_COLORS = {'The theme\'s': None, 'Gold': '#e8a33d', 'Blue': '#1e9bff', 'Green': '#2ecc71', 'Purple': '#c48cff', 'Coral': '#ff7f50', 'Teal': '#2ad4c8',
                 'Pink': '#ff6b9a', 'Yellow': '#d9c63a', 'Lime': '#a6e22e', 'Periwinkle': '#8c9eff', 'Silver': '#c0c7d1', 'White': '#f4f6fa'}   # right-click > Handle colour
HANDLE_CUSTOM = 'Custom...'                                            # its last item: any colour, from the colour picker (G.handle_custom)
FLYOUTS = {'At once': 0.0, 'After a moment  (0.3 s)': 0.3, 'After half a second': 0.5, 'After a second': 1.0}     # right-click > Fly out (G.flyout)
EDGE_SNAP, EDGE_PULL, EDGE_RAM = 22, 90, 24                           # a dragged dock docks with the mouse this close to an edge, or pushed this far past one;
                                                                       # a docked one pulled this far off its edge leaves it
KS = lambda name, style: f'-{name} {style}-'                           # a setting each style keeps for itself:  '-PLACE Bar-', '-SIZE Panel-' ...
K_STACK_IMAGE = '-STACK IMAGE-'                                        # the fly-out of a stack, and its events (values: the tile under the mouse / clicked)
K_STACK_HOVER, K_STACK_CLICK, K_STACK_CLOSE = '-STACK HOVER-', '-STACK CLICK-', '-STACK CLOSE-'
K_ASK_INPUT, K_ASK_OK, K_ASK_NO, K_ASK_X = '-ASK INPUT-', '-ASK OK-', '-ASK NO-', '-ASK X-'                  # ask_near(): a question card by the mouse
K_STACK_OPEN = '-STACK OPEN-'                                          # Open stacks on hover: the mouse rested on a stack, value = its heading's block_num
K_STACKS_HOVER = '-STACKS ON HOVER-'                                   # right-click > Layout > Open stacks on hover (settings entry too)
STACK_REST = 0.4                                                       # seconds the mouse rests on a stack before it opens by itself
SEARCH_AUTO = 12                                                       # a dock with this many programs or more starts with its search on (right-click > Search)
SEARCH_MODES = {'Hide': "Hide the programs that don't match", 'Dim': "Dim the programs that don't match"}     # right-click > Search
C_MARK = '#e8a33d'                                                     # the search: a soft amber mark behind the letters that match


def font(bold, px):
    """ Segoe UI (Windows) / DejaVu Sans (Linux) at px pixels, cached """
    key = (bold, px)
    if key not in G.fonts:
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
        G.fonts[key] = f
    return G.fonts[key]


def fit(d, text, fnt, width, keep_end=False):
    """ text shortened with an ellipsis so it fits in width pixels - at the start instead when keep_end (paths: the file name matters most) """
    if d.textlength(text, font=fnt) <= width:
        return text
    while text and d.textlength('…' + text if keep_end else text + '…', font=fnt) > width:
        text = text[1:] if keep_end else text[:-1]
    return '…' + text if keep_end else text + '…'


def rgba(color, alpha=255):
    """ '#rrggbb' -> (r, g, b, alpha) """
    return tuple(int(color[i:i + 2], 16) for i in (1, 3, 5)) + (alpha,)


def text_scale():
    """ Right-click > Text size: how much bigger or smaller all the dock's text is """
    return TEXT_SIZES.get(G.text, 1.0)


def icon_image(b64, px):
    """ An entry's icon (the base64 PNG as saved, b'...' text or bytes) as an RGBA image fitted in px x px, cached.  None if it isn't a picture """
    key = (b64, px)
    if key not in G.icon_cache:
        try:
            data = ast.literal_eval(b64) if isinstance(b64, str) else b64
            im = Image.open(io.BytesIO(base64.b64decode(data))).convert('RGBA')
            f = px / max(im.size)
            G.icon_cache[key] = im.resize((max(1, round(im.width * f)), max(1, round(im.height * f))), Image.LANCZOS)
        except Exception:
            G.icon_cache[key] = None
        if len(G.icon_cache) > 3000:                                    # magnification makes many sizes - keep the cache from growing forever
            for k in list(G.icon_cache)[:1500]:
                del G.icon_cache[k]
    return G.icon_cache[key]


def draw_gear(d, cx, cy, r, color, hole):
    """ 8-tooth gear: a star-shaped polygon with flat tooth tops, and a hole in the middle """
    pts = []
    for i in range(32):
        a = math.radians(i * 360 / 32)
        rr = r if (i % 4) in (0, 1) else r * 0.72
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=color)
    d.ellipse((cx - r * 0.33, cy - r * 0.33, cx + r * 0.33, cy + r * 0.33), fill=hole)


def hide_shown():
    """ The hide button shows on every docked dock """
    return G.place != 'Floating'


def hide_now(window):
    """ The hide button: tuck the dock away now.  Auto-hide on: it flies out again when the mouse rests at its edge.  Auto-hide off: its handle
        stays (on top of other windows) until you click it - then the dock stays out """
    if hide_shown() and not G.hidden and G.anim is None:
        G.hover = None
        slide(window, False)
        G.handle_since = -1                                             # not out again until the mouse has left the handle


def draw_hide(d, cx, cy, r, color, width):
    """ The hide button: a chevron pointing at the dock's edge """
    v = {'Bottom': (0, 1), 'Top': (0, -1), 'Left': (-1, 0), 'Right': (1, 0)}.get(G.place, (0, 1))
    tip = (cx + v[0] * r * 0.55, cy + v[1] * r * 0.55)
    side = (v[1] * r, v[0] * r)                                         # across the arrow
    back = (cx - v[0] * r * 0.55, cy - v[1] * r * 0.55)
    d.line(((back[0] + side[0], back[1] + side[1]), tip, (back[0] - side[0], back[1] - side[1])), fill=color, width=width, joint='curve')


def draw_magnifier(d, cx, cy, r, color, width):
    """ The search button: a lens, its handle down to the right """
    lr = r * 0.6
    lx, ly = cx - r * 0.2, cy - r * 0.2
    d.ellipse((lx - lr, ly - lr, lx + lr, ly + lr), outline=color, width=width)
    a = lr * 0.72
    d.line((lx + a, ly + a, cx + r * 0.8, cy + r * 0.8), fill=color, width=max(1, round(width * 1.25)))


def draw_switch(d, cx, cy, r, color, to_bar):
    """ The style switch: a little Bar (a capsule with three dots) when it switches to the Bar, a little Panel (a card with three lines) when
        it switches to the Panel """
    w = max(1, round(r * 0.22))
    if to_bar:
        d.rounded_rectangle((cx - r, cy - r * 0.45, cx + r, cy + r * 0.45), radius=r * 0.45, outline=color, width=w)
        for dx in (-0.5, 0, 0.5):
            d.ellipse((cx + dx * r - r * 0.17, cy - r * 0.17, cx + dx * r + r * 0.17, cy + r * 0.17), fill=color)
    else:
        d.rounded_rectangle((cx - r * 0.85, cy - r, cx + r * 0.85, cy + r), radius=r * 0.25, outline=color, width=w)
        for dy in (-0.45, 0, 0.45):
            d.line((cx - r * 0.5, cy + dy * r, cx + r * 0.5, cy + dy * r), fill=color, width=w)


def size_spot(size):
    """ Where a size sits along the T S M L control: 0 = the first letter, 1 = the last, evenly between (below 0 / above 1 for sizes past them) """
    vals = list(SIZE_PRESETS.values())
    n = len(vals) - 1
    for i in range(n):
        if size <= vals[i + 1] or i == n - 1:
            return (i + (size - vals[i]) / (vals[i + 1] - vals[i])) / n
    return 1.0


def size_letter():
    """ The T / S / M / L the dock is at - None for a size in between """
    return next((letter for letter, value in SIZE_PRESETS.items() if abs(G.size - value) < 0.005), None)


def draw_size_control(d, box, horizontal, t, hot):
    """ The T S M L control: a capsule with the letters, the size in use on a blue disc - or, for a size in between, a small blue dot
        at its place along the capsule """
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    thick = min(w, h)
    d.rounded_rectangle(box, radius=thick / 2, fill=mix_hex(t['text'], t['card'], 0.84 if hot else 0.9), outline=mix_hex(t['text'], t['card'], 0.72))
    current = size_letter()
    f = font(True, max(9, round(thick * 0.56)))
    n = len(SIZE_PRESETS)
    for i, letter in enumerate(SIZE_PRESETS):
        cx = x0 + w * (i + 0.5) / n if horizontal else (x0 + x1) / 2
        cy = (y0 + y1) / 2 if horizontal else y0 + h * (i + 0.5) / n
        if letter == current:
            r = thick * 0.43
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=C_SELECT)
        d.text((cx, cy), letter, font=f, fill='#ffffff' if letter == current else t['text'] if hot else t['dim'], anchor='mm')
    if current is None:                                                 # a size between the letters: a dot at its place
        p = min(1.1, max(-0.1, size_spot(G.size)))
        r = max(1.5, thick * 0.1)
        cx, cy = (x0 + w / (2 * n) + p * w * (n - 1) / n, y1 - thick * 0.17) if horizontal else (x1 - thick * 0.17, y0 + h / (2 * n) + p * h * (n - 1) / n)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=C_CHECKED)


def size_letter_at(box, horizontal, x, y):
    """ T, S, M or L - the part of the size control at x, y """
    x0, y0, x1, y1 = box
    n = len(SIZE_PRESETS)
    p = (x - x0) / max(1, x1 - x0) if horizontal else (y - y0) / max(1, y1 - y0)
    return list(SIZE_PRESETS)[min(n - 1, max(0, int(p * n)))]


def soft_shadow(w, h, radius, blur, alpha=110):
    """ A blurred dark rounded rectangle w x h (plus 2 x blur all round) - the Glass look's drop shadow.  Cached """
    key = ('shadow', w // 4, h // 4, radius, blur, alpha)
    if key not in G.icon_cache:
        w, h = max(8, w // 4 * 4), max(8, h // 4 * 4)
        im = Image.new('RGBA', (w + 4 * blur, h + 4 * blur), (0, 0, 0, 0))
        ImageDraw.Draw(im).rounded_rectangle((2 * blur, 2 * blur, 2 * blur + w, 2 * blur + h), radius=radius, fill=(0, 0, 0, alpha))
        G.icon_cache[key] = im.filter(ImageFilter.GaussianBlur(blur))
    return G.icon_cache[key]


def bar_shadow(length, thick, radius, blur):
    """ The Bar's drop shadow for a bar length x thick: made once per bar thickness as two ends and a middle, stretched to the length (the bar
        changes length on every frame while it magnifies - blurring a new shadow each time would be slow) """
    key = ('bar shadow', thick, radius, blur, vertical())
    if key not in G.icon_cache:
        base = soft_shadow(2 * radius + 4 * blur + 8, thick, radius, blur)
        if vertical():
            base = base.transpose(Image.Transpose.TRANSPOSE)
            c = base.height // 2
            G.icon_cache[key] = (base.crop((0, 0, base.width, c)), base.crop((0, c, base.width, c + 1)), base.crop((0, c + 1, base.width, base.height)))
        else:
            c = base.width // 2
            G.icon_cache[key] = (base.crop((0, 0, c, base.height)), base.crop((c, 0, c + 1, base.height)), base.crop((c + 1, 0, base.width, base.height)))
    start, middle, end = G.icon_cache[key]
    total = length + 4 * blur
    if vertical():
        im = Image.new('RGBA', (start.width, total), (0, 0, 0, 0))
        im.paste(start, (0, 0))
        im.paste(middle.resize((start.width, max(1, total - start.height - end.height))), (0, start.height))
        im.paste(end, (0, total - end.height))
    else:
        im = Image.new('RGBA', (total, start.height), (0, 0, 0, 0))
        im.paste(start, (0, 0))
        im.paste(middle.resize((max(1, total - start.width - end.width), start.height)), (start.width, 0))
        im.paste(end, (total - end.width, 0))
    return im


def vertical():
    """ True when the dock runs top to bottom: a Bar on the left or right edge, or Floating vertically """
    return G.style == 'Bar' and bar_side() in ('Left', 'Right')


def bar_side():
    """ The Bar's screen-edge side - what its drawing is turned by: its edge when docked;  floating: Bottom (icons grow upward), or Floating vertically
        Left / Right (it opens toward the middle of the screen) """
    if G.place != 'Floating':
        return G.place
    return G.float_side if G.float_vertical and G.style == 'Bar' else 'Bottom'


# ------------------------------------------------------------ Sections ------------------------------------------------------------

def section_color(color):
    """ How the dock shows a heading's colour on this theme: a palette colour as it is - a darker shade on a light card;  a Custom... colour
        as picked, only moved far enough to read on the card (3:1) """
    t = T()
    light = t.get('light', False)
    if color in SECTION_PALETTE:
        return mix_hex(color, '#000000', 0.32) if light else color
    return readable(color, t['card'], 3.0, '#000000' if light else '#ffffff')


def sections():
    """ Each heading's colour, and the heading every entry sits under:  ({heading block_num: colour}, {block_num: heading block or None}).
        A heading's own Colour (its right-click menu), else the palette's for its place.  Colored sections off: all headings gold """
    colors, owner, current, n = {}, {}, None, 0
    for b in Block.active_blocks.values():
        if b.kind == KIND_HEADING:
            colors[b.block_num] = section_color(G.head_colors.get(b.name) or SECTION_PALETTE[n % len(SECTION_PALETTE)]) if G.sections else T()['heading']
            current, n = b, n + 1
        owner[b.block_num] = current
    return colors, owner


def section_members(heading_num, bar_only=True):
    """ The programs under a heading (only those the Bar shows when bar_only) """
    order = list(Block.active_blocks.values())
    i = next((i for i, b in enumerate(order) if b.block_num == heading_num), len(order))
    out = []
    for b in order[i + 1:]:
        if b.kind == KIND_HEADING:
            break
        if b.bar or not bar_only:
            out.append(b)
    return out


def section_end(heading_num):
    """ The list position just after a heading's last program - where a program dropped onto its stack goes """
    order = list(Block.active_blocks)
    i = order.index(heading_num) + 1 if heading_num in order else len(order)
    while i < len(order) and Block.active_blocks[order[i]].kind != KIND_HEADING:
        i += 1
    return i


# ------------------------------------------------------------ Search ------------------------------------------------------------

def program_count():
    """ How many programs (not headings) the dock has """
    return sum(1 for b in Block.active_blocks.values() if b.kind != KIND_HEADING)


def search_on():
    """ Right-click > Search > Search box (Panel) / Search button (Bar): as set for this dock - not set: on once it has SEARCH_AUTO programs """
    return G.search_pref if G.search_pref is not None else program_count() >= SEARCH_AUTO


def search_row_h():
    """ Panel: the height of the search row under the title strip, in design pixels - 0 when the search is off (or there's nothing to search) """
    return round(36 * (0.25 + 0.75 * text_scale())) if search_on() and program_count() else 0


def match_spans(name, q):
    """ Where the search q (lower case) matches a name: [(start, end)] of the letters to mark - or None.  Anywhere in the name ('pi': Pip
        Refresh, Piano...), each word of q somewhere in it ('ref pip'), or the first letters of its words ('pdm': Piano Dynamics Monitor) """
    low = ''.join(c.lower() if len(c.lower()) == 1 else c for c in name)      # (as long as the name, so the marks land on the right letters)
    i = low.find(q)
    if i >= 0:
        return [(i, i + len(q))]
    words = q.split()
    if len(words) > 1:
        spans = [(low.find(w), low.find(w) + len(w)) for w in words]
        return spans if all(s >= 0 for s, e in spans) else None
    starts = [m.start() for m in re.finditer(r'[^\W_]+|%', low)]
    if len(q) > 1 and ''.join(low[s] for s in starts).startswith(q):
        return [(s, s + 1) for s in starts[:len(q)]]
    return None


def search_find():
    """ The search now: (the programs that match, in list order;  {block_num: the letters to mark};  {the headings they sit under}) - None
        while nothing is typed.  A heading whose name matches brings its whole section """
    q = ' '.join(G.search.lower().split())
    if not q:
        return None
    found, marks, heads = [], {}, set()
    section, whole = None, False
    for b in Block.active_blocks.values():
        spans = match_spans(b.name or '', q)
        if spans:
            marks[b.block_num] = spans
        if b.kind == KIND_HEADING:
            section, whole = b, spans is not None
        elif spans is not None or whole:
            found.append(b)
            if section is not None:
                heads.add(section.block_num)
    return found, marks, heads


def search_pick():
    """ The match Enter opens - the one in blue - or None """
    found = search_find()
    if not found or not found[0]:
        return None
    G.search_sel = min(max(0, G.search_sel), len(found[0]) - 1)
    return found[0][G.search_sel]


def redraw_soon(window):
    """ Redraw once tk is idle - the keys already waiting are taken first, so typing fast makes one picture instead of one per letter """
    if G.redraw_due:
        return
    G.redraw_due = True

    def go():
        if G.redraw_due:
            redraw(window)
    window.TKroot.after_idle(go)


def set_search(window, text):
    """ What's in the Panel's search box changed: the first match is the pick again, and the dock shows the new matches """
    text = text[:60]
    if text != G.search:
        G.search, G.search_sel, G.hover, G.search_all = text, 0, None, False
        if window is G.window and not G.hidden:
            redraw_soon(window)


def clear_search_later(window, ms=450):
    """ A program started from the search: the search clears a moment later, once its row has glowed - unless something new was typed """
    text = G.search
    window.TKroot.after(ms, lambda: set_search(window, '') if window is G.window and G.search == text else None)


def toggle_search(window):
    """ The magnifier in the Panel's title strip, or right-click > Search > Search box / Search button: this dock's search on or off """
    G.search_pref = not search_on()
    sg.user_settings_set_entry(K_SEARCH, G.search_pref)
    G.search, G.search_sel = '', 0
    if G.search_pref and G.style == 'Panel':                            # on: type straight away
        try:
            window.TKroot.focus_force()
        except Exception:
            pass
    relayout(window)
    set_right_click_menu(window, make_menu())


def typed(text, keysym, char, state, root, picked=False):
    """ A key for a search box: (the new text, all of it selected?) - None when the key isn't for the text.  Letters (Ctrl+Alt too: AltGr),
        Backspace (Ctrl: a whole word), Ctrl+V or Shift+Insert: the clipboard's first line.  Ctrl+A selects it all (picked - drawn highlighted,
        as in a real text box): then a letter or a paste replaces it, Backspace or Delete clears it, Ctrl+C copies it, Ctrl+X cuts it """
    ctrl, alt = bool(state & 0x4), bool(state & 0x20000)                # (Windows: Alt is 0x20000)
    command, key = ctrl and not alt, keysym.lower()
    if command and key == 'a':
        return text, bool(text)
    if keysym == 'BackSpace' or (keysym == 'Delete' and picked):
        return ('' if picked else re.sub(r'\S*\s*$', '', text) if ctrl else text[:-1]), False
    if command and key in ('c', 'x'):                                   # copy / cut - only what's selected, as in a text box
        if not picked:
            return None
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
        except Exception:
            return None
        return ('', False) if key == 'x' else (text, True)
    start = '' if picked else text
    if (command and key == 'v') or (keysym == 'Insert' and state & 0x1):
        try:
            clip = root.clipboard_get()
        except Exception:
            return None
        return (start + next((line.strip() for line in clip.splitlines() if line.strip()), '')).lstrip()[:60], False
    if len(char) == 1 and char.isprintable() and ctrl == alt:
        return (start + char).lstrip()[:60], False                      # (a space first does nothing)
    return None


def search_key(window, e):
    """ A key while the dock has the keyboard.  Panel: its search box takes it - letters, Backspace, Ctrl+V;  the arrows move the pick,
        Enter starts it, Esc clears.  Bar: a letter opens its search with that letter """
    if window is not G.window or G.hidden or G.drag_item is not None or not search_on() or not program_count():
        return
    if G.style == 'Bar':
        typing = typed('', e.keysym, e.char, e.state, window.TKroot)
        if typing and typing[0].strip():
            window.write_event_value(K_FIND_OPEN, typing[0])
        return
    G.focus = True                                                      # (a key came, so the dock has the keyboard - in case no FocusIn said so)
    if e.keysym == 'Escape':
        G.search_all = False
        set_search(window, '')
    elif e.keysym in ('Return', 'KP_Enter'):
        b = search_pick()
        if b is not None:
            start_program(window, b.block_num)
            clear_search_later(window)
    elif e.keysym in ('Up', 'Down', 'Left', 'Right'):
        if G.search_all:                                                # an arrow first lets go of Ctrl+A's selection (Left / Right only that)
            G.search_all = False
            redraw_soon(window)
            if e.keysym in ('Left', 'Right'):
                return
        search_move(window, e.keysym)
    else:
        typing = typed(G.search, e.keysym, e.char, e.state, window.TKroot, G.search_all and bool(G.search))
        if typing is not None:
            if typing[1] != G.search_all:
                G.search_all = typing[1]
                redraw_soon(window)
            set_search(window, typing[0])


def search_move(window, key):
    """ The arrows in the Panel's search: Up / Down - the match before / after;  Left / Right - the nearest one in the column beside """
    found = search_find()
    if not found or not found[0]:
        return
    if key in ('Left', 'Right') and G.redraw_due:                       # (where the matches are: from the newest picture)
        redraw(window)
    order = [b.block_num for b in found[0]]
    sel = min(max(0, G.search_sel), len(order) - 1)
    spots = {num: (x, y) for num, x, y in G.search_spots}
    if key in ('Left', 'Right') and order[sel] in spots:
        x, y = spots[order[sel]]
        beside = []
        for i, num in enumerate(order):
            sx, sy = spots.get(num, (x, y))
            if (sx < x) if key == 'Left' else (sx > x):
                beside.append((sx, abs(sy - y), i))
        if beside:
            column = max(c[0] for c in beside) if key == 'Left' else min(c[0] for c in beside)
            sel = min((c for c in beside if c[0] == column), key=lambda c: c[1])[2]
    elif key in ('Up', 'Down'):
        sel += 1 if key == 'Down' else -1
    G.search_sel = min(len(order) - 1, max(0, sel))
    redraw_soon(window)


def start_program(window, num):
    """ Start a program from the dock - a click, or Enter in a search: it hops on the Bar (in Stacks, its stack hops), its row glows in the Panel """
    launch(Block.active_blocks[num].path)
    now = time.time()
    G.bounce[num], G.flash[num] = now, now + 0.35
    if G.style == 'Bar':
        section = sections()[1].get(num) if G.bar_layout == 'Stacks' else None
        if section is not None:
            G.bounce[section.block_num] = now
        bar_track_start(window)
    else:
        redraw(window)
        window.TKroot.after(400, lambda: redraw(window))


def see_through(im, amount):
    """ A copy of a picture at that much of its opacity - the search dims what doesn't match """
    out = im.copy()
    out.putalpha(im.getchannel('A').point(lambda a: round(a * amount)))
    return out


def draw_marks(d, shown, spans, fnt, x, cy, t):
    """ The search: a soft amber mark behind each run of matching letters in a name drawn at x (its middle at cy).  shown = the name as drawn,
        perhaps cut short with … """
    if not spans:
        return
    keep = len(shown) - 1 if shown.endswith('…') else len(shown)
    half = fnt.size * 0.62
    for s, e in spans:
        e = min(e, keep)
        if s < e:
            x0, x1 = x + d.textlength(shown[:s], font=fnt), x + d.textlength(shown[:e], font=fnt)
            d.rounded_rectangle((x0 - 1, cy - half, x1 + 1, cy + half), radius=fnt.size * 0.2, fill=mix_hex(C_MARK, t['card'], 0.5))


def draw_field(d, box, u, t, text, placeholder, caret, right_room=0, picked=False):
    """ A search box: its outline (blue while it has the keyboard), a magnifier, what's typed - or a faint placeholder - and the caret.
        box in pixels, u = pixels per design pixel;  right_room: pixels kept free at its right end;  picked: what's typed is selected (Ctrl+A) -
        white on blue, no caret """
    x0, y0, x1, y1 = box
    cy = (y0 + y1) / 2
    d.rounded_rectangle(box, radius=8 * u, fill=mix_hex(t['track'], t['card'], 0.35), outline=mix_hex(C_CHECKED, t['card'], 0.2) if caret else t['border'],
                        width=max(1, round(u)))
    draw_magnifier(d, x0 + 15 * u, cy, 6.5 * u, t['text'] if caret or text else t['dim'], max(1, round(1.6 * u)))
    f, tx = font(False, round(14 * text_scale() * u)), x0 + 30 * u
    room = max(10 * u, x1 - tx - right_room - 8 * u)
    if text:
        shown = fit(d, text, f, room, keep_end=True)
        end = tx + d.textlength(shown, font=f) + 1.5 * u
        if picked:
            d.rectangle((tx - 1.5 * u, cy - f.size * 0.68, end, cy + f.size * 0.68), fill=C_SELECT)
        d.text((tx, cy), shown, font=f, fill='#ffffff' if picked else t['text'], anchor='lm')
    else:
        d.text((tx + 4 * u, cy), fit(d, placeholder, f, room), font=f, fill=mix_hex(t['dim'], t['card'], 0.2), anchor='lm')
        end = tx + 1.5 * u
    if caret and not (picked and text):
        d.line((end, cy - f.size * 0.55, end, cy + f.size * 0.55), fill=t['text'], width=max(1, round(1.3 * u)))


def draw_search_box(d, k, t, W, h, hits):
    """ Panel: the search box under the title strip - with an x that clears it once something is typed.  Adds their parts to hits """
    x0, y0, x1, y1 = 12, HEAD_H + 6, W - 12, HEAD_H + h
    n = program_count()
    draw_field(d, (x0 * k, y0 * k, x1 * k, y1 * k), k, t, G.search, f'Search {n} program{"s" * (n != 1)}', G.focus, 26 * k if G.search else 0, G.search_all)
    if G.search:
        cx, cy, hot = x1 - 14, (y0 + y1) / 2, G.hover == 'clear'
        hits.append((x1 - 27, y0, x1, y1, 'clear'))
        if hot:
            d.ellipse(((cx - 9) * k, (cy - 9) * k, (cx + 9) * k, (cy + 9) * k), fill=mix_hex(t['text'], t['card'], 0.8))
        r, color = 3.8, t['text'] if hot else t['dim']
        d.line(((cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k), fill=color, width=max(1, round(1.5 * k)))
        d.line(((cx - r) * k, (cy + r) * k, (cx + r) * k, (cy - r) * k), fill=color, width=max(1, round(1.5 * k)))
    hits.append((x0, y0, x1, y1, 'find'))


def bar_lit():
    """ The Bar while its search is out, with Dim: the programs that match (the rest of the bar fades) - None when nothing fades """
    if G.stack_open != 'search' or G.search_mode != 'Dim':
        return None
    found = search_find()
    return {b.block_num for b in found[0]} if found is not None else None


# ------------------------------------------------------------ Panel style ------------------------------------------------------------

def card_layout():
    """ Panel style: where everything goes, in design pixels:  (width, height, [(kind, block, x, y, w, h)], y of the bottom line).
        Rows, headings and columns follow the text size.  The search box (when on) sits under the title strip.  A search that hides what
        doesn't match: the matches and their headings fill the same columns from the top, and the card keeps its size """
    ts = text_scale()
    row_h, head_h = max(ICON_PX + 5, round(ROW_H * (0.25 + 0.75 * ts))), round(30 * (0.2 + 0.8 * ts))
    col_w = round(COL_W * (0.45 + 0.55 * ts))
    top = HEAD_H + 6 + search_row_h()                                   # where the list starts
    G.fit_rows = max(AUTO_ROWS, int(((G.work[3] - G.work[1]) / G.scale - top - FOOT_H - 54) // row_h))      # a Panel on a side edge: rows that fit in one column
    columns = panel_columns(list(Block.active_blocks.values()), row_h, head_h, col_w) or [[]]
    measure, z = ImageDraw.Draw(Image.new('L', (1, 1))), 4                 # room in the title strip for this dock's name (up to 520): narrower columns get wider
    title_w = measure.textlength(G.dock_title.upper(), font=font(True, round(13 * min(ts, 1.25) * z))) / z + measure.textlength(f'v{version}', font=font(False, 12 * z)) / z
    need = min(520, round(38 + title_w + 7 + 14 + 211))                 # (211: the search button, S M L, the switch, the gear and the x)
    n = len(columns)
    if 2 * PAD + n * col_w + (n - 1) * COL_GAP < need:
        col_w = (need - 2 * PAD - (n - 1) * COL_GAP) / n
    full = max((column_height(c, row_h, head_h) for c in columns), default=0)        # how tall the list is with everything showing
    found = search_find() if G.search_mode == 'Hide' and search_row_h() else None
    if found is not None:                                               # Hide: just the matches and their headings, in as many columns
        shown = {b.block_num for b in found[0]} | found[2]
        columns = dock_columns([b for b in Block.active_blocks.values() if b.block_num in shown], n) or [[]]
    items, bottom = [], top
    for c, entries in enumerate(columns):
        x, y = PAD + c * (col_w + COL_GAP), top
        for i, b in enumerate(entries):
            if b.kind == KIND_HEADING:
                y += 8 if i else 0
                items.append((KIND_HEADING, b, x, y, col_w, head_h))
                y += head_h
            else:
                items.append((KIND_APP, b, x, y, col_w, row_h))
                y += row_h
        bottom = max(bottom, y)
    bottom = max(bottom, top + full)
    if not Block.active_blocks or (found is not None and not found[0]):
        bottom = max(bottom, top + row_h)                               # (room for a line: Drop programs here / No matches)
    width = max(2 * PAD + n * col_w + (n - 1) * COL_GAP, 340)
    return width, bottom + 6 + FOOT_H, items, bottom + 6


def hint(part):
    """ The bottom line: what's under the mouse (a program's path), else a summary - while searching: how many match, and the one Enter opens """
    if part == 'gear':
        return 'Programs - add, remove and order them'
    if part == 'close':
        return f'Close {G.dock_title}'
    if part == 'hide':
        return 'Hide this dock'                                         # (a narrow Panel's bottom line has little room)
    if part == 'switch':
        return 'Switch to the Bar - the icons in a row, Mac style' if G.style == 'Panel' else 'Switch to the Panel - names and versions'
    if part == 'search':
        return 'Hide the search box' if search_row_h() else 'Search - a box that finds your programs as you type'
    if part == 'find':
        return 'Type to find a program   ·   Enter opens it   ·   Esc clears'
    if part == 'clear':
        return 'Clear the search'
    if isinstance(part, tuple) and part[0] == 'size':
        return f'Size {round(G.size * 100)}%   ·   click T, S, M or L  -  or drag across them for any size'
    if isinstance(part, tuple) and part[1] in Block.active_blocks:
        b = Block.active_blocks[part[1]]
        if b.kind == KIND_HEADING:
            return f'{b.name}   ·   right-click: add a program here, rename, remove'
        ver = G.versions.get(b.block_num, '') if G.show_versions else ''
        return (b.path + (f'   ·   v{ver}' if ver else '')) if b.path else 'No program set for this entry - add one in the Programs window'
    n = program_count()
    if not n:
        return 'No programs yet - drop some here, or click the gear'
    found = search_find() if search_row_h() else None
    if found is not None and found[0]:
        pick = found[0][min(max(0, G.search_sel), len(found[0]) - 1)]
        return f'{len(found[0])} of {n} match   ·   Enter opens {pick.name or "(no name)"}   ·   arrows move   ·   Esc clears'
    if found is not None:
        return f'No matches among the {n} programs   ·   Esc clears'
    return f'{n} program{"s" * (n != 1)}   ·   drag to rearrange   ·   drop programs here   ·   right-click for options'


def render_card():
    """ Panel style: the whole card as an RGBA picture.  Drawn at 2x and shrunk, so every edge is antialiased.
        Fills G.hits (window pixels) and G.drop_rows (design pixels, for placing dropped programs) """
    s = G.scale
    k = s * 2
    t, ts = T(), text_scale()
    colors, owner = sections()
    W, H, items, foot_y = card_layout()
    im = Image.new('RGBA', (round(W * k), round(H * k)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    radius = RADIUS if sg.running_windows() else 0                      # only Windows can make the corners see-through
    d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=radius * k, fill=rgba(t['card'], 240 if G.glass else 255), outline=t['border'], width=max(1, round(k)))
    hits = []
    # ---- title strip: icon, name, version | S M L, switch, gear, x
    icon = icon_image(launcher_icon, round(18 * k))
    if icon:
        im.alpha_composite(icon, (round(13 * k), round((BTN_Y - 9) * k)))
    title_font = font(True, round(13 * min(ts, 1.25) * k))
    ver_font = font(False, round(12 * k))
    title = fit(d, G.dock_title.upper(), title_font, max(40 * k, (W - 211 - 38 - 14) * k - d.textlength(f'v{version}', font=ver_font)))     # this dock's name
    d.text((38 * k, BTN_Y * k), title, font=title_font, fill=t['dim'], anchor='lm')
    d.text((38 * k + d.textlength(title, font=title_font) + 7 * k, (BTN_Y + 1) * k), f'v{version}', font=ver_font, fill=mix_hex(t['dim'], t['card'], 0.4), anchor='lm')
    size_box = (W - 184, BTN_Y - 10, W - 89, BTN_Y + 10)                    # T S M L
    hot = (isinstance(G.hover, tuple) and G.hover[0] == 'size') or G.scrub is not None
    draw_size_control(d, tuple(v * k for v in size_box), True, t, hot)
    for i, letter in enumerate(SIZE_PRESETS):
        part = (size_box[2] - size_box[0]) / len(SIZE_PRESETS)          # (a third each made L's part reach over the switch once T was added)
        hits.append((size_box[0] + i * part, size_box[1], size_box[0] + (i + 1) * part, size_box[3], ('size', letter)))
    searching = search_row_h()                                          # the search box shows (its magnifier up here is lit)
    for part, cx in (('search', W - 199), ('switch', W - 74), ('gear', W - 47), ('close', W - 20)):
        hits.append((cx - BTN_R, BTN_Y - BTN_R, cx + BTN_R, BTN_Y + BTN_R, part))
        hot = G.hover == part
        if hot:
            d.ellipse(((cx - BTN_R) * k, (BTN_Y - BTN_R) * k, (cx + BTN_R) * k, (BTN_Y + BTN_R) * k), fill=C_CLOSE if part == 'close' else mix_hex(t['text'], t['card'], 0.82))
        color = ('#ffffff' if part == 'close' else t['text']) if hot or (part == 'search' and searching) else mix_hex(t['dim'], t['card'], 0.25)
        if part == 'gear':
            draw_gear(d, cx * k, BTN_Y * k, 6.5 * k, color, mix_hex(t['text'], t['card'], 0.82) if hot else t['card'])
        elif part == 'switch':
            draw_switch(d, cx * k, BTN_Y * k, 6.5 * k, color, to_bar=True)
        elif part == 'search':
            draw_magnifier(d, cx * k, BTN_Y * k, 7 * k, color, max(1, round(1.7 * k)))
        else:
            r = 4.5 * k
            d.line((cx * k - r, BTN_Y * k - r, cx * k + r, BTN_Y * k + r), fill=color, width=max(1, round(1.6 * k)))
            d.line((cx * k - r, BTN_Y * k + r, cx * k + r, BTN_Y * k - r), fill=color, width=max(1, round(1.6 * k)))
    d.line((14 * k, HEAD_H * k, (W - 14) * k, HEAD_H * k), fill=t['track'], width=max(1, round(k)))
    # ---- the search: its box, what matches, the letters to mark, the pick (the one Enter opens)
    found = search_find() if searching else None
    if searching:
        draw_search_box(d, k, t, W, searching, hits)
    lit, marks, heads, pick = None, {}, set(), None
    if found is not None:
        lit, marks, heads = {b.block_num for b in found[0]}, found[1], found[2]
        if found[0]:
            G.search_sel = min(max(0, G.search_sel), len(found[0]) - 1)
            pick = found[0][G.search_sel].block_num
    dim = found is not None and G.search_mode == 'Dim'                  # Dim: what doesn't match fades (Hide: card_layout left it out)
    # ---- headings and programs
    name_font, small_font, head_font = font(False, round(14 * ts * k)), font(False, round(12 * ts * k)), font(True, round(16 * ts * k))
    if not Block.active_blocks:
        d.text((W / 2 * k, (HEAD_H + 6 + ROW_H / 2) * k), 'Drop programs here', font=small_font, fill=t['dim'], anchor='mm')
    elif found is not None and not found[0] and not dim:
        d.text((W / 2 * k, (HEAD_H + 6 + searching + ROW_H / 2) * k), 'No matches  -  Esc clears', font=name_font, fill=t['dim'], anchor='mm')
    position = {n: i for i, n in enumerate(Block.active_blocks)}
    rows, last_x, spots = [], None, []
    now = time.time()
    for kind, b, x, y, w, h in items:
        if x != last_x:
            rows.append([])
            last_x = x
        rows[-1].append((position[b.block_num], kind, x, y, w, h))
        part = ('app' if kind == KIND_APP else 'head', b.block_num)
        hits.append((x, y, x + w, y + h, part))
        if kind == KIND_HEADING:                                        # the section's name in its colour, a thin line under it
            color = colors[b.block_num]
            if dim and b.block_num not in heads and b.block_num not in marks:
                color = mix_hex(color, t['card'], 0.62)
            name = fit(d, b.name, head_font, (w - 16) * k)
            draw_marks(d, name, marks.get(b.block_num), head_font, (x + 8) * k, (y + h * 0.45) * k, t)
            d.text(((x + 8) * k, (y + h * 0.45) * k), name, font=head_font, fill=color, anchor='lm')
            d.line(((x + 8) * k, (y + h - 4) * k, (x + w - 8) * k, (y + h - 4) * k), fill=mix_hex(color, t['card'], 0.55), width=max(1, round(k)))
            continue
        faded = dim and b.block_num not in lit                          # the search, Dim: a program that doesn't match
        if lit is not None and b.block_num in lit:
            spots.append((b.block_num, x, y))
        section = owner.get(b.block_num)
        if section is not None and G.sections:                         # a thin rail in the section's colour down the left of its programs
            rail = mix_hex(colors[section.block_num], t['card'], 0.75 if faded else 0.25)
            d.rounded_rectangle(((x + 1) * k, (y + 4) * k, (x + 3.5) * k, (y + h - 4) * k), radius=1.2 * k, fill=rail)
        flash = G.flash.get(b.block_num, 0) > now                       # just launched / just added: a short accent glow
        if G.hover == part or flash or b.block_num == pick:             # (the search's pick - the one Enter opens - in blue)
            glow = C_CHECKED if flash else C_SELECT if b.block_num == pick else t['text']
            glow = mix_hex(glow, t['card'], 0.55 if flash else 0.4 if b.block_num == pick else 0.88)
            d.rounded_rectangle(((x + 5) * k, (y + 1) * k, (x + w) * k, (y + h - 1) * k), radius=7 * k, fill=glow)
        icon = icon_image(b.iconb64, round(ICON_PX * k))
        ix, iy = (x + 9) * k, (y + (h - ICON_PX) / 2) * k
        if icon:
            im.alpha_composite(see_through(icon, 0.3) if faded else icon, (round(ix + (ICON_PX * k - icon.width) / 2), round(iy + (ICON_PX * k - icon.height) / 2)))
        else:                                                           # no icon: an empty tile
            d.rounded_rectangle((ix, iy, ix + ICON_PX * k, iy + ICON_PX * k), radius=5 * k, fill=mix_hex(t['track'], t['card'], 0.6) if faded else t['track'])
        ver = G.versions.get(b.block_num, '') if G.show_versions else ''
        ver_w = d.textlength(ver, font=small_font) + 10 * k if ver else 0
        if ver and d.textlength(b.name or '(no name)', font=name_font) > (w - 53) * k - ver_w:     # no room for both: the whole name - the version
            ver, ver_w = '', 0                                                                     # is in the bottom line when the mouse is on it
        name = fit(d, b.name or '(no name)', name_font, (w - 53) * k - ver_w)
        draw_marks(d, name, marks.get(b.block_num), name_font, (x + 43) * k, (y + h / 2) * k, t)
        d.text(((x + 43) * k, (y + h / 2) * k), name, font=name_font, fill=mix_hex(t['text'], t['card'], 0.62) if faded else t['text'], anchor='lm')
        if ver:
            d.text(((x + w - 10) * k, (y + h / 2 + 0.5) * k), ver, font=small_font, fill=mix_hex(t['dim'], t['card'], 0.55) if faded else t['dim'], anchor='rm')
    G.drop_rows, G.search_spots = rows, spots
    if G.drag_item:                                                     # a program / section being dragged to a new place: faded where it was
        veil = Image.new('RGBA', im.size, (0, 0, 0, 0))
        vd = ImageDraw.Draw(veil)
        for pos, kind, x, y, w, h in (r for column in rows for r in column):
            if G.drag_item['start'] <= pos < G.drag_item['end']:
                vd.rectangle((x * k, y * k, (x + w) * k, (y + h) * k), fill=rgba(t['card'], 190))
        im.alpha_composite(veil)
    if G.drop_line:                                                     # programs being dragged over: a line where they'll land
        x0, x1, y = G.drop_line
        d.line((x0 * k, y * k, x1 * k, y * k), fill=C_CHECKED, width=max(2, round(2.5 * s)))
        d.ellipse(((x0 - 3) * k, (y - 3) * k, (x0 + 3) * k, (y + 3) * k), fill=C_CHECKED)
    # ---- bottom line: the path of the program under the mouse, or a summary.  Docked + auto-hide: the hide button in the corner away from the edge
    d.line((14 * k, foot_y * k, (W - 14) * k, foot_y * k), fill=t['track'], width=max(1, round(k)))
    room = W - 28
    if hide_shown():                                                    # alone in an empty corner, so it's easy to find (Mike) - not among the title strip's buttons
        room -= 2 * BTN_GAP                                             # (the line's text stays centred, clear of it)
        cx, cy = (W - 22 if G.place == 'Left' else 22), foot_y + FOOT_H / 2
        hits.append((cx - BTN_R, cy - BTN_R, cx + BTN_R, cy + BTN_R, 'hide'))
        hot = G.hover == 'hide'
        if hot:
            d.ellipse(((cx - BTN_R) * k, (cy - BTN_R) * k, (cx + BTN_R) * k, (cy + BTN_R) * k), fill=mix_hex(t['text'], t['card'], 0.82))
        draw_hide(d, cx * k, cy * k, 6.5 * k, t['text'] if hot else mix_hex(t['text'], t['card'], 0.2), max(1, round(2.2 * k)))
    text = G.drag_item['hint'] if G.drag_item else hint(('size', '') if G.scrub is not None else G.hover)
    if '   ·   ' in text and (G.drag_item or G.hover is None):            # a narrow dock: a shorter line instead of a cut-off one
        p = text.split('   ·   ')                                       # (the summary keeps 'drag to rearrange' longest)
        choices = {4: [p, p[:2] + p[3:], p[1:2] + p[3:], p[1:2]], 3: [p, p[:1] + p[2:], p[:1]]}.get(len(p), [p, p[:1]])
        text = next(('   ·   '.join(c) for c in choices if d.textlength('   ·   '.join(c), font=small_font) <= room * k), '   ·   '.join(choices[-1]))
    d.text((W / 2 * k, (foot_y + FOOT_H / 2 - 1) * k), fit(d, text, small_font, room * k, keep_end=True), font=small_font, fill=t['text'] if G.hover or G.scrub else t['dim'], anchor='mm')
    im = im.resize((round(W * s), round(H * s)), Image.LANCZOS)
    off = round(PANEL_SHADOW * s) if G.glass else 0                     # Glass: room all round for a soft shadow
    G.panel_off = off
    if off:
        blur = round(10 * s)
        out = Image.new('RGBA', (im.width + 2 * off, im.height + 2 * off), (0, 0, 0, 0))
        out.alpha_composite(soft_shadow(im.width, im.height, round(radius * s), blur, 120), (off - 2 * blur, off - 2 * blur + round(4 * s)))
        out.alpha_composite(im, (off, off))
        im = out
    G.hits = [(x0 * s + off, y0 * s + off, x1 * s + off, y1 * s + off, part) for x0, y0, x1, y1, part in hits]
    return im


def panel_drop(xd, yd):
    """ Panel style: the list position a drop at design point (xd, yd) lands on, and where to draw the marker line (x0, x1, y) """
    columns = [c for c in G.drop_rows if c]
    if not columns:
        return len(Block.active_blocks), None
    column = min(columns, key=lambda c: 0 if c[0][2] <= xd < c[0][2] + c[0][4] else min(abs(xd - c[0][2]), abs(xd - c[0][2] - c[0][4])))
    for pos, kind, x, y, w, h in column:
        if yd < y + h / 2:
            return pos, (x + 4, x + w - 4, y)
    pos, kind, x, y, w, h = column[-1]
    return pos + 1, (x + 4, x + w - 4, y + h)


# ------------------------------------------------------------ Bar style ------------------------------------------------------------

def bar_items():
    """ What the Bar shows, in order: (kind, block, list position, the heading of its section).  'app' a program; 'sep' a thin line where a
        section starts; 'stack' a whole section as one tile (Stacks layout); then 'size' (S M L), 'switch', 'gear' and 'search' (right-click >
        Search).  Programs and whole sections left out of the Bar (right-click > Show in the Bar) are skipped """
    items, order = [], list(Block.active_blocks.values())
    section, shown, i = None, True, 0
    while i < len(order):
        b = order[i]
        if b.kind == KIND_HEADING:
            section, shown = b, b.bar
            if shown and G.bar_layout == 'Stacks':
                if section_members(b.block_num):
                    if items and items[-1][0] == 'app':
                        items.append(('sep', None, i, None))
                    items.append(('stack', b, i, b))
                i += 1 + len(section_members(b.block_num, bar_only=False))
                continue
            if shown and items and items[-1][0] == 'app':
                items.append(('sep', b, i, b))
        elif shown and b.bar:
            items.append(('app', b, i, section))
        i += 1
    if items and items[-1][0] == 'sep':
        items.pop()
    end = len(order)
    tools = [('size', None, end, None), ('switch', None, end, None), ('gear', None, end, None)]
    tools += [('search', None, end, None)] if search_on() and program_count() else []
    return items + tools + ([('hide', None, end, None)] if hide_shown() else [])


def label_room(items, icon, gap, name_w):
    """ Section names under the bar, Icons layout: a section narrower than its name gets a 'space' either side of its icons (its width in the
        item's block field) - room for the name, so every name sits under its own section instead of crowding its neighbours' """
    out, i = [], 0
    while i < len(items):
        kind, b, pos, sec = items[i]
        if kind != 'app' or sec is None or sec.block_num not in name_w:
            out.append(items[i])
            i += 1
            continue
        j = i
        while j < len(items) and items[j][0] == 'app' and items[j][3] is sec:
            j += 1
        run = items[i:j]                                                # this section's programs
        extra = name_w[sec.block_num] - (len(run) * icon + (len(run) - 1) * gap)
        if extra > 2 * gap:
            w = round(extra / 2) - gap                                  # (each space brings a gap of its own too)
            out += [('space', w, run[0][2], sec)] + run + [('space', w, run[-1][2] + 1, sec)]
        else:
            out += run
        i = j
    return out


def bar_layout():
    """ Bar style sizes in window pixels: the items, their sizes at rest, icon / gap / padding, the bar's thickness, how far magnified icons rise,
        the room for the name bubble, the window size.  Main = along the bar, cross = from the screen edge inward.
        Like the Mac's, the icons get smaller when the bar would not fit along the screen """
    base_items = bar_items()
    M = MAGNIFIES.get(G.magnify, 1.0)
    room = (G.work[3] - G.work[1]) if vertical() else (G.work[2] - G.work[0])
    s = G.scale
    label_px = round(max(12, 12.5 * text_scale()) * G.dpi)             # Section names under the bar: 12 px or more (9 pt)
    name_w = {}                                                         # Section names: how much room each section's name needs along the bar
    if G.bar_labels:
        measure = ImageDraw.Draw(Image.new('L', (1, 1)))
        headings = {(b if kind == 'stack' else sec).block_num: (b if kind == 'stack' else sec) for kind, b, pos, sec in base_items
                    if kind == 'stack' or (kind == 'app' and sec is not None)}
        name_w = {num: round(measure.textlength(h.name, font=font(True, label_px)) + 14 * G.dpi) for num, h in headings.items()}
    for attempt in range(5):
        icon, gap, pad = round(BAR_ICON * s), max(2, round(BAR_GAP * s)), max(3, round(BAR_PAD * s))
        items = label_room(base_items, icon, gap, name_w) if name_w and G.bar_layout == 'Icons' else base_items
        size_thick = min(icon, max(round(icon * 0.5), round(21 * G.dpi)))             # the S M L letters stay readable on a small bar
        size_len = round(size_thick * (len(SIZE_PRESETS) + 0.1))
        slots = [icon if kind == 'app' else max(icon, name_w.get(b.block_num, 0)) if kind == 'stack' else round(BAR_SEP * s) if kind == 'sep' else
                 b if kind == 'space' else size_len if kind == 'size' else round(icon * BAR_TOOL) for kind, b, pos, sec in items]
        rest = sum(slots) + gap * (len(slots) - 1) + 2 * pad
        main = rest + round(icon * (M - 1) * 2.4) + icon + gap + 2 * round(BAR_SIDE * G.scale)     # room to grow: magnification and a gap for a drop
        if main <= room or icon <= 20:
            break
        s *= max(0.5, room / main) * 0.98
    rise = round(icon * (M - 1))
    label = round((BAR_LABEL_SIDE if vertical() else BAR_LABEL) * G.dpi * text_scale())
    edge = round(BAR_EDGE * G.scale)
    lab = round(label_px * 1.55) if G.bar_labels else 0               # their strip, along the bar's screen-edge side, under the rails
    thick = icon + 2 * pad + lab
    cross = edge + thick + rise + label
    W, H = (cross, main) if vertical() else (main, cross)
    return dict(items=items, slots=slots, icon=icon, gap=gap, pad=pad, thick=thick, rise=rise, label=label, edge=edge, rest=rest, main=main, W=W, H=H, M=M,
                size_thick=size_thick, lab=lab, label_px=label_px)


def bar_box(L, m0, c0, m1, c1):
    """ A box in bar coordinates (m along the bar, c inward from the window's screen-edge side) -> window pixels (x0, y0, x1, y1) """
    W, H = L['W'], L['H']
    side = bar_side()
    if side == 'Top':
        return m0, c0, m1, c1
    if side == 'Left':
        return c0, m0, c1, m1
    if side == 'Right':
        return W - c1, m0, W - c0, m1
    return m0, H - c1, m1, H - c0                                       # Bottom and Floating: the bar at the bottom, icons growing upward


def bar_coords(L, x, y):
    """ Window pixels -> bar coordinates (m along the bar, c inward from the screen-edge side) """
    side = bar_side()
    if side == 'Top':
        return x, y
    if side == 'Left':
        return y, x
    if side == 'Right':
        return y, L['W'] - x
    return x, L['H'] - y


def bar_rest_centers(L):
    """ The middle of each item along the bar when nothing is magnified """
    m = (L['main'] - L['rest']) / 2 + L['pad']
    centers = []
    for slot in L['slots']:
        centers.append(m + slot / 2)
        m += slot + L['gap']
    return centers


def bar_targets(L):
    """ Mac-style magnification: how big each item should be with the mouse where it is - full size right under it, falling off smoothly
        over about 2.6 icon widths either side.  Distances are measured on the bar at rest, so nothing wobbles as the icons grow.
        Lines between sections and the S M L control keep their size """
    if G.pointer is None or L['M'] <= 1.0 or G.scrub is not None:
        return [1.0] * len(L['items'])
    u = bar_coords(L, *G.pointer)[0]
    reach = L['icon'] * 2.6
    out = []
    for (kind, b, pos, sec), c in zip(L['items'], bar_rest_centers(L)):
        d = min(1.0, abs(u - c) / reach)
        out.append(1.0 if kind in ('sep', 'size', 'space') else 1 + (L['M'] - 1) * math.cos(d * math.pi / 2) ** 2)
    return out


def bar_drop(L, m):
    """ Bar style: where a drop at m along the bar lands - (list position, item index to open a gap before, the stack it goes into).
        Onto a stack: at the end of its section.  Elsewhere: just before the first item whose middle is past m """
    for i, ((kind, b, pos, sec), c, slot) in enumerate(zip(L['items'], bar_rest_centers(L), L['slots'])):
        if kind == 'stack' and abs(m - c) <= slot * 0.4:
            return section_end(b.block_num), None, b.block_num
        if kind in ('size', 'switch', 'gear', 'search', 'hide') or m < c:
            return pos, i, None
    return len(Block.active_blocks), len(L['items']) - 1, None


def bar_pieces(thick, radius):
    """ The bar's background as three pieces: start cap, a 1-pixel middle to stretch, end cap.  Drawn at 2x and shrunk so the curves are smooth.
        Glass: see-through with a soft sheen across the top.  Cached """
    t = T()
    key = ('bar', thick, radius, G.theme, G.bright, G.glass, vertical())
    if key not in G.icon_cache:
        k = 2
        w2, h2 = (4 * radius + 2) * k, thick * k
        im = Image.new('RGBA', (w2, h2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        light = t.get('light', False)
        border = (255, 255, 255, 46) if G.glass and not light else rgba(t['border'], 255)
        d.rounded_rectangle((0, 0, w2 - 1, h2 - 1), radius=radius * k, fill=rgba(t['card'], 208 if G.glass else 255), outline=border, width=k)
        if G.glass:                                                     # a soft light across the top half - the "glass"
            sheen = Image.new('RGBA', (w2, h2), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sheen)
            for y in range(h2 // 2):
                sd.line((0, y, w2, y), fill=(255, 255, 255, int((22 if light else 30) * (1 - y / (h2 / 2)))))
            mask = Image.new('L', (w2, h2), 0)
            ImageDraw.Draw(mask).rounded_rectangle((k, k, w2 - 1 - k, h2 - 1 - k), radius=max(1, radius * k - k), fill=255)
            im.alpha_composite(Image.composite(sheen, Image.new('RGBA', (w2, h2), (0, 0, 0, 0)), mask))
        im = im.resize((4 * radius + 2, thick), Image.LANCZOS)
        pieces = (im.crop((0, 0, 2 * radius, thick)), im.crop((2 * radius, 0, 2 * radius + 1, thick)), im.crop((2 * radius + 2, 0, 4 * radius + 2, thick)))
        if vertical():
            pieces = tuple(p.transpose(Image.Transpose.TRANSPOSE) for p in pieces)
        G.icon_cache[key] = pieces
    return G.icon_cache[key]


def bounce_lift(num):
    """ Launch bounce: 0..1 of half an icon - two hops, the second smaller.  0 when not bouncing """
    t0 = G.bounce.get(num)
    if t0 is None:
        return 0
    t = (time.time() - t0) / 0.8
    if t >= 1:
        G.bounce.pop(num, None)
        return 0
    return abs(math.sin(t * 2 * math.pi)) * (1 - t)


def draw_stack_tile(im, d, box, heading, color, t, s, lit):
    """ A section as one tile on the Bar: a rounded square tinted in the section's colour with its first four icons in a 2 x 2 grid, and how
        many programs it holds.  lit = open, or a drop is aimed at it """
    x0, y0, x1, y1 = box
    w = x1 - x0
    members = section_members(heading.block_num)
    d.rounded_rectangle(box, radius=round(w * 0.22), fill=rgba(mix_hex(color, t['card'], 0.55 if lit else 0.72), 235 if G.glass else 255),
                        outline=color if lit else mix_hex(color, t['card'], 0.25), width=max(1, round((2.2 if lit else 1.4) * s)))
    pad, gap = w * 0.13, w * 0.07
    mini = max(4, round((w - 2 * pad - gap) / 2))
    for i, b in enumerate(members[:4]):
        icon = icon_image(b.iconb64, mini)
        mx, my = x0 + pad + (i % 2) * (mini + gap), y0 + pad + (i // 2) * (mini + gap)
        if icon:
            im.alpha_composite(icon, (round(mx + (mini - icon.width) / 2), round(my + (mini - icon.height) / 2)))
        else:
            d.rounded_rectangle((mx, my, mx + mini, my + mini), radius=mini * 0.2, fill=t['track'])
    if len(members) > 4:                                                # how many it holds, on a little badge
        f = font(True, max(9, round(11 * G.dpi)))
        text = str(len(members))
        bw, bh = d.textlength(text, font=f) + 10 * G.dpi, 16 * G.dpi
        bx, by = x1 - bw * 0.75, y0 - bh * 0.3
        d.rounded_rectangle((bx, by, bx + bw, by + bh), radius=bh / 2, fill=color)
        d.text((bx + bw / 2, by + bh / 2), text, font=f, fill='#1b1f27' if is_light(color) else '#ffffff', anchor='mm')


def render_bar():
    """ Bar style: the whole window as an RGBA picture - shadow (Glass), the bar, the sections' rails, the icons / stacks at their current
        magnification, the S M L control, switch and gear, a gap where dragged programs would land, and the name bubble.  Fills G.spans """
    if G.bar_geo is None:
        G.bar_geo = bar_layout()
    L = G.bar_geo
    t, s = T(), G.scale
    colors, owner = sections()
    items, n = L['items'], len(L['items'])
    if len(G.mag) != n:
        G.mag = [1.0] * n
    sizes = [slot if kind in ('sep', 'size', 'space') else max(slot, round(L['icon'] * G.mag[i])) if kind == 'stack' else round(slot * G.mag[i])
             for i, ((kind, b, pos, sec), slot) in enumerate(zip(items, L['slots']))]                   # (a stack's place can be wider than its tile: its name)
    opening = round((L['icon'] + L['gap']) * G.drop_open) if G.drop_item is not None else 0
    length = sum(sizes) + L['gap'] * (n - 1) + 2 * L['pad'] + opening
    m0 = round((L['main'] - length) / 2)
    edge, thick, pad, lab = L['edge'], L['thick'], L['pad'], L['lab']
    base, zone = edge + lab, thick - lab                                # the icons' part of the bar: above the strip with the section names
    im = Image.new('RGBA', (L['W'], L['H']), (0, 0, 0, 0))
    radius = max(1, min(round(18 * s), thick // 2, length // 4)) if sg.running_windows() else 0
    bx0, by0, bx1, by1 = bar_box(L, m0, edge, m0 + length, edge + thick)
    if G.glass:
        blur = round(10 * s)
        im.alpha_composite(bar_shadow(length, thick, radius, blur), (bx0 - 2 * blur, by0 - 2 * blur + round(3 * s)))
    if radius:
        start, middle, end = bar_pieces(thick, radius)
        if vertical():
            im.alpha_composite(start, (bx0, by0))
            im.alpha_composite(middle.resize((thick, max(1, length - 4 * radius))), (bx0, by0 + 2 * radius))
            im.alpha_composite(end, (bx0, by1 - 2 * radius))
        else:
            im.alpha_composite(start, (bx0, by0))
            im.alpha_composite(middle.resize((max(1, length - 4 * radius), thick)), (bx0 + 2 * radius, by0))
            im.alpha_composite(end, (bx1 - 2 * radius, by0))
    else:
        ImageDraw.Draw(im).rectangle((bx0, by0, bx1 - 1, by1 - 1), fill=t['card'], outline=t['border'])
    d = ImageDraw.Draw(im)
    places, m = [], m0 + pad                                            # where each item goes along the bar (after a gap for a drop)
    for i, w in enumerate(sizes):
        if opening and i == G.drop_item:
            places.append(('gap', m, opening - L['gap']))
            m += opening
        places.append((i, m, w))
        m += w + L['gap']
    runs = []                                                           # each section's stretch along the bar: [heading block_num, from, to, 'app' / 'stack']
    for entry in places:
        if entry[0] == 'gap':
            continue
        i, m, w = entry
        kind, b, pos, sec = items[i]
        if kind == 'stack':
            runs.append([b.block_num, m, m + w, 'stack'])
        elif kind == 'app' and sec is not None:
            if runs and runs[-1][0] == sec.block_num and runs[-1][3] == 'app' and runs[-1][2] >= m - L['gap'] * 1.5 - (opening or 0):
                runs[-1][2] = m + w
            else:
                runs.append([sec.block_num, m, m + w, 'app'])
    if G.sections:                                                      # each section's rail: a line in its colour along the bar, under its icons
        rail = max(2, round(3 * s))
        c0 = base + max(2, round(pad * 0.3))
        for num, r0, r1, kind in runs:
            if kind == 'app':
                d.rounded_rectangle(bar_box(L, r0 + 2, c0, r1 - 2, c0 + rail), radius=rail / 2, fill=rgba(colors[num], 235))
    G.label_spans = draw_section_labels(im, d, L, runs, colors, t, m0 + pad, m0 + length - pad) if lab else []
    spans, lit, veils = [], bar_lit(), []                               # the search out, with Dim: the programs that match - the rest fades (veils)
    for entry in places:
        if entry[0] == 'gap':                                           # programs being dragged over: an outlined space where they'll land
            m, w = entry[1], entry[2]
            ph = min(L['icon'], w)
            if ph > 6:
                box = bar_box(L, m + (w - ph) / 2, base + pad, m + (w + ph) / 2, base + pad + ph)
                d.rounded_rectangle(box, radius=round(10 * s), outline=C_CHECKED, width=max(2, round(2 * s)), fill=rgba(C_CHECKED, 50) if G.glass else None)
                cx, cy, r = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2, ph * 0.18
                d.line((cx - r, cy, cx + r, cy), fill=C_CHECKED, width=max(2, round(2 * s)))
                d.line((cx, cy - r, cx, cy + r), fill=C_CHECKED, width=max(2, round(2 * s)))
            continue
        i, m, w = entry
        kind, b, pos, sec = items[i]
        if kind == 'app':
            lift = round(bounce_lift(b.block_num) * L['icon'] * 0.5)
            box = bar_box(L, m, base + pad + lift, m + w, base + pad + lift + w)
            icon = icon_image(b.iconb64, w)
            if icon:
                im.alpha_composite(icon, (round(box[0] + (w - icon.width) / 2), round(box[1] + (w - icon.height) / 2)))
            else:
                d.rounded_rectangle(box, radius=round(w * 0.2), fill=t['track'], outline=t['border'])
            if lit is not None and b.block_num not in lit:
                veils.append((box, round(w * 0.2)))
            part, top = ('app', b.block_num), base + pad + lift + w
        elif kind == 'stack':
            lift = round(bounce_lift(b.block_num) * L['icon'] * 0.5) + (round(3 * s) if G.stack_open == b.block_num else 0)
            tile = min(w, round(L['icon'] * G.mag[i]))                  # the tile, in the middle of its place (wider for a long name)
            box = bar_box(L, m + (w - tile) / 2, base + pad + lift, m + (w + tile) / 2, base + pad + lift + tile)
            draw_stack_tile(im, d, box, b, colors[b.block_num], t, s, G.stack_open == b.block_num or G.drop_stack == b.block_num)
            if lit is not None and not any(p.block_num in lit for p in section_members(b.block_num)):
                veils.append((box, round(tile * 0.24)))
            part, top = ('stack', b.block_num), base + pad + lift + tile
        elif kind == 'sep':
            mid, lw = m + w / 2, max(1, round(1.2 * s))
            line = colors[b.block_num] if b is not None and G.sections else mix_hex(t['text'], t['card'], 0.72)
            d.rectangle(bar_box(L, mid - lw / 2, base + zone * 0.2, mid + lw / 2, base + zone * 0.8), fill=line)
            part, top = (('head', b.block_num) if b is not None else None), edge + thick
        elif kind == 'space':                                           # room for a section's name: nothing to draw, nothing to point at
            continue
        elif kind == 'size':
            st = L['size_thick']
            box = bar_box(L, m, base + (zone - st) / 2, m + w, base + (zone + st) / 2)
            draw_size_control(d, box, not vertical(), t, (isinstance(G.hover, tuple) and G.hover[0] == 'size') or G.scrub is not None)
            part, top = ('size', box), base + (zone + st) / 2
        else:                                                           # the switch, the gear and the search button
            box = bar_box(L, m, base + (zone - w) / 2, m + w, base + (zone + w) / 2)
            hot = G.hover == kind or (kind == 'search' and G.stack_open == 'search')
            color = t['text'] if hot else mix_hex(t['dim'], t['card'], 0.15)
            cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
            if hot:
                r = w * 0.56
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=mix_hex(t['text'], t['card'], 0.84))
            if kind == 'gear':
                draw_gear(d, cx, cy, w * 0.36, color, mix_hex(t['text'], t['card'], 0.84) if hot else rgba(t['card'], 208 if G.glass else 255))
            elif kind == 'hide':
                draw_hide(d, cx, cy, w * 0.26, color, max(2, round(w * 0.08)))
            elif kind == 'search':
                draw_magnifier(d, cx, cy, w * 0.38, color, max(2, round(w * 0.07)))
            else:
                draw_switch(d, cx, cy, w * 0.36, color, to_bar=False)
            part, top = kind, base + (zone + w) / 2
        spans.append((m - L['gap'] / 2, m + w + L['gap'] / 2, part, top))
    if veils:                                                           # the search, Dim: what doesn't match fades into the bar
        veil = Image.new('RGBA', im.size, (0, 0, 0, 0))
        vd = ImageDraw.Draw(veil)
        for box, r in veils:
            vd.rounded_rectangle(box, radius=r, fill=rgba(t['card'], 185))
        im.alpha_composite(veil)
    G.spans = spans
    G.bar_extent = (m0, m0 + length)
    if G.stack_open is not None:                                        # its fly-out is the label now
        pass
    elif G.scrub is not None or (isinstance(G.hover, tuple) and G.hover[0] == 'size'):
        bar_bubble(im, d, L, 'size')
    elif G.hover is not None:
        bar_bubble(im, d, L, G.hover)
    elif not any(kind in ('app', 'stack') for kind, b, pos, sec in items):
        bar_bubble(im, d, L, None, 'Drop programs here')
    G.hits = []
    return im


def draw_section_labels(im, d, L, runs, colors, t, lo, hi):
    """ Section names under the bar: each section's name in its colour (lighter or darker where that wouldn't read on the bar) under its rail
        or its stack, in the strip along the bar's screen-edge side - turned on its side on a Left / Right bar.  A name wider than its section
        borrows room from its neighbours; when there isn't room for every name, the longest are shortened.  Returns where each name went:
        [(m0, m1, heading block_num)] """
    if not runs:
        return []
    f, gap = font(True, L['label_px']), round(12 * G.dpi)
    pole = '#000000' if t.get('light') else '#ffffff'
    names = [[Block.active_blocks[num].name if num in Block.active_blocks else '', (r0 + r1) / 2, num] for num, r0, r1, kind in runs]
    widths = [d.textlength(name, font=f) for name, c, num in names]
    room = hi - lo - gap * (len(names) - 1)
    for attempt in range(3 * len(names)):                               # not room for every name: shorten the longest
        if sum(widths) <= room or max(widths) <= 30 * G.dpi:
            break
        i = widths.index(max(widths))
        names[i][0] = fit(d, names[i][0], f, max(30 * G.dpi, widths[i] - (sum(widths) - room) - 1))
        widths[i] = d.textlength(names[i][0], font=f)
    xs = [c - w / 2 for (name, c, num), w in zip(names, widths)]
    for i in range(len(xs)):                                            # left to right: no name on top of the one before
        xs[i] = max(xs[i], lo if i == 0 else xs[i - 1] + widths[i - 1] + gap)
    for i in range(len(xs) - 1, -1, -1):                                # right to left: none past the bar's end
        xs[i] = min(xs[i], (hi if i == len(xs) - 1 else xs[i + 1] - gap) - widths[i])
    c = L['edge'] + L['lab'] * 0.5 + 1                                  # the middle of the strip
    spans = []
    for (name, centre, num), w, x in zip(names, widths, xs):
        color = readable(colors.get(num, t['heading']), t['card'], 4.5, pole)
        if vertical():                                                  # a side bar: the name on its side, reading along the bar
            tag = Image.new('RGBA', (max(1, round(w) + 4), round(L['label_px'] * 1.5)), (0, 0, 0, 0))
            ImageDraw.Draw(tag).text((2, tag.height / 2), name, font=f, fill=color, anchor='lm')
            tag = tag.rotate(90 if bar_side() == 'Left' else -90, expand=True)
            px, py = bar_box(L, x, c, x, c)[:2]
            im.alpha_composite(tag, (round(px - tag.width / 2), round(py)))
        else:
            px, py = bar_box(L, x, c, x, c)[:2]
            d.text((px, py), name, font=f, fill=color, anchor='lm')
        spans.append((x - gap / 2, x + w + gap / 2, num))
    return spans


def bar_bubble(im, d, L, part, text=None):
    """ The name bubble beside the item under the mouse (above a bottom bar, beside a side bar), with a little pointer toward it.
        A program: its name, version and - in its colour - its section.  A section (a line between sections, or a stack): its name big,
        in its colour, and how many programs it has """
    sd, ts, t = G.dpi, text_scale(), T()
    small, big, sub_f = font(False, round(13 * sd * ts)), font(True, round(22 * sd * ts)), font(False, round(12 * sd * ts))
    span = None
    if part is not None:
        span = next((sp for sp in G.spans if sp[2] == part or (part == 'size' and isinstance(sp[2], tuple) and sp[2][0] == 'size')), None)
    runs = []                                                           # (text, font, colour) pieces, side by side
    if text is not None:
        runs.append((text, small, '#eceff6'))
    elif span is None:
        return
    elif part == 'gear':                                                # this dock's name, then what the gear does
        runs.append((G.dock_title, small, mix_hex(t['heading'], '#ffffff', 0.15)))
        runs.append(('Programs  -  add, remove and order them   ·   right-click for settings', sub_f, '#9aa3b2'))
    elif part == 'switch':
        runs.append(('Switch to the Panel  -  names and versions', small, '#eceff6'))
    elif part == 'hide':
        runs.append(('Hide', small, '#eceff6'))
        runs.append(('point at the edge to bring it back' if G.autohide else 'click its handle to bring it back', sub_f, '#9aa3b2'))
    elif part == 'search':
        runs.append(('Search', small, '#eceff6'))
        runs.append(('find a program by its name  -  or click the bar and type', sub_f, '#9aa3b2'))
    elif part == 'size':
        runs.append((f'Size {round(G.size * 100)}%', small, '#eceff6'))
        if G.scrub is None:
            runs.append(('click T S M L  -  or drag across them', sub_f, '#9aa3b2'))
    elif isinstance(part, tuple) and part[1] in Block.active_blocks:
        b = Block.active_blocks[part[1]]
        colors, owner = sections()
        if part[0] == 'app':
            runs.append((b.name or '(no name)', small, '#eceff6'))
            if G.show_versions and G.versions.get(b.block_num):
                runs.append((G.versions[b.block_num], sub_f, '#9aa3b2'))
            section = owner.get(b.block_num)
            if section is not None and G.bubble_section:                # right-click > Section name in the bubble
                runs.append((section.name, sub_f, mix_hex(colors[section.block_num], '#ffffff', 0.25)))
        else:                                                           # a section: its name big, in its colour
            count = len(section_members(b.block_num))
            runs.append((b.name or '(no name)', big, mix_hex(colors.get(b.block_num, t['heading']), '#ffffff', 0.15)))
            runs.append((f'{count} program{"s" * (count != 1)}' + ('   ·   click to open' if part[0] == 'stack' else ''), sub_f, '#9aa3b2'))
    else:
        return
    if span is None:
        mc, top = (G.bar_extent[0] + G.bar_extent[1]) / 2, L['edge'] + L['thick']
    else:
        mc, top = (span[0] + span[1]) / 2, span[3]
    room = (BAR_LABEL_SIDE - 40) * sd * ts if vertical() else 560 * sd * ts
    while len(runs) > 1 and sum(d.textlength(r[0], font=r[1]) for r in runs) + 10 * sd * (len(runs) - 1) > room:
        runs.pop()                                                      # no room on a side bar: the section's name goes first, then the version -
    first, f0, c0 = runs[0]                                             # before the name is shortened (it was cut to fit beside a section name that then went)
    rest = sum(d.textlength(r[0], font=r[1]) + 10 * sd for r in runs[1:])
    runs[0] = (fit(d, first, f0, max(40 * sd, room - rest)), f0, c0)
    tw = sum(d.textlength(r[0], font=r[1]) for r in runs) + 10 * sd * (len(runs) - 1)
    tallest = max(getattr(r[1], 'size', 13 * sd) for r in runs)
    pw, ph = tw + 24 * sd, tallest * 1.85
    gap = 9 * sd
    if vertical():
        mc = min(max(mc, ph / 2 + 2), L['main'] - ph / 2 - 2)
        box = bar_box(L, mc - ph / 2, top + gap, mc + ph / 2, top + gap + pw)
    else:
        mc = min(max(mc, pw / 2 + 2), L['main'] - pw / 2 - 2)
        box = bar_box(L, mc - pw / 2, top + gap, mc + pw / 2, top + gap + ph)
    box = tuple(round(v) for v in box)
    fill = (20, 24, 33, 236) if G.glass else (20, 24, 33, 255)
    d.rounded_rectangle(box, radius=round(min(ph / 2, 10 * sd)), fill=fill, outline=(255, 255, 255, 40) if G.glass else '#3a4458')
    if span is not None:                                                # the little pointer, toward the icon
        tip, side = bar_box(L, mc - 5 * sd, top + 3 * sd, mc + 5 * sd, top + gap + 1), bar_side()
        if side == 'Top':
            d.polygon(((tip[0], tip[3]), (tip[2], tip[3]), ((tip[0] + tip[2]) / 2, tip[1])), fill=fill)
        elif side == 'Left':
            d.polygon(((tip[2], tip[1]), (tip[2], tip[3]), (tip[0], (tip[1] + tip[3]) / 2)), fill=fill)
        elif side == 'Right':
            d.polygon(((tip[0], tip[1]), (tip[0], tip[3]), (tip[2], (tip[1] + tip[3]) / 2)), fill=fill)
        else:
            d.polygon(((tip[0], tip[1]), (tip[2], tip[1]), ((tip[0] + tip[2]) / 2, tip[3])), fill=fill)
    x, cy = (box[0] + box[2]) / 2 - tw / 2, (box[1] + box[3]) / 2
    for i, (txt, f, color) in enumerate(runs):
        d.text((x, cy + (0.5 * sd if i else 0)), txt, font=f, fill=color, anchor='lm')
        x += d.textlength(txt, font=f) + 10 * sd


def bar_part_at(x, y):
    """ Bar style: the item at window pixel (x, y), or None.  On the S M L control: ('size', 'S' / 'M' / 'L') """
    L = G.bar_geo
    if not L or G.hidden:
        return None
    m, c = bar_coords(L, x, y)
    if c < -2 or c > L['edge'] + L['thick'] + L['rise'] + 4:
        return None
    if L['lab'] and c < L['edge'] + L['lab']:                           # on the strip of section names: that section
        return next((('head', num) for m0, m1, num in G.label_spans if m0 <= m < m1), None)
    for m0, m1, part, top in G.spans:
        if m0 <= m < m1:
            if isinstance(part, tuple) and part[0] == 'size':
                return ('size', size_letter_at(part[1], not vertical(), x, y))
            return part
    return None


def bar_track_start(window):
    if G.style == 'Bar' and not G.tracking and not G.hidden:
        G.tracking = True
        window.TKroot.after(1, lambda: bar_tick(window))


def bar_tick(window):
    """ About 60 times a second while the mouse is over the bar, something is magnified, bouncing, or files are being dragged over it:
        follow the mouse, ease the magnification, and redraw when anything changed """
    if window is not G.window or G.style != 'Bar' or G.hidden:
        G.tracking = False
        return
    try:
        px, py = window.TKroot.winfo_pointerxy()
        x, y = px - window.TKroot.winfo_rootx(), py - window.TKroot.winfo_rooty()
    except Exception:
        G.tracking = False
        return
    L = G.bar_geo or bar_layout()
    G.bar_geo = L
    m, c = bar_coords(L, x, y)
    inside = G.bar_extent[0] - L['gap'] <= m <= G.bar_extent[1] + L['gap'] and -L['edge'] <= c <= L['edge'] + L['thick'] + L['rise'] + 6
    now = time.time()
    if inside or G.scrub is not None:
        G.pointer, G.out_since = (x, y), None
    elif G.pointer is not None and G.stack_open is None:               # (a stack flown out: the bar stays as it is while the mouse is on the fly-out)
        G.out_since = G.out_since or now
        if now - G.out_since > 0.1:
            G.pointer = None
    hover = (bar_part_at(x, y) if inside else None) if G.pointer is not None and G.scrub is None else (G.hover if G.scrub is not None else None)
    if hover != G.hover:
        G.hover = hover
        window[K_IMAGE].Widget.configure(cursor='hand2' if hover else '')
    if G.stacks_hover and isinstance(hover, tuple) and hover[0] == 'stack' and hover[1] != G.stack_open and G.press is None:
        if G.rest is None or G.rest[0] != hover:                        # Open stacks on hover: the mouse resting on one opens it
            G.rest = (hover, now, False)
        elif not G.rest[2] and now - G.rest[1] >= STACK_REST:
            G.rest = (hover, G.rest[1], True)
            window.write_event_value(K_STACK_OPEN, hover[1])
    else:
        G.rest = None
    targets = bar_targets(L)
    if len(G.mag) != len(targets):
        G.mag = [1.0] * len(targets)
    G.mag = [cur + (tgt - cur) * 0.42 for cur, tgt in zip(G.mag, targets)]
    open_target = 1.0 if G.drop_item is not None and G.drop_index is not None and G.drop_stack is None else 0.0    # aimed at a stack: no gap
    G.drop_open += (open_target - G.drop_open) * 0.35
    if open_target == 0.0 and G.drop_open < 0.02:
        G.drop_open = 0.0
        if G.drop_index is None or G.drop_stack is not None:
            G.drop_item = None
    settled = all(abs(cur - tgt) < 0.003 for cur, tgt in zip(G.mag, targets)) and abs(G.drop_open - open_target) < 0.02
    signature = (G.pointer, G.hover, tuple(round(v, 3) for v in G.mag), G.drop_item, G.drop_stack, round(G.drop_open, 2), tuple(G.bounce), G.stack_open)
    if signature != G.last_signature or G.bounce:
        G.last_signature = signature
        redraw(window)
    if G.pointer is not None or not settled or G.bounce or G.drop_index is not None or G.drop_item is not None:
        window.TKroot.after(16, lambda: bar_tick(window))
    else:
        G.tracking = False


# ------------------------------------------------------------ Showing a picture: Glass (per-pixel transparency) or the colour key ------------------------------------------------------------

def ulw_api():
    """ The Windows calls Glass needs, declared once (ctypes) """
    if G.api is None:
        import ctypes
        from ctypes import wintypes
        user32 = ctypes.WinDLL('user32', use_last_error=True)
        gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)

        class BLENDFUNCTION(ctypes.Structure):
            _fields_ = [('BlendOp', ctypes.c_ubyte), ('BlendFlags', ctypes.c_ubyte), ('SourceConstantAlpha', ctypes.c_ubyte), ('AlphaFormat', ctypes.c_ubyte)]

        class BITMAPINFOHEADER(ctypes.Structure):
            _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG), ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD),
                        ('biCompression', wintypes.DWORD), ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
                        ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)]

        LONG_PTR = ctypes.c_ssize_t
        user32.GetWindowLongPtrW.restype, user32.GetWindowLongPtrW.argtypes = LONG_PTR, [wintypes.HWND, ctypes.c_int]
        user32.SetWindowLongPtrW.restype, user32.SetWindowLongPtrW.argtypes = LONG_PTR, [wintypes.HWND, ctypes.c_int, LONG_PTR]
        user32.GetDC.restype, user32.GetDC.argtypes = wintypes.HDC, [wintypes.HWND]
        user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
        user32.UpdateLayeredWindow.restype = wintypes.BOOL
        user32.UpdateLayeredWindow.argtypes = [wintypes.HWND, wintypes.HDC, ctypes.POINTER(wintypes.POINT), ctypes.POINTER(wintypes.SIZE), wintypes.HDC,
                                               ctypes.POINTER(wintypes.POINT), wintypes.DWORD, ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD]
        gdi32.CreateCompatibleDC.restype, gdi32.CreateCompatibleDC.argtypes = wintypes.HDC, [wintypes.HDC]
        gdi32.CreateDIBSection.restype = wintypes.HBITMAP
        gdi32.CreateDIBSection.argtypes = [wintypes.HDC, ctypes.c_void_p, wintypes.UINT, ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD]
        gdi32.SelectObject.restype, gdi32.SelectObject.argtypes = wintypes.HGDIOBJ, [wintypes.HDC, wintypes.HGDIOBJ]
        gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
        gdi32.DeleteDC.argtypes = [wintypes.HDC]
        G.api = dict(ctypes=ctypes, wintypes=wintypes, user32=user32, gdi32=gdi32, BLENDFUNCTION=BLENDFUNCTION, BITMAPINFOHEADER=BITMAPINFOHEADER)
    return G.api


def glass_setup(window):
    """ Glass: from now on the window shows exactly the picture handed to UpdateLayeredWindow, transparency and all.
        Returns the window's Glass surface (keep it for glass_present / glass_free), or None if that isn't possible here """
    if not sg.running_windows():
        return None
    try:
        api = ulw_api()
        hwnd = int(window.TKroot.wm_frame(), 16)                       # the toplevel's outer (wrapper) window
        ex = api['user32'].GetWindowLongPtrW(hwnd, -20)
        api['user32'].SetWindowLongPtrW(hwnd, -20, ex & ~0x80000)      # clear and set WS_EX_LAYERED: forgets tk's alpha setting, which would block UpdateLayeredWindow
        api['user32'].SetWindowLongPtrW(hwnd, -20, ex | 0x80000)
        return {'hwnd': hwnd, 'dc': None}
    except Exception:
        return None


def glass_free(surface):
    if surface and surface.get('dc'):
        api = ulw_api()
        hdc, hbmp, bits, old, size = surface['dc']
        api['gdi32'].SelectObject(hdc, old)
        api['gdi32'].DeleteObject(hbmp)
        api['gdi32'].DeleteDC(hdc)
        surface['dc'] = None


def glass_present(surface, im, opacity):
    """ Hand an RGBA picture to Windows as a window's whole content, each pixel with its own transparency, the whole at opacity %.  True if it worked """
    api = ulw_api()
    ctypes, wintypes, user32, gdi32 = api['ctypes'], api['wintypes'], api['user32'], api['gdi32']
    w, h = im.size
    dc = surface.get('dc')
    if not dc or dc[4] != (w, h):
        glass_free(surface)
        screen = user32.GetDC(None)
        hdc = gdi32.CreateCompatibleDC(screen)
        user32.ReleaseDC(None, screen)
        header = api['BITMAPINFOHEADER'](ctypes.sizeof(api['BITMAPINFOHEADER']), w, -h, 1, 32, 0, 0, 0, 0, 0, 0)       # top-down 32-bit
        bits = ctypes.c_void_p()
        hbmp = gdi32.CreateDIBSection(hdc, ctypes.byref(header), 0, ctypes.byref(bits), None, 0)
        if not hbmp:
            gdi32.DeleteDC(hdc)
            return False
        dc = (hdc, hbmp, bits, gdi32.SelectObject(hdc, hbmp), (w, h))
        surface['dc'] = dc
    try:
        data = im.convert('RGBa').tobytes('raw', 'BGRa')                # premultiplied alpha, in Windows' BGRA order
    except ValueError:                                                  # an older Pillow without that packer
        r, g, b, a = im.split()
        data = Image.merge('RGBA', (ImageChops.multiply(b, a), ImageChops.multiply(g, a), ImageChops.multiply(r, a), a)).tobytes()
    ctypes.memmove(dc[2], data, len(data))
    blend = api['BLENDFUNCTION'](0, 0, max(0, min(255, round(opacity * 2.55))), 1)
    return bool(user32.UpdateLayeredWindow(surface['hwnd'], None, None, ctypes.byref(wintypes.SIZE(w, h)), dc[0], ctypes.byref(wintypes.POINT(0, 0)), 0,
                                           ctypes.byref(blend), 2))


def show_picture(win, key, surface, im, opacity, keep):
    """ Put a picture on a window: with Glass (a surface) as the window's own see-through content, else as a tk image on the colour key (the
        window's alpha is then its opacity).  keep: a dict that holds the tk images - tk forgets images nobody holds.  False if Glass failed """
    if surface:
        if keep.get('blank_size') != im.size:                           # tk sizes the window from a blank picture of the same size
            keep['blank'], keep['blank_size'] = ImageTk.PhotoImage(Image.new('RGBA', im.size, (0, 0, 0, 0))), im.size
            win[key].Widget.configure(image=keep['blank'])
        return glass_present(surface, im, opacity)
    keep['photo'] = ImageTk.PhotoImage(im)
    win[key].Widget.configure(image=keep['photo'])
    return True


def present(window, im, handle=False):
    """ Show the dock's picture (or, auto-hidden, its handle) """
    resized = G.win_size != im.size
    G.win_size, G.last_image = im.size, im
    if not handle:
        G.full_size = im.size
    if not show_picture(window, K_IMAGE, G.layered if G.glass else None, im, G.opacity, G.keep):
        window.write_event_value(K_REBUILD, 'glass failed')
        return
    widget = window[K_IMAGE].Widget                                     # the handle slides along its edge: say so with the pointer
    if handle:
        widget.configure(cursor='sb_v_double_arrow' if G.place in ('Left', 'Right') else 'sb_h_double_arrow')
    elif str(widget.cget('cursor')).endswith('double_arrow'):
        widget.configure(cursor='')
    if resized and not handle and not G.sliding and not G.hidden and G.place != 'Floating':
        place_window(window)


def redraw(window):
    """ Draw the dock in its style and show it - or just its handle while auto-hidden """
    if window is not G.window:
        return
    G.redraw_due = False                                                # (a redraw_soon() waiting is done by this one)
    if G.hidden:
        present(window, render_handle(), handle=True)
        return
    present(window, render_bar() if G.style == 'Bar' else render_card())


def set_opacity(window, pct):
    """ The whole dock's opacity - Glass passes it to Windows with the picture, otherwise it's the window's alpha """
    if G.glass and G.layered:
        if G.last_image is not None:
            glass_present(G.layered, G.last_image, pct)
    else:
        window.set_alpha(pct / 100)


# ------------------------------------------------------------ Where the dock goes: floating, docked to an edge, auto-hidden ------------------------------------------------------------

def monitor_area(x, y):
    """ (monitor rectangle, work area) of the monitor that holds screen point x, y - the work area leaves out the taskbar.  Whole screen when unknown """
    if sg.running_windows():
        try:
            import ctypes
            from ctypes import wintypes

            class MONITORINFO(ctypes.Structure):
                _fields_ = [('cbSize', wintypes.DWORD), ('rcMonitor', wintypes.RECT), ('rcWork', wintypes.RECT), ('dwFlags', wintypes.DWORD)]

            user32 = ctypes.windll.user32
            user32.MonitorFromPoint.restype = wintypes.HMONITOR
            user32.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
            user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFO)]
            info = MONITORINFO()
            info.cbSize = ctypes.sizeof(MONITORINFO)
            if user32.GetMonitorInfoW(user32.MonitorFromPoint(wintypes.POINT(int(x), int(y)), 2), ctypes.byref(info)):     # 2 = the nearest monitor
                mon, work = info.rcMonitor, info.rcWork
                return (mon.left, mon.top, mon.right, mon.bottom), (work.left, work.top, work.right, work.bottom)
        except Exception:
            pass
    w, h = sg.Window.get_screen_size()
    return (0, 0, w, h), (0, 0, w, h)


def move_to(window, x, y, firmly=False):
    """ Move a window to screen point x, y.  firmly: and again a moment later if the window system has put it back where it first opened
        (X11 can do that to a window that starts invisible) - unless it has been moved again meanwhile """
    x, y = round(x), round(y)
    window.placed_at = (x, y)
    window.TKroot.geometry(f'+{x}+{y}')
    if firmly:
        def check():
            try:
                if getattr(window, 'placed_at', None) == (x, y) and (window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty()) != (x, y):
                    window.TKroot.geometry(f'+{x}+{y}')
            except Exception:
                pass
        for ms in (80, 250, 600):
            window.TKroot.after(ms, check)


def on_a_screen(x, y):
    """ Is screen point x, y on one of the monitors? """
    mon, work = monitor_area(x, y)
    return mon[0] <= x < mon[2] and mon[1] <= y < mon[3]


def window_rect(window):
    """ (x, y, width, height) of the dock on the screen """
    w, h = G.win_size or (window.TKroot.winfo_width(), window.TKroot.winfo_height())
    return window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty(), w, h


def onto_screen(x, y, w, h):
    """ x, y moved so a w x h window is all on the screen that holds its middle (left / top kept if it's bigger than the screen) """
    mon, work = monitor_area(x + w // 2, y + h // 2)
    return max(work[0], min(x, work[2] - w)), max(work[1], min(y, work[3] - h))


def put_on_screen(window):
    """ A floating dock: at its remembered spot, moved fully onto that screen if it hangs off one.  The first time: the lower right corner
        (Panel) or the bottom centre (Bar) """
    w, h = G.win_size
    if G.location:
        x, y = G.location
    else:
        left, top, right, bottom = G.work
        gap = round(12 * G.dpi)
        x, y = (right - w - gap, bottom - h - gap) if G.style == 'Panel' else ((left + right - w) // 2, bottom - h - gap)
    move_to(window, *onto_screen(x, y, w, h), firmly=True)


def keep_corner(window, before):
    """ A floating dock that changed size stays put at its side nearest the screen's edges - a dock in the lower right corner grows up and
        to the left, one at the bottom centre stays centred - and stays on the screen """
    x, y, w, h = before
    W, H = G.win_size
    if (W, H) == (w, h):
        return
    mon, work = monitor_area(x + w // 2, y + h // 2)

    def keep(start, size, new, low, high):                              # one direction: keep the near edge - or the middle, in the middle third
        middle, third = start + size / 2, (high - low) / 3
        if low + third <= middle <= high - third:
            return round(middle - new / 2)
        return start + size - new if middle > (low + high) / 2 else start

    move_to(window, *onto_screen(keep(x, w, W, work[0], work[2]), keep(y, h, H, work[1], work[3]), W, H))


def remember_location(window, at=None):
    """ A floating dock: keep where it is now (at: where a drag left it), for this style.  Moved onto another monitor: fit to that one """
    if G.place != 'Floating' or window is not G.window:
        return
    try:
        G.location = tuple(at) if at else (window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty())
    except (sg.tk.TclError, AttributeError):                           # the window is already gone: keep the spot saved last
        return
    save_style_setting('LOCATION', list(G.location))
    w, h = G.win_size or (0, 0)
    mon, work = monitor_area(G.location[0] + w // 2, G.location[1] + h // 2)
    if work != G.work:
        G.mon, G.work = mon, work
        relayout(window)


def docked_position(place=None, work=None, size=None, along=-1):
    """ Docked: where the dock shows on its edge of the monitor's work area (so the taskbar stays clear) - centred, or where it was slid to:
        along = its middle as a share of the edge (G.along; None = centred), never past the edge's ends.  The arguments: another edge / monitor /
        size (where a dragged Bar would go) """
    place, work = place or G.place, work or G.work
    w, h = size or G.full_size
    along = G.along if along == -1 else along
    left, top, right, bottom = work
    gap = round(2 * G.dpi)
    if place in ('Bottom', 'Top'):
        x = (left + right - w) // 2 if along is None else round(left + along * (right - left) - w / 2)
        return max(left, min(x, right - w)), (bottom - h - gap if place == 'Bottom' else top + gap)
    y = (top + bottom - h) // 2 if along is None else round(top + along * (bottom - top) - h / 2)
    return (left + gap if place == 'Left' else right - w - gap), max(top, min(y, bottom - h))


def place_window(window):
    """ Docked: put the dock in its place on its edge - or, auto-hidden, its handle """
    if G.place == 'Floating' or window is not G.window:
        return
    G.shown_pos = docked_position()
    move_to(window, *(handle_position() if G.hidden else G.shown_pos), firmly=True)


def hidden_position():
    """ Where an auto-hidden dock slides to: its own size over its edge """
    x, y = G.shown_pos
    w, h = G.full_size
    return {'Bottom': (x, y + h), 'Top': (x, y - h), 'Left': (x - w, y), 'Right': (x + w, y)}[G.place]


def render_handle():
    """ What an auto-hidden dock leaves at its edge: a small pill - point at it (or rest the mouse at the edge) and the dock flies out.
        Name on the handle: a tag with the dock's name instead, reading along the edge """
    t, sd = T(), G.dpi
    if G.handle_name:
        f, m = font(True, round(12.5 * sd * text_scale())), round(3 * sd)
        tw = ImageDraw.Draw(Image.new('L', (1, 1))).textlength(G.dock_title, font=f)
        w, h = round(max(84 * sd, tw + 26 * sd)) + 2 * m, round(f.size * 1.75) + 2 * m
        im = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = G.handle_color                                              # Handle colour: the tag in that colour, its name dark or light to read
        d.rounded_rectangle((m * 2, m * 2, w * 2 - m * 2 - 1, h * 2 - m * 2 - 1), radius=h - 2 * m, fill=rgba(c or t['card'], 235 if G.glass else 255),
                            outline=rgba(mix_hex(c, '#000000', 0.35) if c else t['border'], 255), width=2)
        im = im.resize((w, h), Image.LANCZOS)
        text = ('#14161c' if is_light(c) else '#ffffff') if c else readable(t['heading'], t['card'], 4.5, '#000000' if t.get('light') else '#ffffff')
        ImageDraw.Draw(im).text((w / 2, h / 2), G.dock_title, font=f, fill=text, anchor='mm')
        if G.place in ('Left', 'Right'):
            im = im.rotate(90 if G.place == 'Left' else -90, expand=True)
        return im
    length, thick, m = round(84 * sd), max(4, round(6 * sd)), round(5 * sd)
    w, h = (thick + 2 * m, length + 2 * m) if G.place in ('Left', 'Right') else (length + 2 * m, thick + 2 * m)
    im = Image.new('RGBA', (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((m * 2, m * 2, w * 2 - m * 2 - 1, h * 2 - m * 2 - 1), radius=thick, fill=rgba(G.handle_color or t['dim'], 220 if G.glass else 255),
                                         outline=rgba(t['card'], 255), width=2)
    return im.resize((w, h), Image.LANCZOS)


def handle_position():
    """ Where the handle sits: against the edge, in the middle of where the dock shows """
    w, h = G.win_size
    fx, fy = G.shown_pos
    fw, fh = G.full_size
    left, top, right, bottom = G.work
    cx, cy = fx + fw // 2, fy + fh // 2
    return {'Bottom': (cx - w // 2, bottom - h), 'Top': (cx - w // 2, top), 'Left': (left, cy - h // 2), 'Right': (right - w, cy - h // 2)}[G.place]


def slide(window, show):
    """ Auto-hide: slide the dock over its edge, leaving its handle - or fly it back out """
    if G.anim is not None:
        try:
            window.TKroot.after_cancel(G.anim)
        except Exception:
            pass
        G.anim = None
    if show:
        G.hidden, G.sliding = False, True
        redraw(window)                                                  # the whole dock again - the window grows back from the handle
        G.shown_pos = docked_position()                                 # (the list may have changed while it was tucked away)
        start_x, start_y = hidden_position()
        move_to(window, start_x, start_y)
        end_x, end_y = G.shown_pos
    else:
        G.sliding = True
        start_x, start_y = window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty()
        end_x, end_y = hidden_position()
    started = time.time()

    def step():
        if window is not G.window:
            return
        t = min(1.0, (time.time() - started) * 1000 / SLIDE_MS)
        e = 1 - (1 - t) ** 3                                            # ease out
        move_to(window, start_x + (end_x - start_x) * e, start_y + (end_y - start_y) * e)
        if t < 1:
            G.anim = window.TKroot.after(12, step)
            return
        G.anim, G.sliding = None, False
        if not show:                                                    # tucked away: just the handle shows
            G.hidden, G.pointer, G.hover, G.search, G.search_sel = True, None, None, '', 0          # (a search clears as the dock tucks away)
            present(window, render_handle(), handle=True)
            move_to(window, *handle_position())
            if not G.autohide:                                          # hidden by hand: the handle stays in sight above other windows
                dock_above(window, True)
        elif not G.autohide:
            dock_above(window, False)

    step()


def at_edge(px, py):
    """ Auto-hide: is the pointer at the dock's edge of the monitor, within reach of where the dock shows? """
    left, top, right, bottom = G.mon
    x0, y0 = G.shown_pos
    w, h = G.full_size
    reach = round(40 * G.dpi)
    along_x, along_y = x0 - reach <= px < x0 + w + reach, y0 - reach <= py < y0 + h + reach
    return {'Bottom': py >= bottom - 2 and along_x, 'Top': py <= top + 1 and along_x, 'Left': px <= left + 1 and along_y, 'Right': px >= right - 2 and along_y}[G.place]


def autohide_tick(window):
    """ About 11 times a second with auto-hide on: fly the dock out when the pointer is on its handle or rests at its edge, tuck it away again
        when the pointer has left (not while a stack is open or files are being dragged over it) """
    if window is not G.window or not G.autohide or G.place == 'Floating':
        return
    try:
        px, py = window.TKroot.winfo_pointerxy()
        wx, wy = window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty()
    except Exception:
        return
    now = time.time()
    if G.hidden and G.anim is None and G.press is None:                 # (the handle held: it's being dragged)
        w, h = G.win_size
        if wx <= px < wx + w and wy <= py < wy + h:                     # on the handle: out after a short rest - a press first drags the handle
            G.edge_since = None
            if G.handle_since is None:
                G.handle_since = now
            if G.handle_since >= 0 and now - G.handle_since >= G.flyout:          # (At once: on the first look)
                G.handle_since = None
                slide(window, True)
        elif at_edge(px, py):
            G.handle_since = None
            G.edge_since = G.edge_since or now
            if now - G.edge_since >= max(AUTOHIDE_DWELL, G.flyout):
                G.edge_since = None
                slide(window, True)
        else:
            G.edge_since, G.handle_since = None, None
    elif G.anim is None and not G.hidden:
        x0, y0 = G.shown_pos
        w, h = G.full_size
        margin = round(30 * G.dpi)
        inside = x0 - margin <= px < x0 + w + margin and y0 - margin <= py < y0 + h + margin
        busy = G.drop_index is not None or G.stack_open is not None or G.scrub is not None or G.drag_item is not None or G.press is not None
        if inside or busy or (G.search and G.focus):                    # (typing in its search: it stays out)
            G.out_since = None
        else:
            G.out_since = G.out_since or now
            if now - G.out_since >= AUTOHIDE_DELAY:
                G.out_since = None
                slide(window, False)
    window.TKroot.after(AUTOHIDE_POLL_MS, lambda: autohide_tick(window))


# ------------------------------------------------------------ Moving a docked dock: along its edge, or (a Bar) to another edge ------------------------------------------------------------

def dock_drag(window, p, x_root, y_root):
    """ A docked dock dragged - a Bar by any spot of it, a Panel by its title strip or an empty spot, an auto-hidden one by its handle.  Along its
        edge it slides (not past the edge's ends).  Pulled off its edge it follows the mouse instead - let go there and it floats - and an edge it
        would dock on lights up """
    left, top, right, bottom = G.work
    upright = G.place in ('Left', 'Right')
    inward = {'Bottom': p['y'] - y_root, 'Top': y_root - p['y'], 'Left': x_root - p['x'], 'Right': p['x'] - x_root}[G.place]     # pulled off its edge this far
    if p['pulled'] or inward > EDGE_PULL * G.dpi:
        if not p['pulled']:
            p['pulled'] = True
            window[K_IMAGE].Widget.configure(cursor='fleur')
        move_to(window, p['wx'] + x_root - p['x'], p['wy'] + y_root - p['y'])
        edge_drag_update(window, x_root, y_root)
        return
    fw, fh = G.full_size
    sx, sy = p['shown'] or docked_position()
    start, end, size = (top, bottom, fh) if upright else (left, right, fw)
    middle = (sy + fh / 2 + y_root - p['y']) if upright else (sx + fw / 2 + x_root - p['x'])
    middle = min(max(middle, start + size / 2), end - size / 2)
    G.along = (middle - start) / max(1, end - start)
    G.shown_pos = docked_position()
    move_to(window, *(handle_position() if G.hidden else G.shown_pos))


def finish_dock_drag(window, p, x_root, y_root):
    """ A drag of the dock let go.  At an edge (it lit up): docked there (K_DOCK - the window is made again).  A docked dock pulled off its edge and
        let go away from every edge: floating there (K_FLOAT).  Slid along its edge: that spot is kept.  A floating dock: where it is now (K_MOVED) """
    target, G.edge_target = G.edge_target, None
    if G.preview is not None:
        show_edge_preview(window, None)
        dock_above(window, False)
    if G.place == 'Floating' or p['pulled']:
        if target is not None:
            window.write_event_value(K_DOCK, (target['place'], target['mon'], target['along'], (p['wx'], p['wy'])))
            return
        if G.place != 'Floating':
            window.write_event_value(K_FLOAT, (body_rect(window), G.place in ('Left', 'Right')))
            return
    if G.place == 'Floating':
        window.write_event_value(K_MOVED, (p['wx'] + x_root - p['x'], p['wy'] + y_root - p['y']))
        return
    save_style_setting('ALONG', round(G.along, 4) if G.along is not None else None)
    if G.hidden:
        G.handle_since = -1                                             # the handle was just put somewhere: no flying out until the mouse leaves it


def bar_footprint(place, work):
    """ A Bar docked on place (an edge of the monitor with this work area): (its window's size, the bar's box at rest in that window) """
    key = ('footprint', place, work, G.scale, G.text, G.bar_labels, G.magnify, G.bar_layout, G.sections, tuple((b.block_num, b.bar) for b in Block.active_blocks.values()))
    if key not in G.icon_cache:
        saved = G.place, G.work
        try:
            G.place, G.work = place, work
            L = bar_layout()
            m0 = (L['main'] - L['rest']) / 2
            G.icon_cache[key] = (L['W'], L['H']), bar_box(L, m0, L['edge'], m0 + L['rest'], L['edge'] + L['thick'])
        finally:
            G.place, G.work = saved
    return G.icon_cache[key]


def body_rect(window):
    """ The visible dock on the screen (x0, y0, x1, y1): the bar itself, the Panel's card - not the see-through room around them - or the handle """
    x, y = window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty()
    w, h = G.win_size or (window.TKroot.winfo_width(), window.TKroot.winfo_height())
    if G.hidden:
        return x, y, x + w, y + h
    if G.style == 'Bar' and G.bar_geo:
        L = G.bar_geo
        b = bar_box(L, G.bar_extent[0], L['edge'], G.bar_extent[1], L['edge'] + L['thick'])
        return x + b[0], y + b[1], x + b[2], y + b[3]
    off = G.panel_off
    return x + off, y + off, x + w - off, y + h - off


def panel_footprint(place, work):
    """ The Panel docked on place (an edge of the monitor with this work area): (its window's size, the card's box in that window) """
    key = ('panel footprint', place, work, G.scale, G.text, G.columns, G.glass, G.show_versions, G.dock_title, G.autohide,
           tuple((b.block_num, b.kind, b.name) for b in Block.active_blocks.values()))
    if key not in G.icon_cache:
        saved = G.place, G.work, G.fit_rows
        try:
            G.place, G.work = place, work
            W, H = card_layout()[:2]
        finally:
            G.place, G.work, G.fit_rows = saved
        off = round(PANEL_SHADOW * G.scale) if G.glass else 0
        w, h = round(W * G.scale) + 2 * off, round(H * G.scale) + 2 * off
        G.icon_cache[key] = (w, h), (off, off, w - off, h - off)
    return G.icon_cache[key]


def edge_target(window, x_root, y_root):
    """ A dock being dragged with the mouse here: the edge it would dock on - the nearest edge of the monitor under the mouse when the mouse is within
        EDGE_SNAP of it (or past it, on the taskbar), else an edge the dock is pushed EDGE_RAM past - and where along it.
        {'place', 'mon', 'along', 'rect' (the dock there, on the screen)} or None """
    mon, work = monitor_area(x_root, y_root)
    away = {'Left': x_root - work[0], 'Right': work[2] - 1 - x_root, 'Top': y_root - work[1], 'Bottom': work[3] - 1 - y_root}
    place = min(away, key=away.get)
    if away[place] > EDGE_SNAP * G.dpi:                                 # the mouse isn't at an edge: is the dock rammed into one?
        b = body_rect(window)
        over = {'Left': work[0] - b[0], 'Right': b[2] - work[2], 'Top': work[1] - b[1], 'Bottom': b[3] - work[3]}
        place = max(over, key=over.get)
        if over[place] < EDGE_RAM * G.dpi:
            return None
    along = (x_root - work[0]) / max(1, work[2] - work[0]) if place in ('Top', 'Bottom') else (y_root - work[1]) / max(1, work[3] - work[1])
    size, box = bar_footprint(place, work) if G.style == 'Bar' else panel_footprint(place, work)
    x, y = docked_position(place, work, size, min(1.0, max(0.0, along)))
    left, top, right, bottom = work
    along = ((x + size[0] / 2 - left) / max(1, right - left)) if place in ('Top', 'Bottom') else ((y + size[1] / 2 - top) / max(1, bottom - top))    # (kept off the ends)
    return {'place': place, 'mon': mon, 'along': round(along, 4), 'rect': (x + box[0], y + box[1], x + box[2], y + box[3])}


def edge_drag_update(window, x_root, y_root):
    """ A dock being dragged: light up where it would dock (nothing away from the edges) """
    G.edge_target = edge_target(window, x_root, y_root)
    show_edge_preview(window, G.edge_target['rect'] if G.edge_target else None)


def show_edge_preview(window, rect):
    """ The highlight where a dragged dock would dock - a see-through blue bar with a bright outline, at rect (screen pixels).  None: hide it """
    tk = sg.tk
    pv = G.preview
    if rect is None:
        if pv is not None:
            try:
                pv.withdraw()
            except tk.TclError:
                G.preview = None
        return
    pad = round(5 * G.dpi)
    x0, y0, x1, y1 = (round(v) for v in rect)
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    w, h = max(8, x1 - x0), max(8, y1 - y0)
    try:
        if pv is None or not pv.winfo_exists():
            pv = G.preview = tk.Toplevel(window.TKroot)
            pv.overrideredirect(True)
            pv.attributes('-topmost', True)
            pv.configure(bg=TRANSPARENT)
            try:
                pv.attributes('-alpha', 0.6)
                if sg.running_windows():
                    pv.attributes('-transparentcolor', TRANSPARENT)
            except tk.TclError:
                pass
            pv.label = tk.Label(pv, bd=0, highlightthickness=0, bg=TRANSPARENT)
            pv.label.pack()
            G.preview_size = None
        if G.preview_size != (w, h):                                    # drawn without smoothing: the colour key would fringe soft edges
            im = Image.new('RGB', (w, h), TRANSPARENT)
            r, line = min(round(16 * G.dpi), w // 2, h // 2), max(2, round(3 * G.dpi))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=C_CHECKED)
            d.rounded_rectangle((line, line, w - 1 - line, h - 1 - line), radius=max(1, r - line), fill=mix_hex(C_CHECKED, '#0b1f3a', 0.45))
            pv.photo = ImageTk.PhotoImage(im)
            pv.label.configure(image=pv.photo)
            G.preview_size = (w, h)
        pv.geometry(f'{w}x{h}+{x0}+{y0}')
        if pv.state() != 'normal':
            pv.deiconify()
            pv.lift()
            dock_above(window, True)                                    # the dragged dock stays on top of its highlight
    except tk.TclError:
        G.preview = None


def dock_above(window, on):
    """ While a Bar is dragged over its highlight (which stays on top of everything): the dock on top of it.  on=False: back to how it was.
        Windows' own call, so the Glass surface is left alone """
    if not sg.running_windows():
        return
    try:
        import ctypes
        hwnd = int(window.TKroot.wm_frame(), 16)
        keep = G.on_top or (G.autohide and G.place != 'Floating')
        insert = -1 if on or keep else -2                               # HWND_TOPMOST / HWND_NOTOPMOST
        ctypes.windll.user32.SetWindowPos(hwnd, insert, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)    # no size, no move, no activate
    except Exception:
        pass


def float_at(window, body, upright):
    """ A docked dock pulled off its edge and let go away from every edge: floating where it was let go - a Bar off a side edge runs up and down.
        body = where the visible dock was on the screen: the floating one is put there """
    G.place = 'Floating'
    save_style_setting('PLACE', 'Floating')
    if G.style == 'Bar':
        G.float_vertical = upright
        save_style_setting('VERTICAL', upright)
    G.location = (body[0], body[1])
    window = rebuild(window)
    nb = body_rect(window)                                              # the new window's dock: onto where the dragged one was
    x, y, w, h = window_rect(window)
    x, y = onto_screen(x + body[0] - nb[0], y + body[1] - nb[1], w, h)
    move_to(window, x, y, firmly=True)
    remember_location(window, (x, y))
    float_side_check(window)
    return window


def dock_at(window, place, mon, along, float_spot):
    """ A dock let go at an edge: docked there, on that monitor, where it was let go along the edge.  A floating one keeps its floating spot (where
        the drag started) """
    if G.place == 'Floating':
        G.location = tuple(float_spot)
        save_style_setting('LOCATION', list(G.location))
    G.place, G.along = place, along
    G.monitor_pt = ((mon[0] + mon[2]) // 2, (mon[1] + mon[3]) // 2)
    for name, value in (('PLACE', place), ('MONITOR', list(G.monitor_pt)), ('ALONG', along)):
        save_style_setting(name, value)
    return rebuild(window)


def float_side_check(window):
    """ A Floating vertically bar opens (its bubble, its stacks) toward the middle of the screen: moved past the middle, it turns around - the bar
        itself stays where it was let go """
    if G.style != 'Bar' or G.place != 'Floating' or not G.float_vertical or not G.bar_geo:
        return
    x, y, w, h = window_rect(window)
    L = G.bar_geo
    bar_x = x + (L['edge'] if G.float_side == 'Left' else w - L['edge'] - L['thick'])        # the bar's left side on the screen
    side = 'Right' if bar_x + L['thick'] / 2 > (G.mon[0] + G.mon[2]) / 2 else 'Left'
    if side == G.float_side:
        return
    G.float_side = side
    G.bar_geo, G.mag, G.last_signature = None, [], None
    redraw(window)
    L = G.bar_geo or bar_layout()
    nx = bar_x - (L['edge'] if side == 'Left' else G.win_size[0] - L['edge'] - L['thick'])
    move_to(window, nx, y)
    remember_location(window, (nx, y))


# ------------------------------------------------------------ Mouse, menus, the size control, drops ------------------------------------------------------------

def part_at(x, y):
    """ The part of the dock at window pixel (x, y): ('app', n), ('head', n), ('stack', n), ('size', letter), 'switch', 'gear', 'close', 'search',
        the search box ('find') and its x ('clear') - or None """
    if G.hidden:
        return None
    if G.style == 'Bar':
        return bar_part_at(x, y)
    for x0, y0, x1, y1, part in G.hits:
        if part in ('gear', 'close', 'switch', 'hide', 'search'):
            if math.hypot(x - (x0 + x1) / 2, y - (y0 + y1) / 2) <= BTN_R * G.scale:
                return part
        elif x0 <= x <= x1 and y0 <= y <= y1:
            return part
    return None


def part_menu(part):
    """ The right-click menu for what's under the mouse: a program's own menu, a section's (heading or stack), or the dock's.
        The dock's is a sub-menu of the others """
    if not isinstance(part, tuple) or part[0] not in ('app', 'head', 'stack') or part[1] not in Block.active_blocks:
        return make_menu()
    b = Block.active_blocks[part[1]]
    tick = lambda on: '✓ ' if on else '    '
    title = '!' + menu_label(b.name or '(no name)')
    dock = ['---', f'    {menu_label(G.dock_title)}', make_menu()[1]]
    if b.kind == KIND_HEADING:
        chosen = G.head_colors.get(b.name)
        colours = ([f'{tick(chosen is None)}{HEAD_AUTO}::{K_E_COLOR}{HEAD_AUTO}'] + [f'{tick(chosen == c)}{n}::{K_E_COLOR}{n}' for n, c in zip(SECTION_NAMES, SECTION_PALETTE)] +
                   ['---', f'{tick(chosen is not None and chosen not in SECTION_PALETTE)}{HANDLE_CUSTOM}::{K_E_COLOR}{HANDLE_CUSTOM}'])
        return ['', [title, '---', f'    Add a program here...::{K_E_ADD_HERE}', f'    Add a link here...::{K_E_ADD_LINK}', f'    Rename...::{K_E_RENAME}',
                     '    Colour', colours, f'{tick(b.bar)}Show this section in the Bar::{K_E_BAR}', f'    Remove this heading::{K_E_REMOVE}'] + dock]
    if is_link(b.path):                                                 # a link: no folder, source or sharper icon
        return ['', [title, '---', f'    Open::{K_E_OPEN}', f'    Copy the link::{K_E_COPY}', f'    Rename...::{K_E_RENAME}', f'{tick(b.bar)}Show in the Bar::{K_E_BAR}',
                     f'    Remove from the dock::{K_E_REMOVE}'] + dock]
    items = [title, '---', f'    Open::{K_E_OPEN}', f'    Open its folder::{K_E_FOLDER}']
    if b.path.lower().endswith(('.py', '.pyw')):
        items.append(f'    Edit the source::{K_E_EDIT}')
    items += [f'    Copy the path::{K_E_COPY}', f'    Rename...::{K_E_RENAME}', f'{tick(b.bar)}Show in the Bar::{K_E_BAR}', f'    Sharper icon - fetch it again::{K_E_SHARPEN}',
              f'    Remove from the dock::{K_E_REMOVE}']
    return ['', items + dock]


def set_size(window, size, save=True):
    """ The dock's size (1.0 = M) - from the S M L control, dragging across it, or the menu.  A floating dock keeps its corner nearest the
        screen's edges where it is """
    before = window_rect(window)
    G.size = round(min(SIZE_MAX, max(SIZE_MIN, size)), 3)
    G.scale = G.dpi * G.size
    relayout(window, before)
    if save:
        save_style_setting('SIZE', round(G.size, 3))
        set_right_click_menu(window, make_menu())


def bind_mouse(window):
    """ Hover, clicks, right-clicks, the S M L control - and dragging a floating dock (done here rather than with grab_anywhere, so a drag
        is never taken for a click: the dock only starts moving once the mouse has gone DOCK_DRAG pixels, and a press that moved the dock
        never starts a program).  The S M L control: a click picks a size, a drag across it sets any size.  Panel: a drag that starts on a
        program or a heading moves that entry (a heading: its whole section) - the dock moves by its title strip or an empty spot """
    widget = window[K_IMAGE].Widget

    def motion(e):
        if G.hidden:
            return
        if G.style == 'Bar':
            bar_track_start(window)
            return
        part = part_at(e.x, e.y)
        if part != G.hover and not (G.press and G.press['moving']):
            widget.configure(cursor='xterm' if part == 'find' else 'hand2' if part else '')
            window.write_event_value(K_HOVER, part)

    def press(e):
        part = part_at(e.x, e.y)
        if search_on() and not G.hidden:                                # click the dock, then type: its search takes the keys
            try:
                window.TKroot.focus_force()
            except Exception:
                pass
        if part == 'find' and G.search_all:                             # a click in the search box lets go of Ctrl+A's selection
            G.search_all = False
            redraw_soon(window)
        G.press = {'x': e.x_root, 'y': e.y_root, 'part': part, 'wx': window.TKroot.winfo_rootx(), 'wy': window.TKroot.winfo_rooty(), 'moving': False,
                   'handle': G.hidden, 'along': G.along, 'shown': G.shown_pos, 'pulled': False}             # (docked: where it was, to go back to)
        if isinstance(part, tuple) and part[0] == 'size':
            G.scrub = {'x': e.x_root, 'y': e.y_root, 'start': G.size, 'moved': False, 'letter': part[1], 'pending': None}

    def drag(e):
        p = G.press
        if p is None:
            return
        dx, dy = e.x_root - p['x'], e.y_root - p['y']
        if G.scrub is not None:                                         # across S M L: any size between
            delta = dy if vertical() else dx
            if abs(delta) >= 4:
                G.scrub['moved'] = True
            if G.scrub['moved']:
                if G.scrub['pending'] is None:                          # redraw once per idle moment, with the newest size
                    window.TKroot.after_idle(lambda: scrub_apply(window))
                G.scrub['pending'] = min(SIZE_MAX, max(SIZE_MIN, G.scrub['start'] + delta / G.dpi * 0.004))
            return
        if G.drag_item is not None:                                     # a program or section being moved within the Panel
            drag_entry(window, e.x_root, e.y_root)
            return
        if not p['moving'] and math.hypot(dx, dy) >= DOCK_DRAG:
            if G.style == 'Panel' and G.search.strip() and isinstance(p['part'], tuple) and p['part'][0] in ('app', 'head'):
                return                                                  # while searching, nothing moves (the list may show only part of itself)
            if G.style == 'Panel' and isinstance(p['part'], tuple) and p['part'][0] in ('app', 'head') and start_entry_drag(window, p):
                widget.configure(cursor='fleur')                       # pressed on a program or a heading: that moves, not the dock
                drag_entry(window, e.x_root, e.y_root)
                return
            if G.place != 'Floating' and G.style == 'Bar' and not G.tip_shown and isinstance(p['part'], tuple) and p['part'][0] in ('app', 'stack'):
                G.tip_shown = True                                      # the Bar doesn't rearrange - say where it's done (once)
                window.write_event_value(K_TIP, 'Dragging slides the bar along its edge - pull it off the edge to float it, or into another edge to dock it there.\n'
                                                'To rearrange your programs, use the Panel:\nclick the switch, then drag them where you want. The Bar shows the same order.')
            p['moving'] = True
            if not p['handle']:
                widget.configure(cursor='fleur')
        if p['moving']:
            if G.place == 'Floating':
                move_to(window, p['wx'] + dx, p['wy'] + dy)
                edge_drag_update(window, e.x_root, e.y_root)            # near an edge, or pushed into one: it lights up where it would dock
            else:
                dock_drag(window, p, e.x_root, e.y_root)

    def release(e):
        p, G.press = G.press, None
        if G.scrub is not None:
            scrub, G.scrub = G.scrub, None
            if not scrub['moved']:
                set_size(window, SIZE_PRESETS[scrub['letter']])
            else:
                if scrub['pending'] is not None:
                    G.size = scrub['pending']
                near = min(SIZE_PRESETS.values(), key=lambda v: abs(v - G.size))
                set_size(window, near if abs(near - G.size) < 0.04 else G.size)       # close to T, S, M or L: it snaps there
            return
        if p is None:
            return
        if G.drag_item is not None:                                     # a program or section let go: it lands on the line (outside the dock: no change)
            finish_entry_drag(window)
            widget.configure(cursor='hand2' if part_at(e.x, e.y) else '')
            return
        if p['moving']:                                                 # the dock was dragged - never a launch
            if not G.hidden:
                widget.configure(cursor='hand2' if part_at(e.x, e.y) else '')
            finish_dock_drag(window, p, e.x_root, e.y_root)
        elif p['handle'] and G.hidden:                                  # a click on the handle: out at once
            slide(window, True)
        elif math.hypot(e.x_root - p['x'], e.y_root - p['y']) < DOCK_DRAG and p['part'] is not None and part_at(e.x, e.y) == p['part']:
            window.write_event_value(K_CLICK, p['part'])

    def right_press(e):                                                 # before the menu shows (on release): pick the menu for what's under the mouse
        part = part_at(e.x, e.y)
        G.menu_target = part[1] if isinstance(part, tuple) and part[0] in ('app', 'head', 'stack') else None
        G.menu_at = (e.x_root, e.y_root)                                # questions it asks (Rename...) open here
        set_right_click_menu(window, part_menu(part))

    def enter(e):
        if not G.hidden and G.style == 'Bar':
            bar_track_start(window)

    def leave(e):
        if G.style != 'Bar' and G.hover and G.scrub is None and not (G.press and G.press['moving']):
            window.write_event_value(K_HOVER, None)

    widget.bind('<Motion>', motion, add='+')
    widget.bind('<Enter>', enter, add='+')
    widget.bind('<Leave>', leave, add='+')
    widget.bind('<ButtonPress-1>', press, add='+')
    widget.bind('<B1-Motion>', drag, add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')
    widget.bind('<ButtonPress-3>', right_press, add='+')

    def focus(on):                                                      # the search box shows its caret while the dock has the keyboard
        if G.focus != on:
            G.focus = on
            if window is G.window and G.style == 'Panel' and not G.hidden and search_row_h():
                redraw(window)

    window.TKroot.bind('<KeyPress>', lambda e: search_key(window, e), add='+')
    window.TKroot.bind('<FocusIn>', lambda e: focus(True), add='+')
    window.TKroot.bind('<FocusOut>', lambda e: focus(False), add='+')


def scrub_apply(window):
    """ Dragging across S M L: show the newest size (once per idle moment, however fast the mouse moves) """
    if G.scrub is None or G.scrub['pending'] is None or window is not G.window:
        return
    size, G.scrub['pending'] = G.scrub['pending'], None
    set_size(window, size, save=False)


def drop_over(window, x_root, y_root):
    """ Programs are being dragged over the dock from Explorer: show where they'd land - a gap opening in the Bar (or a stack lighting up),
        a line in the Panel.  None = they left """
    if window is not G.window:
        return
    if x_root is None or G.hidden:
        G.drop_index, G.drop_line, G.drop_stack = None, None, None
        if G.style == 'Bar':
            bar_track_start(window)
        else:
            redraw(window)
        return
    x, y = x_root - window.TKroot.winfo_rootx(), y_root - window.TKroot.winfo_rooty()
    if G.style == 'Bar':
        L = G.bar_geo or bar_layout()
        G.drop_index, item, G.drop_stack = bar_drop(L, bar_coords(L, x, y)[0])
        if item is not None:
            G.drop_item = item
        bar_track_start(window)
    else:
        if G.search:                                                    # programs dragged in: the whole list again, so they land where they're dropped
            G.search, G.search_sel = '', 0
            redraw(window)
        index, line = panel_drop((x - G.panel_off) / G.scale, (y - G.panel_off) / G.scale)
        if (index, line) != (G.drop_index, G.drop_line):
            G.drop_index, G.drop_line = index, line
            redraw(window)


def drop_line_at(index):
    """ Panel: the line for list position index (x0, x1, y in design pixels) - at the top of the entry there, or under the last one """
    rows = [r for column in G.drop_rows for r in column]
    for pos, kind, x, y, w, h in rows:
        if pos == index:
            return x + 4, x + w - 4, y
    if not rows:
        return None
    pos, kind, x, y, w, h = max(rows, key=lambda r: r[0])
    return x + 4, x + w - 4, y + h


def drag_target(pos):
    """ A program / section dragged in the Panel: the list position it lands on for drop position pos - None where it wouldn't move.  A program
        goes anywhere; a heading brings its programs, so a section lands between sections (before a heading, or at the end) """
    drag = G.drag_item
    start, end = drag['start'], drag['end']
    if pos is None or start <= pos <= end:
        return None
    if drag['kind'] == KIND_APP:
        return pos
    order = list(Block.active_blocks.values())
    edges = [i for i, b in enumerate(order) if b.kind == KIND_HEADING and not start <= i <= end] + ([len(order)] if end < len(order) else [])
    return min(edges, key=lambda i: (abs(i - pos), i), default=None)


def render_ghost(drag):
    """ The copy of the dragged entry that follows the mouse: its row, outlined - a heading also says how many programs come with it """
    s, t, ts = G.scale, T(), text_scale()
    k = s * 2
    w, h = drag['size']
    im = Image.new('RGBA', (round(w * k), round(h * k)), rgba(t['card']))
    d = ImageDraw.Draw(im)
    b = Block.active_blocks[drag['num']]
    if drag['kind'] == KIND_HEADING:
        colors, owner = sections()
        n = drag['end'] - drag['start'] - 1
        count, small, head_font = (f'+ {n} program{"s" * (n != 1)}' if n else ''), font(False, round(12 * ts * k)), font(True, round(16 * ts * k))
        count_w = d.textlength(count, font=small) + 12 * k if count else 0
        d.text((8 * k, h * 0.5 * k), fit(d, b.name, head_font, (w - 16) * k - count_w), font=head_font, fill=colors.get(b.block_num, t['heading']), anchor='lm')
        if count:
            d.text(((w - 10) * k, h * 0.5 * k), count, font=small, fill=t['dim'], anchor='rm')
    else:
        icon = icon_image(b.iconb64, round(ICON_PX * k))
        ix, iy = 9 * k, (h - ICON_PX) / 2 * k
        if icon:
            im.alpha_composite(icon, (round(ix + (ICON_PX * k - icon.width) / 2), round(iy + (ICON_PX * k - icon.height) / 2)))
        name_font = font(False, round(14 * ts * k))
        d.text((43 * k, h / 2 * k), fit(d, b.name or '(no name)', name_font, (w - 53) * k), font=name_font, fill=t['text'], anchor='lm')
    d.rectangle((0, 0, im.width - 1, im.height - 1), outline=C_CHECKED, width=max(2, round(1.5 * k)))
    return im.resize((round(w * s), round(h * s)), Image.LANCZOS)


def start_entry_drag(window, p):
    """ A press on a program or a heading in the Panel became a drag: that entry (a heading: its whole section) is faded in place and a copy of
        it follows the mouse.  False if its row isn't on the card """
    kind, num = p['part']
    order = list(Block.active_blocks)
    if num not in order:
        return False
    start = order.index(num)
    end = start + 1 + (len(section_members(num, bar_only=False)) if kind == 'head' else 0)
    row = next((r for column in G.drop_rows for r in column if r[0] == start), None)                    # (list position, kind, x, y, w, h) in design pixels
    if row is None:
        return False
    b = Block.active_blocks[num]
    G.drag_item = drag = {'num': num, 'kind': KIND_HEADING if kind == 'head' else KIND_APP, 'start': start, 'end': end, 'size': (row[4], row[5]), 'index': None,
                          'at': (round(16 * G.dpi), round(10 * G.dpi)), 'ghost': None}     # the copy sits just right of and below the mouse: the line stays in sight
    n = end - start - 1
    what = f'the {b.name} section' + (f' and its {n} program{"s" * (n != 1)}' if n else '') if kind == 'head' else (b.name or 'this program')
    drag['hint'] = f'Moving {what}   ·   let go where the blue line is   ·   outside the dock: no change'
    try:
        photo = ImageTk.PhotoImage(render_ghost(drag))
        ghost = sg.tk.Toplevel(window.TKroot)
        ghost.overrideredirect(True)
        ghost.attributes('-topmost', True)
        try:
            ghost.attributes('-alpha', 0.85)
        except sg.tk.TclError:
            pass
        label = sg.tk.Label(ghost, image=photo, bd=0, highlightthickness=0)
        label.photo = photo
        label.pack()
        drag['ghost'], drag['ghost_w'] = ghost, photo.width()
        place_ghost(drag, p['x'], p['y'])
    except Exception:                                                   # no copy then - the line still shows where it goes
        drag['ghost'] = None
    redraw(window)
    return True


def place_ghost(drag, x_root, y_root):
    """ The dragged entry's copy: just right of and below the mouse - left of it near the screen's right edge, so it stays in sight """
    ghost = drag['ghost']
    if ghost is None:
        return
    gx = x_root + drag['at'][0]
    if gx + drag['ghost_w'] > G.mon[2]:
        gx = x_root - drag['at'][0] - drag['ghost_w']
    try:
        ghost.geometry(f'+{round(gx)}+{round(y_root + drag["at"][1])}')
    except sg.tk.TclError:
        drag['ghost'] = None


def drag_entry(window, x_root, y_root):
    """ The dragged entry's copy follows the mouse; the blue line moves to where it would land (none outside the dock, or where it wouldn't move) """
    drag = G.drag_item
    place_ghost(drag, x_root, y_root)
    x, y = x_root - window.TKroot.winfo_rootx(), y_root - window.TKroot.winfo_rooty()
    w, h = G.win_size or (0, 0)
    off = G.panel_off
    index = None
    if off <= x < w - off and off <= y < h - off:
        index = drag_target(panel_drop((x - off) / G.scale, (y - off) / G.scale)[0])
    if index != drag['index']:
        drag['index'] = index
        G.drop_line = drop_line_at(index) if index is not None else None
        redraw(window)


def finish_entry_drag(window):
    """ The dragged entry was let go: the event loop moves it to the line (K_REORDER).  No line (outside the dock, or no move): nothing changes """
    drag, G.drag_item = G.drag_item, None
    G.drop_line = None
    if drag['ghost'] is not None:
        try:
            drag['ghost'].destroy()
        except sg.tk.TclError:
            pass
    if drag['index'] is not None:
        window.write_event_value(K_REORDER, (drag['start'], drag['end'], drag['index']))
    else:
        redraw(window)


def move_entries(window, start, end, index):
    """ List positions start .. end-1 (a program, or a heading with its programs) move to list position index - saved at once, with a short glow """
    order = list(Block.active_blocks.values())
    if not 0 <= start < end <= len(order) or start <= index <= end:
        redraw(window)
        return
    moving, rest = order[start:end], order[:start] + order[end:]
    at = index - (end - start) if index > end else index
    rest[at:at] = moving
    Block.active_blocks = {b.block_num: b for b in rest}
    save_entries()
    now = time.time()
    for b in moving:
        G.flash[b.block_num] = now + 0.8
    G.hover = None
    relayout(window)
    window.TKroot.after(900, lambda: redraw(window))


def setup_drop(window):
    """ Let programs be dragged from Explorer onto the dock (tkinterdnd2, through psgdnd).  The drop arrives in the event loop as K_DROP """
    widget = window[K_IMAGE].Widget
    try:
        psgdnd.TkinterDnD._require(window.TKroot)
        widget.drop_target_register(psgdnd.DND_FILES)
    except Exception:
        return False
    action = getattr(psgdnd, 'COPY', 'copy')

    def over(e):
        if G.hidden:                                                    # dragged onto the handle: fly out first
            slide(window, True)
        drop_over(window, e.x_root, e.y_root)
        return action

    def leave(e):
        drop_over(window, None, None)
        return action

    def drop(e):
        files = list(widget.tk.splitlist(e.data))
        window.write_event_value(K_DROP, (files, e.x_root, e.y_root))
        return action

    widget.dnd_bind('<<DropEnter>>', over)
    widget.dnd_bind('<<DropPosition>>', over)
    widget.dnd_bind('<<DropLeave>>', leave)
    widget.dnd_bind('<<Drop>>', drop)
    return True


# ------------------------------------------------------------ Changing the list from the dock ------------------------------------------------------------

def pointer():
    """ Where the mouse is on the screen """
    try:
        return tuple(G.window.TKroot.winfo_pointerxy())
    except Exception:
        return tuple(v // 2 for v in sg.Window.get_screen_size())


def notice(text, color='#2e7d32', seconds=2, beside_dock=False):
    """ A short message beside the mouse - where you are looking - that goes away by itself.  beside_dock: next to a docked dock instead, on
        its inward side (above a Bar at the bottom...), so it doesn't cover it """
    px, py = pointer()
    w = round((max(len(line) for line in text.split('\n')) * 9 + 60) * G.dpi)
    h = round((40 + 22 * text.count('\n')) * G.dpi)
    x, y = px + round(16 * G.dpi), py + round(20 * G.dpi)
    if beside_dock and G.window is not None:
        dx, dy, dw, dh = window_rect(G.window)
        gap = round(12 * G.dpi)
        x, y = {'Bottom': (px - w // 2, dy - h - gap), 'Top': (px - w // 2, dy + dh + gap), 'Left': (dx + dw + gap, py - h // 2),
                'Right': (dx - w - gap, py - h // 2)}.get(G.place, (x, y))
    x, y = onto_screen(x, y, w, h)
    sg.popup_quick_message(text, font='_ 12', text_color='white', background_color=color, keep_on_top=True, auto_close_duration=seconds, location=(x, y))


def ask_near(at, title, message, default=None, yes='OK', danger=False, timeout=None):
    """ A small question card that opens where you are, so there is little to move - at = a point on the screen (where the right-click was).
        default = text to edit: it opens with the box under the mouse and the text selected (type, then Enter).  default None: a yes / no.
        Returns the text (a yes / no: True) - or None for Cancel, Escape, the x, or `timeout` seconds going by """
    t = T()
    rows = [title_strip(title, K_ASK_X, with_version=False), [sg.Text(message, font='_ 11', p=((14, 14), (10, 4)))]]
    if default is not None:
        rows.append([sg.Input(default, key=K_ASK_INPUT, s=38, font='_ 12', p=((14, 14), 6))])
    rows.append([sg.Push(), sg.Button(yes, key=K_ASK_OK, button_color=COLOR_DANGER if danger else COLOR_SAVE, s=9, p=(4, (8, 12))),
                 sg.Button('Cancel', key=K_ASK_NO, s=9, p=((4, 14), (8, 12)))])
    card = sg.Window(title, [[sg.Frame('', rows, border_width_no_relief=1, border_color=t['border'], p=0)]], no_titlebar=True, keep_on_top=True, margins=(0, 0),
                     alpha_channel=0, finalize=True, icon=dock_icon_64, modal=True)
    close = card[K_ASK_X].Widget
    close.bind('<Enter>', lambda e: close.configure(bg=C_CLOSE, fg='#ffffff'))
    close.bind('<Leave>', lambda e: close.configure(bg=t['strip'], fg=t['dim']))
    drag_by_strip(card, card[K_STRIP].Widget, skip=close)
    card.bind('<Escape>', K_ASK_NO)
    card.bind('<Return>', K_ASK_OK)
    card.refresh()
    w, h = card.TKroot.winfo_width(), card.TKroot.winfo_height()
    if default is not None:                                             # the text box right under the mouse
        box = card[K_ASK_INPUT].Widget
        cx, cy = box.winfo_rootx() - card.TKroot.winfo_rootx() + box.winfo_width() // 2, box.winfo_rooty() - card.TKroot.winfo_rooty() + box.winfo_height() // 2
    else:                                                               # the question under the mouse, the buttons just below it
        cx, cy = w // 2, h // 2
    move_to(card, *onto_screen(at[0] - cx, at[1] - cy, w, h), firmly=True)
    card.set_alpha(1)
    card.force_focus()
    if default is not None:
        card[K_ASK_INPUT].set_focus()
        card[K_ASK_INPUT].Widget.select_range(0, 'end')
        card[K_ASK_INPUT].Widget.icursor('end')
    answer = None
    while True:
        event, values = card.read(timeout=round(timeout * 1000) if timeout else None)
        if event in (sg.WIN_CLOSED, K_ASK_X, K_ASK_NO, sg.TIMEOUT_KEY):
            break
        if event == K_ASK_OK:
            answer = values[K_ASK_INPUT] if default is not None else True
            break
    card.close()
    return answer


def save_entries():
    """ Write the programs and headings (Block.active_blocks, in order) to the entries file - for changes made on the dock itself """
    entries = {}
    for n, b in Block.active_blocks.items():
        entries[K_B_ICON64(n)] = b.iconb64
        entries[K_B_NAME(n)] = b.name
        entries[K_B_PATH(n)] = b.path
        entries[K_B_KIND(n)] = b.kind
        entries[K_B_BARVIS(n)] = b.bar
    G.launcher_settings.write_new_dictionary(entries)


def entry_from_file(filename):
    """ A new entry for a dropped / chosen file: its name, its path (a shortcut's target) and its icon, sharp - up to ICON_STORE pixels """
    filename = filename.strip().strip('"')
    ext = os.path.splitext(filename)[1].lower()
    path = resolve_shortcut(filename) if ext == '.lnk' else filename
    name = os.path.splitext(os.path.basename(filename if ext == '.lnk' else path))[0].replace('_', ' ')
    try:
        img = program_icon_image(path)
    except Exception:
        img = None
    b = Block(block_num=G.block_number, name=name, path=path, iconb64=image_to_icon_b64(img) if img is not None else '')
    G.block_number += 1
    return b


def add_programs(window, files, index=None):
    """ New entries for files, inserted at list position index (None = at the end) """
    insert_entries(window, [entry_from_file(f) for f in files if f and f.strip()], index)


def insert_entries(window, new, index=None):
    """ New entries (programs, links) put in at list position index (None = at the end), saved at once and shown with a bounce / glow """
    if not new:
        return
    order = list(Block.active_blocks.values())
    index = len(order) if index is None else max(0, min(index, len(order)))
    order[index:index] = new
    Block.active_blocks = {b.block_num: b for b in order}
    save_entries()
    now = time.time()
    for b in new:
        G.versions[b.block_num] = get_version(b.path)
        G.bounce[b.block_num] = now
        G.flash[b.block_num] = now + 1.2
    relayout(window)
    if G.style == 'Bar':
        bar_track_start(window)
    else:
        window.TKroot.after(1300, lambda: redraw(window))
    notice(f'Added {", ".join(b.name for b in new)}')


def ask_for_programs(window):
    """ Choose programs to add with the usual file dialog.  [] if cancelled """
    files = sg.popup_get_file('Programs to add', no_window=True, multiple_files=True, keep_on_top=True,
                              file_types=(('Programs', '*.pyw *.py *.exe *.lnk *.bat *.cmd'), ('All files', '*.*')))
    if not files:
        return []
    return [f for f in (files if isinstance(files, (list, tuple)) else files.split(';')) if f]


def icon_size(b64):
    """ The pixel size of a saved icon (0 if none) """
    try:
        return max(Image.open(io.BytesIO(base64.b64decode(ast.literal_eval(b64)))).size)
    except Exception:
        return 0


def sharpen_icons(window, nums=None):
    """ Fetch programs' own icons again at full size (older entries were saved at 30 pixels, which look soft when the Bar shows them big).
        An icon is only replaced by a bigger one of the program's own - never by the plain Python / PySimpleGUI logo """
    changed = 0
    for b in Block.active_blocks.values():
        if b.kind == KIND_HEADING or not b.path or (nums is not None and b.block_num not in nums):
            continue
        try:
            img = program_icon_image(b.path, fallback=False)
        except Exception:
            img = None
        if img is not None and min(ICON_STORE, max(img.size)) > icon_size(b.iconb64):
            b.iconb64 = image_to_icon_b64(img)
            changed += 1
    if changed:
        save_entries()
        relayout(window)
    notice(f'{changed} icon{"s" * (changed != 1)} made sharper - fetched again, full size, from the program' if changed else
           'No sharper icon found - the program has no bigger icon of its own', '#2e7d32' if changed else '#5c6676', 3)


def open_folder(path):
    """ Show a program in Explorer (selected), or open its folder """
    folder = path if os.path.isdir(path) else os.path.dirname(path)
    if sys.platform == 'win32':
        if os.path.exists(path):
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
        elif os.path.isdir(folder):
            os.startfile(folder)
    elif folder:
        sg.execute_command_subprocess('xdg-open', folder)


def entry_action(window, key):
    """ A choice from a program's or a section's right-click menu """
    b = Block.active_blocks.get(G.menu_target)
    if b is None:
        return
    if key == K_E_OPEN:
        launch(b.path)
        G.bounce[b.block_num] = time.time()
        G.flash[b.block_num] = time.time() + 0.35
        if G.style == 'Bar':
            bar_track_start(window)
        else:
            redraw(window)
            window.TKroot.after(400, lambda: redraw(window))
    elif key == K_E_FOLDER:
        open_folder(b.path)
    elif key == K_E_EDIT:
        sg.execute_editor(b.path)
    elif key == K_E_COPY:
        window.TKroot.clipboard_clear()
        window.TKroot.clipboard_append(b.path)
        notice('Link copied' if is_link(b.path) else 'Path copied', seconds=1)
    elif key == K_E_RENAME:
        name = ask_near(G.menu_at or pointer(), 'Rename', 'New name for this heading' if b.kind == KIND_HEADING else 'New name', default=b.name, yes='Rename')
        if name is not None and name.strip():
            if b.kind == KIND_HEADING and b.name in G.head_colors:     # its Colour goes with it (another heading of the old name keeps it too)
                G.head_colors[name.strip()] = G.head_colors[b.name]
                if not any(o.kind == KIND_HEADING and o.name == b.name for o in Block.active_blocks.values() if o is not b):
                    del G.head_colors[b.name]
                sg.user_settings_set_entry(K_HEAD_COLORS, G.head_colors)
            b.name = name.strip()
            save_entries()
            relayout(window)
    elif key == K_E_BAR:                                                # in the Bar or not (the Panel always shows everything)
        b.bar = not b.bar
        save_entries()
        relayout(window)
    elif key == K_E_REMOVE:
        what = 'the heading' if b.kind == KIND_HEADING else ''
        if ask_near(G.menu_at or pointer(), 'Remove', f'Remove {what} {b.name} from the dock?'.replace('  ', ' '), yes='Remove', danger=True):
            del Block.active_blocks[b.block_num]
            if b.kind == KIND_HEADING and b.name in G.head_colors and not any(o.kind == KIND_HEADING and o.name == b.name for o in Block.active_blocks.values()):
                del G.head_colors[b.name]                               # its Colour goes too
                sg.user_settings_set_entry(K_HEAD_COLORS, G.head_colors)
            save_entries()
            relayout(window)
    elif key == K_E_SHARPEN:
        sharpen_icons(window, [b.block_num])
    elif key == K_E_ADD_HERE:
        files = ask_for_programs(window)
        if files:
            add_programs(window, files, list(Block.active_blocks).index(b.block_num) + 1)
    elif key == K_E_ADD_LINK:
        ask_for_link(window, section_end(b.block_num))


def heading_color(window, choice):
    """ A heading's right-click > Colour: Automatic (the palette's colour for its place), a palette colour by name, or Custom... (the colour
        picker, starting at the heading's colour now).  Kept per dock by the heading's name (G.head_colors, K_HEAD_COLORS).  Picking a colour
        turns Colored sections on - it wouldn't show otherwise """
    b = Block.active_blocks.get(G.menu_target)
    if b is None or b.kind != KIND_HEADING:
        return
    if choice == HANDLE_CUSTOM:
        from tkinter import colorchooser
        try:
            rgb = colorchooser.askcolor(color=sections()[0].get(b.block_num) or T()['heading'], parent=window.TKroot, title=f'Colour of {b.name}')[0]
        except Exception:
            rgb = None
        if not rgb:
            return
        color = '#{:02x}{:02x}{:02x}'.format(*(max(0, min(255, int(v))) for v in rgb[:3]))
    else:
        color = dict(zip(SECTION_NAMES, SECTION_PALETTE)).get(choice)    # None = Automatic
    if color:
        G.head_colors[b.name] = color
    else:
        G.head_colors.pop(b.name, None)
    sg.user_settings_set_entry(K_HEAD_COLORS, G.head_colors)
    if color and not G.sections:
        G.sections = True
        sg.user_settings_set_entry(K_SECTIONS, True)
        notice('Colored sections is on now - the colours show with it', seconds=2.5)
    relayout(window)


def relayout(window, before=None):
    """ After the list, the size, the text size or the magnification changed: measure again and redraw.  A docked dock is centred on its edge
        again; a floating one keeps its corner nearest the screen's edges where it was """
    before = before or window_rect(window)
    G.bar_geo, G.mag, G.last_signature = None, [], None
    redraw(window)
    if G.place == 'Floating':
        keep_corner(window, before)
    else:
        place_window(window)


def refresh_dock(window):
    """ Reload the list of programs (after the Programs window, or from the menu) and redraw """
    load_blocks()
    G.versions = {b.block_num: get_version(b.path) for b in Block.active_blocks.values() if b.kind != KIND_HEADING}
    G.hover, G.drop_index, G.drop_item, G.drop_line, G.drop_stack = None, None, None, None, None
    relayout(window)


# ------------------------------------------------------------ Stacks: a section flies out of the Bar ------------------------------------------------------------

def two_lines(d, text, fnt, width):
    """ A name broken at spaces into at most two lines that fit in width pixels - the second shortened with an ellipsis if it must be """
    if d.textlength(text, font=fnt) <= width or ' ' not in text:
        return [fit(d, text, fnt, width)]
    words, first = text.split(' '), ''
    while words and d.textlength((first + ' ' + words[0]).strip(), font=fnt) <= width:
        first = (first + ' ' + words.pop(0)).strip()
    if not first:                                                       # a first word too long for a line of its own
        return [fit(d, text, fnt, width)]
    return [first, fit(d, ' '.join(words), fnt, width)]


def render_stack(heading, members, color, hover, side, anchor, find=None):
    """ The fly-out of a stack: the section's name (big, in its colour) and its programs in a grid (icon, name) on a card, with a notch on
        `side` ('bottom' = the card is above a bottom bar, 'top', 'left', 'right') at `anchor` pixels along that side.  find: the Bar's
        search instead - {'text': what's typed, 'grid': (columns, rows), 'more': matches with no room, 'count': the count to show} - its box
        where the name goes, and the card keeps its size as the matches change.  Returns (picture, [tile boxes in picture pixels], card box) """
    s, sd, ts, t = G.scale, G.dpi, text_scale(), T()
    n = max(1, len(members))
    cols = min(n, 3 if side in ('left', 'right') else 5)
    rows = -(-n // cols)
    if find:
        cols, rows = find['grid']
    icon = round(52 * s)
    name_f, title_f, count_f = font(False, round(12.5 * sd * ts)), font(True, round(19 * sd * ts)), font(False, round(12 * sd * ts))
    tile_w = max(round(104 * s), round(icon + 24 * sd), round(name_f.size * 8))
    tile_h = icon + round(10 * sd) + round(name_f.size * 2.9)                  # room for a name on two lines
    pad, title_h, notch = round(14 * sd), round(title_f.size * 2.0), round(11 * sd)
    m = round(16 * sd) if G.glass else 0                                # room for the shadow
    cw, ch = 2 * pad + cols * tile_w, pad + title_h + rows * tile_h + pad // 2
    W = cw + 2 * m + (notch if side in ('left', 'right') else 0)
    H = ch + 2 * m + (notch if side in ('top', 'bottom') else 0)
    cx0, cy0 = m + (notch if side == 'left' else 0), m + (notch if side == 'top' else 0)
    k = 2
    card = Image.new('RGBA', (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    fill, edge_color = rgba(t['card'], 236 if G.glass else 255), mix_hex(color, t['card'], 0.35)
    radius = round(16 * sd) if sg.running_windows() else 0
    d.rounded_rectangle((cx0 * k, cy0 * k, (cx0 + cw) * k - 1, (cy0 + ch) * k - 1), radius=radius * k, fill=fill, outline=edge_color, width=max(2, round(1.5 * sd * k)))
    a = min(max(anchor, radius + notch + 4), (cw if side in ('top', 'bottom') else ch) - radius - notch - 4)
    if side == 'bottom':                                                # the notch, pointing at the stack
        pts = ((cx0 + a - notch, cy0 + ch - 1), (cx0 + a + notch, cy0 + ch - 1), (cx0 + a, cy0 + ch + notch - 1))
    elif side == 'top':
        pts = ((cx0 + a - notch, cy0 + 1), (cx0 + a + notch, cy0 + 1), (cx0 + a, cy0 - notch + 1))
    elif side == 'left':
        pts = ((cx0 + 1, cy0 + a - notch), (cx0 + 1, cy0 + a + notch), (cx0 - notch + 1, cy0 + a))
    else:
        pts = ((cx0 + cw - 1, cy0 + a - notch), (cx0 + cw - 1, cy0 + a + notch), (cx0 + cw + notch - 1, cy0 + a))
    d.polygon([(x * k, y * k) for x, y in pts], fill=fill, outline=edge_color)
    card = card.resize((W, H), Image.LANCZOS)
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if G.glass:
        blur = round(10 * sd)
        im.alpha_composite(soft_shadow(cw, ch, radius, blur, 120), (cx0 - 2 * blur, cy0 - 2 * blur + round(4 * sd)))
    im.alpha_composite(card)
    d = ImageDraw.Draw(im)
    if find:                                                            # the Bar's search: its box where a section's name goes, the count at its end
        box = (cx0 + pad, cy0 + pad - round(6 * sd), cx0 + cw - pad, cy0 + pad + title_h * 0.64)
        draw_field(d, box, sd, t, find['text'], 'type to search', True, d.textlength(find['count'], font=count_f) + 16 * sd, find.get('picked'))
        d.text((box[2] - 10 * sd, (box[1] + box[3]) / 2), find['count'], font=count_f, fill=t['dim'], anchor='rm')
    else:
        d.text((cx0 + pad, cy0 + pad + title_h * 0.32), heading.name, font=title_f, fill=color, anchor='lm')
        count = f'{len(members)} program{"s" * (len(members) != 1)}'
        d.text((cx0 + cw - pad, cy0 + pad + title_h * 0.32), count, font=count_f, fill=t['dim'], anchor='rm')
        d.line((cx0 + pad, cy0 + pad + title_h * 0.72, cx0 + cw - pad, cy0 + pad + title_h * 0.72), fill=mix_hex(color, t['card'], 0.6), width=max(1, round(sd)))
    tiles = []
    for i, b in enumerate(members):
        tx, ty = cx0 + pad + (i % cols) * tile_w, cy0 + pad + title_h + (i // cols) * tile_h
        box = (tx + 3, ty, tx + tile_w - 3, ty + tile_h - 4)
        tiles.append(box)
        if hover == i:
            d.rounded_rectangle(box, radius=round(10 * sd), fill=mix_hex(color, t['card'], 0.5 if find else 0.78))
        ic = icon_image(b.iconb64, icon)
        ix, iy = tx + (tile_w - icon) / 2, ty + round(6 * sd)
        if ic:
            im.alpha_composite(ic, (round(ix + (icon - ic.width) / 2), round(iy + (icon - ic.height) / 2)))
        else:
            d.rounded_rectangle((ix, iy, ix + icon, iy + icon), radius=icon * 0.2, fill=t['track'])
        for n, line in enumerate(two_lines(d, b.name or '(no name)', name_f, tile_w - 10 * sd)):
            d.text((tx + tile_w / 2, ty + icon + round(9 * sd) + name_f.size * (0.6 + 1.2 * n)), line, font=name_f, fill=t['text'], anchor='mm')
    if find and find['more']:                                           # more matches than room: how many more, in the last place
        i = len(members)
        tx, ty = cx0 + pad + (i % cols) * tile_w, cy0 + pad + title_h + (i // cols) * tile_h
        d.text((tx + tile_w / 2, ty + tile_h / 2 - round(4 * sd)), f'+{find["more"]} more', font=name_f, fill=t['dim'], anchor='mm')
    if find and not members:
        d.text((cx0 + cw / 2, cy0 + pad + title_h + rows * tile_h / 2 - round(6 * sd)), 'No matches  -  Esc clears', font=name_f, fill=t['dim'], anchor='mm')
    return im, tiles, (cx0, cy0, cx0 + cw, cy0 + ch)


def open_stack(window, heading_num, by_hover=False):
    """ Click a stack on the Bar (or rest the mouse on it - by_hover): its section flies out next to it - the section's name and its programs in
        a grid.  Click one to start it (or arrow keys + Enter).  It closes with Escape, a click elsewhere, the stack clicked again (opened by a
        click), or the mouse away from it and the bar for a moment.  Runs until it closes; a dock event that came in meanwhile (another stack,
        a menu choice...) is returned for the main loop - None otherwise """
    heading, members = Block.active_blocks.get(heading_num), section_members(heading_num)
    span = next((sp for sp in G.spans if sp[2] == ('stack', heading_num)), None)
    if heading is None or not members or span is None:
        return None
    colors, owner = sections()
    color = colors.get(heading_num, T()['heading'])
    L = G.bar_geo
    side = {'Top': 'top', 'Left': 'left', 'Right': 'right'}.get(bar_side(), 'bottom')
    rx, ry = window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty()
    mc = (span[0] + span[1]) / 2
    tip = bar_box(L, mc, span[3] + 4 * G.dpi, mc + 1, span[3] + 5 * G.dpi)                           # just past the stack, inward
    tip_x, tip_y = round(rx + tip[0]), round(ry + tip[1])
    im, tiles, card = render_stack(heading, members, color, None, side, 0)
    W, H = im.size
    mon, work = monitor_area(tip_x, tip_y)
    if side in ('bottom', 'top'):
        x = min(max(round(tip_x - W / 2), work[0]), work[2] - W)
        y = tip_y - H if side == 'bottom' else tip_y
        anchor = tip_x - x - card[0]
    else:
        y = min(max(round(tip_y - H / 2), work[1]), work[3] - H)
        x = tip_x if side == 'left' else tip_x - W
        anchor = tip_y - y - card[1]
    hover = None
    im, tiles, card = render_stack(heading, members, color, hover, side, anchor)
    key_color = sg.running_windows() and not G.glass
    bg = TRANSPARENT if sg.running_windows() else T()['card']
    popup = sg.Window(heading.name, [[sg.Image(key=K_STACK_IMAGE, background_color=bg, pad=(0, 0))]], no_titlebar=True, keep_on_top=True, margins=(0, 0),
                      element_padding=(0, 0), background_color=bg, transparent_color=TRANSPARENT if key_color else None, alpha_channel=0, location=(x, y),
                      finalize=True, icon=dock_icon_64)
    surface, keep = (glass_setup(popup) if G.glass else None), {}
    shift = {'bottom': (0, 1), 'top': (0, -1), 'left': (-1, 0), 'right': (1, 0)}[side]
    started = time.time()
    while True:                                                         # fly out: slide in from the bar while fading in
        f = min(1.0, (time.time() - started) / 0.13)
        e = 1 - (1 - f) ** 3
        off = round((1 - e) * 12 * G.dpi)
        move_to(popup, x + shift[0] * off, y + shift[1] * off)
        if not show_picture(popup, K_STACK_IMAGE, surface, im, round(G.opacity * e), keep) and surface:
            surface = None
            show_picture(popup, K_STACK_IMAGE, None, im, 100, keep)
        if not surface:
            popup.set_alpha(G.opacity / 100 * e)
        popup.refresh()
        if f >= 1:
            break
        time.sleep(0.012)
    widget = popup[K_STACK_IMAGE].Widget
    state = {'press': None, 'hover': None}
    cols = sum(1 for tile in tiles if tile[1] == tiles[0][1])

    def tile_at(px, py):
        return next((i for i, (x0, y0, x1, y1) in enumerate(tiles) if x0 <= px < x1 and y0 <= py < y1), None)

    def set_hover(i):
        if i != state['hover']:
            state['hover'] = i
            widget.configure(cursor='hand2' if i is not None else '')
            popup.write_event_value(K_STACK_HOVER, i)

    def release(e):
        p, state['press'] = state['press'], None
        i = tile_at(e.x, e.y)
        if p is not None and i == p and i is not None:
            popup.write_event_value(K_STACK_CLICK, i)

    def key_move(step):                                                 # the arrow keys move the highlight, Enter starts that program
        i = state['hover']
        set_hover(0 if i is None else min(len(tiles) - 1, max(0, i + step)))

    widget.bind('<Motion>', lambda e: set_hover(tile_at(e.x, e.y)), add='+')
    widget.bind('<Leave>', lambda e: set_hover(None), add='+')
    widget.bind('<ButtonPress-1>', lambda e: state.update(press=tile_at(e.x, e.y)), add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')
    for seq, step in (('<Left>', -1), ('<Right>', 1), ('<Up>', -cols), ('<Down>', cols)):
        popup.TKroot.bind(seq, lambda e, step=step: key_move(step))
    popup.TKroot.bind('<Return>', lambda e: popup.write_event_value(K_STACK_CLICK, state['hover']) if state['hover'] is not None else None)
    popup.bind('<Escape>', K_STACK_CLOSE)
    if not by_hover:                                                    # opened by a click: keys work, and clicking anywhere else closes it
        popup.TKroot.bind('<FocusOut>', lambda e: popup.write_event_value(K_STACK_CLOSE, 'focus') if e.widget is popup.TKroot else None, add='+')
        popup.force_focus()
    G.stack_open = heading_num
    G.last_signature = None
    redraw(window)
    pending, away_since = None, None
    while True:
        win, event, values = sg.read_all_windows(timeout=150)
        if win is popup:
            if event in (sg.WIN_CLOSED, K_STACK_CLOSE):
                break
            if event == K_STACK_HOVER:
                hover = values[event]
                im, tiles, card = render_stack(heading, members, color, hover, side, anchor)
                show_picture(popup, K_STACK_IMAGE, surface, im, G.opacity, keep)
            elif event == K_STACK_CLICK:
                launch(members[values[event]].path)
                G.bounce[heading_num] = time.time()                     # the stack hops, like a program does
                break
        elif win is window:
            if event == K_CLICK and values[K_CLICK] == ('stack', heading_num):
                if by_hover:                                            # opened by resting on it: a click there keeps it open
                    continue
                break                                                   # its own stack clicked again: close
            if event == K_HOVER or (event == K_STACK_OPEN and values[event] == heading_num):
                continue
            pending = (event, values)
            break
        else:                                                           # every 150 ms: the mouse away from the fly-out and the bar for a while closes it
            try:
                px, py = popup.TKroot.winfo_pointerxy()
                over_popup = x <= px < x + W and y <= py < y + H
                over_bar = rx <= px < rx + G.win_size[0] and ry <= py < ry + G.win_size[1]
            except Exception:
                break
            if over_popup or over_bar:
                away_since = None
            else:
                away_since = away_since or time.time()
                if time.time() - away_since > (0.7 if by_hover else 1.4):
                    break
    glass_free(surface)
    popup.close()
    G.stack_open, G.stack_closed, G.last_signature = None, (heading_num, time.time()), None
    G.rest = (('stack', heading_num), time.time(), True)                # resting on it again doesn't reopen it - not until the mouse leaves it
    bar_track_start(window)
    redraw(window)
    return pending


def open_search(window, text=''):
    """ The Bar's search button - or a letter typed while the Bar has the keyboard: a search card flies out of the button.  Type, and the
        programs whose names match show as tiles (every program while nothing is typed - as many as fit, and how many more).  Arrows move,
        Enter or a click starts one, Esc clears what's typed - and closes it once empty;  a click elsewhere or the button again closes it too.
        Dim (right-click > Search): the bar's other icons fade while it's out.  Runs until it closes; a dock event that came in meanwhile is
        returned for the main loop - None otherwise """
    span = next((sp for sp in G.spans if sp[2] == 'search'), None)
    everyone = [b for b in Block.active_blocks.values() if b.kind != KIND_HEADING]
    if span is None or not everyone:
        return None
    L = G.bar_geo
    side = {'Top': 'top', 'Left': 'left', 'Right': 'right'}.get(bar_side(), 'bottom')
    cols = min(len(everyone), 3 if side in ('left', 'right') else 5)
    grid = (cols, min(5 if side in ('left', 'right') else 3, -(-len(everyone) // cols)))      # the card keeps this size as the matches change
    G.search, G.search_sel = text[:60], 0
    state = {'sel': 0 if G.search.strip() else None, 'press': None, 'drawn': [], 'all': False}       # (all: Ctrl+A selected what's typed)

    def view():                                                         # for what's typed now: (the tiles, how many more matches, the count)
        found = search_find()
        hits = everyone if found is None else found[0]
        room = grid[0] * grid[1]
        shown = hits if len(hits) <= room else hits[:room - 1]          # no room for them all: the last place says how many more
        if state['sel'] is not None:
            state['sel'] = min(state['sel'], len(shown) - 1) if shown else None
        count = f'{len(everyone)} programs' if found is None else f'{len(hits)} of {len(everyone)}'
        return shown, len(hits) - len(shown), count

    def picture(anchor):                                                # the card for what's typed now
        shown, more, count = view()
        state['drawn'] = shown
        find = {'text': G.search, 'grid': grid, 'more': more, 'count': count, 'picked': state['all'] and bool(G.search)}
        return render_stack(None, shown, C_SELECT, state['sel'], side, anchor, find=find)

    rx, ry = window.TKroot.winfo_rootx(), window.TKroot.winfo_rooty()
    mc = (span[0] + span[1]) / 2
    tip = bar_box(L, mc, span[3] + 4 * G.dpi, mc + 1, span[3] + 5 * G.dpi)                           # just past the button, inward
    tip_x, tip_y = round(rx + tip[0]), round(ry + tip[1])
    im, tiles, card = picture(0)
    W, H = im.size
    mon, work = monitor_area(tip_x, tip_y)
    if side in ('bottom', 'top'):
        x = min(max(round(tip_x - W / 2), work[0]), work[2] - W)
        y = tip_y - H if side == 'bottom' else tip_y
        anchor = tip_x - x - card[0]
    else:
        y = min(max(round(tip_y - H / 2), work[1]), work[3] - H)
        x = tip_x if side == 'left' else tip_x - W
        anchor = tip_y - y - card[1]
    im, tiles, card = picture(anchor)
    key_color = sg.running_windows() and not G.glass
    bg = TRANSPARENT if sg.running_windows() else T()['card']
    popup = sg.Window('Search', [[sg.Image(key=K_STACK_IMAGE, background_color=bg, pad=(0, 0))]], no_titlebar=True, keep_on_top=True, margins=(0, 0),
                      element_padding=(0, 0), background_color=bg, transparent_color=TRANSPARENT if key_color else None, alpha_channel=0, location=(x, y),
                      finalize=True, icon=dock_icon_64)
    surface, keep = (glass_setup(popup) if G.glass else None), {}
    shift = {'bottom': (0, 1), 'top': (0, -1), 'left': (-1, 0), 'right': (1, 0)}[side]
    started = time.time()
    while True:                                                         # fly out: slide in from the bar while fading in
        f = min(1.0, (time.time() - started) / 0.13)
        e = 1 - (1 - f) ** 3
        off = round((1 - e) * 12 * G.dpi)
        move_to(popup, x + shift[0] * off, y + shift[1] * off)
        if not show_picture(popup, K_STACK_IMAGE, surface, im, round(G.opacity * e), keep) and surface:
            surface = None
            show_picture(popup, K_STACK_IMAGE, None, im, 100, keep)
        if not surface:
            popup.set_alpha(G.opacity / 100 * e)
        popup.refresh()
        if f >= 1:
            break
        time.sleep(0.012)
    widget = popup[K_STACK_IMAGE].Widget

    def tile_at(px, py):
        return next((i for i, (x0, y0, x1, y1) in enumerate(tiles) if x0 <= px < x1 and y0 <= py < y1), None)

    def motion(e):                                                      # the mouse on a tile makes it the pick (off the tiles, the pick stays)
        i = tile_at(e.x, e.y)
        widget.configure(cursor='hand2' if i is not None else '')
        if i is not None and i != state['sel']:
            state['sel'] = i
            popup.write_event_value(K_STACK_HOVER, i)

    def release(e):
        p, state['press'] = state['press'], None
        i = tile_at(e.x, e.y)
        if p is not None and i == p:
            popup.write_event_value(K_STACK_CLICK, i)

    widget.bind('<Motion>', motion, add='+')
    widget.bind('<ButtonPress-1>', lambda e: state.update(press=tile_at(e.x, e.y)), add='+')
    widget.bind('<ButtonRelease-1>', release, add='+')
    popup.TKroot.bind('<KeyPress>', lambda e: popup.write_event_value(K_FIND_KEY, (e.keysym, e.char, e.state)))
    popup.TKroot.bind('<FocusOut>', lambda e: popup.write_event_value(K_STACK_CLOSE, 'focus') if e.widget is popup.TKroot else None, add='+')
    popup.force_focus()
    G.stack_open = 'search'                                             # (the bar keeps still meanwhile, as for a stack)
    G.last_signature = None
    redraw(window)
    pending, chosen, dirty, bar_due = None, None, False, False
    while True:
        win, event, values = sg.read_all_windows(timeout=0 if dirty else 150)
        if event == sg.TIMEOUT_KEY:                                     # no more keys waiting: show what's typed now (one picture per burst of typing)
            if dirty:
                im, tiles, card = picture(anchor)
                show_picture(popup, K_STACK_IMAGE, surface, im, G.opacity, keep)
                if bar_due:
                    redraw(window)                                      # the bar too (Dim: what doesn't match fades)
                dirty, bar_due = False, False
            continue
        if win is popup:
            if event in (sg.WIN_CLOSED, K_STACK_CLOSE):
                break
            if event == K_STACK_CLICK:                                  # (a tile as drawn)
                i = values[event]
                chosen = state['drawn'][i] if i is not None and i < len(state['drawn']) else None
                break
            if event == K_FIND_KEY:
                key, char, st = values[event]
                if key == 'Escape':
                    if not G.search:
                        break
                    G.search, state['sel'], state['all'], bar_due = '', None, False, True
                elif key in ('Return', 'KP_Enter'):
                    shown = view()[0]                                   # (for what's typed now, drawn yet or not)
                    if state['sel'] is not None:
                        chosen = shown[state['sel']]
                        break
                    continue
                elif key in ('Left', 'Right', 'Up', 'Down'):
                    shown, i, held = view()[0], state['sel'], state['all']
                    state['all'] = False                                # an arrow first lets go of Ctrl+A's selection (Left / Right only that)
                    if shown and not (held and key in ('Left', 'Right')):
                        step = {'Left': -1, 'Right': 1, 'Up': -grid[0], 'Down': grid[0]}[key]
                        state['sel'] = 0 if i is None else min(len(shown) - 1, max(0, i + step))
                else:
                    typing = typed(G.search, key, char, st, popup.TKroot, state['all'] and bool(G.search))
                    if typing is None:
                        continue
                    new, state['all'] = typing
                    if new != G.search:
                        G.search, bar_due = new, True
                        state['sel'] = 0 if G.search.strip() else None
            dirty = True
        elif win is window:
            if event == K_CLICK and values[K_CLICK] == 'search':        # its button again: close
                break
            if event in (K_HOVER, K_FIND_OPEN):
                continue
            pending = (event, values)
            break
    glass_free(surface)
    popup.close()
    G.stack_open, G.stack_closed, G.last_signature = None, ('search', time.time()), None
    G.search, G.search_sel = '', 0
    if chosen is not None:
        start_program(window, chosen.block_num)
    bar_track_start(window)
    redraw(window)
    return pending


# ------------------------------------------------------------ The window ------------------------------------------------------------

def make_psg_launcher():
    """ The dock window: one Image the whole dock is drawn into.  Made again whenever the Style, Position, Auto-hide or Glass changes """
    load_blocks()
    G.versions = {b.block_num: get_version(b.path) for b in Block.active_blocks.values() if b.kind != KIND_HEADING}
    floating = G.place == 'Floating'
    key_color = sg.running_windows() and not G.glass
    bg = TRANSPARENT if sg.running_windows() else T()['card']
    m_bg, m_fg = T()['menu']
    layout = [[sg.Image(key=K_IMAGE, background_color=bg, pad=(0, 0))]]
    window = sg.Window(window_title(), layout, icon=dock_icon_64, no_titlebar=True, grab_anywhere=False, keep_on_top=G.on_top or (G.autohide and not floating), margins=(0, 0),
                       element_padding=(0, 0), background_color=bg, transparent_color=TRANSPARENT if key_color else None, alpha_channel=0, use_default_focus=False,
                       location=tuple(G.location) if floating and G.location else (None, None), finalize=True, right_click_menu=make_menu(),
                       right_click_menu_background_color=m_bg, right_click_menu_text_color=m_fg, right_click_menu_selected_colors=('#ffffff', C_SELECT),
                       right_click_menu_font=FONT_MENU, disable_close=True)    # Alt-F4 is ignored: the dock closes with Exit or the Panel's x
    G.window = window
    G.dpi = max(1.0, window.TKroot.winfo_fpixels('1i') / 96)
    G.scale = G.dpi * G.size
    G.hidden, G.sliding, G.anim, G.hover, G.pointer, G.tracking, G.press, G.scrub = False, False, None, None, None, False, None, None
    G.mag, G.bar_geo, G.last_signature, G.win_size, G.full_size, G.keep, G.layered, G.bounce = [], None, None, None, None, {}, None, {}
    G.drop_index, G.drop_item, G.drop_line, G.drop_open, G.drop_stack, G.stack_open, G.rest = None, None, None, 0.0, None, None, None
    G.handle_since, G.edge_target, G.preview, G.preview_size = None, None, None, None
    G.search, G.search_sel, G.focus, G.search_spots, G.redraw_due, G.search_all = '', 0, False, [], False, False
    here = G.default_pt or (window.TKroot.winfo_rootx() + 50, window.TKroot.winfo_rooty() + 50)    # the other style's dock was here, else where tk put this one
    if not floating and G.monitor_pt is None:
        G.monitor_pt = here
        save_style_setting('MONITOR', list(here))
    point = G.monitor_pt if not floating else ((G.location[0] + 50, G.location[1] + 50) if G.location else here)
    G.mon, G.work = monitor_area(*point)
    G.float_side = 'Right' if floating and G.location and G.location[0] + 60 * G.dpi > (G.mon[0] + G.mon[2]) / 2 else 'Left'
    if G.glass:
        G.layered = glass_setup(window)
        if G.layered is None:                                           # Glass isn't possible here: the plain look, on the colour key
            G.glass = False
            sg.user_settings_set_entry(K_GLASS, False)
            if sg.running_windows():
                window.TKroot.attributes('-transparentcolor', TRANSPARENT)
    redraw(window)
    if floating:
        put_on_screen(window)
    else:
        place_window(window)
    if not G.glass:
        window.set_alpha(G.opacity / 100)
    style_menus(window)
    bind_mouse(window)
    setup_drop(window)
    if G.autohide and not floating:
        G.out_since, G.edge_since = None, None
        window.TKroot.after(AUTOHIDE_POLL_MS, lambda: autohide_tick(window))
    return window


def rebuild(window):
    """ Close the dock and make it again - after a Style, Position, Auto-hide or Glass change, which change how the window itself is made """
    G.window = None                                                     # stops the old window's timers
    glass_free(G.layered)
    window.close()
    return make_psg_launcher()


def switch_style(window, style):
    """ Panel <-> Bar: each comes up where it was, at its own size - the first time on the screen the other one is on """
    remember_location(window)
    x, y, w, h = window_rect(window)
    G.default_pt = (x + w // 2, y + h // 2)
    G.style = style
    sg.user_settings_set_entry(K_STYLE, style)
    load_style_settings()
    return rebuild(window)


def launch(launch_file):
    """ Start a program from the dock - or open a link """
    if not launch_file:
        return
    if is_link(launch_file):
        open_link(launch_file)
        return
    if launch_file.lower().endswith(('.py', '.pyw')):
        sg.execute_py_file(launch_file, cwd=os.path.dirname(launch_file))
    elif sys.platform == 'win32' and os.path.exists(launch_file):
        try:
            os.startfile(launch_file, cwd=os.path.dirname(launch_file))    # programs, shortcuts, documents, folders - paths with spaces too
        except TypeError:                                               # Python older than 3.10: no cwd
            os.startfile(launch_file)
    else:
        cmd = launch_file.split()
        sg.execute_command_subprocess(cmd[0], *cmd[1:], cwd=os.path.dirname(__file__))


# ------------------------------------------------------------ Links: entries that open a web page, a Claude chat, mailto: ... ------------------------------------------------------------

LINK_RE = re.compile(r'^[A-Za-z][A-Za-z0-9+.-]+:')                     # a scheme - https:, claude:, mailto:, ms-settings: ... - two letters or more, so C:\ stays a path


def is_link(path):
    """ True when an entry opens a link (a web page, a claude:// chat, mailto: ...) rather than a program, a file or a folder """
    return bool(path) and bool(LINK_RE.match(path.strip()))


def link_handler(scheme):
    """ Windows: the program that opens links of this scheme (http / https: the default browser) - '' if there is none, or not on Windows """
    if not sg.running_windows() or not scheme:
        return ''
    try:                                                                # Windows' own answer - the default browser for https, the Claude app for claude
        import ctypes
        from ctypes import wintypes
        shlwapi = ctypes.windll.shlwapi
        shlwapi.AssocQueryStringW.argtypes = [ctypes.c_uint, ctypes.c_uint, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        size = wintypes.DWORD(1024)
        buf = ctypes.create_unicode_buffer(size.value)
        if shlwapi.AssocQueryStringW(0x1000, 2, scheme, 'open', buf, ctypes.byref(size)) == 0 and buf.value:     # a protocol (0x1000), its program (2)
            return buf.value
    except Exception:
        pass
    try:                                                                # a protocol an app registered for itself (claude:)
        import winreg
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, rf'{scheme}\shell\open\command') as key:
            command = winreg.QueryValueEx(key, '')[0]
        m = re.match(r'\s*"([^"]+)"|\s*(\S+)', command)
        return (m.group(1) or m.group(2)) if m else ''
    except OSError:
        return ''


def link_target(url):
    """ What a link entry really opens: a claude.ai page opens in the Claude app (as claude://claude.ai/...) when the app is installed - else in the browser """
    url = url.strip()
    if re.match(r'https?://claude\.ai/', url, re.I) and link_handler('claude'):
        return 'claude://' + url.split('://', 1)[1]
    return url


def open_link(url):
    target = link_target(url)
    if sg.running_windows():
        os.startfile(target)
    else:
        import webbrowser
        webbrowser.open(target)


def link_name(url):
    """ A first name for a new link: Claude chat for claude.ai, else the site """
    p = urllib.parse.urlparse(url.strip())
    if p.scheme.lower() == 'claude' or p.netloc.lower().endswith('claude.ai'):
        return 'Claude chat'
    return (p.netloc or p.path.split('/')[0]).replace('www.', '') or url


def drawn_link_icon(px=ICON_STORE):
    """ A link's icon when the app that opens it has none: two chain links on a blue tile.  Drawn 4x and shrunk """
    z = 4
    S = px * z
    im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((S * 0.06, S * 0.06, S * 0.94, S * 0.94), radius=S * 0.22, fill=C_SELECT)
    chain = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d, w = ImageDraw.Draw(chain), round(S * 0.075)
    d.rounded_rectangle((S * 0.16, S * 0.38, S * 0.57, S * 0.62), radius=S * 0.12, outline='#ffffff', width=w)
    d.rounded_rectangle((S * 0.43, S * 0.38, S * 0.84, S * 0.62), radius=S * 0.12, outline='#ffffff', width=w)
    im.alpha_composite(chain.rotate(45, resample=Image.BICUBIC, center=(S / 2, S / 2)))
    return im.resize((px, px), Image.LANCZOS)


def link_icon_image(url):
    """ A link's icon: the icon of the app that opens it (the Claude app, the browser ...), else drawn.  One per scheme, made once """
    scheme = link_target(url).split(':', 1)[0].lower()
    if scheme not in G.link_icons:
        exe, img = link_handler(scheme), None
        if exe and os.path.isfile(exe):
            try:
                img = shell_icon_image(exe)
            except Exception:
                img = None
        G.link_icons[scheme] = img if img is not None else drawn_link_icon()
    return G.link_icons[scheme]


def ask_for_link(window, index=None):
    """ Right-click > Add a link... (a heading's: Add a link here...): the link - the clipboard's, when it holds one - then its name.  Added at list
        position index (None = at the end) """
    at = G.menu_at or pointer()
    try:
        clip = window.TKroot.clipboard_get().strip()
    except Exception:
        clip = ''
    url = ask_near(at, 'Add a link', 'The link:  a web page (https://...),  a Claude chat (https://claude.ai/... - it opens in the Claude app),\n'
                   'claude://...,  mailto:...', default=clip if is_link(clip) and '\n' not in clip and len(clip) < 2000 else 'https://', yes='Next')
    url = (url or '').strip()
    if not is_link(url) or url.lower() in ('https://', 'http://'):
        return
    name = ask_near(at, 'Add a link', 'Its name on the dock', default=link_name(url), yes='Add')
    if name is None:
        return
    try:
        img = link_icon_image(url)
    except Exception:
        img = None
    b = Block(block_num=G.block_number, name=name.strip() or link_name(url), path=url, iconb64=image_to_icon_b64(img) if img is not None else '')
    G.block_number += 1
    insert_entries(window, [b], index)


# ------------------------------------------------------------ Several docks: each named dock has its own list and settings ------------------------------------------------------------

def dock_slug(name):
    """ A dock's name made into the part of its file names:  'Claude chats' -> claude_chats """
    slug = re.sub(r'[^a-z0-9]+', '_', name.lower()).strip('_')[:40] or 'dock'
    return slug + '_dock' if slug.endswith('entries') else slug        # never mistaken for an entries file


def dock_files(slug):
    """ (settings file, entries file) of a dock - '' = the dock started without a name, which keeps the files it always had """
    return (MAIN_SETTINGS_FILENAME, 'psgdock_entries.json') if not slug else (f'{DOCK_PREFIX}{slug}.json', f'{DOCK_PREFIX}{slug}_entries.json')


def settings_folder():
    return os.path.dirname(sg.UserSettings(MAIN_SETTINGS_FILENAME).get_filename())


def dock_arg():
    """ The name after --dock on the command line (or --dock=name), None without one """
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == '--dock' and i + 1 < len(args):
            return args[i + 1]
        if a.startswith('--dock='):
            return a.split('=', 1)[1]
    return None


def list_docks():
    """ Every dock there is: [(file name part, name)] - the one started without a name first, then the named ones by name.  Only reads their files """
    folder = settings_folder()

    def name_in(path, default):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f).get(K_DOCK_NAME) or default
        except (OSError, ValueError, AttributeError):
            return default

    named = []
    try:
        for fn in os.listdir(folder):
            if fn.startswith(DOCK_PREFIX) and fn.endswith('.json') and not fn.endswith('_entries.json'):
                slug = fn[len(DOCK_PREFIX):-len('.json')]
                named.append((slug, G.dock_title if slug == G.dock_slug and G.dock_ready else name_in(os.path.join(folder, fn), slug.replace('_', ' '))))
    except OSError:
        pass
    main_name = G.dock_title if not G.dock_slug and G.dock_ready else name_in(os.path.join(folder, MAIN_SETTINGS_FILENAME), APP_NAME)
    return [('', main_name)] + sorted(named, key=lambda d: d[1].casefold())


def find_dock(name):
    """ The dock called name (or made with that name) - its file name part, '' for the main dock, None if there's none """
    name = name.strip()
    for slug, shown in list_docks():
        if shown.casefold() == name.casefold() or (slug and slug == dock_slug(name)):
            return slug
    return '' if name.casefold() == APP_NAME.casefold() else None


def use_dock(name):
    """ --dock NAME: which dock this is - an existing one is found by its name (or the name it was made with), a new name is a new dock.
        Points the two settings files at its own.  Returns (file name part, name) """
    global ENTRIES_FILENAME, WINDOW_SETTINGS_FILENAME
    slug = ''
    if name and name.strip():
        name = name.strip()
        found = find_dock(name)
        slug = found if found is not None else dock_slug(name)
    WINDOW_SETTINGS_FILENAME, ENTRIES_FILENAME = dock_files(slug)
    G.dock_slug = slug
    return slug, name


def dock_mutex_name(slug):
    return f'Local\\PSGDock-{slug or "main"}'


def claim_dock(slug):
    """ Windows: a named mutex says this dock is running.  False when it already is - two copies of one dock would write the same files """
    if not sg.running_windows():
        return True
    import ctypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.CreateMutexW.restype = ctypes.c_void_p
    k32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p]
    G.mutex = k32.CreateMutexW(None, 0, dock_mutex_name(slug))
    return ctypes.get_last_error() != 183                               # ERROR_ALREADY_EXISTS


def dock_running(slug):
    """ Is that dock open (in this program or another copy of it)? """
    if slug == G.dock_slug:
        return True
    if not sg.running_windows():
        return False
    import ctypes
    k32 = ctypes.WinDLL('kernel32', use_last_error=True)
    k32.OpenMutexW.restype = ctypes.c_void_p
    k32.OpenMutexW.argtypes = [ctypes.c_uint, ctypes.c_int, ctypes.c_wchar_p]
    handle = k32.OpenMutexW(0x00100000, 0, dock_mutex_name(slug))      # SYNCHRONIZE
    if handle:
        k32.CloseHandle(ctypes.c_void_p(handle))
    return bool(handle)


def start_new_dock(name):
    """ A dock's first run: its name, the main dock's look (theme, brightness, text size, Glass ...) - only read from the main dock's file - and a
        floating Panel by the mouse.  Its list starts empty """
    try:
        with open(os.path.join(settings_folder(), MAIN_SETTINGS_FILENAME), 'r', encoding='utf-8') as f:
            main = json.load(f)
    except (OSError, ValueError):
        main = {}
    look = (K_THEME, K_BRIGHT, K_OPACITY, K_TEXT, K_GLASS, K_SECTIONS, K_VERSIONS, K_MAGNIFY, K_LAYOUT, K_BAR_LABELS, K_STACKS_HOVER, K_KEEP_ON_TOP)
    for key in look + (KS('SIZE', 'Panel'), KS('SIZE', 'Bar')):
        if key in main:
            sg.user_settings_set_entry(key, main[key])
    sg.user_settings_set_entry(K_DOCK_NAME, name)
    sg.user_settings_set_entry(K_STYLE, 'Panel')
    sg.user_settings_set_entry(KS('PLACE', 'Panel'), 'Floating')
    if sg.running_windows():
        try:
            import ctypes
            from ctypes import wintypes
            pt = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            sg.user_settings_set_entry(KS('LOCATION', 'Panel'), [pt.x - 160, pt.y - 60])     # (moved onto the screen when it shows)
        except Exception:
            pass


def window_title():
    """ The dock window's title (taskbar, Alt-Tab): PSG Dock - its name """
    return APP_NAME if G.dock_title == APP_NAME else f'{APP_NAME} - {G.dock_title}'


def start_dock(slug_or_name):
    """ Start another dock - this same program, with --dock """
    exe = sys.executable
    if exe.lower().endswith('python.exe') and os.path.isfile(exe[:-len('python.exe')] + 'pythonw.exe'):
        exe = exe[:-len('python.exe')] + 'pythonw.exe'
    script = os.path.abspath(__file__)
    subprocess.Popen([exe, script] + (['--dock', slug_or_name] if slug_or_name else []), cwd=os.path.dirname(script))


def open_dock(slug):
    """ Right-click > Docks > a dock: start it (a dock that's already open says so) """
    name = dict(list_docks()).get(slug, slug)
    if slug == G.dock_slug:
        notice(f'This is {name}', C_SELECT)
    elif dock_running(slug):
        notice(f'{name} is already open', C_SELECT)
    else:
        start_dock(slug)
        notice(f'Opening {name}', C_SELECT)


def new_dock(window):
    """ Right-click > Docks > New dock...: ask its name, then start it - its own list (empty) and settings, this dock's look """
    name = ask_near(G.menu_at or pointer(), 'New dock', 'A name for the new dock (for example: Claude chats)\nIt starts empty, with this dock\'s look', default='', yes='Make it')
    name = (name or '').strip()
    if not name:
        return
    slug = find_dock(name)
    if slug is not None:
        open_dock(slug)
        return
    start_dock(name)
    notice(f'Opening {name}  -  drop programs on it, or right-click > Add a link...', C_SELECT, 4)


def rename_dock(window):
    """ Right-click > Docks > Rename this dock...: the name it shows - its files keep their names, so shortcuts made earlier still find it """
    name = ask_near(G.menu_at or pointer(), 'Rename this dock', 'New name for this dock', default=G.dock_title, yes='Rename')
    name = (name or '').strip()
    if not name or name == G.dock_title:
        return
    other = find_dock(name)
    if other is not None and other != G.dock_slug:
        notice(f'There is already a dock called {name}', '#b71c1c', 3)
        return
    G.dock_title = name
    sg.user_settings_set_entry(K_DOCK_NAME, name)
    window.TKroot.title(window_title())
    relayout(window)
    set_right_click_menu(window, make_menu())


def make_dock_shortcut(folder=None):
    """ Right-click > Docks > Desktop shortcut for this dock: a shortcut (on the desktop, or in folder) that starts this dock.  Returns its path, or None """
    script = os.path.abspath(__file__)
    exe = sys.executable
    if exe.lower().endswith('python.exe') and os.path.isfile(exe[:-len('python.exe')] + 'pythonw.exe'):
        exe = exe[:-len('python.exe')] + 'pythonw.exe'
    icon = os.path.join(os.path.dirname(script), 'psgdock.ico')
    lnk = re.sub(r'[<>:"/\\|?*]', '_', G.dock_title) + '.lnk'
    env = dict(os.environ, PSGDOCK_LNK=lnk, PSGDOCK_FOLDER=folder or '', PSGDOCK_EXE=exe, PSGDOCK_DIR=os.path.dirname(script), PSGDOCK_ICON=icon if os.path.isfile(icon) else exe,
               PSGDOCK_ARGS=f'"{script}"' + (f' --dock "{G.dock_title}"' if G.dock_slug else ''))
    ps = ("$f = if ($env:PSGDOCK_FOLDER) { $env:PSGDOCK_FOLDER } else { [Environment]::GetFolderPath('Desktop') }; $p = Join-Path $f $env:PSGDOCK_LNK; "
          "$s = (New-Object -ComObject WScript.Shell).CreateShortcut($p); $s.TargetPath = $env:PSGDOCK_EXE; $s.Arguments = $env:PSGDOCK_ARGS; "
          "$s.WorkingDirectory = $env:PSGDOCK_DIR; $s.IconLocation = $env:PSGDOCK_ICON; $s.Save(); Write-Output $p")
    try:
        out = subprocess.run(['powershell', '-NoProfile', '-Command', ps], env=env, capture_output=True, text=True, timeout=30,
                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        path = out.stdout.strip().splitlines()[-1] if out.returncode == 0 and out.stdout.strip() else None
    except Exception:
        path = None
    if path and os.path.isfile(path):
        notice(f'Made {os.path.basename(path)} on the desktop' if not folder else f'Made {path}', seconds=3)
        return path
    notice('Could not make the shortcut', '#b71c1c', 3)
    return None


def save_style_setting(name, value):
    sg.user_settings_set_entry(KS(name, G.style), value)


def load_style_settings():
    """ What each style keeps for itself: where it goes (Floating or an edge), auto-hide, its monitor, its floating spot, its size.
        Coming from 2.2.19, where both styles shared these, the style that was showing takes the shared values and the other starts fresh -
        the Panel floating where the dock was, the Bar at the bottom of the screen - both at the size 2.2.19 used """
    st, legacy = G.style, G.style == G.legacy_style
    get = lambda name: sg.user_settings_get_entry(KS(name, st), None)
    place = get('PLACE')
    if place not in PLACES:
        old = sg.user_settings_get_entry(K_PLACE, None)
        place = old if legacy and old in PLACES else ('Floating' if st == 'Panel' else 'Bottom')
    G.place = place
    autohide = get('AUTOHIDE')
    G.autohide = bool(sg.user_settings_get_entry(K_AUTOHIDE, False)) if autohide is None and legacy else bool(autohide)
    point = get('MONITOR') or (sg.user_settings_get_entry(K_MONITOR, None) if legacy else None)
    G.monitor_pt = tuple(point) if isinstance(point, (list, tuple)) and len(point) == 2 else None
    size = get('SIZE')
    if not isinstance(size, (int, float)) or isinstance(size, bool):
        size = SIZES.get(sg.user_settings_get_entry(K_SIZE, 'Medium'), 1.0)
    G.size = min(SIZE_MAX, max(SIZE_MIN, float(size)))
    along = get('ALONG')
    G.along = float(along) if isinstance(along, (int, float)) and not isinstance(along, bool) and 0 <= along <= 1 else None
    G.float_vertical = st == 'Bar' and bool(get('VERTICAL'))
    location = get('LOCATION')
    if location is None and st == 'Panel':
        location = sg.user_settings_get_entry('-LAST WINDOW LOCATION-' + APP_NAME, None)          # where 2.2.19 and older kept the floating dock
    G.location = tuple(location) if isinstance(location, (list, tuple)) and len(location) == 2 and None not in location else None
    for name, value in (('PLACE', G.place), ('AUTOHIDE', G.autohide), ('SIZE', round(G.size, 3))):      # from now on this style has its own
        save_style_setting(name, value)
    if G.monitor_pt:
        save_style_setting('MONITOR', list(G.monitor_pt))


def load_view_settings():
    """ The dock's look, from psgdock.json - then the settings of the style it shows """
    G.theme = sg.user_settings_get_entry(K_THEME, 'Toybox')
    G.theme = OLD_THEME_NAMES.get(G.theme, G.theme if G.theme in THEMES else 'Toybox')           # a renamed theme (Midnight -> Carbon) or an unknown one
    G.bright = sg.user_settings_get_entry(K_BRIGHT, 0)
    G.bright = G.bright if G.bright in BRIGHT_LEVELS else 0
    G.opacity = sg.user_settings_get_entry(K_OPACITY, None)
    if G.opacity not in OPACITIES:                                      # older versions saved an Alpha of 1-10
        G.opacity = min(OPACITIES, key=lambda p: abs(p - sg.user_settings_get_entry('-alpha-', 9) * 10))
    G.on_top = sg.user_settings_get_entry(K_KEEP_ON_TOP, False)
    G.columns = str(sg.user_settings_get_entry(K_COLUMNS, 'Auto'))
    G.columns = G.columns if G.columns in COLUMN_CHOICES else 'Auto'
    G.style = sg.user_settings_get_entry(K_STYLE, 'Panel')
    G.style = G.style if G.style in STYLES else 'Panel'
    G.legacy_style = G.style
    G.magnify = sg.user_settings_get_entry(K_MAGNIFY, 'Large')
    G.magnify = G.magnify if G.magnify in MAGNIFIES else 'Large'
    G.glass = bool(sg.user_settings_get_entry(K_GLASS, False)) and sg.running_windows()
    G.text = sg.user_settings_get_entry(K_TEXT, 'Medium')
    G.text = G.text if G.text in TEXT_SIZES else 'Medium'
    G.sections = bool(sg.user_settings_get_entry(K_SECTIONS, True))
    G.show_versions = bool(sg.user_settings_get_entry(K_VERSIONS, True))
    G.bar_labels = bool(sg.user_settings_get_entry(K_BAR_LABELS, False))
    G.handle_name = bool(sg.user_settings_get_entry(K_HANDLE_NAME, False))
    G.bubble_section = bool(sg.user_settings_get_entry(K_BUBBLE_SECTION, True))
    G.flyout = sg.user_settings_get_entry(K_FLYOUT, 0.3)
    G.flyout = G.flyout if G.flyout in FLYOUTS.values() else 0.3
    G.handle_color = sg.user_settings_get_entry(K_HANDLE_COLOR, None)
    G.handle_color = G.handle_color if G.handle_color in HANDLE_COLORS.values() else hex_color(G.handle_color)      # a preset, or a Custom... colour
    G.handle_custom = hex_color(sg.user_settings_get_entry(K_HANDLE_CUSTOM, None))
    G.head_colors = sg.user_settings_get_entry(K_HEAD_COLORS, {})
    G.head_colors = {n: hex_color(c) for n, c in G.head_colors.items() if isinstance(n, str) and hex_color(c)} if isinstance(G.head_colors, dict) else {}
    G.bar_layout = sg.user_settings_get_entry(K_LAYOUT, 'Icons')
    G.bar_layout = G.bar_layout if G.bar_layout in LAYOUTS else 'Icons'
    G.stacks_hover = bool(sg.user_settings_get_entry(K_STACKS_HOVER, True))
    G.search_pref = sg.user_settings_get_entry(K_SEARCH, None)
    G.search_pref = G.search_pref if isinstance(G.search_pref, bool) else None                # not set: on by itself once the dock has many programs
    G.search_mode = sg.user_settings_get_entry(K_SEARCH_MODE, 'Hide')
    G.search_mode = G.search_mode if G.search_mode in SEARCH_MODES else 'Hide'
    load_style_settings()


def keep_going(window, event, values):
    """While the Brightness panel is open the dock keeps hovering (and remembers where it is dragged); anything else (a click on a program...) closes
       the panel and goes to the main loop"""
    if event == K_HOVER:
        G.hover = values[K_HOVER]
        redraw(window)
        return True
    if event == K_MOVED:
        remember_location(window, values[K_MOVED])
        return True
    return False


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


#  ███╗   ███╗ █████╗ ██╗███╗   ██╗
#  ████╗ ████║██╔══██╗██║████╗  ██║
#  ██╔████╔██║███████║██║██╔██╗ ██║
#  ██║╚██╔╝██║██╔══██║██║██║╚██╗██║
#  ██║ ╚═╝ ██║██║  ██║██║██║ ╚████║
#  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝

def main():
    sg.set_options(border_width=0, dpi_awareness=True)
    slug, name = use_dock(dock_arg())                                   # --dock "Claude chats": that dock's own files
    if not claim_dock(slug):                                            # already running: two copies would write the same files
        shown = dict(list_docks()).get(slug) or name or APP_NAME
        sg.popup_quick_message(f'{shown} is already open', font='_ 12', text_color='white', background_color=C_SELECT, auto_close_duration=2, non_blocking=False, keep_on_top=True)
        return
    new = bool(slug) and not os.path.exists(os.path.join(settings_folder(), WINDOW_SETTINGS_FILENAME))
    sg.user_settings_filename(WINDOW_SETTINGS_FILENAME)
    if not slug:
        migrate_settings()
    if new:
        start_new_dock(name)
    G.dock_title = sg.user_settings_get_entry(K_DOCK_NAME, None) or name or APP_NAME
    G.dock_ready = True
    G.launcher_settings = sg.UserSettings(ENTRIES_FILENAME)
    load_view_settings()
    apply_theme()
    window = make_psg_launcher()

    pending = None                                                      # a dock event that came in while the Brightness panel or a stack was open
    while True:  # The Event Loop
        event, values = pending or window.read()
        pending = None
        if event in ('Exit', sg.WINDOW_CLOSED):
            break
        menu_key = event.split('::')[-1] if isinstance(event, str) and '::' in event else event      # right-click items come back as 'label::key'
        if menu_key == 'Exit':
            break
        if event == K_HOVER:
            G.hover = values[K_HOVER]
            redraw(window)
        elif event == K_MOVED:                                          # the floating dock was dragged somewhere new
            remember_location(window, values[K_MOVED])
            float_side_check(window)
        elif event == K_DOCK:                                           # a dock dragged to an edge: docked there
            window = dock_at(window, *values[K_DOCK])
        elif event == K_FLOAT:                                          # pulled off its edge: floating where it was let go
            window = float_at(window, *values[K_FLOAT])
        elif event == K_REORDER:                                        # a program or section dragged to a new place in the Panel
            move_entries(window, *values[K_REORDER])
        elif event == K_TIP:                                            # a tip next to the dock (a docked Bar: on its inward side, not over it)
            notice(values[K_TIP], C_SELECT, 6, beside_dock=True)
        elif event == K_CLICK:
            part = values[K_CLICK]
            if part == 'close':
                break
            if part == 'hide':                                          # tuck it away now (auto-hide)
                hide_now(window)
            elif part == 'gear':
                menu_key = K_PROGRAMS                                   # handled at the bottom
            elif part == 'switch':
                window = switch_style(window, 'Bar' if G.style == 'Panel' else 'Panel')
            elif part == 'search':                                      # the magnifier: the Panel's search box on / off - the Bar's search flies out
                closed = G.stack_closed
                if G.style == 'Panel':
                    toggle_search(window)
                elif not (closed and closed[0] == 'search' and time.time() - closed[1] < 0.5):     # (not the click that just closed it)
                    pending = open_search(window)
            elif part == 'clear':                                       # the x in the search box
                set_search(window, '')
            elif isinstance(part, tuple) and part[0] == 'stack' and part[1] in Block.active_blocks:
                closed = G.stack_closed
                if not (closed and closed[0] == part[1] and time.time() - closed[1] < 0.5):    # the click that just closed it doesn't open it again
                    pending = open_stack(window, part[1])
            elif isinstance(part, tuple) and part[0] == 'app' and part[1] in Block.active_blocks:
                start_program(window, part[1])
                if G.search:                                            # started from a search: it clears a moment later
                    clear_search_later(window)
        elif event == K_STACK_OPEN:                                     # the mouse rested on a stack
            if values[K_STACK_OPEN] in Block.active_blocks and G.style == 'Bar':
                pending = open_stack(window, values[K_STACK_OPEN], by_hover=True)
        elif event == K_FIND_OPEN:                                      # a letter typed while the Bar has the keyboard: its search, with that letter
            if G.style == 'Bar' and search_on():
                pending = open_search(window, values[K_FIND_OPEN])
        elif event == K_DROP:
            files, x_root, y_root = values[K_DROP]
            if G.drop_index is None:
                drop_over(window, x_root, y_root)
            index = G.drop_index
            G.drop_index, G.drop_line, G.drop_item, G.drop_open, G.drop_stack = None, None, None, 0.0, None
            add_programs(window, files, index)
        elif event == K_REBUILD:                                        # Glass couldn't show the dock: back to the plain look
            G.glass = False
            sg.user_settings_set_entry(K_GLASS, False)
            window = rebuild(window)
            notice('The Glass look is not available on this PC - switched back', '#b71c1c', 4)
        elif menu_key == K_BRIGHT:
            pending = brightness_panel(window, keep_going)
            sg.user_settings_set_entry(K_BRIGHT, G.bright)
            apply_theme()                                               # the Programs window and popups follow the brightness too
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_ADD_LINK:
            ask_for_link(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_OPEN_DOCK):  # Docks > a dock
            open_dock(menu_key[len(K_OPEN_DOCK):])
        elif menu_key == K_NEW_DOCK:
            new_dock(window)
        elif menu_key == K_RENAME_DOCK:
            rename_dock(window)
        elif menu_key == K_DOCK_SHORTCUT:
            make_dock_shortcut()
        elif menu_key == 'Version':
            sg.popup_scrolled(f'{__file__}\n{APP_NAME} version {version}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10), icon=dock_icon_64)
        elif menu_key == 'Edit Me':
            sg.execute_editor(__file__)
        elif menu_key in (K_REFRESH, 'Refresh'):
            refresh_dock(window)
        elif menu_key == K_ADD:
            files = ask_for_programs(window)
            if files:
                add_programs(window, files)
        elif menu_key == K_SHARPEN_ALL:
            if ask_near(G.menu_at or pointer(), 'Sharper icons', 'Fetch every program\'s icon again, at full size?\n\nOnly icons that come out bigger are '
                        'replaced, and only by the program\'s own\nicon - a picture you dropped on an entry stays unless\nthe program has a bigger icon of its own.',
                        yes='Fetch them'):
                sharpen_icons(window)
        elif menu_key in (K_E_OPEN, K_E_FOLDER, K_E_EDIT, K_E_COPY, K_E_RENAME, K_E_REMOVE, K_E_SHARPEN, K_E_ADD_HERE, K_E_BAR, K_E_ADD_LINK):
            entry_action(window, menu_key)
        elif isinstance(menu_key, str) and menu_key.startswith(K_E_COLOR):     # a heading's Colour > a choice
            heading_color(window, menu_key[len(K_E_COLOR):])
        elif isinstance(menu_key, str) and menu_key.startswith(K_UNHIDE):  # Hidden from the Bar > Show ...
            num = int(menu_key[len(K_UNHIDE):])
            if num in Block.active_blocks:
                Block.active_blocks[num].bar = True
                save_entries()
                relayout(window)
                set_right_click_menu(window, make_menu())
        elif menu_key == K_KEEP_ON_TOP:
            G.on_top = not G.on_top
            window.keep_on_top_set() if G.on_top or (G.autohide and G.place != 'Floating') else window.keep_on_top_clear()
            if G.glass and G.layered:                                   # in case tk touched the window's layering: set Glass up again
                glass_free(G.layered)
                G.layered = glass_setup(window)
                G.keep = {}
                redraw(window)
            sg.user_settings_set_entry(K_KEEP_ON_TOP, G.on_top)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_STACKS_HOVER:
            G.stacks_hover = not G.stacks_hover
            sg.user_settings_set_entry(K_STACKS_HOVER, G.stacks_hover)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_SEARCH:                                      # right-click > Search > Search box / Search button
            toggle_search(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_SEARCH_MODE):     # right-click > Search > Hide / Dim what doesn't match
            G.search_mode = menu_key[len(K_SEARCH_MODE):] if menu_key[len(K_SEARCH_MODE):] in SEARCH_MODES else 'Hide'
            sg.user_settings_set_entry(K_SEARCH_MODE, G.search_mode)
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_SECTIONS:
            G.sections = not G.sections
            sg.user_settings_set_entry(K_SECTIONS, G.sections)
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_VERSIONS:
            G.show_versions = not G.show_versions
            sg.user_settings_set_entry(K_VERSIONS, G.show_versions)
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_BAR_LABELS:
            G.bar_labels = not G.bar_labels
            sg.user_settings_set_entry(K_BAR_LABELS, G.bar_labels)
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_THEME):
            G.theme = menu_key[len(K_THEME):]
            sg.user_settings_set_entry(K_THEME, G.theme)
            apply_theme()
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_SIZE):
            set_size(window, SIZES.get(menu_key[len(K_SIZE):], 1.0))
        elif isinstance(menu_key, str) and menu_key.startswith((K_TEXT, K_COLUMNS, K_MAGNIFY, K_LAYOUT)):
            for prefix, name in ((K_TEXT, 'text'), (K_COLUMNS, 'columns'), (K_MAGNIFY, 'magnify'), (K_LAYOUT, 'bar_layout')):
                if menu_key.startswith(prefix):
                    setattr(G, name, menu_key[len(prefix):])
                    sg.user_settings_set_entry(prefix, getattr(G, name))
            relayout(window)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_OPACITY):
            G.opacity = int(menu_key[len(K_OPACITY):])
            set_opacity(window, G.opacity)
            sg.user_settings_set_entry(K_OPACITY, G.opacity)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_STYLE):
            if menu_key[len(K_STYLE):] != G.style:
                window = switch_style(window, menu_key[len(K_STYLE):])
        elif menu_key == K_FLOAT_VERTICAL:                              # a floating Bar: across <-> up and down
            remember_location(window)
            G.float_vertical = not G.float_vertical
            save_style_setting('VERTICAL', G.float_vertical)
            window = rebuild(window)
        elif isinstance(menu_key, str) and menu_key.startswith(K_FLYOUT):   # Fly out > how soon
            G.flyout = float(menu_key[len(K_FLYOUT):])
            sg.user_settings_set_entry(K_FLYOUT, G.flyout)
            set_right_click_menu(window, make_menu())
        elif isinstance(menu_key, str) and menu_key.startswith(K_HANDLE_COLOR):     # Handle colour > a colour
            G.handle_color = HANDLE_COLORS.get(menu_key[len(K_HANDLE_COLOR):])
            sg.user_settings_set_entry(K_HANDLE_COLOR, G.handle_color)
            redraw(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_HANDLE_CUSTOM:                               # Handle colour > Custom...: the colour picker
            if pick_handle_color(window):
                redraw(window)
                set_right_click_menu(window, make_menu())
        elif menu_key == K_BUBBLE_SECTION:
            G.bubble_section = not G.bubble_section
            sg.user_settings_set_entry(K_BUBBLE_SECTION, G.bubble_section)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_HANDLE_NAME:
            G.handle_name = not G.handle_name
            sg.user_settings_set_entry(K_HANDLE_NAME, G.handle_name)
            redraw(window)
            set_right_click_menu(window, make_menu())
        elif menu_key == K_AUTOHIDE:
            G.autohide = not G.autohide
            save_style_setting('AUTOHIDE', G.autohide)
            window = rebuild(window)
        elif menu_key == K_GLASS:
            G.glass = not G.glass
            sg.user_settings_set_entry(K_GLASS, G.glass)
            window = rebuild(window)
            if G.glass:                                                 # a new look: keep it only if it shows - it switches back by itself otherwise
                keep = ask_near(pointer(), 'Glass look', 'Keep the Glass look?\n\nIf the dock looks wrong or has vanished, just wait:\n'
                                'it switches back by itself in 15 seconds.', yes='Keep it', timeout=15)
                if not keep:
                    G.glass = False
                    sg.user_settings_set_entry(K_GLASS, False)
                    window = rebuild(window)
        if menu_key in (K_PROGRAMS, 'Programs...'):
            G.hover = None
            redraw(window)
            programs_window(near=window_rect(window))                   # where you left it last time - or in the middle of the dock's screen
            refresh_dock(window)                                        # the list may have changed
    remember_location(window)
    glass_free(G.layered)
    window.close()


blank_image_30x30 = b'iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAYAAAA7MK6iAAAAGklEQVR4nO3BMQEAAADCoPVP7W8GoAAAAKAzDi4AAXXIMrUAAAAASUVORK5CYII='

launcher_icon = b'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAE4UlEQVR4nO1V24uVVRT/rb33dzvnzMW8JOPdUSZx7OagYZlJhvfCQAkkQp/qwYeoByVsknwoUehJEIQgyQd7KAQpBDEHK43OQ46allLqTNnMmTlz5sz5zved79tr9XDmZv4JtWFt9l4/WL+19t7rt4H/x39odIoiAJMNnaIAQKRTPYjQqA+Qzk4Fook4RHXf2PZfNC6AMZAB1CZj80axOw9jzjxA36mvBUA8QdApCgdIWt7ten/6zDlPOTasAECiM9mBvrv5nkNrDl77+sl902dPXSlVNQIAOiOZgZ7+7rYNP3/w0/oX32mZ8ejqiPQwIJQlBD1/99346Juz+0/VyQCs+7jl6cO3LovIy5Ns2+OH73Y9s33dsmr32i6R5FUR2TqKbS1fW3/xyHZnWc9rO7+VsLxDRLaIyCsisql39xuXj82Z0woApn4YCVlGOhRDiY0ZACLrqZQl1aQUoZYg7VcpsoC1MJ6nCJxYB5qsJCgUVNzEpK2FmdKgiDlRrkvjBA3lm1EhkqUrjhY+VbYWAwIxnj8S2Ri3K0XmyhL07jiOKkWkABj2lI3k0lC2uFMPL4r27j0WiVRAUA7gohIGg42N4UQFABSRjcU8IswABIoNCPKXuEwgslBJk9G2CQRAEwQYcKwQDFlj00adpI1EBKMUQBSOxTUAkPWMgrAiTixJIoCAWBNByOiMZo4JKWyakhABmoggBC9wtTBRTYRTIgsiEgixgMRxFEafJN2/mA+t8mri5rTVvrHaN+JmdQqD7ovnKo5OgCy08WG0D4MstGNSunC2v+JwgozWygecADANSussOKne+DGsdwWAPe8dau0abjkVz3vB0zYiALDak6l9PwwvTn+9vnFpfsnmZwtNNlYkAnJ85nOXp5RPdj93beP97se2ctxclXqsDIl8GYqcb1+148TBt3+hI6e+D86dPtl177fujqZccNUYByxCAAugcnAyzZWqlCBcJlUPIiIi0NlcgCkhc0mEy5pAAAkzy0Cp3N7Wuvj6yhWrVpnbNy4tHBzoWzYSpRJzrZ0lGm9PEQF4CFpTM0iNtw0IgAhKRYYi1UyTpIKUgq5FUiz0L/lzaKDNjBTDoUw2V9ZGT2ObyGT5oNGJWUCwD8kXESDgCWIQxLJAacpkcyNptThAANSW1996M4ri/eFIOUeAnpQOoIjYkqQs45omAhhFUFrICsAyQQHAZrKZMOv7h86cOPoJYflyB/l8MLdj8wp/xux5thYqiCJoBS7e46TwBy+YG6iFszyVWK4rm1a42xvLzbs1Oz8XqPmZQFkAsIDvGVsol3rOXLlyCUBIANC2+3hDadGm1eJnNaB5LP1qeaDW+Nmq279/5bWaaY0uwHVMC6GUpus3XL91YuFLC2c0eB5E8Wh5VGErX5Qq3+26cGHIAED/E89TrmozHJessCUA0Iop0Vmz58M9oXFOBmEh0IAVANCwQOC6n+9bF+rTzX4fqg5E1TFiIcd1ts1qpl1j2r/AH65aMYNQWpRxUuX6CSvfBlqKxphiKmbIdVLrepS4HiXaUaxTNVRtHCkaqhVdUewrSRziVBOJsC32DQ6GeODD6RTTlikEgyELAHBGUXt4tXrhwNpUzq8xmJkEsE79MnVC+UocdXTkk/Nr1pj2pqaAPU8AQMUx3entjTry+QQA/gF0+YdyFnDz5wAAAABJRU5ErkJggg=='            # PSG Dock icon, 24 px, beside the title

dock_icon_64 = b'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAANlklEQVR4nO1afXBc1XX/nXvve7tvV9JKlvwhW7YsgY2xKV82CYZQORA+CkNKQu3pkATP0A6fiYFJk5AZQHFJJ2TSmVBTkgwkIVOgAdvQEkM6qSFU1CYmtmNiQ4SpiZAtf8j61q60u2/fPad/vJUtS7vyytBSqH4zRzurve/cc3/33nPOvecBU5jCFKYwhSlMYQpTmMIUpjCFKUzh/xvoA2ozAvmA9Pxv6ir6DEGEQAolidKAiCpknDRDGU1QCiWJ0QQRqIJWNTcrTQRVohgiNKOwLkzAJI1iraIEtgiADyANIkCOEy4CIoLk21SUMBsKQApAMOrZ8AcicKg7AiBagi4CMICwIVGB9mbcIyIEInFrFy6quvbb91BVw3Jm9iboS6AUtARH/X1bnu157uvfB6kshEnCXuXWVdOvvPEvZ6yZVUVnwrIpRjuBRAxx7yDaNr3Y+yjRoafzJIQMiuDbZ591y5W1s77kAXOsMEGoiDaBUdrv8LNv/MM7e79HBztfL0TCWAIUlOZo5fz6qht+/K/uwkvOcIe6hxKe2s8CXaQfYUD355xl7tyly1S8srbriZvvXi9CSpFd88UZl99/15znqhdEY+iNdEJ5vYDognwSMdgva6gY/vSChuiKSJwcpQ4+IbJSE22w65ae9/WbT2v8bkQrDEe990ibNETUWFUEAIqspIdnLRZcP8+LfYpl95+pQ4d2NQNqLcAntD0+GFEg4ppVDzXHV6z5VnVwdMdLf1X5QFUskhyzLcb2FzzU0r9s3S56wB84oo8+/qUL+cCONyyL85v1izddeFXiylzX6U9T4z89dgJ1BewWwErbl1e5iZ23t24f2r34qj2XGE2D5U5k7tZLm7YvrKioSS6/+DuVa+7cDMAE4SwW0iUB4CbvuO2rVQP9l29s3/+TlVte+2sRISI6vq1OnMxQkamuX8Qi8ueL3H+pikX6OoeDRADEskFQVkDifcNB1V1NldtmRzM7UTYzEmtc1sgsAFAxs8acjh6xqvb+5wygDYbLEGTjJsiWjZG4QTbuAHG34R83oc/pm5agBiAyI7CCc6eVz51mzMzhqPdu5Zo7Xw6y2QSy2Tiy2XiQzZaNFgRBLEgmKwzge5+7fiPYSp3nLQSgHKVk9MSP9wEARMQSmCKGAgBOuWusAcQYU9ARZG1AAFzHOGlABHxsiQlEGJYEsBT253IxPSOzFwDakM4yw4ysFE3EAogyOnPM7kiECw4AgPE8C8BBfsAM4YLtCj4tIIDgKGUBUGBBwQSxN22hKgAoEgbU2Hbh0haHwxVnJ47hga9gYjkg9FhjFJGABIDA9xW0Lk6ktRQYo+C6FggfLNSsIAFEECGN1i5/LoBXKyJwANhifc00JgOA+4bt3NC8YySQCFl4oiWzuxqxxj1ApByjnNDYrmFMhtJ7Z0H5CYAyEYCyI9wAotLpmQAcU14+WHQCAcAYZYD+9DtvL42CIAQuFPYLbwFSpG0Wv27Lrb77xb5MU6O7LxuQLkaB0pAfb09d05VRS5TNAOq4bxFAYIRUz7qvgo8+ClM3ALJqrKowxCixQX8U/U+uRizwAJWKRLLIZgFXRDEo5/jZWYN33PYN97PXrYcxrAvMjAYgjmPtvn2f4Jc335q3o/QVABGCWPiWKze2yjeee7Nfxi/I442FNIlyoTiTj9rHQQDBJ2gMLsDgY9+zPgnReGUcJk2iHQl/yh7LLE/gOiMCp/PIitxjP1oRAEJFBiaARAGCCBBx89t6PIqmiACBSAJl01x88ABARMLQNl1sWQME5AKy1idRVNyXKALZHEngky2eLAEZwAaAqAn8kgIoA7AlCorbPiEBx5zhxG2ON52wHQFEBJrI/Uvof+ikdoWe9uS6AAWRCZ1uSYP7OGOKgA/bgA8bUwR82AZMBCKIjApfhc7z7xeFb12KxMzStR6LCOb9Miz5HIlECh/HSzUp/Bg3rtH20aoN4XdCwPnIP1nGhYiA9ACeWblSe56ngzAHlUnpIggLhJkIrqtWrl+p+wBweI6dnE1EApDk8jdLOeYTSDhhgjZ89xa1cv163bXn17/IDSehTcRALAN8cuGATVmNGu491Drwmyd2rNqwIZ5Op/v+0HrkRRVTBCjFDGYBMxeR/G/CgKoy1H6g599TKb9j56oNZa8d7t7bNdC3pTwaJSsiLBK2n0CsCCsiA7b0+wP7n29uFv7WkiXO6JVAoz5VXV2d29HRkf78jTf9aWviiq8Nzr/qQkVUIzIx6RQyjeH+o+8sPvDUm+ctrK1NpzOO53n2cMfB3ns+szF2/vnuRVDGgRRaiHmMdCPM774ztP2+5z/bOb1uwUx/OKUiXrkdaN11pPlwa8OcROKcMOM+mTKCYTv4b1m74/s1DQ9t/tnDm+rr66Pt7e1B/gghNDL4+vomp729JXPb2of/xo14D7617eWDe/YP/LbmohuSYCiGLZx8CUOZqFC6J9Ctz8dra2deqiJl05itEAGkjN3f1vHaNUuP/vGi87Rhn1Uxm1kAN6r493s5eOY/KmfPrq9vUkpcYYEiRVnmVE/Hu698MW56GhzjZJgnTD8dbfjJtgOxtnlnnNP0qcsWgfnv19176z31TU1Oe0tLDgCHg29qcttbWjK3Na+7XTvuI6/+6nlOpVIq5mrceN2lP0mUl2eCgBVRoaWgADACJjejYgnLnIHYQJEChCEQMo4TS6adrLVO8qTuVQClbKws5sclyA1DwCAFFoYCadKul1IqyY7KqJMEMQbj2ac2rg5SqbhxHNt09ee0VurBR+6/45v19U3R9vYWn5qamkxLS4tc/fmb6hqXfmL3tld+VdbdeQiRqEccJuclRQQRABzkm4+9amQoRVDj7kqK6GKBZQEVmF8RhiYq1axwVxFJLufDi8V5xVXXqb7DRy745x8+sGvp0qXaeJ6nAWTnn33uFYN9vRXdnYds1ItpZh65yinJ64Y3sYVnZGQgXPy8OE5bMbKI1CRDCggi5LoRJAf6pavzMM2aO+c6ADsdpzGi+vvLFQA4jrswlRyQEOPG9lEWID+PRAqDA31QSi8I/3sAKpdL5yeaC5a1Po6QfAkvl8udsMn4FIuIHyVQ3l3xMQIcp1sAqMGB3r0VldMoxIdt5wcPIgURlqrq6eSn03vD/86E2ta9jQHEX9+8qaWsPNE1p75RDw+lrFIqvML5GIhSCpn0EFdPn6Wqp8/039zxn78E4PX2trLBPnBVVaNqfeP1riUXXHLf+cubfhQEgT584D1LpGhMsfcjBcr/YWaZNn2WvvgzV6Ov68h3tvzy2b2JxDy3o2P/UL5aAzcWq0kMD3era1d/+QsNZ/zJN3t7uip7j3aChYsWBf8vY3SiXFk9HTUzatNHD7Y9/MwPHnzEq64O0j09gwCylL9GdwB4kUiiMpsdMHWnLVzyycuuvaK8onoRi/WErZZ8ueSkPYucQNbILJzSKx1jjn7HDi4nUUZEAoEorawik02lBvbt2vrSy/+1Z+fvIpGKIJsd7AcwDCA3cgOr8y8dxFy3vNL3k7H897K8RPIkjU/zxvR9sjFNAqeqayRPCvIvbaQAJAFkXbcs7fupfgBDALIAgpHiI+cfyPp+MgkgqGg4tzpy5jUOGyPiZ3IQCSBcfBVoDdu9T9K7XwhC48Oaje9Dlp1Xpi9fnlB6ElcaW383wK9sTVnXPU6ED8jVtbX6nIqKcZWlEYyUvjURO0pZiDgvdXVh68GDSe2nhgGkAeRGwv6IcgVAoa7OQUeHTlx214yKy+4+S8VqNNQkZk5rDL212e9+dFW3QQ5BEPB9X5lT/rdfm5eAW/rgAQBW6Ic/7Uzefl9bvzFQQQB+avkF1TfMb/AmpUeEkr4vP2vveHvNzp0dtQAfDgmwownIL+0mBbSoOX/XdjGcaI2yvi9celZASoQiFc7Qb598r+fprxz+5Lk1sS0/P+1MKNZ+lqTUFWABaBKKeBo33fne3sd/cWTg3iVLau5dcsbpycAWLdIWNorEiBgWHlq9bcerLxw+7I9K+o7V3vL7piWoX/24gjYxAgeiDMFolCwwgPVRtuAiB0DPHV+YFkDDgRC7LqB1aeJqQCtiMOubr68WAF1/MXeWyrEoTSQmH7pKEhEKAKtIRfO3QYGMuqIbnQoLAMTnX1Dyma0ghEl58QBAZsmCeLaEJ4rCMmh2XdQH4JdH3AlrfBNhpAJcH4uNG9u486s3e8n7DvnK9RgA5sx0J7dcC2DGNGMBIOE61pYShidATSQybmz/I3UBydd24/H3rysaDT8n60NLxTgCdt6CQBNlhEkThIkhpQpEhNlqscEgALT3RIfAYgEQNPGoGF2KhDmVcBIAfFcPWhGCIhGahGjFYFYM+Fi8OIMxBZYTCRAhgCQTmDcBMARR0sotTcSF1p6Q7pxW3dcmAJ316ZaUhX2bwBGyEiHAJV2CAC4TeZzjd2nx9h4R0MNPnX3IaNqvxMYUkVuyCCJkjCbot2jt2mDsmyJF91R9c1tlEPfmacsOVAnHISYKhJOHsnP+iLXhSwkj+XjqD0tr48adBRLyJ1jOJ/4WdNGCHQdG2SkioP5VK+dTLjdNaMLXA0I44RW7Nraj4ucvdBd7XbYQPoY3AoUxwUCFTukIWGBmTrXWSAUsKPay00l1FZn5/wbjepkPMOCMewAAAABJRU5ErkJggg=='            # PSG Dock icon, 64 px, window / taskbar icon

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        sg.popup_error_with_traceback(f'{APP_NAME} crashed', e)
