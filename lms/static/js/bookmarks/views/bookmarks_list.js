;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'moment'],
        function (gettext, $, _, Backbone) {

        return Backbone.View.extend({

            el: '#courseware-results-list',
            coursewareContentElement: '#course-content',

            errorIcon: '<i class="fa fa-fw fa-exclamation-triangle message-error" aria-hidden="true"></i>',
            loadingIcon: '<i class="fa fa-fw fa-spinner fa-pulse message-in-progress" aria-hidden="true"></i>',

            errorMessage: gettext('An error has occurred. Please try again.'),
            loadingMessage: gettext('Loading'),

            url: '/api/bookmarks/v1/bookmarks',

            events : {
                'click .bookmarks-results-list-item': 'visitBookmark'
            },

            initialize: function (options) {
                this.template = _.template($('#bookmarks_list-tpl').text());
                this.loadingMessageView = options.loadingMessageView;
                this.errorMessageView = options.errorMessageView;
                _.bindAll(this, 'render');
            },

            render: function () {
                var data = {
                    bookmarks: this.collection.models,
                    breadcrumbTrail: this.breadcrumbTrail,
                    userFriendlyDate: this.userFriendlyDate,
                    bookmarkUrl: this.bookmarkUrl
                };
                this.$el.html(this.template(data));
                this.delegateEvents();
                return this;
            },

            loadBookmarks: function () {
                var view = this;

                this.hideErrorMessage();
                this.showBookmarksContainer();
                this.showLoadingMessage();

                this.collection.url = this.url;
                this.collection.fetch({
                    reset: true,
                    data: {course_id: this.getCourseId(), fields: 'path', page: 1, page_size: 65536}
                }).done(function () {
                    view.hideLoadingMessage();
                    view.render();
                    view.focusBookmarksElement();
                }).fail(function () {
                    view.hideLoadingMessage();
                    view.showErrorMessage();
                });
            },

            visitBookmark: function (event) {
                window.location = event.target.pathname;
            },

            getCourseId: function() {
              return this.$el.data('courseId');
            },

            breadcrumbTrail: function (bookmarkPath) {
                var separator = ' <i class="icon fa fa-caret-right" aria-hidden="true"></i><span class="sr">-</span> ';
                return _.pluck(bookmarkPath, 'display_name').join(separator);
            },

            userFriendlyDate: function (isoDate) {
                // What is the correct/right way to set locale?
                moment.locale(window.navigator.userLanguage || window.navigator.language);
                return moment(isoDate).format('LL');
            },

            bookmarkUrl: function (courseId, usageId) {
                return '/courses/' + courseId + '/jump_to/' + usageId
            },

            isVisible: function () {
                return this.$('#my-bookmarks').is(":visible");
            },

            hideBookmarks: function () {
              this.$el.hide();
              $(this.coursewareContentElement).show();
            },

            showBookmarksContainer: function () {
                $(this.coursewareContentElement).hide();
                // Empty el if there anything in it so that we are in clean state.
                this.$el.html('');
                this.$el.show();
            },

            showLoadingMessage: function () {
                this.loadingMessageView.showMessage(this.loadingMessage, this.loadingIcon);
            },

            hideLoadingMessage: function () {
                this.loadingMessageView.hideMessage();
            },

            showErrorMessage: function () {
                this.errorMessageView.showMessage(this.errorMessage, this.errorIcon);
            },

            hideErrorMessage: function () {
                this.errorMessageView.hideMessage();
            },

            focusBookmarksElement: function () {
                this.$('#my-bookmarks').focus();
            }
        });
    });
}).call(this, define || RequireJS.define);
