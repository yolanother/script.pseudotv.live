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
from FileAccess import FileLock, FileAccess


class Migrate:

    def log(self, msg, level = xbmc.LOGDEBUG):
        Globals.log('Migrate: ' + msg, level)


    def migrate(self):
        self.log("migration")    
        chanlist = ChannelList.ChannelList()
        chanlist.background = False
        chanlist.forceReset = True
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))
        
        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning") == "true":
            self.log("initializeChannels")
            if self.initializeChannels():
                return True           
        else:
            if FileAccess.exists(settingsFile):
                return False
            else:
                for i in range(200):
                    self.log("addPlaylist")
                    if os.path.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'):
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_type", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_1", "special://profile/playlists/video/Channel_" + str(i + 1) + ".xsp")
                    elif os.path.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'):
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_type", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_1", "special://profile/playlists/mixed/Channel_" + str(i + 1) + ".xsp") 
                    elif os.path.exists(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'):
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_type", "0")
                        Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_1", "special://profile/playlists/music/Channel_" + str(i + 1) + ".xsp")

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

                for i in range(999):
                    try:
                        if Globals.ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_type") == '6':
                            if Globals.ADDON_SETTINGS.getSetting("Channel_" + str(i + 1) + "_2") == "6":
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_rulecount", "2")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_rule_1_id", "8")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_rule_2_id", "9")
                                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(i + 1) + "_2", "4")
                    except:
                        pass

            return True


    def addPreset(self, channel, presetnum):
        BBCWW = ['BBCWW']
        Trailers = ['movieclips']
        
        if presetnum < len(BBCWW):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "BBCWorldwide")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")
        elif presetnum - len(BBCWW) < len(Trailers):
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_type", "10")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_1", "movieclips")
            Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2", "1")


    def initializeChannels(self):
            self.log('Autotune, initializeChannels')
            updatedlg = xbmcgui.DialogProgress()
            updatedlg.create("PseudoTV", "Initializing")
            updatedlg.update(1, "Initializing", "Autotune Channel Setup")
            chanlist = ChannelList.ChannelList()
            chanlist.background = False
            chanlist.forceReset = True
            
            if Globals.REAL_SETTINGS.getSetting("AutotuneTV") == "true":
                self.log('Autotune, fillTVInfo')
                Globals.REAL_SETTINGS.setSetting('AutotuneTV', "False")
                chanlist.fillTVInfo(True)
                updatedlg.update(30)
            elif Globals.REAL_SETTINGS.getSetting("AutotuneMovie") == "true":
                self.log('Autotune, AutotuneMovie')
                chanlist.fillMovieInfo(True)
                Globals.REAL_SETTINGS.setSetting('AutotuneMovie', "False")
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
            updatedlg.update(2, "Auto Tune","Searching for TV Channels","")
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
            Globals.REAL_SETTINGS.setSetting('Autotune', "False")
            Globals.REAL_SETTINGS.setSetting('Warning', "False")

            if currentchan > 1:
                return True

            return False


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
   