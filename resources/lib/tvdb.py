#
#      Copyright (C) 2013 Tommy Winther
#      http://tommy.winther.nu
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#
import urllib
import urllib2
import re
import ChannelList

from Channel import Channel
from Globals import *

class TVDB(object):
    def __init__(self, api_key='01F0668B2FC765B9'):
        self.apikey = api_key
        self.baseurl = 'http://thetvdb.com'

    def __repr__(self):
        return 'TVDB(baseurl=%s, apikey=%s)' % (self.baseurl, self.apikey)

    def _buildUrl(self, cmd, parms={}):
        url = '%s/api/%s?%s' % (self.baseurl, cmd, urllib.urlencode(parms))
        #self.log(url)
        return url

    def getIdByZap2it(self, zap2it_id):
        try:
            response = urllib2.urlopen(self._buildUrl('GetSeriesByRemoteID.php', {'zap2it' : zap2it_id})).read()
            tvdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
            match = tvdbidRE.search(response)
            if match:
                return match.group(1)
            else:
                return 0
        except:
            return 0

    def getEpisodeByAirdate(self, tvdbid, airdate):
        try:
            response = urllib2.urlopen(self._buildUrl('GetEpisodeByAirDate.php', {'apikey' : self.apikey, 'seriesid' : tvdbid, 'airdate' : airdate})).read()
            return response
        except:
            return ''

    def getIdByShowName(self, showName):
        try:
            #NOTE: This assumes an exact match. It is possible to get multiple results though. This could be smarter
            response = urllib2.urlopen(self._buildUrl('GetSeries.php', {'seriesname' : showName})).read()
            tvdbidRE = re.compile('<id>(.+?)</id>', re.DOTALL)
            match = tvdbidRE.search(response)
            if match:
                return match.group(1)
            else:
                return 0
        except:
            return 0
