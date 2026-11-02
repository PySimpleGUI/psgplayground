# Resizable panes that remember their positions

**What you get:** two or three areas side by side with draggable dividers (sashes), each area filling its pane completely as the window
grows, and the divider positions restored the next time the program starts. The Toybox's Sections | Apps | Details is this.

## Prompt

```
Write a PySimpleGUI 6 program (single .pyw) whose main area is three panes side by side separated by draggable dividers:
a Listbox on the left, a Table in the middle, and on the right a block of text with a Multiline under it.
Requirements:
- Each element fills its pane completely and grows with the window (the Table gets taller and wider, the Multiline too).
- When the window gets wider the extra width goes to the middle and right panes; the left pane keeps its width unless I drag its divider.
- Each pane has a sensible minimum width so nothing collapses to nothing.
- The dividers are visible (a slightly lighter bar with a small grip in the middle) and show a left-right cursor.
- The divider positions and the window size are saved on exit and restored on the next start.
- Long text on the right wraps to the width of its pane and re-wraps when the pane is resized.
```

## Hints for the model

```
- sg.Pane([col_left, col_middle, col_right], orientation='h', expand_x=True, expand_y=True, show_handle=True, relief=sg.RELIEF_FLAT, border_width=0)
  Each member is an sg.Column(..., expand_x=True, expand_y=True); the elements inside also get expand_x=True, expand_y=True.
- The tk widget is window[key].PanedWindow. After finalize:
      pane.configure(sashwidth=7, sashrelief='flat', bg='#2f3a4e', sashcursor='sb_h_double_arrow', showhandle=True, handlesize=10)
      for child, minsize, stretch in zip(pane.panes(), (120, 220, 380), ('never', 'always', 'always')):
          pane.paneconfigure(child, minsize=minsize, stretch=stretch)
- Restore: window.refresh() first (geometry must exist), then pane.sash_place(i, x, 0) for each saved x.
  Save on exit: pane.sash_coord(i)[0] for i in 0, 1 -> sg.user_settings_set_entry('-sashes-', [...]).
- Window size: sg.Window(..., size=saved_size or (None, None)); window.set_min_size((w, h)); save list(window.size) on exit.
- Wrapping text: bind '<Configure>' on the right pane's frame and set window['-TEXT-'].Widget.configure(wraplength=frame.winfo_width() - 16).
  Guard against re-entry: changing wraplength resizes the label, which fires <Configure> again - only act when the width changed.
- Table columns: tree = window['-TABLE-'].Widget; tree.column('Needs', stretch=False); tree.column('Name', stretch=True) so one column takes the extra width.
```
