function sanitizeContent(content) {
    if (typeof content === 'undefined') { return }
    return content
        .replace(/(?:(?:<div>)?\s*<br\s*\/?>\s*(?:<\/div>)?\s*){3,}/gi, '')
        .replace(/http:\/\//gi, 'https://')
}

function cleanUpAfterLoad() {
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
}

// When the window is resized
$(window).resize(function() {
    if (typeof $allVideos === 'undefined') { return }
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
    passive: true,
    onRefresh: async function(done) { 
        await showRandomEntry()
        done()
    }
})

$(function () { showRandomEntry() } )