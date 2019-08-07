/* globals $ */
import 'jquery.cookie';

export class LatestUpdate {  // eslint-disable-line import/prefer-default-export

  constructor(options) {
    if ($.cookie('update-message') === 'hide') {
      $(options.messageContainer).hide();
    }
    $(options.dismissButton).click(() => {
      $.cookie('update-message', 'hide', { expires: 1 });
      $(options.messageContainer).hide();
    });
  }
}
