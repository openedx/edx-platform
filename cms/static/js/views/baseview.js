define(
    [
        'jquery',
        'underscore',
        'backbone',
        "js/utils/handle_iframe_binding"
    ],
    function ($, _, Backbone, IframeUtils) {
    /*  This view is extended from backbone with custom functions 'beforeRender' and 'afterRender'. It allows other
        views, which extend from it to access these custom functions. 'afterRender' function of BaseView calls a utility
        function 'iframeBinding' which modifies iframe src urls on a page so that they are rendered as part of the DOM.
        Other common functions which need to be run before/after can also be added here.
    */

    var BaseView = Backbone.View.extend({
        //override the constructor function
        constructor: function(options) {
            _.bindAll(this, 'beforeRender', 'render', 'afterRender');
            var _this = this;
            this.render = _.wrap(this.render, function (render) {
                _this.beforeRender();
                render();
                _this.afterRender();
                return _this;
            });

            //call Backbone's own constructor
            Backbone.View.prototype.constructor.apply(this, arguments);
        },

        beforeRender: function () {
        },

        render: function () {
            return this;
        },

        afterRender: function () {
            IframeUtils.iframeBinding(this);
        }
    });

    return BaseView;
});