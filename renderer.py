import tkinter as tk
from tkinter import ttk

class TkRenderer:
    def __init__(self, master, script_handler):
        self.master = master
        self.script_handler = script_handler
        self.widget_map = {}
        self.styles = {
            "h1": {"font": ("Arial", 24, "bold"), "pady": (15, 5)},
            "h2": {"font": ("Arial", 20, "bold"), "pady": (12, 4)},
            "h3": {"font": ("Arial", 16, "bold"), "pady": (10, 3)},
            "p": {"font": ("Arial", 12), "wraplength": 700},
            "input": {"font": ("Arial", 12), "width": 30}
        }
        
    def render(self, vnode, parent):
        if vnode.tag == "text":
            return self.create_text(vnode, parent)
        elif vnode.tag in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            return self.create_header(vnode, parent)
        elif vnode.tag == "a":
            return self.create_link(vnode, parent)
        elif vnode.tag == "input":
            return self.create_input(vnode, parent)
        elif vnode.tag == "form":
            return self.create_form(vnode, parent)
        else:
            return self.create_container(vnode, parent)

    def create_text(self, vnode, parent):
        widget = ttk.Label(parent, text=vnode.attrs.get("content", ""))
        widget.pack(anchor="w")
        return widget

    def create_header(self, vnode, parent):
        style = self.styles[vnode.tag]
        text = self.get_child_text(vnode)
        widget = ttk.Label(
            parent,
            text=text,
            font=style["font"],
            wraplength=700
        )
        widget.pack(anchor="w", pady=style["pady"])
        return widget

    def create_input(self, vnode, parent):
        input_type = vnode.attrs.get("type", "text")
        if input_type == "submit":
            widget = ttk.Button(
                parent,
                text=vnode.attrs.get("value", "Submit"),
                command=lambda: self.handle_form_submit(parent)
            )
        else:
            widget = ttk.Entry(
                parent,
                show="*" if input_type == "password" else None,
                **self.styles["input"]
            )
        widget.pack(pady=5)
        return widget

    def handle_form_submit(self, form_widget):
        # Collect form data
        inputs = {}
        for child in form_widget.winfo_children():
            if isinstance(child, ttk.Entry):
                inputs[child.widget_name] = child.get()
        self.script_handler("form_submitted", inputs)

    def create_link(self, vnode, parent):
        widget = ttk.Label(
            parent,
            text=self.get_child_text(vnode),
            style="Link.TLabel",
            cursor="hand2"
        )
        widget.bind("<Button-1>", lambda e: self.script_handler("navigate", vnode.attrs.get("href")))
        widget.pack(anchor="w")
        return widget

    def get_child_text(self, vnode):
        return "".join([
            child.attrs.get("content", "") 
            for child in vnode.children 
            if child.tag == "text"
        ])