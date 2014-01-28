define(["js/views/baseview", "underscore", "jquery", "js/views/edit_syllabus", "js/views/show_syllabus"],
        function(BaseView, _, $, EditSyllabusView, ShowSyllabusView) {
    var ListSyllabuses = BaseView.extend({
        initialize: function() {
            this.emptyTemplate = _.template($("#no-syllabuses-tpl").text());
            this.listenTo(this.collection, 'all', this.render);
            this.listenTo(this.collection, 'destroy', this.handleDestroy);
        },
        tagName: "div",
        className: "syllabuses-list",
        render: function() {
            var syllabuses = this.collection;
            if(syllabuses.length === 0) {
                this.$el.html(this.emptyTemplate());
            }
            else {
                this.$el.empty();
                var that = this;
                syllabuses.each(function(syllabus) {
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
    return ListSyllabuses;
});
