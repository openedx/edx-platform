define(["backbone", "underscore", "jquery", "js/views/edit_syllabus", "js/views/show_syllabus"],
        function(Backbone, _, $, EditSyllabusView, ShowSyllabusView) {
    var ListSyllabus = Backbone.View.extend({
        initialize: function() {
            this.emptyTemplate = _.template($("#no-syllabus-tpl").text());
            this.listenTo(this.collection, 'all', this.render);
            this.listenTo(this.collection, 'destroy', this.handleDestroy);
        },
        tagName: "div",
        className: "syllabus-list",
        render: function() {
            var syllabus = this.collection;
            if(syllabus.length === 0) {
                this.$el.html(this.emptyTemplate());
            }
            else {
                this.$el.empty();
                var that = this;
                syllabus.each(function(syllabus) {
                   var view;
                  if (syllabus.get("editing")) {
                        view = new EditSyllabusView({model: syllabus});
                    } else {
                        view = new ShowSyllabusView({model: syllabus});
                    }
                    that.$el.append(view.render().el);
                });
            }
            return this;
        },
        events: {
            "click .new-button": "addOne"
        },
        addOne: function(e) {
            if(e && e.preventDefault) { e.preventDefault(); }
            this.collection.add([{editing: true}]);
        },
        handleDestroy: function(model, collection, options) {
            collection.remove(model);
        }
    });
    return ListSyllabus;
});
