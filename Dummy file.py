import tkinter.font
import tkinter

window = tkinter.Tk()
font1 = tkinter.font.Font(family="Times", size=16)
font2 = tkinter.font.Font(family="Times", size=16, slant='italic')
canvas = tkinter.Canvas(
            window,
            width=800,
            height=300
)
x, y = 200, 225
canvas.create_text(x, y, text="Hello, ", font=font1, anchor='nw')
x += font1.measure("Hello, ")
canvas.create_text(x, y, text="overlapping!", font=font2, anchor='nw')
canvas.pack()
window.mainloop()
