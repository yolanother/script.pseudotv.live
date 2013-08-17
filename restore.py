import xbmc, xbmcgui, xbmcaddon
import subprocess, os
import sys, re

from Globals import *
from FileAccess import FileLock, FileAccess


if Globals.REAL_SETTINGS.getSetting("Autotune") == "false" and Globals.REAL_SETTINGS.getSetting("Warning") == "false":
    settingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.xml'))
    nsettingsFile = xbmc.translatePath(os.path.join(Globals.SETTINGS_LOC, 'settings2.bak.xml'))
    
    if FileAccess.exists(settingsFile) and FileAccess.exists(nsettingsFile):
        os.remove(settingsFile)
        FileAccess.rename(nsettingsFile, ssettingsFile)
        Globals.REAL_SETTINGS.setSetting('Restore', "False")
        Globals.REAL_SETTINGS.setSetting('Warning2', "False")