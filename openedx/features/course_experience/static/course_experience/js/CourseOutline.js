/* globals Logger */

import { keys } from 'edx-ui-toolkit/js/utils/constants';

// @TODO: Figure out how to make webpack handle default exports when libraryTarget: 'window'
export class CourseOutline {  // eslint-disable-line import/prefer-default-export
  constructor() {
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

    function expandSection(sectionToggleButton) {
      const $toggleButtonChevron = $(sectionToggleButton).children('.fa-chevron-right');
      const $contentPanel = $(document.getElementById(sectionToggleButton.getAttribute('aria-controls')));

      $contentPanel.slideDown();
      $contentPanel.removeClass('is-hidden');
      $toggleButtonChevron.addClass('fa-rotate-90');
      sectionToggleButton.setAttribute('aria-expanded', 'true');
    }

    function collapseSection(sectionToggleButton) {
      const $toggleButtonChevron = $(sectionToggleButton).children('.fa-chevron-right');
      const $contentPanel = $(document.getElementById(sectionToggleButton.getAttribute('aria-controls')));

      $contentPanel.slideUp();
      $contentPanel.addClass('is-hidden');
      $toggleButtonChevron.removeClass('fa-rotate-90');
      sectionToggleButton.setAttribute('aria-expanded', 'false');
    }

    [...document.querySelectorAll(('.accordion'))]
      .forEach((accordion) => {
        const sections = Array.prototype.slice.call(accordion.querySelectorAll('.accordion-trigger'));

        sections.forEach(section => section.addEventListener('click', (event) => {
          const sectionToggleButton = event.currentTarget;
          if (sectionToggleButton.classList.contains('accordion-trigger')) {
            const isExpanded = sectionToggleButton.getAttribute('aria-expanded') === 'true';
            if (!isExpanded) {
              expandSection(sectionToggleButton);
            } else if (isExpanded) {
              collapseSection(sectionToggleButton);
            }
            event.stopImmediatePropagation();
          }
        }));
      });

    const toggleAllButton = document.querySelector('#expand-collapse-outline-all-button');
    const toggleAllSpan = document.querySelector('#expand-collapse-outline-all-span');
    const extraPaddingClass = 'expand-collapse-outline-all-extra-padding';
    toggleAllButton.addEventListener('click', (event) => {
      const toggleAllExpanded = toggleAllButton.getAttribute('aria-expanded') === 'true';
      let sectionAction;
      /* globals gettext */
      if (toggleAllExpanded) {
        toggleAllButton.setAttribute('aria-expanded', 'false');
        sectionAction = collapseSection;
        toggleAllSpan.classList.add(extraPaddingClass);
        toggleAllSpan.innerText = gettext('Expand All');
      } else {
        toggleAllButton.setAttribute('aria-expanded', 'true');
        sectionAction = expandSection;
        toggleAllSpan.classList.remove(extraPaddingClass);
        toggleAllSpan.innerText = gettext('Collapse All');
      }
      const sections = Array.prototype.slice.call(document.querySelectorAll('.accordion-trigger'));
      sections.forEach((sectionToggleButton) => {
        sectionAction(sectionToggleButton);
      });
      event.stopImmediatePropagation();
    });

    const urlHash = window.location.hash;

    if (urlHash !== '') {
      const button = document.getElementById(urlHash.substr(1, urlHash.length));
      if (button.classList.contains('subsection-text')) {
        const parentLi = button.closest('.section');
        const parentButton = parentLi.querySelector('.section-name');
        expandSection(parentButton);
      }
      expandSection(button);
    }
  }
}
