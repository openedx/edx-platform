define(["backbone", "underscore", "js/models/location"], function(Backbone, _, Location) {
    var AssignmentGrade = Backbone.Model.extend({
        defaults : {
            graderType : null, // the type label (string). May be "Not Graded" which implies None. I'd like to use id but that's ephemeral
            location : null // A location object
        },
        initialize : function(attrs) {
            if (attrs['assignmentUrl']) {
                this.set('location', new Location(attrs['assignmentUrl'], {parse: true}));
            }
        },
        parse : function(attrs) {
            if (attrs && attrs['location']) {
                attrs.location = new Location(attrs['location'], {parse: true});
            }
        },
        urlRoot : function() {
            if (this.has('location')) {
                var location = this.get('location');
                return '/' + location.get('org') + "/" + location.get('course') + '/' + location.get('category') + '/'
                + location.get('name') + '/gradeas/';
            }
            else return "";
        }
    });
    return AssignmentGrade;
});
