package main

import (
	"context"
	json "encoding/json"
	"errors"
	"fmt"
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
const memcacheKey = "min_posts"
const keyNumPosts = "num_posts"

var (
	stayTemplate           = template.Must(template.ParseFiles("stay.html"))
	errAPIKeyNotConfigured = errors.New("api key not configured")
)

func main() {
	rand.Seed(time.Now().UnixNano())
	http.HandleFunc("/stay", handleStay)
	http.HandleFunc("/stay/", handleStay)
	http.HandleFunc("/bri", handleBri)
	http.HandleFunc("/bri/", handleBri)
	http.HandleFunc("/test", handleTest)
	http.HandleFunc("/", handleRedirect)
	appengine.Main()
}

func getClient(ctx context.Context, r *http.Request) (apiKey string, client *http.Client, err error) {
	apiKey, keyPresent := os.LookupEnv("API_KEY")
	if !keyPresent || len(apiKey) == 0 {
		err = errAPIKeyNotConfigured
	}

	client = urlfetch.Client(ctx)
	return
}

func handleRedirect(w http.ResponseWriter, r *http.Request) {
	ctx := appengine.NewContext(r)

	_, client, err := getClient(ctx, r)
	if err != nil && err != errAPIKeyNotConfigured {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	postURL, _, _, err := getRandomPost(ctx, client)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// redirect to a random url
	http.Redirect(w, r, postURL, 302)
}

func getRandomPost(ctx context.Context, client *http.Client) (url string, post entry, count int, err error) {
	postCount, err := getPostCount(ctx, client)
	if err != nil {
		return
	}

	for url == "" {
		url, post, count, err = getPost(ctx, client, rand.Intn(postCount)+1, postCount)
		if err != nil {
			return
		}
	}
	return
}

func getPost(ctx context.Context, client *http.Client, index int, prevCount int) (url string, post entry, count int, err error) {
	count = 0
	post = entry{}
	url = ""
	request := fmt.Sprintf("https://www.blogger.com/feeds/%s/posts/default?alt=json&start-index=%d&max-results=1", blogID, index)
	log.Debugf(ctx, "request: %s", request)
	resp, err := client.Get(request)
	if err != nil {
		return
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return
	}

	res := responseV1{}
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

	if count != prevCount {
		item := &memcache.Item{
			Key:        keyNumPosts,
			Value:      []byte(strconv.Itoa(count)),
			Expiration: 12 * time.Hour,
		}
		err = memcache.Set(ctx, item)
	}

	return
}

func getPostCount(ctx context.Context, client *http.Client) (count int, err error) {
	item, err := memcache.Get(ctx, keyNumPosts)
	if err == memcache.ErrCacheMiss {
		_, _, count, err = getPost(ctx, client, 1, 0)
		return
	} else if err != nil {
		return
	}
	count, err = strconv.Atoi(string(item.Value[:]))
	return
}
