var edx = edx || {},

    Navigation = (function() {

        var navigation = {

            init: function() {

                if ($('#accordion').length) {

                    navigation.openAccordion();
                    navigation.checkForCurrent();
                    navigation.listenForClick();
                }
            },

            openAccordion: function() {
                $('#open_close_accordion a').click();
                $('.course-wrapper').toggleClass('closed');
                $('#accordion').show();
            },

            checkForCurrent: function() {
                var active;

                active = $('#accordion div div:has(a.active)').index('#accordion div div');

                if (typeof active === 'undefined' || active < 0) {
                    active = 0;
                }

                if (active > 0) {
                    $('#accordion').find('.button-chapter:eq(' + active + ')').trigger('click');
                }
            },

            listenForClick: function() {
                $('#accordion').on('click', '.button-chapter', function(event) {
                    // close and reset all accrdions
                    navigation.resetAllAccordions();

                    // open this accordion and send focus
                    navigation.openAccordionSection(event.currentTarget);

                    // assign classes and set open aria
                    navigation.setAriaAttrs(event.currentTarget);
                });
            },

            resetAllAccordions: function() {
                $('.chapter-content-container').hide();
                $('.chapter-content-container .chapter-menu').hide();

                $('#accordion .button-chapter').each(function(event) {
                    $(this).removeClass('is-open').attr('aria-pressed', 'false');
                    $(this).next('.chapter-content-container').attr('aria-expanded', 'false');
                    $(this).children('.group-heading').removeClass('active');
                    $(this).children('.group-heading').find('.icon').addClass('fa-caret-right').removeClass('fa-caret-down');
                });
            },

            openAccordionSection: function(section) {
                $(section).next('.chapter-content-container').show().focus();
                $(section).next('.chapter-content-container').find('.chapter-menu').show();

                navigation.setAriaAttrs(section);
            },

            setAriaAttrs: function(section) {
                $(section).addClass('is-open').attr('aria-pressed', 'true');
                $(section).next('.chapter-content-container').attr('aria-expanded', 'true');
                $(section).children('.group-heading').addClass('active');
                $(section).children('.group-heading').find('.icon').removeClass('fa-caret-right').addClass('fa-caret-down');
            }
        };

        return {
            init: navigation.init
        };

    })();

    edx.util = edx.util || {};
    edx.util.navigation = Navigation;
    edx.util.navigation.init();
