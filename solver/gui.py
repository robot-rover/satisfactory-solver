import tkinter as tk

window = tk.Tk()

input_frame = tk.Frame(master=window, width=200, height=100, bg="red")
input_frame.pack(fill=tk.Y, side=tk.LEFT, expand=True)

main_frame = tk.Frame(master=window, width=200, height=100, bg="blue")
main_frame.pack(fill=tk.BOTH, side=tk.LEFT, expand=True)

input_frame = tk.Frame(master=window, width=200, height=100, bg="green")
input_frame.pack(fill=tk.Y, side=tk.LEFT, expand=True)

window.mainloop()
