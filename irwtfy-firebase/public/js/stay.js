function getCount() {
    const count = Cookies.get('count')
    if (count) {
        return Promise.resolve(parseInt(count))
    }
    return $.ajax({
            url: 'https://www.blogger.com/feeds/6752139154038265086/posts/default',
            crossDomain: true,
            dataType: 'jsonp',
            data: {
                'alt': 'json',
                'start-index': 1,
                'max-results': 1,
            },
        })
    .then(function(result) {
        const count = result.feed.openSearch$totalResults.$t
        setCountCookie(count)
        return Promise.resolve(parseInt(count))
    })
}

function setCountCookie(count) {
    Cookies.set('count', count, { expires: 365 })
}

function showRandomEntry() {
    return getCount()
        .then(function(count) {
            return $.ajax({
                url: 'https://www.blogger.com/feeds/6752139154038265086/posts/default',
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
            const count = result.feed.openSearch$totalResults.$t
            setCountCookie(count)
            const entry = result.feed.entry[0]
            $app.published = new Date(entry.published.$t).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
            $app.title = entry.title.$t
            $app.url = entry.link.find(function(l) { return l.rel == 'alternate' }).href
            $app.content = sanitizeContent(entry.content.$t)
            Vue.nextTick(cleanUpAfterLoad)
        })
}
