# The skeleton every program here uses

**What you get:** the habits that make a PySimpleGUI program pleasant to live with - and the things a chatbot leaves out unless you ask.
`Templates/app_template.pyw` in this repo is the finished version; this prompt gets you the same from any model.

## Prompt

```
Write a PySimpleGUI 6 program as a single .pyw file (no console window on Windows) with these conventions:
- A VERSION constant at the top and a CHANGE LOG in the docstring (newest first, one line per change). Show the version in the window.
- Every element key is a module-level constant: K_NAME = '-NAME-'. Repeated elements use a tuple key made by a lambda:
  KT_ROW = lambda n: (K_ROW, n). No raw key strings inside the layout or event loop.
- A right-click menu with "Edit Me", "Version" and "Exit": Edit Me opens the file in my editor, Version shows the file name,
  version and sg.get_versions() in a scrolled popup, Exit closes.
- Settings persist through sg.user_settings (window position via auto_save_location=True, plus any choices the user makes).
- Keyboard: Escape closes; scrollable areas take Up/Down, PgUp/PgDn, Home/End.
- main() is wrapped so that any exception shows sg.popup_error_with_traceback instead of a silent exit (pythonw has no console).
- Threads report into the event loop with window.write_event_value, never touch the window directly.
- Lines up to 180 characters; one element per line in layouts; comments explain the why, not the what.
```

## Hints for the model

```
- Right-click menu: sg.Window(..., right_click_menu=sg.MENU_RIGHT_CLICK_EDITME_VER_EXIT)
      if event == 'Version': sg.popup_scrolled(__file__, f'{APP_NAME}  version {VERSION}', sg.get_versions(), keep_on_top=True, non_blocking=True, size=(70, 10))
      elif event == 'Edit Me': sg.execute_editor(__file__)
      if event in ('Exit', sg.WINDOW_CLOSED): break
- Settings: sg.user_settings_filename(filename='myprogram.json') before building the layout;
  sg.user_settings_get_entry('-key-', default) / sg.user_settings_set_entry('-key-', value).
- Keys: window.bind('<Escape>', '-ESCAPE-');  for a Multiline:  text = window['-OUT-'].Widget;  text.bind('<Prior>', lambda e: (text.yview_scroll(-1, 'pages'), 'break')[1])
- Crash guard:
      if __name__ == '__main__':
          try: main()
          except Exception as e: sg.popup_error_with_traceback(f'{APP_NAME} crashed', e, traceback.format_exc())
- The editor for "Edit Me" is set once in PySimpleGUI's global settings: python -m PySimpleGUI.
```
