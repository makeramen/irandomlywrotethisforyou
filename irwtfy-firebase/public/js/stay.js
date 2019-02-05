async function getCount() {
    let count = Cookies.get('count')
    if (count) {
        return parseInt(count)
    }
    const result = await fetchJsonp('https://www.blogger.com/feeds/6752139154038265086/posts/default?alt=json&start-index=1&max-results=1')
    const resultJson = await result.json()
    count = resultJson.feed.openSearch$totalResults.$t
    setCountCookie(count)
    return parseInt(count)
}

function setCountCookie(count) {
    Cookies.set('count', count, { expires: 365 })
}

async function showRandomEntry() {
    let count = await getCount()
    const result = await fetchJsonp('https://www.blogger.com/feeds/6752139154038265086/posts/default?alt=json&max-results=1&' + Math.floor(Math.random() * count) + 1);
    const resultJson = await result.json()
    newCount = resultJson.feed.openSearch$totalResults.$t
    setCountCookie(newCount)
    const entry = resultJson.feed.entry[0]
    $app.published = new Date(entry.published.$t).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
    $app.title = entry.title.$t
    $app.url = entry.link.find(function (l) { return l.rel == 'alternate' }).href
    $app.content = sanitizeContent(entry.content.$t)
    Vue.nextTick(cleanUpAfterLoad)
}
