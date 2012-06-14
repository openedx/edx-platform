$(document).ready(function () {
  $('a.options').toggle(function() {
    $('ol.user-options').addClass("expanded");
    $('a.options').addClass("active");
  }, function() {
    $('ol.user-options').removeClass("expanded");
    $('a.options').removeClass("active");
  });
});
