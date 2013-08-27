#  This file is part of mylar.
#
#  mylar is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  mylar is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with mylar.  If not, see <http://www.gnu.org/licenses/>.

from mylar import logger
import base64
import cherrypy
import urllib
import urllib2
import mylar
from httplib import HTTPSConnection
from urllib import urlencode
import os.path
import subprocess
import lib.simplejson as simplejson

# This was obviously all taken from headphones with great appreciation :)

class PROWL:

    keys = []
    priority = []

    def __init__(self):
        self.enabled = mylar.PROWL_ENABLED
        self.keys = mylar.PROWL_KEYS
        self.priority = mylar.PROWL_PRIORITY   
        pass

    def conf(self, options):
        return cherrypy.config['config'].get('Prowl', options)

    def notify(self, message, event):
        if not mylar.PROWL_ENABLED:
            return

        http_handler = HTTPSConnection("api.prowlapp.com")
                                                
        data = {'apikey': mylar.PROWL_KEYS,
                'application': 'Mylar',
                'event': event,
                'description': message.encode("utf-8"),
                'priority': mylar.PROWL_PRIORITY }

        http_handler.request("POST",
                                "/publicapi/add",
                                headers = {'Content-type': "application/x-www-form-urlencoded"},
                                body = urlencode(data))
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
                logger.info(u"Prowl notifications sent.")
                return True
        elif request_status == 401: 
                logger.info(u"Prowl auth failed: %s" % response.reason)
                return False
        else:
                logger.info(u"Prowl notification failed.")
                return False

    def updateLibrary(self):
        #For uniformity reasons not removed
        return

    def test(self, keys, priority):

        self.enabled = True
        self.keys = keys
        self.priority = priority

        self.notify('ZOMG Lazors Pewpewpew!', 'Test Message')
        
class NMA:

    def __init__(self):
    
        self.apikey = mylar.NMA_APIKEY
        self.priority = mylar.NMA_PRIORITY
        
    def _send(self, data):
        
        url_data = urllib.urlencode(data)
        url = 'https://www.notifymyandroid.com/publicapi/notify'
        
        req = urllib2.Request(url, url_data)

        try:
            handle = urllib2.urlopen(req)
        except Exception, e:
            logger.warn('Error opening NotifyMyAndroid url: ' % e)
            return

        response = handle.read().decode(mylar.SYS_ENCODING)
        
        return response     
        
    def notify(self, ComicName=None, Year=None, Issue=None, snatched_nzb=None):
    
        apikey = self.apikey
        priority = self.priority
        
        if snatched_nzb:
            event = snatched_nzb + " snatched!"
            description = "Mylar has snatched: " + snatched_nzb + " and has sent it to SABnzbd+"
        else:
            event = ComicName + ' (' + Year + ') - Issue #' + Issue + ' complete!'
            description = "Mylar has downloaded and postprocessed: " + ComicName + ' (' + Year + ') #' + Issue
    
        data = { 'apikey': apikey, 'application':'Mylar', 'event': event, 'description': description, 'priority': priority}

        logger.info('Sending notification request to NotifyMyAndroid')
        request = self._send(data)
        
        if not request:
            logger.warn('Error sending notification request to NotifyMyAndroid')        
        
# 2013-04-01 Added Pushover.net notifications, based on copy of Prowl class above.
# No extra care has been put into API friendliness at the moment (read: https://pushover.net/api#friendly)
class PUSHOVER:

    def __init__(self):
        self.enabled = mylar.PUSHOVER_ENABLED
        self.apikey = mylar.PUSHOVER_APIKEY
        self.userkey = mylar.PUSHOVER_USERKEY
        self.priority = mylar.PUSHOVER_PRIORITY
        # other API options:
        # self.device_id = mylar.PUSHOVER_DEVICE_ID
        # device - option for specifying which of your registered devices Mylar should send to. No option given, it sends to all devices on Pushover (default)
        # URL / URL_TITLE (both for use with the COPS/OPDS server I'm building maybe?)
        # Sound - name of soundfile to override default sound choice
    
    # not sure if this is needed for Pushover
    
    #def conf(self, options):
    # return cherrypy.config['config'].get('Pushover', options)

    def notify(self, message, event):
        if not mylar.PUSHOVER_ENABLED:
            return

        http_handler = HTTPSConnection("api.pushover.net:443")
                                                
        data = {'token': mylar.PUSHOVER_APIKEY,
                'user': mylar.PUSHOVER_USERKEY,
                'message': message.encode("utf-8"),
                'title': event,
                'priority': mylar.PUSHOVER_PRIORITY }

        http_handler.request("POST",
                                "/1/messages.json",
                                body = urlencode(data),
                                headers = {'Content-type': "application/x-www-form-urlencoded"}
                                )
        response = http_handler.getresponse()
        request_status = response.status

        if request_status == 200:
                logger.info(u"Pushover notifications sent.")
                return True
        elif request_status == 401:
                logger.info(u"Pushover auth failed: %s" % response.reason)
                return False
        else:
                logger.info(u"Pushover notification failed.")
                return False

    def test(self, apikey, userkey, priority):

        self.enabled = True
        self.apikey = apikey
        self.userkey = userkey
        self.priority = priority

        self.notify('ZOMG Lazors Pewpewpew!', 'Test Message')
