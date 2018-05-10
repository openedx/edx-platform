/* globals $, loadFixtures */

import {
  expectRequest,
  requests as mockRequests,
  respondWithJson,
} from 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers';
import { WelcomeMessage } from '../WelcomeMessage';

describe('Welcome Message factory', () => {
  describe('Ensure button click', () => {
    const endpointUrl = '/course/course_id/dismiss_message/';

    beforeEach(() => {
      loadFixtures('course_experience/fixtures/welcome-message-fragment.html');
      new WelcomeMessage(endpointUrl);  // eslint-disable-line no-new
    });

    it('When button click is made, ajax call is made and message is hidden.', () => {
      const $message = $('.welcome-message');
      const requests = mockRequests(this);
      document.querySelector('.dismiss-message button').dispatchEvent(new Event('click'));
      expectRequest(
        requests,
        'POST',
        endpointUrl,
      );
      respondWithJson(requests);
      expect($message.attr('style')).toBe('display: none;');
      requests.restore();
    });
  });
});
