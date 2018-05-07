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

	"google.golang.org/appengine"
	"google.golang.org/appengine/log"
	"google.golang.org/appengine/memcache"
	"google.golang.org/appengine/urlfetch"
)

const blogID string = "6752139154038265086"
const memcacheKey = "minposts"

var (
	stayTemplate = template.Must(template.ParseFiles("stay.html"))
)

func main() {
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
	request.WriteString("/posts/")
	// request.WriteString(ids[rand.Intn(len(ids))])
	request.WriteString("?fields=id,url,title,content&key=")
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

	// fmt.Fprintln(w, request.String())

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

	params := templateParams{Title: post.Title, Content: post.Content, URL: post.URL, Published: post.Published}
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
		Key:    memcacheKey,
		Object: minPosts,
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
	Content   string
	Published string
	URL       string
	Imgurl    string
}
