import tkinter as tk
from tkinter import ttk
from fuzzywuzzy import process

from . import game_parse

# https://stackoverflow.com/questions/59119896/tkinter-ttk-combobox-dropdown-expand-and-focus-on-text

def main():
    recipes, items = game_parse.get_docs()
    item_lookup = { item.display: item for item in items.values() }

    window = tk.Tk()
    window.minsize(800, 600)
    window.unbind_all("<<NextWindow>>")

    input_frame = tk.Frame(master=window, width=200, height=100, bg="red")
    input_frame.pack(fill=tk.BOTH, side=tk.LEFT)

    def update_search(w, sv):
        w.event_generate("<Down>")
        term = sv.get()
        print("Update", term)
        l = process.extractBests(term, item_lookup, limit=20)
        l = list(l)
        values = [
            t[2] for t in l
        ]
        w.configure(values=values)


    def finish_search(e):
        term = e.widget.get()
        print("Finish", term)

    def complete_search(e):
        term = e.widget.get()
        print("Complete", term)

    input_search_term = tk.StringVar()
    input_search = ttk.Combobox(master=input_frame, textvariable=input_search_term)
    input_search_term.trace_add("write", lambda *dc: update_search(input_search, input_search_term))
    input_search.pack()
    input_search.bind("<Return>", finish_search)
    input_search.bind("<Tab>", complete_search)
    # input_search.bind("<KeyRelease>", update_search)

    main_frame = tk.Frame(master=window, width=200, height=100, bg="blue")
    main_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

    input_frame = tk.Frame(master=window, width=200, height=100, bg="green")
    input_frame.pack(fill=tk.BOTH, side=tk.LEFT)

    window.mainloop()

if __name__ == "__main__":
    main()