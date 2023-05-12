// eslint-disable-next-line no-unused-vars
function playVideo(src) {
    'use strict';

    document.querySelector('#program_video button').style = 'display:none;';
    document.querySelector('#program_video iframe').style = 'display:block;';
    document.querySelector('#program_video iframe').src = src;
}
$('.instructor-image, .instructor-label').leanModal({closeButton: '.modal_close', top: '10%'});
// Create MutationObserver which prevents the body of
// the page from scrolling when a modal window is displayed
/* eslint-disable-next-line no-unused-vars, no-var */
var observer = new MutationObserver(function(mutations, obv) {
    mutations.forEach(function(mutation) {
        if ($(mutation.target).css('display') === 'block') {
            $('body').css('overflow', 'hidden');
        } else {
            $('body').css('overflow', 'auto');
        }
    });
});
$('.modal').each(function(index, element) {
    observer.observe(element, {attributes: true, attributeFilter: ['style']});
});
