/* globals gettext */

export class CourseGoals {  // eslint-disable-line import/prefer-default-export

  constructor(options) {
    $('.goal-option').click((e) => {
      const goal = $(e.target).data().choice;
      $.post({
        url: options.setGoalUrl,
        data: {
          goal,
        },
        dataType: 'json',
        success: (data) => {
          $('.message-content').html(data.html);
        },
        error: () => {
          $('.message-content').html(
              gettext('There was an error in setting your goal, please reload the page and try again.'),
          );
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
