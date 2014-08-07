define(["js/views/baseview", "underscore", "underscore.string", "jquery", "gettext"], 
        function(BaseView, _, str, $, gettext){
    _.str = str;
    var EditTopic = BaseView.extend({
        initialize: function(){
            this.template = _.template($("#edit-topic-tpl").text());
            this.listenTo(this.model, "change", this.render);
        },
        tagName: "li",
        className: function() {
            return "field-group topic topic" + this.model.get('order');
        },
        render: function() {
            this.$el.html(this.template({
                name: this.model.escape('name'),
                description: this.model.escape('description'),
                order: this.model.get('order'),
                error: this.model.validationError
            }));
            return this;
        },
        events: {
            "change .topic-name": "changeName",
            "change .topic-description": "changeDescription",
            "click .action-close": "removeTopic",
        },
        changeName: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set({
                name: this.$(".topic-name").val()
            }, {silent: true});
            return this;
        },
        changeDescription: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.set({
                description: this.$(".topic-description").val()
            }, {silent: true});
            return this;
        },
        removeTopic: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.model.collection.remove(this.model);
            return this.remove();
        },
    });
    return EditTopic;
});