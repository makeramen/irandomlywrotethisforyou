package main

type response struct {
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
	Title     tag    `json:"title"`
	Links     []link `json:"link"`
	Content   tag    `json:"content"`
	Published tag    `json:"published"`
}

type link struct {
	Rel  string `json:"rel"`
	Href string `json:"href"`
	Type string `json:"type"`
}
