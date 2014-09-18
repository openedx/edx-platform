define([
    'backbone', 'coffee/src/main', 'js/models/group_configuration',
    'js/models/group', 'js/collections/group', 'squire'
], function(
    Backbone, main, GroupConfigurationModel, GroupModel, GroupCollection, Squire
) {
    'use strict';
    beforeEach(function() {
      this.addMatchers({
        toBeInstanceOf: function(expected) {
          return this.actual instanceof expected;
        },
        toBeEmpty: function() {
            return this.actual.length === 0;
        }
      });
    });

    describe('GroupConfigurationModel', function() {
        beforeEach(function() {
            main();
            this.model = new GroupConfigurationModel();
        });

        describe('Basic', function() {
            it('should have an empty name by default', function() {
                expect(this.model.get('name')).toEqual('');
            });

            it('should have an empty description by default', function() {
                expect(this.model.get('description')).toEqual('');
            });

            it('should not show groups by default', function() {
                expect(this.model.get('showGroups')).toBeFalsy();
            });

            it('should have a collection with 2 groups by default', function() {
                var groups = this.model.get('groups');

                expect(groups).toBeInstanceOf(GroupCollection);
                expect(groups.at(0).get('name')).toBe('Group A');
                expect(groups.at(1).get('name')).toBe('Group B');
            });

            it('should have an empty usage by default', function() {
                expect(this.model.get('usage')).toBeEmpty();
            });

            it('should be able to reset itself', function() {
                this.model.set('name', 'foobar');
                this.model.reset();

                expect(this.model.get('name')).toEqual('');
            });

            it('should be dirty after it\'s been changed', function() {
                this.model.set('name', 'foobar');

                expect(this.model.isDirty()).toBeTruthy();
            });

            describe('should not be dirty', function () {
                it('by default', function() {
                    expect(this.model.isDirty()).toBeFalsy();
                });

                it('after calling setOriginalAttributes', function() {
                    this.model.set('name', 'foobar');
                    this.model.setOriginalAttributes();

                    expect(this.model.isDirty()).toBeFalsy();
                });
            });
        });

        describe('Input/Output', function() {
            var deepAttributes = function(obj) {
                if (obj instanceof Backbone.Model) {
                    return deepAttributes(obj.attributes);
                } else if (obj instanceof Backbone.Collection) {
                    return obj.map(deepAttributes);
                } else if (_.isObject(obj)) {
                    var attributes = {};

                    for (var prop in obj) {
                        if (obj.hasOwnProperty(prop)) {
                            attributes[prop] = deepAttributes(obj[prop]);
                        }
                    }
                    return attributes;
                } else {
                    return obj;
                }
            };

            it('should match server model to client model', function() {
                var serverModelSpec = {
                        'id': 10,
                        'name': 'My Group Configuration',
                        'description': 'Some description',
                        'version': 1,
                        'groups': [
                            {
                                'version': 1,
                                'name': 'Group 1'
                            }, {
                                'version': 1,
                                'name': 'Group 2'
                            }
                        ]
                    },
                    clientModelSpec = {
                        'id': 10,
                        'name': 'My Group Configuration',
                        'description': 'Some description',
                        'showGroups': false,
                        'editing': false,
                        'version': 1,
                        'groups': [
                            {
                                'version': 1,
                                'order': 0,
                                'name': 'Group 1'
                            }, {
                                'version': 1,
                                'order': 1,
                                'name': 'Group 2'
                            }
                        ],
                        'usage': []
                    },
                    model = new GroupConfigurationModel(
                        serverModelSpec, { parse: true }
                    );

                expect(deepAttributes(model)).toEqual(clientModelSpec);
                expect(model.toJSON()).toEqual(serverModelSpec);
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new GroupConfigurationModel({ name: '' });

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new GroupConfigurationModel({ name: 'foo' });

                expect(model.isValid()).toBeTruthy();
            });
        });
    });

    describe('GroupModel', function() {
        beforeEach(function() {
            this.collection = new GroupCollection([{}]);
            this.model = this.collection.at(0);
        });

        describe('Basic', function() {
            it('should have an empty name by default', function() {
                expect(this.model.get('name')).toEqual('');
            });

            it('should be empty by default', function() {
                expect(this.model.isEmpty()).toBeTruthy();
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new GroupModel({ name: '' });

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new GroupConfigurationModel({ name: 'foo' });

                expect(model.isValid()).toBeTruthy();
            });

            it('requires at least one group', function() {
                var group1 = new GroupModel({ name: 'Group A' }),
                    model = new GroupConfigurationModel({ name: 'foo' });

                model.get('groups').reset([]);
                expect(model.isValid()).toBeFalsy();

                model.get('groups').add(group1);
                expect(model.isValid()).toBeTruthy();
            });

            it('requires a valid group', function() {
                var group = new GroupModel(),
                    model = new GroupConfigurationModel({ name: 'foo' });

                model.get('groups').reset([group]);

                expect(model.isValid()).toBeFalsy();
            });

            it('requires all groups to be valid', function() {
                var group1 = new GroupModel({ name: 'Group A' }),
                    group2 = new GroupModel(),
                    model = new GroupConfigurationModel({ name: 'foo' });

                model.get('groups').reset([group1, group2]);

                expect(model.isValid()).toBeFalsy();
            });
        });
    });

    describe('GroupCollection', function() {
        beforeEach(function() {
            this.collection = new GroupCollection();
        });

        it('is empty by default', function() {
            expect(this.collection.isEmpty()).toBeTruthy();
        });

        it('is empty if all groups are empty', function() {
            this.collection.add([{ name: '' }, { name: '' }, { name: '' }]);

            expect(this.collection.isEmpty()).toBeTruthy();
        });

        it('is not empty if a group is not empty', function() {
            this.collection.add([
                { name: '' }, { name: 'full' }, { name: '' }
            ]);

            expect(this.collection.isEmpty()).toBeFalsy();
        });

        describe('getGroupId', function () {
            var collection, injector, mockGettext, initializeGroupModel;

            mockGettext = function (returnedValue) {
                var injector = new Squire();

                injector.mock('gettext', function () {
                    return function () { return returnedValue; };
                });

                return injector;
            };

            initializeGroupModel = function (dict, that) {
                runs(function() {
                    injector = mockGettext(dict);
                    injector.require(['js/collections/group'],
                    function(GroupCollection) {
                        collection = new GroupCollection();
                    });
                });

                waitsFor(function() {
                    return collection;
                }, 'GroupModel was not instantiated', 500);

                that.after(function () {
                    collection = null;
                    injector.clean();
                    injector.remove();
                });
            };

            it('returns correct ids', function () {
                var collection = new GroupCollection();

                expect(collection.getGroupId(0)).toBe('A');
                expect(collection.getGroupId(1)).toBe('B');
                expect(collection.getGroupId(25)).toBe('Z');
                expect(collection.getGroupId(702)).toBe('AAA');
                expect(collection.getGroupId(704)).toBe('AAC');
                expect(collection.getGroupId(475253)).toBe('ZZZZ');
                expect(collection.getGroupId(475254)).toBe('AAAAA');
                expect(collection.getGroupId(475279)).toBe('AAAAZ');
            });

            it('just 1 character in the dictionary', function () {
                initializeGroupModel('1', this);
                runs(function() {
                    expect(collection.getGroupId(0)).toBe('1');
                    expect(collection.getGroupId(1)).toBe('11');
                    expect(collection.getGroupId(5)).toBe('111111');
                });
            });

            it('allow to use unicode characters in the dict', function () {
                initializeGroupModel('ö诶úeœ', this);
                runs(function() {
                    expect(collection.getGroupId(0)).toBe('ö');
                    expect(collection.getGroupId(1)).toBe('诶');
                    expect(collection.getGroupId(5)).toBe('öö');
                    expect(collection.getGroupId(29)).toBe('œœ');
                    expect(collection.getGroupId(30)).toBe('ööö');
                    expect(collection.getGroupId(43)).toBe('öúe');
                });
            });

            it('return initial value if dictionary is empty', function () {
                initializeGroupModel('', this);
                runs(function() {
                    expect(collection.getGroupId(0)).toBe('0');
                    expect(collection.getGroupId(5)).toBe('5');
                    expect(collection.getGroupId(30)).toBe('30');
                });
            });
        });
    });
});
