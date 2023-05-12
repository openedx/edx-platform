(function($) {
    $.fn.extend({
    /*
     * leanModal prepares an element to be a modal dialog.  Call it once on the
     * element that launches the dialog, when the page is ready.  This function
     * will add a .click() handler that properly opens the dialog.
     *
     * The launching element must:
     *   - be an <a> element, not a button,
     *   - have an href= attribute identifying the id of the dialog element,
     *   - have rel='leanModal'.
     */
        leanModal: function(options) {
            // eslint-disable-next-line no-var
            var defaults = {
                top: 100,
                overlay: 0.5,
                closeButton: null,
                position: 'fixed'
            };

            // eslint-disable-next-line eqeqeq
            if ($('#lean_overlay').length == 0) {
                // eslint-disable-next-line no-var
                var $overlay = $("<div id='lean_overlay'></div>");
                $('body').append($overlay);
            }

            options = $.extend(defaults, options);

            return this.each(function() {
                // eslint-disable-next-line no-var
                var o = options;

                $(this).click(function(e) {
                    $('.modal, .js-modal').hide();

                    /* eslint-disable-next-line camelcase, no-var */
                    var modal_id = $(this).attr('href');

                    if ($(modal_id).hasClass('video-modal')) {
                        // Video modals need to be cloned before being presented as a modal
                        // This is because actions on the video get recorded in the history.
                        // Deleting the video (clone) prevents the odd back button behavior.
                        /* eslint-disable-next-line camelcase, no-var */
                        var modal_clone = $(modal_id).clone(true, true);
                        // eslint-disable-next-line camelcase
                        modal_clone.attr('id', 'modal_clone');
                        $(modal_id).after(modal_clone); // xss-lint: disable=javascript-jquery-insertion
                        // eslint-disable-next-line camelcase
                        modal_id = '#modal_clone';
                    }

                    // eslint-disable-next-line no-shadow
                    $('#lean_overlay').click(function(e) {
                        // eslint-disable-next-line no-use-before-define
                        close_modal(modal_id, e);
                    });

                    // eslint-disable-next-line no-shadow
                    $(o.closeButton).click(function(e) {
                        // eslint-disable-next-line no-use-before-define
                        close_modal(modal_id, e);
                    });

                    // To enable closing of email modal when copy button hit
                    // eslint-disable-next-line no-shadow
                    $(o.copyEmailButton).click(function(e) {
                        // eslint-disable-next-line no-use-before-define
                        close_modal(modal_id, e);
                    });

                    /* eslint-disable-next-line camelcase, no-unused-vars, no-var */
                    var modal_height = $(modal_id).outerHeight();
                    /* eslint-disable-next-line camelcase, no-var */
                    var modal_width = $(modal_id).outerWidth();

                    $('#lean_overlay').css({display: 'block', opacity: 0});
                    $('#lean_overlay').fadeTo(200, o.overlay);

                    $('iframe', modal_id).attr('src', $('iframe', modal_id).data('src'));
                    if ($(modal_id).hasClass('email-modal')) {
                        $(modal_id).css({
                            width: 80 + '%',
                            height: 80 + '%',
                            position: o.position,
                            opacity: 0,
                            'z-index': 11000,
                            left: 10 + '%',
                            top: 10 + '%'
                        });
                    } else {
                        $(modal_id).css({
                            position: o.position,
                            opacity: 0,
                            'z-index': 11000,
                            left: 50 + '%',
                            // eslint-disable-next-line camelcase
                            'margin-left': -(modal_width / 2) + 'px',
                            top: o.top + 'px'
                        });
                    }

                    $(modal_id).show().fadeTo(200, 1);
                    $(modal_id).find('.notice').hide().html('');
                    window.scrollTo(0, 0);
                    e.preventDefault();
                });
            });

            // eslint-disable-next-line camelcase
            function close_modal(modal_id, e) {
                $('#lean_overlay').fadeOut(200);
                $('iframe', modal_id).attr('src', '');
                $(modal_id).css({display: 'none'});
                /* eslint-disable-next-line camelcase, eqeqeq */
                if (modal_id == '#modal_clone') {
                    $(modal_id).remove();
                }
                e.preventDefault();
            }
        }
    });

    // eslint-disable-next-line no-shadow
    $(document).ready(function($) {
        $('a[rel*=leanModal]').each(function() {
            // eslint-disable-next-line no-var
            var $link = $(this),
                closeButton = $link.data('modalCloseButtonSelector') || '.close-modal',
                embed;

            $link.leanModal({
                top: 120, overlay: 1, closeButton: closeButton, position: 'absolute'
            });
            embed = $($link.attr('href')).find('iframe');
            if (embed.length > 0 && embed.attr('src')) {
                // eslint-disable-next-line no-var
                var sep = (embed.attr('src').indexOf('?') > 0) ? '&' : '?';
                embed.data('src', embed.attr('src') + sep + 'autoplay=1&rel=0');
                embed.attr('src', '');
            }
        });
    });
// eslint-disable-next-line no-undef
}(jQuery));
