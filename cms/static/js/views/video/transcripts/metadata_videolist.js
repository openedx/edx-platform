define(
    [
        "jquery", "backbone", "underscore", "js/views/abstract_editor",
        "js/views/video/transcripts/utils", "js/views/video/transcripts/message_manager",
        "js/views/metadata"
    ],
function($, Backbone, _, AbstractEditor, Utils, MessageManager, MetadataView) {
    var VideoList = AbstractEditor.extend({
        // Time that we wait since the last time user typed.
        inputDelay: 300,

        events : {
            'click .setting-clear' : 'clear',
            'keypress .setting-input' : 'showClearButton',
            'click .collapse-setting' : 'toggleExtraVideosBar'
        },

        templateName: 'metadata-videolist-entry',

        // Pre-defined dict of placeholders: "videoType - placeholder" pairs.
        placeholders: {
            'webm': '.webm',
            'mp4': 'http://somesite.com/video.mp4',
            'youtube': 'http://youtube.com/'
        },

        initialize: function () {
            // Initialize MessageManager that is responsible for
            // status messages and errors.


            var messenger = this.options.MessageManager || MessageManager;
            this.messenger = new messenger({
                el: this.$el,
                parent: this
            });

            // Call it after MessageManager. This is because
            // MessageManager is used in `render` method that
            // is called in `AbstractEditor.prototype.initialize`.
            AbstractEditor.prototype.initialize
                .apply(this, arguments);

            this.$el.on(
                'input', 'input',
                _.debounce(_.bind(this.inputHandler, this), this.inputDelay)
            );

            this.component_locator = this.$el.closest('.component').data('locator');
        },

        render: function () {
            // Call inherited `render` method.
            AbstractEditor.prototype.render
                .apply(this, arguments);

            var self = this,
                component_locator =  this.$el.closest('.component').data('locator'),
                videoList = this.getVideoObjectsList(),

                showServerError = function (response) {
                    var errorMessage = response.status || 'Error: Connection with server failed.';
                    self.messenger
                        .render('not_found')
                        .showError(
                            errorMessage,
                            true // hide buttons
                        );
                };

            this.$extraVideosBar = this.$el.find('.videolist-extra-videos');

            if (videoList.length === 0) {
                this.messenger
                    .render('not_found')
                    .showError(
                        'No sources',
                        true // hide buttons
                    );

                return void(0);
            }

            // Check current state of Timed Transcripts.
            Utils.command('check', component_locator, videoList)
                .done(function (resp) {
                    var params = resp,
                        len = videoList.length,
                        mode = (len === 1) ? videoList[0].mode : false;

                    // If there are more than 1 video or just html5 source is
                    // passed, video sources box should expand
                    if (len > 1 || mode === 'html5') {
                        self.openExtraVideosBar();
                    } else {
                        self.closeExtraVideosBar();
                    }

                    self.messenger.render(resp.command, params);
                    self.checkIsUniqVideoTypes();
                    // Synchronize transcripts field in the `Advanced` tab.
                    Utils.Storage.set('sub', resp.subs);
                })
                .fail(showServerError);
        },

        /**
        * @function
        *
        * Returns the values currently displayed in the editor/view.
        *
        * @returns {array} List of non-empty values.
        *
        */
        getValueFromEditor: function () {
            return _.map(
                this.$el.find('.input'),
                function (ele) {
                    return ele.value.trim();
                }
            ).filter(_.identity);
        },

        /**
        * @function
        *
        * Returns list of objects with information about the values currently
        * displayed in the editor/view.
        *
        * @returns {array} List of objects.
        *
        * @examples
        * this.getValueFromEditor(); // =>
        *     [
        *          'http://youtu.be/OEoXaMPEzfM',
        *          'video_name.mp4',
        *          'video_name.webm'
        *     ]
        *
        * this.getVideoObjectsList(); // =>
        *     [
        *       {mode: `youtube`, type: `youtube`, ...},
        *       {mode: `html5`, type: `mp4`, ...},
        *       {mode: `html5`, type: `webm`, ...}
        *     ]
        *
        */
        getVideoObjectsList: function () {
            var links = this.getValueFromEditor();

            return Utils.getVideoList(links);
        },

        /**
        * @function
        *
        * Sets the values currently displayed in the editor/view.
        *
        * @params {array} value List of values.
        *
        */
        setValueInEditor: function (value) {
            var parseLink = Utils.parseLink,
                list = this.$el.find('.input'),
                val = value.filter(_.identity),
                placeholders = this.getPlaceholders(val);

            list.each(function (index) {
                $(this)
                    .val(val[index] || null)
                    .attr('placeholder', placeholders[index]);
            });
        },


        /**
        * @function
        *
        * Returns the placeholders for the values currently displayed in the
        * editor/view.
        *
        * @returns {array} List of placeholders.
        *
        */
        getPlaceholders: function (value) {
            var parseLink = Utils.parseLink,
                placeholders = _.clone(this.placeholders);

            // Returned list should have the same size as a count of editors/views.
            return _.map(
                this.$el.find('.input'),
                function (element, index) {
                    var linkInfo = parseLink(value[index]),
                        type = (linkInfo) ? linkInfo.type : null,
                        label;

                    // If placeholder for current video type exist, retrieve it
                    // and remove from cloned list.
                    // Otherwise, we use the remaining placeholders.
                    if (placeholders[type]) {
                        label = placeholders[type];
                        delete placeholders[type];
                    } else {
                        if ( !($.isArray(placeholders)) ) {
                            placeholders = _.values(placeholders);
                        }

                        label = placeholders.pop();
                    }

                    return label;
                }
            );
        },

        /**
        * @function
        *
        * Opens video sources box.
        *
        * @params {object} event Event object.
        *
        */
        openExtraVideosBar: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            this.$extraVideosBar.addClass('is-visible');
        },

        /**
        * @function
        *
        * Closes video sources box.
        *
        * @params {object} event Event object.
        *
        */
        closeExtraVideosBar: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            this.$extraVideosBar.removeClass('is-visible');
        },

        /**
        * @function
        *
        * Toggles video sources box.
        *
        * @params {object} event Event object.
        *
        */
        toggleExtraVideosBar: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            if (this.$extraVideosBar.hasClass('is-visible')) {
                this.closeExtraVideosBar.apply(this, arguments);
            } else {
                this.openExtraVideosBar.apply(this, arguments);
            }
        },

        /**
        * @function
        *
        * Handle `input` event.
        *
        * @params {object} event Event object.
        *
        */
        inputHandler: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            var $el = $(event.currentTarget),
                $inputs = this.$el.find('.input'),
                entry = $el.val(),
                data = Utils.parseLink(entry),
                isNotEmpty = Boolean(entry);

            // Empty value should not be validated
            if (this.checkValidity(data, isNotEmpty)) {
                var fieldsValue = this.getValueFromEditor(),
                    modelValue = this.model.getValue();

                if (modelValue) {
                    // Remove empty values
                    modelValue = modelValue.filter(_.identity);
                }

                // When some correct value is adjusted (model is changed),
                // then field changes to incorrect value (no changes to model),
                // then back to previous correct value (that value is already
                // in model). In this case Backbone doesn't trigger 'change'
                // event on model. That's why render method will not be invoked
                // and we should hide error here.
                if (_.isEqual(fieldsValue, modelValue)) {
                    this.messenger.hideError();
                } else {
                    this.updateModel();
                }

                // Enable inputs.
                $inputs
                    .prop('disabled', false)
                    .removeClass('is-disabled');

            } else {
                // If any error occurs, disable all inputs except the current.
                // User cannot change other inputs before putting valid value in
                // the current input.
                $inputs
                    .not($el)
                    .prop('disabled', true)
                    .addClass('is-disabled');

                // If error occurs in the main video input, just close video
                // sources box.
                if ($el.hasClass('videolist-url')) {
                    this.closeExtraVideosBar();
                }
            }
        },

        /**
        * @function
        *
        * Checks the values currently displayed in the editor/view have unique
        * types (mp4 | webm | youtube).
        *
        * @param {object} videoList List of objects with information about the
        *                           values currently displayed in the editor/view
        *
        * @returns {boolean} Boolean value that indicate if video types are unique.
        *
        */
        isUniqVideoTypes: function (videoList) {
            // Extract a list of "type" property values.
            var arr = _.pluck(videoList, 'type'), // => ex: ['youtube', 'mp4', 'mp4']
            // Produces a duplicate-free version of the array.
                uniqArr = _.uniq(arr); // => ex: ['youtube', 'mp4']

            return arr.length === uniqArr.length;
        },

        /**
        * @function
        *
        * Shows error message if the values currently displayed in the
        * editor/view have duplicate types.
        *
        * @param {object} list List of objects with information about the
        *                           values currently displayed in the editor/view
        *
        * @returns {boolean} Boolean value that indicate if video types are unique.
        *
        */
        checkIsUniqVideoTypes: function (list) {
            var videoList = list || this.getVideoObjectsList(),
                isUnique = true;

            if (!this.isUniqVideoTypes(videoList)) {
                this.messenger
                    .showError('Link types should be unique.', true);

                isUnique = false;
            }

            return isUnique;
        },

        /**
        * @function
        *
        * Checks if the values currently displayed in the editor/view have
        * valid values and show error messages.
        *
        * @param {object} data Objects with information about the  value
        *                      currently displayed in the editor/view
        *
        * @param {boolean} showErrorModeMessage Disable mode validation
        *
        * @returns {boolean} Boolean value that indicate if value is valid.
        *
        */
        checkValidity: function (data, showErrorModeMessage) {
            var self = this,
                videoList = this.getVideoObjectsList();

             if (!this.checkIsUniqVideoTypes(videoList)) {
                return false;
             }

            if (data.mode === 'incorrect' && showErrorModeMessage) {
                this.messenger
                    .showError('Incorrect url format.', true);

                return false;
            }

            return true;
        }
    });

    return VideoList;
});
