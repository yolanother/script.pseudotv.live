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
import httplib
import base64
import Globals
import urllib2 
import feedparser
import tvdb_api
import tmdbsimple
import shutil
# import json 
# try:
    # import StorageServer
# except:
   # import storageserverdummy as StorageServer

   # cache = StorageServer.StorageServer(ADDON_ID, 24) # (Your plugin name, Cache time in hours)


from urllib import unquote
from urllib import urlopen
from xml.etree import ElementTree as ET
from xml.dom.minidom import parse, parseString
from subprocess import Popen, PIPE, STDOUT

from Playlist import Playlist
from Globals import *
from Channel import Channel
from VideoParser import VideoParser
from FileAccess import FileLock, FileAccess
from sickbeard import *
from couchpotato import *
from tvdb import *
from tmdb import *


class ChannelList:
    def __init__(self):
        self.networkList = []
        self.studioList = []
        self.mixedGenreList = []
        self.showGenreList = []
        self.movieGenreList = []
        self.musicGenreList = []
        self.showList = []
        self.channels = []
        self.videoParser = VideoParser()
        self.httpJSON = True
        self.sleepTime = 0
        self.discoveredWebServer = False
        self.threadPaused = False
        self.runningActionChannel = 0
        self.runningActionId = 0
        self.enteredChannelCount = 0
        self.background = True
        random.seed()
        self.cached_json_detailed_TV = []
        self.cached_json_detailed_Movie = []


    def readConfig(self):
        self.channelResetSetting = int(REAL_SETTINGS.getSetting("ChannelResetSetting"))
        self.log('Channel Reset Setting is ' + str(self.channelResetSetting))
        self.forceReset = REAL_SETTINGS.getSetting('ForceChannelReset') == "true"
        self.log('Force Reset is ' + str(self.forceReset))
        self.updateDialog = xbmcgui.DialogProgress()
        self.startMode = int(REAL_SETTINGS.getSetting("StartMode"))
        self.log('Start Mode is ' + str(self.startMode))
        self.backgroundUpdating = int(REAL_SETTINGS.getSetting("ThreadMode"))
        self.incIceLibrary = REAL_SETTINGS.setSetting('IncludeIceLib', "true")
        self.incIceLibrary = REAL_SETTINGS.getSetting('IncludeIceLib') == "true"
        self.log("IceLibrary is " + str(self.incIceLibrary))
        self.showSeasonEpisode = REAL_SETTINGS.getSetting("ShowSeEp") == "true"
        self.findMaxChannels()

        if self.forceReset:
            REAL_SETTINGS.setSetting('ForceChannelReset', "False")
            self.forceReset = False

        try:
            self.lastResetTime = int(ADDON_SETTINGS.getSetting("LastResetTime"))
        except:
            self.lastResetTime = 0

        try:
            self.lastExitTime = int(ADDON_SETTINGS.getSetting("LastExitTime"))
        except:
            self.lastExitTime = int(time.time())


    def setupList(self):
        self.readConfig()
        self.updateDialog.create("PseudoTV Live", "Updating channel list")
        self.updateDialog.update(0, "Updating channel list")
        self.updateDialogProgress = 0
        foundvalid = False
        makenewlists = False
        self.background = False

        if self.backgroundUpdating > 0 and self.myOverlay.isMaster == True:
            makenewlists = True

        # Go through all channels, create their arrays, and setup the new playlist
        for i in range(self.maxChannels):
            self.updateDialogProgress = i * 100 // self.enteredChannelCount
            self.updateDialog.update(self.updateDialogProgress, "Loading channel " + str(i + 1), "waiting for file lock")
            self.channels.append(Channel())

            # If the user pressed cancel, stop everything and exit
            if self.updateDialog.iscanceled():
                self.log('Update channels cancelled')
                self.updateDialog.close()
                return None

            self.setupChannel(i + 1, False, makenewlists, False)

            if self.channels[i].isValid:
                foundvalid = True

        if makenewlists == True:
            REAL_SETTINGS.setSetting('ForceChannelReset', 'false')

        if foundvalid == False and makenewlists == False:
            for i in range(self.maxChannels):
                self.updateDialogProgress = i * 100 // self.enteredChannelCount
                self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(i + 1), "waiting for file lock", '')
                self.setupChannel(i + 1, False, True, False)

                if self.channels[i].isValid:
                    foundvalid = True
                    break


        self.updateDialog.update(100, "Update complete")
        self.updateDialog.close()

        return self.channels



    def log(self, msg, level = xbmc.LOGDEBUG):
        log('ChannelList: ' + msg, level)

    def logDebug(self, msg, level = xbmc.LOGDEBUG):
        if REAL_SETTINGS.getSetting('enable_Debug') == "true":
            log('ChannelList: ' + msg, level)
                    
    # Determine the maximum number of channels by opening consecutive
    # playlists until we don't find one
    def findMaxChannels(self):
        self.log('findMaxChannels')
        self.maxChannels = 0
        self.enteredChannelCount = 0

        for i in range(999):
            chtype = 9999
            chsetting1 = ''
            chsetting2 = ''
            chsetting3 = ''
            chsetting4 = ''

            try:
                chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_type'))
                chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_1')
                chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_2')
                chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_3')
                chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(i + 1) + '_4')
            except:
                pass

            if chtype == 0:
                if FileAccess.exists(xbmc.translatePath(chsetting1)):
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
            elif chtype <= 12:
                if len(chsetting1) > 0:
                    self.maxChannels = i + 1
                    self.enteredChannelCount += 1
                    
            if self.forceReset and (chtype != 9999):
                ADDON_SETTINGS.setSetting('Channel_' + str(i + 1) + '_changed', "True")

        self.log('findMaxChannels return ' + str(self.maxChannels))


    def determineWebServer(self):
        if self.discoveredWebServer:
            return

        self.discoveredWebServer = True
        self.webPort = 8080
        self.webUsername = ''
        self.webPassword = ''
        fle = xbmc.translatePath("special://profile/guisettings.xml")

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log("determineWebServer Unable to open the settings file", xbmc.LOGERROR)
            self.httpJSON = False
            return

        try:
            dom = parse(xml)
        except:
            self.log('determineWebServer Unable to parse settings file', xbmc.LOGERROR)
            self.httpJSON = False
            return

        xml.close()

        try:
            plname = dom.getElementsByTagName('webserver')
            self.httpJSON = (plname[0].childNodes[0].nodeValue.lower() == 'true')
            self.log('determineWebServer is ' + str(self.httpJSON))

            if self.httpJSON == True:
                plname = dom.getElementsByTagName('webserverport')
                self.webPort = int(plname[0].childNodes[0].nodeValue)
                self.log('determineWebServer port ' + str(self.webPort))
                plname = dom.getElementsByTagName('webserverusername')
                self.webUsername = plname[0].childNodes[0].nodeValue
                self.log('determineWebServer username ' + self.webUsername)
                plname = dom.getElementsByTagName('webserverpassword')
                self.webPassword = plname[0].childNodes[0].nodeValue
                self.log('determineWebServer password is ' + self.webPassword)
        except:
            return


    # Code for sending JSON through http adapted from code by sffjunkie (forum.xbmc.org/showthread.php?t=92196)
    def sendJSON(self, command):
        self.log('sendJSON')
        data = ''
        usedhttp = False

        self.determineWebServer()

        if USING_EDEN:
            command = command.replace('fields', 'properties')

        self.log('sendJSON command: ' + command)

        # If there have been problems using the server, just skip the attempt and use executejsonrpc
        if self.httpJSON == True:
            try:
                payload = command.encode('utf-8')
            except:
                return data

            headers = {'Content-Type': 'application/json-rpc; charset=utf-8'}

            if self.webUsername != '':
                userpass = base64.encodestring('%s:%s' % (self.webUsername, self.webPassword))[:-1]
                headers['Authorization'] = 'Basic %s' % userpass

            try:
                conn = httplib.HTTPConnection('127.0.0.1', self.webPort)
                conn.request('POST', '/jsonrpc', payload, headers)
                response = conn.getresponse()

                if response.status == 200:
                    data = uni(response.read())
                    usedhttp = True

                conn.close()
            except:
                self.log("Exception when getting JSON data")

        if usedhttp == False:
            self.httpJSON = False
            
            try:
                data = xbmc.executeJSONRPC(uni(command))
            except UnicodeEncodeError:
                data = xbmc.executeJSONRPC(ascii(command))

        return uni(data)


    def setupChannel(self, channel, background = False, makenewlist = False, append = False):
        self.log('setupChannel ' + str(channel))
        returnval = False
        createlist = makenewlist
        chtype = 9999
        chsetting1 = ''
        chsetting2 = ''
        chsetting3 = ''
        chsetting4 = ''
        needsreset = False
        self.background = background
        self.settingChannel = channel

        try:
            chtype = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_type'))
            chsetting1 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_1')
            chsetting2 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_2')
            chsetting3 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_3')
            chsetting4 = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_4')

        except:
            pass

        while len(self.channels) < channel:
            self.channels.append(Channel())

        if chtype == 9999:
            self.channels[channel - 1].isValid = False
            return False

        self.channels[channel - 1].type = chtype
        self.channels[channel - 1].isSetup = True
        self.channels[channel - 1].loadRules(channel)
        self.runActions(RULES_ACTION_START, channel, self.channels[channel - 1])

        try:
            needsreset = ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_changed') == 'True'
            
            # #disable force rebuild for livetv channels w/ TVDB and TMDB, else force rebuild:
            # if chtype == 8:
                # if (REAL_SETTINGS.getSetting('ForceChannelReset') == 'true' and (REAL_SETTINGS.getSetting('tvdb.enabled') == 'false' or REAL_SETTINGS.getSetting('tmdb.enabled') == 'false')):
                    # self.log("Force LiveTV rebuild - Disabled")
                    # needsreset = True
                    # makenewlist = True

            # if chtype == 9:
                # needsreset = True
                # makenewlist = True
            
            if needsreset:
                self.channels[channel - 1].isSetup = False
        except:
            pass

        # If possible, use an existing playlist
        # Don't do this if we're appending an existing channel
        # Don't load if we need to reset anyway
        if FileAccess.exists(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') and append == False and needsreset == False:
            try:
                self.channels[channel - 1].totalTimePlayed = int(ADDON_SETTINGS.getSetting('Channel_' + str(channel) + '_time', True))
                createlist = True

                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, "Loading channel " + str(channel), "reading playlist", '')

                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    self.channels[channel - 1].isValid = True
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    returnval = True

                    # If this channel has been watched for longer than it lasts, reset the channel
                    if self.channelResetSetting == 0 and self.channels[channel - 1].totalTimePlayed < self.channels[channel - 1].getTotalDuration():
                        createlist = False

                    if self.channelResetSetting > 0 and self.channelResetSetting < 4:
                        timedif = time.time() - self.lastResetTime

                        if self.channelResetSetting == 1 and timedif < (60 * 60 * 24):
                            createlist = False

                        if self.channelResetSetting == 2 and timedif < (60 * 60 * 24 * 7):
                            createlist = False

                        if self.channelResetSetting == 3 and timedif < (60 * 60 * 24 * 30):
                            createlist = False

                        if timedif < 0:
                            createlist = False

                    if self.channelResetSetting == 4:
                        createlist = False
            except:
                pass

        if createlist or needsreset:
            self.channels[channel - 1].isValid = False

            if makenewlist:
            
                try:#clean artwork folder
                    artworkLOC = (xbmc.translatePath(os.path.join(CHANNELS_LOC, 'generated')  + '/' + 'artwork' + '/'))
                    self.logDebug("artworkLOC = " + str(artworkLOC))
                    shutil.rmtree(artworkLOC)
                    self.log("artwork folder cleaned")
                except:
                    pass

                try:#remove old playlist
                    os.remove(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u')
                except:
                    pass

                append = False

                if createlist:
                    ADDON_SETTINGS.setSetting('LastResetTime', str(int(time.time())))

        if append == False:
            if chtype == 6 and chsetting2 == str(MODE_ORDERAIRDATE):
                self.channels[channel - 1].mode = MODE_ORDERAIRDATE

            # if there is no start mode in the channel mode flags, set it to the default
            if self.channels[channel - 1].mode & MODE_STARTMODES == 0:
                if self.startMode == 0:
                    self.channels[channel - 1].mode |= MODE_RESUME
                elif self.startMode == 1:
                    self.channels[channel - 1].mode |= MODE_REALTIME
                elif self.startMode == 2:
                    self.channels[channel - 1].mode |= MODE_RANDOM

        if ((createlist or needsreset) and makenewlist) or append:
            if self.background == False:
                self.updateDialogProgress = (channel - 1) * 100 // self.enteredChannelCount
                self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(channel), "adding videos", '')

            if self.makeChannelList(channel, chtype, chsetting1, chsetting2, chsetting3, chsetting4, append) == True:
                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == True:
                    returnval = True
                    self.channels[channel - 1].fileName = CHANNELS_LOC + 'channel_' + str(channel) + '.m3u'
                    self.channels[channel - 1].isValid = True

                    # Don't reset variables on an appending channel
                    if append == False:
                        self.channels[channel - 1].totalTimePlayed = 0
                        ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', '0')

                        if needsreset:
                            ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_changed', 'False')
                            self.channels[channel - 1].isSetup = True

        self.runActions(RULES_ACTION_BEFORE_CLEAR, channel, self.channels[channel - 1])

        # Don't clear history when appending channels
        if self.background == False and append == False and self.myOverlay.isMaster:
            self.updateDialogProgress = (channel - 1) * 100 // self.enteredChannelCount
            self.updateDialog.update(self.updateDialogProgress, "Loading channel " + str(channel), "clearing history", '')
            self.clearPlaylistHistory(channel)

        if append == False:
            self.runActions(RULES_ACTION_BEFORE_TIME, channel, self.channels[channel - 1])

            if self.channels[channel - 1].mode & MODE_ALWAYSPAUSE > 0:
                self.channels[channel - 1].isPaused = True

            if self.channels[channel - 1].mode & MODE_RANDOM > 0:
                self.channels[channel - 1].showTimeOffset = random.randint(0, self.channels[channel - 1].getTotalDuration())

            if self.channels[channel - 1].mode & MODE_REALTIME > 0:
                timedif = int(self.myOverlay.timeStarted) - self.lastExitTime
                self.channels[channel - 1].totalTimePlayed += timedif

            if self.channels[channel - 1].mode & MODE_RESUME > 0:
                self.channels[channel - 1].showTimeOffset = self.channels[channel - 1].totalTimePlayed
                self.channels[channel - 1].totalTimePlayed = 0

            while self.channels[channel - 1].showTimeOffset > self.channels[channel - 1].getCurrentDuration():
                self.channels[channel - 1].showTimeOffset -= self.channels[channel - 1].getCurrentDuration()
                self.channels[channel - 1].addShowPosition(1)

        self.channels[channel - 1].name = self.getChannelName(chtype, chsetting1)

        if ((createlist or needsreset) and makenewlist) and returnval:
            self.runActions(RULES_ACTION_FINAL_MADE, channel, self.channels[channel - 1])
        else:
            self.runActions(RULES_ACTION_FINAL_LOADED, channel, self.channels[channel - 1])

        return returnval

        
    def clearPlaylistHistory(self, channel):
        self.log("clearPlaylistHistory")

        if self.channels[channel - 1].isValid == False:
            self.log("channel not valid, ignoring")
            return

        # if we actually need to clear anything
        if self.channels[channel - 1].totalTimePlayed > (60 * 60 * 24 * 2):
            try:
                fle = FileAccess.open(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', 'w')
            except:
                self.log("clearPlaylistHistory Unable to open the smart playlist", xbmc.LOGERROR)
                return

            flewrite = uni("#EXTM3U\n")
            tottime = 0
            timeremoved = 0

            for i in range(self.channels[channel - 1].Playlist.size()):
                tottime += self.channels[channel - 1].getItemDuration(i)

                if tottime > (self.channels[channel - 1].totalTimePlayed - (60 * 60 * 12)):
                    tmpstr = str(self.channels[channel - 1].getItemDuration(i)) + ','
                    tmpstr += self.channels[channel - 1].getItemTitle(i) + "//" + self.channels[channel - 1].getItemEpisodeTitle(i) + "//" + self.channels[channel - 1].getItemDescription(i) + "//" + self.channels[channel - 1].getItemgenre(i) + "//" + self.channels[channel - 1].getItemtimestamp(i) + "//" + self.channels[channel - 1].getItemLiveID(i)
                    tmpstr = uni(tmpstr)
                    tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                    tmpstr = uni(tmpstr) + uni('\n') + uni(self.channels[channel - 1].getItemFilename(i))
                    flewrite += uni("#EXTINF:") + uni(tmpstr) + uni("\n")
                else:
                    timeremoved = tottime

            fle.write(flewrite)
            fle.close()

            if timeremoved > 0:
                if self.channels[channel - 1].setPlaylist(CHANNELS_LOC + 'channel_' + str(channel) + '.m3u') == False:
                    self.channels[channel - 1].isValid = False
                else:
                    self.channels[channel - 1].totalTimePlayed -= timeremoved
                    # Write this now so anything sharing the playlists will get the proper info
                    ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', str(self.channels[channel - 1].totalTimePlayed))


    def getChannelName(self, chtype, setting1):
        self.log('getChannelName ' + str(chtype))

        if len(setting1) == 0:
            return ''

        if chtype == 0:
            return self.getSmartPlaylistName(setting1)
        elif chtype == 1 or chtype == 2 or chtype == 5 or chtype == 6 or chtype == 12:
            return setting1
        elif chtype == 3:
            return setting1 + " TV"
        elif chtype == 4:
            return setting1 + " Movies"
        # elif chtype == 8:
            # return setting1 + " LiveTV"
        # elif chtype == 9:
            # return setting1 + " InternetTV"
        # elif chtype == 10:
            # return setting1 + " Youtube"
        # elif chtype == 11:
            # return setting1 + " RSS"
        # elif chtype == 12:
            # return setting1 + " Music"
        elif chtype == 7:
            if setting1[-1] == '/' or setting1[-1] == '\\':
                return os.path.split(setting1[:-1])[1]
            else:
                return os.path.split(setting1)[1]

        return ''


    # Open the smart playlist and read the name out of it...this is the channel name
    def getSmartPlaylistName(self, fle):
        self.log('getSmartPlaylistName')
        fle = xbmc.translatePath(fle)

        try:
            xml = FileAccess.open(fle, "r")
        except:
            self.log("getSmartPlaylisyName Unable to open the smart playlist " + fle, xbmc.LOGERROR)
            return ''

        try:
            dom = parse(xml)
        except:
            self.log('getSmartPlaylistName Problem parsing playlist ' + fle, xbmc.LOGERROR)
            xml.close()
            return ''

        xml.close()

        try:
            plname = dom.getElementsByTagName('name')
            self.log('getSmartPlaylistName return ' + plname[0].childNodes[0].nodeValue)
            return plname[0].childNodes[0].nodeValue
        except:
            self.log("Unable to get the playlist name.", xbmc.LOGERROR)
            return ''
    
    # Based on a smart playlist, create a normal playlist that can actually be used by us
    def makeChannelList(self, channel, chtype, setting1, setting2, setting3, setting4, append = False):
        self.log('makeChannelList, CHANNEL: ' + str(channel))
        israndom = False
        fileList = []

        if chtype == 7:
            fileList = self.createDirectoryPlaylist(setting1)
            israndom = True                    
     
        elif chtype == 8: # LiveTV
            self.log("Building LiveTV Channel, " + setting1 + " , " + setting2 + " , " + setting3)
            
            # HDhomerun #
            if setting2[0:9] == 'hdhomerun' and REAL_SETTINGS.getSetting('HdhomerunMaster') == "true":
                #If you're using a HDHomeRun Dual and want 1 Tuner assigned per instance of PseudoTV, 
                #this will ensure Master instance uses tuner0 and slave instance uses tuner1 *Thanks Blazin912*
                self.log("Building LiveTV using tuner0")
                setting2 = re.sub(r'\d/tuner\d',"0/tuner0",setting2)
            else:
                self.log("Building LiveTV using tuner1")
                setting2 = re.sub(r'\d/tuner\d',"1/tuner1",setting2)
            
            # Validate XMLTV Data #
            if setting3 != '':
                self.xmltv_ok(setting3)
            
            # Validate LiveTV Feed #
            if self.xmltvValid == True:
                #Override Checks# 
                if REAL_SETTINGS.getSetting('Override_ok') == "true":
                    self.log("Overriding Stream Validation")
                    fileList = self.buildLiveTVFileList(setting1, setting2, setting3, channel) 
                else:
                
                    if setting2[0:4] == 'rtmp' or setting2[0:5] == 'rtmpe':#rtmp check
                        self.rtmpDump(setting2)  
                        if self.rtmpValid == True:   
                            fileList = self.buildLiveTVFileList(setting1, setting2, setting3, channel)    
                        else:
                            self.log('makeChannelList, CHANNEL: ' + str(channel) + ', CHTYPE: ' + str(chtype), 'RTMP invalid: ' + str(setting2))
                            return    
                    
                    elif setting2[0:4] == 'http':#http check     
                        self.url_ok(setting2) 
                        if self.urlValid == True: 
                            fileList = self.buildLiveTVFileList(setting1, setting2, setting3, channel)    
                        else:
                            self.log('makeChannelList, CHANNEL: ' + str(channel) + ', CHTYPE: ' + str(chtype), 'HTTP invalid: ' + str(setting2))
                            return    
                
                    elif setting2[0:6] == 'plugin':#plugin check    
                        self.plugin_ok(setting2)
                        if self.PluginFound == True:
                            fileList = self.buildLiveTVFileList(setting1, setting2, setting3, channel)    
                        else:
                            self.log('makeChannelList, CHANNEL: ' + str(channel) + ', CHTYPE: ' + str(chtype), 'PLUGIN invalid: ' + str(setting2))
                            return
                    else:
                        fileList = self.buildLiveTVFileList(setting1, setting2, setting3, channel)   
            else:
                return
                
        elif chtype == 9: # InternetTV
            self.log("Building InternetTV Channel, " + setting1 + " , " + setting2 + " , " + setting3)
            
            #Override Checks# 
            if REAL_SETTINGS.getSetting('Override_ok') == "true":
                self.log("Overriding Stream Validation")
                fileList = self.buildInternetTVFileList(setting1, setting2, setting3, setting4, channel)
            else:
            
                if setting2[0:4] == 'rtmp':#rtmp check
                    self.rtmpDump(setting2)
                    if self.rtmpValid == True:
                        fileList = self.buildInternetTVFileList(setting1, setting2, setting3, setting4, channel)
                    else:
                        self.log('makeChannelList, CHANNEL: ' + str(channel) + ', CHTYPE: ' + str(chtype), 'RTMP invalid: ' + str(setting2))
                        return
       
                elif setting2[0:4] == 'http':#http check                
                    self.url_ok(setting2)
                    if self.urlValid == True:
                        fileList = self.buildInternetTVFileList(setting1, setting2, setting3, setting4, channel)
                    else:
                        self.log('makeChannelList, CHANNEL: ' + str(channel) + ', CHTYPE: ' + str(chtype), 'HTTP invalid: ' + str(setting2))
                        return   
                
                elif setting2[0:6] == 'plugin':#plugin check                
                    self.plugin_ok(setting2)
                    if self.PluginFound == True:
                        fileList = self.buildInternetTVFileList(setting1, setting2, setting3, setting4, channel)
                    else:
                        self.log('makeChannelList, CHANNEL: ' + str(channel) + ', CHTYPE: ' + str(chtype), 'PLUGIN invalid: ' + str(setting2))
                        return
                
                elif setting2[-4:] == 'strm':#strm check           
                    self.strm_ok(setting2)
                    if self.strmValid == True:
                        fileList = self.buildInternetTVFileList(setting1, setting2, setting3, setting4, channel)
                        self.log('makeChannelList, Building STRM channel')
                        
                        
        elif chtype == 10: # Youtube
            self.log("Building Youtube Channel " + setting1 + " using type " + setting2 + "...")
            fileList = self.createYoutubeFilelist(setting1, setting2, setting3, channel)
            
        elif chtype == 11: # RSS/iTunes/feedburner/Podcast
            self.log("Building RSS Feed " + setting1 + " using type " + setting2 + "...")
            fileList = self.createRSSFileList(setting1, setting2, setting3, channel)   
            
        else:
            if chtype == 0:
                if FileAccess.copy(setting1, MADE_CHAN_LOC + os.path.split(setting1)[1]) == False:
                    if FileAccess.exists(MADE_CHAN_LOC + os.path.split(setting1)[1]) == False:
                        self.log("Unable to copy or find playlist " + setting1)
                        return False

                fle = MADE_CHAN_LOC + os.path.split(setting1)[1]
            else:
                fle = self.makeTypePlaylist(chtype, setting1, setting2)

            fle = xbmc.translatePath(fle)

            if len(fle) == 0:
                self.log('Unable to locate the playlist for channel ' + str(channel), xbmc.LOGERROR)
                return False

            try:
                xml = FileAccess.open(fle, "r")
            except:
                self.log("makeChannelList Unable to open the smart playlist " + fle, xbmc.LOGERROR)
                return False


            try:
                dom = parse(xml)
            except:
                self.log('makeChannelList Problem parsing playlist ' + fle, xbmc.LOGERROR)
                xml.close()
                return False

            xml.close()

            if self.getSmartPlaylistType(dom) == 'mixed':
                fileList = self.buildMixedFileList(dom, channel)
            else:
                fileList = self.buildFileList(fle, channel)

            try:
                order = dom.getElementsByTagName('order')

                if order[0].childNodes[0].nodeValue.lower() == 'random':
                    israndom = True
            except:
                pass

        try:
            if append == True:
                channelplaylist = FileAccess.open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "r+")
                channelplaylist.seek(0, 2)
            else:
                channelplaylist = FileAccess.open(CHANNELS_LOC + "channel_" + str(channel) + ".m3u", "w")
        except:
            self.log('Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)
            return False

        if append == False:
            channelplaylist.write(uni("#EXTM3U\n"))

        if None == fileList or len(fileList) == 0:
            self.log("Unable to get information about channel " + str(channel), xbmc.LOGERROR)
            channelplaylist.close()
            return False

        if israndom:
            random.shuffle(fileList)

        if len(fileList) > 4096:
            fileList = fileList[:4096]

        fileList = self.runActions(RULES_ACTION_LIST, channel, fileList)
        self.channels[channel - 1].isRandom = israndom

        if append:
            if len(fileList) + self.channels[channel - 1].Playlist.size() > 4096:
                fileList = fileList[:(4096 - self.channels[channel - 1].Playlist.size())]
        else:
            if len(fileList) > 4096:
                fileList = fileList[:4096]

        # Write each entry into the new playlist
        for string in fileList:
            channelplaylist.write(uni("#EXTINF:") + uni(string) + uni("\n"))

        channelplaylist.close()
        self.log('makeChannelList return')
        return True

        
    def makeTypePlaylist(self, chtype, setting1, setting2):
        if chtype == 1:
            if len(self.networkList) == 0:
                self.fillTVInfo()
            return self.createNetworkPlaylist(setting1)
            
        elif chtype == 2:
            if len(self.studioList) == 0:
                self.fillMovieInfo()
            return self.createStudioPlaylist(setting1)
            
        elif chtype == 3:
            if len(self.showGenreList) == 0:
                self.fillTVInfo()
            return self.createGenrePlaylist('episodes', chtype, setting1)
            
        elif chtype == 4:
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()
            return self.createGenrePlaylist('movies', chtype, setting1)
            
        elif chtype == 5:
            if len(self.mixedGenreList) == 0:
                if len(self.showGenreList) == 0:
                    self.fillTVInfo()

                if len(self.movieGenreList) == 0:
                    self.fillMovieInfo()

                self.mixedGenreList = self.makeMixedList(self.showGenreList, self.movieGenreList)
                self.mixedGenreList.sort(key=lambda x: x.lower())

            return self.createGenreMixedPlaylist(setting1)
            
        elif chtype == 6:
            if len(self.showList) == 0:
                self.fillTVInfo()
            return self.createShowPlaylist(setting1, setting2)    
            
        elif chtype == 12:
            if len(self.musicGenreList) == 0:
                self.fillMusicInfo()
            return self.createGenrePlaylist('songs', chtype, setting1)
            
    
    def createMusicPlaylist(self, genre, channelname):
        self.log("createMusicPlaylist")
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'songs_' + genre + '.xsp')

        ATLimit = {}
        ATLimit['0'] = 25 
        ATLimit['1'] = 50 
        ATLimit['2'] = 100           
        ATLimit['3'] = 250           
        ATLimit['4'] = 500             
        ATLimit['5'] = 1000
        ATLimit['6'] = 0 #unlimited

        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":  
            limit = int(ATLimit[REAL_SETTINGS.getSetting('ATLimit')])
        else:
            limit = 0

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''
        
        self.writeXSPHeader(fle, "songs", self.getChannelName(1, genre))
        genre = genre.lower()
        added = False
        
        for i in range(len(self.showList)):
            if self.threadPause() == False:
                fle.close()
                return ''

            if self.musicGenreList[i][1].lower() == genre:
                thesong = self.cleanString(self.musicGenreList[i][0])
                fle.write('    <rule field="songs" operator="is">' + thesong + '</rule>\n')
                added = True

        self.writeXSPFooter(fle, limit, "random")
        fle.close()

        if added == False:
            return ''

        return flename
    
    
    def createNetworkPlaylist(self, network):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Network_' + network + '.xsp')
  
        ATLimit = {}
        ATLimit['0'] = 25 
        ATLimit['1'] = 50 
        ATLimit['2'] = 100           
        ATLimit['3'] = 250           
        ATLimit['4'] = 500             
        ATLimit['5'] = 1000
        ATLimit['6'] = 0 #unlimited

        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":  
            limit = int(ATLimit[REAL_SETTINGS.getSetting('ATLimit')])
        else:
            limit = 0

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, "episodes", self.getChannelName(1, network))
        network = network.lower()
        added = False

        for i in range(len(self.showList)):
            if self.threadPause() == False:
                fle.close()
                return ''

            if self.showList[i][1].lower() == network:
                theshow = self.cleanString(self.showList[i][0])
                fle.write('    <rule field="tvshow" operator="is">' + theshow + '</rule>\n')
                added = True

        self.writeXSPFooter(fle, limit, "random")
        fle.close()

        if added == False:
            return ''

        return flename




    def createShowPlaylist(self, show, setting2):
        order = 'random'

        ATLimit = {}
        ATLimit['0'] = 25 
        ATLimit['1'] = 50 
        ATLimit['2'] = 100           
        ATLimit['3'] = 250           
        ATLimit['4'] = 500             
        ATLimit['5'] = 1000
        ATLimit['6'] = 0 #unlimited

        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":  
            limit = int(ATLimit[REAL_SETTINGS.getSetting('ATLimit')])
        else:
            limit = 0

        try:
            setting = int(setting2)

            if setting & MODE_ORDERAIRDATE > 0:
                order = 'airdate'
        except:
            pass

        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Show_' + show + '_' + order + '.xsp')

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, 'episodes', self.getChannelName(6, show))
        show = self.cleanString(show)
        fle.write('    <rule field="tvshow" operator="is">' + show + '</rule>\n')
        self.writeXSPFooter(fle, limit, order)
        fle.close()
        return flename

    
    def fillMixedGenreInfo(self):
        if len(self.mixedGenreList) == 0:
            if len(self.showGenreList) == 0:
                self.fillTVInfo()
            if len(self.movieGenreList) == 0:
                self.fillMovieInfo()

            self.mixedGenreList = self.makeMixedList(self.showGenreList, self.movieGenreList)
            self.mixedGenreList.sort(key=lambda x: x.lower())

    
    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break

        return newlist
    
    
    def createGenreMixedPlaylist(self, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Mixed_' + genre + '.xsp')

        ATLimit = {}
        ATLimit['0'] = 25 
        ATLimit['1'] = 50 
        ATLimit['2'] = 100           
        ATLimit['3'] = 250           
        ATLimit['4'] = 500             
        ATLimit['5'] = 1000
        ATLimit['6'] = 0 #unlimited

        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":  
            limit = int(ATLimit[REAL_SETTINGS.getSetting('ATLimit')])
        else:
            limit = 0

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        epname = os.path.basename(self.createGenrePlaylist('episodes', 3, genre))
        moname = os.path.basename(self.createGenrePlaylist('movies', 4, genre))
        self.writeXSPHeader(fle, 'mixed', self.getChannelName(5, genre))
        fle.write('    <rule field="playlist" operator="is">' + epname + '</rule>\n')
        fle.write('    <rule field="playlist" operator="is">' + moname + '</rule>\n')
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        return flename


    def createGenrePlaylist(self, pltype, chtype, genre):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + pltype + '_' + genre + '.xsp')

        ATLimit = {}
        ATLimit['0'] = 25 
        ATLimit['1'] = 50 
        ATLimit['2'] = 100           
        ATLimit['3'] = 250           
        ATLimit['4'] = 500             
        ATLimit['5'] = 1000
        ATLimit['6'] = 0 #unlimited

        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":  
            limit = int(ATLimit[REAL_SETTINGS.getSetting('ATLimit')])
        else:
            limit = 0

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, pltype, self.getChannelName(chtype, genre))
        genre = self.cleanString(genre)
        fle.write('    <rule field="genre" operator="is">' + genre + '</rule>\n')
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        return flename


    def createStudioPlaylist(self, studio):
        flename = xbmc.makeLegalFilename(GEN_CHAN_LOC + 'Studio_' + studio + '.xsp')

        ATLimit = {}
        ATLimit['0'] = 25 
        ATLimit['1'] = 50 
        ATLimit['2'] = 100           
        ATLimit['3'] = 250           
        ATLimit['4'] = 500             
        ATLimit['5'] = 1000
        ATLimit['6'] = 0 #unlimited

        if Globals.REAL_SETTINGS.getSetting("Autotune") == "true" and Globals.REAL_SETTINGS.getSetting("Warning1") == "true":  
            limit = int(ATLimit[REAL_SETTINGS.getSetting('ATLimit')])
        else:
            limit = 0

        try:
            fle = FileAccess.open(flename, "w")
        except:
            self.Error('Unable to open the cache file ' + flename, xbmc.LOGERROR)
            return ''

        self.writeXSPHeader(fle, "movies", self.getChannelName(2, studio))
        studio = self.cleanString(studio)
        fle.write('    <rule field="studio" operator="is">' + studio + '</rule>\n')
        self.writeXSPFooter(fle, limit, "random")
        fle.close()
        return flename


    def createDirectoryPlaylist(self, setting1):
        self.log("createDirectoryPlaylist " + setting1)
        fileList = []
        filecount = 0
        json_query = '{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "files"}, "id": 1}' % ( self.escapeDirJSON(setting1),)

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "getting file list")

        json_folder_detail = self.sendJSON(json_query)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
        thedir = ''

        if setting1[-1:1] == '/' or setting1[-1:1] == '\\':
            thedir = os.path.split(setting1[:-1])[1]
        else:
            thedir = os.path.split(setting1)[1]

        for f in file_detail:
            if self.threadPause() == False:
                del fileList[:]
                break

            match = re.search('"file" *: *"(.*?)",', f)

            if match:
                if(match.group(1).endswith("/") or match.group(1).endswith("\\")):
                    fileList.extend(self.createDirectoryPlaylist(match.group(1).replace("\\\\", "\\")))
                else:
                    duration = self.videoParser.getVideoLength(match.group(1).replace("\\\\", "\\"))

                    if duration == 0 and self.incIceLibrary == True:
                        if match.group(1).replace("\\\\", "\\")[-4:].lower() == 'strm':
                            self.log("Building Strm Directory Channel")
                            duration = 1800 #parse duration from nfoparser todo
                            needsreset = True
                            makenewlist = True
                    
                    if duration > 0:
                        filecount += 1

                        if self.background == False:
                            if filecount == 1:
                                self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "added " + str(filecount) + " entry")
                            else:
                                self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "added " + str(filecount) + " entries")

                        afile = uni(os.path.split(match.group(1).replace("\\\\", "\\"))[1])
                        afile, ext = os.path.splitext(afile)
                        afile = unquote(afile)
                        tmpstr = uni(str(duration) + ',')
                        tmpstr += uni(afile) + uni("//") + uni(thedir) + uni("//")
                        tmpstr = uni(tmpstr[:500])
                        tmpstr = uni(tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\""))
                        tmpstr += uni("\n") + uni(match.group(1).replace("\\\\", "\\"))
                        fileList.append(tmpstr)

        if filecount == 0:
            self.log(json_folder_detail)

        return fileList


    def writeXSPHeader(self, fle, pltype, plname):
        fle.write('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n')
        fle.write('<smartplaylist type="' + pltype + '">\n')
        plname = self.cleanString(plname)
        fle.write('    <name>' + plname + '</name>\n')
        fle.write('    <match>one</match>\n')


    def writeXSPFooter(self, fle, limit, order):
        if limit > 0:
            fle.write('    <limit>' + str(limit) + '</limit>\n')

        fle.write('    <order direction="ascending">' + order + '</order>\n')
        fle.write('</smartplaylist>\n')


    def writeFileList(self, channel, fileList):
        try:
            channelplaylist = open("channel_" + str(channel) + ".m3u", "w")
        except:
            self.Error('writeFileList: Unable to open the cache file ' + CHANNELS_LOC + 'channel_' + str(channel) + '.m3u', xbmc.LOGERROR)

        # get channel name from settings
        channelplaylist.write("#EXTM3U\n")
        fileList = fileList[:500]
        # Write each entry into the new playlist
        string_split = []
        totalDuration = 0
        for string in fileList:
            # capture duration of final filelist to get total duration for channel
            string_split = string.split(',')
            totalDuration = totalDuration + int(string_split[0])
            # write line
            channelplaylist.write("#EXTINF:" + string + "\n")
        channelplaylist.close()
        ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_totalDuration", str(totalDuration))
        # copy to prestage to ensure there is always a prestage file available for the auto reset
        # this is to cover the use case where a channel setting has been changed 
        # after the auto reset time has expired resulting in a new channel being created
        # during the next start as well as a auto reset being triggered which moves
        # files from prestage to the cache directory

    
    def cleanString(self, string):
        newstr = uni(string)
        newstr = newstr.replace('&', '&amp;')
        newstr = newstr.replace('>', '&gt;')
        newstr = newstr.replace('<', '&lt;')
        return uni(newstr)

    
    def uncleanString(self, string):
        self.log("uncleanString")
        newstr = string
        newstr = newstr.replace('&amp;', '&')
        newstr = newstr.replace('&gt;', '>')
        newstr = newstr.replace('&lt;', '<')
        return uni(newstr)
               
            
    def fillMusicInfo(self, sortbycount = False):
        self.log("fillMusicInfo")
        self.musicGenreList = [] 
        json_query = '{"jsonrpc": "2.0", "method": "AudioLibrary.GetAlbums", "params": {"fields":["genre"]}, "id": 1}'
        
        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding music", "reading music data")

        json_folder_detail = self.sendJSON(json_query)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.musicGenreList[:]
                return

            if USING_FRODO:
                match = re.search('"genre" *: *\[(.*?)\]', f)
            else:
                match = re.search('"genre" *: *"(.*?)",', f)

            if match:
                if USING_FRODO:
                    genres = match.group(1).split(',')
                else:
                    genres = match.group(1).split('/')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.musicGenreList)):
                        if self.threadPause() == False:
                            del self.musicGenreList[:]
                            return
                            
                        itm = self.musicGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.musicGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.musicGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.musicGenreList.append(genre.strip('"').strip())
    
        if sortbycount:
            self.musicGenreList.sort(key=lambda x: x[1], reverse = True)
        else:
            self.musicGenreList.sort(key=lambda x: x.lower())

        if (len(self.musicGenreList) == 0):
            self.log(json_folder_detail)

        self.log("found genres " + str(self.musicGenreList))
     
    
    def fillTVInfo(self, sortbycount = False):
        self.log("fillTVInfo")
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"fields":["studio", "genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "reading TV data")

        json_folder_detail = self.sendJSON(json_query)
        self.logDebug(json_folder_detail)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.networkList[:]
                del self.showList[:]
                del self.showGenreList[:]
                return

            if USING_FRODO:
                match = re.search('"studio" *: *\[(.*?)\]', f)
            else:
                match = re.search('"studio" *: *"(.*?)",', f)

            network = ''

            if match:
                if USING_FRODO:
                    network = (match.group(1).split(','))[0]
                else:
                    network = match.group(1)

                network = network.strip('"').strip()
                found = False

                for item in range(len(self.networkList)):
                    if self.threadPause() == False:
                        del self.networkList[:]
                        del self.showList[:]
                        del self.showGenreList[:]
                        return

                    itm = self.networkList[item]

                    if sortbycount:
                        itm = itm[0]

                    if itm.lower() == network.lower():
                        found = True

                        if sortbycount:
                            self.networkList[item][1] += 1

                        break

                if found == False and len(network) > 0:
                    if sortbycount:
                        self.networkList.append([network, 1])
                    else:
                        self.networkList.append(network)

            match = re.search('"label" *: *"(.*?)",', f)

            if match:
                show = match.group(1).strip()
                self.showList.append([show, network])

            if USING_FRODO:
                match = re.search('"genre" *: *\[(.*?)\]', f)
            else:
                match = re.search('"genre" *: *"(.*?)",', f)

            if match:
                if USING_FRODO:
                    genres = match.group(1).split(',')
                else:
                    genres = match.group(1).split('/')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.showGenreList)):
                        if self.threadPause() == False:
                            del self.networkList[:]
                            del self.showList[:]
                            del self.showGenreList[:]
                            return

                        itm = self.showGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.showGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.showGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.showGenreList.append(genre.strip('"').strip())

        if sortbycount:
            self.networkList.sort(key=lambda x: x[1], reverse = True)
            self.showGenreList.sort(key=lambda x: x[1], reverse = True)
        else:
            self.networkList.sort(key=lambda x: x.lower())
            self.showGenreList.sort(key=lambda x: x.lower())

        if (len(self.showList) == 0) and (len(self.showGenreList) == 0) and (len(self.networkList) == 0):
            self.log(json_folder_detail)

        self.log("found shows " + str(self.showList))
        self.log("found genres " + str(self.showGenreList))
        self.log("fillTVInfo return " + str(self.networkList))


    def fillMovieInfo(self, sortbycount = False):
        self.log("fillMovieInfo")
        studioList = []
        json_query = '{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"fields":["studio", "genre"]}, "id": 1}'

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "reading movie data")

        json_folder_detail = self.sendJSON(json_query)
        # self.log(json_folder_detail)
        detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in detail:
            if self.threadPause() == False:
                del self.movieGenreList[:]
                del self.studioList[:]
                del studioList[:]
                break

            if USING_FRODO:
                match = re.search('"genre" *: *\[(.*?)\]', f)
            else:
                match = re.search('"genre" *: *"(.*?)",', f)

            if match:
                if USING_FRODO:
                    genres = match.group(1).split(',')
                else:
                    genres = match.group(1).split('/')

                for genre in genres:
                    found = False
                    curgenre = genre.lower().strip('"').strip()

                    for g in range(len(self.movieGenreList)):
                        itm = self.movieGenreList[g]

                        if sortbycount:
                            itm = itm[0]

                        if curgenre == itm.lower():
                            found = True

                            if sortbycount:
                                self.movieGenreList[g][1] += 1

                            break

                    if found == False:
                        if sortbycount:
                            self.movieGenreList.append([genre.strip('"').strip(), 1])
                        else:
                            self.movieGenreList.append(genre.strip('"').strip())

            if USING_FRODO:
                match = re.search('"studio" *: *\[(.*?)\]', f)
            else:
                match = re.search('"studio" *: *"(.*?)"', f)

            if match:
                if USING_FRODO:
                    studios = match.group(1).split(',')
                else:
                    studios = match.group(1).split('/')

                for studio in studios:
                    curstudio = studio.strip('"').strip()
                    found = False

                    for i in range(len(studioList)):
                        if studioList[i][0].lower() == curstudio.lower():
                            studioList[i][1] += 1
                            found = True
                            break

                    if found == False and len(curstudio) > 0:
                        studioList.append([curstudio, 1])

        maxcount = 0

        for i in range(len(studioList)):
            if studioList[i][1] > maxcount:
                maxcount = studioList[i][1]

        bestmatch = 1
        lastmatch = 1000
        counteditems = 0

        for i in range(maxcount, 0, -1):
            itemcount = 0

            for j in range(len(studioList)):
                if studioList[j][1] == i:
                    itemcount += 1

            if abs(itemcount + counteditems - 8) < abs(lastmatch - 8):
                bestmatch = i
                lastmatch = itemcount

            counteditems += itemcount

        if sortbycount:
            studioList.sort(key=lambda x: x[1], reverse=True)
            self.movieGenreList.sort(key=lambda x: x[1], reverse=True)
        else:
            studioList.sort(key=lambda x: x[0].lower())
            self.movieGenreList.sort(key=lambda x: x.lower())

        for i in range(len(studioList)):
            if studioList[i][1] >= bestmatch:
                if sortbycount:
                    self.studioList.append([studioList[i][0], studioList[i][1]])
                else:
                    self.studioList.append(studioList[i][0])

        if (len(self.movieGenreList) == 0) and (len(self.studioList) == 0):
            self.log(json_folder_detail)

        self.log("found genres " + str(self.movieGenreList))
        self.log("fillMovieInfo return " + str(self.studioList))


    def makeMixedList(self, list1, list2):
        self.log("makeMixedList")
        newlist = []

        for item in list1:
            curitem = item.lower()

            for a in list2:
                if curitem == a.lower():
                    newlist.append(item)
                    break

        self.log("makeMixedList return " + str(newlist))
        return newlist

    def buildGenreLiveID(self, showtitle, type): ##return genre and LiveID by json
        #query GetTVShows for by tv or movie: get title/genre, match title return genre...
        self.log("buildGenreLiveID")
        match = []
        TVtype = False
        MovieType = False
        try:
            if type == 'TV':
                json_query = uni('{"jsonrpc":"2.0","method":"VideoLibrary.GetTVShows","params":{"properties":["title","year","genre","imdbnumber"]}, "id": 1}')
                if not self.cached_json_detailed_TV:
                    self.logDebug('buildGenreLiveID, json_detail creating cache')
                    self.cached_json_detailed_TV = self.sendJSON(json_query)
                    json_detail = self.cached_json_detailed_TV
                    TVtype = True
                else:
                    json_detail = self.cached_json_detailed_TV
                    TVtype = True
                    self.logDebug('buildGenreLiveID, json_detail using cache')
            else:
                json_query = uni('{"jsonrpc":"2.0","method":"VideoLibrary.GetMovies","params":{"properties":["title","year","genre","imdbnumber"]}, "id": 1}')
                if not self.cached_json_detailed_Movie:
                    self.logDebug('buildGenreLiveID, json_detail creating cache')
                    self.cached_json_detailed_Movie = self.sendJSON(json_query)
                    json_detail = self.cached_json_detailed_Movie 
                    MovieType = True
                else:
                    json_detail = self.cached_json_detailed_Movie 
                    MovieType = True
                    self.logDebug('buildGenreLiveID, json_detail using cache')
            
            file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_detail)
            ShowLST = json_detail.split("},{")
            # self.logDebug("buildGenreLiveID.ShowLST = " + str(ShowLST))#JsonOutput to big for log!
            showtitle = ('"title":"' + showtitle + '"')
            self.logDebug("buildGenreLiveID.showtitle = " + str(showtitle))
            match = [s for s in ShowLST if showtitle in s]
            self.logDebug("buildGenreLiveID.match.1 = " + str(match))
            match = match[0]
            self.logDebug("buildGenreLiveID.match.2 = " + str(match))
            genre = match.split('"],"imdbnumber":')[0]
            self.logDebug("buildGenreLiveID.genre.1 = " + str(genre))
            genre = genre.split('"genre":["', 1)[-1]
            self.logDebug("buildGenreLiveID.genre.2 = " + str(genre))
            genre = genre.split('","')
            self.logDebug("buildGenreLiveID.genre.3 = " + str(genre))
            genre = genre[0]
            self.logDebug("buildGenreLiveID.genre.4 = " + str(genre))
            
            if TVtype:
                tvdbid = match.split('","label":')[0]
                self.logDebug("buildGenreLiveID.tvdbid.1 = " + str(tvdbid))
                tvdbid = tvdbid.split('"],"', 1)[-1]
                self.logDebug("buildGenreLiveID.tvdbid.2 = " + str(tvdbid))
                tvdbid = tvdbid.split('imdbnumber":"', 1)[-1]
                self.logDebug("buildGenreLiveID.tvdbid.3 = " + str(tvdbid))
                tvdbid = (str(tvdbid))
                self.logDebug("buildGenreLiveID.tvdbid.4 = " + str(tvdbid))
                GenreLiveID = ( str(genre) + ',' + str(tvdbid))
            elif MovieType:
                imdbid = match.split('","label":')[0]
                self.logDebug("buildGenreLiveID.imdbid.1 = " + str(imdbid))
                imdbid = imdbid.split('"],"', 1)[-1]
                self.logDebug("buildGenreLiveID.imdbid.2 = " + str(imdbid))
                imdbid = imdbid.split('imdbnumber":"', 1)[-1]
                self.logDebug("buildGenreLiveID.imdbid.3 = " + str(imdbid))
                imdbid = (str(imdbid))
                self.logDebug("buildGenreLiveID.imdbid.4 = " + str(imdbid))
                GenreLiveID = ( str(genre) + ',' + str(imdbid))
            
            return GenreLiveID
        except:
            return 'Unknown,0'
            self.logDebug('buildGenreLiveID, GenreLiveID failed')
    

    def buildFileList(self, dir_name, channel): ##fix music channel todo
        self.log("buildFileList")
        fileList = []
        seasoneplist = []
        filecount = 0
        imdbid = 0
        tvdbid = 0
        genre = ''
        LiveID = ''
        cpManaged = False
        sbManaged = False
        json_query = uni('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "%s", "media": "video", "fields":["season","episode","playcount","streamdetails","duration","runtime","tagline","showtitle","album","artist","plot"]}, "id": 1}' % (self.escapeDirJSON(dir_name)))

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "querying database")

        json_folder_detail = self.sendJSON(json_query)
        self.log(json_folder_detail)
        file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)

        for f in file_detail:
            if self.threadPause() == False:
                del fileList[:]
                break

            f = uni(f)
            match = re.search('"file" *: *"(.*?)",', f)
            istvshow = False

            if match:
                if(match.group(1).endswith("/") or match.group(1).endswith("\\")):
                    fileList.extend(self.buildFileList(match.group(1), channel))
                else:
                    f = self.runActions(RULES_ACTION_JSON, channel, f)
                    duration = re.search('"duration" *: *([0-9]*?),', f)

                    try:
                        dur = int(duration.group(1))
                    except:
                        dur = 0

                    # As a last resort (since it's not as accurate), use runtime
                    if dur == 0:
                        duration = re.search('"runtime" *: *([0-9]*?),', f)

                        try:
                            dur = int(duration.group(1))
                        except:
                            dur = 0

                    # If duration doesn't exist, try to figure it out
                    if dur == 0:
                        dur = self.videoParser.getVideoLength(uni(match.group(1)).replace("\\\\", "\\"))

                    # Remove any file types that we don't want (ex. IceLibrary)
                    if self.incIceLibrary == False:
                        if match.group(1).replace("\\\\", "\\")[-4:].lower() == 'strm':
                            dur = 0

                    try:
                        if dur > 0:
                            filecount += 1
                            seasonval = -1
                            epval = -1

                            if self.background == False:
                                if filecount == 1:
                                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "added " + str(filecount) + " entry")
                                else:
                                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "adding videos", "added " + str(filecount) + " entries")

                            title = re.search('"label" *: *"(.*?)"', f)
                            tmpstr = str(dur) + ','
                            showtitle = re.search('"showtitle" *: *"(.*?)"', f)
                            plot = re.search('"plot" *: *"(.*?)",', f)
                            
                            if plot == None:
                                theplot = ""
                            else:
                                theplot = plot.group(1)

                            # This is a TV show
                            if showtitle != None and len(showtitle.group(1)) > 0:
                                season = re.search('"season" *: *(.*?),', f)
                                episode = re.search('"episode" *: *(.*?),', f)
                                swtitle = title.group(1)
                                swtitle = swtitle.split('.', 1)[-1]

                                try:
                                    seasonval = int(season.group(1))
                                    epval = int(episode.group(1))

                                    if self.showSeasonEpisode:
                                        swtitle = ('S' + ('0' if seasonval < 10 else '') + str(seasonval) + 'E' + ('0' if epval < 10 else '') + str(epval) + ' - '+ swtitle)
                                
                                    else:
                                        swtitle = (('0' if seasonval < 10 else '') + str(seasonval) + 'x' + ('0' if epval < 10 else '') + str(epval) + ' - '+ swtitle)
                                    
                                except:
                                    seasonval = -1
                                    epval = -1
                                    
                                GenreLiveID = self.buildGenreLiveID(showtitle.group(1), 'TV')
                                self.logDebug('buildFileList.GenreLiveID.TV = ' + str(GenreLiveID))
                                try:
                                    if GenreLiveID != 'Unknown,0':
                                        GenreLiveID = GenreLiveID.split(',')
                                        self.logDebug('buildFileList.GenreLiveID.2 = ' + str(GenreLiveID))
                                        genre = GenreLiveID[0]
                                        self.logDebug('buildFileList.genre = ' + str(genre))
                                        genre = uni(genre)
                                        tvdbid = GenreLiveID[1]                     
                                        tvdbid = int(tvdbid)
                                        self.logDebug('buildFileList.tvdbid = ' + str(tvdbid))   
                                    
                                        # Lookup IMDBID, 1st with tvdb, then with tvdb_api
                                        if imdbid == 0:
                                            try:
                                                tvdbAPI = TVDB(REAL_SETTINGS.getSetting('tvdb.apikey'))
                                                imdbid = tvdbAPI.getIMDBbyShowName(showtitle.group(1))  
                                                self.logDebug('buildFileList.imdbid.1 = ' + showtitle.group(1) + ' - ' + str(imdbid))
                                                if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None':
                                                    t = tvdb_api.Tvdb()
                                                    imdbid = t[showtitle.group(1)]['imdb_id']  
                                                    self.logDebug('buildFileList.imdbid.2 = ' + showtitle.group(1) + ' - ' + str(imdbid))
                                                    if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None':#clean output
                                                        imdbid = 0
                                            except:
                                                imdbid = 0
                                                self.logDebug('buildFileList, imdbid lookup failed')
                                       
                                        ## Correct Invalid IMDBID format   
                                        if imdbid != 0 and str(imdbid[0:2]) != 'tt':
                                            imdbid = ('tt' + str(imdbid))
                                        
                                        #Rob Newton - 20130130 - Check for show being managed by SickBeard
                                        sbManaged = False
                                        if REAL_SETTINGS.getSetting('sickbeard.enabled') == 'true':
                                            try:
                                                sbAPI = SickBeard(REAL_SETTINGS.getSetting('sickbeard.baseurl'),REAL_SETTINGS.getSetting('sickbeard.apikey'))
                                                if sbAPI.isShowManaged(tvdbid):
                                                    sbManaged = True
                                            except:
                                                pass
                                        
                                        #Build LiveID (imdb/tvdb/sickbeard or couchpoato/unaired or aired)
                                        
                                        if imdbid != 0:
                                            IID = ('imdb_' + str(imdbid))
                                            LiveID = (IID + '|')
                                        else:
                                            LiveID = ('NA' + '|')
                                        
                                        if tvdbid != 0:
                                            TID = ('tvdb_' + str(tvdbid))
                                            LiveID = (LiveID + '|' + TID + '|')
                                        else:
                                            LiveID = (LiveID + '|' + 'NA' + '|')
                                                              
                                        if sbManaged == True:
                                            SB = ('SB')
                                            LiveID = (LiveID + '|' + SB + '|')
                                        elif cpManaged == True:
                                            CP = ('CP')
                                            LiveID = (LiveID + '|' + CP + '|')
                                        else:
                                            LiveID = (LiveID + '|' + 'NA' + '|')
                                        
                                        LiveID = (LiveID + '|' + 'NA' + '|')
                                        LiveID = LiveID.replace('||','|')
                                        LiveID = uni(LiveID)
                                        genre = uni(genre)
                                        self.logDebug('buildFileList.LiveID = ' + LiveID)
                                        tmpstr += showtitle.group(1) + "//" + swtitle + "//" + theplot[:250] + "//" + genre + "//" + "//" + LiveID
                                        istvshow = True

                                    else:##Further parsing??
                                        tmpstr += showtitle.group(1) + "//" + swtitle + "//" + theplot[:250] + "//" + 'Unknown' + "////" + 'LiveID|'
                                        istvshow = True
                                   
                                except:
                                    tmpstr += showtitle.group(1) + "//" + swtitle + "//" + theplot[:250] + "//" + 'Unknown' + "////" + 'LiveID|'
                                    istvshow = True
                            else:
                                tmpstr += title.group(1) + "//"
                                album = re.search('"album" *: *"(.*?)"', f)
                                showtitle.group(1)

                                # This is a movie
                                if album == None or len(album.group(1)) == 0:
                                    tagline = re.search('"tagline" *: *"(.*?)"', f)
                                
                                    if tagline != None:
                                        tmpstr += tagline.group(1)
                                    
                                    GenreLiveID = self.buildGenreLiveID(title.group(1), 'Movie')
                                    self.logDebug('buildFileList.GenreLiveID.Movie = ' + str(GenreLiveID))
                                    try:
                                        if GenreLiveID != 'Unknown,0':
                                            GenreLiveID = GenreLiveID.split(',')
                                            self.logDebug('buildFileList.GenreLiveID.2 = ' + str(GenreLiveID))
                                            genre = GenreLiveID[0]
                                            self.logDebug('buildFileList.genre = ' + str(genre))
                                            genre = uni(genre)
                                            tvdbid = 0
                                            imdbid = GenreLiveID[1]
                                            self.logDebug('buildFileList.imdbid = ' + str(imdbid))   
                                        
                                            # Lookup IMDBID, 1st with tvdb, then with tvdb_api
                                            if imdbid == 0:
                                                try:
                                                    tvdbAPI = TVDB(REAL_SETTINGS.getSetting('tvdb.apikey'))
                                                    imdbid = tvdbAPI.getIMDBbyShowName(title.group(1))  
                                                    self.logDebug('buildFileList.imdbid.1 = ' + title.group(1) + ' - ' + str(imdbid))
                                                    if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None':
                                                        t = tvdb_api.Tvdb()
                                                        imdbid = t[title.group(1)]['imdb_id']  
                                                        self.logDebug('buildFileList.imdbid.2 = ' + title.group(1) + ' - ' + str(imdbid))
                                                        if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None':#clean output
                                                            imdbid = 0
                                                except:
                                                    imdbid = 0
                                                    self.logDebug('buildFileList, imdbid lookup failed')
                                           
                                            ## Correct Invalid IMDBID format   
                                            if imdbid != 0 and str(imdbid[0:2]) != 'tt':
                                                imdbid = ('tt' + str(imdbid))

                                            cpManaged = False
                                            # if REAL_SETTINGS.getSetting('couchpotato.enabled') == 'true':
                                                # try:
                                                    # if cpAPI.isMovieManaged(imdbid):
                                                        # cpManaged = True
                                                # except:
                                                    # pass
                                            
                                            #Build LiveID (imdb/tvdb/sickbeard or couchpoato/unaired or aired)
                                            
                                            if imdbid != 0:
                                                IID = ('imdb_' + str(imdbid))
                                                LiveID = (IID + '|')
                                            else:
                                                LiveID = ('NA' + '|')
                                            
                                            if tvdbid != 0:
                                                TID = ('tvdb_' + str(tvdbid))
                                                LiveID = (LiveID + '|' + TID + '|')
                                            else:
                                                LiveID = (LiveID + '|' + 'NA' + '|')
                                                                  
                                            if sbManaged == True:
                                                SB = ('SB')
                                                LiveID = (LiveID + '|' + SB + '|')
                                            elif cpManaged == True:
                                                CP = ('CP')
                                                LiveID = (LiveID + '|' + CP + '|')
                                            else:
                                                LiveID = (LiveID + '|' + 'NA' + '|')
                                            
                                            LiveID = (LiveID + '|' + 'NA' + '|')
                                            LiveID = LiveID.replace('||','|')
                                            LiveID = uni(LiveID)
                                            genre = uni(genre)
                                            self.logDebug('buildFileList.LiveID = ' + LiveID)
                                            if (REAL_SETTINGS.getSetting('EPGcolor_MovieGenre') == "true" and REAL_SETTINGS.getSetting('EPGcolor_enabled') == "1"):
                                                tmpstr += "//" + theplot[:250] + "//" + genre + "////" + LiveID
                                            else:
                                                tmpstr += "//" + theplot[:250] + "//" + 'Movie' + "////" + LiveID
                                    except:
                                        tmpstr += "//" + theplot[:250] + "//" + 'Movie' + "////" + 'LiveID|'
                                else:
                                    artist = re.search('"artist" *: *"(.*?)"', f)
                                    tmpstr += album.group(1) + "//" + artist.group(1)

                            tmpstr = tmpstr
                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            tmpstr = tmpstr + '\n' + match.group(1).replace("\\\\", "\\")

                            if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
                                    seasoneplist.append([seasonval, epval, tmpstr])
                            else:
                                fileList.append(tmpstr)
                    except:
                        pass
            else:
                continue

        if self.channels[channel - 1].mode & MODE_ORDERAIRDATE > 0:
            seasoneplist.sort(key=lambda seep: seep[1])
            seasoneplist.sort(key=lambda seep: seep[0])

            for seepitem in seasoneplist:
                fileList.append(seepitem[2])

        if filecount == 0:
            self.log(json_folder_detail)

        self.log("buildFileList return")
        return fileList


    def buildMixedFileList(self, dom1, channel):
        fileList = []
        self.log('buildMixedFileList')

        try:
            rules = dom1.getElementsByTagName('rule')
            order = dom1.getElementsByTagName('order')
        except:
            self.log('buildMixedFileList Problem parsing playlist ' + filename, xbmc.LOGERROR)
            xml.close()
            return fileList

        for rule in rules:
            rulename = rule.childNodes[0].nodeValue

            if FileAccess.exists(xbmc.translatePath('special://profile/playlists/video/') + rulename):
                FileAccess.copy(xbmc.translatePath('special://profile/playlists/video/') + rulename, MADE_CHAN_LOC + rulename)
                fileList.extend(self.buildFileList(MADE_CHAN_LOC + rulename, channel))
            else:
                fileList.extend(self.buildFileList(GEN_CHAN_LOC + rulename, channel))

        self.log("buildMixedFileList returning")
        return fileList

    
    def parseXMLTVDate(self, dateString):
        if dateString is not None:
            if dateString.find(' ') != -1:
                # remove timezone information
                dateString = dateString[:dateString.find(' ')]
            t = time.strptime(dateString, '%Y%m%d%H%M%S')
            return datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
        else:
            return None
    
    
    def buildLiveTVFileList(self, setting1, setting2, setting3, channel):
        showList = []
        seasoneplist = []
        showcount = 0  
        elements_parsed = 0
        xmltv = setting3
        title = ''
        description = ''
        subtitle = ''
        tmdbAPI = TMDB(REAL_SETTINGS.getSetting('tmdb.apikey'))
        tvdbAPI = TVDB(REAL_SETTINGS.getSetting('tvdb.apikey'))
        sbAPI = SickBeard(REAL_SETTINGS.getSetting('sickbeard.baseurl'),REAL_SETTINGS.getSetting('sickbeard.apikey'))
        cpAPI = CouchPotato(REAL_SETTINGS.getSetting('couchpotato.baseurl'),REAL_SETTINGS.getSetting('couchpotato.apikey'))
        
        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "Parsing LiveTV")
        
        if setting3 == 'ustvnow':
            f = urlopen(self.xmlTvFile)    
        
        elif setting3 != 'ustvnow':
            f = FileAccess.open(self.xmlTvFile, "rb")
        
        context = ET.iterparse(f, events=("start", "end")) 
        event, root = context.next()
        inSet = False
        
        for event, elem in context:
            if self.threadPause() == False:
                del showList[:]
                break
                
            if event == "end":
                if elem.tag == "programme":
                    channel = elem.get("channel")
                    url = unquote(setting2)
                    if setting1 == channel:
                        inSet = True
                        title = elem.findtext('title')
                        try:
                            title = title.split("*")[0] #Remove "*" from title
                        except:
                            pass
                        description = elem.findtext("desc")
                        iconElement = elem.find("icon")
                        icon = None
                        if iconElement is not None:
                            icon = iconElement.get("src")
                        subtitle = elem.findtext("sub-title")
                        if not description:
                            if not subtitle:
                                description = title  
                            else:
                                description = subtitle  
                        if not subtitle:                        
                                subtitle = 'LiveTV'                      
                        
                        ##################################
                        #Parse the category of the program
                        istvshow = True
                        movie = False
                        Unaired = False
                        category = 'Unknown'
                        categories = ''
                        categoryList = elem.findall("category")
                        for cat in categoryList:
                            categories += ', ' + cat.text
                            if cat.text == 'Movie':
                                category = cat.text
                                movie = True
                                istvshow = False
                            elif cat.text == 'Sports':
                                category = cat.text
                            elif cat.text == 'Children':
                                category = 'Kids'
                            elif cat.text == 'Kids':
                                category = cat.text
                            elif cat.text == 'News':
                                category = cat.text
                            elif cat.text == 'Comedy':
                                category = cat.text
                            elif cat.text == 'Drama':
                                category = cat.text

                        #Trim prepended comma and space (considered storing all categories, but one is ok for now)
                        categories = categories[2:]
                        
                        #If the movie flag was set, it should override the rest (ex: comedy and movie sometimes come together)
                        if movie:
                            category = 'Movie'


                        #Decipher the TVDB ID by using the Zap2it ID in dd_progid
                        dd_progid = ''
                        tvdbid = 0
                        imdbid = 0
                        seasonNumber = 0
                        episodeNumber = 0
                        episodeDesc = ''
                        episodeName = ''
                        episodeGenre = ''
                        
                        if not movie and REAL_SETTINGS.getSetting('tvdb.enabled') == 'true':
                            episodeNumList = elem.findall("episode-num")
                            for epNum in episodeNumList:
                                if epNum.attrib["system"] == 'dd_progid':
                                    dd_progid = epNum.text
                                    # self.log('dd_progid %s' % dd_progid) ##debug

                            #The Zap2it ID is the first part of the string delimited by the dot
                            #  Ex: <episode-num system="dd_progid">MV00044257.0000</episode-num>
                            dd_progid = dd_progid.split('.',1)[0]
                            try:
                                tvdbid = tvdbAPI.getIdByZap2it(dd_progid)
                                # self.log('title.tvdbid.1 = ' + title + ' - ' + str(tvdbid))#debug
                                if tvdbid == 0 or tvdbid == '0' or tvdbid == None or tvdbid == 'None': #clean output
                                    # self.log('clean.title.tvdbid.1 = ' + title + ' - ' + str(tvdbid))#debug
                                    tvdbid = 0
                            except:
                                pass
                            
                            #Sometimes GetSeriesByRemoteID does not find by Zap2it so we use the series name as backup
                            # Lookup TVDBID, 1st with tvdb_api, then with tvdb.
                            if tvdbid == 0:
                                try:
                                    t = tvdb_api.Tvdb()
                                    tvdbid = t[title]['seriesid']
                                    # self.log('title.tvdbid.2 = ' + title + ' - ' + str(tvdbid))#debug
                                    if tvdbid == 0 or tvdbid == '0' or tvdbid == None or tvdbid == 'None':
                                        tvdbid = tvdbAPI.getIdByShowName(elem.findtext('title'))
                                        # self.log('title.tvdbid.3 = ' + title + ' - ' + str(tvdbid))#debug
                                        if tvdbid == 0 or tvdbid == '0' or tvdbid == None or tvdbid == 'None': #clean output
                                            # self.log('clean.title.tvdbid.2 = ' + title + ' - ' + str(tvdbid))#debug
                                            tvdbid = 0
                                except:
                                    pass
                                    
                            # Lookup IMDBID, 1st with tvdb, then with tvdb_api
                            if imdbid == 0:
                                try:
                                    imdbid = tvdbAPI.getIMDBbyShowName(elem.findtext('title'))  
                                    # self.log('title.imdbid.1 = ' + title + ' - ' + str(imdbid))#debug
                                    if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None':
                                        t = tvdb_api.Tvdb()
                                        imdbid = t[title]['imdb_id']  
                                        # self.log('title.imdbid.2 = ' + title + ' - ' + str(imdbid))#debug
                                        if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None': #clean output
                                            imdbid = 0
                                except:
                                    pass
                            
                            # last chance for tvdbid try by IMDBID
                            if tvdbid == 0 and imdbid != 0:
                                try:
                                    tvdbid = tvdbAPI.getIdByIMDB(imdbid)  
                                    # self.log('title.tvdbid.4 = ' + title + ' - ' + str(imdbid))#debug   
                                    if tvdbid == 0 or tvdbid == '0' or tvdbid == None or tvdbid == 'None': #clean output
                                        tvdbid = 0  
                                except:
                                    pass 
                                    
                            ## Correct Invalid IMDBID format   
                            if imdbid != 0 and str(imdbid[0:2]) != 'tt':
                                imdbid = ('tt' + str(imdbid))
                                    
                            if tvdbid != 0: #Find Episode info by air date.
                                #Date element holds the original air date of the program                   
                                airdateStr = elem.findtext('date')
                                if airdateStr != None:
                                    try:
                                        #Change date format into the byAirDate lookup format (YYYY-MM-DD)
                                        t = time.strptime(airdateStr, '%Y%m%d')
                                        airDateTime = datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)
                                        airdate = airDateTime.strftime('%Y-%m-%d')
                                        #Only way to get a unique lookup is to use TVDB ID and the airdate of the episode
                                        episode = ET.fromstring(tvdbAPI.getEpisodeByAirdate(tvdbid, airdate))
                                        episode = episode.find("Episode")
                                        seasonNumber = episode.findtext("SeasonNumber")
                                        # self.log('title.seasonNumber.1 = ' + title + ' - ' + str(seasonNumber))#debug
                                        episodeNumber = episode.findtext("EpisodeNumber")
                                        # self.log('title.episodeNumber.1 = ' + title + ' - ' + str(episodeNumber))#debug
                                        episodeDesc = episode.findtext("Overview")
                                        # self.log('title.episodeDesc.1 = ' + title + ' - ' + episodeDesc)#debug 
                                        episodeName = episode.findtext("EpisodeName")  
                                        # self.log('title.episodename.1 = ' + title + ' - ' + episodeName)#debug 
                                    except:
                                        pass
 
                                ## Clean and reset Invalid values.                                                                                                            
                                if seasonNumber == None or seasonNumber == 'None' or seasonNumber == '0':
                                    seasonNumber = 0             
                                if episodeNumber == None or episodeNumber == 'None' or episodeNumber == '0':
                                    episodeNumber = 0             
                                if episodeDesc == None or episodeDesc == 'None' or episodeDesc == ' ':
                                    episodeDesc = ''       
                                if episodeName == None or episodeName == 'None' or episodeName == ' ':
                                    episodeName = ''

                            ## Find missing information by compairing subtitle to episodename. 
                            if subtitle != 'LiveTV' and (seasonNumber == 0 or episodeNumber == 0):
                                try:
                                    t = tvdb_api.Tvdb()
                                    episode = t[title].search(subtitle, key = 'episodename')# Output example: [<Episode 01x01 - My First Day>]
                                    episode = str(episode)
                                    # self.log('title.episodename.2 = ' + title + ' - ' + episode)#debug 
                                    episodeNum = episode.split(' - ')[0]
                                    episodeNum = episodeNum.split('[<Episode ', 1)[-1]
                                    seasonNumber = episodeNum.split('x')[0]
                                    # self.log('title.seasonNumber.2 = ' + title + ' - ' + str(seasonNumber))#debug 
                                    episodeNumber = episodeNum.split('x', 1)[-1]
                                    # self.log('title.episodeNumber.2 = ' + title + ' - ' + str(episodeNumber))#debug 
                                    episodeName = episode.split(' - ', 1)[-1]
                                    episodeName = episodeName.split('>]')[0]
                                    # self.log('title.episodeName.2 = ' + title + ' - ' + str(episodeName))#debug
                                except:
                                    pass
                                                                            
                            ## Clean and reset Invalid values. 
                            if seasonNumber == '[]':
                                seasonNumber = 0             
                            if episodeNumber == '[]':
                                episodeNumber = 0         
                            if episodeName == '[]':
                                episodeName = ''
                                    
                            ## Find missing information by using title and season/episode information.
                            if episodeDesc == '' and (seasonNumber != 0 and episodeNumber != 0):
                                try:
                                    t = tvdb_api.Tvdb()
                                    episode = t[title][seasonNumber][episodeNumber]
                                    episodeDesc = episode['overview'] 
                                    # self.log('title.episodeDesc.2 = ' + title + ' - ' + str(episodeDesc))#debug
                                except:
                                    pass
                            
                            if episodeName == '' and (seasonNumber != 0 and episodeNumber != 0):
                                try:
                                    t = tvdb_api.Tvdb()
                                    episode = t[title][seasonNumber][episodeNumber]
                                    episodeName = episode['episodename']
                                    # self.log('title.episodeName.3 = ' + title + ' - ' + str(episodeName))#debug
                                except:
                                    pass
                            
                            if episodeGenre == '' and category == 'Unknown':
                                try:
                                    t = tvdb_api.Tvdb()
                                    episodeGenre = t[title]['genre']## Output ex. Comedy|Talk Show|
                                    self.log('title.episodeGenre.1 = ' + title + ' - ' + str(episodeGenre))#debug
                                    episodeGenre = episodeGenre.split('|', 1)[-1]
                                    self.log('title.episodeGenre.2 = ' + title + ' - ' + str(episodeGenre))#debug
                                    category = episodeGenre.split("|")[0]
                                    self.log('title.episodeGenre.3 = ' + title + ' - ' + str(category))#debug
                                    if category == 0 or category == '0' or category == None or category == 'None': #clean output
                                        category = 'Unknown'  
                                except:
                                    pass
                            
                            # # cleanup Invalid data
                            # if seasonNumber == None:
                                # seasonNumber = 0
                            # if episodeNumber == None:
                                # episodeNumber = 0
                            # if episodeDesc == None:
                                # episodeDesc = ''
                            # if episodeName == None:
                                # episodeName = ''

                            if episodeDesc != '': #Change Description to TVDB Overview, not always correct!
                                description = episodeDesc
                            if episodeName == '':
                                episodeName = subtitle

                        #Rob Newton - 20130131 - Lookup the movie info from TMDB
                        if movie and REAL_SETTINGS.getSetting('tmdb.enabled') == 'true':
                            try:
                                #Date element holds the original air date of the program
                                movieYear = elem.findtext('date')
                                self.logDebug('movieYear = ' + str(movieYear))
                                movieInfo = tmdbAPI.getMovie(uni(elem.findtext('title')), movieYear)
                                imdbid = movieInfo['imdb_id']
                                self.logDebug('movie.title.imdbid.1 = ' + title + ' - ' + str(imdbid))
                                if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None': ## Fix search
                                    tmdbs = TMDB(REAL_SETTINGS.getSetting('tmdb.apikey'))
                                    search = tmdbs.Search()
                                    search.movie({'query': title + '(' + movieYear + ')'})
                                    for s in search.results:
                                        imdbid = (s['id'])
                                        self.logDebug('movie.title.imdbid.2 = ' + title + ' - ' + str(imdbid))
                                        if imdbid == 0 or imdbid == '0' or imdbid == None or imdbid == 'None': #clean output
                                            imdbid == 0
                            except:
                                pass


                        #Rob Newton - 20130130 - Check for show being managed by SickBeard
                        sbManaged = False
                        if REAL_SETTINGS.getSetting('sickbeard.enabled') == 'true':
                            try:
                                if sbAPI.isShowManaged(tvdbid):
                                    sbManaged = True
                            except:
                                pass
                        #Rob Newton - 20130130 - Check for movie being managed by CouchPotato
                        cpManaged = False
                        if REAL_SETTINGS.getSetting('couchpotato.enabled') == 'true':
                            try:
                                if cpAPI.isMovieManaged(imdbid):
                                    cpManaged = True
                            except:
                                pass
                        
                        now = datetime.datetime.now()
                        stopDate = self.parseXMLTVDate(elem.get('stop'))
                        startDate = self.parseXMLTVDate(elem.get('start'))

                        if seasonNumber == None or seasonNumber == 'None' or seasonNumber == '0':
                            seasonNumber = 0
                        if episodeName == None or episodeName == 'None' or episodeName == '0':
                            episodeName = 0

                        if seasonNumber > 0:
                            seasonNumber = '%02d' % int(seasonNumber)
                            # self.log('title.seasonNumber.3 = ' + title + ' - ' + str(seasonNumber))#debug
                        
                        if episodeName > 0:
                            episodeNumber = '%02d' % int(episodeNumber)
                            # self.log('title.episodeNumber.3 = ' + title + ' - ' + str(episodeNumber))#debug  
                                                   
                        #filter unwanted ids by title
                        if title == ('Paid Programming'):
                            tvdbid = 0
                            imdbid = 0
                            
                        #Read the "new" boolean for this program
                        if elem.find("new") != None:
                            Unaired = True
                            title = (title + '*NEW*')
                        else:
                            Unaired = False

                        #Correct encoding??
                        title = uni(title)
                        description = uni(description)
                        subtitle = uni(subtitle)
                        episodeDesc = uni(episodeDesc)
                        episodeName = uni(episodeName)
                        genre = uni(category)
                        
                        #Build LiveID (imdb/tvdb/sickbeard or couchpoato/unaired or aired)
                        LiveID = ''
                        if imdbid != 0:
                            IID = ('imdb_' + str(imdbid))
                            LiveID = (IID + '|')
                        else:
                            LiveID = ('NA' + '|')
                        
                        if tvdbid != 0:
                            TID = ('tvdb_' + str(tvdbid))
                            LiveID = (LiveID + '|' + TID + '|')
                        else:
                            LiveID = (LiveID + '|' + 'NA' + '|')
                                              
                        if sbManaged == True:
                            SB = ('SB')
                            LiveID = (LiveID + '|' + SB + '|')
                        elif cpManaged == True:
                            CP = ('CP')
                            LiveID = (LiveID + '|' + CP + '|')
                        else:
                            LiveID = (LiveID + '|' + 'NA' + '|')
                            
                        if Unaired == True:
                            LiveID = (LiveID + '|' + 'NEW' + '|')
                        else:
                            LiveID = (LiveID + '|' + 'OLD' + '|')

                        
                        LiveID = LiveID.replace('||','|')
                        self.log('LiveID = ' + LiveID)##Debug
                        
                        #skip old shows that have already ended
                        if now > stopDate:
                            self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + "  OLD: " + title)
                            self.logDebug("Unaired = " + str(Unaired) + ", tvdbid = " + str(tvdbid) + ", imdbid = " + str(imdbid) + ", seasonNumber = " + str(seasonNumber) + ", episodeNumber = " + str(episodeNumber) + ", category = " + str(category) + ", sbManaged = " + str(sbManaged) + ", cpManaged = " + str(cpManaged))         
                            continue
                        
                        #adjust the duration of the current show
                        if now > startDate and now < stopDate:
                            try:
                                dur = ((stopDate - startDate).seconds)
                                self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + "  NOW PLAYING: " + title + "  DUR: " + str(dur))
                                self.logDebug("Unaired = " + str(Unaired) + ", tvdbid = " + str(tvdbid) + ", imdbid = " + str(imdbid) + ", seasonNumber = " + str(seasonNumber) + ", episodeNumber = " + str(episodeNumber) + ", category = " + str(category) + ", sbManaged = " + str(sbManaged) + ", cpManaged = " + str(cpManaged))           
                            except:
                                dur = 3600  #60 minute default
                                self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + " - Error calculating show duration (defaulted to 60 min)")
                                raise
                        
                        #use the full duration for an upcoming show
                        if now < startDate:
                            try:
                                dur = (stopDate - startDate).seconds
                                self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + "  UPCOMING: " + title + "  DUR: " + str(dur))
                                self.logDebug("Unaired = " + str(Unaired) + ", tvdbid = " + str(tvdbid) + ", imdbid = " + str(imdbid) + ", seasonNumber = " + str(seasonNumber) + ", episodeNumber = " + str(episodeNumber) + ", category = " + str(category) + ", sbManaged = " + str(sbManaged) + ", cpManaged = " + str(cpManaged))          
                            except:
                                dur = 3600  #60 minute default
                                self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + " - Error calculating show duration (default to 60 min)")
                                raise

                        if imdbid > 0 or tvdbid > 0:#Enhanced tmpstr
                            
                            if movie == False: #TV IMDB/TVDB
                                if self.showSeasonEpisode:
                                    episodetitle = ('S' + ('0' if seasonNumber < 10 else '') + str(seasonNumber) + 'E' + ('0' if episodeNumber < 10 else '') + str(episodeNumber) + ' - '+ episodeName)
                                else:
                                    episodetitle = (('0' if seasonNumber < 10 else '') + str(seasonNumber) + 'x' + ('0' if episodeNumber < 10 else '') + str(episodeNumber) + ' - '+ episodeName)
                                
                                if str(episodetitle[0:6]) == 'S00E00':
                                    episodetitle = episodetitle.split("- ", 1)[-1]
                                    
                                episodetitle = uni(episodetitle)
                                tmpstr = uni(str(dur) + ',' + title + "//" + episodetitle[:50] + "//" + description[:150] + "//" + genre + "//" + str(startDate) + "//" + LiveID + '\n' + url)
                            
                            else: #Movie IMDB           
                                tmpstr = str(dur) + ',' + title + "//" + subtitle[:50] + "//" + description[:150] + "//" + genre + "//" + str(startDate) + "//" + LiveID + '\n' + url
                        
                        else: #Default Playlist
                            
                            if movie == False: #TV fallback  
                                tmpstr = str(dur) + ',' + title + "//" + subtitle[:50] + "//" + description[:150] + "//" + genre + "//" + str(startDate) + "//" + LiveID + '\n' + url               
                            
                            else: #Movie fallback         
                                tmpstr = str(dur) + ',' + title + "//" + subtitle[:50] + "//" + description[:150] + "//" + genre + "//" + str(startDate) + "//" + LiveID + '\n' + url       
                        
                        tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                        showList.append(tmpstr)

                    else:
                        if inSet == True:
                            self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + "  DONE")
                            break
                    showcount += 1
                    # self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + str(showcount) +" SHOWS FOUND")#Debug
                    
            root.clear()
                
        if showcount == 0:
            self.log("buildLiveTVFileList, CHANNEL: " + str(self.settingChannel) + " 0 SHOWS FOUND")
        
        return showList

    
    def buildInternetTVFileList(self, setting1, setting2, setting3, setting4, channel):
        showList = []
        seasoneplist = []
        showcount = 0
            
        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "Building InternetTV")
   
        try:
            self.ninstance = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings.xml'))
        except:
            self.log("buildInternetTVFileList, Could not find settings.xml. Run configuration first...")
            return   
            
        f = open(self.ninstance, "rb")
        context = ET.iterparse(f, events=("start", "end"))

        event, root = context.next()
     
        inSet = False
        for event, elem in context:
            if self.threadPause() == False:
                del showList[:]
                break
                
            if event == "end":
                if setting1 >= 1:
                    inSet = True
                    title = setting3
                    url = unquote(setting2)
                    description = setting4
                    iconElement = elem.find("icon")
                    icon = None
                    if iconElement is not None:
                        icon = iconElement.get("src")
                    if not description:
                        if not subtitle:
                            description = title
                        else:
                            description = subtitle 
                    istvshow = True

                    if setting1 >= 1:
                        try:
                            dur = setting1
                            self.log("buildInternetTVFileList, CHANNEL: " + str(self.settingChannel) + ", " + title + "  DUR: " + str(dur))
                        except:
                            dur = 5400  #90 minute default
                            self.log("buildInternetTVFileList, CHANNEL: " + str(self.settingChannel) + " - Error calculating show duration (defaulted to 90 min)")
                            raise

                    tmpstr = str(dur) + ',' + title + "//" + "InternetTV" + "//" + description + "//" 'InternetTV' + "////" + 'LiveID|' + '\n' + url
                    tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")

                    showList.append(tmpstr)
                else:
                    if inSet == True:
                        self.log("buildInternetTVFileList, CHANNEL: " + str(self.settingChannel) + ", DONE")
                        break
                showcount += 1
                    
            root.clear()

        return showList

        
    def createYoutubeFilelist(self, setting1, setting2, setting3, channel):
        showList = []
        seasoneplist = []
        showcount = 0   
        limit = 0
        stop = 0
        global youtube
        youtube = ''

        if setting3 == '':
            limit = 50
            self.log("createYoutubeFilelist, Using Global Parse-limit " + str(limit))
        else:
            limit = int(setting3)
            self.log("createYoutubeFilelist, Overriding Global Parse-limit to " + str(limit))
            
        stop = (limit / 25)

        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "Parsing Youtube")
        
        inSet = False
        startIndex = 1
        for x in range(stop):    
            if self.threadPause() == False:
                del showList[:]
                break

            if setting2 == '1': #youtubechannel
                self.log("createYoutubeFilelist, CHANNEL: " + str(self.settingChannel) + ", Youtube Channel" + ", Limit = " + str(limit))
                youtubechannel = 'http://gdata.youtube.com/feeds/api/users/' +setting1+ '/uploads?start-index=' +str(startIndex)+ '&max-results=25'
                youtube = youtubechannel
            elif setting2 == '2': #youtubeplaylist 
                self.log("createYoutubeFilelist, CHANNEL: " + str(self.settingChannel) + ", Youtube Playlist" + ", Limit = " + str(limit))
                youtubeplaylist = 'https://gdata.youtube.com/feeds/api/playlists/' +setting1+ '?start-index=1'
                youtube = youtubeplaylist                        
            elif setting2 == '3': #youtubesubscript 
                self.log("createYoutubeFilelist, CHANNEL: " + str(self.settingChannel) + ", Youtube Subscription" + ", Limit = " + str(limit))
                youtubesubscript = 'http://gdata.youtube.com/feeds/api/users/' +setting1+ '/newsubscriptionvideos?start-index=' +str(startIndex)+ '&max-results=25'
                youtube = youtubesubscript      
            
            feed = feedparser.parse(youtube)
            self.logDebug('createYoutubeFilelist, youtube = ' + str(youtube))                
            startIndex = startIndex + 25
                
            for i in range(len(feed['entries'])):
                try:
                    showtitle = feed.channel.author_detail['name']
                    showtitle = showtitle.replace(":", "")
                    try:
                        genre = (feed.entries[0].tags[1]['term'])
                    except:
                        self.log("createYoutubeFilelist, Invalid genre")
                        pass
                    
                    try:
                        thumburl = feed.entries[i].media_thumbnail[0]['url']
                    except:
                        self.log("createYoutubeFilelist, Invalid media_thumbnail")
                        pass 
        
                    #Time when the episode was published
                    time = (feed.entries[i].published_parsed)
                    time = str(time)
                    time = time.replace("time.struct_time", "")            
                    
                    #Some channels release more than one episode daily.  This section converts the mm/dd/hh to season=mm episode=dd+hh
                    showseason = [word for word in time.split() if word.startswith('tm_mon=')]
                    showseason = str(showseason)
                    showseason = showseason.replace("['tm_mon=", "")
                    showseason = showseason.replace(",']", "")
                    showepisodenum = [word for word in time.split() if word.startswith('tm_mday=')]
                    showepisodenum = str(showepisodenum)
                    showepisodenum = showepisodenum.replace("['tm_mday=", "")
                    showepisodenum = showepisodenum.replace(",']", "")
                    showepisodenuma = [word for word in time.split() if word.startswith('tm_hour=')]
                    showepisodenuma = str(showepisodenuma)
                    showepisodenuma = showepisodenuma.replace("['tm_hour=", "")
                    showepisodenuma = showepisodenuma.replace(",']", "")
                
                    eptitle = feed.entries[i].title
                    eptitle = re.sub('[!@#$/:]', '', eptitle)
                    eptitle = uni(eptitle)
                    eptitle = re.sub("[\W]+", " ", eptitle.strip()) 
                    eptitle = eptitle[:100]            
                    summary = feed.entries[i].summary
                    summary = uni(summary)
                    summary = re.sub("[\W]+", " ", summary.strip())
                    summary = summary[:200]
                    
                    # try:
                        # runtime = feed.entries[i].media_content[0]['duration']
                        # self.log("createYoutubeFilelist, Invalid media_content_duration")
                    # except:
                        # runtime = feed.entries[i].yt_duration['seconds']
                        # self.log("createYoutubeFilelist, Invalid yt_duration")
                    # else:
                        # pass
                        
                    runtime = feed.entries[i].yt_duration['seconds']
                    self.logDebug('createYoutubeFilelist, runtime = ' + str(runtime))
                    runtime = int(runtime)
                    # runtime = round(runtime/60.0)
                    # runtime = int(runtime)
                    
                    if runtime >= 1:
                        duration = runtime
                    else:
                        duration = 90
                        self.log("createYoutubeFilelist, CHANNEL: " + str(self.settingChannel) + " - Error calculating show duration (defaulted to 90 min)")
                    
                    # duration = round(duration*60.0)
                    self.logDebug('createYoutubeFilelist, duration = ' + str(duration))
                    duration = int(duration)

                    url = feed.entries[i].media_player['url']
                    self.logDebug('createYoutubeFilelist, url.1 = ' + str(url))
                    
                    if setting2 == '1':  
                        url = url.replace("https://", "").replace("http://", "").replace("www.youtube.com/watch?v=", "").replace("&feature=youtube_gdata_player", "")     
                    elif setting2 == '2':                    
                        url = url.replace("https://", "").replace("http://", "").replace("www.youtube.com/watch?v=", "").replace("&feature=youtube_gdata_player", "").replace("?version=3&f=playlists&app=youtube_gdata", "")
                    elif setting2 == '3':
                        url = url.replace("https://", "").replace("http://", "").replace("www.youtube.com/watch?v=", "").replace("&feature=youtube_gdata_player", "").replace("?version=3&f=newsubscriptionvideos&app=youtube_gdata", "")
                    
                    self.logDebug('createYoutubeFilelist, url.2 = ' + str(url))
                    
                    # Build M3U
                    if setting2 == '1'or setting2 == '2'or setting2 == '3':
                        inSet = True
                        istvshow = True
                        tmpstr = str(duration) + ',' + eptitle + "//" + "Youtube" + "//" + summary + "//" + genre + "//NA//" + 'LiveID|' + '\n' + 'plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid='+url + '\n'
                        tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                        self.log("createYoutubeFilelist, CHANNEL: " + str(self.settingChannel) + ", " + eptitle + "  DUR: " + str(duration))
                        showList.append(tmpstr)
                    else:
                        if inSet == True:
                            self.log("createYoutubeFilelist, CHANNEL: " + str(self.settingChannel) + ", DONE")
                            break                    
                except:
                    pass
        
        return showList


    def createRSSFileList(self, setting1, setting2, setting3, channel):
        self.log("createRSSFileList ")
        showList = []
        seasoneplist = []
        showcount = 0
        limit = 0
        stop = 0 
     
        if setting3 == '':
            limit = 50
            self.log("createRSSFileList, Using Global Parse-limit " + str(limit))
        else:
            limit = int(setting3)
            self.log("createRSSFileList, Overiding Global Parse-limit to " + str(limit))    
        
        stop = (limit / 25)
               
        if self.background == False:
            self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "Parsing RSS")

        self.ninstance = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings.xml'))
        f = open(self.ninstance, "rb")
        context = ET.iterparse(f, events=("start", "end"))
        
        event, root = context.next()
        
        inSet = False
        startIndex = 1
        for x in range(stop):    
            if self.threadPause() == False:
                del showList[:]
                break
                
            if setting2 == '1': #RSS
                self.log("createRSSFileList, RSS " + ", Limit = " + str(limit))
                rssfeed = setting1
                feed = feedparser.parse(rssfeed)

                for i in range(len(feed['entries'])):
                    try:
                        showtitle = feed.channel.title
                        showtitle = showtitle.replace(":", "")
                        eptitle = feed.entries[i].title
                        eptitle = eptitle.replace("/", "-")
                        eptitle = eptitle.replace(":", " ")
                        eptitle = eptitle.replace("\"", "")
                        eptitle = eptitle.replace("?", "")
                        eptitle = uni(eptitle)
                        eptitle = eptitle[:50]     
                        studio = feed.entries[i].author_detail['name']                        
                        try:
                            thumburl = feed.entries[i].media_thumbnail[0]['url']
                        except:
                            self.log("createRSSFileList, Invalid media_thumbnail")
                            pass 

                        if not '<p>' in feed.entries[i].summary_detail.value:
                            epdesc = feed.entries[i]['summary_detail']['value']
                            head, sep, tail = epdesc.partition('<div class="feedflare">')
                            epdesc = head
                        else:
                            epdesc = feed.entries[i]['subtitle']
                        if 'media_content' in feed.entries[i]:
                            url = feed.entries[i].media_content[0]['url']
                        else:
                            url = feed.entries[i].links[1]['href']

                        epdesc = epdesc[:150]
                        runtimex = feed.entries[i]['itunes_duration']
                        summary = feed.channel.subtitle
                        summary = summary.replace(":", "")
                        try:
                            if feed.channel.has_key("tags"):
                                genre = feed.channel.tags[0]['term']
                                genre = uni(genre)
                            else:
                                genre = "RSS"
                        except:
                            pass
                        time = (feed.entries[i].published_parsed)
                        time = str(time)
                        time = time.replace("time.struct_time", "")
                    
                        showseason = [word for word in time.split() if word.startswith('tm_mon=')]
                        showseason = str(showseason)
                        showseason = showseason.replace("['tm_mon=", "")
                        showseason = showseason.replace(",']", "")
                        showepisodenum = [word for word in time.split() if word.startswith('tm_mday=')]
                        showepisodenum = str(showepisodenum)
                        showepisodenum = showepisodenum.replace("['tm_mday=", "")
                        showepisodenum = showepisodenum.replace(",']", "")
                        showepisodenuma = [word for word in time.split() if word.startswith('tm_hour=')]
                        showepisodenuma = str(showepisodenuma)
                        showepisodenuma = showepisodenuma.replace("['tm_hour=", "")
                        showepisodenuma = showepisodenuma.replace(",']", "")  
                        
                        if len(runtimex) > 4:
                            runtime = runtimex.split(':')[-2]
                            runtimel = runtimex.split(':')[-3]
                            runtime = int(runtime)
                            runtimel = int(runtimel)
                            runtime = runtime + (runtimel*60)
                        if not len(runtimex) > 4:
                            runtimex = int(runtimex)
                            runtime = round(runtimex/60.0)
                            runtime = int(runtime)
                            
                        if runtime >= 1:
                            duration = runtime
                        else:
                            duration = 90
                        
                        duration = round(duration*60.0)
                        duration = int(duration)
                        
                        # Build M3U
                        if setting2 == '1':
                            inSet = True
                            istvshow = True
                            tmpstr = str(duration) + ',' + eptitle + "//" + "RSS" + "//" + epdesc + "//" + genre + "//NA//" + 'LiveID|' + '\n' + url + '\n'
                            tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                            self.log("createRSSFileList, CHANNEL: " + str(self.settingChannel) + ", " + eptitle + "  DUR: " + str(duration))
                            
                            showList.append(tmpstr)
                        else:
                            if inSet == True:
                                self.log("createRSSFileList, CHANNEL: " + str(self.settingChannel) + ", DONE")
                                break
                                
                    except:
                        pass

        return showList

        
    # Run rules for a channel
    def runActions(self, action, channel, parameter):
        self.log("runActions " + str(action) + " on channel " + str(channel))
        if channel < 1:
            return

        self.runningActionChannel = channel
        index = 0

        for rule in self.channels[channel - 1].ruleList:
            if rule.actions & action > 0:
                self.runningActionId = index

                if self.background == False:
                    self.updateDialog.update(self.updateDialogProgress, "Updating channel " + str(self.settingChannel), "processing rule " + str(index + 1), '')

                parameter = rule.runAction(action, self, parameter)

            index += 1

        self.runningActionChannel = 0
        self.runningActionId = 0
        return parameter


    def threadPause(self):
        if threading.activeCount() > 1:
            while self.threadPaused == True and self.myOverlay.isExiting == False:
                time.sleep(self.sleepTime)

            # This will fail when using config.py
            try:
                if self.myOverlay.isExiting == True:
                    self.log("IsExiting")
                    return False
            except:
                pass

        return True


    def escapeDirJSON(self, dir_name):
        mydir = uni(dir_name)

        if (mydir.find(":")):
            mydir = mydir.replace("\\", "\\\\")

        return mydir


    def getSmartPlaylistType(self, dom):
        self.log('getSmartPlaylistType')

        try:
            pltype = dom.getElementsByTagName('smartplaylist')
            return pltype[0].attributes['type'].value
        except:
            self.log("Unable to get the playlist type.", xbmc.LOGERROR)
            return ''
    

    
    # def makeChannelListFromFolder(self, channel, folder, location):
        # self.log("makeChannelListFromFolder")
        # folder = self.uncleanString(folder)
        # fileList = []
        # self.videoParser = VideoParser()
        # # set the types of files we want in our folder based file list
        # flext = [".avi",".mp4",".m4v",".3gp",".3g2",".f4v",".flv",".mkv",".flv"]
        # # get limit
        # limit = REAL_SETTINGS.getSetting("limit")

        # chname = self.uncleanString(ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_1_opt_1")
        # ADDON_SETTINGS.setSetting('Channel_' + str(channel) + '_time', '0')

        # self.line2 = "Creating Channel " + str(channel) + " - " + str(chname)
        # self.line3 = ""
        # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
        
        # # make sure folder exist
        # if os.path.exists(folder):
            # self.log("Scanning Folder")
            # self.line3 = "Scanning Folder"
            # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
            # # get a list of filenames from the folder
            # fnlist = []
            # for root, subFolders, files in os.walk(folder):            
                # for file in files:
                    # self.log("file found " + str(file) + " checking for valid extension")
                    # # get file extension
                    # basename, extension = os.path.splitext(file)
                    # if extension in flext:
                        # self.log("adding file " + str(file))
                        # fnlist.append(os.path.join(root,file))

            # # randomize list
            # random.shuffle(fnlist)

            # numfiles = 0
            # if len(fnlist) < limit:
                # limit = len(fnlist)

            # self.line3 = "Adding Files to Channel"
            # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                
            # for i in range(limit):
                # fpath = fnlist[i]
                # # get metadata for file
                # title = self.getTitle(fpath)
                # showtitle = self.getShowTitle(fpath)
                # theplot = self.getThePlot(fpath)
                # # get durations
                # dur = self.videoParser.getVideoLength(fpath)
                # if dur > 0:
                    # # add file to file list
                    # tmpstr = str(dur) + ',' + title + "//" + showtitle + "//" + theplot
                    # tmpstr = tmpstr[:600]
                    # tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                    # tmpstr = tmpstr + '\n' + fpath.replace("\\\\", "\\")
                    # fileList.append(tmpstr)
        # else:
            # self.log("Unable to open folder " + str(folder))
            
        # # trailers bumpers commercials
        # # check if fileList contains files
        # if len(fileList) == 0:
            # offair = REAL_SETTINGS.getSetting("offair")
            # offairFile = REAL_SETTINGS.getSetting("offairfile")            
            # if offair and len(offairFile) > 0:
                # self.line3 = "Channel is Off Air"
                # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                # dur = self.videoParser.getVideoLength(offairFile)
                # # insert offair video file
                # if dur > 0:
                    # numFiles = int((60 * 60 * 24)/dur)
                    # for i in range(numFiles):
                        # tmpstr = str(dur) + ','
                        # title = "Off Air"
                        # showtitle = "Off Air"
                        # theplot = "This channel is currently off the air"
                        # tmpstr = str(dur) + ',' + showtitle + "//" + title + "//" + theplot
                        # tmpstr = tmpstr.replace("\\n", " ").replace("\\r", " ").replace("\\\"", "\"")
                        # tmpstr = tmpstr + '\n' + offairFile.replace("\\\\", "\\")
                        # fileList.append(tmpstr)
                # ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_offair","1")
                # ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_2",MODE_SERIAL)
        # else:
            # ADDON_SETTINGS.setSetting("Channel_" + str(channel) + "_offair","0")
            # commercials = REAL_SETTINGS.getSetting("commercials")
            # commercialsfolder = REAL_SETTINGS.getSetting("commercialsfolder")
            # commercialInterval = 0            
            # bumpers = REAL_SETTINGS.getSetting("bumpers")
            # bumpersfolder = REAL_SETTINGS.getSetting("bumpersfolder")
            # bumperInterval = 0
            # if (commercials == "true" and os.path.exists(commercialsfolder)) or (bumpers == "true" and os.path.exists(bumpersfolder)):
                # if (commercials == "true" and os.path.exists(commercialsfolder)) :
                    # commercialInterval = self.getCommercialInterval(channel, len(fileList))
                    # commercialNum = self.getCommercialNum(channel, len(fileList))
                # else:
                    # commercialInterval = 0
                    # commercialNum = 0                        
                # if (bumpers == "true" and os.path.exists(bumpersfolder)):
                    # bumperInterval = self.getBumperInterval(channel, len(fileList))
                    # bumperNum = self.getBumperNum(channel, len(fileList))
                # else:
                    # bumperInterval = 0
                    # bumperNum = 0                        
                # trailerInterval = 0
                # trailerNum = 0
                # trailers = False
                # bumpers = False
                # commercials = False
                
                # if not int(bumperInterval) == 0:
                    # bumpers = True
                # if not int(commercialInterval) == 0:
                    # commercials = True
                
                # fileList = self.insertFiles(channel, fileList, commercials, bumpers, trailers, commercialInterval, bumperInterval, trailerInterval, commercialNum, bumperNum, trailerNum)

        # # write m3u
        # self.writeFileList(channel, fileList, location)
    
    
    # def getBumpersList(self, channel):
        # self.log("getBumpersList")
        # bumpersList = []
        # chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_1_opt_1")
        # type = "bumpers"

        # try:
            # metafile = open(META_LOC + str(type) + ".meta", "r")
        # except:
            # self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
            # return False

        # for file in metafile:
            # # filter by channel name
            # bumperMeta = []
            # bumperMeta = file.split('|')
            # thepath = bumperMeta[0]
            # basepath = os.path.dirname(thepath)
            # chfolder = os.path.split(basepath)[1]
            # # bumpers are channel specific
            # if chfolder == chname:
                # bumpersList.append(file)

        # metafile.close()

        # return bumpersList



    # def getCommercialsList(self, channel):
        # self.log("getCommercialsList")
        # commercialsList = []
        # chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_1_opt_1")
        # type = "commercials"
        # channelOnlyCommercials = False

        # try:
            # metafile = open(META_LOC + str(type) + ".meta", "r")
        # except:
            # self.Error('Unable to open the meta file ' + META_LOC + str(type) + '.meta', xbmc.LOGERROR)
            # return False

        # for file in metafile:
            # # filter by channel name
            # commercialMeta = []
            # commercialMeta = file.split('|')
            # thepath = commercialMeta[0]
            # basepath = os.path.dirname(thepath)
            # chfolder = os.path.split(basepath)[1]
            # if chfolder == chname:
                # if channelOnlyCommercials:
                    # # channel specific trailers are in effect
                    # commercialsList.append(file)
                # else:
                    # # reset list to only contain channel specific trailers
                    # channelOnlyCommercials = True
                    # commercialsList = []
                    # commercialsList.append(file)
            # else:
                # if not channelOnlyCommercials:
                    # commercialsList.append(file)

        # metafile.close()

        # return commercialsList


    # def getTrailersList(self, channel):
        # self.log("getTrailersList")
        # trailersList = []
        # chname = ADDON_SETTINGS.getSetting("Channel_" + str(channel) + "_rule_1_opt_1")
        # type = "trailers"
        # channelOnlyTrailers = False

        # try:
            # metafile = open(META_LOC + str(type) + ".meta", "r")
        # except:
            # self.log('Unable to open the meta file ' + META_LOC + str(type) + '.meta')
            # return False

        # for file in metafile:
            # # filter by channel name
            # trailerMeta = []
            # trailerMeta = file.split('|')
            # thepath = trailerMeta[0]
            # basepath = os.path.dirname(thepath)
            # chfolder = os.path.split(basepath)[1]
            # if chfolder == chname:
                # if channelOnlyTrailers:
                    # # channel specific trailers are in effect
                    # trailersList.append(file)
                # else:
                    # # reset list to only contain channel specific trailers
                    # channelOnlyTrailers = True
                    # trailersList = []
                    # trailersList.append(file)
            # else:
                # if not channelOnlyTrailers:
                    # trailersList.append(file)

        # metafile.close()

        # return trailersList


    # def convertMetaToFile(self, metaFileStr):
        # # parse file meta data
        # metaFile = []
        # metaFile = metaFileStr.split('|')
        # thepath = metaFile[0]
        # dur = metaFile[1]
        # title = metaFile[2]
        # showtitle = metaFile[3]
        # theplot = metaFile[4]
        # # format to file list structure
        # tmpstr = str(dur) + ','
        # tmpstr += showtitle + "//" + title + "//" + theplot
        # tmpstr = tmpstr[:600]
        # tmpstr = tmpstr.replace("\\n", " ").replace("\n", " ").replace("\r", " ").replace("\\r", " ").replace("\\\"", "\"")
        # tmpstr = tmpstr + '\n' + thepath.replace("\\\\", "\\")
        # return tmpstr
    

    # def insertFiles(self, channel, fileList, commercials, bumpers, trailers, cinterval, binterval, tinterval, cnum, bnum, tnum):
        # newFileList = []
        
        # if bumpers:
            # bumpersList = []
            # bumpersList = self.getBumpersList(channel)
            
        # if commercials:
            # commercialsList = []
            # commercialsList = self.getCommercialsList(channel)
        
        # if trailers:
            # trailersList = []
            # trailersList = self.getTrailersList(channel)
        
        # for i in range(len(fileList)):
            # newFileList.append(fileList[i])
            # if commercials:
                # self.line3 = "Inserting Commercials"
                # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                # if len(commercialsList) > 0:
                    # if (i+1) % cinterval == 0:
                        # for n in range(int(cnum)):
                            # commercialFile = random.choice(commercialsList)
                            # if len(commercialFile) > 0:
                                # newFileList.append(self.convertMetaToFile(commercialFile))
                            # else:
                                # self.log('insertFiles: Unable to get commercial')                                        
                # else:
                    # self.log("No valid commercials available")

            # if bumpers:
                # self.line3 = "Inserting Bumpers"
                # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                # if len(bumpersList) > 0:
                    # # mix in bumpers
                    # if (i+1) % binterval == 0:
                        # for n in range(int(bnum)):
                            # bumperFile = random.choice(bumpersList)
                            # if len(bumperFile) > 0:
                                # newFileList.append(self.convertMetaToFile(bumperFile))
                            # else:
                                # self.log('insertFiles: Unable to get bumper')                                                                
                # else:
                    # self.log("No valid bumpers available")

            # if trailers:
                # self.line3 = "Inserting Trailers"
                # self.updateDialog(self.progress,self.line1,self.line2,self.line3)
                # if len(trailersList) > 0:
                    # # mix in trailers
                    # if (i+1) % tinterval == 0:
                        # for n in range(int(tnum)):
                            # trailerFile = random.choice(trailersList)
                            # if len(trailerFile) > 0:
                                # newFileList.append(self.convertMetaToFile(trailerFile))
                            # else:
                                # self.log('insertFiles: Unable to get trailer')
                
        # fileList = newFileList    

        # return fileList
    
    def strm_ok(self, setting2):
        self.log("strm_ok, " + str(setting2))
        self.strmFailed = False
        self.strmValid = False
        rtmpOK = True
        urlOK = True
        pluginOK = True
        lines = ''
        # try:
        f = FileAccess.open(setting2, "r")
        linesLST = f.readlines()
        self.log("strm_ok.Lines = " + str(linesLST))
        f.close()

        for i in range(len(set(linesLST))):
            lines = linesLST[i]
            if lines[0:4] == 'rtmp':#rtmp check
                rtmpOK = self.rtmpDump(lines)
                self.logDebug("strm_ok.Lines rtmp = " + str(lines))
                #if invalid delete line
            elif lines[0:4] == 'http':#http check                
                urlOK = self.url_ok(lines)
                self.logDebug("strm_ok.Lines http = " + str(lines))
                #if invalid delete line
            elif lines[0:6] == 'plugin':#plugin check                
                pluginOK = self.plugin_ok(lines)
                self.logDebug("strm_ok.Lines plugin= " + str(lines))
            
            if rtmpOK == False or urlOK == False or pluginOK == False:
                self.strmFailed = True
            
        if self.strmFailed == True:
            self.log("strm_ok, failed strmCheck; writing fallback video")
            f = FileAccess.open(setting2, "w")
            for i in range(len(linesLST)):
                lines = linesLST[i]
                f.write(lines + '\n')
                self.logDebug("strm_ok, file write lines = " + str(lines))
            f.write('plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=-2GXT8bLe04')
            f.close()
            self.strmValid = True           
            
            
    def xmltv_ok(self, setting3):
        self.xmltvValid = False
        self.xmlTvFile = ''
        self.log("setting3 = " + str(setting3))
        
        if setting3 == 'ustvnow':
            self.log("xmltv_ok, testing " + str(setting3))
            url = 'http://dl.dropboxusercontent.com/s/q6oewxto709es2r/ustvnow.xml' # USTVnow XMLTV list
            url_bak = 'http://dl.dropboxusercontent.com/s/q6oewxto709es2r/ustvnow.xml' # USTVnow BACKUP XMLTV list
            try: 
                urllib2.urlopen(url)
                self.log("INFO: URL Connected...")
                self.xmltvValid = True
                self.xmlTvFile = url 
            except urllib2.URLError as e:
                urllib2.urlopen(url_bak)
                self.log("INFO: URL_BAK Connected...")
                self.xmltvValid = True
                self.xmlTvFile = url_bak
            except urllib2.URLError as e:
                if "Errno 10054" in e:
                    raise
                else:                
                    self.log("ERROR: Problem accessing the DNS. USTVnow XMLTV URL NOT VALiD, ERROR: " + str(e))
                    self.xmltvValid = False

        elif setting3 != 'ustvnow':
            self.xmlTvFile = xbmc.translatePath(os.path.join(REAL_SETTINGS.getSetting('xmltvLOC'), str(setting3) +'.xml'))
            self.log("xmltv_ok, testing " + str(self.xmlTvFile))
            try:
                FileAccess.exists(self.xmlTvFile)
                # channelplaylist.seek(0, 2)#todo add open, seek to verify info inside xmltv.xml
                self.log("INFO: XMLTV Data Found...")
                self.xmltvValid = True
            except IOError as e:
                self.xmltvValid = False
                self.log("ERROR: Problem accessing the DNS. " + str(setting3) +".xml XMLTV file NOT FOUND, ERROR: " + str(e))

        self.log("xmltvValid = " + str(self.xmltvValid))
                    
        
    def rtmpDump(self, stream):
        self.rtmpValid = False
        url = unquote(stream)
        
        OSplat = REAL_SETTINGS.getSetting('os')
        if OSplat == '0':
            OSpath = 'androidarm/rtmpdump'
        elif OSplat == '1':
            OSpath = 'android86/rtmpdump'
        elif OSplat == '2':
            OSpath = 'atv1linux/rtmpdump'
        elif OSplat == '3':
            OSpath = 'atv1stock/rtmpdump'
        elif OSplat == '4':
            OSpath = 'atv2/rtmpdump'
        elif OSplat == '5':
            OSpath = 'ios/rtmpdump'
        elif OSplat == '6':
            OSpath = 'linux32/rtmpdump'
        elif OSplat == '7':
            OSpath = 'linux64/rtmpdump'
        elif OSplat == '8':
            OSpath = 'mac32/rtmpdump'
        elif OSplat == '9':
            OSpath = 'mac64/rtmpdump'
        elif OSplat == '10':
            OSpath = 'pi/rtmpdump'
        elif OSplat == '11':
            OSpath = 'win/rtmpdump.exe'
        elif OSplat == '12':
            OSpath = '/usr/bin/rtmpdump'
            
        RTMPDUMP = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'lib', 'rtmpdump', OSpath))
        self.log("RTMPDUMP = " + RTMPDUMP)
        assert os.path.isfile(RTMPDUMP)
        
        if "playpath" in url:
            url = re.sub(r'playpath',"-y playpath",url)
            self.log("playpath url = " + str(url))
            command = [RTMPDUMP, '-B 1', '-m 2', '-r', url,'-o','test.flv']
            self.log("RTMPDUMP command = " + str(command))
        else:
            command = [RTMPDUMP, '-B 1', '-m 2', '-r', url,'-o','test.flv']
            self.log("RTMPDUMP command = " + str(command))
       
        CheckRTMP = Popen(command, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        output = CheckRTMP.communicate()[0]
        self.log("output = " + output)
        
        if "ERROR:" in output:
            self.log("ERROR: Problem accessing the DNS. RTMP URL NOT VALiD")
            self.rtmpValid = False 
        elif "WARNING:" in output:
            self.log("WARNING: Problem accessing the DNS. RTMP URL NOT VALiD")
            self.rtmpValid = False
        elif "INFO: Connected..." in output:
            self.log("INFO: Connected...")
            self.rtmpValid = True
        else:
            self.log("ERROR?: Unknown responce...")
            self.rtmpValid = False
        
        self.log("rtmpValid = " + str(self.rtmpValid))
        return self.rtmpValid

        
    def url_ok(self, url):
        self.urlValid = False
        url = unquote(url)
        try: 
            urllib2.urlopen(urllib2.Request(url))
            self.log("INFO: Connected...")
            self.urlValid = True
        except urllib2.URLError as e:
            self.log("ERROR: Problem accessing the DNS. HTTP URL NOT VALID, ERROR: " + str(e))
            self.urlValid = False
        
        self.log("urlValid = " + str(self.urlValid))
        return self.urlValid
        
        
    def plugin_ok(self, plugin):
        self.PluginFound = False
        self.PlugInvalid = False
        stream = plugin
        self.log("plugin stream = " + stream)
        id = plugin.split("/?")[0]
        id = id.split('//', 1)[-1]
        self.log("plugin id = " + id)
        try:
            xbmcaddon.Addon(id)
            self.PluginFound = True
        except Exception:
            self.PluginFound = False 
        return self.PluginFound
        
        # self.log("PluginFound = " + str(self.PluginFound))
        
        # if self.PluginFound == True:
            # # try:
            # json_query = uni('{"jsonrpc":"2.0","method":"Files.GetDirectory","params":{"directory":"%s""}, "id": 1}' % (self.escapeDirJSON(stream)))
            # json_folder_detail = self.sendJSON(json_query)
            # file_detail = re.compile( "{(.*?)}", re.DOTALL ).findall(json_folder_detail)
            # self.log('json_folder_detail = ' + str(json_folder_detail))
            # self.log('file_detail = ' + str(file_detail))
            # self.PlugInvalid = True        
            # # except Exception:
                # # self.PlugInvalid = False
                
    def smart_truncate(content, length=250, suffix='.'):
        if len(content) <= length:
            return content
        else:
            return content[:length].rsplit(' ', 1)[0]+suffix

# xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "id": 1, "params": {"directory": "plugin://plugin.video.youtube"}}')