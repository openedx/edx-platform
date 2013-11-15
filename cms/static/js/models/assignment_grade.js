define(["backbone", "underscore"], function(Backbone, _) {
    var AssignmentGrade = Backbone.Model.extend({
        defaults : {
            graderType : null, // the type label (string). May be "Not Graded" which implies None. 
            locator : null // locator for the block
        },
        urlRoot : function() {
            // return locator.url_reverse('xblock', 'gradeas') + '/' + graderType
            if (this.has('locator')) {
                return '/' + this.get('locator') + '/gradeas/' + this.get('graderType');
            }
            else return "";
        }
    });
    return AssignmentGrade;
});
