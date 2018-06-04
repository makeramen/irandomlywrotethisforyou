package main

import "html/template"

type responseV3 struct {
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

type responseV1 struct {
	Feed feed `json:"feed"`
}

type feed struct {
	Entries      []entry `json:"entry"`
	TotalResults tag     `json:"openSearch$totalResults"`
}

type tag struct {
	Value string `json:"$t"`
}

type entry struct {
	Title     tag    `json"title"`
	Links     []link `json:"link"`
	Content   tag    `json:"content"`
	Published tag    `json"title"`
}

type link struct {
	Rel  string `json:"rel"`
	Href string `json:"href"`
	Type string `json:"type"`
}
