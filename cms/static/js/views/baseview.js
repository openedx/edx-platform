define(["jquery", "underscore", "backbone", "js/utils/handle_iframe_binding"],
    function ($, _, Backbone, IframeUtils) {
        /*
          This view is extended from backbone to provide useful functionality for all Studio views.
          This functionality includes:
            - automatic expand and collapse of elements with the 'ui-toggle-expansion' class specified
            - additional control of rendering by overriding 'beforeRender' or 'afterRender'

          Note: the default 'afterRender' function calls a utility function 'iframeBinding' which modifies
          iframe src urls on a page so that they are rendered as part of the DOM.
         */

        var BaseView = Backbone.View.extend({
            events: {
                "click .ui-toggle-expansion": "toggleExpandCollapse"
            },

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

            beforeRender: function() {
            },

            render: function() {
                return this;
            },

            afterRender: function() {
                IframeUtils.iframeBinding(this);
            },

            toggleExpandCollapse: function(event) {
                var target = $(event.target);
                event.preventDefault();
                target.closest('.expand-collapse').toggleClass('expand').toggleClass('collapse');
                target.closest('.is-collapsible, .window').toggleClass('collapsed');
            },

            showLoadingIndicator: function() {
                $('.ui-loading').show();
            },

            hideLoadingIndicator: function() {
                $('.ui-loading').hide();
            }
        });

        return BaseView;
    });
