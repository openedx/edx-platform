var edx = edx || {};

(function($, _, Backbone, gettext, interpolate_text) {
    'use strict';

    var hiddenClass = 'is-hidden',
        disabledClass = 'is-disabled';

    edx.discussions = edx.discussions || {};

    edx.discussions.DiscussionTopicsView = Backbone.View.extend({
        //events : {
        //    'click .toggle-cohort-management-discussions': 'showDiscussionTopics'
        //},

        initialize: function(options) {
            //var model = this.model;

            this.template = _.template($('#cohort-discussion-topics-tpl').text());
            //this.selectorTemplate = _.template($('#cohort-selector-tpl').text());
            this.context = options.context;

            //model.on('sync', this.onSync, this);
            //
            //// Update cohort counts when the user clicks back on the cohort management tab
            //// (for example, after uploading a csv file of cohort assignments and then
            //// checking results on data download tab).
            //$(this.getSectionCss('cohort_management')).click(function () {
            //    model.fetch();
            //});
        },

        render: function() {
            this.$el.html(this.template({
                coursewideTopics: this.model.get('entries')
            }));
            return this;
        },

        showDiscussionTopics: function(event) {
            event.preventDefault();

            $(event.currentTarget).addClass(hiddenClass);
            var topicsElement = this.$('.discussion-topics').removeClass(hiddenClass);

            this.template('cohort-discussion-topics').render();
            //if (!this.fileUploaderView) {
            //    this.fileUploaderView = new FileUploaderView({
            //        el: uploadElement,
            //        title: gettext("Assign students to cohorts by uploading a CSV file."),
            //        inputLabel: gettext("Choose a .csv file"),
            //        inputTip: gettext("Only properly formatted .csv files will be accepted."),
            //        submitButtonText: gettext("Upload File and Assign Students"),
            //        extensions: ".csv",
            //        url: this.context.uploadCohortsCsvUrl,
            //        successNotification: function (file, event, data) {
            //            var message = interpolate_text(gettext(
            //                "Your file '{file}' has been uploaded. Allow a few minutes for processing."
            //            ), {file: file});
            //            return new NotificationModel({
            //                type: "confirmation",
            //                title: message
            //            });
            //        }
            //    }).render();
            //}
        }

    });
}).call(this, $, _, Backbone, gettext, interpolate_text);
