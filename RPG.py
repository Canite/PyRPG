#!/usr/bin/env python3
import pygame, sys, numpy, random
from pygame.locals import *
from math import *

colors = {}
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
CAMERA_WIDTH = SCREEN_WIDTH
CAMERA_HEIGHT = SCREEN_HEIGHT
FPS = 60


output = open("out.txt", 'w+')
with open("colors.txt", 'r') as colorfile:
    for line in colorfile:
        line_sp = line.rstrip('\n').split('\t')
        colors[line_sp[0]] = (int(line_sp[1]), int(line_sp[2]), int(line_sp[3]))

class switch(object):
    def __init__(self, value):
        self.value = value
        self.fall = False

    def __iter__(self):
        yield self.match
        raise StopIteration

    def match(self, *args):
        if self.fall or not args:
            return True
        elif self.value in args:
            self.fall = True
            return True
        else:
            return False

class Player:
    def __init__(self, startx, starty, width, height, movespeed):
        self.x = startx
        self.y = starty
        self.w = width
        self.h = height
        self.ms = movespeed
        self.img = colors["white"]
        self.numkeys = 0
        self.onexit = False

    def move(self, xval, yval):
        self.x += xval
        self.y += yval

class Enemy:
    def __init__(self, startx, starty, width, height, movespeed, etype, minsteps):
        self.x = startx
        self.y = starty
        self.w = width
        self.h = height
        self.img = colors["orangered"]
        self.state = "wander"
        self.collide = False
        self.ms = movespeed
        self.etype = etype
        self.minsteps = minsteps
        self.direction = 0
        self.steps = 0
        self.nextmove = 20
        # 0 = stopped, 1 = W, 2 = NW, 3 = N, 4 = NE, 5 = E, 6 = SE, 7 = S, 8 = SW

    def Decide(self):
        for case in switch(self.state):
            if case("stopped"):
                if (self.steps >= self.nextmove):
                    self.steps = 0
                    self.state = "wander"
                    self.direction = random.randrange(1, 9)
                    self.nextmove = self.minsteps + random.randrange(0, self.minsteps*4)
                #break
            if case("wander"):
                if (self.steps < self.nextmove): # and not self.collide):
                    self.steps += 1
                else:
                    self.steps = 0
                    self.state = "stopped"
                    self.direction = 0
                    self.nextmove = self.minsteps + random.randrange(0, self.minsteps*4)
                    if (self.collide):
                        self.collide = False
                #break

    def move(self, xval, yval):
        self.x += xval
        self.y += yval

class Tile:
    def __init__(self, xcoord, ycoord, name, img, block):
        self.coords = (xcoord, ycoord)
        self.name = name
        self.img = img
        self.block = block

class PathNode:
    def __init__(self, coords, gscore, hscore, parentnode):
        self.coords = coords
        self.gscore = gscore
        self.hscore = hscore
        self.parentnode = parentnode
        self.fscore = gscore + hscore

def CheckCoord(coord, nodelist):
    ## Return first instance if coord exists, else return None
    return next((node for node in nodelist if node.coords == coord), None)

def InsertNode(node, nodelist):
    ## Insert node in order of Fscore
    if (len(nodelist) == 0):
        nodelist.append(node)
    else:
        for i in xrange(len(nodelist)):
            if (nodelist[i].fscore >= node.fscore):
                nodelist.insert(i, node)
                break

def AddPath(tiles, curnode, stopcoord, openlist, closedlist, maxw, maxh):
    wallpen = 10
    openlist.remove(curnode)
    closedlist[curnode.coords] = 1
    curx = curnode.coords[0]
    cury = curnode.coords[1]

    for i in xrange(-1, 2):
        for j in xrange(-1, 2):
            ## Get von nuemann neighbors
            if ((i == 0 or j == 0) and not(i == 0 and j == 0)):
                if (curx + i > 1 and cury + j > 1 and curx + i < maxw - 1 and cury + j < maxh - 1):
                    coord = (curx + i, cury + j)
                    if (not coord in closedlist):
                        gscore = curnode.gscore + 1
                        multiplier = 10 if tiles[coord] == 1 else 1
                        hscore = multiplier*(abs(coord[0] - stopcoord[0]) + abs(coord[1] - stopcoord[1]))
                        fscore = gscore + hscore
                        oldnode = CheckCoord(coord, openlist)
                        if (oldnode == None):

                            newnode = PathNode(coord, gscore, hscore, curnode)
                            InsertNode(newnode, openlist)
                        elif (oldnode.fscore >= fscore):
                            oldnode.coords = coord
                            oldnode.gscore = gscore
                            oldnode.hscore = hscore
                            oldnode.fscore = fscore
                            oldnode.parentnode = curnode


def CreatePath(tiles, startcoord, stopcoord, maxw, maxh):
    openlist = []
    closedlist = {}

    startnode = PathNode(startcoord, 0, 0, None)
    openlist.append(startnode)
    stopnode = CheckCoord(stopcoord, openlist)
    while (stopnode == None):
        AddPath(tiles, openlist[0], stopcoord, openlist, closedlist, maxw, maxh)
        stopnode = CheckCoord(stopcoord, openlist)

    curnode = stopnode
    pathlist = []
    pathlist.append(curnode.coords)
    while (curnode.parentnode != None):
        tmp = curnode
        curnode = tmp.parentnode
        pathlist.append(curnode.coords)

    return pathlist

def FloodFill(startcoord, tiles, fillid, coorddict, coordlist, coordid, coordranges):
    minx = coordranges[0]
    maxx = coordranges[1]
    miny = coordranges[2]
    maxy = coordranges[3]
    coordstack = {}
    coordstack[startcoord] = coordid
    coordlist.append(startcoord)
    coorddict[startcoord] = coordid
    while (len(coordstack) > 0):
        curcoord = coordstack.popitem()[0]
        for i in xrange(-1, 2):
            for j in xrange(-1, 2):
                if ((i == 0 or j == 0) and (i != j)):
                    x = curcoord[0] + i
                    y = curcoord[1] + j
                    if ((x >= minx and x <= maxx) \
                            and (y >= miny and y <= maxy) \
                            and not (x, y) in coorddict \
                            and tiles[(x,y)].name == fillid):
                        coorddict[(x,y)] = coordid
                        coordlist.append((x,y))
                        coordstack[(x,y)] = coordid

    return len(coordlist)

class Map:
    def __init__(self, width, height, tilesize):
        self.w = width
        self.h = height
        self.ts = tilesize
        self.tiles = {}
        self.lockedrooms = []
        self.caverncoords = {}
        self.caverns = []
        self.cavernsizes = []
        self.maincavern = 0

        #GenerateMap()


    def GenerateMap(self, iterations, wallchance, doorchance, minroomsize, minwallsize, maxhallsize):
        # Fill in outer walls
        for i in xrange(0, self.w):
            self.tiles[(i, 0)] = Tile(i, 0, "wall", colors["blue"], True) # wall
            self.tiles[(i, self.h - 1)] = Tile(i, self.h - 1, "wall", colors["blue"], True)
        for i in xrange(0, self.h):
            self.tiles[(0, i)] = Tile(0, i, "wall", colors["blue"], True)
            self.tiles[(self.w - 1, i)] = Tile(self.w - 1, i, "wall", colors["blue"], True)

        # Fill in random walls everywhere else
        for i in xrange(1, self.w-1):
            for j in xrange(1, self.h-1):
                chance = random.random()
                if (chance <= wallchance):
                    self.tiles[(i, j)] = Tile(i, j, "wall", colors["blue"], True)
                else:
                    self.tiles[(i, j)] = Tile(i, j, "floor", colors["black"], False)

        # Perform cellular automaton transitions
        oldtiles = self.tiles
        count = 0
        while(count < iterations):
            for i in xrange(1, self.w-1):
                for j in xrange(1, self.h-1):
                    NW = oldtiles[(i-1, j-1)]
                    N = oldtiles[(i, j-1)]
                    NE = oldtiles[(i+1, j-1)]
                    W = oldtiles[(i-1, j)]
                    E = oldtiles[(i+1, j)]
                    SW = oldtiles[(i-1, j+1)]
                    S = oldtiles[(i, j+1)]
                    SE = oldtiles[(i+1, j+1)]
                    neighborwallcount = NW.block + N.block + NE.block + W.block + E.block + SW.block + S.block + SE.block
                    # If a wall
                    if (oldtiles[(i, j)].block):
                        # And surrounded by less than 3 walls
                        if (neighborwallcount < 3):
                            self.tiles[(i, j)].name = "floor"
                            self.tiles[(i, j)].block = False
                    # If not a wall
                    else:
                        # And surrounded by more than 4 walls
                        if (neighborwallcount > 4):
                            self.tiles[(i, j)].name = "wall"
                            self.tiles[(i, j)].block = True
            count += 1

        ## Flood fill to find caverns
        cavernnum = 0
        maxsize = 0
        for i in xrange(1, self.w-1):
            for j in xrange(1, self.h-1):
                if (not self.tiles[(i, j)].block and not (i, j) in self.caverncoords):
                    size = 0
                    self.cavernsizes.append(size)
                    self.caverns.append([])
                    self.cavernsizes[cavernnum] = FloodFill((i, j), self.tiles, "floor", self.caverncoords, self.caverns[cavernnum], cavernnum, (1, self.w - 1, 1, self.h - 1))
                    if (self.cavernsizes[cavernnum] > maxsize):
                        maxsize = self.cavernsizes[cavernnum]
                        self.maincavern = cavernnum

                    cavernnum += 1

        for i in xrange(len(self.caverns)):
            if (i != self.maincavern):
                if (self.cavernsizes[i] < minroomsize):
                    for j in xrange(len(self.caverns[i])):
                        self.tiles[(self.caverns[i][j][0], self.caverns[i][j][1])].name = "wall"
                        self.tiles[(self.caverns[i][j][0], self.caverns[i][j][1])].block = True

        ## Fill in small caverns first, now carve paths for larger subcaverns
        maxdist = maxhallsize
        for i in xrange(len(self.caverns)):
            if (i != self.maincavern):
                if (self.cavernsizes[i] >= minroomsize):
                    randpointsubcave = self.caverns[i][random.randrange(0, len(self.caverns[i]))]
                    closestpoint = self.caverns[self.maincavern][0]
                    closestdis = sqrt((randpointsubcave[0] - closestpoint[0])**2 + (randpointsubcave[1] - closestpoint[1])**2)
                    for z in xrange(len(self.caverns[self.maincavern])):
                        point = self.caverns[self.maincavern][z]
                        dist = sqrt((randpointsubcave[0] - point[0])**2 + (randpointsubcave[1] - point[1])**2)
                        if (dist < closestdis):
                            closestdis = dist
                            closestpoint = point
                    if (closestdis <= maxdist):
                        pathlist = CreatePath(self.tiles, randpointsubcave, closestpoint, self.w, self.h)
                        for q in xrange(len(pathlist)):
                            if (self.tiles[pathlist[q]].block):
                                self.tiles[pathlist[q]].name = "floor"
                                self.tiles[pathlist[q]].block = False
                                N = (pathlist[q][0], pathlist[q][1]-1)
                                S = (pathlist[q][0], pathlist[q][1]+1)
                                E = (pathlist[q][0]+1, pathlist[q][1])
                                W = (pathlist[q][0]-1, pathlist[q][1])
                                if ((self.tiles[N].block and self.tiles[S].block) or (self.tiles[E].block and self.tiles[W].block)):
                                    self.caverncoords[pathlist[q]] = self.maincavern
                                else:
                                    self.caverncoords[pathlist[q]] = i
                    else:
                        for j in xrange(len(self.caverns[i])):
                            self.tiles[(self.caverns[i][j][0], self.caverns[i][j][1])].name = "wall"
                            self.tiles[(self.caverns[i][j][0], self.caverns[i][j][1])].block = True

        ## Get rid of small subareas of wall within cave
        wallcoords = {}
        for i in xrange(1, self.w-1):
            for j in xrange(1, self.h-1):
                if (self.tiles[(i, j)].name == "wall" and not (i, j) in wallcoords):
                    walllist = []
                    FloodFill((i, j), self.tiles, "wall", wallcoords, walllist, 0, (1, self.w - 1, 1, self.h - 1))
                    if (len(walllist) < minwallsize):
                        for z in xrange(len(walllist)):
                            self.caverncoords[walllist[z]] = self.maincavern + 1
                            self.tiles[walllist[z]].name = "floor"
                            self.tiles[walllist[z]].block = False

        for i in xrange(1, self.w-1):
            for j in xrange(1, self.h-1):
                if (self.tiles[(i, j)].block):
                    NW = self.tiles[(i-1, j-1)]
                    N = self.tiles[(i, j-1)]
                    NE = self.tiles[(i+1, j-1)]
                    W = self.tiles[(i-1, j)]
                    E = self.tiles[(i+1, j)]
                    SW = self.tiles[(i-1, j+1)]
                    S = self.tiles[(i, j+1)]
                    SE = self.tiles[(i+1, j+1)]

                    ## Get rid of diagonal corners
                    if (SW.block and not W.block and not S.block):
                        self.tiles[(i, j)].name = "floor"
                        self.tiles[(i, j)].block = False
                        self.tiles[(i-1, j+1)].name = "floor"
                        self.tiles[(i-1, j+1)].block = False
                    if (SE.block and not E.block and not S.block):
                        self.tiles[(i, j)].name = "floor"
                        self.tiles[(i, j)].block = False
                        self.tiles[(i+1, j+1)].name = "floor"
                        self.tiles[(i+1, j+1)].block = False
                    if (NW.block and not W.block and not N.block):
                        self.tiles[(i, j)].name = "floor"
                        self.tiles[(i, j)].block = False
                        self.tiles[(i-1, j-1)].name = "floor"
                        self.tiles[(i-1, j-1)].block = False
                    if (NE.block and not E.block and not N.block):
                        self.tiles[(i, j)].name = "floor"
                        self.tiles[(i, j)].block = False
                        self.tiles[(i+1, j-1)].name = "floor"
                        self.tiles[(i+1, j-1)].block = False

        numkeys = 0
        for i in xrange(1, self.w-1):
            for j in xrange(1, self.h-1):
                if (not self.tiles[(i, j)].block):
                    N = self.tiles[(i, j-1)]
                    W = self.tiles[(i-1, j)]
                    E = self.tiles[(i+1, j)]
                    S = self.tiles[(i, j+1)]

                    ## Set up doors
                    if (N.block and S.block and not E.block and not W.block and self.caverncoords[(i-1, j)] != self.caverncoords[(i+1, j)] and (self.caverncoords[(i-1, j)] == self.maincavern or self.caverncoords[(i+1, j)] == self.maincavern)):
                        doorrand = random.random()
                        if (doorrand <= doorchance):
                            if (self.caverncoords[(i-1, j)] == self.maincavern and not self.caverncoords[(i+1, j)] in self.lockedrooms):
                                self.tiles[(i, j)].name = "door"
                                self.tiles[(i, j)].block = True
                                self.lockedrooms.append(self.caverncoords[(i+1, j)])
                                numkeys += 1
                            elif (not self.caverncoords[(i-1, j)] in self.lockedrooms):
                                self.tiles[(i, j)].name = "door"
                                self.tiles[(i, j)].block = True
                                self.lockedrooms.append(self.caverncoords[(i-1, j)])
                                numkeys += 1

                    if (E.block and W.block and not N.block and not S.block and self.caverncoords[(i, j-1)] != self.caverncoords[(i, j+1)] and (self.caverncoords[(i, j-1)] == self.maincavern or self.caverncoords[(i, j+1)] == self.maincavern)):
                        doorrand = random.random()
                        if (doorrand <= doorchance):
                            if (self.caverncoords[(i, j-1)] == self.maincavern and not self.caverncoords[(i, j+1)] in self.lockedrooms):
                                self.tiles[(i, j)].name = "door"
                                self.tiles[(i, j)].block = True
                                self.lockedrooms.append(self.caverncoords[(i, j+1)])
                                numkeys += 1
                            elif (not self.caverncoords[(i, j-1)] in self.lockedrooms):
                                self.tiles[(i, j)].name = "door"
                                self.tiles[(i, j)].block = True
                                self.lockedrooms.append(self.caverncoords[(i, j-1)])
                                numkeys += 1

        for i in xrange(numkeys):
            randx = random.randrange(self.w)
            randy = random.randrange(self.h)
            while (self.tiles[(randx, randy)].name != "floor" or self.caverncoords[(randx, randy)] != self.maincavern):
                randx = random.randrange(self.w)
                randy = random.randrange(self.h)
            self.tiles[(randx, randy)].name = "key"
            self.tiles[(randx, randy)].block = False

        for i in xrange(len(self.lockedrooms)):
            caveid = self.lockedrooms[i]
            randcoord = self.caverns[caveid][random.randrange(len(self.caverns[caveid]))]
            self.tiles[randcoord].name = "treasure"

        for i in xrange(1, self.w-1):
            for j in xrange(1, self.h-1):
                if (self.tiles[(i, j)].name == "wall"):
                    self.tiles[(i, j)].img = colors["blue"]
                elif (self.tiles[(i, j)].name == "floor"):
                    self.tiles[(i, j)].img = colors["black"]
                elif (self.tiles[(i, j)].name == "door"):
                    self.tiles[(i, j)].img = colors["red"]
                elif (self.tiles[(i, j)].name == "key"):
                    self.tiles[(i, j)].img = colors["yellow"]
                elif (self.tiles[(i, j)].name == "treasure"):
                    self.tiles[(i, j)].img = colors["green"]

def PlayerCheckCollisions(p1, keylist, tiles, tilesize):
    toplefthorpos = (int(floor((p1.x-p1.ms)/tilesize)), int(floor(p1.y/tilesize)))
    botlefthorpos = (int(floor((p1.x-p1.ms)/tilesize)), int(floor((p1.y+p1.h-1)/tilesize)))
    toplefttilehor = tiles[toplefthorpos]
    botlefttilehor = tiles[botlefthorpos]

    if (keylist[K_LEFT]):
        if (not toplefttilehor.block and not botlefttilehor.block):
            p1.move(-p1.ms, 0)
            if (toplefttilehor.name == "key"):
                p1.numkeys += 1
                tiles[toplefthorpos].name = "floor"
                tiles[toplefthorpos].img = colors["black"]
            if (botlefttilehor.name == "key"):
                p1.numkeys += 1
                tiles[botlefthorpos].name = "floor"
                tiles[botlefthorpos].img = colors["black"]
            if (toplefttilehor.name == "exit" or botlefttilehor.name == "exit"):
                p1.onexit = True
        else:
            # +1 to move up to right edge of wall
            if (toplefttilehor.name == "door" and botlefttilehor.name == "door" and p1.numkeys > 0):
                p1.numkeys -= 1
                p1.move(-p1.ms, 0)
                tiles[toplefthorpos].name = "floor"
                tiles[toplefthorpos].block = False
                tiles[toplefthorpos].img = colors["black"]
            else:
                p1.move(int(floor(((p1.x-p1.ms)/tilesize)) + 1)*tilesize - p1.x, 0)

    toprighthorpos = (int(floor((p1.x+p1.w+p1.ms-1)/tilesize)), int(floor((p1.y)/tilesize)))
    botrighthorpos = (int(floor((p1.x+p1.w+p1.ms-1)/tilesize)), int(floor((p1.y+p1.h-1)/tilesize)))
    toprighttilehor = tiles[toprighthorpos]
    botrighttilehor = tiles[botrighthorpos]

    if (keylist[K_RIGHT]):
        if (not toprighttilehor.block and not botrighttilehor.block):
            p1.move(p1.ms, 0)
            if (toprighttilehor.name == "key"):
                p1.numkeys += 1
                tiles[toprighthorpos].name = "floor"
                tiles[toprighthorpos].img = colors["black"]
            if (botrighttilehor.name == "key"):
                p1.numkeys += 1
                tiles[botrighthorpos].name = "floor"
                tiles[botrighthorpos].img = colors["black"]
            if (toprighttilehor.name == "exit" or botrighttilehor.name == "exit"):
                p1.onexit = True
        else:
            # +1 to move up to right edge of wall
            if (toprighttilehor.name == "door" and botrighttilehor.name == "door" and p1.numkeys > 0):
                p1.numkeys -= 1
                p1.move(p1.ms, 0)
                tiles[toprighthorpos].name = "floor"
                tiles[toprighthorpos].block = False
                tiles[toprighthorpos].img = colors["black"]
            else:
                p1.move(int(floor(((p1.x+p1.w+p1.ms)/tilesize)))*tilesize - (p1.x + p1.w), 0)

    topleftverpos = (int(floor((p1.x)/tilesize)), int(floor((p1.y-p1.ms)/tilesize)))
    toprightverpos = (int(floor((p1.x+p1.w-1)/tilesize)), int(floor((p1.y-p1.ms)/tilesize)))
    toplefttilever = tiles[topleftverpos]
    toprighttilever = tiles[toprightverpos]

    if (keylist[K_UP]):
        if (not toplefttilever.block and not toprighttilever.block):
            p1.move(0, -p1.ms)
            if (toplefttilever.name == "key"):
                p1.numkeys += 1
                tiles[topleftverpos].name = "floor"
                tiles[topleftverpos].img = colors["black"]
            if (toprighttilever.name == "key"):
                p1.numkeys += 1
                tiles[toprightverpos].name = "floor"
                tiles[toprightverpos].img = colors["black"]
            if (toplefttilever.name == "exit" or toprighttilever.name == "exit"):
                p1.onexit = True
        else:
            # +1 to move up to right edge of wall
            if (toplefttilever.name == "door" and toprighttilever.name == "door" and p1.numkeys > 0):
                p1.numkeys -= 1
                p1.move(0, -p1.ms)
                tiles[topleftverpos].name = "floor"
                tiles[topleftverpos].block = False
                tiles[topleftverpos].img = colors["black"]
            else:
                p1.move(0, int(floor(((p1.y-p1.ms)/tilesize)) + 1)*tilesize - p1.y)

    botrightverpos = (int(floor((p1.x+p1.w-1)/tilesize)), int(floor((p1.y+p1.h+p1.ms-1)/tilesize)))
    botleftverpos = (int(floor((p1.x)/tilesize)), int(floor((p1.y+p1.h+p1.ms-1)/tilesize)))
    botrighttilever = tiles[botrightverpos]
    botlefttilever = tiles[botleftverpos]

    if (keylist[K_DOWN]):
        if (not botlefttilever.block and not botrighttilever.block):
            p1.move(0, p1.ms)
            if (botlefttilever.name == "key"):
                p1.numkeys += 1
                tiles[botleftverpos].name = "floor"
                tiles[botleftverpos].img = colors["black"]
            if (botrighttilever.name == "key"):
                p1.numkeys += 1
                tiles[botrightverpos].name = "floor"
                tiles[botrightverpos].img = colors["black"]
            if (botlefttilever.name == "exit" or botrighttilever.name == "exit"):
                p1.onexit = True
        else:
            # +1 to move up to right edge of wall
            if (botlefttilever.name == "door" and botrighttilever.name == "door" and p1.numkeys > 0):
                p1.numkeys -= 1
                p1.move(0, p1.ms)
                tiles[botleftverpos].name = "floor"
                tiles[botleftverpos].block = False
                tiles[botleftverpos].img = colors["black"]
            else:
                p1.move(0, int(floor(((p1.y+p1.h+p1.ms)/tilesize)))*tilesize - (p1.y + p1.h))

def EnemyCheckCollisions(p1, tiles, tilesize):
    def case(num):
        return p1.direction == num
    #for case in switch(p1.direction):
    if case(0):
        return
    # Left movement
    if case(1) or case(2) or case(8):
        toplefthorpos = (int(floor((p1.x-p1.ms)/tilesize)), int(floor(p1.y/tilesize)))
        botlefthorpos = (int(floor((p1.x-p1.ms)/tilesize)), int(floor((p1.y+p1.h-1)/tilesize)))
        toplefttilehor = tiles[toplefthorpos]
        botlefttilehor = tiles[botlefthorpos]
        if (not toplefttilehor.block and not botlefttilehor.block):
            p1.move(-p1.ms, 0)
        else:
            p1.move(int(floor(((p1.x-p1.ms)/tilesize)) + 1)*tilesize - p1.x, 0)
            p1.collide = True
        #break

    # Right movement
    if case(4) or case(5) or case(6):
        toprighthorpos = (int(floor((p1.x+p1.w+p1.ms-1)/tilesize)), int(floor((p1.y)/tilesize)))
        botrighthorpos = (int(floor((p1.x+p1.w+p1.ms-1)/tilesize)), int(floor((p1.y+p1.h-1)/tilesize)))
        toprighttilehor = tiles[toprighthorpos]
        botrighttilehor = tiles[botrighthorpos]
        if (not toprighttilehor.block and not botrighttilehor.block):
            p1.move(p1.ms, 0)
        else:
            p1.move(int(floor(((p1.x+p1.w+p1.ms)/tilesize)))*tilesize - (p1.x + p1.w), 0)
            p1.collide = True
        #break

    # Up movement
    if case(2) or case(3) or case(4):
        topleftverpos = (int(floor((p1.x)/tilesize)), int(floor((p1.y-p1.ms)/tilesize)))
        toprightverpos = (int(floor((p1.x+p1.w-1)/tilesize)), int(floor((p1.y-p1.ms)/tilesize)))
        toplefttilever = tiles[topleftverpos]
        toprighttilever = tiles[toprightverpos]
        if (not toplefttilever.block and not toprighttilever.block):
            p1.move(0, -p1.ms)
        else:
            p1.move(0, int(floor(((p1.y-p1.ms)/tilesize)) + 1)*tilesize - p1.y)
            p1.collide = True
        #break

    # Down movement
    if case(6) or case(7) or case(8):
        botrightverpos = (int(floor((p1.x+p1.w-1)/tilesize)), int(floor((p1.y+p1.h+p1.ms-1)/tilesize)))
        botleftverpos = (int(floor((p1.x)/tilesize)), int(floor((p1.y+p1.h+p1.ms-1)/tilesize)))
        botrighttilever = tiles[botrightverpos]
        botlefttilever = tiles[botleftverpos]
        if (not botrighttilever.block and not botlefttilever.block):
            p1.move(0, p1.ms)
        else:
            p1.move(0, int(floor(((p1.y+p1.h+p1.ms)/tilesize)))*tilesize - (p1.y + p1.h))
            p1.collide = True
        #break

def main():
    GAME_WIDTH = SCREEN_WIDTH
    GAME_HEIGHT = SCREEN_HEIGHT

    ## Init pygame
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    ## Init surfaces
    WINDOWSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    CAMERASURF = pygame.Surface((CAMERA_WIDTH, CAMERA_HEIGHT))
    GAMESURF = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    TILESURF = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    MENUSURF = pygame.Surface((120, SCREEN_HEIGHT))
    pygame.display.set_caption("RPG")
    tilesize = 24

    GAMESURF.set_colorkey(colors["thistle"])

    ## Generate map
    levels = []
    curmap = 0
    shopmap = Map(GAME_WIDTH/tilesize, GAME_HEIGHT/tilesize, tilesize)
    shopmap.GenerateMap(3, 0.3, 0.5, 15, 30, sqrt(shopmap.h**2 + shopmap.w**2)/8)
    exitx = random.randrange(1, GAME_WIDTH/shopmap.ts)
    exity = random.randrange(1, GAME_HEIGHT/shopmap.ts)
    while (shopmap.tiles[(exitx, exity)].block or shopmap.caverncoords[exitx, exity] != shopmap.maincavern):
        exitx = random.randrange(1, GAME_WIDTH/shopmap.ts)
        exity = random.randrange(1, GAME_HEIGHT/shopmap.ts)
    shopmap.tiles[(exitx, exity)].name = "exit"
    shopmap.tiles[(exitx, exity)].block = False
    shopmap.tiles[(exitx, exity)].img = colors["violet"]

    levels.append(shopmap)

    ## Select player start position
    startx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
    starty = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
    while (levels[curmap].tiles[(startx, starty)].name == "exit" or levels[curmap].tiles[(startx, starty)].block or levels[curmap].caverncoords[startx, starty] != levels[curmap].maincavern):
        startx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
        starty = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
    player = Player(startx*levels[curmap].ts, starty*levels[curmap].ts, 24, 24, 3.0)
    move_limit = 0

    startx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
    starty = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
    while (levels[curmap].tiles[(startx, starty)].name == "exit" or levels[curmap].tiles[(startx, starty)].block or levels[curmap].caverncoords[startx, starty] != levels[curmap].maincavern):
        startx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
        starty = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
    enemy = Enemy(startx*levels[curmap].ts, starty*levels[curmap].ts, 24, 24, 0.75, "rat", 15)

    ## Set up camera
    camerax = max(min(player.x + player.w/2 - CAMERA_WIDTH/2, GAME_WIDTH - CAMERA_WIDTH), 0)
    cameray = max(min(player.y + player.h/2 - CAMERA_HEIGHT/2, GAME_HEIGHT - CAMERA_HEIGHT), 0)

    ## Create menu font
    menufont = pygame.font.SysFont(None, 16)
    menuup = False

    ## Create font for showing FPS
    FPSfont = pygame.font.SysFont(None, 24)
    showFPS = False

    for i in xrange(GAME_WIDTH/tilesize):
        for j in xrange(GAME_HEIGHT/tilesize):
            pygame.draw.rect(TILESURF, levels[curmap].tiles[(i, j)].img, (i*levels[curmap].ts, j*levels[curmap].ts, levels[curmap].ts, levels[curmap].ts))

    ## Game loop
    while (True):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if (event.type == KEYUP and event.key == K_SPACE):
                menuup = not menuup

            if (event.type == KEYUP and event.key == K_f):
                showFPS = not showFPS

        if (player.onexit):
            player.onexit = False
            curmap += 1
            GAME_WIDTH = SCREEN_WIDTH*3
            GAME_HEIGHT = SCREEN_HEIGHT*3
            GAMESURF = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            TILESURF = pygame.Surface((GAME_WIDTH, GAME_HEIGHT))
            GAMESURF.set_colorkey(colors["thistle"])
            levels.append(Map(GAME_WIDTH/tilesize, GAME_HEIGHT/tilesize, tilesize))
            levels[curmap].GenerateMap(3, 0.41, 0.5, 15, 15, sqrt(levels[curmap].h**2 + levels[curmap].w**2)/8)

            exitx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
            exity = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
            while (levels[curmap].tiles[(exitx, exity)].name != "floor" or levels[curmap].caverncoords[exitx, exity] != levels[curmap].maincavern):
                exitx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
                exity = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
            levels[curmap].tiles[(exitx, exity)].name = "exit"
            levels[curmap].tiles[(exitx, exity)].block = False
            levels[curmap].tiles[(exitx, exity)].img = colors["violet"]

            startx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
            starty = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
            dist = sqrt((startx - exitx)**2 + (starty - exity)**2)
            count = 0
            while ((dist < (sqrt((GAME_WIDTH/3)**2 + (GAME_HEIGHT/3)**2)/tilesize) and count < 1000) or levels[curmap].tiles[(startx, starty)].block or levels[curmap].caverncoords[startx, starty] != levels[curmap].maincavern):
                count += 1
                startx = random.randrange(1, GAME_WIDTH/levels[curmap].ts)
                starty = random.randrange(1, GAME_HEIGHT/levels[curmap].ts)
                dist = sqrt((startx - exitx)**2 + (starty - exity)**2)
            player.x = startx*levels[curmap].ts
            player.y = starty*levels[curmap].ts
            move_limit = 0
            camerax = max(min(player.x + player.w/2 - CAMERA_WIDTH/2, GAME_WIDTH - CAMERA_WIDTH), 0)
            cameray = max(min(player.y + player.h/2 - CAMERA_HEIGHT/2, GAME_HEIGHT - CAMERA_HEIGHT), 0)
            for i in xrange(GAME_WIDTH/tilesize):
                for j in xrange(GAME_HEIGHT/tilesize):
                    pygame.draw.rect(TILESURF, levels[curmap].tiles[(i, j)].img, (i*levels[curmap].ts, j*levels[curmap].ts, levels[curmap].ts, levels[curmap].ts))

        ## Check collisions
        keys = pygame.key.get_pressed()
        if (move_limit == 0):
            PlayerCheckCollisions(player, keys, levels[curmap].tiles, levels[curmap].ts)
            move_limit = 0
        else:
            move_limit -= 1

        enemy.Decide()
        EnemyCheckCollisions(enemy, levels[curmap].tiles, levels[curmap].ts)

        if (player.x < 0):
            player.x = 0
        if (player.x + player.w > GAME_WIDTH):
            player.x = GAME_WIDTH - player.w
        if (player.y < 0):
            player.y = 0
        if (player.y + player.h > GAME_HEIGHT):
            player.y = GAME_HEIGHT - player.h

        ## Move camera with player
        if (player.x + (player.w/2) >= CAMERA_WIDTH/2 and player.x + (player.w/2) <= GAME_WIDTH - CAMERA_WIDTH/2):
            camerax = player.x + (player.w/2) - (CAMERA_WIDTH/2)
        if (player.y + (player.h/2) >= CAMERA_HEIGHT/2 and player.y + (player.h/2) <= GAME_HEIGHT - CAMERA_HEIGHT/2):
            cameray = player.y + (player.h/2) - (CAMERA_HEIGHT/2)

        ## Fill surfaces
        WINDOWSURF.fill(colors["blue"])
        MENUSURF.fill(colors["black"])
        GAMESURF.fill(colors["thistle"])

        ## Draw player and map
        #for i in xrange(int(floor(camerax/levels[curmap].ts)), int(ceil((camerax + CAMERA_WIDTH)/levels[curmap].ts)) + 1):
        #    for j in xrange(int(floor(cameray/levels[curmap].ts)), int(ceil((cameray + CAMERA_HEIGHT)/levels[curmap].ts)) + 1):
        #        if (i < levels[curmap].w and j < levels[curmap].h):
        #            pygame.draw.rect(GAMESURF, levels[curmap].tiles[(i, j)].img, (i*levels[curmap].ts, j*levels[curmap].ts, levels[curmap].ts, levels[curmap].ts))

        pygame.draw.rect(GAMESURF, enemy.img, (enemy.x, enemy.y, enemy.w, enemy.h))
        pygame.draw.rect(GAMESURF, player.img, (player.x, player.y, player.w, player.h))

        ## Draw the menu
        if (menuup):
            pygame.draw.rect(MENUSURF, colors["white"], (0, 0, 120, SCREEN_HEIGHT), 1)
            menutext = menufont.render("You have %i %s." % (player.numkeys, "key" if player.numkeys == 1 else "keys"), True, colors["white"])
            textrect = menutext.get_rect()
            MENUSURF.blit(menutext, (60 - textrect.width/2, 10))

        ## Blit game screen and menu screen to the window
        CAMERASURF.blit(TILESURF, (0,0), (camerax, cameray, CAMERA_WIDTH, CAMERA_HEIGHT))
        CAMERASURF.blit(GAMESURF, (0,0), (camerax, cameray, CAMERA_WIDTH, CAMERA_HEIGHT))
        WINDOWSURF.blit(CAMERASURF, (0,0))
        if (menuup):
            WINDOWSURF.blit(MENUSURF, (SCREEN_WIDTH-120, 0))

        ## If F was pressed, display current FPS
        if (showFPS):
            FPStext = FPSfont.render("FPS: " + str(int(FPSCLOCK.get_fps())), True, colors["red"])
            WINDOWSURF.blit(FPStext, (10, 10))

        pygame.display.flip()
        FPSCLOCK.tick(FPS)

if __name__ == '__main__':
    main()
    output.close()
