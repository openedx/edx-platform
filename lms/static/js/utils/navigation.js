var edx = edx || {},

    Navigation = (function() {

        var navigation = {

            init: function() {

                if ($('.accordion').length) {

                    navigation.openAccordion();
                    navigation.checkForCurrent();
                    navigation.listenForClick();
                }
            },

            openAccordion: function() {
                navigation.checkForCurrent();
                navigation.listenForClick();
            },

            checkForCurrent: function() {
                var active = $('.accordion .chapter-content-container .chapter-menu:has(.active)').index('.accordion .chapter-content-container .chapter-menu') ? $('.accordion .chapter-content-container .chapter-menu:has(.active)').index('.accordion .chapter-content-container .chapter-menu') : 0,
                    activeSection = $('.accordion .button-chapter:eq(' + active + ')');

                active = $('#accordion div div:has(a.active)').index('#accordion div div');

                if (typeof active === 'undefined' || active < 0) {
                    active = 0;
                }

                if (active > 0) {
                    $('#accordion').find('.button-chapter:eq(' + active + ')').trigger('click');
                }
            },

            listenForClick: function() {
                $('.accordion').on('click', '.button-chapter', function(event) {
                    navigation.closeAccordions();
                    navigation.openAccordionSection(event.currentTarget);

                    // assign classes and set open aria
                    navigation.setAriaAttrs(event.currentTarget);
                });
            },

            resetAllAccordions: function() {
                $('.chapter-content-container').hide();
                $('.chapter-content-container .chapter-menu').hide();

                $('.accordion .button-chapter').each(function(event) {
                    var el = $(this);

                    el.removeClass('is-open').attr('aria-pressed', 'false');
                    el.next('.chapter-content-container').attr('aria-expanded', 'false');
                    el.children('.group-heading').removeClass('active');
                    el.children('.group-heading').find('.icon').addClass('fa-caret-right').removeClass('fa-caret-down');
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
