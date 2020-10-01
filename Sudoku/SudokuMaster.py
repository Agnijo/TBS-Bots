import random
from random import randint
from datetime import datetime

dim=3#This is n for an n^2*n^2 sudoku, so 3 for 9*9 sudokus
dimsquared=dim*dim
grid=[]
candidates=True#Will candidates be shown?

#List of characters (up to 16)
chars=["1","2","3","4","5","6","7","8","9","0","A","B","C","D","E","F"]

#Max difficulty of all strategies
maxDiff=7

#Choose difficulty for generated sudoku
minGenDifficulty=5
maxGenDifficulty=7

class Group:
    def __init__(self):
        self.nums=[set(range(dimsquared))for i in range(dimsquared)]#Squares for each number
        self.squs=[]#Numbers for each square
        self.subgroups=[]
    def remove(self,square,number):
        index=self.squs.index(square)
        if index in self.nums[number]:
            self.nums[number].discard(index)
            return True
        return False
    def known(self,square,number):
        inp=False
        index=self.squs.index(square)
        if self.nums[number]!={index}:
            for i in self.squs:
                if i!=square:
                    i.remove(number)
            self.nums[number]={index}
            inp=True
        for i in range(dimsquared):
            if i!=number and index in self.nums[i]:
                self.nums[i].discard(index)
                inp=True
        return inp
    def basicSolve(self):
        inp=False
        for i in self.squs:
            if len(i.num)==1:
                inp=i.known(i.get()) or inp
            else:
                for j in range(dimsquared):
                    if j not in i.num:
                        inp=i.remove(j) or inp
        for ind,i in enumerate(self.nums):
            if len(i)==1:
                for j in i:
                    inp=self.squs[j].known(ind) or inp
        return inp
    def basicSubgroup(self):
        inp=False
        for i in range(dimsquared):
            for j in self.subgroups:
                if i in j.reqnums:#Is j required to contain i?
                    for k in self.squs:
                        if not(k in j.squs):
                            inp=k.remove(i) or inp
                else:
                    subgr=True#Do all squares containing i lie in subgroup j?
                    for k in self.squs:
                        if i in k.num and not(k in j.squs):
                            subgr=False
                    if subgr and not(i in j.reqnums):
                        j.reqnums.add(i)
                        inp=True
        return inp
    def basicLockedSet(self,numOfSquares,hidden):#Pairs,triples etc. Hidden is 1 for hidden pairs etc.
        inp=False
        numUnsolved=dimsquared
        for i in self.squs:
            if len(i.num)==1:
                numUnsolved-=1
        if numUnsolved>=(numOfSquares*2)+hidden:#If there are enough blank squares to make this analysis worthwhile
            if hidden==1:
                remList=lockedSetFinder(self.nums,numOfSquares)
            else:
                remList=lockedSetFinder([self.squs[i].num for i in range(dimsquared)],numOfSquares)
            if len(remList)!=0:
                if hidden==1:
                    for i in remList:
                        self.nums[i[0]].discard(i[1])
                        self.squs[i[1]].remove(i[0])
                else:
                    for i in remList:
                        self.nums[i[1]].discard(i[0])
                        self.squs[i[0]].remove(i[1])
                inp=True
        return inp

class Square:
    unid=0
    def __init__(self,row,col,box,subrow,subcol):
        self.num=set(range(dimsquared))
        row.squs.append(self)
        self.row=row
        col.squs.append(self)
        self.col=col
        box.squs.append(self)
        self.box=box
        subrow.squs.append(self)
        self.subrow=subrow
        subcol.squs.append(self)
        self.subcol=subcol
        self.unid=Square.unid
        Square.unid+=1
    def __eq__(self,other):
        return self.unid==other.unid
    def remove(self,number):
        inp=False
        if number in self.num:
            self.num.discard(number)
            inp=True
        inp=self.row.remove(self,number) or inp
        inp=self.col.remove(self,number) or inp
        inp=self.box.remove(self,number) or inp
        return inp
    def known(self,number):
        inp=False
        if self.num!={number}:
            self.num={number}
            inp=True
        inp=self.row.known(self,number) or inp
        inp=self.col.known(self,number) or inp
        inp=self.box.known(self,number) or inp
        return inp
    def get(self):
        for i in self.num:
            return i
    def __str__(self):
        if len(self.num)==1:
            for i in self.num:
                return chars[i]
        else:
            if candidates:#If candidates are shown
                candidatestring=""
                for i in self.num:
                    candidatestring=candidatestring+chars[i]
                return candidatestring
            else:
                return ""

class Subgroup:#A subgroup is a 1x3 or 3x1 rectangle formed by the intersection of a row/column and a box
    def __init__(self,rowcol,box):
        self.reqnums=set()#Numbers which must appear inside this subgroup - initially empty set
        self.squs=[]
        rowcol.subgroups.append(self)
        self.rowcol=rowcol
        box.subgroups.append(self)
        self.box=box

def lockedSetFinder(inputList,setLen):
    indList=[]#List of indices for members of numList that are unsolved and not too big
    removeList=[]#List of values in numList to delete
    for i in range(dimsquared):
        if len(inputList[i])!=1 and len(inputList[i])<=setLen:#Is i in inputList worth using?
            indList.append(i)
    indLen=len(indList)
    if indLen>=setLen:#Are there enough members worth using?
        lockedSet=set()#List of members of inputList in locked set
        for i in range(indLen+1-setLen):
            for j in range(indLen+1-setLen-i):
                jval=i+j+1
                lockedVal=inputList[indList[i]]|inputList[indList[jval]]#List of values in the possible locked set
                if setLen==2:
                    if len(lockedVal)==2:
                        for k in range(dimsquared):
                            if k!=indList[i] and k!=indList[jval]:
                                for l in range(dimsquared):
                                    if l in lockedVal and l in inputList[k]:
                                        removeList.append([k,l])
                else:
                    for k in range(indLen+1-setLen-i-j):
                        kval=i+j+k+2
                        lockedVal=inputList[indList[i]]|inputList[indList[jval]]|inputList[indList[kval]]
                        if setLen==3:
                            if len(lockedVal)==3:
                                for l in range(dimsquared):
                                    if l!=indList[i] and l!=indList[jval] and l!=indList[kval]:
                                        for m in range(dimsquared):
                                            if m in lockedVal and m in inputList[l]:
                                                removeList.append([l,m])
                        else:
                            for l in range(indLen-3-i-j-k):#setLen must be 4 (cannot yet deal with sets of 5 or more, and those are useless for 9*9 sudokus)
                                lval=i+j+k+l+3
                                lockedVal=inputList[indList[i]]|inputList[indList[jval]]|inputList[indList[kval]]|inputList[indList[lval]]
                                if len(lockedVal)==4:
                                    for m in range(dimsquared):
                                        if m!=indList[i] and m!=indList[jval] and m!=indList[kval] and m!=indList[lval]:
                                            for n in range(dimsquared):
                                                if n in lockedVal and n in inputList[m]:
                                                    removeList.append([m,n])
    return removeList

def basicFish(num,numOfRowcols,row):#X wings etc. row is 1 for rows and 0 for columns
    inp=False
    numUnsolved=dimsquared
    for i in squs:
        if i.num=={num}:
            numUnsolved-=1
    if numUnsolved>=(numOfRowcols*2)+row:
        fishArray=[set() for i in range(dimsquared)]
        if row==1:
            for i in range(dimsquared):
                for j in range(dimsquared):
                    if num in rows[i].squs[j].num:
                        fishArray[i].add(j)
            remList=lockedSetFinder(fishArray,numOfRowcols)
        else:
            for i in range(dimsquared):
                for j in range(dimsquared):
                    if num in cols[i].squs[j].num:
                        fishArray[i].add(j)
            remList=lockedSetFinder(fishArray,numOfRowcols)
        if len(remList)!=0:
            if row==1:
                for i in remList:
                    rows[i[0]].squs[i[1]].remove(num)
            else:
                for i in remList:
                    cols[i[0]].squs[i[1]].remove(num)
            inp=True
    return inp

def arrayRemoveDuplicates(array):#Removes duplicates in an array
    duplicates=[]
    for i in range(len(array)):
        for j in range(i):
            if array[i]==array[j]:
                duplicates.append(i)
    newarray=[]
    for i in range(len(array)):
        if not (i in duplicates):
            newarray.append(array[i])
    return newarray

def xyWing():#Finds and applies all XY Wings
    bivalueConnections=[]#Array of pairs of bivalue cells in a group sharing one number (first cell, second cell, common number, num unique to second)
    def groupBivalueConnections(group):#Returns all bivalue connections within one group
        groupConnections=[]
        for i in group.squs:
            for j in group.squs:
                if len(i.num)==2 and len(j.num)==2 and i.num!=j.num:
                    for k in range(dimsquared):
                        if k in i.num and k in j.num:
                            jset=j.num.copy()
                            jset.discard(k)
                            jnum=jset.pop()
                            groupConnections.append([i,j,k,jnum])
        return groupConnections
    for i in groups:#Adds every bivalue connection
        bivalueConnections.extend(groupBivalueConnections(i))
    bivalueConnections=arrayRemoveDuplicates(bivalueConnections)
    xywings=[]#Array of xywings consisting of a single bivalue hinge and two connected cells sharing the same extra number (both connected cells, extra number)
    for i in squs:
        iset=i.num.copy()
        num1=iset.pop()#One number in set - num2 is other num
        num1connections=[]#Connections involving i as a hinge and num1 as common num
        num2connections=[]#Connections involving i as a hinge and num2 as common num
        for j in bivalueConnections:
            if j[0]==i:
                if j[2]==num1:
                    num1connections.append(j)
                else:
                    num2connections.append(j)
        for j in num1connections:
            for k in num2connections:
                if j[3]==k[3]:
                    xywings.append([j[1],k[1],j[3]])
    xywings=arrayRemoveDuplicates(xywings)
    inp=False
    for i in squs:#Now start actually removing candidates based on the xywings obtained
        ineighbours=[]
        for j in i.row.squs:
            if i!=j:
                ineighbours.append(j)
        for j in i.col.squs:
            if i!=j:
                ineighbours.append(j)
        for j in i.box.squs:
            if i!=j:
                ineighbours.append(j)        
        for j in xywings:
            if j[0] in ineighbours and j[1] in ineighbours and j[2] in i.num:
                inp=i.remove(j[2]) or inp
    return inp

def getBasicMedusa():#Basic 3D Medusa, rules are applied later
    exors=[]
    for i in squs:#If two possibilities in a square, they form an exor.
        if len(i.num)==2:
            newpair=[]
            for j in range(dimsquared):
                if j in i.num:
                    newpair.append([[i,j]])
            exors.append(newpair)
    for i in range(dimsquared):#If two locations for a number in a group, they form an exor.
        for j in groups:
            if len(j.nums[i])==2:
                newpair=[]
                for k in range(dimsquared):
                    if k in j.nums[i]:
                        newpair.append([[j.squs[k],i]])
                exors.append(newpair)
    exorprogress=True
    while exorprogress:#Merging the exors
        exorprogress=False
        exorlen = len(exors)
        for i in range(exorlen):
            for j in range(i):
                if i < len(exors):#Because perhaps exors has become shorter
                    e00=exors[i][0]
                    e01=exors[i][1]
                    e10=exors[j][0]
                    e11=exors[j][1]
                    directmerge=False
                    crossmerge=False
                    for k in e00:
                        for l in e10:
                            if k==l:
                                directmerge=True
                        for l in e11:
                            if k==l:
                                crossmerge=True
                    for k in e01:
                        for l in e10:
                            if k==l:
                                crossmerge=True
                        for l in e11:
                            if k==l:
                                directmerge=True
                    if directmerge:
                        exors[i][0].extend(e10)
                        exors[i][1].extend(e11)
                        exors.pop(j)
                        exorprogress=True
                    elif crossmerge:
                        exors[i][0].extend(e11)
                        exors[i][1].extend(e10)
                        exors.pop(j)
                        exorprogress=True
    for i in range(len(exors)):#Remove duplicates within exors
        exors[i][0]=arrayRemoveDuplicates(exors[i][0])
        exors[i][1]=arrayRemoveDuplicates(exors[i][1])        
    return exors

def applyBasicMedusa(exors):#Basic 3D Medusa
    inp=False
    for i in exors:
        i0Forced=False
        i1Forced=False
        for j in squs:
            jIn0=0#Counts number of times j is in 1st part of exor
            jIn1=0
            for k in i[0]:
                if k[0]==j:
                    jIn0 += 1
            for k in i[1]:
                if k[0]==j:
                    jIn1 += 1
            if jIn0>=2:#If the same square appears twice in one part of an exor, it's a contradiction (Rule 1)
                i1Forced=True
            if jIn1>=2:
                i0Forced=True
        for j in range(dimsquared):
            for k in groups:
                jIn0=0#Counts number of times j is in 1st part of exor in k
                jIn1=0
                for l in i[0]:
                    if l[0] in k.squs and l[1]==j:
                        jIn0 += 1
                for l in i[1]:
                    if l[0] in k.squs and l[1]==j:
                        jIn1 += 1
                if jIn0>=2:#If the same number appears twice in a group in one part of an exor, it's a contradiction (Rule 2)
                    i1Forced=True
                if jIn1>=2:
                    i0Forced=True
        for j in squs:
            j.removedby0 = set()#What possibilities are removed if 1st part is true?
            j.removedby1 = set()#What possibilities are removed if 2nd part is true?
        for j in i[0]:
            for k in j[0].num:
                if k != j[1]:
                    j[0].removedby0.add(k)#Add everything in a square other than what's in the 1st part to those removed.
            for k in j[0].row.squs:
                if j[1] in k.num and k != j[0]:
                    k.removedby0.add(j[1])#Add everything in a group with same number as 1st part other than square in that part.
            for k in j[0].col.squs:
                if j[1] in k.num and k != j[0]:
                    k.removedby0.add(j[1])
            for k in j[0].box.squs:
                if j[1] in k.num and k != j[0]:
                    k.removedby0.add(j[1])
        for j in i[1]:
            for k in j[0].num:
                if k != j[1]:
                    j[0].removedby1.add(k)
            for k in j[0].row.squs:
                if j[1] in k.num and k != j[0]:
                    k.removedby1.add(j[1])
            for k in j[0].col.squs:
                if j[1] in k.num and k != j[0]:
                    k.removedby1.add(j[1])
            for k in j[0].box.squs:
                if j[1] in k.num and k != j[0]:
                    k.removedby1.add(j[1])
        for j in squs:
            if j.removedby0 == j.num:
                i1Forced=True#Does 1st part being true clear a square entirely? (Rule 6)
            if j.removedby1 == j.num:
                i0Forced=True#Does 2nd part being true clear a square entirely?
        for j in groups:
            for k in range(dimsquared):
                allremovedby0 = True#Does 1st part being true eliminate a number entirely? (Rule 7, not in wiki)
                allremovedby1 = True#Does 2nd part being true eliminate a number entirely?
                for l in j.squs:
                    if k in l.num:
                        if k not in l.removedby0:
                            allremovedby0 = False
                        if k not in l.removedby1:
                            allremovedby1 = False
                if allremovedby0:
                    i1Forced=True
                if allremovedby1:
                    i0Forced=True
        for j in squs:
            for k in range(dimsquared):
                if k in j.removedby0 and k in j.removedby1:
                    inp=j.remove(k) or inp#If something is eliminated by both parts, remove it (Rules 3, 4, 5)
        if i0Forced:
            for j in i[0]:
                inp=j[0].known(j[1]) or inp
        if i1Forced:
            for j in i[1]:
                inp=j[0].known(j[1]) or inp
    return inp

rows,cols,boxs,groups,subrows,subcols,squs=(None,)*7

def reset():
    global rows,cols,boxs,groups,subrows,subcols,squs
    rows=[Group() for i in range(dimsquared)]
    cols=[Group() for i in range(dimsquared)]
    boxs=[Group() for i in range(dimsquared)]
    subrows=[]
    for i in range(dimsquared):
        for j in range(dim):
            subrows.append(Subgroup(rows[i],boxs[(i//dim)*dim+j]))
    subcols=[]
    for i in range(dim):
        for j in range(dimsquared):
            subcols.append(Subgroup(cols[j],boxs[i*dim+j//dim]))
    squs=[]
    for i in range(dimsquared):
        for j in range(dimsquared):
            squs.append(Square(rows[i],cols[j],boxs[(i//dim)*dim+j//dim],subrows[i*dim+j//dim],subcols[(i//dim)*dimsquared+j]))
    groups=[]
    for i in range(dimsquared):
        groups.append(rows[i])
        groups.append(cols[i])
        groups.append(boxs[i])
reset()

#Main solving routine (limited to a maximum difficulty)
def mainSolve(maxdifficulty,valData=None,returnSquStrs=False):
    if not valData==None:
        for i in range(dimsquared):
            for j in range(dimsquared):
                valnums=valData[i][j]
                if len(valnums)==1:
                    rows[i].squs[j].known(valnums[0])
                elif len(valnums)!=0:
                    for k in range(dimsquared):
                        if k not in valnums:
                            rows[i].squs[j].remove(k)
    progress=True
    difficulty=1
    contradiction=False
    while progress:
        progress=False
        for i in groups:
            progress=i.basicSolve() or progress
        solved=True
        for i in squs:#Check if the sudoku is solved or has a contradiction, and stop if it is
            if len(i.num)!=1:
                solved=False
            if len(i.num)==0:
                contradiction=True
        if solved or contradiction:
            break
        if not(progress or solved):#If it cannot make progress with basicSolve it uses basicSubgroup
            if maxdifficulty<2:
                break
            difficulty=max(difficulty,2)
            for i in groups:
                progress=i.basicSubgroup() or progress
        if not(progress):#If it needs locked pairs or X-wing
            if maxdifficulty<3:
                break
            difficulty=max(difficulty,3)
            for i in groups:
                progress=i.basicLockedSet(2,0) or progress
                progress=i.basicLockedSet(2,1) or progress
            for i in range(dimsquared):
                progress=basicFish(i,2,0) or progress
                progress=basicFish(i,2,1) or progress
        if not(progress):#If it needs locked triples or swordfish
            if maxdifficulty<4:
                break
            difficulty=max(difficulty,4)
            for i in groups:
                progress=i.basicLockedSet(3,0) or progress
                progress=i.basicLockedSet(3,1) or progress
            for i in range(dimsquared):
                progress=basicFish(i,3,0) or progress
                progress=basicFish(i,3,1) or progress
        if not(progress):#If it needs locked quads or jellyfish
            if maxdifficulty<5:
                break
            difficulty=max(difficulty,5)
            for i in groups:
                progress=i.basicLockedSet(4,0) or progress
                progress=i.basicLockedSet(4,1) or progress
            for i in range(dimsquared):
                progress=basicFish(i,4,0) or progress
                progress=basicFish(i,4,1) or progress
        if not(progress):#If it needs XY Wings
            if maxdifficulty<6:
                break
            difficulty=max(difficulty,6)
            progress=xyWing() or progress
        if not(progress):#If it needs basic 3D Medusa
            if maxdifficulty<7:
                break
            difficulty=max(difficulty,7)
            exors=getBasicMedusa()
            progress=applyBasicMedusa(exors) or progress
    if returnSquStrs:
        squStrs=[[None]*dimsquared for i in range(dimsquared)]
        for i in range(dimsquared):
            for j in range(dimsquared):
                squStrs[i][j]=str(rows[i].squs[j])
        return solved,contradiction,difficulty,squStrs
    return solved,contradiction,difficulty

preSolveData=[]

#Main function for generating a sudoku up to a given difficulty
def mainGenerate(diff):
    reset()
    preSolveStates=[]
    nextSolveState=[[None]*dimsquared for i in range(dimsquared)]
    for i in range(dimsquared):
        for j in range(dimsquared):
            nextSolveState=set(range(dimsquared))
    def updateSqus(solveState):#Sets squs to whatever solveState has
        reset()
        for i in range(dimsquared):
            for j in range(dimsquared):
                for k in range(dimsquared):
                    if k not in solveState[i][j]:
                        rows[i].squs[j].remove(k)
    def updateSolveState():#Returns solveState determined by what the squs have
        solveState=[[None]*dimsquared for i in range(dimsquared)]
        for i in range(dimsquared):
            for j in range(dimsquared):
                solveState[i][j]=rows[i].squs[j].num.copy()
        return solveState
    initData=[]#What values is it using as initial data?
    random.seed(datetime.now())#Set random seed
    while True:
        solved,contradiction,difficulty = mainSolve(diff)
        if contradiction:#Go back a step, and remove the last choice from possibilities
            pastData=initData.pop()
            pastSolveState=preSolveStates.pop()
            updateSqus(pastSolveState)
            i=pastData[0]
            j=pastData[1]
            numChosen=pastData[2]
            rows[i].squs[j].remove(numChosen)
        elif solved:#Stop generating once it can be solved
            break
        else:
            #Another number needed
            #Preserve current state before the additional clue is given
            preSolveStates.append(updateSolveState())
            #Find a square with more than two numbers in it
            #Then add that number, and push the result
            ambiguousSqus=[]
            for i in range(dimsquared):
                for j in range(dimsquared):
                    if len(rows[i].squs[j].num)>1:
                        ambiguousSqus.append([i,j])
            ijChosen=ambiguousSqus[randint(0,len(ambiguousSqus)-1)]
            i=ijChosen[0]
            j=ijChosen[1]
            squChosen=rows[i].squs[j]
            numChosen=random.choice(tuple(squChosen.num))
            rows[i].squs[j].known(numChosen)
            initData.append([i,j,numChosen])
    #We have initData for a sudoku now!
    #But want to check that none of the clues are redundant (up to diff level)
    def buildFromInitData(initData):
        reset()
        for k in range(len(initData)):
            i=initData[k][0]
            j=initData[k][1]
            numChosen=initData[k][2]
            rows[i].squs[j].known(numChosen)
    redundancy=True
    checkedk=0
    while redundancy:
        redundancy=False
        for k in range(checkedk,len(initData)):
            newInitData=initData.copy()
            newInitData.pop(k)
            buildFromInitData(newInitData)
            mainSolve(diff)
            i=initData[k][0]
            j=initData[k][1]
            numChosen=initData[k][2]
            if rows[i].squs[j].num=={numChosen}:
                initData=newInitData
                checkedk=k
                redundancy=True
                break
    #We now have a sudoku without redundant clues! (at least, as far as the solver knows)
    #Get its difficulty!
    buildFromInitData(initData)
    solved,contradiction,difficulty=mainSolve(maxDiff)
    return initData,solved,difficulty

#Generates a sudoku within a difficulty range
def generateDiff(mindiff,maxdiff):
    solved=False
    difficulty=1
    while difficulty < mindiff or difficulty > maxdiff or not solved:
        initData,solved,difficulty=mainGenerate(maxdiff)
    print("Diff: "+str(difficulty))
    reset()
    rowarray=[[None]*(dimsquared+1) for i in range(dimsquared)]
    for i in range(dimsquared):
        for j in range(dimsquared):
            rowarray[i][j]=" "
        rowarray[i][dimsquared]="\n"
    for k in range(len(initData)):
        i=initData[k][0]
        j=initData[k][1]
        numChosen=initData[k][2]
        rowarray[i][j]=chars[numChosen]
    rowstrings=[""]*dimsquared
    for i in range(dimsquared):
        rowstrings[i]="".join(rowarray[i])
    return rowstrings
