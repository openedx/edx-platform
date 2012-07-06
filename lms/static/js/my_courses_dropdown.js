$(document).ready(function () {
  $('a.dropdown').toggle(function() {
    $('ul.dropdown-menu').addClass("expanded");
    $('a.dropdown').addClass("active");
  }, function() {
    $('ul.dropdown-menu').removeClass("expanded");
    $('a.dropdown').removeClass("active");
  });
});
