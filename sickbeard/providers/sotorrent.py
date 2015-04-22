# -*- coding: latin-1 -*-
# Author: Staros 
# URL: http://code.google.com/p/sickbeard/
#
# This file is part of Sick Beard.
#
# Sick Beard is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Sick Beard is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Sick Beard.  If not, see <http://www.gnu.org/licenses/>.

from bs4 import BeautifulSoup
from sickbeard import classes, show_name_helpers, logger
from sickbeard.common import Quality

import generic
import cookielib
import sickbeard
import urllib
import urllib2
import random

class SOTORRENTProvider(generic.TorrentProvider):

    def __init__(self):
        generic.TorrentProvider.__init__(self, "Sotorrent")
        self.supportsBacklog = True
        
        self.cj = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        self.url = "https://so-torrent.com"

        self.login_done = False

        self.params = "q=&c73=1&c75=1" # English (HD and SD)

    def imageName(self):
        return 'sotorrent.png'
        
    def isEnabled(self):
        return sickbeard.SOTORRENT

    def getSearchParams(self, searchString, audio_lang, subcat, french=None, season=None):
        """ 
            @q string / exact for sphinx research / c[NUMCAT]
        """
        if(season):
            if audio_lang == "en" and french==None:
                self.params = urllib.urlencode({ 'q': searchString})+"&c85=1"
            elif audio_lang == "fr" or french:
                self.params = urllib.urlencode({ 'q': searchString})+"&71=1"
            else:
                self.params = urllib.urlencode({ 'q': searchString})+"&71=1&85=1"
        else:
            if audio_lang == "en" and french==None:
                self.params = urllib.urlencode({ 'q': searchString})+"&c73=1&c75=1"
            elif audio_lang == "fr" or french:
                self.params = urllib.urlencode({ 'q': searchString})+"&c74=1&c72=1"
            else:
                self.params = urllib.urlencode({ 'q': searchString})+"&c74=1&c72=1&c73=1&c75=1"  

        return self.params        
 
    def _get_season_search_strings(self, show, season):
        """
            Don't find how to test this but seem working
        """
        results = []
        possible_show = show_name_helpers.allPossibleShowNames(ep_obj.show)
        list_show = set(possible_show)        
        for show in list_show:
            results.append(self.getSearchParams("+S%02d" % season, show.audio_lang, season))
        return results

    def _get_episode_search_strings(self, ep_obj, french=None):
        """
        """
        results = []
        possible_show = show_name_helpers.allPossibleShowNames(ep_obj.show)
        list_show = set(possible_show)        
        for show in list_show:
            results.append(self.getSearchParams("%s S%02dE%02d" % (show, ep_obj.scene_season, ep_obj.scene_episode), ep_obj.show.audio_lang, french))            
        return results

    
    def _get_title_and_url(self, item):
        return (item.title, item.url)
    
    def getQuality(self, item):
        return item.getQuality()
    
    def _doLogin(self, username, password):

        listeUserAgents = [ 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_5; fr-fr) AppleWebKit/525.18 (KHTML, like Gecko) Version/3.1.2 Safari/525.20.1',
                                                'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/14.0.835.186 Safari/535.1',
                                                'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.2.149.27 Safari/525.13',
                                                'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/528.5+ (KHTML, like Gecko, Safari/528.5+) midori',
                                                'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.107 Safari/535.1',
                                                'Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/312.1 (KHTML, like Gecko) Safari/312',
                                                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11',
                                                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.8 (KHTML, like Gecko) Chrome/17.0.940.0 Safari/535.8' ]

        self.opener.addheaders = [('User-agent', random.choice(listeUserAgents))] 
        data = urllib.urlencode({'username': username,'password': password, 'submit': ' Se Connecter '})
        r = self.opener.open(self.url + '/connect.php',data)
        
        for index, cookie in enumerate(self.cj):
            if (cookie.name == "pwSoTorrent"): self.login_done = True

        if not self.login_done:
            logger.log(u"Unable to login to so-torrent. Please check username and password.", logger.WARNING) 
        
        if self.login_done:
            logger.log(u"Login to so-torrent successful", logger.MESSAGE) 

    def _doSearch(self, searchString, show=None, season=None, french=None):
        if not self.login_done:
            self._doLogin(sickbeard.SOTORRENT_USERNAME, sickbeard.SOTORRENT_PASSWORD)

        results = []

        search_url = "{0}/sphinx.php?{1}".format(self.url, searchString.replace('!',''))
        req = self.opener.open(search_url)
        page = BeautifulSoup(req)

        torrent_table = page.find("table", {"id" : "torrent_list"})
        if torrent_table:
            logger.log(u"So-torrent found shows ! " , logger.DEBUG)  
            torrent_rows = torrent_table.findAll("tr", {"id" : "infos_sphinx"})

            for row in torrent_rows:
                release = row.strong.string
                id_search = row.find("img", {"alt" : "+"})
                id_torrent = id_search['id'].replace('expandoGif', '')
                download_url = "https://so-torrent.com/get.php?id={0}".format(id_search['id'].replace('expandoGif', ''))
                id_quality = Quality.nameQuality(release)

                if show and french==None:
                       results.append(SOTORRENTSearchResult(self.opener, release, download_url, id_quality, str(show.audio_lang)))
                elif show and french:
                   results.append(SOTORRENTSearchResult(self.opener, release, download_url, id_quality, 'fr'))
                else:
                    results.append(SOTORRENTSearchResult(self.opener, release, download_url, id_quality))

        else:
            logger.log(u"No table founded.", logger.DEBUG)
            self.login_done = False             
        return results
    
    def getResult(self, episodes):
        """
        Returns a result of the correct type for this provider
        """
        result = classes.TorrentDataSearchResult(episodes)
        result.provider = self

        return result    
    
class SOTORRENTSearchResult:
    def __init__(self, opener, title, url, quality, audio_langs=None):
        self.opener = opener
        self.title = title
        self.url = url
        self.quality = quality
        self.audio_langs=audio_langs

    def getNZB(self):
        return self.opener.open( self.url , 'wb').read()             

    def getQuality(self):
        return self.quality

provider = SOTORRENTProvider()


