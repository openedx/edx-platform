/* globals setFixtures */

import UnenrollView from '../views/unenroll_view';

describe('Unenroll View', () => {
    let view = null;
    const options = {
        urls: {
            dashboard: '/dashboard',
            browseCourses: '/courses',
        },
        isEdx: true,
    };

    const initView = () => new UnenrollView(options);

    beforeEach(() => {
        setFixtures('<div class="unenroll-modal"><div class="wrapper-action-more" data-course-key="course-v1:edX+DemoX+Demo_Course"> <button type="button" class="action action-more" id="actions-dropdown-link-0" aria-haspopup="true" aria-expanded="true" aria-controls="actions-dropdown-0" data-course-number="DemoX" data-course-name="edX Demonstration Course" data-dashboard-index="0"> <span class="sr">Course options for</span> <span class="sr">&nbsp;  edX Demonstration Course </span> <span class="fa fa-cog" aria-hidden="true"></span> </button> <div class="actions-dropdown is-visible" id="actions-dropdown-0" tabindex="-1"> <ul class="actions-dropdown-list" id="actions-dropdown-list-0" aria-label="Available Actions" role="menu"> <div class="reasons_survey"> <div class="slide1 hidden">  <h3>We\'re sorry to see you go! Please share your main reason for unenrolling.</h3><br>  <ul class="options">  <li><label class="option"><input type="radio" name="reason" val="I don\'t have enough support">I don\'t have enough support</label></li><li><label class="option"><input type="radio" name="reason" val="I don’t have the academic or language prerequisites">I don\'t have the academic or language prerequisites</label></li><li><label class="option"><input type="radio" name="reason" val="Something was broken">Something was broken</label></li><li><label class="option"><input type="radio" name="reason" val="I just wanted to browse the material">I just wanted to browse the material</label></li><li><label class="option"><input type="radio" name="reason" val="This won’t help me reach my goals">This won\'t help me reach my goals</label></li><li><label class="option"><input type="radio" name="reason" val="I am not happy with the quality of the content">I am not happy with the quality of the content</label></li><li><label class="option"><input type="radio" name="reason" val="The course material was too hard">The course material was too hard</label></li><li><label class="option"><input type="radio" name="reason" val="I don\'t have the time">I don\'t have the time</label></li><li><label class="option"><input type="radio" name="reason" val="The course material was too easy">The course material was too easy</label></li><li><label class="option"><input class="other_radio" type="radio" name="reason" val="Other">Other <input type="text" class="other_text"></label></li></ul>  <button class="submit_reasons">Submit</button> </div> </div> <div class="slide2 hidden"> Thank you for sharing your reasons for unenrolling.<br> You are unenrolled from edX Demonstration Course. <a class="button survey_button return_to_dashboard">  Return To Dashboard </a> <a class="button survey_button browse_courses">  Browse Courses </a> </div>   <li class="actions-item" id="actions-item-unenroll-0">   <a href="#unenroll-modal" class="action action-unenroll" rel="leanModal" data-course-id="course-v1:edX+DemoX+Demo_Course" data-course-number="DemoX" data-course-name="edX Demonstration Course" data-dashboard-index="0" data-track-info="Are you sure you want to unenroll from %(course_name)s (%(course_number)s)?" id="unenroll-0">    Unenroll   </a>  </li>  <li class="actions-item" id="actions-item-email-settings-0">  </li>  </ul> </div> </div></div>');  // eslint-disable-line max-len
    });

    afterEach(() => {
        view.remove();
    });

    it('should exist', () => {
        view = initView();
        expect(view).toBeDefined();
    });

    it('switch between slides', () => {
        view = initView();
        expect($('.slide1').hasClass('hidden')).toEqual(true);
        view.switchToSlideOne();
        expect($('.slide1').hasClass('hidden')).toEqual(false);
        expect($('.slide2').hasClass('hidden')).toEqual(true);
        view.switchToSlideTwo();
        expect($('.slide2').hasClass('hidden')).toEqual(false);
    });
});
