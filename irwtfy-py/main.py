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
end_trim_re = re.compile(r'__+.*')

bri_urls = (
    "http://www.iwrotethisforyou.me/2007/07/first-sip.html",
    "http://www.iwrotethisforyou.me/2007/08/fur.html",
    "http://www.iwrotethisforyou.me/2007/08/iris.html",
    "http://www.iwrotethisforyou.me/2007/09/building.html",
    "http://www.iwrotethisforyou.me/2007/09/defiance.html",
    "http://www.iwrotethisforyou.me/2007/09/freeze.html",
    "http://www.iwrotethisforyou.me/2007/09/porcelain.html",
    "http://www.iwrotethisforyou.me/2007/09/reflection.html",
    "http://www.iwrotethisforyou.me/2007/09/salt.html",
    "http://www.iwrotethisforyou.me/2007/09/warmth.html",
    "http://www.iwrotethisforyou.me/2007/10/following.html",
    "http://www.iwrotethisforyou.me/2007/10/importance.html",
    "http://www.iwrotethisforyou.me/2007/10/jewels.html",
    "http://www.iwrotethisforyou.me/2007/10/sweet.html",
    "http://www.iwrotethisforyou.me/2007/10/talk.html",
    "http://www.iwrotethisforyou.me/2007/11/finding.html",
    "http://www.iwrotethisforyou.me/2007/11/need.html",
    "http://www.iwrotethisforyou.me/2007/11/pinch.html"
    "http://www.iwrotethisforyou.me/2007/11/sea.html",
    "http://www.iwrotethisforyou.me/2007/11/smiling.html",
    "http://www.iwrotethisforyou.me/2007/11/where.html",
    "http://www.iwrotethisforyou.me/2007/12/meeting.html",
    "http://www.iwrotethisforyou.me/2007/12/sleep.html",
    "http://www.iwrotethisforyou.me/2007/12/watching.html",
    "http://www.iwrotethisforyou.me/2008/01/grasping-of-hands.html",
    "http://www.iwrotethisforyou.me/2008/03/long-ago.html",
    "http://www.iwrotethisforyou.me/2008/04/path-we-walk.html",
    "http://www.iwrotethisforyou.me/2008/04/shades.html"
    "http://www.iwrotethisforyou.me/2008/06/clarification.html",
    "http://www.iwrotethisforyou.me/2008/06/sunshine.html",
    "http://www.iwrotethisforyou.me/2008/08/oranges-lemons.html",
    "http://www.iwrotethisforyou.me/2008/08/price.html",
    "http://www.iwrotethisforyou.me/2008/08/shy.html",
    "http://www.iwrotethisforyou.me/2008/08/station.html",
    "http://www.iwrotethisforyou.me/2008/09/big-blue-sea.html",
    "http://www.iwrotethisforyou.me/2008/09/fact-of-matter.html",
    "http://www.iwrotethisforyou.me/2008/09/place-we-were-in.html",
    "http://www.iwrotethisforyou.me/2008/09/point-of-contact.html",
    "http://www.iwrotethisforyou.me/2008/09/profile.html",
    "http://www.iwrotethisforyou.me/2008/10/directions-we-give.html",
    "http://www.iwrotethisforyou.me/2008/10/never-ending-search-for-something-real.html",
    "http://www.iwrotethisforyou.me/2008/10/shatter-proof.html",
    "http://www.iwrotethisforyou.me/2008/10/walking-away.html",
    "http://www.iwrotethisforyou.me/2008/11/tired-advice.html",
    "http://www.iwrotethisforyou.me/2008/12/water.html",
    "http://www.iwrotethisforyou.me/2009/01/pressure-to-wounded.html",
    "http://www.iwrotethisforyou.me/2009/01/things-ive-never-seen-or-heard.html",
    "http://www.iwrotethisforyou.me/2009/01/world-loves-you-too.html",
    "http://www.iwrotethisforyou.me/2009/02/light-we-fly-to.html",
    "http://www.iwrotethisforyou.me/2009/02/time-we-could-spend.html",
    "http://www.iwrotethisforyou.me/2009/03/heart-beats-per-minute.html",
    "http://www.iwrotethisforyou.me/2009/03/person-in-front-of-me.html",
    "http://www.iwrotethisforyou.me/2009/04/beautiful-mess-we-could-be.html",
    "http://www.iwrotethisforyou.me/2009/04/fading-grey.html",
    "http://www.iwrotethisforyou.me/2009/04/metal-starts-to-twist.html",
    "http://www.iwrotethisforyou.me/2009/04/nature-starts-to-turn.html",
    "http://www.iwrotethisforyou.me/2009/05/way-saturn-turns.html",
    "http://www.iwrotethisforyou.me/2009/06/day-i-got-older.html",
    "http://www.iwrotethisforyou.me/2009/06/moths-dont-die-for-nothing.html",
    "http://www.iwrotethisforyou.me/2009/06/seat-next-to-you.html",
    "http://www.iwrotethisforyou.me/2009/07/needle-and-ink.html",
    "http://www.iwrotethisforyou.me/2009/07/well-of-dreams.html",
    "http://www.iwrotethisforyou.me/2009/09/beakers-id-break.html",
    "http://www.iwrotethisforyou.me/2009/09/corner-of-me-you.html",
    "http://www.iwrotethisforyou.me/2009/09/gun-in-stars.html",
    "http://www.iwrotethisforyou.me/2009/09/new-colour.html",
    "http://www.iwrotethisforyou.me/2009/09/train-of-lies.html",
    "http://www.iwrotethisforyou.me/2009/10/absence-of-oxygen.html",
    "http://www.iwrotethisforyou.me/2009/10/autumn-in-their-eyes.html",
    "http://www.iwrotethisforyou.me/2009/10/deaths-of-millions.html",
    "http://www.iwrotethisforyou.me/2009/10/new-species.html",
    "http://www.iwrotethisforyou.me/2009/10/to-not-do-list.html",
    "http://www.iwrotethisforyou.me/2009/10/wet-hair-and-eyes.html",
    "http://www.iwrotethisforyou.me/2009/11/awol-hearts.html",
    "http://www.iwrotethisforyou.me/2009/11/beauty-of-errors.html",
    "http://www.iwrotethisforyou.me/2009/11/heart-rides-on.html",
    "http://www.iwrotethisforyou.me/2009/11/zodiac-of-one.html",
    "http://www.iwrotethisforyou.me/2009/12/laboratory-in-my-heart.html",
    "http://www.iwrotethisforyou.me/2009/12/ronin-have-names.html"
    "http://www.iwrotethisforyou.me/2010/01/fury-of-water.html",
    "http://www.iwrotethisforyou.me/2010/05/avoidance-of-pain.html",
    "http://www.iwrotethisforyou.me/2010/05/books-never-written.html",
    "http://www.iwrotethisforyou.me/2010/05/fading-glow.html",
    "http://www.iwrotethisforyou.me/2010/05/untouchable-city.html",
    "http://www.iwrotethisforyou.me/2010/06/anthems-for-people-not-places.html",
    "http://www.iwrotethisforyou.me/2010/06/pattern-is-system-is-maze.html",
    "http://www.iwrotethisforyou.me/2010/06/world-is-too-big.html",
    "http://www.iwrotethisforyou.me/2010/07/air-never-saw-it-comming.html",
    "http://www.iwrotethisforyou.me/2010/09/day-tomorrow-came.html",
    "http://www.iwrotethisforyou.me/2010/09/first-crack-is-last.html",
    "http://www.iwrotethisforyou.me/2010/09/molten-core.html",
    "http://www.iwrotethisforyou.me/2010/09/trauma-transmission.html",
    "http://www.iwrotethisforyou.me/2010/09/world-of-one.html",
    "http://www.iwrotethisforyou.me/2010/11/new-singularity.html",
    "http://www.iwrotethisforyou.me/2011/03/superstition-and-fear.html",
    "http://www.iwrotethisforyou.me/2011/08/sound-of-sea.html",
    "http://www.iwrotethisforyou.me/2012/02/relative-phenomena.html",
    "http://www.iwrotethisforyou.me/2012/03/broken-ice-in-your-wake.html",
    "http://www.iwrotethisforyou.me/2012/02/stuff-and-things.html",
    "http://www.iwrotethisforyou.me/2012/04/hidden-depths.html",
    "http://www.iwrotethisforyou.me/2012/04/envy-of-billion-little-unique.html",
    "http://www.iwrotethisforyou.me/2012/05/remaining-of-me.html",
    "http://www.iwrotethisforyou.me/2012/06/endless-night-and-all-it-promises.html",
    "http://www.iwrotethisforyou.me/2012/06/grand-distraction.html",
    "http://www.iwrotethisforyou.me/2012/07/the-purpose-of-love.html",
    "http://www.iwrotethisforyou.me/2012/07/desire-to-live-underwater-forever.html",
    "http://www.iwrotethisforyou.me/2012/08/the-last-land-i-stood-on.html",
    "http://www.iwrotethisforyou.me/2012/10/the-language-stripped-naked.html",
    "http://www.iwrotethisforyou.me/2012/10/the-night-holds-day-so-softly.html",
    "http://www.iwrotethisforyou.me/2012/10/the-sun-leaves-earth.html",
    "http://www.iwrotethisforyou.me/2012/12/the-nature-of-river-is-to-run.html",
    "http://www.iwrotethisforyou.me/2012/12/the-nature-of-river-is-to-run.html",
    "http://www.iwrotethisforyou.me/2014/02/the-hands-you-gave-me.html",
    "http://www.iwrotethisforyou.me/2014/06/the-dreams-on-line.html",
    "http://www.iwrotethisforyou.me/2014/07/the-city-that-sleeps-where-they-fell.html",
    "http://www.iwrotethisforyou.me/2014/08/the-best-i-could-with-what-i-had-in.html",
    "http://www.iwrotethisforyou.me/2014/08/the-world-is-not-as-dark-as-it-seems.html",
    "http://www.iwrotethisforyou.me/2014/09/the-sky-warps-sun.html",
    "http://www.iwrotethisforyou.me/2014/09/the-things-i-make-when-im-alone.html",
    "http://www.iwrotethisforyou.me/2014/11/the-twin-engines.html",
    "http://www.iwrotethisforyou.me/2014/12/the-splinter-of-light.html",
    "http://www.iwrotethisforyou.me/2015/04/the-fire-is-where-were-all-born.html",
    "http://www.iwrotethisforyou.me/2015/06/the-saying-of-when.html",
    "http://www.iwrotethisforyou.me/2015/08/the-box-of-songs.html",
    "http://www.iwrotethisforyou.me/2015/08/the-landscapes-of-you.html",
    "http://www.iwrotethisforyou.me/2015/08/the-uncontrollable.html",
    "http://www.iwrotethisforyou.me/2015/09/the-murder-of-clock.html",
    "http://www.iwrotethisforyou.me/2016/01/the-slow-gentle-continental-drift.html",
    "http://www.iwrotethisforyou.me/2016/02/the-failure-of-prayer.html",
    "http://www.iwrotethisforyou.me/2016/03/the-spider-silk.html",
    "http://www.iwrotethisforyou.me/2016/04/the-terrible-inadequacy-of-entire-life.html",
    "http://www.iwrotethisforyou.me/2016/09/the-remaining-you.html",
    "http://www.iwrotethisforyou.me/2016/10/the-anchors-i-found-in-others.html",
    "http://www.iwrotethisforyou.me/2016/11/the-hard-way.html",
    "http://www.iwrotethisforyou.me/2016/11/the-light-of-all-stars.html",
    # )

# miss_urls = (
    "http://www.iwrotethisforyou.me/2007/09/distance.html",
    "http://www.iwrotethisforyou.me/2007/09/timing.html",
    "http://www.iwrotethisforyou.me/2007/10/alone.html",
    "http://www.iwrotethisforyou.me/2007/10/clouds.html",
    "http://www.iwrotethisforyou.me/2007/10/flame.html",
    "http://www.iwrotethisforyou.me/2007/10/parcel.html",
    "http://www.iwrotethisforyou.me/2007/11/today.html",
    "http://www.iwrotethisforyou.me/2008/02/weather-and-you.html",
    "http://www.iwrotethisforyou.me/2008/08/space-left.html",
    "http://www.iwrotethisforyou.me/2008/11/long-way-home.html",
    "http://www.iwrotethisforyou.me/2009/09/road-trip.html",
    "http://www.iwrotethisforyou.me/2009/10/train-after-dinner.html",
    "http://www.iwrotethisforyou.me/2010/05/day-time-waited-for-me.html",
    "http://www.iwrotethisforyou.me/2010/05/theory-is-still-just-theory.html",
    "http://www.iwrotethisforyou.me/2011/08/negative-space.html",
    "http://www.iwrotethisforyou.me/2011/12/forest-of-stars.html",
    "http://www.iwrotethisforyou.me/2014/10/the-world-of-your-own.html",
    "http://www.iwrotethisforyou.me/2015/01/the-truth-is-its-just-something-to-hold.html",
    "http://www.iwrotethisforyou.me/2016/05/the-rain-of-black-umbrellas.html",
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

    title = unicode(entry.title.text, 'utf-8') if entry.title.text else ""

    content = unicode(entry.content.text, 'utf-8') if entry.content.text else ""

    imgurl = imgurl_re.findall(content)

    if content:
        content = xml_style_re.sub(r'', content)
        content = ws_re.sub(r' ', content)
        content = ws2_re.sub(r'<', content)
        content = non_br_p_re.sub(r'', content)
        content = br_re.sub(r'\n', content)
        content = p_re.sub(r'\n\n', content)
        content = content.strip()
        content = dbln_re.sub(r'\n\n', content)
        content = n_re.sub(r'<br />', content)
        content = end_trim_re.sub(r'', content)

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
            if not entries:
                if bri and memcache.get("entries"):
                    entries = memcache.get('entries')
                    memcache.set("bri_entries", [e for e in entries if e['url'] in bri_urls], 43200)
                    entries = memcache.get('bri_entries')
                    logging.info('reset bri')
                else:
                    logging.info('cache miss')
                    entries = get_cached_entries()
                    memcache.set("entries", entries, 43200)
                    memcache.set("bri_entries", [e for e in entries if e['url'] in bri_urls], 43200)
            elif len(entries[0]) != 5: # check for 5 elements per entry
                logging.info('flushing memcache')
                memcache.flush_all()
                entries = get_cached_entries()
                memcache.add("entries", entries, 43200)
                memcache.set("bri_entries", [e for e in entries if e['url'] in bri_urls], 43200)
            else:
                logging.info('cache hit')

            if bri:
                entries = memcache.get("bri_entries")
            else:
                entries = memcache.get("entries")

            num = random.randint(0,len(entries)-1)
            logging.info("num: %s" % num)
            entry = entries[num]

            if bri:
                entry = entries.pop(num)
                memcache.set("bri_entries", entries)
            else:
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
