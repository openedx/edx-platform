;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/empty_programs_list.underscore'
        ],
        function (Backbone,
                  $,
                  _,
                  gettext,
                  emptyProgramsListTpl) {
            return Backbone.View.extend({
                initialize: function(data) {
                    this.childView = data.childView;
                    this.context = data.context;
                },

                render: function() {
                    var childList, tpl;

                    if (!this.collection.length) {
                        if (this.context.xseriesUrl) {
                            //Only show the xseries advertising panel if the link is passed in
                            tpl = _.template(emptyProgramsListTpl);
                            this.$el.html(tpl(this.context));
                        }
                    } else {
                        childList = [];
                        this.collection.each(function (program) {
                            var child = new this.childView({model: program});
                            childList.push(child.el);
                        }, this);
                        this.$el.html(childList);
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
