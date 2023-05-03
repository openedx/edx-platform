/* globals _, Backbone, DiscussionTopicMenuView, DiscussionUtil, Thread */
(function() {
    'use strict';
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            for (var key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function ctor() {
                this.constructor = child;
            }

            ctor.prototype = parent.prototype;
            child.prototype = new ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    if (typeof Backbone !== 'undefined' && Backbone !== null) {
        this.NewPostView = (function(_super) {
            __extends(NewPostView, _super);

            function NewPostView() {
                var self = this;
                this.updateStyles = function() {
                    return NewPostView.prototype.updateStyles.apply(self, arguments);
                };
                this.resetForm = function() {
                    return NewPostView.prototype.resetForm.apply(self, arguments);
                };
                return NewPostView.__super__.constructor.apply(this, arguments);
            }

            NewPostView.prototype.initialize = function(options) {
                var _ref;
                this.mode = options.mode || 'inline';
                this.startHeader = options.startHeader;
                if ((_ref = this.mode) !== 'tab' && _ref !== 'inline') {
                    throw new Error('invalid mode: ' + this.mode);
                }
                this.course_settings = options.course_settings;
                this.is_commentable_divided = options.is_commentable_divided;
                this.user_group_id = options.user_group_id;
                this.topicId = options.topicId;
                this.discussionBoardView = options.discussionBoardView;
            };

            NewPostView.prototype.render = function() {
                var context,
                    threadTypeTemplate;
                context = _.clone(this.course_settings.attributes);
                _.extend(context, {
                    group_options: this.getGroupOptions(),
                    is_commentable_divided: this.is_commentable_divided,
                    is_discussion_division_enabled: this.course_settings.get('is_discussion_division_enabled'),
                    mode: this.mode,
                    startHeader: this.startHeader,
                    form_id: this.mode + (this.topicId ? '-' + this.topicId : '')
                });
                edx.HtmlUtils.setHtml(
                    this.$el,
                    edx.HtmlUtils.template($('#new-post-template').html())(context)
                );
                threadTypeTemplate = edx.HtmlUtils.template($('#thread-type-template').html());
                if ($('.js-group-select').prop('disabled')) {
                    $('.group-selector-wrapper').addClass('disabled');
                }
                this.addField(threadTypeTemplate({
                    form_id: _.uniqueId('form-')
                }));
                if (this.isTabMode()) {
                    this.topicView = new DiscussionTopicMenuView({
                        topicId: this.topicId,
                        course_settings: this.course_settings,
                        group_name: this.getGroupName()
                    });
                    this.topicView.on('thread:topic_change', this.toggleGroupDropdown);
                    if (this.course_settings.get('is_discussion_division_enabled')) {
                        this.topicView.on('thread:topic_change', this.updateVisibilityMessage);
                    }
                    this.addField(edx.HtmlUtils.HTML(this.topicView.render()));
                } else {
                    this.group_name = this.getGroupName();
                    this.updateVisibilityMessage(null, this.is_commentable_divided);
                }
                return DiscussionUtil.makeWmdEditor(this.$el, $.proxy(this.$, this), 'js-post-body');
            };

            NewPostView.prototype.addField = function(fieldView) {
                return edx.HtmlUtils.append(
                    this.$('.forum-new-post-form-wrapper'),
                    fieldView
                );
            };

            NewPostView.prototype.isTabMode = function() {
                return this.mode === 'tab';
            };

            NewPostView.prototype.getGroupOptions = function() {
                var userGroupId;
                if (this.course_settings.get('is_discussion_division_enabled') && DiscussionUtil.isPrivilegedUser()) {
                    userGroupId = $('#discussion-container').data('user-group-id');
                    return _.map(this.course_settings.get('groups'), function(group) {
                        return {
                            value: group.id,
                            text: group.name,
                            selected: group.id === userGroupId
                        };
                    });
                } else {
                    return null;
                }
            };

            NewPostView.prototype.getGroupName = function() {
                var userGroupId;
                var group;
                var groupName = null;
                if (this.course_settings.get('is_discussion_division_enabled')) {
                    userGroupId = $('#discussion-container').data('user-group-id');
                    if (!userGroupId) {
                        userGroupId = this.user_group_id;
                    }
                    group = this.course_settings.get('groups').find(function(courseSettingsGroup) {
                        return courseSettingsGroup.id === String(userGroupId);
                    });
                    if (group) {
                        groupName = group.name;
                    }
                }

                return groupName;
            };

            NewPostView.prototype.events = {
                'keypress .forum-new-post-form input:not(.wmd-input)': function(event) {
                    return DiscussionUtil.ignoreEnterKey(event);
                },
                'submit .forum-new-post-form': 'createPost',
                'change .post-option-input': 'postOptionChange',
                'change .js-group-select': 'groupOptionChange',
                'click .cancel': 'cancel',
                'click  .add-post-cancel': 'cancel',
                'reset .forum-new-post-form': 'updateStyles',
                'keydown .wmd-button': function(event) {
                    return DiscussionUtil.handleKeypressInToolbar(event);
                }
            };

            NewPostView.prototype.toggleGroupDropdown = function($target) {
                if ($target.data('divided')) {
                    $('.js-group-select').prop('disabled', false);
                    $('.js-group-select').val('').prop('selected', true);
                    return $('.group-selector-wrapper').removeClass('disabled');
                } else {
                    $('.js-group-select').val('').prop('disabled', true);
                    return $('.group-selector-wrapper').addClass('disabled');
                }
            };

            NewPostView.prototype.updateVisibilityMessage = function($target, forceDivided) {
                var $visEl = $('#wrapper-visibility-message');
                var visTemplate = edx.HtmlUtils.template($('#new-post-visibility-template').html());
                var groupName = null;
                if (($target && $target.data('divided')) || forceDivided) {
                    groupName = this.group_name;
                }

                edx.HtmlUtils.setHtml($visEl, visTemplate({group_name: groupName}));
            };

            NewPostView.prototype.postOptionChange = function(event) {
                var $optionElem, $target;
                $target = $(event.target);
                $optionElem = $target.closest('.post-option');
                if ($target.is(':checked')) {
                    return $optionElem.addClass('is-enabled');
                } else {
                    return $optionElem.removeClass('is-enabled');
                }
            };

            NewPostView.prototype.createPost = function(event) {
                var anonymous, anonymousToPeers, body, follow, group, threadType, title, topicId, url,
                    self = this;
                event.preventDefault();
                threadType = this.$('.input-radio:checked').val();
                title = this.$('.js-post-title').val();
                body = this.$('.js-post-body').find('.wmd-input').val();
                group = this.$('.js-group-select option:selected').attr('value');
                anonymous = false || this.$('input[name=anonymous]').is(':checked');
                anonymousToPeers = false || this.$('input[name=anonymous_to_peers]').is(':checked');
                follow = false || this.$('input[name=follow]').is(':checked');
                topicId = this.isTabMode() ? this.topicView.getCurrentTopicId() : this.topicId;
                url = DiscussionUtil.urlFor('create_thread', topicId);
                return DiscussionUtil.safeAjax({
                    $elem: $(event.target),
                    $loading: event ? $(event.target) : void 0,
                    url: url,
                    type: 'POST',
                    dataType: 'json',
                    data: {
                        thread_type: threadType,
                        title: title,
                        body: body,
                        anonymous: anonymous,
                        anonymous_to_peers: anonymousToPeers,
                        auto_subscribe: follow,
                        group_id: group
                    },
                    error: DiscussionUtil.formErrorHandler(this.$('.post-errors')),
                    success: function(response) {
                        var thread, discussionBreadcrumbsModel;
                        thread = new Thread(response.content);
                        // Update the breadcrumbs and discussion Id(s) related to current topic
                        if (self.discussionBoardView) {
                            discussionBreadcrumbsModel = self.discussionBoardView.breadcrumbs.model;
                            if (discussionBreadcrumbsModel.get('contents').length) {
                                discussionBreadcrumbsModel.set('contents', self.topicView.topicText.split('/'));
                            }
                            self.discussionBoardView.discussionThreadListView.discussionIds =
                                self.topicView.currentTopicId;
                        }
                        self.$el.addClass('is-hidden');
                        self.resetForm();
                        self.trigger('newPost:createPost');
                        return self.collection.add(thread);
                    }
                });
            };

            NewPostView.prototype.formModified = function() {
                var postBodyHasContent = this.$('.js-post-body').find('.wmd-input').val() !== '',
                    titleHasContent = this.$('.js-post-title').val() !== '';
                return postBodyHasContent || titleHasContent;
            };

            NewPostView.prototype.cancel = function(event) {
                event.preventDefault();
                if (this.formModified()) {
                    if (!confirm(gettext('Your post will be discarded.'))) {  // eslint-disable-line no-alert
                        return;
                    }
                }
                this.trigger('newPost:cancel');
                this.resetForm();
            };

            NewPostView.prototype.resetForm = function() {
                var $general;
                this.$('.forum-new-post-form')[0].reset();
                DiscussionUtil.clearFormErrors(this.$('.post-errors'));
                this.$('.wmd-preview').html('');
                if (this.isTabMode()) {
                    $general = this.$('.post-topic option:contains(General)');
                    this.topicView.setTopic($general || this.$('button.topic-title').first());
                }
            };

            NewPostView.prototype.updateStyles = function() {
                var self = this;
                return setTimeout(function() { return self.$('.post-option-input').trigger('change'); }, 1);
            };

            NewPostView.prototype.groupOptionChange = function(event) {
                var $target = $(event.target),
                    data = $target.data();
                this.group_name = this.$('.js-group-select option:selected').text();
                data.divided = true;
                this.updateVisibilityMessage($target);
            };

            return NewPostView;
        }(Backbone.View));
    }
}).call(window);
