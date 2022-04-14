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
      creative: 'sidebarupsell',
      name: 'In-Course Verification Prompt',
      position: 'sidebar-message',
    };

    it('should send events to Segment and edX on initial load', () => {
      expect(window.analytics.track).toHaveBeenCalledWith('Promotion Viewed', segmentEventProperties);
      expect(Logger.log).toHaveBeenCalledWith('edx.bi.course.upgrade.sidebarupsell.displayed', { courseRunKey: runKey });
    });

    it('should send events to Segment and edX after clicking the upgrade button ', () => {
      $('.section-upgrade .btn-upgrade').click();
      expect(window.analytics.track).toHaveBeenCalledWith('Promotion Viewed', segmentEventProperties);
      expect(Logger.log).toHaveBeenCalledWith('edx.bi.course.upgrade.sidebarupsell.clicked', { courseRunKey: runKey });
      expect(Logger.log).toHaveBeenCalledWith('edx.course.enrollment.upgrade.clicked', { location: 'sidebar-message' });
    });
  });
});
