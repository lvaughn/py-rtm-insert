import json
import sys
import urllib2
import os
import plistlib
import webbrowser
from urllib import quote_plus
from hashlib import md5

API_KEY = 'YOUR-API-KEY-HERE'
SHARED_SECRET = 'YOUR-SHARED-SECRET-HERE'
    
AUTH_URL='http://www.rememberthemilk.com/services/auth/'
SERVICE_URL = 'https://api.rememberthemilk.com/services/rest/'
AUTH_FILENAME = 'rtm_auth.plist'

class RTM(object):
    def __init__(self, api_key, shared_secret):
        self.api_key = api_key
        self.shared_secret = shared_secret
        self.frob = None
        self.token = None

    def _sign(self, args):
        elements = [self.shared_secret]
        for key in sorted(args.keys()):
            elements.append(key)
            elements.append(args[key].encode('utf-8'))
        return md5(''.join(elements)).hexdigest()

    def call(self, method, call_args={}):
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
        results = self.call('rtm.auth.getFrob')
        frob = results['rsp']['frob']
        return frob

    def getAuthURL(self, perms='delete'):
        frob = self.getFrob()
        args = {'api_key': self.api_key,
                'perms': perms,
                'frob': frob}
        sig = self._sign(args)
        url = "%s?%s&api_sig=%s" % (AUTH_URL, '&'.join([k + '=' + quote_plus(args[k]) for k in args.keys()]), sig)
        self.frob = frob
        return url

    def finishAuth(self):
        results = self.call('rtm.auth.getToken', {'frob': self.frob})
        self.token = results['rsp']['auth']['token']
        plistlib.writePlist(results['rsp'], AUTH_FILENAME)
        return self.token

    def addTask(self, name, timeline=None):
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
        resp = self.call('rtm.timelines.create')
        return resp['rsp']['timeline']

    def login(self, perms='delete'):
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
        
if __name__ == "__main__":
    rtm = RTM(API_KEY, SHARED_SECRET)
    rtm.login(perms='write')
    print "Creating task(s)"
    timeline = rtm.createTimeline()
    for task in [s.strip() for s in sys.argv[1].split("\n")]:
        if len(task) > 0:
            rtm.addTask(task, timeline)
    webbrowser.open("drafts://", modal=False, stop_when_done=True)
        
