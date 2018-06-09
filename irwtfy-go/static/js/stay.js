function getCount() {
    var count = Cookies.get('count')
    if (!count) {
        $.get('https://www.blogger.com/feeds/6752139154038265086/posts/default',
            {
                'alt': 'json',
                'start-index': 1,
                'max-results': 1,
            },
            function(result) {
                count = parseInt(result.feed.openSearch$totalResults.$t)
                Cookies.set('count', count, { expires: 365 })
            })
    }
    return count
}

function getRandomEntry(done) {
    $.ajax({
        url :'http://www.blogger.com/feeds/6752139154038265086/posts/default',
        crossDomain: true,
        dataType: 'jsonp',
        data : {
            'alt': 'json',
            'start-index': Math.floor(Math.random() * getCount()) + 1,
            'max-results': 1,
        },
        success: function(result) {
            var count = result.feed.openSearch$totalResults.$t
            Cookies.set('count', count)
            var entry = result.feed.entry[0] 
            $app.published = new Date(entry.published.$t).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
            $app.title = entry.title.$t
            $app.url = entry.link.find(function(l) { return l.rel == 'alternate' }).href
            $app.content = entry.content.$t.replace(/(?:(?:<div>)?\s*<br\s*\/?>\s*(?:<\/div>)?\s*){3,}/i, '')
            Vue.nextTick(function() {
                // Set all anchors that wrap images to display: block
                $("#content a:has(img)").css("display","block");

                // Remove any line breaks immediately before the text
                var node = $("#content").contents().toArray()
                    .find(function(n) { return n.nodeType == 3 && $.trim(n.textContent) })
                while (node && node.previousSibling
                    && (node.previousSibling.nodeName == "BR" || node.previousSibling.nodeType == 8)) {
                    node.previousSibling.remove();
                }

                // Find all YouTube and Vimeo videos
                $allVideos = $("iframe[src*='www.youtube.com'], iframe[src*='player.vimeo.com']");

                if ($allVideos.length > 0) {
                    // Figure out and save aspect ratio for each video
                    $allVideos.each(function() {
                        $(this)
                        .data('aspectRatio', this.height / this.width)
                        // and remove the hard coded width/height
                        .removeAttr('height')
                        .removeAttr('width');
                    });

                    // Kick off one resize to fix all videos on page load
                    $(window).resize()
                }
            })
            done()
        }
    })
}

var $app = new Vue({
    el: "#wrapper",
    data : {
        published: '',
        title: '',
        url: '',
        content: '',
    }
})
var $ptr = PullToRefresh.init({
    mainElement: '#wrapper',
    onRefresh: function(done) { 
        getRandomEntry(done)
    }
})
var $allVideos
getRandomEntry(function() {})

// When the window is resized
$(window).resize(function() {
    // Resize all videos according to their own aspect ratio
    $allVideos.each(function() {
    var $el = $(this);
    // Get parent width of this video
    var newWidth = $el.parent().width();
    $el
        .width(newWidth)
        .height(newWidth * $el.data('aspectRatio'));
    });
});