#!/usr/bin/env python
import os
import gdata
import atom
import random
import re
import datetime
import logging

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from gdata import service

class RedirectHandler(webapp.RequestHandler):
    def get(self):
        allhrefs = memcache.get("allhrefs")
        if allhrefs is None:
            logging.info('cache miss')
            allhrefs = self.get_hrefs()
            memcache.add("allhrefs", allhrefs, 43200)
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
        feed = blogger_service.Get(query.ToUri())
        logging.info('%d urls fetched, fetch number %d' %(len(feed.entry), 1))
                
        allhrefs = map(lambda x: x.link[-1].href, feed.entry)

        i = 1
        while len(feed.entry) == 500:
            query.start_index = i*500 + 1
            feed = blogger_service.Get(query.ToUri())
            logging.info('%d urls fetched, fetch number %d' %(len(feed.entry), i + 1))
            for entry in feed.entry:
                allhrefs.append(entry.link[-1].href)
            i += 1
        
        logging.info('retrieved %d urls total' %len(allhrefs))
        return allhrefs

class StayPageHandler(webapp.RequestHandler):
    def get(self):
        entries = memcache.get("entries")
        # entries = None
        # memcache.flush_all()
        if entries is None:
            logging.info('cache miss')
            entries = self.get_cached_entries()
            memcache.add("entries", entries, 43200)
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
        #entry = entries[0]
        # entry = entries[-472]
        
        template_values = { 'entry' : entry, }

        path = os.path.join(os.path.dirname(__file__), 'stay.html')
        self.response.out.write(template.render(path, template_values))
        
    def get_cached_entries(self):
        blogger_service = service.GDataService()
        blogger_service.service = 'blogger'
        blogger_service.server = 'www.blogger.com'
        blogger_service.ssl = False
        query = service.Query()
        query.feed = '/feeds/6752139154038265086/posts/default'
        query.max_results = 500
        feed = blogger_service.Get(query.ToUri())
        logging.info('%d entries fetched, fetch number %d' %(len(feed.entry), 1))
        entries = feed.entry
        
        i = 1
        while len(feed.entry) == 500:
            query.start_index = i*500 + 1
            feed = blogger_service.Get(query.ToUri())
            logging.info('%d entries fetched, fetch number %d' %(len(feed.entry), i + 1))
            entries.extend(feed.entry)
            i += 1
        
        logging.info('retrieved %d entries total' %len(entries))
        
        cachedentries = map(self.format_entry, entries)

        return cachedentries
    
    def format_entry(self, entry):
        
        imgurl_re = re.compile(r'href="([^"]*)')
        
        xml_style_re = re.compile(r'<(?:xml|style)>.*?</(?:xml|style)>')
        ws_re = re.compile(r'\s+')
        ws2_re = re.compile(r' <')
        ie_re = re.compile(r'<!--.*?-->')
        non_br_re = re.compile(r'<(?!br).*?>')
        br_re = re.compile('(?:<br *?/?>)')
        n_re = re.compile('\n')
        
        title = entry.title.text
        content = entry.content.text
        imgurl = imgurl_re.findall(content)
        content = xml_style_re.sub(r'', content)
        content = ws_re.sub(r' ', content)
        content = ws2_re.sub(r'<', content)
        content = non_br_re.sub(r'', content)
        content = br_re.sub(r'\n', content)
        content = content.strip()
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

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    application = webapp.WSGIApplication([('/stay/?', StayPageHandler), ('.*', RedirectHandler)])
    util.run_wsgi_app(application)

if __name__ == '__main__':
        main()
