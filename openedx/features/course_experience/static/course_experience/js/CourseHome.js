/* globals Logger */

export class CourseHome {  // eslint-disable-line import/prefer-default-export
  constructor(options) {
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
