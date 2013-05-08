CMS.Views.Alert = Backbone.View.extend({
    template: _.template($("#alert-tpl").text()),
    initialize: function() {
        this.setElement($("#page-alert"));
        this.listenTo(this.model, 'change', this.render);
    },
    render: function() {
        this.$el.html(this.template(this.model.attributes));
        return this;
    }
});
