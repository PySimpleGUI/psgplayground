# Drag an entry to reorder a list

**What you get:** a scrolling list of entries (each a row of elements, not just text) that you reorder by dragging a ☰ grip.
The entry lifts out as a floating copy that follows the mouse, a shaded slot shows where it will land, the list scrolls when you
drag near its top or bottom, and on release the entries are renumbered. This is how the PSG Dock's settings window works.

## Prompt

```
Write a PySimpleGUI 6 program (single .pyw) with a scrollable list of entries. Each entry is a row inside a Frame: a "☰" grip
text, a Checkbox, an Input for a name and an Input for a path, plus a delete button. There are Add and Save buttons above the list.
Requirements:
- Press on an entry's ☰ grip and drag to move it. The press only becomes a drag after the mouse moves a few pixels.
- While dragging, the entry lifts out of the list as a floating copy (its own borderless top-level window, slightly transparent,
  with an orange outline) that follows the mouse but never leaves the list area, and a shaded empty slot in the list shows where
  it will land. Dragging near the top or bottom edge of the list scrolls it.
- On release the entry lands in the slot; the entries keep their widget keys but their contents move (so nothing is destroyed).
- Everything the mouse does is sent into the normal PySimpleGUI event loop; no logic lives inside tkinter callbacks.
- Save writes the list to a settings file; it loads it on start.
```

## Hints for the model

```
- The list: sg.Column(rows, scrollable=True, vertical_scroll_only=True, expand_x=True, expand_y=True, key='-LIST-').
  Call window['-LIST-'].contents_changed() after adding/removing rows (PySimpleGUI's scrollregion goes stale otherwise).
- Keys for repeated rows: K_NAME = '-NAME-';  K_B_NAME = lambda n: (K_NAME, n)  - events come back as tuples, so event[0] tells
  the kind and event[1] the row number.
- Grip bindings (on the grip's tk widget) that forward to the event loop:
      w.bind('<ButtonPress-1>',   lambda e, n=n: window.write_event_value('-DRAG PRESS-',   (n, e.x_root, e.y_root)))
      w.bind('<B1-Motion>',       lambda e, n=n: window.write_event_value('-DRAG MOTION-',  (n, e.x_root, e.y_root)))
      w.bind('<ButtonRelease-1>', lambda e, n=n: window.write_event_value('-DRAG RELEASE-', (n, e.x_root, e.y_root)))
- The row frame PySimpleGUI packed the entry into: window[K_B_FRAME(n)].Widget.master; its parent .pack_slaves() is the list
  of rows top to bottom. Lift = row.pack_forget(); slot = tk.Frame(parent, width=w, height=h, bg=...) with pack_propagate(False),
  packed with before=<row> at the target index; the floating copy = tk.Toplevel(window.TKroot) with overrideredirect(True),
  attributes('-topmost', True), attributes('-alpha', 0.9), geometry(f'+{x}+{y}').
- Landing index: the first row whose rooty + height/2 is below the mouse's y_root.
- Autoscroll: window['-LIST-'].widget.canvas.yview_scroll(±1, 'units') when y_root is within 30 px of the list's top/bottom.
- Release: re-pack the original row (pack(before=next_row, **saved_pack_info)), destroy the copy and the slot in a finally:, then
  move the CONTENTS (name, path, checkbox) along the entries so entry number `index` holds the dragged one.
- Mouse cursor: window.set_cursor('fleur') while dragging, window.set_cursor('') after.
```
