/* globals Logger, loadFixtures */

import { CourseHome } from '../CourseHome';

describe('Course Home factory', () => {
  let home;
  const runKey = 'course-v1:edX+DemoX+Demo_Course';
  window.analytics = jasmine.createSpyObj('analytics', ['page', 'track', 'trackLink']);

  beforeEach(() => {
    loadFixtures('course_experience/fixtures/course-home-fragment.html');
    spyOn(Logger, 'log');
    home = new CourseHome({ // eslint-disable-line no-unused-vars
      courseRunKey: runKey,
      resumeCourseLink: '.action-resume-course',
      courseToolLink: '.course-tool-link',
    });
  });

  describe('Ensure course tool click logging', () => {
    it('sends an event when resume or start course is clicked', () => {
      $('.action-resume-course').click();
      expect(Logger.log).toHaveBeenCalledWith(
        'edx.course.home.resume_course.clicked',
        {
          event_type: 'start',
          url: `http://${window.location.host}/courses/course-v1:edX+DemoX+Demo_Course/courseware` +
          '/19a30717eff543078a5d94ae9d6c18a5/',
        },
      );
    });

    it('sends an event when an course tool is clicked', () => {
      const courseToolNames = document.querySelectorAll('.course-tool-link');
      for (let i = 0; i < courseToolNames.length; i += 1) {
        const courseToolName = courseToolNames[i].dataset['analytics-id']; // eslint-disable-line dot-notation
        const event = new CustomEvent('click');
        event.srcElement = { dataset: { 'analytics-id': courseToolName } };
        courseToolNames[i].dispatchEvent(event);
        expect(Logger.log).toHaveBeenCalledWith(
          'edx.course.tool.accessed',
          {
            tool_name: courseToolName,
          },
        );
      }
    });
  });

  describe('Upgrade message events', () => {
    const segmentEventProperties = {
      promotion_id: 'courseware_verified_certificate_upsell',
      creative: 'hero_matthew_smith',
      name: 'In-Course Verification Prompt',
      position: 'hero',
    };

    it('should send events to Segment and edX on initial load', () => {
      expect(window.analytics.track).toHaveBeenCalledWith('Promotion Viewed', segmentEventProperties);
      expect(Logger.log).toHaveBeenCalledWith('edx.course.upgrade.hero.displayed', { courseRunKey: runKey });
    });

    it('should send events to Segment and edX after clicking the upgrade button ', () => {
      $('.vc-message .btn-upgrade').click();
      expect(window.analytics.track).toHaveBeenCalledWith('Promotion Viewed', segmentEventProperties);
      expect(Logger.log).toHaveBeenCalledWith('edx.course.upgrade.hero.clicked', { courseRunKey: runKey });
    });
  });

  describe('upgrade message display toggle', () => {
    let $message;
    let $toggle;

    beforeEach(() => {
      $.fx.off = true;

      $message = $('.vc-message');
      $toggle = $('.vc-toggle', $message);
      expect($message.length).toEqual(1);
      expect($toggle.length).toEqual(1);
    });

    it('hides/shows the message and writes/removes a key from local storage', () => {
      // NOTE (CCB): Ideally this should be two tests--one for collapse, another for expansion.
      // After a couple hours I have been unable to make these two tests pass, probably due to
      // issues with the initial state of local storage.
      expect($message.is(':visible')).toBeTruthy();
      expect($message.hasClass('polite')).toBeFalsy();
      expect($toggle.text().trim()).toEqual('Show less');

      $toggle.click();
      expect($message.hasClass('polite')).toBeTruthy();
      expect($toggle.text().trim()).toEqual('Show more');
      expect(window.localStorage.getItem(home.msgStateStorageKey)).toEqual('true');

      $toggle.click();
      expect($message.hasClass('polite')).toBeFalsy();
      expect($toggle.text().trim()).toEqual('Show less');
      expect(window.localStorage.getItem(home.msgStateStorageKey)).toBeNull();
    });
  });
});
