package main

import (
	"html/template"
	"net/http"
	"regexp"
	"strings"

	"google.golang.org/appengine"
)

var trimSpace, _ = regexp.Compile("(?:(?:<div>)?\\s*<br\\s*\\/?>\\s*(?:<\\/div>)?\\s*){3,}")

func handleStay(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)
	_, client, err := getClient(ctx, r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	url, post, _, err := getRandomPost(ctx, client)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
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
