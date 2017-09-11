/* globals $ */

export class CourseGoal {  // eslint-disable-line import/prefer-default-export

  constructor(options) {
    $('.goal-option').click(() => {
      $.ajax({
        type: 'POST',
        url: options.setCourseGoalUrl,
        success: () => {
          alert("woooo!!");
        },
      });
    });
  }
}
