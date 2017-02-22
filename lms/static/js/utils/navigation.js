var edx = edx || {},

    Navigation = (function() {
        var navigation = {

            init: function() {
                if ($('.accordion').length) {
                    navigation.loadAccordion();
                }
            },

            loadAccordion: function() {
                navigation.checkForCurrent();
                navigation.listenForClick();
                navigation.listenForKeypress();
            },

            getActiveIndex: function() {
                var index = $('.accordion .button-chapter:has(.active)').index('.accordion .button-chapter'),
                    button = null;

                if (index > -1) {
                    button = $('.accordion .button-chapter:eq(' + index + ')');
                }

                return button;
            },

            checkForCurrent: function() {
                var button = navigation.getActiveIndex();

                navigation.closeAccordions();

                if (button !== null) {
                    navigation.setupCurrentAccordionSection(button);
                }
            },

            listenForClick: function() {
                $('.accordion').on('click', '.button-chapter', function(event) {
                    event.preventDefault();

                    var button = $(event.currentTarget),
                        section = button.next('.chapter-content-container');

                    navigation.closeAccordions(button, section);
                    navigation.openAccordion(button, section);
                });
            },

            listenForKeypress: function() {
                $('.accordion').on('keydown', '.button-chapter', function(event) {
                    // because we're changing the role of the toggle from an 'a' to a 'button'
                    // we need to ensure it has the same keyboard use cases as a real button.
                    // this is useful for screenreader users primarily.
                    if (event.which == 32) { // spacebar
                        event.preventDefault();
                        $(event.currentTarget).trigger('click');
                    } else {
                        return true;
                    }
                });
            },

            closeAccordions: function(button, section) {
                var menu = $(section).find('.chapter-menu'), toggle;

                $('.accordion .button-chapter').each(function(index, element) {
                    toggle = $(element);

                    toggle
                        .removeClass('is-open')
                        .attr('aria-expanded', 'false');

                    toggle
                        .children('.group-heading')
                        .removeClass('active')
                        .find('.icon')
                            .addClass('fa-caret-right')
                            .removeClass('fa-caret-down');

                    toggle
                        .next('.chapter-content-container')
                        .removeClass('is-open')
                        .find('.chapter-menu').not(menu)
                            .removeClass('is-open')
                            .slideUp();
                });
            },

            setupCurrentAccordionSection: function(button) {
                var section = $(button).next('.chapter-content-container');

                navigation.openAccordion(button, section);
            },

            openAccordion: function(button, section) {
                var sectionEl = $(section),
                    firstLink = sectionEl.find('.menu-item').first(),
                    buttonEl = $(button);

                buttonEl
                    .addClass('is-open')
                    .attr('aria-expanded', 'true');

                buttonEl
                    .children('.group-heading')
                    .addClass('active')
                    .find('.icon')
                        .removeClass('fa-caret-right')
                        .addClass('fa-caret-down');

                sectionEl
                    .addClass('is-open')
                    .find('.chapter-menu')
                        .addClass('is-open')
                        .slideDown();
            }
        };

        return {
            init: navigation.init
        };
    })();

edx.util = edx.util || {};
edx.util.navigation = Navigation;
edx.util.navigation.init();
