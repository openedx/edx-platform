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
        success: (data) => { // LEARNER-2522 will address the success message
          $('.section-goals').slideDown();
          $('.section-goals .goal .text').text(data.goal_text);
          $('.section-goals select').val(data.goal_key);
          const successMsg = gettext(`Thank you for setting your course goal to ${data.goal_text.toLowerCase()}!`);
          if (!data.is_unsure) {
            // xss-lint: disable=javascript-jquery-html
            $('.message-content').html(`<div class="success-message">${successMsg}</div>`);
          } else {
            $('.message-content').parent().hide();
          }
        },
        error: () => { // LEARNER-2522 will address the error message
          const errorMsg = gettext('There was an error in setting your goal, please reload the page and try again.');
          // xss-lint: disable=javascript-jquery-html
          $('.message-content').html(`<div class="error-message"> ${errorMsg} </div>`);
        },
      });
    });

    // Allow goal selection with an enter press for accessibility purposes
    $('.goal-option').keypress((e) => {
      if (e.which === 13) {
        $(e.target).click();
      }
    });
  }
}
