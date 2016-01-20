define(["jquery", "underscore", "backbone", "gettext", "js/utils/handle_iframe_binding", "js/utils/templates",
        "js/views/utils/view_utils"],
    function ($, _, Backbone, gettext, IframeUtils, TemplateUtils, ViewUtils) {
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

            options: {
                // UX is moving towards using 'is-collapsed' in preference over 'collapsed',
                // but use the old scheme as the default so that existing code doesn't need
                // to be rewritten.
                collapsedClass: 'collapsed'
            },

            //override the constructor function
            constructor: function(options) {
                _.bindAll(this, 'beforeRender', 'render', 'afterRender');
                var _this = this;
                this.render = _.wrap(this.render, function (render, options) {
                    _this.beforeRender();
                    render(options);
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
                // Don't propagate the event as it is possible that two views will both contain
                // this element, e.g. clicking on the element of a child view container in a parent.
                event.stopPropagation();
                event.preventDefault();
                ViewUtils.toggleExpandCollapse(target, this.options.collapsedClass);
            },

            /**
             * Loads the named template from the page, or logs an error if it fails.
             * @param name The name of the template.
             * @returns The loaded template.
             */
            loadTemplate: function(name) {
                return TemplateUtils.loadTemplate(name);
            }
        });

        return BaseView;
    });
