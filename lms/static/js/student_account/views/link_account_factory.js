(function(define) {
    'use strict';
    define('js/student_account/views/link_account_factory',
        [
            'gettext', 'jquery', 'underscore', 'backbone',
            'js/student_account/views/LinkAccountView'
        ],
        function(gettext, $, _, Backbone, LinkAccountView) {
            return function(authData, platformName, userName, duplicateProvider) {
                var provider = authData.providers && authData.providers[0];
                var view = new LinkAccountView({
                    connectUrl: provider.connect_url,
                    providerName: provider.name,
                    platformName: platformName,
                    userName: userName,
                    duplicateProvider: duplicateProvider
                });
                view.render();
                return view;
            };
        }
    );
}).call(this, define || RequireJS.define);
