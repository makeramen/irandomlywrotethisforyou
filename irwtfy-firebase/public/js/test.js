const pathIdMap = {
    '/2012/01/start-of-world-wide-war.html': '4311347037095158672',
    '/2011/01/skin-im-in.html': '2254171920948949691',
}

function getId(apiKey, path) {
    return $.ajax({
        url: 'https://www.googleapis.com/blogger/v3/blogs/6752139154038265086/posts/bypath',
            crossDomain: true,
            dataType: 'jsonp',
            data : {
                'path': path,
                'fields': 'id,url,title,content,published',
                'key': apiKey,
            },
        })
        .then(function(entry) {
            console.log(entry.id)
        })
}

function getRandomEntryId() {
    const ids = Object.values(pathIdMap)
    return Promise.resolve(ids[Math.floor(Math.random() * ids.length)])
}

function showRandomEntry() {
    return getRandomEntryId()
        .then(function(entryId) {
            return $.ajax({
                url: 'https://www.blogger.com/feeds/6752139154038265086/posts/default/' + entryId,
                crossDomain: true,
                dataType: 'jsonp',
                data : {
                    'alt': 'json'
                },
            })
        })
        .then(function(result) {
            const entry = result.entry
            $app.published = new Date(entry.published.$t).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
            $app.title = entry.title.$t
            $app.url = entry.link.find(function(l) { return l.rel == 'alternate' }).href
            $app.content = sanitizeContent(entry.content.$t)
            Vue.nextTick(cleanUpAfterLoad)
        })
}
