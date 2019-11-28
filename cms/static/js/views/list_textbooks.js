define(['js/views/baseview', 'jquery', 'js/views/edit_textbook', 'js/views/show_textbook', 'common/js/components/utils/view_utils'],
        function(BaseView, $, EditTextbookView, ShowTextbookView, ViewUtils) {
            var ListTextbooks = BaseView.extend({
                initialize: function() {
                    this.emptyTemplate = this.loadTemplate('no-textbooks');
                    this.listenTo(this.collection, 'change:editing', this.render);
                    this.listenTo(this.collection, 'destroy', this.handleDestroy);
                },
                tagName: 'div',
                className: 'textbooks-list',
                render: function() {
                    var textbooks = this.collection;
                    if (textbooks.length === 0) {
                        this.$el.html(this.emptyTemplate()); // xss-lint: disable=javascript-jquery-html
                    } else {
                        this.$el.empty();
                        var that = this;
                        textbooks.each(function(textbook) {
                            var view;
                            if (textbook.get('editing')) {
                                view = new EditTextbookView({model: textbook});
                            } else {
                                view = new ShowTextbookView({model: textbook});
                            }
                            that.$el.append(view.render().el);
                        });
                    }
                    return this;
                },
                events: {
                    'click .new-button': 'addOne'
                },
                addOne: function(e) {
                    var $sectionEl, $inputEl;
                    if (e && e.preventDefault) { e.preventDefault(); }
                    this.collection.add([{editing: true}]); // (render() call triggered here)
                    this.render();
            // find the outer 'section' tag for the newly added textbook
                    $sectionEl = this.$el.find('section:last');
            // scroll to put this at top of viewport
                    ViewUtils.setScrollOffset($sectionEl, 0);
            // find the first input element in this section
                    $inputEl = $sectionEl.find('input:first');
            // activate the text box (so user can go ahead and start typing straight away)
                    $inputEl.focus().select();
                },
                handleDestroy: function(model, collection, options) {
                    collection.remove(model);
                }
            });
            return ListTextbooks;
        });
