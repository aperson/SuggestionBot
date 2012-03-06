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
        '''Makes a submission on reddit and returns the url.'''
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
            output = json.loads(w.read().decode('utf-8'))
            if 'data' in output:
                return output['data']['children']
            else:
                # We don't care about the .self text of the last submission
                return output[1]['data']['children']

def bot():
    '''This is the main bot function that, when ran, will grab the last submission+comments, edit
    the last submission, and create the next submission for the day.'''
    
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
    
    comment_template = '''**{author}**[{score}][+{ups}/-{downs}]:\n\n>{body}'''
    
    # login
    r = Reddit(USERNAME, PASSWORD)
    r.login()
    
    # get prequisite info about last submission
    submission_history = r.get_feed('/user/{}/submitted/'.format(USERNAME))
    
    # This wont work unless we have an account dedicated for the bot, which we don't atm.
    #last_submission = r.get_feed('/user/{}/submitted/'.format('USERNAME'))[0]['data']['permalink']
    #last_comments = r.get_feed(last_submission')['data']['children']
    # This will because aperson would never start a submission with [Suggestion]:
    for i in submission_history:
        if i['data']['title'].startswith('[Suggestion]'):
            last_url = i['data']['permalink']
            last_comments = r.get_feed(last_url)
            break
    
    # build from the comment_template(s) (sometimes I don't feel like doing this the 'right' way)
    comment_0 = comment_template.format(author=last_comments[0]['data']['author'],
                                         score=last_comments[0]['data']['score'],
                                         ups=last_comments[0]['data']['ups'],
                                         downs=last_comments[0]['data']['downs'],
                                         body=last_comments[0]['data']['body']
                                        )
    
    comment_1 = comment_template.format(author=last_comments[1]['data']['author'],
                                         score=last_comments[1]['data']['score'],
                                         ups=last_comments[1]['data']['ups'],
                                         downs=last_comments[1]['data']['downs'],
                                         body=last_comments[1]['data']['body']
                                        )
    
    comment_2 = comment_template.format(author=last_comments[2]['data']['author'],
                                         score=last_comments[2]['data']['score'],
                                         ups=last_comments[2]['data']['ups'],
                                         downs=last_comments[2]['data']['downs'],
                                         body=last_comments[2]['data']['body']
                                        )
    
    submission_title = '''[Suggestion] Post for {date}'''.format(date=time.strftime('%y/%m/%d')
    submission_text = submission_template.format(comment_0=comment_0, comment_1=comment_1,
                                                  comment_2=comment_2, last=last_url)
