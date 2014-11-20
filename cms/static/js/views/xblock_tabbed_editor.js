/**
 * XBlockEditorView displays the authoring view of an xblock, and allows the user to switch between
 * the available modes.
 */
define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/xblock"],
    function ($, _, gettext, BaseView, XBlockView) {

        var XBlockTabbedEditorView = BaseView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('xblock-tabbed-editor');
            },

            render: function(options) {
                this.$el.html(this.template({
                    tabs: this.model.editor_tabs,
                    xblockInfo: this.model
                }));
                this.xblockView = new XBlockView({
                    el: this.$('.xblock-editor'),
                    model: this.model,
                    view: 'xml_tab_view'
                });
                this.xblockView.render({
                    success: options.success
                });
                return this;
            },

            hasCustomTabs: function() {
                return true;
            },

            hasCustomButtons: function() {
                return false;
            },

            notifyRuntime: function() {
                // TODO: do something real!!!
            }
        });

        return XBlockTabbedEditorView;
    }); // end define();
