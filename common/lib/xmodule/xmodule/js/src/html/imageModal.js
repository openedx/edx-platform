$(function() {
  $(".imageModal-link").click(function() {
    event.preventDefault();
    $(this).closest(".imageModal-trigger").siblings(".imageModal").show();
  });
  
  $(".imageModal").click(function() {
    $(this).hide();
  });
});