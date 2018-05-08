package main

import "html/template"

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
