/* globals Logger */

export class CourseHome {  // eslint-disable-line import/prefer-default-export
  constructor(options) {
    // Logging for course tool click events
    const $courseToolLink = $(options.courseToolLink);
    $courseToolLink.on('click', () => {
      const courseToolName = document.querySelector('.course-tool-link').text.trim().toLowerCase();
      Logger.log(
        'edx.course.tool.accessed',
        {
          tool_name: courseToolName,
          page: 'course_home',
        },
      );
    });
  }
}
