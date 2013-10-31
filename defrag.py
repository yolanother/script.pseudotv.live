#-------------------------------------------------------------------------------
# Name:        module2
# Purpose:
#
# Author:      strtmkurt
#
# Created:     22/07/2013
# Copyright:   (c) strtmkurt 2013
# Licence:     <your licence>
#-------------------------------------------------------------------------------

def main():
    pass


import re
import os
import xbmcaddon, xbmc, xbmcgui

from resources.lib.Globals import *
from resources.lib.Settings import *
from resources.lib.FileAccess import FileAccess


flename = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))  
flenname = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'new_settings2.xml'))  
OpnFil = FileAccess.open(flename, "rb")
WrtFil = FileAccess.open(flename, "w")
WrtFil.write('<settings> \n')
WrtFil.write('    ' + '<setting id="Version" value="2.1.0" />\n')                        


    # Number of total lines in Settings2.xml file
nr_of_lines = sum(1 for line in FileAccess.open(flename))

# def simplecount(filename):
    # lines = 0
    # for line in FileAccess.open(flename):
        # lines += 1
    # return nr_of_lines

    # Procedure to get the total number of channels for this Settings2.xml file
    # High_Chan_Num variable will be the highest channel for the user
    # ChanNum variable is used to compare the current input channel with the
    # current highest channel (High_Chan_Num)

High_Chan_Num = 0
OpnFil.seek(0)  # Start file at the first line
for line in range(1, nr_of_lines): # Equal length of file
    Xstring = OpnFil.readline() #Input line as string from Settings2.xml file
    ins = Xstring.split("_")    # Split the line into parts using "_" delimeter
        # If the first part <> this string, then get next line
    if ins[0] == "    <setting id=" + chr(34) + "Channel":
        n=ins[1]    # assign variable to channel # string
        ChanNum=int(n)  # convert Channel Number to integer
        if ChanNum > High_Chan_Num:     #If > High_Chan_Num then
            High_Chan_Num=ChanNum       # assign to High_Chan_Num

High_Chan_Num = High_Chan_Num + 1    #Add 1 for following procedures.

for Num_Pos_Chan in range(1, High_Chan_Num): # Equal number of possible channels

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_type"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)  # Start file at the first line
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_1"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
           WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_2"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_3"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_4"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_rule"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_changed"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_time"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

    OpnFil.seek(0)
    for line in range(1, nr_of_lines): # Equal length of file
        Search_Item = "Channel_" + str(Num_Pos_Chan) + "_SetResetTime"
        Xstring = OpnFil.readline()
        if re.search(Search_Item, Xstring, re.I):
            WrtFil.write (Xstring)

OpnFil.seek(0)
for line in range(1, nr_of_lines): # Equal length of file
    #Search_Item_A = "LastExitTime"
    #Search_Item_B = "LastResetTime"
    Xstring = OpnFil.readline()
    if re.search("LastExitTime", Xstring, re.I):
        WrtFil.write (Xstring)
    elif re.search("LastResetTime", Xstring, re.I):
        WrtFil.write (Xstring)

WrtFil.write('</settings> \n')

OpnFil.close()
WrtFil.close()

os.remove (flename)
FileAccess.rename (flenname, flename)

if __name__ == '__main__':
    main()
