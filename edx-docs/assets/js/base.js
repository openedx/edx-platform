// smooth scrolling links
function smoothScrollLink(e) {
  (e).preventDefault();

  $.smoothScroll({
    offset: -200,
    easing: 'swing',
    speed: 1000,
    scrollElement: null,
    scrollTarget: $(this).attr('href')
  });
}

// open in new window/tab
function linkNewWindow(e) {
    window.open($(e.target).attr('href'));
    e.preventDefault();
}

// doc ready
$(function() {
  var $body = $('body');
  $body.removeClass('no-js');

  // general link management - new window/tab
  // $('a[rel="external"]').attr('title', 'This link will open in a new browser window/tab').bind('click', linkNewWindow);

  // general link management - smooth scrolling page links
  $('a[rel*="view"][href^="#"]').bind('click', smoothScrollLink);
});
