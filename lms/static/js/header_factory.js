;(function (define) {
    'use strict';

    define([
        'edx-ui-toolkit/js/dropdown-menu/dropdown-menu-view'
    ],
    function (DropdownMenuView) {
        return function() {
            var dropdownMenuView = new DropdownMenuView({
                el: '.js-header-user-menu'
            }).postRender();

            return dropdownMenuView;
        };
    });
}).call(this, define || RequireJS.define);
