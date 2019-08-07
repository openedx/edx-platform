/* globals $, loadFixtures */

import 'jquery.cookie';
import { LatestUpdate } from '../LatestUpdate';


describe('LatestUpdate tests', () => {
  function createLatestUpdate() {
    new LatestUpdate({ messageContainer: '.update-message', dismissButton: '.dismiss-message button' }); // eslint-disable-line no-new
  }
  describe('Test dismiss', () => {
    beforeEach(() => {
      // This causes the cookie to be deleted.
      $.cookie('update-message', '', { expires: -1 });
      loadFixtures('course_experience/fixtures/latest-update-fragment.html');
    });

    it('Test dismiss button', () => {
      expect($.cookie('update-message')).toBe(null);
      createLatestUpdate();
      expect($('.update-message').attr('style')).toBe(undefined);
      $('.dismiss-message button').click();
      expect($('.update-message').attr('style')).toBe('display: none;');
      expect($.cookie('update-message')).toBe('hide');
    });

    it('Test cookie hides update', () => {
      $.cookie('update-message', 'hide');
      createLatestUpdate();
      expect($('.update-message').attr('style')).toBe('display: none;');

      $.cookie('update-message', '', { expires: -1 });
      loadFixtures('course_experience/fixtures/latest-update-fragment.html');
      createLatestUpdate();
      expect($('.update-message').attr('style')).toBe(undefined);
    });
  });
});
