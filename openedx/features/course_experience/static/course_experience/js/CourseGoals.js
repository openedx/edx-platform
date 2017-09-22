/* globals gettext */

export class CourseGoals {  // eslint-disable-line import/prefer-default-export

  constructor(options) {
    $('.goal-option').click((e) => {
      const goalKey = $(e.target).data().choice;
      $.ajax({
        method: 'POST',
        url: options.goalApiUrl,
        headers: { 'X-CSRFToken': $.cookie('csrftoken') },
        data: {
          goal_key: goalKey,
          course_key: options.courseId,
          user: options.username,
        },
        dataType: 'json',
        success: () => {
          // LEARNER-2522 will address the success message
          const successMsg = gettext('Thank you for setting your course goal!');
          // xss-lint: disable=javascript-jquery-html
          $('.message-content').html(`<div class="success-message">${successMsg}</div>`);
        },
        error: () => {
          // LEARNER-2522 will address the error message
          const errorMsg = gettext('There was an error in setting your goal, please reload the page and try again.'); // eslint-disable-line max-len
          // xss-lint: disable=javascript-jquery-html
          $('.message-content').html(`<div class="error-message"> ${errorMsg} </div>`);
        },
      });
    });

    // Allow goal selection with an enter press for accessibility purposes
    $('.goal-option').keyup((e) => {
      if (e.which === 13) {
        $(e.target).trigger('click');
      }
    });
  }
}
