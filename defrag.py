#   Copyright (C) 2011 Jason Anderson
#
#
# This file is part of PseudoTV.
#
# PseudoTV is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PseudoTV is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PseudoTV.  If not, see <http://www.gnu.org/licenses/>.

import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import time, threading
import datetime
import sys, re
import random
import resources.lib.Globals

from resources.lib.Globals import *
from resources.lib.FileAccess import FileAccess


class ConfigWindow(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.log("__init__")
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)
        self.doModal()
        self.log("__init__ return")
            
    def onFocus(self, controlId):
        pass


    def log(self, msg, level = xbmc.LOGDEBUG):
        log('ChannelConfig: ' + msg, level)

    def onInit(self):
        self.log("onInit")
        pass
        self.dlg = xbmcgui.DialogProgress()
        self.dlg.create("PseudoTV Live", "Optimizing Configurations...")
        Fil_Path = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
        OpnFil = FileAccess.open(Fil_Path, "rb")
        WrtFil = FileAccess.open(Fil_Path, "wb")
        WrtFil.write('<settings> \n')
        WrtFil.write('    ' + '<setting id="Version" value="2.1.0" />\n')

            # Number of total lines in Settings2.xml file
        nr_of_lines = sum(1 for line in OpnFil)

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

        os.remove (Fil_Path + "settings2.xml")
        os.rename (Fil_Path + "new_settings2.xml", Fil_Path + "settings2.xml")
        self.dlg.close()

__cwd__ = REAL_SETTINGS.getAddonInfo('path')


mydialog = ConfigWindow("script.pseudotv.live.ChannelConfig.xml", __cwd__, "default")
del mydialog
