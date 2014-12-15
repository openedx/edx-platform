/**
 * View for the requirements (webcam, credit card, etc.)
 */
var edx = edx || {};

(function( $, Backbone, _, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.RequirementsView = Backbone.View.extend({

        template: "#requirements-tpl",

        initialize: function( obj ) {
            this.requirements = obj.requirements || {};
        },

        render: function() {
            var renderedHtml = _.template(
                $( this.template ).html(),
                { requirements: this.requirements }
            );
            $( this.el ).html( renderedHtml );
        }

    });

})( jQuery, Backbone, _, gettext );
