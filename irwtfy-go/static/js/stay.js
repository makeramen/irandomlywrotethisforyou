function getCount() {
    var count = Cookies.get('count')
    if (count) {
        return Promise.resolve(count)
    }
    return $.ajax({
            url :'https://www.blogger.com/feeds/6752139154038265086/posts/default',
            crossDomain: true,
            dataType: 'jsonp',
            data: {
                'alt': 'json',
                'start-index': 1,
                'max-results': 1,
            },
            success: function(result) {
                count = parseInt(result.feed.openSearch$totalResults.$t)
                Cookies.set('count', count, { expires: 365 })
            onCount(count)
            }
        })
    .then(function(result) {
        count = parseInt(result.feed.openSearch$totalResults.$t)
        Cookies.set('count', count, { expires: 365 })
        return Promise.resolve(count)
    })
}

function getRandomEntry() {
    return getCount()
        .then(function(count) {
            return $.ajax({
                url :'https://www.blogger.com/feeds/6752139154038265086/posts/default',
                crossDomain: true,
                dataType: 'jsonp',
                data : {
                    'alt': 'json',
                    'start-index': Math.floor(Math.random() * count) + 1,
                    'max-results': 1,
                },
            })
        })
        .then(function(result) {
            var count = result.feed.openSearch$totalResults.$t
            Cookies.set('count', count)
            var entry = result.feed.entry[0]
            $app.published = new Date(entry.published.$t).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
            $app.title = entry.title.$t
            $app.url = entry.link.find(function(l) { return l.rel == 'alternate' }).href
            $app.content = sanitizeContent(entry.content.$t)
            Vue.nextTick(cleanUpAfterLoad)
        })
}
