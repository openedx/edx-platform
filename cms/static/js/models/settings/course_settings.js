if (!CMS.Models['Settings']) CMS.Models.Settings = new Object();
CMS.Models.Settings.CourseSettings = Backbone.Model.extend({
    // a container for the models representing the n possible tabbed states
    defaults: {
        courseLocation: null,
        details: null,
        faculty: null,
        grading: null,
        problems: null,
        discussions: null
    },

    retrieve: function(submodel, callback) {
        if (this.get(submodel)) callback();
        else {
            var cachethis = this;
            switch (submodel) {
            case 'details':
                var details = new CMS.Models.Settings.CourseDetails({location: this.get('courseLocation')});
                details.fetch( {
                    success : function(model) {
                        cachethis.set('details', model);
                        callback(model);
                    }
                });
                break;
            case 'grading':
                var grading = new CMS.Models.Settings.CourseGradingPolicy({course_location: this.get('courseLocation')});
                grading.fetch( {
                    success : function(model) {
                        cachethis.set('grading', model);
                        callback(model);
                    }
                });
                break;

            default:
                break;
            }
        }
    }
})