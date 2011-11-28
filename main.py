#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import gdata
import atom
import random
import re
import datetime
import logging
import webapp2
import jinja2

from google.appengine.api import memcache
from google.appengine.runtime import DeadlineExceededError
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

class RedirectHandler(webapp2.RequestHandler):
    def get(self):
        # memcache.flush_all()
        allhrefs = memcache.get("allhrefs")
        if allhrefs is None:
            logging.info('cache miss')
            allhrefs = self.get_hrefs()
            memcache.set("allhrefs", allhrefs, 43200)
        else:
            logging.info('cache hit')
        
        self.redirect(allhrefs[random.randint(0,len(allhrefs) - 1)])

    def get_hrefs(self):
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
            logging.info('%d urls fetched, fetch number %d' %(len(feed.entry), i + 1))
            allhrefs.extend([entry.link[-1].href for entry in feed.entry])
            
            if len(feed.entry) == 500:
                i += 1
            else:
                break
        
        logging.info('retrieved %d urls total' %len(allhrefs))
        return allhrefs

class StayPageHandler(webapp2.RequestHandler):
    def get(self):
        try:
            memcache.flush_all()
            entries = memcache.get("entries")
            if entries is None:
                logging.info('cache miss')
                entries = self.get_cached_entries()
                memcache.set("entries", entries, 43200)
            elif len(entries[0]) != 5: # check for 5 elements per entry
                logging.info('flushing memcache')
                memcache.flush_all()
                entries = self.get_cached_entries()
                memcache.add("entries", entries, 43200)
            else:
                logging.info('cache hit')
    
            num = random.randint(0,len(entries)-1)
            logging.info("num: %s" % num)
            entry = entries[num]
            # entry = entries[0]
            # entry = entries[-472]
            # entry = entries[-165]
    
            template_values = { 'entry' : entry, }
    
            template = jinja_environment.get_template('stay.html')
            
            self.response.out.write(template.render(template_values))
        except DeadlineExceededError:
            return redirect('/stay')
            
        
    def get_cached_entries(self):
        blogger_service = service.GDataService()
        blogger_service.service = 'blogger'
        blogger_service.server = 'www.blogger.com'
        blogger_service.ssl = False
        query = service.Query()
        query.feed = '/feeds/6752139154038265086/posts/default'
        query.max_results = 500
        
        entries = []
        i = 0
        while 1:
            query.start_index = i*500 + 1
            feed = blogger_service.Get(query.ToUri())
            logging.info('%d entries fetched, fetch number %d' %(len(feed.entry), i + 1))
            entries.extend(feed.entry)
            
            if len(feed.entry) == 500:
                i += 1
            else:
                break
        
        logging.info('retrieved %d entries total' %len(entries))
        
        cachedentries = map(self.format_entry, entries)
        
        return cachedentries
    
    def format_entry(self, entry):
        
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

app = webapp2.WSGIApplication([
    ('/stay/?', StayPageHandler), 
    ('.*', RedirectHandler)])
