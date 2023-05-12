var FaceBook = (function() {
    var _args = {};

    return {
        init: function(Args) {
            _args = Args;
            window.fbAsyncInit = function() {
                // eslint-disable-next-line no-undef
                FB.init({
                    appId: _args.facebook_app_id,
                    xfbml: true,
                    version: 'v2.3'
                });
            };
            (function(d, s, id) {
                var js,
                    fjs = d.getElementsByTagName(s)[0];
                if (d.getElementById(id)) { return; }
                js = d.createElement(s); js.id = id;
                js.src = '//connect.facebook.net/en_US/sdk.js';
                fjs.parentNode.insertBefore(js, fjs);
            }(document, 'script', 'facebook-jssdk'));
        },
        // eslint-disable-next-line camelcase
        share: function(feed_data) {
            FB.ui( // eslint-disable-line no-undef
                {
                    method: 'feed',
                    // eslint-disable-next-line camelcase
                    name: feed_data.share_text,
                    // eslint-disable-next-line camelcase
                    link: feed_data.share_link,
                    // eslint-disable-next-line camelcase
                    picture: feed_data.picture_link,
                    // eslint-disable-next-line camelcase
                    description: feed_data.description
                },
                // The Facebook API now requires a callback. Since we weren't doing anything after posting before,
                // I'm leaving this as an empty function.
                function(response) {} // eslint-disable-line no-unused-vars
            );
        }
    };
}());
