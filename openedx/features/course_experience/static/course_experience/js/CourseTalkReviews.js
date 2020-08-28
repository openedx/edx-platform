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
    $.getScript(options.readSrc, () => { // eslint-disable-line func-names
      $('iframe').load(() => {
        $(options.loadIcon).hide();
      });
    });
    $courseTalkToggleReadWriteReviews.text(toWriteBtnText);

    $courseTalkToggleReadWriteReviews.on('click', () => {
      const switchToReadView = self.currentSrc === options.writeSrc;
      // Cache js file for future button clicks
      $.ajaxSetup({ cache: true });

      // Show the loading icon
      $(options.loadIcon).show();

      // Update toggle button text
      const newBtnText = switchToReadView ? toWriteBtnText : toReadBtnText;
      $courseTalkToggleReadWriteReviews.text(newBtnText);

      // Toggle the new coursetalk script object
      self.currentSrc = switchToReadView ? options.readSrc : options.writeSrc;
      $.getScript(self.currentSrc, () => { // eslint-disable-line func-names
        $('iframe').load(() => {
          $(options.loadIcon).hide();
        });
      });
    });
  }
}
