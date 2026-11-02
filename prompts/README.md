# Prompts - make these things yourself, with any AI chatbot

The programs in this Playground were all written with an AI assistant. The tricks that make them feel polished are small, and
PySimpleGUI makes them short - short enough that a chatbot can reproduce them from a one-paragraph spec. Each file here is one
trick: what you get, a prompt to paste into your chatbot, and the handful of PySimpleGUI / tkinter calls that make it work
(the part a generic model most often gets wrong).

| Prompt | What you get |
|---|---|
| [frameless_window.md](frameless_window.md) | A window with no title bar: drag it by a strip across the top, ✕ to close, size grip, still on the taskbar |
| [resizable_panes.md](resizable_panes.md) | Side-by-side panes with draggable dividers that remember their positions between runs |
| [picture_buttons.md](picture_buttons.md) | Buttons that are pictures - an icon with its label - with disabled and narrow-layout versions |
| [drag_to_reorder.md](drag_to_reorder.md) | A list of entries you reorder by dragging a grip; the entry floats, a slot shows where it lands |
| [drop_files.md](drop_files.md) | Drop a file (or a program) from Explorer onto the window and use it |
| [background_work.md](background_work.md) | Long jobs in a thread that report into the window without freezing it |
| [app_skeleton.md](app_skeleton.md) | The skeleton every program here uses: version, change log, right-click menu, settings, no silent crashes |

How to use one: open the file, copy the block under **Prompt**, paste it into Claude / ChatGPT / Gemini / whatever you use, then
paste the **Hints for the model** block after it. Ask for the whole program as one `.pyw` file. If the first try isn't right, paste
the error or describe what you see - these models are good at the second round.

These prompts describe PySimpleGUI 6 (`python -m pip install PySimpleGUI`). The hints name real calls in the library; if your
model invents something that isn't in the hints, ask it to stick to what's listed.
