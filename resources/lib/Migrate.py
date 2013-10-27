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
            self.log("autoTune")
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
        self.log('autoTune')
        chanlist = ChannelList.ChannelList()
        chanlist.needsreset = True
        chanlist.makenewlists = True
        # chanlist.createlist = True
        chanlist.background = True
        # self.clearPlaylistHistory(channel)
        
        # delete settings2.xml
        # settingsFile = xbmc.translatePath(os.path.join(SETTINGS_LOC, 'settings2.xml'))
        
        # if  FileAccess.exists(settingsFile):
            # try:
                # os.remove(settingsFile)
            # except:
                # self.log("Unable to delete " + str(settingsFile))

        channelNum = 0
        
        self.updateDialog = xbmcgui.DialogProgress()
        self.updateDialog.create("PseudoTV Live", "Auto Tune")
        
        # LiveTV - Hdhomerun
        self.updateDialogProgress = 10

        # LiveTV - USTVNOW
        self.updateDialogProgress = 15
        if Globals.REAL_SETTINGS.getSetting("autoFindLive") == "true" and Globals.REAL_SETTINGS.getSetting("autoFindLiveUSTVnow") == "true" :
            self.log("Adding Live USTVnow Channel")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding USTVnow Channel","")
            for i in range(1):
                channelNum = channelNum + 1
                # add ustvnow presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "I27.28460898.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "plugin://plugin.video.ustvnow/?name=ABC&mode=play")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "ABC USTVNOW")  
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_1", "I21.28459588.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_2", "plugin://plugin.video.ustvnow/?name=CBS&mode=play")    
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 1) + "_rule_1_opt_1", "CBS USTVNOW") 
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum + 1) + '_changed', 'true')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_1", "I15.28461494.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_2", "plugin://plugin.video.ustvnow/?name=CW&mode=play")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 2) + "_rule_1_opt_1", "CW USTVNOW")
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum + 2) + '_changed', 'true')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_1", "I43.28457987.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_2", "plugin://plugin.video.ustvnow/?name=FOX&mode=play")   
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 3) + "_rule_1_opt_1", "FOX USTVNOW")  
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum + 3) + '_changed', 'true')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_1", "I8.28460167.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_2", "plugin://plugin.video.ustvnow/?name=NBC&mode=play")     
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 4) + "_rule_1_opt_1", "NBC USTVNOW")  
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum + 4) + '_changed', 'true')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_1", "I33.28455626.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_2", "plugin://plugin.video.ustvnow/?name=PBS&mode=play")   
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 5) + "_rule_1_opt_1", "PBS USTVNOW")
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum + 5) + '_changed', 'true')
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_type", "8")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_1", "I238.28455933.microsoft.com")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_2", "plugin://plugin.video.ustvnow/?name=My9&mode=play")  
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_3", "ustvnow")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum + 6) + "_rule_1_opt_1", "MY9 USTVNOW")  
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum + 6) + '_changed', 'true')

        
        #TV - Networks/Genres
        self.updateDialogProgress = 20
        self.log("autoFindNetworks " + str(Globals.REAL_SETTINGS.getSetting("autoFindNetworks")))
        self.log("autoFindTVGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindTVGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true"):
            self.log("Searching for TV Channels")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for TV Channels","")
            chanlist.fillTVInfo()

        # need to add check for auto find network channels
        self.updateDialogProgress = 25
        if Globals.REAL_SETTINGS.getSetting("autoFindNetworks") == "true":
            self.log("Adding TV Networks")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Networks","")
            for i in range(len(chanlist.networkList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.networkList[i]))
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Network",str(chanlist.networkList[i]))

        self.updateDialogProgress = 30
        if Globals.REAL_SETTINGS.getSetting("autoFindTVGenres") == "true":
            self.log("Adding TV Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres","")
            for i in range(len(chanlist.showGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "3")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.showGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding TV Genres",str(chanlist.showGenreList[i]) + " TV")
        
        self.updateDialogProgress = 40
        self.log("autoFindStudios " + str(Globals.REAL_SETTINGS.getSetting("autoFindStudios")))
        self.log("autoFindMovieGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres")))
        if (Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true" or Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true"):
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Movie Channels","")
            chanlist.fillMovieInfo()

        self.updateDialogProgress = 50
        if Globals.REAL_SETTINGS.getSetting("autoFindStudios") == "true":
            self.log("Adding Movie Studios")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios","")
            for i in range(len(chanlist.studioList)):
                channelNum = channelNum + 1
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.studioList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "2")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.studioList[i]))
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Studios",str(chanlist.studioList[i]))

        self.updateDialogProgress = 60
        if Globals.REAL_SETTINGS.getSetting("autoFindMovieGenres") == "true":
            self.log("Adding Movie Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","")
            for i in range(len(chanlist.movieGenreList)):
                channelNum = channelNum + 1
                self.updateDialogProgress = self.updateDialogProgress + (10/len(chanlist.movieGenreList))
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "4")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.movieGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Movie Genres","Found " + str(chanlist.movieGenreList[i]) + " Movies")

        self.updateDialogProgress = 65
        self.log("autoFindMixGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMixGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Mixed Channels","")
            chanlist.fillMixedGenreInfo()
        
        self.updateDialogProgress = 70
        if Globals.REAL_SETTINGS.getSetting("autoFindMixGenres") == "true":
            self.log("Adding Mixed Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres","")
            for i in range(len(chanlist.mixedGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "5")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.mixedGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Mixed Genres",str(chanlist.mixedGenreList[i]) + " Mix")

        self.updateDialogProgress = 80
        self.log("autoFindMusicGenres " + str(Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres")))
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Searching for Music Channels","")
            chanlist.fillMusicInfo()

        self.updateDialogProgress = 85
        #Music Genre
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicGenres") == "true":
            self.log("Adding Music Genres")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres","")
            for i in range(len(chanlist.musicGenreList)):
                channelNum = channelNum + 1
                # add network presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "12")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", str(chanlist.musicGenreList[i]))
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "0")
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
                self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Genres",str(chanlist.musicGenreList[i]) + " Music")

        self.updateDialogProgress = 90
        #Music Videos
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideos") == "true" and Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosVevoTV") == "true":
            self.log("Adding Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Videos","")
            for i in range(1):
                channelNum = channelNum + 1
                # add VevoTV presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "9")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "5400")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_2", "rtmp://vevohp2livefs.fplive.net:1935/vevohp2live-live/ playpath=stream2272000 swfUrl=http://cache.vevo.com/livepassdl.conviva.com/ver/2.64.0.68610/LivePassModuleMain_osmf.swf")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_3", "VevoTV")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_4", "Sit back and enjoy a 24/7 stream of music videos on VEVO TV.")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "VevoTV")  
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')
        self.updateDialogProgress = 95
        
        if Globals.REAL_SETTINGS.getSetting("autoFindMusicVideos") == "true" and Globals.REAL_SETTINGS.getSetting("autoFindMusicVideosLocal") != None:
            self.log("Adding Music Videos")
            self.updateDialog.update(self.updateDialogProgress,"Auto Tune","Adding Music Videos","")
            LocalVideo = str(Globals.REAL_SETTINGS.getSetting('autoFindMusicVideosLocal'))
            for i in range(1):
                channelNum = channelNum + 1
                # add Local presets
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_type", "7")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_time", "0")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_1", "" +LocalVideo+ "")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rulecount", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_id", "1")
                Globals.ADDON_SETTINGS.setSetting("Channel_" + str(channelNum) + "_rule_1_opt_1", "Music Videos")  
                Globals.ADDON_SETTINGS.setSetting('Channel_' + str(channelNum) + '_changed', 'true')

        Globals.ADDON_SETTINGS.writeSettings()

        #set max channels
        # chanlist.MaxChannels()

        # reset auto tune settings
        Globals.REAL_SETTINGS.setSetting("autoFindNetworks","false")
        Globals.REAL_SETTINGS.setSetting("autoFindStudios","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMovieGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMixGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindTVShows","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicGenres","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideos","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosYoutube","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosVevoTV","false")
        Globals.REAL_SETTINGS.setSetting("autoFindMusicVideosLocal","")
        Globals.REAL_SETTINGS.setSetting("autoFindLive","false")
        Globals.REAL_SETTINGS.setSetting('autoFindLiveUSTVnow', "false")
        Globals.REAL_SETTINGS.setSetting('Warning1', "false")
        Globals.REAL_SETTINGS.setSetting('Autotune', "false")
        
        # force a reset
        Globals.REAL_SETTINGS.setSetting("ForceChannelReset","true")
        
        self.updateDialog.close()
    
    # Old PTV tuning...
    # def initializeChannels(self):
        # updatedlg = xbmcgui.DialogProgress()
        # updatedlg.create("PseudoTV", "Initializing")
        # updatedlg.update(1, "Initializing", "Initial Channel Setup")
        # chanlist = ChannelList.ChannelList()
        # chanlist.background = True
        # chanlist.fillTVInfo(True)
        # updatedlg.update(30)
        # chanlist.fillMovieInfo(True)
        # updatedlg.update(60)
        # # Now create TV networks, followed by mixed genres, followed by TV genres, and finally movie genres
        # currentchan = 1
        # mixedlist = []

        # for item in chanlist.showGenreList:
            # curitem = item[0].lower()

            # for a in chanlist.movieGenreList:
                # if curitem == a[0].lower():
                    # mixedlist.append([item[0], item[1], a[1]])
                    # break

        # mixedlist.sort(key=lambda x: x[1] + x[2], reverse=True)
        # currentchan = self.initialAddChannels(chanlist.networkList, 1, currentchan)
        # updatedlg.update(70)

        # # Mixed genres
        # if len(mixedlist) > 0:
            # added = 0.0

            # for item in mixedlist:
                # if item[1] > 2 and item[2] > 1:
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_type", "5")
                    # Globals.ADDON_SETTINGS.setSetting("Channel_" + str(currentchan) + "_1", item[0])
                    # added += 1.0
                    # currentchan += 1
                    # itemlow = item[0].lower()

                    # # Remove that genre from the shows genre list
                    # for i in range(len(chanlist.showGenreList)):
                        # if itemlow == chanlist.showGenreList[i][0].lower():
                            # chanlist.showGenreList.pop(i)
                            # break

                    # # Remove that genre from the movie genre list
                    # for i in range(len(chanlist.movieGenreList)):
                        # if itemlow == chanlist.movieGenreList[i][0].lower():
                            # chanlist.movieGenreList.pop(i)
                            # break

                    # if added > 10:
                        # break

                    # updatedlg.update(int(70 + 10.0 / added))

        # updatedlg.update(80)
        # currentchan = self.initialAddChannels(chanlist.showGenreList, 3, currentchan)
        # updatedlg.update(90)
        # currentchan = self.initialAddChannels(chanlist.movieGenreList, 4, currentchan)
        # updatedlg.close()

        # if currentchan > 1:
            # return True

        # return False
        
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
   