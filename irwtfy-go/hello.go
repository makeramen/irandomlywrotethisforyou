// Copyright 2018 Google Inc. All rights reserved.
// Use of this source code is governed by the Apache 2.0
// license that can be found in the LICENSE file.

package main

import (
	"bytes"
	"context"
	json "encoding/json"
	"errors"
	"fmt"
	"io/ioutil"
	"math/rand"
	"net/http"
	"os"

	"google.golang.org/appengine"
	"google.golang.org/appengine/log"
	"google.golang.org/appengine/memcache"
	"google.golang.org/appengine/urlfetch"
)

const blogID string = "6752139154038265086"
const memcacheKey = "min_posts"

func main() {
	http.HandleFunc("/", handleRedirect)
	http.HandleFunc("/stay", handleStay)
	http.HandleFunc("/bri", handleBri)
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

	minPosts, err := getMinPosts(ctx, client, apiKey)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// redirect to a random url
	http.Redirect(w, r, minPosts[rand.Intn(len(minPosts))].URL, 302)
}

func handleStay(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	apiKey, client, err := getClient(ctx, r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	minPosts, err := getMinPosts(ctx, client, apiKey)
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
	request.WriteString("?fields=&key=")
	request.WriteString(apiKey)

	showPost(w, client, request.String())

	fmt.Fprintln(w, "Hello, world!")
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
	request.WriteString("?fields=&key=")
	request.WriteString(apiKey)

	showPost(w, client, request.String())

	// todo

}

func getMinPosts(ctx context.Context, client *http.Client, apiKey string) ([]minPost, error) {
	var minPosts []minPost
	_, err := memcache.Gob.Get(ctx, memcacheKey, minPosts)
	if err == nil && minPosts != nil {
		log.Debugf(ctx, "cache hit")
		// cache hit return early
		return minPosts, nil
	}
	log.Debugf(ctx, "cache miss")

	minPosts = []minPost{}
	var pageToken string
	for {
		var request bytes.Buffer
		request.WriteString("https://www.googleapis.com/blogger/v3/blogs/")
		request.WriteString(blogID)
		request.WriteString("/posts?fetchImages=true&fields=nextPageToken,items(url)&maxResults=500")

		request.WriteString("&key=")
		request.WriteString(apiKey)

		if len(pageToken) > 0 {
			request.WriteString("&pageToken=")
			request.WriteString(pageToken)
		}

		resp, err := client.Get(request.String())
		if err != nil {
			return nil, err
		}
		defer resp.Body.Close()
		body, err := ioutil.ReadAll(resp.Body)
		if err != nil {
			return nil, err
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
		log.Debugf(ctx, "memcache set error")
		return nil, err
	}
	log.Debugf(ctx, "memcache set success")

	return minPosts, nil
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
	json.Unmarshal(body, &post)
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
	ID      string `json:"id"`
	URL     string `json:"url"`
	Title   string `json:"title"`
	Content string `json:"content"`
}
