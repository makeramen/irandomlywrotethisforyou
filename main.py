#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import random
import re
import datetime
import logging
import webapp2
import jinja2

from google.appengine.api import memcache
from gdata import service

logging.getLogger().setLevel(logging.DEBUG)

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__), encoding='utf-8'))


imgurl_re = re.compile(r'href="([^"]*)')

xml_style_re = re.compile(r'<(?:xml|style)>.*?</(?:xml|style)>')
ws_re = re.compile(r'\s+')
ws2_re = re.compile(r' <')
ie_re = re.compile(r'<!--.*?-->')
non_br_p_re = re.compile(r'<\s*(?!br|/?(?:p|div)).*?>')
br_re = re.compile(r'<br *?/?>')
p_re = re.compile(r'</?(?:p|div).*?>')
n_re = re.compile(r'\n')
dbln_re = re.compile(r'\n{3,}')

bri_urls = (
    "http://www.iwrotethisforyou.me/2009/07/well-of-dreams.html",
    "http://www.iwrotethisforyou.me/2010/05/avoidance-of-pain.html",
    "http://www.iwrotethisforyou.me/2008/04/path-we-walk.html",
    "http://www.iwrotethisforyou.me/2007/09/reflection.html",
    "http://www.iwrotethisforyou.me/2009/04/fading-grey.html",
    "http://www.iwrotethisforyou.me/2009/01/things-ive-never-seen-or-heard.html",
    "http://www.iwrotethisforyou.me/2009/06/seat-next-to-you.html",
    "http://www.iwrotethisforyou.me/2009/09/new-colour.html",
    "http://www.iwrotethisforyou.me/2010/05/books-never-written.html",
    "http://www.iwrotethisforyou.me/2010/07/air-never-saw-it-comming.html",
    "http://www.iwrotethisforyou.me/2009/06/moths-dont-die-for-nothing.html",
    "http://www.iwrotethisforyou.me/2009/02/time-we-could-spend.html",
    "http://www.iwrotethisforyou.me/2008/06/clarification.html",
    "http://www.iwrotethisforyou.me/2009/04/beautiful-mess-we-could-be.html",
    "http://www.iwrotethisforyou.me/2009/03/person-in-front-of-me.html",
    "http://www.iwrotethisforyou.me/2012/02/stuff-and-things.html",
    "http://www.iwrotethisforyou.me/2008/10/never-ending-search-for-something-real.html",
    "http://www.iwrotethisforyou.me/2009/10/absence-of-oxygen.html",
    "http://www.iwrotethisforyou.me/2008/08/station.html",
    "http://www.iwrotethisforyou.me/2010/05/untouchable-city.html",
    "http://www.iwrotethisforyou.me/2009/11/heart-rides-on.html",
    "http://www.iwrotethisforyou.me/2007/10/frustration.html",
    "http://www.iwrotethisforyou.me/2009/12/laboratory-in-my-heart.html",
    "http://www.iwrotethisforyou.me/2008/09/big-blue-sea.html",
    "http://www.iwrotethisforyou.me/2012/06/grand-distraction.html",
    "http://www.iwrotethisforyou.me/2012/10/the-night-holds-day-so-softly.html",
    "http://www.iwrotethisforyou.me/2012/10/the-sun-leaves-earth.html",
    "http://www.iwrotethisforyou.me/2012/10/the-language-stripped-naked.html",
    "http://www.iwrotethisforyou.me/2012/08/the-last-land-i-stood-on.html",
    "http://www.iwrotethisforyou.me/2012/07/the-purpose-of-love.html",
    "http://www.iwrotethisforyou.me/2012/06/endless-night-and-all-it-promises.html",
    "http://www.iwrotethisforyou.me/2012/05/defiance-of-different.html",
    "http://www.iwrotethisforyou.me/2012/02/relative-phenomena.html",
    )

def get_hrefs():
    blogger_service = service.GDataService()
    blogger_service.service = 'blogger'
    blogger_service.server = 'www.blogger.com'
    blogger_service.ssl = False
    query = service.Query()
    query.feed = '/feeds/6752139154038265086/posts/default'
    query.max_results = 500
            
    allhrefs = []
    i = 0
    while 1:
        query.start_index = i*500 + 1
        feed = blogger_service.Get(query.ToUri())
        logging.info('%d urls fetched, fetch number %d' % (len(feed.entry), i + 1))
        allhrefs.extend(entry.link[-1].href for entry in feed.entry)
        
        if len(feed.entry) == 500:
            i += 1
        else:
            break
    
    logging.info('retrieved %d urls total' % len(allhrefs))
    return allhrefs

def get_cached_entries():
    blogger_service = service.GDataService()
    blogger_service.service = 'blogger'
    blogger_service.server = 'www.blogger.com'
    blogger_service.ssl = False
    query = service.Query()
    query.feed = '/feeds/6752139154038265086/posts/default'
    query.max_results = 500
    
    bri_entries = []
    entries = []
    i = 0
    while 1:
        query.start_index = i*500 + 1
        feed = blogger_service.Get(query.ToUri())
        logging.info('%d entries fetched, fetch number %d' % (len(feed.entry), i + 1))
        entries.extend(feed.entry)
        
        if len(feed.entry) == 500:
            i += 1
        else:
            break
    
    logging.info('retrieved %d entries total' % len(entries))
    
    cachedentries = tuple(format_entry(e) for e in entries)
    
    return cachedentries

def format_entry(entry):
    
    title = unicode(entry.title.text, 'utf-8')
    
    content = unicode(entry.content.text, 'utf-8')
    
    imgurl = imgurl_re.findall(content)

    content = xml_style_re.sub(r'', content)
    content = ws_re.sub(r' ', content)
    content = ws2_re.sub(r'<', content)
    content = non_br_p_re.sub(r'', content)
    content = br_re.sub(r'\n', content)
    content = p_re.sub(r'\n\n', content)
    content = content.strip()
    content = dbln_re.sub(r'\n\n', content)
    content = n_re.sub(r'<br />', content)

    date = datetime.datetime.strptime(entry.published.text[:10], "%Y-%m-%d").strftime("%A, %B %d, %Y")
    url = entry.link[-1].href
    return {
        'title' : title,
        'date' : date,
        'imgurl' : imgurl,
        'content' : content,
        'url' : url
        }

class RedirectHandler(webapp2.RequestHandler):
    def get(self):
        try:
            # memcache.flush_all()
            allhrefs = memcache.get("allhrefs")
            if allhrefs is None:
                logging.info('cache miss')
                allhrefs = get_hrefs()
                memcache.set("allhrefs", allhrefs, 43200)
            else:
                logging.info('cache hit')
        
            self.redirect(allhrefs[random.randint(0,len(allhrefs) - 1)])
        except Exception as e:
            logging.warning('error, redirecting to self: %s' % e)
            return self.redirect('/')

class StayPageHandler(webapp2.RequestHandler):
    def get(self, bri=None):
        try:
            # memcache.flush_all()
            if bri:
                entries = memcache.get("bri_entries")
            else:
                entries = memcache.get("entries")

            if entries is None:
                logging.info('cache miss')
                entries = get_cached_entries()
                memcache.set("entries", entries, 43200)
                bri_entries = tuple(e for e in entries if e['url'] in bri_urls)
                memcache.set("bri_entries", bri_entries, 43200)
            elif len(entries[0]) != 5: # check for 5 elements per entry
                logging.info('flushing memcache')
                memcache.flush_all()
                entries = get_cached_entries()
                memcache.add("entries", entries, 43200)
                bri_entries = tuple(e for e in entries if e['url'] in bri_urls)
                memcache.set("bri_entries", bri_entries, 43200)
            else:
                logging.info('cache hit')

            if bri:
                entries = memcache.get("bri_entries")
            else:
                entries = memcache.get("entries")
    
            num = random.randint(0,len(entries)-1)
            logging.info("num: %s" % num)
            entry = entries[num]
            # entry = entries[0]
            # entry = entries[-472]
            # entry = entries[-165]
    
            template_values = { 'entry' : entry, }
    
            template = jinja_environment.get_template('stay.html')
            
            self.response.out.write(template.render(template_values))
        except Exception as e:
            logging.exception(e)
            logging.warning('error, redirecting to self: %s' % e)
            if bri:
                return self.redirect('/bri')
            else:
                return self.redirect('/stay')
            

app = webapp2.WSGIApplication([
    ('/stay/?', StayPageHandler),
    ('/(bri)/?', StayPageHandler),
    ('.*', RedirectHandler)])
