package main

import (
	"html/template"
	"net/http"
	"regexp"
	"strings"
	"time"

	"google.golang.org/appengine"
)

var trimSpace, _ = regexp.Compile("(?:(?:<div>)?\\s*<br\\s*\\/?>\\s*(?:<\\/div>)?\\s*){3,}")
var stayTemplate = template.Must(template.ParseFiles("template.html"))

func handleStay(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	_, client, err := getClient(ctx, r)
	if err != nil && err != errAPIKeyNotConfigured {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	url, post, _, err := getRandomPost(ctx, client)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	t, err := time.Parse(time.RFC3339, post.Published.Value)
	if err == nil {
		post.Published.Value = t.Format("Monday, January 2, 2006")
	}

	params := templateParams{
		Title:     post.Title.Value,
		Content:   template.HTML(strings.Replace(trimSpace.ReplaceAllLiteralString(post.Content.Value, ""), "http://", "https://", -1)),
		URL:       url,
		Published: post.Published.Value,
	}
	stayTemplate.Execute(w, params)
	w.Header().Set("Content-Type", "text/html")
}
