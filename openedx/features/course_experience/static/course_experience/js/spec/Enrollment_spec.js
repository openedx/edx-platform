/* globals $, loadFixtures */

import {
  expectRequest,
  requests as mockRequests,
  respondWithJson,
  respondWithError,
} from 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers';
import { CourseEnrollment } from '../Enrollment';


describe('CourseEnrollment tests', () => {
  describe('Ensure button behavior', () => {
    const endpointUrl = '/api/enrollment/v1/enrollment';
    const courseId = 'course-v1:edX+DemoX+Demo_Course';
    const enrollButtonClass = '.enroll-btn';

    window.analytics = jasmine.createSpyObj('analytics', ['page', 'track', 'trackLink']);

    beforeEach(() => {
      loadFixtures('course_experience/fixtures/enrollment-button.html');
      new CourseEnrollment('.enroll-btn', courseId);  // eslint-disable-line no-new
    });
    it('Verify that we reload on success', () => {
      const requests = mockRequests(this);
      $(enrollButtonClass).click();
      expectRequest(
        requests,
        'POST',
        endpointUrl,
        `{"course_details":{"course_id":"${courseId}"}}`,
      );
      spyOn(CourseEnrollment, 'refresh');
      respondWithJson(requests);
      expect(CourseEnrollment.refresh).toHaveBeenCalled();
      expect(window.analytics.track).toHaveBeenCalled();
      requests.restore();
    });
    it('Verify that we redirect to track selection on fail', () => {
      const requests = mockRequests(this);
      $(enrollButtonClass).click();
      spyOn(CourseEnrollment, 'redirect');
      respondWithError(requests, 403);
      expect(CourseEnrollment.redirect).toHaveBeenCalled();
      requests.restore();
    });
  });
});
