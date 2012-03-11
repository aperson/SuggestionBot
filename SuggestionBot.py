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


class Bot:
    def __init__(self, username, password):
        self.cj = http.cookiejar.CookieJar() 
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        self._login(username, password)
    
    def _login(self, username, password):
        '''Logs into reddit.  Returns the modhash.'''
        body = {'user' : username, 'passwd' : password, 'api_type' : 'json'}
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
    
    def edit_submission(self, thing_id, text):
        '''Edits the submission text for a given thing_id.'''
        body = {'thing_id' : thing_id, 'text' : text, 'uh' : self.modhash}
        body = urlencode(body).encode('utf-8')
        try:
            with self.opener.open('http://www.reddit.com/api/editusertext', body) as w:
                return True
        except urllib.error.HTTPError:
            return False
    
    def get_feed(self, url):
        '''Takes a url sans the http://www.reddit.com and returns a dict.'''
        if not url.startswith('/'): url = '/' + url
        if not url.endswith('/'): url = url + '/'
        if not '.json' in url: url += '.json'
        with self.opener.open('http://www.reddit.com' + url) as w:
            output = json.loads(w.read().decode('utf-8'))
            if 'data' in output:
                return output['data']['children']
            else:
                return output
    
    def puburl(self, url):
        '''Creates or updates a tiny.cc url.  If PUBURL does not exist in the credentials file, it will
        be created.  Otherwise, we're doing an update'''
        
        body = {'login': TINYCC, 'apiKey' : TINYCCKEY, 'c' : 'rest_api', 'version' : '2.0.3', 
                'format' : 'json', 'longUrl' : url, 'hash' : PUBURL, 'shortUrl' : PUBURL}
        
        if PUBURL:
            body['m'] = 'edit'
        else:
            body['m'] = 'create'
        with self.opener.open('http://tiny.cc/?' + urlencode(body)) as w:
            return json.loads(w.read().decode('utf-8'))['results']

def main():
    '''This is the main bot function that, when ran, will grab the last submission+comments, edit
    the last submission, and create the next submission for the day.'''
    
    submission_base = '''**Having trouble seeing just the suggestions?**  *Try clicking\
    [this](http://db.tt/ZU2USTiK)*.\n\n-----\n\nHello /r/Minecraft, welcome to the official suggestion post\
    for this week. This is the place where all [Suggestion], [Idea], [Mod Request], and other\
    submissions of the like are to go.  If you have an [Idea], post it as a top-level comment and\
    if it's a good one, hopefully it'll be upvoted and commented on.\n\nHere's the top three\
    comments from the last submission:'''
    
    navigation_template = '''\n\n----\n\nThis submission is for Minecraft suggestions only.  If you\
    have an idea or suggestion regarding the subreddit, please direct it at the\
    [moderators](http://www.reddit.com/message/compose?to=%2Fr%2FMinecraft). Any non-Minecraft\
    related suggestions will be removed.\
    \n\nNavigation:\n\n[<- prev ]({}?depth=1)'''
    
    comment_template = '''\n\n**[](/{flair}) [{author}]({link})** [{score}][+{ups}/-{downs}]:\n\n>{body}'''
    
        
    strfdate = time.strftime('%W')
    
    submission_title = '''[Suggestion] Post for week #{}'''.format(strfdate)
    
    # dict to translate css class names to sprite code names
    flairs = {'blaze' : 'blaze', 'cavespider' : 'cavespider', 'chicken' : 'chicken', 'cow' : 'cow',
              'creeper' : 'creeper', 'enderdragon' : 'enderdragon', 'enderman' : 'enderman',
              'ghast' : 'ghast', 'magmacube' : 'magmacube', 'mooshroom' : 'mooshroom', 'pig' : 'pig',
              'silverfish' : 'silverfish', 'skeleton' : 'skeleton', 'slime' : 'slime',
              'snowgolem' : 'snowgolem', 'spider' : 'spider', 'steve' : 'steve', 'squid' : 'squid',
              'testificate' : 'testificate', 'wolf' : 'wolf', 'zombie' : 'zombie',
              'zombiepigman' : 'zombiepigman', 'sheep' : 'sheep', 'lightgraysheep' : 'sheep_lightgray',
              'graysheep' : 'sheep_gray', 'blacksheep' : 'sheep_black', 'brownsheep' : 'sheep_brown',
              'pinksheep' : 'sheep_pink', 'redsheep' : 'sheep_red', 'orangesheep' : 'sheep_orange',
              'yellowsheep' : 'sheep_yellow', 'limesheep' : 'sheep_lime', 'greensheep' : 'sheep_green',
              'lightbluesheep' : 'sheep_lightblue', 'cyansheep' : 'sheep_cyan', 'bluesheep' : 'sheep_blue',
              'purplesheep' : 'sheep_purple', 'magentasheep' : 'sheep_magenta', 'ozelot' : 'ozelot',
              'catsiamese' : 'cat_siamese', 'catred' : 'cat_red', 'catblack' : 'cat_black',
              'irongolem' : 'iron_golem', 'redstonehelper' : 'redstone', 'painting' : 'painting',
              'rftw' : 'rftw', 'mojang' : 'mojang'}
    
    # login
    b = Bot(USERNAME, PASSWORD)
    time.sleep(2)
    
    # get prequisite info about last submission
    submission_history = b.get_feed('/user/{}/submitted/.json?limit=1'.format(USERNAME))
    time.sleep(2)
    
    # This wont work unless we have an account dedicated for the bot, which we don't atm.
    last_submission = b.get_feed('/user/{}/submitted/'.format(USERNAME))[0]['data']
    if last_submission['title'] == submission_title: sys.exit(0) # Sanity check
    last_url = last_submission['permalink']
    last_thing_id = last_submission['name']
    last_submission = b.get_feed(last_url)
    time.sleep(2)
    last_text = last_submission[0]['data']['children'][0]['data']['selftext']
    last_comments = last_submission[1]['data']['children']
    # This will because aperson would never start a submission with [Suggestion]:
    #for i in submission_history:
        #if i['data']['title'].startswith('[Suggestion]'):
            #last_url = i['data']['permalink']
            #last_thing_id = i['data']['name']
            #last_submission = b.get_feed(last_url)
            #last_text = last_submission[0]['data']['children'][0]['data']['selftext']
            #last_comments = last_submission[1]['data']['children']
            #time.sleep(2)
            #break
    
    top_comments = []
    
    for i in last_comments:
        i['data']['score'] = i['data']['ups'] - i['data']['downs']
        top_comments.append(i['data'])
    
    top_comments.sort(key=lambda x: -x['score'])
    
    formatted_comments = ''
    if top_comments:
        count = 0
        for i in top_comments:
            if i['author'] != '[deleted]':
                count += 1
                if i['author_flair_css_class']:
                    flair = flairs[i['author_flair_css_class']]
                else:
                    flair = 'null'
                
                formatted_comments += comment_template.format(author=i['author'], score=i['score'],
                                                               ups=i['ups'], downs=i['downs'],
                                                               body=i['body'].replace('\n', '\n>'),
                                                               link='/r/{}/comments/{}/a/{}'.format(
                                                               SUBREDDIT, i['link_id'][3:],
                                                               [i['id']), flair=flair
                                                              )
            if count == 3: break
    else:
        formatted_comments = '\n\nLooks like there were no suggestions yesterday.'

    submission_text = submission_base + formatted_comments + navigation_template.format(last_url)
    
    # Submit!
    submission_url = b.submit(SUBREDDIT, submission_title, text=submission_text)
    time.sleep(2)
    
    # Edit the last submission so it includes a <next> link
    b.edit_submission(last_thing_id, '{}|[ next ->]({}?depth=1)'.format(last_text.replace('&lt;', '<'
                                                                 ).replace('&gt;', '>'),
                                                                 submission_url))
    
    # Finally, we need to update the permalink
    # having issues with puburl, pending contact from their devs
    #print(b.puburl(submission_url))
    # So, we hack it:
    with open(DBPATH, 'w') as f:
        f.write('<html><head><meta http-equiv="Refresh" content="0;url={}?depth=1" /></head><body></body></html>'.format(submission_url))

if __name__ == '__main__':
    main()
