if (!CMS.Models['Settings']) CMS.Models.Settings = {};

CMS.Models.Settings.Advanced = Backbone.Model.extend({
    defaults: {

    },

    initialize: function() {
        console.log('in initialize');
        var editor = ace.edit('course-advanced-policy-1-value');
        editor.setTheme("ace/theme/monokai");
        editor.getSession().setMode("ace/mode/javascript");
    }
});
