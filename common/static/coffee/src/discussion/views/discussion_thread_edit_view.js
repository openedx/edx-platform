(function(Backbone) {
    'use strict';
    if (Backbone) {
        this.DiscussionThreadEditView = Backbone.View.extend({
            tagName: 'form',
            events: {
                'submit': 'updateHandler',
                'click .post-cancel': 'cancelHandler'
            },

            attributes: {
                'class': 'discussion-post edit-post-form'
            },

            initialize: function(options) {
                this.container = options.container || $('.thread-content-wrapper');
                this.mode = options.mode || 'inline';
                this.course_settings = options.course_settings;
                this.topicId = options.topicId;
                _.bindAll(this);
                return this;
            },

            render: function() {
                this.template = _.template($('#thread-edit-template').html());
                this.$el.html(this.template(this.model.toJSON())).appendTo(this.container);
                this.submitBtn = this.$('.post-update');
                if (this.isTabMode()) {
                    this.topicView = new DiscussionTopicMenuView({
                        topicId: this.topicId,
                        course_settings: this.course_settings
                    });
                    this.addField(this.topicView.render());
                }
                DiscussionUtil.makeWmdEditor(this.$el, $.proxy(this.$, this), 'edit-post-body');
                return this;
            },

            addField: function(fieldView) {
                this.$('.forum-edit-post-form-wrapper').append(fieldView);
                return this;
            },

            isTabMode: function () {
                return this.mode === 'tab';
            },

            save: function() {
                var title = this.$('.edit-post-title').val(),
                    body = this.$('.edit-post-body textarea').val(),
                    commentableId = this.isTabMode() ? this.topicView.getCurrentTopicId() : null;

                return DiscussionUtil.safeAjax({
                    $elem: this.submitBtn,
                    $loading: this.submitBtn,
                    url: DiscussionUtil.urlFor('update_thread', this.model.id),
                    type: 'POST',
                    dataType: 'json',
                    async: false, // @TODO when the rest of the stuff below is made to work properly..
                    data: {
                        title: title,
                        body: body,
                        commentable_id: commentableId
                    },
                    error: DiscussionUtil.formErrorHandler(this.$('.post-errors')),
                    success: function() {
                        var newAttrs = {
                            title: title,
                            body: body
                        };
                        // @TODO: Move this out of the callback, this makes it feel sluggish
                        this.$('.edit-post-title').val('').attr('prev-text', '');
                        this.$('.edit-post-body textarea').val('').attr('prev-text', '');
                        this.$('.wmd-preview p').html('');
                        if (this.isTabMode()) {
                            _.extend(newAttrs, {
                                commentable_id: commentableId,
                                courseware_title: this.topicView.getFullTopicName()
                            });
                        }
                        this.model.set(newAttrs).unset('abbreviatedBody');
                        this.trigger('thread:updated');
                    }.bind(this)
                });
            },

            updateHandler: function(event) {
                event.preventDefault();
                // this event is for the moment triggered and used nowhere.
                this.trigger('thread:update', event);
                this.save();
                return this;
            },

            cancelHandler: function(event) {
                event.preventDefault();
                this.trigger("thread:cancel_edit", event);
                this.remove();
                return this;
            }
        });
    }
}).call(this, Backbone);
