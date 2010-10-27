#!/usr/bin/env python
import os
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from gdata import service
import gdata
import atom
import random
import re
import datetime
import string

class RedirectHandler(webapp.RequestHandler):
  def get(self):
    allhrefs = memcache.get("allhrefs")
    if allhrefs is None:
      allhrefs = self.get_hrefs()
      memcache.add("allhrefs", allhrefs, 43200)
    
    self.redirect(allhrefs[random.randint(0,len(allhrefs) - 1)])

  def get_hrefs(self):
    blogger_service = service.GDataService()
    blogger_service.service = 'blogger'
    blogger_service.server = 'www.blogger.com'
    blogger_service.ssl = False
    query = service.Query()
    query.feed = '/feeds/6752139154038265086/posts/default'
    query.max_results = 400
    feed = blogger_service.Get(query.ToUri())
    
    allhrefs = []
    for entry in feed.entry:
      allhrefs.append(entry.link[-1].href)
		
    i = 1
    while len(feed.entry) == 400:
      query.start_index = i*400 + 1
      feed = blogger_service.Get(query.ToUri())
      for entry in feed.entry:
        allhrefs.append(entry.link[-1].href)
      i += 1

    return allhrefs

class StayPage(webapp.RequestHandler):
  def get(self):
    entries = memcache.get("entries")
    if entries is None:
      entries = self.get_cached_entries()
      memcache.add("entries", entries, 43200)
    
    entry = entries[random.randint(0,len(entries)-1)]
    
    template_values = {
                'imgurl': entry[0],
                'content': entry[1],
                'date': entry[2]
                }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))
    
  def get_cached_entries(self):
    blogger_service = service.GDataService()
    blogger_service.service = 'blogger'
    blogger_service.server = 'www.blogger.com'
    blogger_service.ssl = False
    query = service.Query()
    query.feed = '/feeds/6752139154038265086/posts/default'
    query.max_results = 400
    feed = blogger_service.Get(query.ToUri())
    entries = feed.entry

    i = 1
    while len(feed.entry) == 400:
      query.start_index = i*400 + 1
      feed = blogger_service.Get(query.ToUri())
      entries.extend(feed.entry)
      i += 1

    cachedentries = []
    for entry in entries:
      imgurl = re.findall('href="([^"]*)"', entry.content.text)[0]
      content = re.sub('<br[ ]*/>', '\n', entry.content.text)
      content = re.sub('<.*?>', ' ', content)
      content = string.strip(content)
      # content = re.findall('</a>[<br />|<div>|</div>]*(.*)</div', entry.content.text)
      date = datetime.datetime.strptime(entry.published.text[:10], "%Y-%m-%d").strftime("%B %d %Y")
      # if imgurl:
      #   imgurl = imgurl[0]
      # else:
      #   imgurl = ""
      # if content:
      #   # content = re.findall('(.*)</div>', content[0])
      #   # if content:
      #     content = content[0]
      #   # else:
      #   #      content = ""
      # else:
      #   content = ""
      
      cachedentry = [imgurl, content, date]
      cachedentries.append(cachedentry)

    return cachedentries


def main():
    application = webapp.WSGIApplication([('/', RedirectHandler),
                                            ('/stay', StayPage)],
                                            debug = True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
