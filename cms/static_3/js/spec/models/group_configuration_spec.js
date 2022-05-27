define([
    'backbone', 'cms/js/main', 'js/models/group_configuration',
    'js/models/group', 'js/collections/group', 'squire'
], function(Backbone, main, GroupConfigurationModel, GroupModel, GroupCollection, Squire) {
    'use strict';

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
                expect(this.model.get('usage').length).toBe(0);
            });

            it('should be able to reset itself', function() {
                var originalName = 'Original Name',
                    model = new GroupConfigurationModel({name: originalName});
                model.set({name: 'New Name'});
                model.reset();

                expect(model.get('name')).toEqual(originalName);
            });

            it('should be dirty after it\'s been changed', function() {
                this.model.set('name', 'foobar');

                expect(this.model.isDirty()).toBeTruthy();
            });

            describe('should not be dirty', function() {
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
                } else if ($.isPlainObject(obj)) {
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
                        id: 10,
                        name: 'My Group Configuration',
                        description: 'Some description',
                        version: 2,
                        scheme: 'random',
                        groups: [
                            {
                                version: 1,
                                name: 'Group 1',
                                usage: []
                            }, {
                                version: 1,
                                name: 'Group 2',
                                usage: []
                            }
                        ],
                        read_only: true
                    },
                    clientModelSpec = {
                        id: 10,
                        name: 'My Group Configuration',
                        description: 'Some description',
                        scheme: 'random',
                        showGroups: false,
                        editing: false,
                        version: 2,
                        groups: [
                            {
                                version: 1,
                                order: 0,
                                name: 'Group 1',
                                usage: []
                            }, {
                                version: 1,
                                order: 1,
                                name: 'Group 2',
                                usage: []
                            }
                        ],
                        usage: [],
                        read_only: true
                    },
                    model = new GroupConfigurationModel(
                        serverModelSpec, {parse: true}
                    );

                expect(deepAttributes(model)).toEqual(clientModelSpec);
                expect(JSON.parse(JSON.stringify(model))).toEqual(serverModelSpec);
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new GroupConfigurationModel({name: ''});

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                // Note that two groups - Group A and Group B - are
                // created by default.
                var model = new GroupConfigurationModel({name: 'foo'});

                expect(model.isValid()).toBeTruthy();
            });

            it('requires at least one group', function() {
                var group1 = new GroupModel({name: 'Group A'}),
                    model = new GroupConfigurationModel({name: 'foo', groups: []});

                expect(model.isValid()).toBeFalsy();

                model.get('groups').add(group1);
                expect(model.isValid()).toBeTruthy();
            });

            it('requires a valid group', function() {
                var model = new GroupConfigurationModel({name: 'foo', groups: [{name: ''}]});

                expect(model.isValid()).toBeFalsy();
            });

            it('requires all groups to be valid', function() {
                var model = new GroupConfigurationModel({name: 'foo', groups: [{name: 'Group A'}, {name: ''}]});

                expect(model.isValid()).toBeFalsy();
            });

            it('requires all groups to have unique names', function() {
                var model = new GroupConfigurationModel({
                    name: 'foo', groups: [{name: 'Group A'}, {name: 'Group A'}]
                });

                expect(model.isValid()).toBeFalsy();
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
                var model = new GroupModel({name: ''});

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new GroupConfigurationModel({name: 'foo'});

                expect(model.isValid()).toBeTruthy();
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
            this.collection.add([{name: ''}, {name: ''}, {name: ''}]);

            expect(this.collection.isEmpty()).toBeTruthy();
        });

        it('is not empty if a group is not empty', function() {
            this.collection.add([
                {name: ''}, {name: 'full'}, {name: ''}
            ]);

            expect(this.collection.isEmpty()).toBeFalsy();
        });

        describe('getGroupId', function() {
            var collection, injector, mockGettext, initializeGroupModel, cleanUp;

            mockGettext = function(returnedValue) {
                var injector = new Squire();

                injector.mock('gettext', function() {
                    return function() {
                        return returnedValue;
                    };
                });

                return injector;
            };

            initializeGroupModel = function(dict) {
                var deferred = $.Deferred();

                injector = mockGettext(dict);
                injector.require(['js/collections/group'],
                    function(GroupCollection) {
                        collection = new GroupCollection();
                        deferred.resolve(collection);
                    });

                return deferred.promise();
            };

            cleanUp = function() {
                collection = null;
                injector.clean();
                injector.remove();
            };

            it('returns correct ids', function() {
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

            it('just 1 character in the dictionary', function(done) {
                initializeGroupModel('1')
                    .then(function(collection) {
                        expect(collection.getGroupId(0)).toBe('1');
                        expect(collection.getGroupId(1)).toBe('11');
                        expect(collection.getGroupId(5)).toBe('111111');
                    })
                    .always(function() {
                        cleanUp();
                        done();
                    });
            });

            it('allow to use unicode characters in the dict', function(done) {
                initializeGroupModel('ö诶úeœ')
                    .then(function(collection) {
                        expect(collection.getGroupId(0)).toBe('ö');
                        expect(collection.getGroupId(1)).toBe('诶');
                        expect(collection.getGroupId(5)).toBe('öö');
                        expect(collection.getGroupId(29)).toBe('œœ');
                        expect(collection.getGroupId(30)).toBe('ööö');
                        expect(collection.getGroupId(43)).toBe('öúe');
                    })
                    .always(function() {
                        cleanUp();
                        done();
                    });
            });

            it('return initial value if dictionary is empty', function(done) {
                initializeGroupModel('')
                    .then(function(collection) {
                        expect(collection.getGroupId(0)).toBe('0');
                        expect(collection.getGroupId(5)).toBe('5');
                        expect(collection.getGroupId(30)).toBe('30');
                    })
                    .always(function() {
                        cleanUp();
                        done();
                    });
            });
        });
    });
});
