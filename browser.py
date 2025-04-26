import tkinter as tk
from tkinter import ttk
import requests
from bs4 import BeautifulSoup
from vdom import VNode
import urllib.parse
# from parser import parse_vdom

class SimpleBrowser:
    def __init__(self, parent=None):
        if parent is None:
            # Create our own root window if none is provided
            self.root = tk.Tk()
            self.root.title("Prowser")
            self.root.geometry("800x600")
            self.root.config(bg="white")
            self.parent = self.root
        else:
            # Use the provided parent
            self.parent = parent
            # Check if parent is a Tk instance to set title
            if isinstance(parent, tk.Tk):
                parent.title("Prowser")
                parent.geometry("800x600")
                parent.config(bg="white")
        
        self.script_functions = {}
        self.widget_map = {}
        self.current_vdom = None  # Initialize current_vdom attribute

        # URL bar and fetch button
        self.url_frame = tk.Frame(self.parent, bg="white")
        self.url_entry = tk.Entry(self.url_frame, width=50)
        self.url_entry.bind("<Return>", lambda event: self.load_url())
        self.fetch_btn = tk.Button(self.url_frame, text="Go", command=self.load_url)
        self.url_entry.pack(side=tk.LEFT, padx=5)
        self.fetch_btn.pack(side=tk.LEFT)
        self.url_frame.pack(pady=10)

        self.root.option_add("*Font", "Arial 12")
        self.root.option_add("*Label.Font", "Arial 12")
        self.root.option_add("*Button.Font", "Arial 12")

        # Content area (scrollable)
        self.content_canvas = tk.Canvas(self.parent, bg="white", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.parent, orient="vertical", command=self.content_canvas.yview)
        self.scrollable_frame = tk.Frame(self.content_canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )

        self.content_window = self.content_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.content_canvas.configure(yscrollcommand=self.scrollbar.set)

        self.content_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.content_frame = self.scrollable_frame  # For compatibility with existing code

        # Bind mouse wheel for scrolling (cross-platform)
        self.content_canvas.bind_all("<MouseWheel>", self._on_mousewheel)      # Windows/macOS
        self.content_canvas.bind_all("<Button-4>", self._on_mousewheel)        # Linux scroll up
        self.content_canvas.bind_all("<Button-5>", self._on_mousewheel)        # Linux scroll down

        self.content_canvas.bind_all("<Up>", self._on_arrow)
        self.content_canvas.bind_all("<Down>", self._on_arrow)

    def load_link(self, url):
        if url.startswith("#"):
            return  # Ignore anchor links

        # Resolve relative URLs against the current base URL
        current_url = self.url_entry.get()
        if not current_url.startswith(("http://", "https://")):
            current_url = "http://" + current_url

        absolute_url = urllib.parse.urljoin(current_url, url)
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, absolute_url)
        self.load_url()

    def load_url(self):
        url = self.url_entry.get()
        if not url.startswith(("http://", "https://")):
            url = "http://" + url
        try:
            for widget in self.content_frame.winfo_children():
                widget.destroy()
            self.widget_map.clear()
            new_vdom = self.fetch_and_parse(url)
            self.current_vdom = new_vdom
            self.render_vdom(new_vdom, self.content_frame)
            # Reset scroll to top after rendering
            self.content_canvas.yview_moveto(0.0)
        except Exception as e:
            error_label = tk.Label(self.content_frame, text=f"Error: {str(e)}", fg="red")
            error_label.pack(pady=20)

    def update_dom(self, html):
        # Step 3: Parse HTML into a new virtual DOM
        new_vdom = self.parse_html(html)
        # Step 4: Diff old and new VDOM, then reconcile
        if self.current_vdom:
            diffs = self.diff_vdom(self.current_vdom, new_vdom)
            self.apply_diffs(diffs)
        else:
            self.render_vdom(new_vdom, self.content_frame)
        self.current_vdom = new_vdom

    def parse_html(self, html):
        # Parse HTML into a virtual DOM tree using BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        return self.build_vdom(soup)

    def build_vdom(self, soup_node):
        if isinstance(soup_node, str):
            content = soup_node.strip()
            return VNode("text", {"content": content}, []) if content else None
        
        if not hasattr(soup_node, "name") or soup_node.name in ["script", "style"]:
            return None

        # Handle special cases for form elements
        attrs = dict(soup_node.attrs)
        children = []
        
        # Process children recursively
        for child in soup_node.children:
            child_vdom = self.build_vdom(child)
            if child_vdom:
                children.append(child_vdom)

        # Special handling for form structure
        if soup_node.name == "form":
            return VNode("form", attrs, children)
        
        return VNode(soup_node.name, attrs, children)

    def diff_vdom(self, old_node, new_node):
        diffs = []
        if old_node.tag != new_node.tag or old_node.key != new_node.key:
            # Node type/key changed → replace
            diffs.append(("replace", old_node, new_node))
        else:
            # Check for attribute changes
            attr_diff = {}
            for key in set(old_node.attrs) | set(new_node.attrs):
                old_val = old_node.attrs.get(key)
                new_val = new_node.attrs.get(key)
                if old_val != new_val:
                    attr_diff[key] = new_val
            if attr_diff:
                diffs.append(("attrs", old_node, attr_diff))
            
            # Diff children (include index)
            max_children = max(len(old_node.children), len(new_node.children))
            for i in range(max_children):
                old_child = old_node.children[i] if i < len(old_node.children) else None
                new_child = new_node.children[i] if i < len(new_node.children) else None

                if not old_child and new_child:
                    # Add action: (parent, new_child, index)
                    diffs.append(("add", old_node, new_child, i))
                elif old_child and not new_child:
                    # Remove action: (parent, old_child, index)
                    diffs.append(("remove", old_node, old_child, i))
                elif old_child and new_child:
                    diffs.extend(self.diff_vdom(old_child, new_child))
        return diffs

    def render_vdom(self, vdom, parent):
        try:

            if vdom.tag == "text":
                content = vdom.attrs.get("content", "")
                widget = tk.Label(parent, text=content)
                widget.pack(anchor="w")
                self.widget_map[vdom] = widget

            elif vdom.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                sizes = {"h1": 24, "h2": 20, "h3": 18, "h4": 16, "h5": 14, "h6": 12}
                font_size = sizes.get(vdom.tag, 12)
                widget = tk.Label(
                    parent,
                    text="".join(child.attrs.get("content", "") for child in vdom.children if child.tag == "text"),
                    font=("Arial", font_size, "bold"),
                    bg="white",
                    anchor="w",
                    justify="left",
                    wraplength=700
                )
                widget.pack(anchor="w", pady=(10, 5))
                self.widget_map[vdom] = widget

            elif vdom.tag == "form":
                form_frame = tk.Frame(parent, bg="white")
                form_frame.pack(fill=tk.X, padx=5, pady=10)
                self.widget_map[vdom] = form_frame
                
                # Store form metadata
                form_data = {
                    "action": vdom.attrs.get("action", ""),
                    "method": vdom.attrs.get("method", "get").upper(),
                    "inputs": {}
                }
                
                # Add hidden attribute to track form state
                form_frame.form_data = form_data
                
                for child in vdom.children:
                    self.render_vdom(child, form_frame)

            elif vdom.tag == "input":
                input_type = vdom.attrs.get("type", "text")
                parent_form = self.find_parent_form(parent)
                
                if input_type == "submit":
                    widget = tk.Button(
                        parent,
                        text=vdom.attrs.get("value", "Submit"),
                        command=lambda f=parent_form: self.handle_form_submit(f)
                    )
                    widget.pack(pady=5)
                else:
                    frame = tk.Frame(parent, bg="white")
                    frame.pack(fill=tk.X, pady=2)
                    
                    label_text = vdom.attrs.get("placeholder", "")
                    if label_text:
                        tk.Label(frame, text=label_text, bg="white").pack(side=tk.LEFT, padx=5)
                    
                    entry = tk.Entry(frame)
                    entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
                    
                    # Store input reference in form data
                    if parent_form:
                        input_name = vdom.attrs.get("name", f"input_{id(entry)}")
                        parent_form.form_data["inputs"][input_name] = entry
                    
                    widget = entry

                self.widget_map[vdom] = widget
            elif vdom.tag == "button":
                widget = tk.Button(
                    parent,
                    text=vdom.attrs.get("content", ""),
                    command=lambda: self.handle_event(vdom.attrs.get("onclick")),
                )
                widget.pack(pady=5)
                self.widget_map[vdom] = widget

            elif vdom.tag == "a":
                url = vdom.attrs.get("href", "#")
                text = ""
                for child in vdom.children:
                    if child.tag == "text":
                        text += child.attrs.get("content", "")
                widget = tk.Label(parent, text=text, fg="blue", cursor="hand2", underline=True)
                widget.pack(anchor="w")
                widget.bind("<Button-1>", lambda e, link=url: self.load_link(link))
                self.widget_map[vdom] = widget
                
            else:
                # Generic container for unknown tags
                frame = tk.Frame(parent)
                frame.pack(fill=tk.X, padx=5, pady=5)
                self.widget_map[vdom] = frame
                for child in vdom.children:
                    self.render_vdom(child, frame)

        except Exception as e:
            print(f"Rendering error for VNode {vdom}: {str(e)}")
            raise
    
    def find_parent_form(self, widget):
        while widget:
            if hasattr(widget, 'form_data'):
                return widget
            widget = widget.master
        return None

    def handle_form_submit(self, form_widget):
        form_data = form_widget.form_data
        data = {}

        for name, entry in form_data["inputs"].items():
            data[name] = entry.get()

        # Resolve relative action URL
        current_url = self.url_entry.get()
        action_url = form_data["action"]
        if not action_url:
            action_url = current_url
        else:
            action_url = urllib.parse.urljoin(current_url, action_url)

        try:
            if form_data["method"] == "GET":
                response = requests.get(action_url, params=data)
            else:
                response = requests.post(action_url, data=data)

            if response.status_code == 200:
                self.url_entry.delete(0, tk.END)
                self.url_entry.insert(0, response.url)
                self.update_dom(response.text)

        except Exception as e:
            error_label = tk.Label(self.content_frame, text=f"Form Error: {str(e)}", fg="red")
            error_label.pack(pady=10)

    def apply_diffs(self, diffs):
        for diff in diffs:
            action, *payload = diff  # Unpack dynamically
            if action == "replace":
                old_node, new_node = payload
                old_widget = self.widget_map.pop(old_node)
                old_widget.destroy()
                self.render_vdom(new_node, old_widget.master)
            elif action == "attrs":
                old_node, attr_diff = payload
                widget = self.widget_map.get(old_node)
                if widget:
                    for key, value in attr_diff.items():
                        if key == "content":
                            widget.config(text=value)
            elif action == "add":
                parent_node, new_child, index = payload
                parent_widget = self.widget_map.get(parent_node)
                if parent_widget:
                    self.render_vdom(new_child, parent_widget)
            elif action == "remove":
                parent_node, old_child, index = payload
                widget = self.widget_map.pop(old_child, None)
                if widget:
                    widget.destroy()
                    self._clean_widget_map(old_child)
                    
    def _clean_widget_map(self, node):
        """Recursively remove all children of a node from widget_map"""
        for child in node.children:
            if child in self.widget_map:
                self.widget_map.pop(child)
                self._clean_widget_map(child)

    def handle_event(self, script_name):
        if script_name in self.script_functions:
            self.script_functions[script_name]()

    def register_script(self, name, func):
        self.script_functions[name] = func

    def fetch_and_parse(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # Use final URL after redirects
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, response.url)
            return self.parse_html(response.text)
        except Exception as e:
            raise Exception(f"Failed to fetch {url}: {str(e)}") 
        
    def _on_mousewheel(self, event):
        # Windows and macOS
        if event.num == 4 or event.delta > 0:
            self.content_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or event.delta < 0:
            self.content_canvas.yview_scroll(1, "units")

    def _on_arrow(self, event):
        if event.keysym == "Up":
            self.content_canvas.yview_scroll(-1, "units")
        elif event.keysym == "Down":
            self.content_canvas.yview_scroll(1, "units")

# Example usage:
def on_button_click():
    print("Button clicked!")

if __name__ == "__main__":
    # Create a browser with default root window
    browser = SimpleBrowser()
    browser.register_script("onButtonClick", on_button_click)
    browser.parent.mainloop()