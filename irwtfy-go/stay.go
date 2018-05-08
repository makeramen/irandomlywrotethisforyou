package main

import (
	"bytes"
	json "encoding/json"
	"html/template"
	"io/ioutil"
	"math/rand"
	"net/http"
	"time"

	"google.golang.org/appengine"
)

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
