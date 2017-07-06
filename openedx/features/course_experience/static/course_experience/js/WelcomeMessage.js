/* globals $ */
import 'jquery.cookie';

export class WelcomeMessage {  // eslint-disable-line import/prefer-default-export

  constructor(options) {
    $('.dismiss-message button').click(() => {
      $.ajax({
        type: 'POST',
        url: options.dismissUrl,
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
