import os
from tkinter import filedialog

import matplotlib.pyplot as plt
import numpy as np
from tkinter import *
from threading import Thread

from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

from PIL import Image, ImageTk
from itertools import count, cycle


class ImageLabel(Label):
    """
    A Label that displays images, and plays them if they are gifs
    :im: A PIL Image instance or a string filename
    """

    def load(self, im):
        if isinstance(im, str):
            im = Image.open(im)
        frames = []

        try:
            for i in count(1):
                frames.append(ImageTk.PhotoImage(im.copy()))
                im.seek(i)
        except EOFError:
            pass
        self.frames = cycle(frames)

        try:
            self.delay = im.info['duration']
        except:
            self.delay = 100

        if len(frames) == 1:
            self.config(image=next(self.frames))
        else:
            self.next_frame()

    def unload(self):
        self.config(image=None)
        self.frames = None

    def next_frame(self):
        if self.frames:
            self.config(image=next(self.frames))
            self.after(self.delay, self.next_frame)


r = Tk()
r.geometry("900x500")
input_frame = Frame(r)
input_frame.pack()
output_frame = Frame(r)
output_frame.pack(side=BOTTOM)
r.title('MolAromaProjection')
waitGif = ImageLabel(r)
entry = Entry(input_frame)
# dictionary of diverse value

colorMol = {"C": "black", "H": "grey"}
sizeMol = {"C": 0.2, "H": 0.1}  # test // todo : ask if it's fine to do that. Also maybe let the user change the values
colorAroma = {0: (1, 0.898, 0.8), 1: (0.984, 0.984, 0.992), 2: (0.906, 0.906, 0.953), 3: (0.831, 0.831, 0.914),
              4: (0.753, 0.753, 0.875)}

timer_id = None


def interface_generate():
    # Creating the GUI

    Label(input_frame, text='emplacement du fichier à parser : ').grid(row=0, column=0)
    entry.grid(row=0, column=1)
    button_file = Button(input_frame,
                         text="Chercher le fichier",
                         command=browse_files)
    button_file.grid(row=0, column=2)
    button = Button(r, text='Parser', width=25,
                    command=lambda: Thread(target=interface_create_projection, args=(entry.get(),)).start())

    button.pack()
    waitGif.pack()

    r.mainloop()


def interface_create_projection(filename):
    waitGif.load("ressources/loading.gif")

    for child in output_frame.winfo_children():
        child.destroy()

    graph_frame = Frame(output_frame)

    canvas = FigureCanvasTkAgg(create_projection(filename), master=graph_frame)
    canvas.draw()
    # placing the canvas on the Tkinter window
    canvas.get_tk_widget().pack()

    # creating the Matplotlib toolbar
    toolbar = NavigationToolbar2Tk(canvas, graph_frame)
    toolbar.children['!button4'].pack_forget()
    toolbar.update()

    # placing the toolbar on the Tkinter window
    canvas.get_tk_widget().pack()

    graph_frame.pack()

    waitGif.unload()


def no_GUI_create_projection():
    #filename_to_parse = input("emplacement du fichier à parser : \n")# // todo: uncomment that
    filename_to_parse = "ressources/test.txt"  # //todo : comment that
    while not os.path.isfile(filename_to_parse):
        filename_to_parse = input("chemin incorrect ou incomplet. veuillez re-essayer : \n")
    create_projection(filename_to_parse).show()


def create_projection(filename):
    """Create a 2D projection of a molecule and it's aromaticity.
    :param filename: Location of a file that contain the data of the molecule (use the example in ressources for reference)
    """
    try:
        file = open(filename, "r")
    except:
        return

    fig, ax = plt.subplots(1, 2, figsize=(10, 5), dpi=80)
    ax[0].set_aspect('equal', adjustable='box')
    ax[1].set_aspect('equal', adjustable='box')

    # //todo : maybe put everything in a class and do the file reading in the constructor. (would need to send ax)
    list_mol = []
    list_aroma = []
    origin_x = None
    origin_y = None
    origin_z = None
    incr_aroma_x = 0
    incr_aroma_y = 0

    increment_value_x = 1  # size of each increment on the graph // todo : let the user change it
    increment_value_y = 0.5  # size of each increment on the graph // todo : let the user change it

    # DO NOT DELETE
    # size = 0.1  # size of the molecule circle
    # DO NOT DELETE

    max_y = 0
    max_x = 0

    # read the file to parse to find the data. //todo: check if the file is properly formatted and stop parsing if not.
    for line in file.readlines():

        cur_line = line.split()
        #print(cur_line)  # not needed // todo : remove at the end

        if len(cur_line) == 0:  # no word on the line => blank line separating aromaticity
            if origin_x is not None:
                list_aroma.append([])

        elif cur_line[0] == "origine":  # if the first word is "origine" => origin value
            origin_x = -float(cur_line[1])  # inelegant reverse origin
            origin_y = -float(cur_line[2])  # inelegant reverse origin
            origin_z = -float(cur_line[3])  # inelegant reverse origin

        elif len(cur_line) == 1:  # only one "word" => aromaticity value
            list_aroma[-1].append(float(cur_line[0]))

            color_aroma = get_aromaticity_color(float(cur_line[0]))

            patch = plt.Circle(
                ((len(list_aroma) - 1) * incr_aroma_x, -1 * (len(list_aroma[-1]) * incr_aroma_y - max_y)),
                0.1, facecolor=color_aroma)  # todo : fix the hardcoded size (should be added to the dictionary)
            # (len(list_aroma)-1) => minus 1 evil trick, but it saves a bit of time
            ax[1].add_patch(patch)

        elif cur_line[0] == "V1":  # if first word V1 => get the space between each aromaticity on x
            incr_aroma_x = float(cur_line[1])
            max_x = float(cur_line[4]) * incr_aroma_x

        elif cur_line[0] == "V2":  # if first word V2 => get the space between each aromaticity on y
            incr_aroma_y = float(cur_line[2])
            max_y = float(cur_line[4]) * incr_aroma_y

            ax[0].set_ylim(ax[0].get_ylim()[::-1])  # invert the axis
            ax[0].xaxis.tick_top()  # and move the X-Axis
            ax[0].xaxis.set_ticks(np.arange(0, max_x + increment_value_x, increment_value_x))  # set x-ticks
            ax[0].yaxis.set_ticks(np.arange(0, max_y + increment_value_y, increment_value_y))  # set y-ticks
            ax[0].yaxis.tick_left()  # move the Y-Axis

            # bis for the second graph
            ax[1].set_ylim(ax[1].get_ylim()[::-1])
            ax[1].xaxis.tick_top()
            ax[1].xaxis.set_ticks(np.arange(0, max_x + increment_value_x, increment_value_x))
            ax[1].yaxis.set_ticks(np.arange(0, max_y + increment_value_y, increment_value_y))
            ax[1].yaxis.tick_left()

        else:  # last option is always a molecule
            list_mol.append(cur_line)

    file.close()

    # todo : optimize those two loops below to avoid duplicate code and save time
    for i in range(round(1 / incr_aroma_x * increment_value_x)):
        for j in range(round(max_y / incr_aroma_y)):
            patch = plt.Circle((max_x + incr_aroma_x * i, incr_aroma_y * j), 0.1, facecolor=colorAroma[0])
            ax[1].add_patch(patch)

    for i in range(round(max_x / incr_aroma_x)):
        for j in range(round(1 / incr_aroma_y * increment_value_y)):
            patch = plt.Circle((incr_aroma_x * i, max_y + incr_aroma_y * j), 0.1, facecolor=colorAroma[0])
            ax[1].add_patch(patch)

    for mol in list_mol:  # //todo : check if there's a way to do it in the first loop, would cut some of the processing time.

        cur_color = colorMol[mol[0]]  # chose the molecule color using dictionary

        # no idea how to do that in once instead of twice
        patch1 = plt.Circle((float(mol[1]) + origin_x, -1 * (float(mol[2]) + origin_y - max_y)),
                            sizeMol[mol[0]], facecolor=cur_color)
        patch2 = plt.Circle((float(mol[1]) + origin_x, -1 * (float(mol[2]) + origin_y - max_y)),
                            sizeMol[mol[0]], facecolor=cur_color)

        ax[0].add_patch(patch1)
        ax[1].add_patch(patch2)

    # ax[0].imshow(sign)

    #  filename_to_save = input("nommer le fichier de sauvegarde (appuyez sur entrée pour ne pas faire de sauvegarde) : \n") //todo : uncomment that
    #  filename_to_save = "essai.png"  # //todo : comment that

    # plt.show()  # show delete the graph after usage. ALWAYS AT THE END.

    return fig


def get_aromaticity_color(aromaticity_value):
    """
    Returns a color depending on the aromaticity
    :param aromaticity_value: Value of the aromaticity of a point in the graph
    :return: A RGB value (x,y,z) based on the dictionary for that range of aromaticity where x, y and z are between 0 and 1
    """
    if aromaticity_value < 0:
        return colorAroma[0]
    elif aromaticity_value < 5:
        return colorAroma[1]
    elif aromaticity_value < 10:
        return colorAroma[2]
    elif aromaticity_value < 15:
        return colorAroma[3]
    else:
        return colorAroma[4]


def browse_files():
    filename = filedialog.askopenfilename(initialdir="./",
                                          title="Choisir le fichier a parser",
                                          filetypes=(("Text files",
                                                      "*.txt*"),
                                                     ("all files",
                                                      "*.*")))

    # Change label contents
    entry.delete(0, END)
    entry.insert(0, filename)


if __name__ == '__main__':
    # filename_to_parse = input("emplacement du fichier à parser : \n")  //todo : uncomment that
    # filename_to_parse = "ressources/test.txt"  # //todo : comment that
    # while not os.path.isfile(filename_to_parse):
    #    filename_to_parse = input("chemin incorrect ou incomplet. veuillez re-essayer : \n")
    # create_projection(filename_to_parse)
    interface_generate()
