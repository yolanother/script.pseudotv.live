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
import json
import ChannelList

from Channel import Channel
from Globals import *

class TMDB(object):
    def __init__(self, api_key='c974c461a9767defec862674bf6c704e'):
        self.apikey = api_key
        self.baseurl = 'http://api.themoviedb.org/3'
        try:
            self.imagebaseurl = self._getPosterBaseUrl()
        except:
            pass

    def __repr__(self):
        return 'TMDB(apikey=%s, baseurl=%s, imagebaseurl=%s)' % (self.apikey,self.baseurl,self.imagebaseurl)

    def _buildUrl(self, cmd, parms={}):
        parmsCopy = parms.copy()
        parmsCopy.update({'api_key' : self.apikey})
        url = '%s/%s?%s' % (self.baseurl, cmd, urllib.urlencode(parmsCopy))
        #self.log(url)
        return url

    def _getPosterBaseUrl(self):
        response = json.loads(urllib2.urlopen(urllib2.Request(self._buildUrl('configuration'), headers={"Accept": "application/json"})).read())
        #self.log('Response: \r\n%s' % response)
        return response['images']['base_url']

    def getPosterUrl(self, filename):
        return '%s%s%s' % (self.imagebaseurl, 'w92/', filename)

    def getMovie(self, movieName, year):
        #self.log('movieName: %s' % movieName)
        response = json.loads(urllib2.urlopen(urllib2.Request(self._buildUrl('search/movie', {'query' : movieName, 'year' : year}), headers={"Accept": "application/json"})).read())
        if response['total_results'] > 0:
            #self.log('Response: \r\n%s' % response)
            response = json.loads(urllib2.urlopen(urllib2.Request(self._buildUrl('movie/%s' % (response['results'][0]['id'])), headers={"Accept": "application/json"})).read())
        else:
            #self.log('No matches found for %s' % movieName)
            response = json.loads('{"imdb_id":"", "poster_path":""}')
        return response

    def getIMDBId(self, movieName, year):
        response = self.getMovie(movieName, year)
        return response['imdb_id']
