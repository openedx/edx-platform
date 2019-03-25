/* globals setFixtures */

import Backbone from 'backbone';

import CourseCardModel from '../models/course_card_model';
import CourseEnrollModel from '../models/course_enroll_model';
import CourseEnrollView from '../views/course_enroll_view';

describe('Course Enroll View', () => {
  let view = null;
  let courseCardModel;
  let courseEnrollModel;
  let urlModel;
  let singleCourseRunList;
  let multiCourseRunList;
  const course = {
    key: 'WageningenX+FFESx',
    uuid: '9f8562eb-f99b-45c7-b437-799fd0c15b6a',
    title: 'Systems thinking and environmental sustainability',
    owners: [
      {
        uuid: '0c6e5fa2-96e8-40b2-9ebe-c8b0df2a3b22',
        key: 'WageningenX',
        name: 'Wageningen University & Research',
      },
    ],
  };
  const urls = {
    commerce_api_url: '/commerce',
    track_selection_url: '/select_track/course/',
  };

  beforeEach(() => {
        // Stub analytics tracking
    window.analytics = jasmine.createSpyObj('analytics', ['track']);

        // NOTE: This data is redefined prior to each test case so that tests
        // can't break each other by modifying data copied by reference.
    singleCourseRunList = [{
      key: 'course-v1:WageningenX+FFESx+1T2017',
      uuid: '2f2edf03-79e6-4e39-aef0-65436a6ee344',
      title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
      image: {
        src: 'https://example.com/2f2edf03-79e6-4e39-aef0-65436a6ee344.jpg',
      },
      marketing_url: 'https://www.edx.org/course/food-security-sustainability-systems-wageningenx-ffesx',
      start: '2017-02-28T05:00:00Z',
      end: '2017-05-30T23:00:00Z',
      enrollment_start: '2017-01-18T00:00:00Z',
      enrollment_end: null,
      type: 'verified',
      certificate_url: '',
      course_url: 'https://courses.example.com/courses/course-v1:edX+DemoX+Demo_Course',
      enrollment_open_date: 'Jan 18, 2016',
      is_course_ended: false,
      is_enrolled: false,
      is_enrollment_open: true,
      status: 'published',
      upgrade_url: '',
    }];

    multiCourseRunList = [{
      key: 'course-v1:WageningenX+FFESx+2T2016',
      uuid: '9bbb7844-4848-44ab-8e20-0be6604886e9',
      title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
      image: {
        src: 'https://example.com/9bbb7844-4848-44ab-8e20-0be6604886e9.jpg',
      },
      short_description: 'Learn how to apply systems thinking to improve food production systems.',
      marketing_url: 'https://www.edx.org/course/food-security-sustainability-systems-wageningenx-stesx',
      start: '2016-09-08T04:00:00Z',
      end: '2016-11-11T00:00:00Z',
      enrollment_start: null,
      enrollment_end: null,
      pacing_type: 'instructor_paced',
      type: 'verified',
      certificate_url: '',
      course_url: 'https://courses.example.com/courses/course-v1:WageningenX+FFESx+2T2016',
      enrollment_open_date: 'Jan 18, 2016',
      is_course_ended: false,
      is_enrolled: false,
      is_enrollment_open: true,
      status: 'published',
    }, {
      key: 'course-v1:WageningenX+FFESx+1T2017',
      uuid: '2f2edf03-79e6-4e39-aef0-65436a6ee344',
      title: 'Food Security and Sustainability: Systems thinking and environmental sustainability',
      image: {
        src: 'https://example.com/2f2edf03-79e6-4e39-aef0-65436a6ee344.jpg',
      },
      marketing_url: 'https://www.edx.org/course/food-security-sustainability-systems-wageningenx-ffesx',
      start: '2017-02-28T05:00:00Z',
      end: '2017-05-30T23:00:00Z',
      enrollment_start: '2017-01-18T00:00:00Z',
      enrollment_end: null,
      type: 'verified',
      certificate_url: '',
      course_url: 'https://courses.example.com/courses/course-v1:WageningenX+FFESx+1T2017',
      enrollment_open_date: 'Jan 18, 2016',
      is_course_ended: false,
      is_enrolled: false,
      is_enrollment_open: true,
      status: 'published',
    }];
  });

  const setupView = (courseRuns, urlMap) => {
    course.course_runs = courseRuns;
    setFixtures('<div class="course-actions"></div>');
    courseCardModel = new CourseCardModel(course);
    courseEnrollModel = new CourseEnrollModel({}, {
      courseId: courseCardModel.get('course_run_key'),
    });
    if (urlMap) {
      urlModel = new Backbone.Model(urlMap);
    }
    view = new CourseEnrollView({
      $parentEl: $('.course-actions'),
      model: courseCardModel,
      enrollModel: courseEnrollModel,
      urlModel,
    });
  };

  afterEach(() => {
    view.remove();
    urlModel = null;
    courseCardModel = null;
    courseEnrollModel = null;
  });

  it('should exist', () => {
    setupView(singleCourseRunList);
    expect(view).toBeDefined();
  });

  it('should render the course enroll view when not enrolled', () => {
    setupView(singleCourseRunList);
    expect(view.$('.enroll-button').text().trim()).toEqual('Enroll Now');
    expect(view.$('.run-select').length).toBe(0);
  });

  it('should render the course enroll view when enrolled', () => {
    singleCourseRunList[0].is_enrolled = true;

    setupView(singleCourseRunList);
    expect(view.$('.view-course-button').text().trim()).toEqual('View Course');
    expect(view.$('.run-select').length).toBe(0);
  });

  it('should not render anything if course runs are empty', () => {
    setupView([]);

    expect(view.$('.run-select').length).toBe(0);
    expect(view.$('.enroll-button').length).toBe(0);
  });

  it('should render run selection dropdown if multiple course runs are available', () => {
    setupView(multiCourseRunList);

    expect(view.$('.run-select').length).toBe(1);
    expect(view.$('.run-select').val()).toEqual(multiCourseRunList[0].key);
    expect(view.$('.run-select option').length).toBe(2);
  });

  it('should not allow enrollment in unpublished course runs', () => {
    multiCourseRunList[0].status = 'unpublished';

    setupView(multiCourseRunList);
    expect(view.$('.run-select').length).toBe(0);
    expect(view.$('.enroll-button').length).toBe(1);
  });

  it('should not allow enrollment in course runs with a null status', () => {
    multiCourseRunList[0].status = null;

    setupView(multiCourseRunList);
    expect(view.$('.run-select').length).toBe(0);
    expect(view.$('.enroll-button').length).toBe(1);
  });

  it('should enroll learner when enroll button is clicked with one course run available', () => {
    setupView(singleCourseRunList);

    expect(view.$('.enroll-button').length).toBe(1);

    spyOn(courseEnrollModel, 'save');

    view.$('.enroll-button').click();

    expect(courseEnrollModel.save).toHaveBeenCalled();
  });

  it('should enroll learner when enroll button is clicked with multiple course runs available', () => {
    setupView(multiCourseRunList);

    spyOn(courseEnrollModel, 'save');

    view.$('.run-select').val(multiCourseRunList[1].key);
    view.$('.run-select').trigger('change');
    view.$('.enroll-button').click();

    expect(courseEnrollModel.save).toHaveBeenCalled();
  });

  it('should redirect to track selection when audit enrollment succeeds', () => {
    singleCourseRunList[0].is_enrolled = false;
    singleCourseRunList[0].mode_slug = 'audit';

    setupView(singleCourseRunList, urls);

    expect(view.$('.enroll-button').length).toBe(1);
    expect(view.trackSelectionUrl).toBeDefined();

    spyOn(CourseEnrollView, 'redirect');

    view.enrollSuccess();

    expect(CourseEnrollView.redirect).toHaveBeenCalledWith(
      view.trackSelectionUrl + courseCardModel.get('course_run_key'));
  });

  it('should redirect to track selection when enrollment in an unspecified mode is attempted', () => {
    singleCourseRunList[0].is_enrolled = false;
    singleCourseRunList[0].mode_slug = null;

    setupView(singleCourseRunList, urls);

    expect(view.$('.enroll-button').length).toBe(1);
    expect(view.trackSelectionUrl).toBeDefined();

    spyOn(CourseEnrollView, 'redirect');

    view.enrollSuccess();

    expect(CourseEnrollView.redirect).toHaveBeenCalledWith(
      view.trackSelectionUrl + courseCardModel.get('course_run_key'),
    );
  });

  it('should not redirect when urls are not provided', () => {
    singleCourseRunList[0].is_enrolled = false;
    singleCourseRunList[0].mode_slug = 'verified';

    setupView(singleCourseRunList);

    expect(view.$('.enroll-button').length).toBe(1);
    expect(view.verificationUrl).not.toBeDefined();
    expect(view.dashboardUrl).not.toBeDefined();
    expect(view.trackSelectionUrl).not.toBeDefined();

    spyOn(CourseEnrollView, 'redirect');

    view.enrollSuccess();

    expect(CourseEnrollView.redirect).not.toHaveBeenCalled();
  });

  it('should redirect to track selection on error', () => {
    setupView(singleCourseRunList, urls);

    expect(view.$('.enroll-button').length).toBe(1);
    expect(view.trackSelectionUrl).toBeDefined();

    spyOn(CourseEnrollView, 'redirect');

    view.enrollError(courseEnrollModel, { status: 500 });
    expect(CourseEnrollView.redirect).toHaveBeenCalledWith(
      view.trackSelectionUrl + courseCardModel.get('course_run_key'),
    );
  });

  it('should redirect to login on 403 error', () => {
    const response = {
      status: 403,
      responseJSON: {
        user_message_url: 'redirect/to/this',
      },
    };

    setupView(singleCourseRunList, urls);

    expect(view.$('.enroll-button').length).toBe(1);
    expect(view.trackSelectionUrl).toBeDefined();

    spyOn(CourseEnrollView, 'redirect');

    view.enrollError(courseEnrollModel, response);

    expect(CourseEnrollView.redirect).toHaveBeenCalledWith(
      response.responseJSON.user_message_url,
    );
  });

  it('sends analytics event when enrollment succeeds', () => {
    setupView(singleCourseRunList, urls);
    spyOn(CourseEnrollView, 'redirect');
    view.enrollSuccess();
    expect(window.analytics.track).toHaveBeenCalledWith(
      'edx.bi.user.program-details.enrollment',
    );
  });
});
