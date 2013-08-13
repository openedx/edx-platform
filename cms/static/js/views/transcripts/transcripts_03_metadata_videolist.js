(function (window, undefined) {
    CMS.Views.Metadata.VideoList = CMS.Views.Metadata.AbstractEditor.extend({

        events : {
            'click .setting-clear' : 'clear',
            'keypress .setting-input' : 'showClearButton',
            'click .collapse-setting' : 'toggleExtraVideosBar'
        },

        templateName: 'metadata-videolist-entry',
        placeholders: {
            'webm': '.webm',
            'mp4': 'http://somesite.com/video.mp4',
            'youtube': 'http://youtube.com/'
        },

        initialize: function () {
            this.messenger = new Transcripts.MessageManager({
                el: this.$el,
                parent: this
            });

            CMS.Views.Metadata.AbstractEditor.prototype.initialize
                .apply(this, arguments);

            this.$el.on(
                'input', 'input',
                _.debounce(_.bind(this.inputHandler, this), 300)
            );

            this.component_id = this.$el.closest('.component').data('id');
        },

        render: function () {
            CMS.Views.Metadata.AbstractEditor.prototype.render
                .apply(this, arguments);

            var self = this,
                utils = Transcripts.Utils,
                component_id =  this.$el.closest('.component').data('id'),
                videoList = this.getVideoObjectsList();

            this.$extraVideosBar = this.$el.find('.videolist-extra-videos');

            utils.command('check', component_id, videoList)
                .done(function (resp) {
                    if (resp.status === 'Success') {
                        var params = resp,
                            len = videoList.length,
                            mode = (len === 1) ? videoList[0].mode : false;

                        if (len > 1 || mode === 'html5') {
                            self.openExtraVideosBar();
                        } else {
                            self.closeExtraVideosBar();
                        }

                        self.messenger.render(resp.command, params);
                        self.checkIsUniqVideoTypes();
                    } else {
                        self.messenger
                            .render('not_found')
                            .showError(
                                'Error: Connection with server failed.',
                                true
                            );
                    }

                    utils.Storage.set('sub', resp.subs);
                })
                .fail(function() {
                    self.messenger
                        .render('not_found')
                        .showError(
                            'Error: Connection with server failed.',
                            true
                        );
                });
        },

        clear: function () {
            CMS.Views.Metadata.AbstractEditor.prototype.clear
                .apply(this, arguments);

            this.$el.find('.input')
                .prop('disabled', false)
                .removeClass('is-disabled');
        },

        getValueFromEditor: function () {
            return _.map(
                this.$el.find('.input'),
                function (ele) {
                    return ele.value.trim();
                }
            ).filter(_.identity);
        },

        getVideoObjectsList: function () {
            var parseLink = Transcripts.Utils.parseLink,
                values = this.getValueFromEditor(),
                arr = [],
                data;

            for (var i = 0, len = values.length; i < len; i += 1) {
                data = parseLink(values[i]);

                if (data.mode !== 'incorrect') {
                    arr.push(data);
                }
            }

            return arr;
        },

        setValueInEditor: function (value) {
            var parseLink = Transcripts.Utils.parseLink,
                list = this.$el.find('.input'),
                val = value.filter(_.identity),
                placeholders = this.getPlaceholders(val);

            for (var i = 0; i < 3; i += 1) {
                list.eq(i)
                    .val(val[i] || null)
                    .attr('placeholder', placeholders[i]);
            }
        },

        getPlaceholders: function (value) {
            var parseLink = Transcripts.Utils.parseLink,
                placeholders = _.clone(this.placeholders),
                result = [],
                linkInfo, label, type;

            for (var i = 0; i < 3; i += 1) {
                linkInfo = parseLink(value[i]);
                type = (linkInfo) ? linkInfo.type : null;

                if (placeholders[type]) {
                    label = placeholders[type];
                    delete placeholders[type];
                } else {
                    placeholders = _.values(placeholders);
                    label = placeholders.pop();
                }

                result.push(label);
            }

            return result;
        },

        openExtraVideosBar: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            this.$extraVideosBar.addClass('is-visible');
        },

        closeExtraVideosBar: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            this.$extraVideosBar.removeClass('is-visible');
        },

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

        inputHandler: function (event) {
            if (event && event.preventDefault) {
                event.preventDefault();
            }

            var $el = $(event.currentTarget),
                $inputs = this.$el.find('.input'),
                entry = $el.val(),
                data = Transcripts.Utils.parseLink(entry),
                isNotEmpty = Boolean(entry);

            if (this.checkValidity(data, isNotEmpty)) {
                var fieldsValue = this.getValueFromEditor(),
                    modelValue = this.model.getValue();

                if (modelValue) {
                    modelValue = modelValue.filter(_.identity);
                }

                // When some correct value (change model) is adjusted,
                // than change to incorrect (no changes to model), than
                // back previous one correct value (that value is already
                // in model). In this case Backbone doesn't trigger 'change'
                // event on model. That's why render method will not be invoked
                // and we should hide error here.
                if (_.isEqual(fieldsValue, modelValue)) {
                    this.messenger.hideError();
                } else {
                    this.updateModel();
                }

                $inputs
                    .prop('disabled', false)
                    .removeClass('is-disabled');

            } else {
                $inputs
                    .not($el)
                    .prop('disabled', true)
                    .addClass('is-disabled');

                if ($el.hasClass('videolist-url')) {
                    this.closeExtraVideosBar();
                }
            }
        },

        isUniqVideoTypes: function (videoList) {
            var arr = _.pluck(videoList, 'type'),
                uniqArr = _.uniq(arr);

            return arr.length === uniqArr.length;
        },

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

        checkValidity: function (data, showErrorModeMessage) {
            var self = this,
                utils = Transcripts.Utils,
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
}(this));
