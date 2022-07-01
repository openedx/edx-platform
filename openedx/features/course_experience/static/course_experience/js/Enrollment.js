
/*
 * Course Enrollment on the Course Home page
 */
export class CourseEnrollment {  // eslint-disable-line import/prefer-default-export
  /**
   * Redirect to a URL.  Mainly useful for mocking out in tests.
   * @param  {string} url The URL to redirect to.
   */
  static redirect(url) {
    window.location.href = url;
  }

  static refresh() {
    window.location.reload(false);
  }

  static createEnrollment(courseId) {
    const data = JSON.stringify({
      course_details: { course_id: courseId },
    });
    const enrollmentAPI = '/api/enrollment/v1/enrollment';
    const trackSelection = '/course_modes/choose/';

    return () =>
      $.ajax(
        {
          type: 'POST',
          url: enrollmentAPI,
          data,
          contentType: 'application/json',
        }).done(() => {
          window.analytics.track('edx.bi.user.course-home.enrollment');
          CourseEnrollment.refresh();
        }).fail(() => {
          // If the simple enrollment we attempted failed, go to the track selection page,
          // which is better for handling more complex enrollment situations.
          CourseEnrollment.redirect(trackSelection + courseId);
        });
  }

  constructor(buttonClass, courseId) {
    $(buttonClass).click(CourseEnrollment.createEnrollment(courseId));
  }
}
