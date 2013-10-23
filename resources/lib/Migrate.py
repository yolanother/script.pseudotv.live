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

import os
import xbmcaddon, xbmc, xbmcgui
import Settings
import Globals
import ChannelList
import ConfigParser

# from xml.parsers.expat import ExpatError
from FileAccess import FileLock, FileAccess


class Migrate:

    def log(self, msg, level = xbmc.LOGDEBUG):
        Globals.log('Migrate: ' + msg, level)


    def migrate(self):
        self.log("migrate")
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))    
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.forceReset = True
        
        # # If Autotune is enabled direct to autotuning
        # if Globals.REAL_SETTINGS.getSetting("Autotune") == "true":
            # self.log("initializeChannels")
            # if self.initializeChannels():
                # return True
        # else:
        if FileAccess.exists(settingsFile):
            return False
        else:
            currentpreset = 0

            for i in range(Globals.TOTAL_FILL_CHANNELS):
                chantype = 9999

                try:
                    chantype = int(Globals.ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type"))
                except:
                    pass

                if chantype == 9999:
                    self.log("addPreset")
                    self.addPreset(i + 1, currentpreset)
                    currentpreset += 1
                    
        return True

    def addPreset(self, channel, presetnum): # Initial settings2.xml preset on first run when empty...
    # Youtube
        BBCWW = ['BBCWW']
        Trailers = ['Trailers']
    # RSS
        HDNAT = ['HDNAT']
        TEKZA = ['TEKZA']
        
        if presetnum < len(BBCWW):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "BBCWorldwide")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "BBC World News")
        elif presetnum - len(BBCWW) < len(Trailers):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "movieclips")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")          
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "Movie Trailers")
        elif presetnum - len(BBCWW) - len(Trailers) < len(HDNAT):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "11")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "http://revision3.com/hdnation/feed/Quicktime-High-Definition")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")     
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "HD Nation")
        elif presetnum - len(BBCWW) - len(Trailers) - len(HDNAT) < len(TEKZA):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "11")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "http://revision3.com/tekzilla/feed/quicktime-high-definition")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_3", "50")            
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "Tekzilla")
            
              
    def initializeChannels(self):
        updatedlg = xbmcgui.DialogProgress()
        updatedlg.create("PseudoTV", "Initializing")
        updatedlg.update(1, "Initializing", "Initial Channel Setup")
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.fillTVInfo(True)
        updatedlg.update(30)
        chanlist.fillMovieInfo(True)
        updatedlg.update(60)
        # Now create TV networks, followed by mixed genres, followed by TV genres, and finally movie genres
        currentchan = 1
        mixedlist = []

        for item in chanlist.showGenreList:
            curitem = item[0].lower()

            for a in chanlist.movieGenreList:
                if curitem == a[0].lower():
                    mixedlist.append([item[0], item[1], a[1]])
                    break

        mixedlist.sort(key=lambda x: x[1] + x[2], reverse=True)
        currentchan = self.initialAddChannels(chanlist.networkList, 1, currentchan)
        updatedlg.update(70)

        # Mixed genres
        if len(mixedlist) > 0:
            added = 0.0

            for item in mixedlist:
                if item[1] > 2 and item[2] > 1:
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_type", "5")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_1", item[0])
                    added += 1.0
                    currentchan += 1
                    itemlow = item[0].lower()

                    # Remove that genre from the shows genre list
                    for i in range(len(chanlist.showGenreList)):
                        if itemlow == chanlist.showGenreList[i][0].lower():
                            chanlist.showGenreList.pop(i)
                            break

                    # Remove that genre from the movie genre list
                    for i in range(len(chanlist.movieGenreList)):
                        if itemlow == chanlist.movieGenreList[i][0].lower():
                            chanlist.movieGenreList.pop(i)
                            break

                    if added > 10:
                        break

                    updatedlg.update(int(70 + 10.0 / added))

        updatedlg.update(80)
        currentchan = self.initialAddChannels(chanlist.showGenreList, 3, currentchan)
        updatedlg.update(90)
        currentchan = self.initialAddChannels(chanlist.movieGenreList, 4, currentchan)
        updatedlg.close()

        if currentchan > 1:
            return True

        return False
        
        # InternetTV - addons.ini
        # elif Globals.REAL_SETTINGS.getSetting("AutotuneADDONS") == "true":
            # self.log('Autotune, AutotuneADDONS')
            # updatedlg.update(1, "Autotune", "Populating addons...")
            # Globals.REAL_SETTINGS.setSetting('AutotuneADDONS', "False")
            # self.addonsFile = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('addons'), 'addons.ini'))
            # self.addonsParser = ConfigParser.ConfigParser(dict_type=OrderedDict)
            # self.addonsParser.optionxform = lambda option: option
            # matches = list()
            # try:
                # self.addonsParser.read(self.addonsFile)
            # except:
                # print 'unable to parse addons.ini'
        
            # for id in self.getAddons():
                # try:
                    # xbmcaddon.Addon(id)
                # except Exception:
                    # continue # ignore addons that are not installed

                # for (label, stream) in self.getAddonStreams(id):
                    # matches.append((id, label, stream))         
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "9")
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "5400")
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "+stream +")
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rulecount", "1")
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_id", "1")
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_rule_1_opt_1", "+ label +")  

                # if len(matches) == 1:
                    # return matches[0][2]
                # else:
                    # return matches
            
        # InternetTV - Livestream
        # elif Globals.REAL_SETTINGS.getSetting("AutotuneLivestream") == "true":
            # self.log('Autotune, AutotuneLivestream')
            # Globals.REAL_SETTINGS.setSetting('AutotuneLivestream', "False") 
                
            
        # InternetTV - Music Videos - VevoTV
        # elif Globals.REAL_SETTINGS.getSetting("AutotuneVevoTV") == "true":
            # self.log('Autotune, AutotuneVevoTV')
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_type", "9")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_1", "5400")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_2", "rtmp://vevohp2livefs.fplive.net:1935/vevohp2live-live/ playpath=stream2272000 swfUrl=http://cache.vevo.com/livepassdl.conviva.com/ver/2.64.0.68610/LivePassModuleMain_osmf.swf")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_3", "VevoTV")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_rulecount", "1")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_rule_1_id", "1")
            # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_rule_1_opt_1", "VevoTV")  
            # Globals.REAL_SETTINGS.setSetting('AutotuneVevoTV', "False") 
   
        # # # Music Genre
        # if Globals.REAL_SETTINGS.getSetting("AutotuneMusic") == "true":
            # self.log('Autotune, AutotuneMusic')
            # chanlist.fillMusicInfo(True)
            # Globals.REAL_SETTINGS.setSetting('AutotuneMusic', "False")               
            # currentchan = self.initialAddChannels(chanlist.musicGenreList, 12, currentchan)
            # updatedlg.update(15)   
        
        # updatedlg.close()
        # Globals.REAL_SETTINGS.setSetting('Autotune', "False")
        # Globals.REAL_SETTINGS.setSetting('ATClean', "False")

    def getAddons(self):
        return self.addonsParser.sections()

    def getAddonStreams(self, id):
        return self.addonsParser.items(id)
        
    def initialAddChannels(self, thelist, chantype, currentchan):
        if len(thelist) > 0:
            counted = 0
            lastitem = 0
            curchancount = 1
            lowerlimit = 1
            lowlimitcnt = 0

            for item in thelist:
                if item[1] > lowerlimit:
                    if item[1] != lastitem:
                        if curchancount + counted <= 10 or counted == 0:
                            counted += curchancount
                            curchancount = 1
                            lastitem = item[1]
                        else:
                            break
                    else:
                        curchancount += 1

                    lowlimitcnt += 1

                    if lowlimitcnt == 3:
                        lowlimitcnt = 0
                        lowerlimit += 1
                else:
                    break

            if counted > 0:
                for item in thelist:
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_type", str(chantype))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_1", item[0])
                    counted -= 1
                    currentchan += 1

                    if counted == 0:
                        break

        return currentchan
   