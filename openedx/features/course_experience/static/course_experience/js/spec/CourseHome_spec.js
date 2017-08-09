/* globals Logger, loadFixtures */

import { CourseHome } from '../CourseHome';

describe('Course Home factory', () => {
  describe('Ensure course tool click logging', () => {
    let home; // eslint-disable-line no-unused-vars

    beforeEach(() => {
      loadFixtures('course_experience/fixtures/course-home-fragment.html');
      home = new CourseHome({
        resumeCourseLink: '.action-resume-course',
        courseToolLink: '.course-tool-link',
      });
      spyOn(Logger, 'log');
    });

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
});
