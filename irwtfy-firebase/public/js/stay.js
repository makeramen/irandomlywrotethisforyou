async function getCount() {
    let count = Cookies.get('count')
    if (count) {
        return parseInt(count)
    }
    const result = await $.ajax({
        url: 'https://www.blogger.com/feeds/6752139154038265086/posts/default',
        crossDomain: true,
        dataType: 'jsonp',
        data: {
            'alt': 'json',
            'start-index': 1,
            'max-results': 1,
        },
    })
    count = result.feed.openSearch$totalResults.$t
    setCountCookie(count)
    return parseInt(count)
}

function setCountCookie(count) {
    Cookies.set('count', count, { expires: 365 })
}

async function showRandomEntry() {
    let count = await getCount()
    const result = await $.ajax({
        url: 'https://www.blogger.com/feeds/6752139154038265086/posts/default',
        crossDomain: true,
        dataType: 'jsonp',
        data: {
            'alt': 'json',
            'start-index': Math.floor(Math.random() * count) + 1,
            'max-results': 1,
        },
    })
    newCount = result.feed.openSearch$totalResults.$t
    setCountCookie(newCount)
    const entry = result.feed.entry[0]
    $app.published = new Date(entry.published.$t).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    $app.title = entry.title.$t
    $app.url = entry.link.find(function (l) { return l.rel == 'alternate' }).href
    $app.content = sanitizeContent(entry.content.$t)
    Vue.nextTick(cleanUpAfterLoad)
}
