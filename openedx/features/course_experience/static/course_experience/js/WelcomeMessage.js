/* globals $ */
import 'jquery.cookie';

export class WelcomeMessage {  // eslint-disable-line import/prefer-default-export

  constructor(dismissUrl) {
    $('.dismiss-message button').click(() => {
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
    });
  }
}
