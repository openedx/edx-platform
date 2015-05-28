RequireJS.require(['js/discovery/app'], function (App) {
    'use strict';

    new App(getParameterByName('search_query'));

});
