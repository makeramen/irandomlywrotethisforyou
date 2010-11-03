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
    elif len(entries[0]) != 5:
      memcache.flush_all()
      entries = self.get_cached_entries()
      memcache.add("entries", entries, 43200)
    
    entry = entries[random.randint(0,len(entries)-1)]
    # entry = entries[506]
    
    template_values = {
                'title' : entry[0],
                'date': entry[1],
                'imgurl': entry[2],
                'content': entry[3],
                'url': entry[4]
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
      title = entry.title.text
      imgurl = re.findall('href="([^"]*)"', entry.content.text)[0]
      content = re.sub('<!--.*?-->', '', entry.content.text)
      content = re.sub('<br[ ]*/>', '\n', content)
      content = re.sub('<.*?>|', '', content)
      content = string.strip(content)
      content = re.sub('\n', '<br />', content)
      date = datetime.datetime.strptime(entry.published.text[:10], "%Y-%m-%d").strftime("%A, %B %d, %Y")
      url = entry.link[-1].href
      cachedentry = [title, date, imgurl, content, url]
      cachedentries.append(cachedentry)

    return cachedentries


def main():
    application = webapp.WSGIApplication([('/', RedirectHandler),
                                            ('/stay', StayPage)])
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
