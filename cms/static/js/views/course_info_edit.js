define(['js/views/baseview', 'js/views/course_info_update', 'js/views/course_info_handout'],
    function(BaseView, CourseInfoUpdateView, CourseInfoHandoutView) {
        /*  this view should own everything on the page which has controls effecting its operation
   generate other views for the individual editors.
   The render here adds views for each update/handout by delegating to their collections but does not
   generate any html for the surrounding page.
*/

        var CourseInfoEdit = BaseView.extend({
            // takes CMS.Models.CourseInfo as model
            tagName: 'div',

            render: function() {
                // instantiate the ClassInfoUpdateView and delegate the proper dom to it
                new CourseInfoUpdateView({
                    el: $('body.updates'),
                    collection: this.model.get('updates'),
                    base_asset_url: this.model.get('base_asset_url')
                });

                new CourseInfoHandoutView({
                    el: this.$('#course-handouts-view'),
                    model: this.model.get('handouts'),
                    base_asset_url: this.model.get('base_asset_url')
                });
                return this;
            }
        });
        return CourseInfoEdit;
    }); // end define()
