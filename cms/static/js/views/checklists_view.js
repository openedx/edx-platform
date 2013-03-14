CMS.Views.Checklists = Backbone.View.extend({
    // takes CMS.Models.CourseInfo as model
    tagName: 'div',

    render: function() {
        // instantiate the ClassInfoUpdateView and delegate the proper dom to it
        new CMS.Views.ClassInfoUpdateView({
            el: $('body.updates'),
            collection: this.model.get('updates')
        });

        new CMS.Views.ClassInfoHandoutsView({
            el: this.$('#course-handouts-view'),
            model: this.model.get('handouts')
        });
        return this;
    }
});