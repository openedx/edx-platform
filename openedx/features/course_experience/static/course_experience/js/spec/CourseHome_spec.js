/* globals Logger, loadFixtures */

import { CourseHome } from '../CourseHome';

describe('Course Home factory', () => {
  describe('Ensure course tool click logging', () => {
    let home; // eslint-disable-line no-unused-vars

    beforeEach(() => {
      loadFixtures('course_experience/fixtures/course-home-fragment.html');
      home = new CourseHome({
        courseToolLink: '.course-tool-link',
      });
      spyOn(Logger, 'log');
    });

    it('sends an event when an course tool is clicked', () => {
      document.querySelector('.course-tool-link').dispatchEvent(new Event('click'));
      const courseToolName = document.querySelector('.course-tool-link').text.trim().toLowerCase();
      expect(Logger.log).toHaveBeenCalledWith(
        'edx.course.tool.accessed',
        {
          tool_name: courseToolName,
          page: 'course_home',
        },
      );
    });
  });
});
