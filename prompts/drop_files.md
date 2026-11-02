# Drop files onto the window

**What you get:** drag a file from Explorer (or a program, or a block of text) onto an element in your window and the program uses
it - fills in a path, loads an image, reads a document. The PSG Dock fills in a program's name, path and icon from one drop.

## Prompt

```
Write a PySimpleGUI 6 program (single .pyw) with an Input for a file path and an Image element next to it.
Requirements:
- Dropping a file from Explorer onto either element puts its path in the Input; if it is an image, show it in the Image element.
- Dropping text onto the Input pastes the text.
- The drop arrives in the normal PySimpleGUI event loop like any other event.
Use the psgdnd package (pip install psgdnd) - it wraps tkinterdnd2 for PySimpleGUI.
```

## Hints for the model

```
- import psgdnd
- After the window is finalized:  psgdnd.register_element_dnd(window['-PATH-'], window, psgdnd.DROP_TYPE_FILES)
  (DROP_TYPE_TEXT for text, DROP_TYPE_ALL for both).
- In the event loop:
      if psgdnd.is_drop_event(event):
          if event.drop_type == psgdnd.DROP_TYPE_FILES:
              filename = values[event].split(',')[0]        # several files come comma separated
          elif event.drop_type == psgdnd.DROP_TYPE_TEXT:
              text = values[event]
      event.key is the key of the element that received the drop (so one handler can serve many rows: event.key[1] = row number
      when keys are tuples).
- Images for sg.Image: PNG/GIF directly (filename=...); other formats via Pillow -> PNG bytes -> update(data=...).
- psgdnd needs tkinterdnd2, which pip pulls in; the program should say so in its docstring.
```
