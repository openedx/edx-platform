define(['jquery', 'backbone', 'underscore', 'common/js/components/views/list'],
    function($, Backbone, _, ListView) {
        'use strict';
        describe('ListView', function() {
            var Model = Backbone.Model.extend({
                    defaults: {
                        name: 'default name'
                    }
                }),
                View = Backbone.View.extend({
                    tagName: 'div',
                    className: 'my-view',
                    template: _.template('<p>Name: "<%- name %>"</p>'),
                    render: function() {
                        this.$el.html(this.template(this.model.attributes));
                        return this;
                    }
                }),
                Collection = Backbone.Collection.extend({
                    model: Model
                }),
                expectListNames = function(names) {
                    expect(listView.$('.my-view').length).toBe(names.length);
                    _.each(names, function(name, index) {
                        expect($(listView.$('.my-view')[index]).text()).toContain(name);
                    });
                },
                listView;

            beforeEach(function() {
                setFixtures('<div class="list"></div>');
                listView = new ListView({
                    el: $('.list'),
                    collection: new Collection(
                        [{name: 'first model'}, {name: 'second model'}, {name: 'third model'}]
                    ),
                    itemViewClass: View
                });
                listView.render();
            });

            it('renders itself', function() {
                expectListNames(['first model', 'second model', 'third model']);
            });

            it('does not render subviews for an empty collection', function() {
                listView.collection.set([]);
                expectListNames([]);
            });

            it('re-renders itself when the collection changes', function() {
                expectListNames(['first model', 'second model', 'third model']);
                listView.collection.set([{name: 'foo'}, {name: 'bar'}, {name: 'third model'}]);
                expectListNames(['foo', 'bar', 'third model']);
                listView.collection.reset([{name: 'baz'}, {name: 'bar'}, {name: 'quux'}]);
                expectListNames(['baz', 'bar', 'quux']);
            });

            it('re-renders itself when items are added to the collection', function() {
                expectListNames(['first model', 'second model', 'third model']);
                listView.collection.add({name: 'fourth model'});
                expectListNames(['first model', 'second model', 'third model', 'fourth model']);
                listView.collection.add({name: 'zeroth model'}, {at: 0});
                expectListNames(['zeroth model', 'first model', 'second model', 'third model', 'fourth model']);
                listView.collection.add({name: 'second-and-a-half model'}, {at: 3});
                expectListNames([
                    'zeroth model', 'first model', 'second model',
                    'second-and-a-half model', 'third model', 'fourth model'
                ]);
            });

            it('re-renders itself when items are removed from the collection', function() {
                listView.collection.reset([{name: 'one'}, {name: 'two'}, {name: 'three'}, {name: 'four'}]);
                expectListNames(['one', 'two', 'three', 'four']);
                listView.collection.remove(listView.collection.at(0));
                expectListNames(['two', 'three', 'four']);
                listView.collection.remove(listView.collection.at(1));
                expectListNames(['two', 'four']);
                listView.collection.remove(listView.collection.at(1));
                expectListNames(['two']);
                listView.collection.remove(listView.collection.at(0));
                expectListNames([]);
            });

            it('removes old views', function() {
                listView.collection.reset(null);
                expect(listView.itemViews).toEqual([]);
            });
        });
    });
