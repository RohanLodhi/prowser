# Prowser

Prowser is a minimal, educational web browser built with Python and Tkinter. It demonstrates the concepts of virtual DOM (VDOM), HTML parsing, and rendering web content using a custom renderer. The project is modular, with clear separation between networking, parsing, rendering, and browser logic.

## Features

- Fetch and display web pages using HTTP(S)
- Parse HTML into a virtual DOM structure
- Render HTML elements (headers, paragraphs, links, buttons, forms, etc.) using Tkinter widgets
- Scrollable content area with mouse wheel and arrow key support
- Clickable hyperlinks and basic form handling
- Modular codebase for easy extension and learning

## Project Structure

```
prowser/
├── browser.py    # Main browser logic and UI
├── main.py       # Entry point
├── network.py    # Networking (fetch_url)
├── parser.py     # HTML to VDOM parsing
├── renderer.py   # TkRenderer: VDOM to Tkinter widgets
├── vdom.py       # VNode class (virtual DOM node)
└── README.md     # This file
```

## Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`

Install dependencies with:

```bash
pip install requests beautifulsoup4
```

## Usage

Run the browser:

```bash
python main.py
```

Enter a URL (e.g., `example.com`) and click "Go" to load the page. You can scroll using your mouse wheel, touchpad, or arrow keys. Click hyperlinks to navigate.

## Extending

- Add CSS, JS (main feature)
- Add new HTML tag support in `renderer.py`
- Improve VDOM diffing or event handling in `browser.py`
- Enhance HTML parsing in `parser.py`