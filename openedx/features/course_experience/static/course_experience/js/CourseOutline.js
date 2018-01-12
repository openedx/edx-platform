/* globals Logger */

import { keys } from 'edx-ui-toolkit/js/utils/constants';

// @TODO: Figure out how to make webpack handle default exports when libraryTarget: 'window'
export class CourseOutline {  // eslint-disable-line import/prefer-default-export
  constructor(newCourseOutlineEnabled) {
    const focusable = [...document.querySelectorAll('.outline-item.focusable')];

    focusable.forEach(el => el.addEventListener('keydown', (event) => {
      const index = focusable.indexOf(event.target);

      switch (event.key) {  // eslint-disable-line default-case
        case keys.down:
          event.preventDefault();
          focusable[Math.min(index + 1, focusable.length - 1)].focus();
          break;
        case keys.up:  // @TODO: Get these from the UI Toolkit
          event.preventDefault();
          focusable[Math.max(index - 1, 0)].focus();
          break;
      }
    }));

    [...document.querySelectorAll('a:not([href^="#"])')]
      .forEach(link => link.addEventListener('click', (event) => {
        Logger.log(
          'edx.ui.lms.link_clicked',
          {
            current_url: window.location.href,
            target_url: event.currentTarget.href,
          },
        );
      }),
    );

    // TODO: EDUCATOR-2283 Remove check for waffle flag after it is turned on.
    if (newCourseOutlineEnabled) {
      [...document.querySelectorAll(('.accordion'))]
        .forEach((accordion) => {
          const sections = Array.prototype.slice.call(accordion.querySelectorAll('.accordion-trigger'));

          sections.forEach(section => section.addEventListener('click', (event) => {
            const sectionToggleButton = event.currentTarget;
            const $toggleButtonChevron = $(sectionToggleButton).children('.fa-chevron-right');

            if (sectionToggleButton.classList.contains('accordion-trigger')) {
              const isExpanded = sectionToggleButton.getAttribute('aria-expanded') === 'true';
              const $contentPanel = $(document.getElementById(sectionToggleButton.getAttribute('aria-controls')));

              if (!isExpanded) {
                $contentPanel.slideDown();
                $contentPanel.removeClass('is-hidden');
                $toggleButtonChevron.addClass('fa-rotate-90');
                sectionToggleButton.setAttribute('aria-expanded', 'true');
              } else if (isExpanded) {
                $contentPanel.slideUp();
                $contentPanel.addClass('is-hidden');
                $toggleButtonChevron.removeClass('fa-rotate-90');
                sectionToggleButton.setAttribute('aria-expanded', 'false');
              }

              event.stopImmediatePropagation();
            }
          }));
        });
    }
  }
}
