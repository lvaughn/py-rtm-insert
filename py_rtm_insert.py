### A simple script to take a series of tasks (one per line) and
### Add them to Remember The Milk using their API (details
### at https://www.rememberthemilk.com/services/api/)
###
### All tasks are moved to today if they don't get one set by default
### (i.e., the task as parsed by RTM doesn't assign them one).  This
### may seem weird, but it fits my work flow.
###
### Designed to be run inside of Pythonista on an iOS device.
### This limits some of the libraries we can use as Pythonista
### has a pretty limited subset up Python (hence we get to re-invent
### the wheel here). On the other hand, PROGRAMING!  On iOS! So that's
### useful.

import json
import sys
import urllib2
import os
import plistlib
import webbrowser
from urllib import quote_plus
from hashlib import md5

# You can get an API key and shared secret here at
# https://www.rememberthemilk.com/services/api/keys.rtm
API_KEY = 'YOUR-API-KEY-HERE'
SHARED_SECRET = 'YOUR-SHARED-SECRET-HERE'
    
AUTH_URL='http://www.rememberthemilk.com/services/auth/'
SERVICE_URL = 'https://api.rememberthemilk.com/services/rest/'
AUTH_FILENAME = 'rtm_auth.plist'

class RTM(object):
    """
    Handles all interaction with Remember The Milk
    """
    def __init__(self, api_key, shared_secret):
        """
        Parameters:
          api_key - The RTM API key
          shared_secret - The RTM shared secret
        """
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.frob = None
        self.token = None

    def _sign(self, args):
        """
        Take the arguments to an API call and sign them.

        See https://www.rememberthemilk.com/services/api/authentication.rtm for more info
        """
        elements = [self.shared_secret]
        for key in sorted(args.keys()):
            elements.append(key)
            elements.append(args[key].encode('utf-8'))
        return md5(''.join(elements)).hexdigest()

    def call(self, method, call_args={}):
        """
        Calls an API method and decodes the result

        Arguments:
           method - The method we're calling (e.g., "rtm.tasks.add")
           call_args - Any named arguments required by that method
        """
        args = dict(call_args)
        args['method'] = method
        args['format'] = 'json'
        args['api_key'] = self.api_key
        if self.token is not None:
            args['auth_token'] = self.token
        sig = self._sign(args)
        url = "%s?%s&api_sig=%s" % (SERVICE_URL, '&'.join([k + '=' + quote_plus(args[k]) for k in args.keys()]), sig)
        response = urllib2.urlopen(url)
        return json.loads(response.read())

    def getFrob(self):
        """
        Get's a frob so we can authenticate against RTM. The frob is used to keep track of the login process.

        https://www.rememberthemilk.com/services/api/methods/rtm.auth.getFrob.rtm
        """
        results = self.call('rtm.auth.getFrob')
        frob = results['rsp']['frob']
        return frob

    def getAuthURL(self, perms='delete'):
        """
        Get's a URL to allow us to continue with auth.

        See the "Desktop" section on https://www.rememberthemilk.com/services/api/authentication.rtm

        Parameters:
          perms - The level of access for the login (one of "read", "write" or "delete")
        """
        frob = self.getFrob()
        args = {'api_key': self.api_key,
                'perms': perms,
                'frob': frob}
        sig = self._sign(args)
        url = "%s?%s&api_sig=%s" % (AUTH_URL, '&'.join([k + '=' + quote_plus(args[k]) for k in args.keys()]), sig)
        self.frob = frob
        return url

    def finishAuth(self):
        """
        Finishes the Auth process started by getAuthURL().
        """
        results = self.call('rtm.auth.getToken', {'frob': self.frob})
        self.token = results['rsp']['auth']['token']
        plistlib.writePlist(results['rsp'], AUTH_FILENAME)
        return self.token

    def addTask(self, name, timeline=None):
        """
        Adds a task to RTM.  If no timeline is specified, one is created. We use RTM's advanced parsing (so
        that saying something like "Give up all hope tomorrow !2" yields a task ("give up all hope") due
        tomorrow with a priority of 2.

        If the parser doesn't give it a due date, set it to today (which works well with the RTM's Gmail
        integration).

        Parameters:
           name - The name of the task (to be parsed by RTM).
           timeline - The timeline to add the task to.  Optional, but if you have several tasks to add,
                      it's faster to only create one. 
        """
        if timeline is None:
            timeline = self.createTimeline()
        result = self.call('rtm.tasks.add', 
                           {'timeline': timeline,
                            'name': name,
                            'parse': '1'})
        lst = result['rsp']['list']
        taskseries = lst['taskseries']
        task = taskseries['task']

        # If there's no due date, set it as today
        if task['due'] == '':
            self.call('rtm.tasks.setDueDate', 
                      {'timeline': timeline,
                       'task_id': task['id'],
                       'taskseries_id': taskseries['id'],
                       'list_id': lst['id'],
                       'parse': '1',
                       'due': 'today'})

    def createTimeline(self):
        """
        All calls to create tasks require a timeline.  This creates one.
        """ 
        resp = self.call('rtm.timelines.create')
        return resp['rsp']['timeline']

    def login(self, perms='delete'):
        """
        This performs the login to RTM. It first checks to see if it has credentials
        from a previous run.  If so, it checks to see if the token is still good.
        If there is no previous token, or RTM isn't accepting it for whatever reason,
        it launches a modal webbrowser to handle auth and then completes the process.

        Parameters:
          perms - The level of access we're requesting  (one of "read", "write" or "delete")
        """
        if os.path.exists(AUTH_FILENAME):
            auth = plistlib.readPlist(AUTH_FILENAME)
            if auth is not None:
                self.token = auth['auth']['token']
                rsp = self.call('rtm.auth.checkToken' )
                try:
                    if rsp['rsp']['stat'] == 'ok':
                        return self.token
                except:
                    pass # fall through, something blew up
            # If that doesn't work for any reason, delete those files and log in
            self.token = None
            os.remove(AUTH_FILENAME)

        url = self.getAuthURL(perms='write')
        webbrowser.open(url, modal=True)
        self.finishAuth()

# Our main body, log in, create the tasks, and head back to drafts.
if __name__ == "__main__":
    rtm = RTM(API_KEY, SHARED_SECRET)
    rtm.login(perms='write')

    # I find a little feedback about this point in the process is nice
    print "Creating task(s)"
    timeline = rtm.createTimeline()
    for task in [s.strip() for s in sys.argv[1].split("\n")]:
        if len(task) > 0:
            rtm.addTask(task, timeline)
            
    # We're done, go back to Drafts
    webbrowser.open("drafts://", modal=False, stop_when_done=True)
        
