package main

import (
	json "encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"
)

const blogID string = "6752139154038265086"
const memcacheKey = "min_posts"
const keyNumPosts = "num_posts"

func main() {
	rand.Seed(time.Now().UnixNano())
	http.HandleFunc("/", handleRedirect)
	// [START setting_port]
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
		log.Printf("Defaulting to port %s", port)
	}

	log.Printf("Listening on port %s", port)
	log.Fatal(http.ListenAndServe(fmt.Sprintf(":%s", port), nil))
	// [END setting_port]
}

func handleRedirect(w http.ResponseWriter, r *http.Request) {
	count := getCookieCount(r)

	postURL, _, count, err := getRandomPost(count)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	newCookie := http.Cookie{
		Name:   "count",
		Value:  strconv.Itoa(count),
		MaxAge: 365 * 24 * 60 * 60 * 1000,
	}
	http.SetCookie(w, &newCookie)

	// redirect to a random url
	http.Redirect(w, r, postURL, 302)
}

func getCookieCount(r *http.Request) (count int) {
	count = -1
	currentCookie, err := r.Cookie("count")
	if err != nil {
		return
	}
	cookieCount, err := strconv.Atoi(currentCookie.Value)
	if err != nil {
		return
	}
	count = cookieCount
	return
}

func getRandomPost(postCount int) (url string, post entry, count int, err error) {
	if postCount < 0 {
		_, _, postCount, err = getPost(1, 0)
		if err != nil {
			return
		}
	}

	for url == "" {
		url, post, count, err = getPost(rand.Intn(postCount)+1, postCount)
		if err != nil {
			return
		}
	}
	return
}

func getPost(index int, prevCount int) (url string, post entry, count int, err error) {
	count = 0
	post = entry{}
	url = ""
	request := fmt.Sprintf("https://www.blogger.com/feeds/%s/posts/default?alt=json&start-index=%d&max-results=1", blogID, index)
	log.Printf("request: %s", request)
	resp, err := http.Get(request)
	if err != nil {
		return
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return
	}

	res := response{}
	json.Unmarshal(body, &res)
	count, err = strconv.Atoi(res.Feed.TotalResults.Value)
	if err != nil {
		return
	}
	post = res.Feed.Entries[0]
	for _, link := range res.Feed.Entries[0].Links {
		if link.Rel == "alternate" && link.Type == "text/html" {
			url = link.Href
			break
		}
	}

	return
}
