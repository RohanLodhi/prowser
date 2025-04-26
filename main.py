from browser import SimpleBrowser

def on_button_click():
    print("Button clicked!")

if __name__ == "__main__":
    browser = SimpleBrowser()
    browser.register_script("onButtonClick", on_button_click)
    browser.parent.mainloop()