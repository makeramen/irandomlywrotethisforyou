package main

import (
	"bytes"
	"math/rand"
	"net/http"

	"google.golang.org/appengine"
)

func handleTest(w http.ResponseWriter, r *http.Request) {
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
	request.WriteString(testUrls[rand.Intn(len(testUrls))])
	request.WriteString("&fields=id,url,title,content,published&key=")
	request.WriteString(apiKey)

	showPost(w, client, request.String())
}

var testUrls = [...]string{
	"/2016/04/the-terrible-inadequacy-of-entire-life.html",
	// "/2015/03/how-to-win-signed-copies-of-all-i-wrote.html",
	// "/2010/03/defender-of-forgotten.html",
	// "/2012/07/footsteps-made-of-fire.html",
	// "/2007/09/rain.html",
	// "/2009/12/corners-of-your-mouth.html",
	// "/2010/11/monsters-i-miss.html",
	// "/2018/01/the-sadness-of-comedy.html",
	// "/2009/12/laboratory-in-my-heart.html",
	// "/2014/02/blog-post.html",
	// "/2010/08/dwindling-conversation.html",
}
