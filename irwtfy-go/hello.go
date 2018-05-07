// Copyright 2018 Google Inc. All rights reserved.
// Use of this source code is governed by the Apache 2.0
// license that can be found in the LICENSE file.

package main

import (
	"bytes"
	"context"
	json "encoding/json"
	"errors"
	"html/template"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"

	"google.golang.org/appengine"
	"google.golang.org/appengine/log"
	"google.golang.org/appengine/memcache"
	"google.golang.org/appengine/urlfetch"
)

const blogID string = "6752139154038265086"
const memcacheKey = "minPosts"

var (
	stayTemplate = template.Must(template.ParseFiles("stay.html"))
)

func main() {
	rand.Seed(time.Now().UnixNano())
	http.HandleFunc("/stay", handleStay)
	http.HandleFunc("/stay/", handleStay)
	http.HandleFunc("/bri", handleBri)
	http.HandleFunc("/bri/", handleBri)
	http.HandleFunc("/", handleRedirect)
	appengine.Main()
}

func getClient(ctx context.Context, r *http.Request) (string, *http.Client, error) {
	apiKey, keyPresent := os.LookupEnv("API_KEY")
	if !keyPresent {
		return "", nil, errors.New("api key not configured")
	}

	client := urlfetch.Client(ctx)
	return apiKey, client, nil
}

func handleRedirect(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)

	apiKey, client, err := getClient(ctx, r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	minPosts, _, err := getMinPosts(ctx, client, apiKey)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Debugf(ctx, "how many minposts???")
	log.Debugf(ctx, strconv.Itoa(len(minPosts)))

	// redirect to a random url
	http.Redirect(w, r, minPosts[rand.Intn(len(minPosts))].URL, 302)
}

func handleBri(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	apiKey, client, err := getClient(ctx, r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// build a request for a random post
	var request bytes.Buffer
	request.WriteString("https://www.googleapis.com/blogger/v3/blogs/")
	request.WriteString(blogID)
	request.WriteString("/posts/bypath?path=")
	request.WriteString(briUrls[rand.Intn(len(briUrls))])
	request.WriteString("&fields=id,url,title,content,published&key=")
	request.WriteString(apiKey)

	showPost(w, client, request.String())
}

func handleStay(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	apiKey, client, err := getClient(ctx, r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	minPosts, _, err := getMinPosts(ctx, client, apiKey)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// build a request for a random post
	var request bytes.Buffer
	request.WriteString("https://www.googleapis.com/blogger/v3/blogs/")
	request.WriteString(blogID)
	request.WriteString("/posts/")
	request.WriteString(minPosts[rand.Intn(len(minPosts))].ID)
	request.WriteString("?fields=id,url,title,content,published&key=")
	request.WriteString(apiKey)

	showPost(w, client, request.String())
}

func showPost(w http.ResponseWriter, client *http.Client, request string) {
	resp, err := client.Get(request)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	post := post{}
	err = json.Unmarshal(body, &post)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	t, err := time.Parse(time.RFC3339, post.Published)
	if err == nil {
		post.Published = t.Format("Monday, January 2, 2006")
	}

	params := templateParams{
		Title:     post.Title,
		Content:   template.HTML(post.Content),
		URL:       post.URL,
		Published: post.Published,
	}
	stayTemplate.Execute(w, params)
	w.Header().Set("Content-Type", "text/html")
}

func getMinPosts(ctx context.Context, client *http.Client, apiKey string) ([]minPost, bool, error) {
	var minPosts []minPost
	_, err := memcache.Gob.Get(ctx, memcacheKey, &minPosts)
	if err != nil && err.Error() != "memcache: cache miss" {
		return nil, false, err
	}

	if err == nil && minPosts != nil {
		log.Debugf(ctx, "cache hit")
		// cache hit return early
		return minPosts, true, nil
	}
	log.Debugf(ctx, "cache miss")

	minPosts = []minPost{}
	var pageToken string
	for {
		var request bytes.Buffer
		request.WriteString("https://www.googleapis.com/blogger/v3/blogs/")
		request.WriteString(blogID)
		request.WriteString("/posts?fetchImages=true&fields=nextPageToken,items(id,url)&maxResults=500")

		request.WriteString("&key=")
		request.WriteString(apiKey)

		if len(pageToken) > 0 {
			request.WriteString("&pageToken=")
			request.WriteString(pageToken)
		}

		resp, err := client.Get(request.String())
		if err != nil {
			return nil, false, err
		}
		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			return nil, false, err
		}

		res := response{}
		json.Unmarshal(body, &res)

		// append to list of all urls
		minPosts = append(minPosts, res.Items...)

		// repeat if there are more pages
		if len(res.NextPageToken) > 0 {
			pageToken = res.NextPageToken
			continue
		} else {
			break
		}
	}

	item := &memcache.Item{
		Key:        memcacheKey,
		Object:     minPosts,
		Expiration: 12 * time.Hour,
	}
	err = memcache.Gob.Set(ctx, item)
	if err != nil {
		return nil, false, err
	}

	return minPosts, false, nil
}

type response struct {
	NextPageToken string    `json:"nextPageToken"`
	Items         []minPost `json:"items"`
}

type minPost struct {
	ID  string `json:"id"`
	URL string `json:"url"`
}

type post struct {
	ID        string `json:"id"`
	URL       string `json:"url"`
	Published string `json:"published"`
	Title     string `json:"title"`
	Content   string `json:"content"`
}

type templateParams struct {
	Title     string
	Content   template.HTML
	Published string
	URL       string
	Imgurl    string
}

var briUrls = [...]string{
	"/2007/07/first-sip.html",
	"/2007/08/fur.html",
	"/2007/08/iris.html",
	"/2007/09/building.html",
	"/2007/09/defiance.html",
	"/2007/09/freeze.html",
	"/2007/09/porcelain.html",
	"/2007/09/reflection.html",
	"/2007/09/salt.html",
	"/2007/09/warmth.html",
	"/2007/10/following.html",
	"/2007/10/importance.html",
	"/2007/10/jewels.html",
	"/2007/10/sweet.html",
	"/2007/10/talk.html",
	"/2007/11/finding.html",
	"/2007/11/need.html",
	"/2007/11/pinch.html",
	"/2007/11/sea.html",
	"/2007/11/smiling.html",
	"/2007/11/where.html",
	"/2007/12/meeting.html",
	"/2007/12/sleep.html",
	"/2007/12/watching.html",
	"/2008/01/grasping-of-hands.html",
	"/2008/03/long-ago.html",
	"/2008/04/path-we-walk.html",
	"/2008/04/shades.html",
	"/2008/06/clarification.html",
	"/2008/06/sunshine.html",
	"/2008/08/oranges-lemons.html",
	"/2008/08/price.html",
	"/2008/08/shy.html",
	"/2008/08/station.html",
	"/2008/09/big-blue-sea.html",
	"/2008/09/fact-of-matter.html",
	"/2008/09/place-we-were-in.html",
	"/2008/09/point-of-contact.html",
	"/2008/09/profile.html",
	"/2008/10/directions-we-give.html",
	"/2008/10/never-ending-search-for-something-real.html",
	"/2008/10/shatter-proof.html",
	"/2008/10/walking-away.html",
	"/2008/11/tired-advice.html",
	"/2008/12/water.html",
	"/2009/01/pressure-to-wounded.html",
	"/2009/01/things-ive-never-seen-or-heard.html",
	"/2009/01/world-loves-you-too.html",
	"/2009/02/light-we-fly-to.html",
	"/2009/02/time-we-could-spend.html",
	"/2009/03/heart-beats-per-minute.html",
	"/2009/03/person-in-front-of-me.html",
	"/2009/04/beautiful-mess-we-could-be.html",
	"/2009/04/fading-grey.html",
	"/2009/04/metal-starts-to-twist.html",
	"/2009/04/nature-starts-to-turn.html",
	"/2009/05/way-saturn-turns.html",
	"/2009/06/day-i-got-older.html",
	"/2009/06/moths-dont-die-for-nothing.html",
	"/2009/06/seat-next-to-you.html",
	"/2009/07/needle-and-ink.html",
	"/2009/07/well-of-dreams.html",
	"/2009/09/beakers-id-break.html",
	"/2009/09/corner-of-me-you.html",
	"/2009/09/gun-in-stars.html",
	"/2009/09/new-colour.html",
	"/2009/09/train-of-lies.html",
	"/2009/10/absence-of-oxygen.html",
	"/2009/10/autumn-in-their-eyes.html",
	"/2009/10/deaths-of-millions.html",
	"/2009/10/new-species.html",
	"/2009/10/to-not-do-list.html",
	"/2009/10/wet-hair-and-eyes.html",
	"/2009/11/awol-hearts.html",
	"/2009/11/beauty-of-errors.html",
	"/2009/11/heart-rides-on.html",
	"/2009/11/zodiac-of-one.html",
	"/2009/12/laboratory-in-my-heart.html",
	"/2009/12/ronin-have-names.html",
	"/2010/01/fury-of-water.html",
	"/2010/05/avoidance-of-pain.html",
	"/2010/05/books-never-written.html",
	"/2010/05/fading-glow.html",
	"/2010/05/untouchable-city.html",
	"/2010/06/anthems-for-people-not-places.html",
	"/2010/06/pattern-is-system-is-maze.html",
	"/2010/06/world-is-too-big.html",
	"/2010/07/air-never-saw-it-comming.html",
	"/2010/09/day-tomorrow-came.html",
	"/2010/09/first-crack-is-last.html",
	"/2010/09/molten-core.html",
	"/2010/09/trauma-transmission.html",
	"/2010/09/world-of-one.html",
	"/2010/11/new-singularity.html",
	"/2011/03/superstition-and-fear.html",
	"/2011/08/sound-of-sea.html",
	"/2012/02/relative-phenomena.html",
	"/2012/03/broken-ice-in-your-wake.html",
	"/2012/02/stuff-and-things.html",
	"/2012/04/hidden-depths.html",
	"/2012/04/envy-of-billion-little-unique.html",
	"/2012/05/remaining-of-me.html",
	"/2012/06/endless-night-and-all-it-promises.html",
	"/2012/06/grand-distraction.html",
	"/2012/07/the-purpose-of-love.html",
	"/2012/07/desire-to-live-underwater-forever.html",
	"/2012/08/the-last-land-i-stood-on.html",
	"/2012/10/the-language-stripped-naked.html",
	"/2012/10/the-night-holds-day-so-softly.html",
	"/2012/10/the-sun-leaves-earth.html",
	"/2012/12/the-nature-of-river-is-to-run.html",
	"/2012/12/the-nature-of-river-is-to-run.html",
	"/2014/02/the-hands-you-gave-me.html",
	"/2014/06/the-dreams-on-line.html",
	"/2014/07/the-city-that-sleeps-where-they-fell.html",
	"/2014/08/the-best-i-could-with-what-i-had-in.html",
	"/2014/08/the-world-is-not-as-dark-as-it-seems.html",
	"/2014/09/the-sky-warps-sun.html",
	"/2014/09/the-things-i-make-when-im-alone.html",
	"/2014/11/the-twin-engines.html",
	"/2014/12/the-splinter-of-light.html",
	"/2015/04/the-fire-is-where-were-all-born.html",
	"/2015/06/the-saying-of-when.html",
	"/2015/08/the-box-of-songs.html",
	"/2015/08/the-landscapes-of-you.html",
	"/2015/08/the-uncontrollable.html",
	"/2015/09/the-murder-of-clock.html",
	"/2016/01/the-slow-gentle-continental-drift.html",
	"/2016/02/the-failure-of-prayer.html",
	"/2016/03/the-spider-silk.html",
	"/2016/04/the-terrible-inadequacy-of-entire-life.html",
	"/2016/09/the-remaining-you.html",
	"/2016/10/the-anchors-i-found-in-others.html",
	"/2016/11/the-hard-way.html",
	"/2016/11/the-light-of-all-stars.html",

	// miss_urls
	"/2007/09/distance.html",
	"/2007/09/timing.html",
	"/2007/10/alone.html",
	"/2007/10/clouds.html",
	"/2007/10/flame.html",
	"/2007/10/parcel.html",
	"/2007/11/today.html",
	"/2008/02/weather-and-you.html",
	"/2008/08/space-left.html",
	"/2008/11/long-way-home.html",
	"/2009/09/road-trip.html",
	"/2009/10/train-after-dinner.html",
	"/2010/05/day-time-waited-for-me.html",
	"/2010/05/theory-is-still-just-theory.html",
	"/2011/08/negative-space.html",
	"/2011/12/forest-of-stars.html",
	"/2014/10/the-world-of-your-own.html",
	"/2015/01/the-truth-is-its-just-something-to-hold.html",
	"/2016/05/the-rain-of-black-umbrellas.html",
}
