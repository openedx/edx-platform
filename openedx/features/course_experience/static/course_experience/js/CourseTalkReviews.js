/**
  Enable users to switch between viewing and writing CourseTalk reviews.
 */

export class CourseTalkReviews {  // eslint-disable-line import/prefer-default-export
  constructor(options) {
    const $courseTalkToggleReadWriteReviews = $(options.toggleButton);

    const toReadBtnText = 'View Reviews';
    const toWriteBtnText = 'Write a Review';

    // Initialize page to the read reviews view
    self.currentSrc = options.readSrc;
    $.getScript(options.readSrc);
    $courseTalkToggleReadWriteReviews.text(toWriteBtnText);

    $courseTalkToggleReadWriteReviews.on('click', () => {
      // Cache js file for future button clicks
      $.ajaxSetup({ cache: true });

      // Toggle the new coursetalk script object
      const switchToReadView = self.currentSrc === options.writeSrc;
      self.currentSrc = switchToReadView ? options.readSrc : options.writeSrc;
      $.getScript(self.currentSrc);

      // Toggle button text on switch to the other view
      const newText = switchToReadView ? toWriteBtnText : toReadBtnText;
      $courseTalkToggleReadWriteReviews.text(newText);
    });
  }
}
