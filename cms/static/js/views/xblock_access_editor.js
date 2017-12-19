/**
 * XBlockAccessEditor is a view that allows the user to restrict access at the unit level on the container page.
 * This view renders the button to restrict unit access into the appropriate place in the unit page.
 */
define(['js/views/baseview', 'edx-ui-toolkit/js/utils/html-utils'],
    function(BaseView, HtmlUtils) {
        'use strict';
        var XBlockAccessEditor = BaseView.extend({
            // takes XBlockInfo as a model
            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('xblock-access-editor');
            },

            render: function() {
                HtmlUtils.append(
                    this.$el,
                    HtmlUtils.HTML(this.template({}))
                );
                return this;
            }
        });

        return XBlockAccessEditor;
    }); // end define();
