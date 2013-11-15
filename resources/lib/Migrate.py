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
        
        # If Autotune is enabled direct to autotuning
        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":
            self.log("autoTune, migrate")
            if self.autoTune():
                return True
        else:
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
            
              
    def autoTune(self):
        self.log('autoTune, Init')
        chanlist = ChannelList.ChannelList()
        chanlist.background = True
        chanlist.needsreset = True
        chanlist.makenewlists = True
        # chanlist.createlist = True
        
        UserPass = Globals.REAL_SETTINGS.getSetting('Donor_UP')
        # self.log("autoTune, Donor VIP User:Password = " + str(UserPass))
        
        # delete settings2.xml
        settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))
        
        if  FileAccess.exists(settingsFile):
            try:
                os.remove(settingsFile)
            except:
                self.log("autoTune, Unable to delete " + str(settingsFile))

        ## If channelNum == maxchannel todo ##
        channelNum = 0
        # currentchan = 0
        updateDialogProgress = 0
        
        self.updateDialog = xbmcgui.DialogProgress()
        self.updateDialog.create("PseudoTV Live", "Auto Tune")
        
        # LiveTV - USTVNOW
        self.updateDialogProgress = 5
        if Globals.REAL_SETTINGS.getSetting("autoFindLiveUSTVnow") == "true" :
            id = 'plugin.video.ustvnow'
            try:
                xbmcaddon.Addon(id)
                installed = True
            except Exception:
                installed = False

            if installed == True:
                self.log("autoTune, Adding Live USTVnow Channel")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding USTVnow Channel","")
                for i in range(1):
                    # add ustvnow presets
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "I27.28460898.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "plugin://plugin.video.ustvnow/?name=ABC&mode=play")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "ABC USTVNOW")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "I21.28459588.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_2", "plugin://plugin.video.ustvnow/?name=CBS&mode=play")    
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "CBS USTVNOW") 
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_1", "I15.28461494.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_2", "plugin://plugin.video.ustvnow/?name=CW&mode=play")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_opt_1", "CW USTVNOW")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_1", "I43.28457987.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_2", "plugin://plugin.video.ustvnow/?name=FOX&mode=play")   
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_rule_1_opt_1", "FOX USTVNOW")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_1", "I8.28460167.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_2", "plugin://plugin.video.ustvnow/?name=NBC&mode=play")     
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_rule_1_opt_1", "NBC USTVNOW")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_1", "I33.28455626.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_2", "plugin://plugin.video.ustvnow/?name=PBS&mode=play")   
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_rule_1_opt_1", "PBS USTVNOW")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_type", "8")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_1", "I238.28455933.microsoft.com")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_2", "plugin://plugin.video.ustvnow/?name=My9&mode=play")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_3", "ustvnow")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_rule_1_opt_1", "MY9 USTVNOW")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 7) + "_changed", "true")
        
            channelNum = channelNum + 7
        
        # LiveTV - Hdhomerun
        self.updateDialogProgress = 10
        
        # Custom Channels
        self.updateDialogProgress = 20
        if Globals.REAL_SETTINGS.getSetting("autoFindCustom") == "true" :
            self.log("autoTune, Adding Custom Channel")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Custom Channel","")
            for i in range(500):
                if os.path.exists(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Video Playlist Channel")
                    channelNum = channelNum + 1
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/video/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", str(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + str(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/video') + '/Channel_' + str(i + 1) + '.xsp')),"")
                elif os.path.exists(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Mixed Playlist Channel")
                    channelNum = channelNum + 1
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/mixed/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", str(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + str(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/mixed') + '/Channel_' + str(i + 1) + '.xsp')),"")
                elif os.path.exists(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'):
                    self.log("autoTune, Adding Custom Music Playlist Channel")
                    channelNum = channelNum + 1
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(xbmc.translatePath('special://profile/playlists/music/') + "Channel_" + str(i + 1) + '.xsp'))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", str(chanlist.cleanString(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp'))))
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                    self.updateDialog.update(self.updateDialogProgress,"PseudoTV Live","Found " + str(chanlist.getSmartPlaylistName(xbmc.translatePath('special://profile/playlists/music') + '/Channel_' + str(i + 1) + '.xsp')),"")
        
            channelNum = channelNum
        
        #TV - Networks/Genres
        self.updateDialogProgress = 25
        self.log("autoTune, autoFindNetworks " + str(Globals.REAL_SETTINGS.getSetting("autoFindNetworks")))
        self.log("autoTune, autoFindTVGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindTVGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.log("autoTune, Searching for TV Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for TV Channels","")
            chanlist.fillTVInfo()

        # need to add check for auto find network channels
        self.updateDialogProgress = 28
        if Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.log("autoTune, Adding TV Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Networks","")
            # currentchan = self.initialAddChannels(chanlist.networkList, 1, currentchan)
            for i in range(len(chanlist.networkList)):
                # channelNum = currentchan
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.networkList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Network",str(chanlist.networkList[i]))
        
            channelNum = channelNum
        
        self.updateDialogProgress = 30
        if Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.log("autoTune, Adding TV Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres","")
            for i in range(len(chanlist.showGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.showGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres",str(chanlist.showGenreList[i]) + " TV")
        
            channelNum = channelNum
        
        self.updateDialogProgress = 35
        self.log("autoTune, autoFindStudios " + str(Globals.REAL_SETTINGS.getSetting("autoFindStudios")))
        self.log("autoTune, autoFindMovieGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Movie Channels","")
            chanlist.fillMovieInfo()

        self.updateDialogProgress = 38
        if Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.log("autoTune, Adding Movie Studios")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios","")
            for i in range(len(chanlist.studioList)):
                channelNum = channelNum + 1
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.studioList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.studioList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios",str(chanlist.studioList[i]))

            channelNum = channelNum
        
        self.updateDialogProgress = 40
        if Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.log("autoTune, Adding Movie Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","")
            for i in range(len(chanlist.movieGenreList)):
                channelNum = channelNum + 1
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.movieGenreList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.movieGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","Found " + str(chanlist.movieGenreList[i]) + " Movies")
        
            channelNum = channelNum
        
        self.updateDialogProgress = 45
        self.log("autoTune, autoFindMixGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMixGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Mixed Channels","")
            chanlist.fillMixedGenreInfo()
        
        self.updateDialogProgress = 48
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.log("autoTune, Adding Mixed Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres","")
            for i in range(len(chanlist.mixedGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.mixedGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres",str(chanlist.mixedGenreList[i]) + " Mix")

            channelNum = channelNum
        
        self.updateDialogProgress = 55
        self.log("autoTune, autoFindMusicGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Music Channels","")
            chanlist.fillMusicInfo()

        self.updateDialogProgress = 58
        #Music Genre
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.log("autoTune, Adding Music Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres","")
            for i in range(len(chanlist.musicGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "12")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.musicGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_changed", "true")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres",str(chanlist.musicGenreList[i]) + " Music")
        
            channelNum = channelNum
        
        #Music Videos - Last.fm user
        self.updateDialogProgress = 60
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastFM") == "true":
            self.log("autoTune, Adding Last.FM Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Last.FM Music Videos","")
            user = Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLastfmUser")
            lastapi = "http://api.tv.timbormans.com/user/"+user+"/topartists.xml"
            for i in range(1):
                # add Last.fm user presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "13")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "rtmp://vevohp2livefs.fplive.net:1935/vevohp2live-live/ playpath=stream2272000 swfUrl=http://cache.vevo.com/livepassdl.conviva.com/ver/2.64.0.68610/LivePassModuleMain_osmf.swf")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "VevoTV")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "Last.fm")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
       
            channelNum = channelNum
        
        #Music Videos - Youtube
        self.updateDialogProgress = 62
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosYoutube") == "true":
            self.log("autoTune, Adding Youtube Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Youtube Music Videos","")
            for i in range(1):
                # add HungaryRChart presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "HungaryRChart")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "HRChart")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                # add BillbostdHot100 presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "BillbostdHot100")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "BillbostdHot100")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")
                # add TheTesteeTop50Charts presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_type", "10")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_1", "TheTesteeTop50Charts")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_2", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_3", "50")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_opt_1", "TheTesteeTop50Charts")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_changed", "true")
        
            channelNum = channelNum + 3
        
        #Music Videos - VevoTV
        self.updateDialogProgress = 64
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosVevoTV") == "true":
            self.log("autoTune, Adding VevoTV Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding VevoTV Music Videos","")
            for i in range(1):
                # add VevoTV presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "rtmp://vevohp2livefs.fplive.net:1935/vevohp2live-live/ playpath=stream2272000 swfUrl=http://cache.vevo.com/livepassdl.conviva.com/ver/2.64.0.68610/LivePassModuleMain_osmf.swf")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "VevoTV")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "VevoTV")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")

            channelNum = channelNum + 1
        
        #Music Videos - Local
        self.updateDialogProgress = 68
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal") != "":
            self.log("autoTune, Adding Local Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Local Music Videos","")
            LocalVideo = str(Globals.REAL_SETTINGS.getSetting('autoFindMusicVideosLocal'))
            for i in range(1):
                # add Local presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +LocalVideo+ "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "Music Videos")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")        

            channelNum = channelNum + 1
        
        #InternetTV - Strms
        self.updateDialogProgress = 85
        if Globals.REAL_SETTINGS.getSetting("autoFindInternetStrms") == "true":
            self.log("autoTune, Adding InternetTV Strms")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV Strms","")
            InternetStrms = str('http://whufclee.googlecode.com/svn/whufclee_public/TVGuides/DixieDean/Streams/')
            for i in range(1):
                # add InternetTV
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +InternetStrms+ "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "InternetTV Strms")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")

            channelNum = channelNum + 1
        
        if Globals.REAL_SETTINGS.getSetting("autoFindInternetStrms") == "true" and Globals.REAL_SETTINGS.getSetting("Donor_Enabled") == "true":
            id = 'plugin.video.tgun'
            try:
                xbmcaddon.Addon(id)
                installed = True
            except Exception:
                installed = False

            if installed == True:
                self.log("autoTune, Adding InternetTV TGUN")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from TGUN","")
                InternetTgunTVMovies = str('http://'+UserPass+'@ptvl.comeze.com/strms/TGUN.-.TVMovies/')
                InternetTgunClassicTV = str('http://'+UserPass+'@ptvl.comeze.com/strms/TGUN.-.ClassicTV/')
                for i in range(1):
                    # add TGUN
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +InternetTgunTVMovies+ "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "TGUN - TV/Movies")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "7")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "" +InternetTgunClassicTV+ "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "TGUN - ClassicTV")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")

            channelNum = channelNum + 2           
                    
        if Globals.REAL_SETTINGS.getSetting("autoFindInternetStrms") == "true" and Globals.REAL_SETTINGS.getSetting("Donor_Enabled") == "true":
            id = 'plugin.video.jtv.archives'            
            try:
                xbmcaddon.Addon(id)
                installed = True
            except Exception:
                installed = False

            if installed == True:
                self.log("autoTune, Adding InternetTV JTV")
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding InternetTV from JTV","")
                InternetJTVDocumentary = str('http://'+UserPass+'@ptvl.comeze.com/strms/JTV.-.Documentary/')
                InternetJTVMovies = str('http://'+UserPass+'@ptvl.comeze.com/strms/JTV.-.Movies/')
                InternetJTVSeries = str('http://'+UserPass+'@ptvl.comeze.com/strms/JTV.-.Series/')
                for i in range(1):
                    # add JTV
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "7")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "" +InternetJTVDocumentary+ "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "JTV - Documentary")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "7")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "" +InternetJTVMovies+ "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "JTV - Movies")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_changed", "true")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_type", "7")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_time", "0")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_1", "" +InternetJTVSeries+ "")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rulecount", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_id", "1")
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_opt_1", "JTV - Series")  
                    Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_changed", "true")

            channelNum = channelNum + 3
        
        Globals.ADDON_SETTINGS.writeSettings()

        #set max channels
        # chanlist.setMaxChannels()
        
        self.updateDialogProgress = 100
        # reset auto tune settings        
        Globals.REAL_SETTINGS.setSetting('Autotune', "false")
        Globals.REAL_SETTINGS.setSetting('Warning1', "false")
        Globals.REAL_SETTINGS.setSetting('autoFindLiveUSTVnow', "false")
        Globals.REAL_SETTINGS.setSetting("autoFindLiveHDhomerun","false")
        Globals.REAL_SETTINGS.setSetting("autoFindCustom","false")
        Globals.REAL_SETTINGS.setSetting("autoFindNetworks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindStudios","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMixGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVShows","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLastFM","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLocal","")
        Globals.REAL_SETTINGS.setSetting("autoFindInternetStrms","false")
        
        # force a reset
        Globals.REAL_SETTINGS.setSetting("ForceChannelReset","true")
        
        self.updateDialog.close()


    ##### TV-Guide addons.ini prasing * Thanks Tommy Winther ##### todo #####
    # def Addons(self):
        # path = xbmc.translatePath(os.path.join(Globals.REAL_SETTINGS.getSetting('Addons'), 'addons.ini'))
        # self.addonsParser = ConfigParser.ConfigParser(dict_type=OrderedDict)
        # self.addonsParser.optionxform = lambda option: option
        # try:
            # self.addonsParser.read(path)
        # except:
            # print 'unable to parse addons.ini'

    #############################################   

    ##### TheStreamDB prasing todo #####
    # def Livestream(self):
    # thestreamdb = http://thestreamdb.com/all.xml
    
    # try:
        # self.thestreamdb = url      
    # except:
        # self.log("")
        # return
    
    # f = urlopen(url)        
           
    ############################################
           
    # Last.fm Music Videos **TODO**    
    # def LastFM(self):
        # api = "http://api.tv.timbormans.com/user/"+user+"/topartists.xml"
        # user = REAL_SETTINGS.getSetting('autoFindMusicVideosLastfmUser')
        # url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid='+url"
        
        # Sample xml output:
        # <clip>
            # <artist url="http://www.last.fm/music/Tears+for+Fears">Tears for Fears</artist>
            # <track url="http://www.last.fm/music/Tears+for+Fears/_/Everybody+Wants+to+Rule+the+World">Everybody Wants to Rule the World</track>
            # <url>http://www.youtube.com/watch?v=ST86JM1RPl0&amp;feature=youtube_gdata_player</url>
            # <duration>191</duration>
            # <thumbnail>http://i.ytimg.com/vi/ST86JM1RPl0/0.jpg</thumbnail>
            # <rating max="5">4.9660454</rating>
            # <stats hits="1" misses="4" />
        # </clip>
        
        #for loop
        #Call api
        #Parse data (artist,track,url,duration)
        #Append tmpstr data
        #repeat
    
    
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



        