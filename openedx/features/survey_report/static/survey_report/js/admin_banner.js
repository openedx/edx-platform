$(document).ready(function(){
    // Function to get user ID
  function getUserId() {
    return $('#userIdSurvey').val();
  }

  // Function to get current time in milliseconds
  function getCurrentTime() {
    return new Date().getTime();
  }

  // Function to set dismissal time and expiration time in local storage
  function setDismissalAndExpirationTime(userId, dismissalTime) {
    let expirationTime = dismissalTime + (30 * 24 * 60 * 60 * 1000); // 30 days
    localStorage.setItem('bannerDismissalTime_' + userId, dismissalTime);
    localStorage.setItem('bannerExpirationTime_' + userId, expirationTime);
  }

  // Function to check if banner should be shown or hidden
  function checkBannerVisibility() {
    let userId = getUserId();
    let bannerDismissalTime = localStorage.getItem('bannerDismissalTime_' + userId);
    let bannerExpirationTime = localStorage.getItem('bannerExpirationTime_' + userId);
    let currentTime = getCurrentTime();

    if (bannerDismissalTime && bannerExpirationTime && currentTime > bannerExpirationTime) {
      // Banner was dismissed and it's not within the expiration period, so show it
      $('#originalContent').show();
    } else if (bannerDismissalTime && bannerExpirationTime && currentTime < bannerExpirationTime) {
      // Banner was dismissed and it's within the expiration period, so hide it
      $('#originalContent').hide();
    } else {
      // Banner has not been dismissed ever so we need to show it.
      $('#originalContent').show();
    }
  }

  // Click event for dismiss button
  $('#dismissButton').click(function() {
    $('#originalContent').slideUp('slow', function() {
      let userId = getUserId();
      let dismissalTime = getCurrentTime();
      setDismissalAndExpirationTime(userId, dismissalTime);
    });
  });

  // Check banner visibility on page load
  checkBannerVisibility();
  // When the form is submitted
  $("#survey_report_form").submit(function(event){
    event.preventDefault();  // Prevent the form from submitting traditionally

    // Make the AJAX request
    $.ajax({
      url: $(this).attr("action"),
      type: $(this).attr("method"),
      data: $(this).serialize(),
      success: function(response){
        // Hide the original content block
        $("#originalContent").slideUp(400, function() {
          //$(this).css('display', 'none');
          // Show the thank-you message block with slide down effect
          $("#thankYouMessage").slideDown(400, function() {
            // Wait for 3 seconds (3000 milliseconds) and then slide up the thank-you message
            setTimeout(function() {
              $("#thankYouMessage").slideUp(400);
              }, 3000);
          });
        });
        },
      error: function(error){
        // Handle any errors
        console.error("Error sending report:", error);
      }
    });
  });
});
