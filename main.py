#!/usr/bin/env python
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import memcache
from gdata import service
import gdata
import atom
import random

class MainHandler(webapp.RequestHandler):
  def get(self):
    allhrefs = memcache.get("allhrefs")
    if allhrefs is None:
      allhrefs = self.get_hrefs()
      memcache.add("allhrefs", allhrefs, 3600)
    
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
		

def main():
    application = webapp.WSGIApplication([('/', MainHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
