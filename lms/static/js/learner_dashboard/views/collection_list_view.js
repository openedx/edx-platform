;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/string-utils',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!../../../templates/learner_dashboard/empty_programs_list.underscore'
        ],
        function (Backbone,
                  $,
                  _,
                  gettext,
                  StringUtils,
                  HtmlUtils,
                  emptyProgramsListTpl) {
            return Backbone.View.extend({

                initialize: function(data) {
                    this.childView = data.childView;
                    this.context = data.context;
                    this.titleContext = data.titleContext;
                },

                render: function() {
                    var childList;

                    if (!this.collection.length) {
                        if (this.context.xseriesUrl) {
                            //Only show the xseries advertising panel if the link is passed in
                            HtmlUtils.setHtml(this.$el, HtmlUtils.template(emptyProgramsListTpl)(this.context));
                        }
                    } else {        
                        childList = []; 

                        this.collection.each(function(model) {
                            var child = new this.childView({
                                model: model,
                                context: this.context
                            });
                            childList.push(child.el);
                        }, this);

                        if (this.titleContext){
                            this.$el.before(HtmlUtils.ensureHtml(this.getTitleHtml()).toString());
                        }

                        this.$el.html(childList);
                    }
                },

                getTitleHtml: function(){
                    var titleHtml = HtmlUtils.joinHtml(
                        HtmlUtils.HTML('<'), 
                        this.titleContext.el,
                        HtmlUtils.HTML(' class="sr-only collection-title">'),
                        StringUtils.interpolate(this.titleContext.title),
                        HtmlUtils.HTML('</'),
                        this.titleContext.el,
                        HtmlUtils.HTML('>'));
                    return titleHtml;
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
