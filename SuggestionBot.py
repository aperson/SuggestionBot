#/usr/bin/env python3

from credentials import *
import json, signal, sys, time
import urllib.request
from urllib.parse import urlencode
import http.cookiejar


def sigint_handler(signal, frame):
    '''Handles ^c'''
    print('Recieved SIGINT! Exiting...')
    sys.exit(0)


class Reddit:
    def __init__(self, username, password):
        self.cj = http.cookiejar.CookieJar() 
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self.username, self.password = username, password
    
    def login(self):
        '''Logs into reddit.  Returns the modhash.'''
        body = {'user' : self.username, 'passwd' : self.password, 'api_type' : 'json'}
        body = urlencode(body).encode('utf-8')
        
        with self.opener.open('https://www.reddit.com/api/login', body) as w:
            data = json.loads(w.read().decode('utf-8'))
            if 'json' in data:
                self.modhash = data['json']['data']['modhash']
    
    def submit(self, subreddit, title, url=None, text=None):
        body = {'title' : title, 'sr' : subreddit, 'uh' : self.modhash}
        if url:
            body['kind'] = 'link'
            body['url'] = url
        else:
            if text:
                body['text'] = text
            body['kind'] = 'self'
        
        body = urlencode(body).encode('utf-8')
        
        try:
            with self.opener.open('http://www.reddit.com/api/submit', body) as w:
                link = json.loads(w.read().decode('utf-8'))['jquery'][12][3][0]
                return(link)
        except urllib.error.HTTPError:
            print('Failed to submit!')
    
    def get_feed(self, url):
        '''Takes a url sans the http://www.reddit.com and without the .json and returns a dict.'''
        if not url.startswith('/'): url = '/' + url
        if not url.endswith('/'): url = url + '/'
        with self.opener.open('http://www.reddit.com' + url + '.json') as w:
            return(json.loads(w.read().decode('utf-8'))['data']['children'])

def bot():
    submission_template = '''Hello /r/Minecraft, welcome to the official suggestion post for today \
    ({date}).  This is the place where all [Suggestion], [Idea], [Mod Request], and other \
    submissions of the like are to go.  If you have an [Idea], post it as a top-level comment \
    and if it's a good one, hopefully it'll be upvoted and commented on.
    
    Here's the top three comments from the last submission:
    
    {comment_0}
    
    {comment_1}
    
    {comment_2}
    
    ----
    Navigation:
    
    [<last>]({last})'''
    
    comment_template = '''**{author}**[{score}][+{ups}/-{downs}]:\n\n>{comment}'''
    
    title_template = '''[Suggestion] Post for {date}'''
    
    r = Reddit(USERNAME, PASSWORD)
    
    last_submission = r.get_feed('/user/aperson/submitted/')['data']['children'][0]['data']['permalink']
    last_comments = r.get_feed(last_submission)['data']['children']
