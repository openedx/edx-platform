// eslint-disable-next-line camelcase
function sendLog(name, data, event_type) {
    var message = data || {};
    message.chapter = PDF_URL || '';
    message.name = 'textbook.pdf.' + name;
    // eslint-disable-next-line camelcase
    Logger.log(event_type || message.name, message);
}

// this event is loaded after the others to accurately represent the order of events:
// click next -> pagechange
$(function() {
    // eslint-disable-next-line camelcase
    var first_page = true;
    var scroll = {timeStamp: 0, direction: null};

    $(window).bind('pagechange', function(event) {
    // log every page render
        var page = PDFViewerApplication.page;
        // eslint-disable-next-line camelcase
        var old_page = event.originalEvent.previousPageNumber;
        // pagechange is called many times per viewing.
        // eslint-disable-next-line camelcase
        if (old_page !== page || first_page) {
            // eslint-disable-next-line camelcase
            first_page = false;
            if ((event.timeStamp - scroll.timeStamp) < 50) {
                sendLog('page.scrolled', {page: page, direction: scroll.direction});
            }
            // eslint-disable-next-line camelcase
            sendLog('page.loaded', {type: 'gotopage', old: old_page, new: page}, 'book');
            scroll.timeStamp = 0;
        }
    });

    $('#viewerContainer').bind('DOMMouseScroll mousewheel', function(event) {
        scroll.timeStamp = event.timeStamp;
        scroll.direction = PDFViewerApplication.pdfViewer.scroll.down ? 'down' : 'up';
    });
});

$('#viewThumbnail,#sidebarToggle').on('click', function() {
    sendLog('thumbnails.toggled', {page: PDFViewerApplication.page});
});

$('#thumbnailView a').live('click', function() {
    sendLog('thumbnail.navigated', {page: $('#thumbnailView a').index(this) + 1, thumbnail_title: $(this).attr('title')});
});

$('#viewOutline').on('click', function() {
    sendLog('outline.toggled', {page: PDFViewerApplication.page});
});

$('#previous').on('click', function() {
    sendLog('page.navigatednext', {type: 'prevpage', new: PDFViewerApplication.page - 1}, 'book');
});

$('#next').on('click', function() {
    sendLog('page.navigatednext', {type: 'nextpage', new: PDFViewerApplication.page + 1}, 'book');
});

$('#zoomIn,#zoomOut').on('click', function() {
    sendLog('zoom.buttons.changed', {direction: $(this).attr('id') == 'zoomIn' ? 'in' : 'out', page: PDFViewerApplication.page});
});

$('#pageNumber').on('change', function() {
    sendLog('page.navigated', {page: $(this).val()});
});

// eslint-disable-next-line camelcase
var old_amount = 1;
$(window).bind('scalechange', function(event) {
    var amount = event.originalEvent.scale;
    // eslint-disable-next-line camelcase
    if (amount !== old_amount) {
        sendLog('display.scaled', {amount: amount, page: PDFViewerApplication.page});
        // eslint-disable-next-line camelcase
        old_amount = amount;
    }
});

$('#scaleSelect').on('change', function() {
    sendLog('zoom.menu.changed', {amount: $('#scaleSelect').val(), page: PDFViewerApplication.page});
});

// eslint-disable-next-line camelcase
var search_event = null;
$(window).bind('find findhighlightallchange findagain findcasesensitivitychange', function(event) {
    // eslint-disable-next-line camelcase
    if (search_event && event.type == 'find') {
        clearTimeout(search_event);
    }
    // eslint-disable-next-line camelcase
    search_event = setTimeout(function() {
        var message = event.originalEvent.detail;
        message.status = $('#findMsg').text();
        message.page = PDFViewerApplication.page;
        // eslint-disable-next-line camelcase
        var event_name = 'search';
        // eslint-disable-next-line default-case
        switch (event.type) {
        case 'find':
            // eslint-disable-next-line camelcase
            event_name += '.executed';
            break;
        case 'findhighlightallchange':
            // eslint-disable-next-line camelcase
            event_name += '.highlight.toggled';
            break;
        case 'findagain':
            // eslint-disable-next-line camelcase
            event_name += '.navigatednext';
            break;
        case 'findcasesensitivitychange':
            // eslint-disable-next-line camelcase
            event_name += 'casesensitivity.toggled';
            break;
        }
        sendLog(event_name, message);
    }, 500);
});
