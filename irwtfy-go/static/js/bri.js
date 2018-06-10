function getRandomPath() {
    return Promise.resolve('/2011/11/chest-cavity.html')
}

function getRandomEntry() {
    return getRandomPath()
        .then(function(path) {
            return $.ajax({
                url :'https://www.googleapis.com/blogger/v3/blogs/6752139154038265086/posts/bypath',
                crossDomain: true,
                dataType: 'jsonp',
                data : {
                    'path': path,
                    'fields': 'id,url,title,content,published',
                    'key': api_key,
                },
            })
        })
        .then(function(entry) {
            $app.published = new Date(entry.published).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
            $app.title = entry.title
            $app.url = entry.url
            $app.content = sanitizeContent(entry.content)
            Vue.nextTick(cleanUpAfterLoad)
        })
}
