window.MasterClass = function (el) {
    RequireJS.require(['MasterClassMain'], function (MasterClassMain) {
        new MasterClassMain(el);
    });
};
