import SudokuMaster
from SudokuMaster import *
import tkinter as tk
from tkinter import filedialog
import os

main=tk.Tk()
main.geometry("400x400")
frame=tk.Frame(grid,padx=20,pady=20)
frame.pack()

#Max difficulty to solve with
solveDiff=7

for i in range(dimsquared+dim-1):
    if not i%(dim+1)==dim:
        grid.append([])
    for j in range(dimsquared+dim-1):
        xpad=0
        if j%(dim+1)==dim or i%(dim+1)==dim:
            xpad=10
            a=tk.Frame(frame,width=8,height=6)
        else:
            a=tk.Entry(frame,width=3)
        a.grid(row=i,column=j,padx=0,sticky=tk.NE)#(10 if i%dim==0 else 0))
        if not (j%(dim+1)==dim or i%(dim+1)==dim):
            grid[-1].append(a)

def gui(x,y,val=None):
    box=grid[x][y]    
    old=box.get()
    if val!=None:
        box.delete(0,tk.END)
        box.insert(0,val)
    return old

def solveFunc(event=None):
    reset()
    global preSolveData
    nextSolveData=[[None]*dimsquared for i in range(dimsquared)]
    valData=[[None]*dimsquared for i in range(dimsquared)]
    for i in range(dimsquared):
        for j in range(dimsquared):
            val=gui(i,j)
            valnums=[]
            for k in range(dimsquared):
                for l in range(len(val)):
                    if val[l]==chars[k]:
                        valnums.append(k)
            valnums=arrayRemoveDuplicates(valnums)
            if len(valnums)==0:
                valData[i][j]=list(range(dimsquared))
            else:
                valData[i][j]=valnums
            if len(valnums)!=0:
                nextSolveData[i][j]=val
    preSolveData.append(nextSolveData)
    solved,contradiction,difficulty,squStrs = mainSolve(solveDiff,valData,True)    
    if solved:
        print("Diff: "+str(difficulty))
    if contradiction:
        print("Contradiction found!")
    for i in range(dimsquared):
        for j in range(dimsquared):
            gui(i,j,squStrs[i][j])
solve=tk.Button(main,text="Solve Me!")
solve.bind("<Button-1>",solveFunc)
solve.pack()

def unsolveFunc(event=None):
    global preSolveData
    if len(preSolveData)==0:
        return
    nextSolveData=preSolveData.pop()
    for i in range(dimsquared):
        for j in range(dimsquared):
            val=nextSolveData[i][j]
            gui(i,j,("" if val == None else val))
unsolve=tk.Button(main,text="Unsolve Me!")
unsolve.bind("<Button-1>",unsolveFunc)
unsolve.pack()

def resetFunc(event=None):
    reset()
    global preSolveData
    preSolveData=[]
    for i in range(dimsquared):
        for j in range(dimsquared):
            gui(i,j,"")
res=tk.Button(main,text="Reset Me!")
res.bind("<Button-1>",resetFunc)
res.pack()

#Generate a sudoku of the appropriate difficulty
def generateFunc(event=None):
    global preSolveData
    preSolveData=[]
    rowstrings=generateDiff(minGenDifficulty,maxGenDifficulty)
    loadFromString(rowstrings)
gen=tk.Button(main,text="Generate Sudoku!")
gen.bind("<Button-1>",generateFunc)
gen.pack()

#Save a sudoku to a file.
def saveFunc(event=None):
    try:
        filepath=filedialog.asksaveasfilename(initialdir=os.path.dirname(__file__)+"/Sudokus",title="Select file",filetypes=(("Text files","*.txt"),("All files","*.*")))
        if filepath=="":
            return
        file=open(filepath,"w")
    except:
        print("Invalid file path.")
        return
    savestring=""
    for i in range(dimsquared):
        rowstr=""
        for j in range(dimsquared):
            val=gui(i,j)
            valstr=""
            valint=-1
            for k in range(dimsquared):
                if val==chars[k]:
                    valint=k
            if valint==-1:
                valstr=" "
            else:
                valstr=val
            rowstr=rowstr+valstr
        if i!=dimsquared-1:
            rowstr=rowstr+"\n"
        savestring=savestring+rowstr
    try:
        file.write(savestring)
        file.close()
    except:
        print("An error occurred when saving the file.")
save=tk.Button(main,text="Save Sudoku!")
save.bind("<Button-1>",saveFunc)
save.pack()

#Load a sudoku from a string
def loadFromString(rowstrings):
    for i in range(dimsquared):
        rowstr=rowstrings[i]
        for j in range(dimsquared):
            if rowstr[j]==" ":
                gui(i,j,"")
            else:
                gui(i,j,rowstr[j])

#Load a sudoku from a file.
def loadFunc(event=None):
    try:
        filepath=filedialog.askopenfilename(initialdir=os.path.dirname(__file__)+"/Sudokus",title="Select file",filetypes=(("Text files","*.txt"),("All files","*.*")))
        if filepath=="":
            return
        file=open(filepath,"r")
    except:
        print("Invalid file path.")
        return
    try:
        rowstrings=file.readlines()
        file.close()
    except:
        print("An error occurred when loading the file.")
    global preSolveData
    preSolveData=[]
    loadFromString(rowstrings)
load=tk.Button(main,text="Load Sudoku!")
load.bind("<Button-1>",loadFunc)
load.pack()

tk.mainloop()
