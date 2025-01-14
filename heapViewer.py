#!/usr/bin/python3
'''
Todo: 
1. Free functioanlity
2. How to show and remove a box
   Map Allocated address to (x1,y1,x2,y2)
   if there are no wrap around due to > xlimit, set x2,y2 as -1, -1
   On free(), fetch coords from dictionary and remove that from coordinates list
'''
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import random
  
#x = []
#y = []
colors = []

#CommandFile Processing globals
loopContinue = True
lastReadFileOffset = 0

#Graph configurations
fig = plt.figure()
ax = fig.add_subplot(111)
boxHeight = 25
guardBand = 5
MAX_BUFFERED_COMMANDS = 714
ResetGraphOnMemoryFree = False
#We limit viewing to 4MB because point is to visualize fragmentation
xlimit = 1024
ylimit = 4*1024

#Address allocations
coordinate = []
allocationCoordHashMap = {}
allocationSizeHasMap = {}
heapBaseAddress = None

def CalcuateYCoordinate(allocatedAddr, allocatedSize):
	y1coord = (allocatedAddr//xlimit) * boxHeight + guardBand
	if (allocatedAddr + allocatedSize) > xlimit:
		y2coord = ((allocatedAddr + allocatedSize)//xlimit) * boxHeight + guardBand
	else:
		y2coord = -1
	return [y1coord, y2coord]

def AppendCordinates(allocatedAddr, allocatedSize):
	tempAddr = allocatedAddr
	numAllocations = allocatedSize//xlimit
	allocAddress = allocatedAddr
	for num in range(numAllocations):
		allocSize = xlimit
		[y1coord, y2coord] = CalcuateYCoordinate(allocAddress, allocSize)
		if allocAddress > xlimit:
			allocAddress = allocAddress - (xlimit * (allocAddress//xlimit))
		coordinate.append([allocAddress, y1coord, allocSize, boxHeight])
		allocationCoordHashMap[(tempAddr, y1coord)] = [allocAddress, y1coord, allocSize, boxHeight]
		#This special case where alloc + Size > xlimit
		#In this case we need to split up the allocation into 2. The first one show still xlimit
		#Whatever allocaiton is remaining, we display that in the next row above
		if (allocAddress + allocSize) > xlimit:
			remainingSize = (allocAddress + allocSize) % xlimit
			coordinate.append([0, y2coord, remainingSize, boxHeight])
			allocationCoordHashMap[(0, y2coord)] = [0, y2coord, remainingSize, boxHeight]
		allocAddress = allocAddress + xlimit * (num + 1) + 1

	allocatedSize = allocatedSize - (numAllocations * xlimit)
	if allocatedSize > 0:
		[y1coord, y2coord] = CalcuateYCoordinate(allocatedAddr, allocatedSize)
		if allocatedAddr > xlimit:
			allocatedAddr = allocatedAddr - (xlimit * (allocatedAddr//xlimit))
		coordinate.append([allocatedAddr, y1coord, allocatedSize, boxHeight])
		allocationCoordHashMap[(tempAddr, y1coord)] = [allocatedAddr, y1coord, allocatedSize, boxHeight]
		#This special case where alloc + Size > xlimit
		#In this case we need to split up the allocation into 2. The first one show still xlimit
		#Whatever allocaiton is remaining, we display that in the next row above
		if (allocatedAddr + allocatedSize) > xlimit:
			remainingSize = (allocatedAddr + allocatedSize) % xlimit
			coordinate.append([0, y2coord, remainingSize, boxHeight])
			allocationCoordHashMap[(0, y2coord)] = [0, y2coord, remainingSize, boxHeight]


def RemoveCordinates(allocatedAddr, allocatedSize):
	global coordinate
	if allocatedSize == -1:
		return

	tempAddr = allocatedAddr
	[y1coord, y2coord] = CalcuateYCoordinate(allocatedAddr, allocatedSize)
	[allocatedAddr, y1coord, allocatedSize, boxHeight] = allocationCoordHashMap.get((tempAddr, y1coord), [-1, -1, -1, -1])
	
	try:
		if allocatedSize != -1:
			coordinate.remove([allocatedAddr, y1coord, allocatedSize, boxHeight])
			#allocationCoordHashMap[(allocatedAddr, y1coord)] = [-1, -1, -1, -1]
			allocationCoordHashMap.pop((tempAddr, y1coord))
	except ValueError:
		print(" !!!! WARNING !!!! ")
		print(allocatedAddr, y1coord, allocatedSize, boxHeight)
		print(" !!!! END OF WARNING !!!!")

	try:
		if y2coord != -1:
			[allocatedAddr, y2coord, allocatedSize, boxHeight] = allocationCoordHashMap.get((0, y2coord), [-1, -1, -1, -1])
			if allocatedSize != -1:
				coordinate.remove([0, y2coord, allocatedSize, boxHeight])
				#allocationCoordHashMap[(0, y2coord)] = [-1, -1, -1, -1]
				allocationCoordHashMap.pop((0, y2coord))
	except ValueError:
		print(" !!!! WARNING !!!! ")
		print(allocatedAddr, y2coord, allocatedSize, boxHeight)
		print(" !!!! END OF WARNING !!!!")


def ReadDataFile(fileName, bufferedCommandMaxCount):
	global heapBaseAddress, loopContinue, coordinate, lastReadFileOffset
	bufferedCommandCount = 0
	freeCommandSeen = False

	with open(fileName) as f:
		f.seek(lastReadFileOffset ,0)
		while loopContinue == True:
			line = f.readline()
			line = line.strip('\n')
			if not line:
				loopContinue = False
			else:
				cmd = line[0]
				addresss = 0
				size = 0

				bufferedCommandCount = bufferedCommandCount + 1
				if cmd == 'M':
					_,address,size,_ = line.split(" ")
					allocAddr = int(address)
					allocLength = int(size)
					#Update heapBase address as the allocation address from the first alloc
					if heapBaseAddress == None:
						heapBaseAddress = allocAddr
		
					allocAddr = allocAddr - heapBaseAddress
					allocationSizeHasMap[allocAddr] = allocLength
					AppendCordinates(allocAddr, allocLength)

				elif cmd == 'F':
					_,address,_ = line.split(" ")
					allocAddr = int(address)
					if heapBaseAddress != None:
						allocAddr = allocAddr - heapBaseAddress
					allocationBlockSize = allocationSizeHasMap.get(allocAddr, -1)
					RemoveCordinates(allocAddr, allocationBlockSize)
					#freeCommandSeen = True
				
				if bufferedCommandCount >= bufferedCommandMaxCount:
					break
		lastReadFileOffset = f.tell()

	return [bufferedCommandCount, freeCommandSeen]

def ResetGraph():
	ax.cla()
	plt.xlim(0,xlimit)
	plt.ylim(0,ylimit)
	#plt.autoscale(True, 'y')

def animation_func():
	global loopContinue, coordinate
	cmdsDisplayed = 0
	ResetGraph()
	while loopContinue == True:
		#[cmdsProcessed, restGraphOnFreeCmd] = ReadDataFile("allocation.txt", MAX_BUFFERED_COMMANDS)
		[cmdsProcessed, restGraphOnFreeCmd] = ReadDataFile("glsc2test1_allocation.txt",  MAX_BUFFERED_COMMANDS)
		
		ptchs = []

		for [x0, y0, w, h] in coordinate:
			ptchs.append(plt.Rectangle((x0, y0), w, h))
			p = PatchCollection(ptchs, cmap=cm.jet,alpha=0.4)
			#colors.append(0)
			#p.set_array(colors)
			ax.add_collection(p)
			plt.pause(0.01)

		cmdsDisplayed = cmdsDisplayed + cmdsProcessed
		print("Commands Displayed: " +str(cmdsDisplayed))
		if restGraphOnFreeCmd == True:
			ResetGraph()

	if len(coordinate) != 0:
		print("!!! WARNING: Potential Memory leak !!!")
		leakedBytes = 0
		for [x0, y0, w, h] in coordinate:
			leakedBytes = leakedBytes + w
		print( str(leakedBytes) + " bytes potentially leaked")
		print(" !!!! END OF WARNING !!!!")

	print("**** Program Completed ****")
	plt.show()

#ReadDataFile("glsc2test1_allocation.txt")
#animation = FuncAnimation(fig, animation_func, 
#                          interval = 100)
animation_func()