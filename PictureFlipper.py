

import pyautogui
import time
import datetime
import threading
from threading import Event, Thread
from pynput import mouse
import warnings
import numpy as np
import easygui
import keyboard
import cv2
import tkinter as tk
from tkinter import BOTH, END, LEFT, RIGHT, NORMAL, DISABLED, W, E, N, S
from tkinter.simpledialog import askstring, askinteger
from tkinter.messagebox import showerror
from tkinter import filedialog
import os
import re
import shutil
import screeninfo
from PIL import Image, ImageChops
import math, operator
import imagehash
import pandas as pd

def defaultThread(interval, func, *args):
    stopped = Event()
    def loop():
       while not stopped.wait(interval): 
            func(*args)
    Thread(target=loop, daemon=True).start()    
    return stopped.set

def focus_next_widget(event):
    event.widget.tk_focusNext().focus()
    return("break")

def call_findFolder(event):
    findFolder()
    

    
def call_showPrevImage(event):
    showPrevImage()
    
def call_deleteFile(event):
    deleteFile()
    
def call_addFile(event):
    addFile()

def showNextImage():
    global q
    path = flist[q]
    
    img = cv2.imread(path,
                     cv2.IMREAD_UNCHANGED)
    makewindow(img)
    updatefpathq()
    master.lift()
    master.focus_force()

def showPrevImage():
    global q
    if q > 0:
        q-=1
        path = flist[q]
        img = cv2.imread(path,
                         cv2.IMREAD_UNCHANGED)
        makewindow(img)
        updatefpathq()
        master.lift()
        master.focus_force()

def refreshCurrentImage():
    global q
    path = flist[q]
    img = cv2.imread(path,
                     cv2.IMREAD_UNCHANGED)
    makewindow(img)
    updatefpathq()
    master.lift()
    master.focus_force()

def makewindow(img):
    try:
        screen_id = 0
        screen = screeninfo.get_monitors()[screen_id]
        scale_width = screen.width / img.shape[1]
        scale_height = screen.height / img.shape[0]
        scale = min(scale_width, scale_height)
        window_width = int(img.shape[1] * scale)
        window_height = int(img.shape[0] * scale)
        cv2.namedWindow('Resized Window', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Resized Window', window_width, window_height)
        cv2.imshow('Resized Window', img)
    except:
        global q
        flist.remove(flist[q])
        path = flist[q]
        img = cv2.imread(path,
                         cv2.IMREAD_UNCHANGED)
        makewindow(img)
    
def updatefpathq():
    global q
    fpath_queue.config(state=NORMAL)
    fpath_queue.delete(1.0, END)
    if len(flist)-1 != 0:
        fpath_queue.insert(END, str(q) + "/" + str(len(flist)-1))
    else:
        fpath_queue.insert(END, "0/0")
    fpath_queue.config(state=DISABLED)
    fpath_curr.config(state=NORMAL)
    fpath_curr.delete(1.0, END)
    try:
        fpath_curr.insert(END, str(flist[q]))
    except:
        fpath_curr.insert(END, "Out of files...")
    fpath_curr.config(state=DISABLED)

def findFolder():
    global folder_selected
    folder_selected = filedialog.askdirectory()
    if folder_selected != "":
        fpath_str.set(folder_selected)
        fpath_text.config(state=NORMAL)
        fpath_text.delete(1.0, END)
        fpath_text.insert(END, folder_selected)
        fpath_text.config(state=DISABLED)
        getFolderStats(folder_selected)

def deleteFile():
    global q
    fname = os.path.basename(flist[q])
    if "/add/" in flist[q]:
        shutil.move(flist[q], folder_selected + "/del/" + fname)
    else:
        shutil.copy(flist[q], folder_selected + "/del/" + fname)
    flist[q] = folder_selected + "/del/" + fname
    updatefpathq()
    refreshCurrentImage()

def addFile():
    global q
    try:
        fname = os.path.basename(flist[q])
        shutil.copy(flist[q], folder_selected + "/add/" + fname)
        flist[q] = str(folder_selected + "/add/" + fname)
        incrementq()
        updatefpathq()
    except:
        print("Already in Add or Failed")
        incrementq()
        updatefpathq()
    
def incrementq():
    global q
    if int(skipamt.get())>0:
        n = int(skipamt.get())
    else: n = 1
    if q < len(flist)-1:
        q += n
        showNextImage()

def autoNextTask():
    if toggleswitch.get() == "on":
        incrementq()
    try:
        master.after(int(float(autotimer.get())*1000), autoNextTask)
    except:
        print("Bad number, defaulting to 1 second")
        master.after(1000, autoNextTask)

def call_autoOn(event):
    toggleswitch.set("on")

def call_autoOff(event):
    toggleswitch.set("off")

def call_killimg(event):
    cv2.destroyAllWindows()
    toggleswitch.set("off")
    master.lift()
    master.focus_force()

def getFolderStats(path):
    global flist
    global hlist
    flist = []
    hlist = []
    accepted = ("jpeg","png","jpg","gif","bmp","tif","tiff","raw")
    for (dirpath, dirnames, filenames) in os.walk(path):
        for file in filenames:
            if file[-3:] in accepted and \
            "\\add\\" not in os.path.join(dirpath, file) \
            and \
            "\\del\\" not in os.path.join(dirpath, file):
                flist.append(os.path.join(dirpath, file))
    try:
        os.mkdir(folder_selected + "/add")
        os.mkdir(folder_selected + "/del")
    except: pass
    flist.sort()
    updatefpathq()
    showNextImage()

def call_showNextImage(event):
    showNextImage()

def call_incrementq(event):
    incrementq()

    #should be some kind of optional checkbox
    checkhashes()
    
def genhashes():
    global df
    ###wonder if dhash is the best for this now
    global hlist
    cv2.destroyAllWindows()
    for img in flist:
        try:
            hlist.append(imagehash.dhash(Image.open(img)))
        except: pass

    df = pd.DataFrame(np.column_stack([flist, hlist]),
                      columns=['path','hash'])
    df.to_csv("data.csv", index=False)
    hashes_button.configure(text="Check\nHashes", command=checkhashes)
    master.bind("<Delete>", call_checkhashes)
    print("Hashes Generated")
    master.lift()
    master.focus_force()

def call_checkhashes(event):
    checkhashes()
    
def checkhashes():
    global dupelist
    global dupeiterator
    global temptk
    global df
    dupeiterator = 0
    dupelist = []
    found = 0
    
    hlist = df['hash'].tolist()
    for i in range(len(df)):
        if df.loc[q, 'path'] != df.loc[i, 'path'] and \
        df.loc[q, 'hash'] == df.loc[i, 'hash']:
            df.loc[i, 'x'] = "X"
            found=1
    if found == 1:
        dupelist = df.loc[df['x'] == "X"]
        print(dupelist)
        print("Found:" + str(len(dupelist)))
        cv2.destroyAllWindows()
        temptk = tk.Tk()
        w = 200 
        h = 300 
        ws = temptk.winfo_screenwidth()
        hs = temptk.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        temptk.geometry('%dx%d+%d+%d' % (w, h, x, y))
        temptk.title("Dupe Handler")       
        autoLabel = tk.Label(temptk, text="Add or Delete")
        sourcefile = tk.Button(temptk, text="Move Source", command=moveSrcFile)
        sourcefile.grid(row=0, column=0, sticky=N+W+E+S,pady=10)
        dupefile = tk.Button(temptk, text="Move Dupe", command=moveDupFile)
        dupefile.grid(row=1, column=0, sticky=N+W+E+S,pady=10)
        moveon = tk.Button(temptk, text="Next", command=leaveFile)
        temptk.bind("<Insert>", call_leaveit)
        moveon.grid(row=2, column=0, sticky=N+W+E+S,pady=10)

        popupDupe(cv2.imread(flist[q],
                         cv2.IMREAD_UNCHANGED),
                  "Source",0)
        popupDupe(cv2.imread(df.iloc[dupelist.iloc[[dupeiterator]].index.item(),:]['path'],
                         cv2.IMREAD_UNCHANGED),
                  "Dupe?",1)

        temptk.lift()
        temptk.focus_force()
    else: print("No dupes found.")

def call_leaveit(event):
    leaveFile()

def moveSrcFile():
    global df
    print("MOVING: " + str(flist[q]))
    moveFile(df.iloc[[q]]['path'])
    df.drop([q], 0, inplace=True)

def moveDupFile():
    global df
    print("MOVING: " + str(df.iloc[dupelist.iloc[[dupeiterator]].index.item(),:]['path']))
    moveFile(df.iloc[dupelist.iloc[[dupeiterator]].index.item(),:]['path'])
    df.drop([dupelist.iloc[[dupeiterator]].index.item()], 0, inplace=True)


def moveFile(path):
    global temptk
    global dupeiterator
    print("Moving: " + str(path))
    fname = os.path.basename(path)
    shutil.move(path, folder_selected + "/del/" + fname)
    dupeiterator+=1
    if dupeiterator<len(dupelist):    
        popupDupe(cv2.imread(df.iloc[dupelist.iloc[[dupeiterator]].index.item(),:]['path'],
                         cv2.IMREAD_UNCHANGED),
                  "Dupe?",1)
    else:
        del df['x']
        temptk.destroy()
        cv2.destroyAllWindows()
        incrementq()
        master.focus_force()
   
def leaveFile():
    global temptk
    global dupeiterator
    dupeiterator+=1
    if dupeiterator<len(dupelist):
        popupDupe(cv2.imread(df.iloc[dupelist.iloc[[dupeiterator]].index.item(),:]['path'],
                         cv2.IMREAD_UNCHANGED),
                  "Dupe?",1)
    else:
        del df['x']
        temptk.destroy()
        cv2.destroyAllWindows()
        incrementq()
        master.focus_force()

def popupDupe(img, name, scrn):
    screen_id = scrn
    screen = screeninfo.get_monitors()[screen_id]
    scale_width = screen.width / img.shape[1]
    scale_height = screen.height / img.shape[0]
    scale = min(scale_width, scale_height)
    window_width = int(img.shape[1] * scale)
    window_height = int(img.shape[0] * scale)
    cv2.namedWindow(str(name), cv2.WINDOW_NORMAL)
    cv2.resizeWindow(str(name), window_width, window_height)
    cv2.imshow(str(name), img)

        
global flist
global hlist
global q
global df
flist = []
q = 0
master = tk.Tk()
master.title("Picture Sorter")

try:
    df = pd.read_csv("data.csv")
    hlist = df['hash'].tolist()
    print("Hash table found!")
except:
    df = pd.DataFrame()
    print("No hash table found.")

fpath_str = tk.StringVar(master)
folder = tk.Button(master, text="Select\nFolder", command=findFolder)

fp_label1 = tk.Label(master, text="Folder Path:")
fpath_text = tk.Text(master, height=1, width=30, bg='lightgrey', relief='flat')
fpath_text.insert(END, "Waiting....")
fpath_text.config(width=30,state=DISABLED) 

fp_label2 = tk.Label(master, text="Queue:")
fpath_queue = tk.Text(master, height=1, width=20, bg='lightgrey', relief='flat')
fpath_queue.insert(END, "Waiting....")
fpath_queue.config(width=20,state=DISABLED)

fp_label1.grid(row=0,column=1, sticky=N+W)
fp_label2.grid(row=0,column=2, sticky=N+W)
fpath_queue.grid(row=1,column=2)
fpath_text.grid(row=1,column=1)
folder.grid(row=1, column=0)
master.bind("/", call_findFolder)

fp_label3 = tk.Label(master, text="File:")
fpath_curr = tk.Text(master, height=5, width=50, bg='lightgrey', relief='flat')
fpath_curr.insert(END, "Waiting....")
fpath_curr.config(width=50,state=DISABLED)
fp_label3.grid(row=2, column=0)
fpath_curr.grid(row=2, column=1,columnspan=2)

shownimg = tk.Button(master, text="Next", command=incrementq)
shownimg.grid(row=3, column=0, sticky=N+W,pady=10)
master.bind("<Right>", call_incrementq)

showpimg = tk.Button(master, text="Prev", command=showPrevImage)
showpimg.grid(row=3, column=1, sticky=N+W,pady=10)
master.bind("<Left>", call_showPrevImage)

skipamt = tk.StringVar(master)
skipamt.set("0")
skipent = tk.Entry(master, textvariable=skipamt)
skipent.grid(row=4, column=2, sticky=N+W)
skiplabel = tk.Label(master, text="Skip Amt #:")
skiplabel.grid(row=3, column=2, sticky=N+W)

deletefile = tk.Button(master, text="Delete", command=deleteFile)
deletefile.grid(row=4, column=0, sticky=N+W,pady=10)
master.bind("-", call_deleteFile)

addfile = tk.Button(master, text="Add", command=addFile)
addfile.grid(row=4, column=1, sticky=N+W,pady=10)
master.bind("+", call_addFile)

autoLabel = tk.Label(master, text="AutoNext")
toggleswitch = tk.StringVar(value="off")
plus_button = tk.Radiobutton(master, text="On", variable=toggleswitch,
                            indicatoron=False, value="on", width=8)
minus_button = tk.Radiobutton(master, text="Off", variable=toggleswitch,
                              indicatoron=False, value="off", width=8)

master.bind("/", call_autoOn)
master.bind("*", call_autoOff)

autoLabel2 = tk.Label(master, text="AutoNext Timer (.1 Sec tolerance)")
autotimer = tk.StringVar(value="1")
autotimerent = tk.Entry(master, textvariable=autotimer)

autoLabel.grid(row=5, column=0, columnspan=2, sticky=N+W)
plus_button.grid(row=6, column=0, sticky=N+W)
minus_button.grid(row=6, column=1, sticky=N+W)
autoLabel2.grid(row=5, column=2, columnspan=1, sticky=N+W)
autotimerent.grid(row=6, column=2, sticky=N+W)
autoNextTask()

if df.empty:
    hashes_button = tk.Button(master, text="Generate\nHashes", command=genhashes)
    hashes_button.grid(row=6, column=1, sticky=N+E+S)
else:
    hashes_button = tk.Button(master, text="Check\nHashes", command=checkhashes)
    hashes_button.grid(row=6, column=1, sticky=N+E+S)
    master.bind("<Delete>", call_checkhashes)
    
master.bind("<Insert>", call_killimg)

tk.mainloop()















    
