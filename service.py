# modules
from time import sleep
import xbmc, xbmcgui, os
import xbmcaddon

from resources.lib.Globals import *

# get addon info
REAL_SETTINGS = xbmcaddon.Addon(id='script.pseudotv.live')
ADDON_INFO = REAL_SETTINGS.getAddonInfo('path')
__language__  = REAL_SETTINGS.getLocalizedString

image = xbmc.translatePath(os.path.join(ADDON_INFO, 'resources', 'images')) + '/' + 'icon.png'

timer_amounts = {}
timer_amounts['0'] = 0            
timer_amounts['1'] = 5           
timer_amounts['2'] = 10            
timer_amounts['3'] = 15
timer_amounts['4'] = 20

IDLE_TIME = int(timer_amounts[REAL_SETTINGS.getSetting('timer_amount')])
Msg = REAL_SETTINGS.getSetting('notify')
Enabled = REAL_SETTINGS.getSetting('Auto_Start')

# start service
def Notify():	
	if (Msg == 'true'):
		xbmc.executebuiltin("Notification( %s, %s, %d, %s)" % (__language__(30047), __language__(30048), 3000, image) )
		xbmc.log("AUTOSTART PTVL: Notifications Enabled...")
	else:
		xbmc.log("AUTOSTART PTVL: Notifications Disabled...")
	
def autostart():
	Notify()		
	sleep(IDLE_TIME)	
	xbmc.executebuiltin("XBMC.RunScript(special://home/addons/script.pseudotv.live-master/default.py)")
	xbmc.executebuiltin("XBMC.RunScript(special://home/addons/script.pseudotv.live/default.py)")
	xbmc.log("AUTOSTART PTVL: Service Started...")
				
if (Enabled == 'true'):	
	autostart()