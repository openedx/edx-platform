/* globals $ */
import 'jquery.cookie';
import gettext from 'gettext'; // eslint-disable-line
import { clampHtmlByWords } from 'common/js/utils/clamp-html'; // eslint-disable-line

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


    // "Show More" support for welcome messages
    const messageContent = document.querySelector('#welcome-message-content');
    const fullText = messageContent.innerHTML;
    if (clampHtmlByWords(messageContent, 100) < 0) {
      const showMoreButton = document.querySelector('#welcome-message-show-more');
      const shortText = messageContent.innerHTML;

      showMoreButton.removeAttribute('hidden');

      showMoreButton.addEventListener('click', (event) => {
        if (showMoreButton.getAttribute('data-state') === 'less') {
          showMoreButton.textContent = gettext('Show More');
          messageContent.innerHTML = shortText;
          showMoreButton.setAttribute('data-state', 'more');
        } else {
          showMoreButton.textContent = gettext('Show Less');
          messageContent.innerHTML = fullText;
          showMoreButton.setAttribute('data-state', 'less');
        }
        event.stopImmediatePropagation();
      });
    }
  }
}
