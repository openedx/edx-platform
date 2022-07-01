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
      new WelcomeMessage({ dismissUrl: endpointUrl });  // eslint-disable-line no-new
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

  describe('Ensure cookies behave as expected', () => {
    const endpointUrl = '/course/course_id/dismiss_message/';

    function deleteAllCookies() {
      const cookies = document.cookie.split(';');
      cookies.forEach((cookie) => {
        const eqPos = cookie.indexOf('=');
        const name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT`;
      });
    }

    beforeEach(() => {
      deleteAllCookies();
    });

    function createWelcomeMessage() {
      loadFixtures('course_experience/fixtures/welcome-message-fragment.html');
      new WelcomeMessage({ dismissUrl: endpointUrl });  // eslint-disable-line no-new
    }

    it('Cookies are created if none exist.', () => {
      createWelcomeMessage();
      expect($.cookie('welcome-message-viewed')).toBe('True');
      expect($.cookie('welcome-message-timer')).toBe('True');
    });

    it('Nothing is hidden or dismissed if the timer is still active', () => {
      const $message = $('.welcome-message');
      $.cookie('welcome-message-viewed', 'True');
      $.cookie('welcome-message-timer', 'True');
      createWelcomeMessage();
      expect($message.attr('style')).toBe(undefined);
    });

    it('Message is dismissed if the timer has expired and the message has been viewed.', () => {
      const requests = mockRequests(this);
      $.cookie('welcome-message-viewed', 'True');
      createWelcomeMessage();

      const $message = $('.welcome-message');
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

  describe('Shortened welcome message', () => {
    const endpointUrl = '/course/course_id/dismiss_message/';

    beforeEach(() => {
      loadFixtures('course_experience/fixtures/welcome-message-fragment.html');
      new WelcomeMessage({  // eslint-disable-line no-new
        dismissUrl: endpointUrl,
      });
    });

    it('Shortened message can be toggled', () => {
      expect($('#welcome-message-content').text()).toContain('…');
      expect($('#welcome-message-show-more').text()).toContain('Show More');
      $('#welcome-message-show-more').click();
      expect($('#welcome-message-content').text()).not.toContain('…');
      expect($('#welcome-message-show-more').text()).toContain('Show Less');
      $('#welcome-message-show-more').click();
      expect($('#welcome-message-content').text()).toContain('…');
      expect($('#welcome-message-show-more').text()).toContain('Show More');
    });
  });
});
