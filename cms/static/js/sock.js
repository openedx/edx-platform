require(["domReady", "jquery", "jquery.smoothScroll"],
    function (domReady, $) {
        var toggleSock = function (e) {
            e.preventDefault();

            var $btnLabel = $(this).find('.copy');
            var $sock = $('.wrapper-sock');
            var $sockContent = $sock.find('.wrapper-inner');

            $sock.toggleClass('is-shown');
            $sockContent.toggle('fast');

            $.smoothScroll({
                offset: -200,
                easing: 'swing',
                speed: 1000,
                scrollElement: null,
                scrollTarget: $sock
            });

            if ($sock.hasClass('is-shown')) {
                $btnLabel.text(gettext('Hide Studio Help'));
            } else {
                $btnLabel.text(gettext('Looking for Help with Studio?'));
            }
        };

        domReady(function () {
            // toggling footer additional support
            $('.cta-show-sock').bind('click', toggleSock);
        });
    });
