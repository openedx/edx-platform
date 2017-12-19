/* globals $ */
import 'jquery.cookie';

export class WelcomeMessage {  // eslint-disable-line import/prefer-default-export

  static dismissWelcomeMessage(dismissUrl) {
    $.ajax({
      type: 'POST',
      url: dismissUrl,
      headers: {
        'X-CSRFToken': $.cookie('csrftoken'),
      },
      success: () => {
        $('.welcome-message').hide();
      },
    });
  }

  constructor(options) {
    // Dismiss the welcome message if the user clicks dismiss, or auto-dismiss if
    // the user doesn't click dismiss in 7 days from when it was first viewed.

    // Check to see if the welcome message has been displayed at all.
    if ($('.welcome-message').length > 0) {
      // If the welcome message has been viewed.
      if ($.cookie('welcome-message-viewed') === 'True') {
        // If the timer cookie no longer exists, dismiss the welcome message permanently.
        if ($.cookie('welcome-message-timer') !== 'True') {
          WelcomeMessage.dismissWelcomeMessage(options.dismissUrl);
        }
      } else {
        // Set both the viewed cookie and the timer cookie.
        $.cookie('welcome-message-viewed', 'True', { expires: 365 });
        $.cookie('welcome-message-timer', 'True', { expires: 7 });
      }
    }
    $('.dismiss-message button').click(() => WelcomeMessage.dismissWelcomeMessage(options.dismissUrl));
  }
}
