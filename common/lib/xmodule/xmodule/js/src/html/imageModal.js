$(function() {
  $(".imageModal-link").toggle(function() {
    $(".imageModal", this).show();
  }, function() {
    $(".imageModal", this).hide();
  });
});