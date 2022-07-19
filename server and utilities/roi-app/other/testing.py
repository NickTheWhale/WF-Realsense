"""A program to help manage the levels of player characters in Elder Scolls: Oblivion"""

from tkinter import *
from tkinter import ttk

# Create root and set the title
root = Tk()
root.title("PyBlivion Level Manager")

# top level frame
mainframe = ttk.Frame(root)
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

# Character name
ttk.Label(mainframe, text="Character name:").grid(column=1, row=1)
ttk.Entry(mainframe).grid(column=2, row=1, sticky=E)

# Attributes
ttk.Label(mainframe, text="Attributes").grid(column=1, row=2, sticky=W)
attributes = ["Strenth", "Intelligence", "Willpower", "Agility", "Speed", "Endurance", "Luck"]
for pos, attr in enumerate(attributes):
    ttk.Label(mainframe, text=attr).grid(column=1, row=pos+3, sticky=W)
for pos, attr in enumerate(attributes):
    Spinbox(mainframe).grid(column=2, row=pos+3, stick=W)

# Skills
ttk.Label(mainframe, text="Skills").grid(column=1, row=10, sticky=W)
skills = ["Alteration", "Destruction", "Illusion", "Mysticism", "Restoration", "Security", "Sneak", "Armorer", "Athletics", "Blade", "Block", "Blunt", "Hand to Hand", "Heavy Armor", "Alchemy", "Conjuration", "Acrobatics", "Light Armor", "Marksman", "Mercantile", "Speechcraft"]
for pos, name in enumerate(skills):
    ttk.Label(mainframe, text=name).grid(column=1, row=pos+11, sticky=W)
for pos, name in enumerate(skills):
    Spinbox(mainframe).grid(column=2, row=pos+11, sticky=W)

root.mainloop()