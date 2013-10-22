define(["backbone", "underscore", "gettext", "js/views/section_edit", "require"], function(Backbone, _, gettext, SectionEditView, require) {

    var SectionShow = Backbone.View.extend({
        template: _.template('<span data-tooltip="<%= gettext("Edit this section\'s name") %>" class="section-name-span"><%= name %></span>'),
        render: function() {
            var attrs = {
                name: this.model.escape('name')
            };
            this.$el.html(this.template(attrs));
            this.delegateEvents();
            return this;
        },
        events: {
            "click": "switchToEditView"
        },
        switchToEditView: function() {
            if(!this.editView) {
                SectionEditView = require('js/views/section_edit');
                this.editView = new SectionEditView({
                    model: this.model, el: this.el, showView: this});
            }
            this.undelegateEvents();
            this.editView.render();
        }
    });
    return SectionShow;

});
