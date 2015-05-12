;(function (define, undefined) {
'use strict';
define([
    'jquery', 'underscore', 'backbone', 'gettext', 'js/edxnotes/utils/logger',
    'js/edxnotes/collections/notes'
], function ($, _, Backbone, gettext, NotesLogger, NotesCollection) {
    var SearchBoxView = Backbone.View.extend({
        events: {
            'submit': 'submitHandler'
        },

        errorMessage: gettext('An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page.'),
        emptyFieldMessage: (function () {
            var message = gettext('Please enter a term in the %(anchor_start)s search field%(anchor_end)s.');
            return interpolate(message, {
                'anchor_start': '<a href="#search-notes-input">',
                'anchor_end': '</a>'
            }, true);
        } ()),

        initialize: function (options) {
            _.bindAll(this, 'onSuccess', 'onError', 'onComplete');
            this.options = _.defaults(options || {}, {
                beforeSearchStart: function () {},
                search: function () {},
                error: function () {},
                complete: function () {}
            });
            this.logger = NotesLogger.getLogger('search_box', this.options.debug);
            this.$el.removeClass('is-hidden');
            this.isDisabled = false;
            this.logger.log('initialized');
        },

        submitHandler: function (event) {
            event.preventDefault();
            this.search();
        },

        /**
         * Prepares server response to appropriate structure.
         * @param  {Object} data The response form the server.
         * @return {Array}
         */
        prepareData: function (data) {
            var collection;

            if (!(data && _.has(data, 'total') && _.has(data, 'rows'))) {
                this.logger.log('Wrong data', data, this.searchQuery);
                return null;
            }

            collection = new NotesCollection(data.rows);
            return [collection, data.total, this.searchQuery];
        },

        /**
         * Returns search text.
         * @return {String}
         */
        getSearchQuery: function () {
            return this.$el.find('#search-notes-input').val();
        },

        /**
         * Starts search if form is not disabled.
         * @return {Boolean} Indicates if search is started or not.
         */
        search: function () {
            if (this.isDisabled) {
                return false;
            }

            this.searchQuery = this.getSearchQuery();
            if (!this.validateField(this.searchQuery)) {
                return false;
            }

            this.options.beforeSearchStart(this.searchQuery);
            this.disableForm();
            this.sendRequest(this.searchQuery)
                .done(this.onSuccess)
                .fail(this.onError)
                .complete(this.onComplete);

            return true;
        },

        validateField: function (searchQuery) {
            if (!($.trim(searchQuery))) {
                this.options.error(this.emptyFieldMessage, searchQuery);
                return false;
            }
            return true;
        },

        onSuccess: function (data) {
            var args = this.prepareData(data);
            if (args) {
                this.options.search.apply(this, args);
                this.logger.emit('edx.course.student_notes.searched', {
                    'number_of_results': args[1],
                    'search_string': args[2]
                });
            } else {
                this.options.error(this.errorMessage, this.searchQuery);
            }
        },

        onError:function (jXHR) {
            var searchQuery = this.getSearchQuery(),
                message;

            if (jXHR.responseText) {
                try {
                    message = $.parseJSON(jXHR.responseText).error;
                } catch (error) { }
            }

            this.options.error(message || this.errorMessage, searchQuery);
            this.logger.log('Response fails', jXHR.responseText);
        },

        onComplete: function () {
            this.enableForm();
            this.options.complete(this.searchQuery);
        },

        enableForm: function () {
            this.isDisabled = false;
            this.$el.removeClass('is-looking');
            this.$('button[type=submit]').removeClass('is-disabled');
        },

        disableForm: function () {
            this.isDisabled = true;
            this.$el.addClass('is-looking');
            this.$('button[type=submit]').addClass('is-disabled');
        },

        /**
         * Sends a request with appropriate configurations.
         * @param  {String} text Search query.
         * @return {jQuery.Deferred}
         */
        sendRequest: function (text) {
            var settings = {
                url: this.el.action,
                type: this.el.method,
                dataType: 'json',
                data: {text: text}
            };

            this.logger.log(settings);
            return $.ajax(settings);
        }
    });

    return SearchBoxView;
});
}).call(this, define || RequireJS.define);
