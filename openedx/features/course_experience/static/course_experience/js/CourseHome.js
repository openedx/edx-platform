/* globals Logger */

export class CourseHome {  // eslint-disable-line import/prefer-default-export
  constructor(options) {
    // Logging for 'Resume Course' or 'Start Course' button click
    const $resumeCourseLink = $(options.resumeCourseLink);
    $resumeCourseLink.on('click', (event) => {
      const eventType = $resumeCourseLink.find('span').data('action-type');
      Logger.log(
        'edx.course.home.resume_course.clicked',
        {
          event_type: eventType,
          url: event.currentTarget.href,
        },
      );
    });

    // Logging for course tool click events
    const $courseToolLink = $(options.courseToolLink);
    $courseToolLink.on('click', (event) => {
      const courseToolName = event.srcElement.dataset['analytics-id']; // eslint-disable-line dot-notation
      Logger.log(
        'edx.course.tool.accessed',
        {
          tool_name: courseToolName,
        },
      );
    });
  }
}
