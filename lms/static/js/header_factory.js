(function(define) {
    'use strict';

    define([
        'edx-ui-toolkit/js/dropdown-menu/dropdown-menu-view'
    ],
    function(DropdownMenuView) {
        return function() {
            // eslint-disable-next-line no-var
            var dropdownMenuView = new DropdownMenuView({
                el: '.js-header-user-menu'
            }).postRender();

            return dropdownMenuView;
        };
    });
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
