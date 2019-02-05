function sanitizeContent(content) {
    if (typeof content === 'undefined') { return }
    return content
        .replace(/(?:(?:<div>)?\s*<br\s*\/?>\s*(?:<\/div>)?\s*){3,}/gi, '')
        .replace(/http:\/\//gi, 'https://')
}

function cleanUpAfterLoad() {
    // Set all anchors that wrap images to display: block
    document.querySelectorAll("#content a:has(img)").style.display = 'block';

    // Remove any line breaks immediately before the text
    var node = document.querySelectorAll("#content").childNodes
        .find(function(n) { return n.nodeType == 3 && n.textContent.trim() })
    while (node && node.previousSibling
        && (node.previousSibling.nodeName == "BR" || node.previousSibling.nodeType == 8)) {
        node.previousSibling.remove();
    }

    // Find all YouTube and Vimeo videos
    $allVideos = document.querySelectorAll("iframe[src*='www.youtube.com'], iframe[src*='player.vimeo.com']");

    if ($allVideos.length > 0) {
        // Figure out and save aspect ratio for each video
        $allVideos.each(function() {
            this.dataset.aspectRatio = this.height / this.width;
            // and remove the hard coded width/height
            this.removeAttribute('height');
            this.removeAttribute('width');
        });

        // Kick off one resize to fix all videos on page load
        window.dispatchEvent(new Event('resize'));
    }
}

// When the window is resized
window.onresize = function() {
    if (typeof $allVideos === 'undefined') { return }
    // Resize all videos according to their own aspect ratio
    $allVideos.forEach(element => {
        let newWidth = element.parentElement.width;
        element.width = newWidth;
        element.height = newWidth * element.dataset.aspectRatio;
    });
};

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

showRandomEntry()
// (function () { showRandomEntry() } )