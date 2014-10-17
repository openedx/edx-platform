(function(Backbone) {
    'use strict';
    if (Backbone) {
        this.DiscussionTopicMenuView = Backbone.View.extend({
            events: {
                'click .post-topic-button': 'toggleTopicDropdown',
                'click .topic-menu-wrapper': 'handleTopicEvent',
                'click .topic-filter-label': 'ignoreClick',
                'keyup .topic-filter-input': this.DiscussionFilter.filterDrop
            },

            attributes: {
                'class': 'post-field'
            },

            initialize: function(options) {
                this.course_settings = options.course_settings;
                this.currentTopicId = options.topicId;
                this.maxNameWidth = 100;
                _.bindAll(this);
                return this;
            },

            /**
             * When the menu is expanded, a click on the body element (outside of the menu) or on a menu element
             * should close the menu except when the target is the search field. To accomplish this, we have to ignore
             * clicks on the search field by stopping the propagation of the event.
             */
            ignoreClick: function(event) {
                event.stopPropagation();
                return this;
            },

            render: function() {
                var context = _.clone(this.course_settings.attributes);
                context.topics_html = this.renderCategoryMap(this.course_settings.get('category_map'));
                this.$el.html(_.template($('#topic-template').html(), context));
                this.dropdownButton = this.$('.post-topic-button');
                this.topicMenu = this.$('.topic-menu-wrapper');
                this.selectedTopic = this.$('.js-selected-topic');
                this.hideTopicDropdown();
                if (this.getCurrentTopicId()) {
                    this.setTopic(this.$('a.topic-title').filter('[data-discussion-id="' + this.getCurrentTopicId() + '"]'));
                } else {
                    this.setTopic(this.$('a.topic-title').first());
                }
                return this.$el;
            },

            renderCategoryMap: function(map) {
                var category_template = _.template($('#new-post-menu-category-template').html()),
                    entry_template = _.template($('#new-post-menu-entry-template').html());

                return _.map(map.children, function(name) {
                    var html = '', entry;
                    if (_.has(map.entries, name)) {
                        entry = map.entries[name];
                        html = entry_template({
                            text: name,
                            id: entry.id,
                            is_cohorted: entry.is_cohorted
                        });
                    } else { // subcategory
                        html = category_template({
                            text: name,
                            entries: this.renderCategoryMap(map.subcategories[name])
                        });
                    }
                    return html;
                }, this).join('');
            },

            toggleTopicDropdown: function(event) {
                event.preventDefault();
                event.stopPropagation();
                if (this.menuOpen) {
                    this.hideTopicDropdown();
                } else {
                    this.showTopicDropdown();
                }
                return this;
            },

            showTopicDropdown: function() {
                this.menuOpen = true;
                this.dropdownButton.addClass('dropped');
                this.topicMenu.show();
                $(document.body).on('click.topicMenu', this.hideTopicDropdown);
                // Set here because 1) the window might get resized and things could
                // change and 2) can't set in initialize because the button is hidden
                this.maxNameWidth = this.dropdownButton.width() - 40;
                return this;
            },

            hideTopicDropdown: function() {
                this.menuOpen = false;
                this.dropdownButton.removeClass('dropped');
                this.topicMenu.hide();
                $(document.body).off('click.topicMenu');
                return this;
            },

            handleTopicEvent: function(event) {
                event.preventDefault();
                event.stopPropagation();
                this.setTopic($(event.target));
                return this;
            },

            setTopic: function($target) {
                if ($target.data('discussion-id')) {
                    this.topicText = this.getFullTopicName($target);
                    this.currentTopicId = $target.data('discussion-id');
                    this.setSelectedTopicName(this.topicText);
                    this.trigger('thread:topic_change', $target);
                    this.hideTopicDropdown();
                }
                return this;
            },

            getCurrentTopicId: function() {
                return this.currentTopicId;
            },

            setSelectedTopicName: function(text) {
                return this.selectedTopic.html(this.fitName(text));
            },
            /**
             * Return full name for the `topicElement` if it is passed.
             * Otherwise, full name for the current topic will be returned.
             * @param {jQuery Element} [topicElement]
             * @return {String}
             */
            getFullTopicName: function(topicElement) {
                var name;
                if (topicElement) {
                    name = topicElement.html();
                    _.each(topicElement.parents('.topic-submenu'), function(item) {
                        name = $(item).siblings('.topic-title').text() + ' / ' + name;
                    });
                    return name;
                } else {
                    return this.topicText;
                }
            },

            // @TODO move into utils.coffee
            getNameWidth: function(name) {
                var test = $('<div>'),
                    width;

                test.css({
                    'font-size': this.dropdownButton.css('font-size'),
                    'opacity': 0,
                    'position': 'absolute',
                    'left': -1000,
                    'top': -1000
                }).html(name).appendTo(document.body);
                width = test.width();
                test.remove();
                return width;
            },

            // @TODO move into utils.coffee
            fitName: function(name) {
                var ellipsisText = gettext('…'),
                    partialName, path, rawName;

                if (this.getNameWidth(name) < this.maxNameWidth) {
                    return name;
                } else {
                    path = _.map(name.split('/'), function(item){
                        return item.replace(/^\s+|\s+$/g, '');
                    });
                    while (path.length > 1) {
                        path.shift();
                        partialName = ellipsisText + ' / ' + path.join(' / ');
                        if (this.getNameWidth(partialName) < this.maxNameWidth) {
                          return partialName;
                        }
                    }
                    rawName = path[0];
                    name = ellipsisText + ' / ' + rawName;
                    while (this.getNameWidth(name) > this.maxNameWidth) {
                      rawName = rawName.slice(0, -1);
                      name = ellipsisText + ' / ' + rawName + ' ' + ellipsisText;
                    }
                }
                return name;
            }
        });
    }
}).call(this, Backbone);
