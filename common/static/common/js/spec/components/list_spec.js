define(['jquery', 'backbone', 'underscore', 'common/js/components/views/list'], function ($, Backbone, _, ListView) {
    describe('ListView', function () {
        var Model = Backbone.Model.extend({
                defaults: {
                    name: 'default name'
                }
            }),
            View = Backbone.View.extend({
                tagName: 'div',
                className: 'my-view',
                template: _.template('<p>Name: "<%- name %>"</p>'),
                render: function () {
                    this.$el.html(this.template(this.model.attributes));
                    return this;
                }
            }),
            Collection = Backbone.Collection.extend({
                model: Model
            }),
            expectListNames,
            listView;

        expectListNames = function (names) {
            expect(listView.$('.my-view').length).toBe(names.length);
            _.each(names, function (name, index) {
                expect($(listView.$('.my-view')[index]).text()).toContain(name);
            });
        };

        beforeEach(function () {
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

        it('renders itself', function () {
            expect(listView.$('.my-view').length).toBe(3);
            expect($(listView.$('.my-view')[0]).text()).toContain('first model');
            expect($(listView.$('.my-view')[1]).text()).toContain('second model');
            expect($(listView.$('.my-view')[2]).text()).toContain('third model');
        });

        it('re-renders itself when the collection changes', function () {
            var model = new Model({name: 'fourth model'});
            expectListNames(['first model', 'second model', 'third model']);
            listView.collection.add([model]);
            expectListNames(['first model', 'second model', 'third model', 'fourth model']);
            listView.collection.remove(model);
            expectListNames(['first model', 'second model', 'third model']);
            listView.collection.set([{name: 'foo'}, {name: 'bar'}, {name: 'third model'}]);
            expectListNames(['foo', 'bar', 'third model']);
            listView.collection.reset([{name: 'baz'}, {name: 'bar'}, {name: 'quux'}]);
            expectListNames(['baz', 'bar', 'quux']);
        });

        it('removes old views', function () {
            listView.collection.reset(null);
            expect(listView.itemViews).toEqual([]);
        });
    });
});
