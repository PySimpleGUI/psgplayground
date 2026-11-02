# Background work that reports into the window

**What you get:** a long job (pip install, a network scan, reading a big file, MIDI input) runs in a thread while the window stays
responsive, lines of progress appear as they happen, and a crash in the thread shows a proper error popup instead of vanishing.
The Toybox's "Install missing" button is this.

## Prompt

```
Write a PySimpleGUI 6 program (single .pyw) with a Multiline output area and a button that starts a long job - run
"python -m pip install --upgrade <package>" as a subprocess and show its output line by line as it arrives.
Requirements:
- The window never freezes; you can move it and the output scrolls in while the job runs.
- The button is disabled while the job runs and enabled again when it finishes; a status line shows "done" or the exit code.
- No popup or window is created from the thread. Every result goes through the event loop.
- If the thread hits an exception, the main thread shows sg.popup_error_with_traceback with the traceback.
- No console window appears for the subprocess on Windows.
```

## Hints for the model

```
- threading.Thread(target=job, daemon=True).start()
- From the thread, only ever:  window.write_event_value('-LINE-', text)   /   window.write_event_value('-DONE-', code)
  and on exception:  window.write_event_value('-ERROR-', traceback.format_exc())
- In the event loop:  if event == '-LINE-': window['-OUT-'].print(values[event])   (Multiline.print appends and scrolls)
- subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
  then  for line in proc.stdout:  ...;  code = proc.wait()
- Never call window[...].update() or any sg.popup from the thread - tkinter is single-threaded.
- Several jobs: give each a key tuple ('-LINE-', job_id) and check event[0] in the loop.
```
