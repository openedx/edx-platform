;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/program_card.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             programCardTpl
         ) {
            return Backbone.View.extend({
                className: 'program-card',
                tpl: _.template(programCardTpl),
                initialize: function() {
                    this.render();
                },
                render: function() {
                    var templated = this.tpl(this.model.toJSON());
                    this.$el.html(templated);
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
