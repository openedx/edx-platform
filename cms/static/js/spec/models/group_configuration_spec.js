define([
    'backbone', 'js/models/group_configuration',
    'js/collections/group_configuration', 'js/models/group',
    'js/collections/group', 'coffee/src/main'
], function(
    Backbone, GroupConfiguration, GroupConfigurationSet, Group, GroupSet, main
) {
    'use strict';
    beforeEach(function() {
      this.addMatchers({
        toBeInstanceOf: function(expected) {
          return this.actual instanceof expected;
        }
      });
    });

    describe('GroupConfiguration model', function() {
        beforeEach(function() {
            main();
            this.model = new GroupConfiguration();
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

            it('should have a GroupSet with two groups by default', function() {
                var groups = this.model.get('groups');

                expect(groups).toBeInstanceOf(GroupSet);
                expect(groups.length).toEqual(2);
                expect(groups.at(0).isEmpty()).toBeTruthy();
                expect(groups.at(1).isEmpty()).toBeTruthy();
            });

            it('should be empty by default', function() {
                expect(this.model.isEmpty()).toBeTruthy();
            });

            it('should be able to reset itself', function() {
                this.model.set('name', 'foobar');
                this.model.reset();

                expect(this.model.get('name')).toEqual('');
            });

            it('should not be dirty by default', function() {
                expect(this.model.isDirty()).toBeFalsy();
            });

            it('should be dirty after it\'s been changed', function() {
                this.model.set('name', 'foobar');

                expect(this.model.isDirty()).toBeTruthy();
            });

            it('should not be dirty after calling setOriginalAttributes', function() {
                this.model.set('name', 'foobar');
                this.model.setOriginalAttributes();

                expect(this.model.isDirty()).toBeFalsy();
            });
        });

        describe('Input/Output', function() {
            var deepAttributes = function(obj) {
                if (obj instanceof Backbone.Model) {
                    return deepAttributes(obj.attributes);
                } else if (obj instanceof Backbone.Collection) {
                    return obj.map(deepAttributes);
                } else if (_.isArray(obj)) {
                    return _.map(obj, deepAttributes);
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
                      'name': 'My GroupConfiguration',
                      'description': 'Some description',
                      'groups': [
                        {
                          'name': 'Group 1'
                        }, {
                          'name': 'Group 2'
                        }
                      ]
                    },
                    clientModelSpec = {
                      'id': 10,
                      'name': 'My GroupConfiguration',
                      'description': 'Some description',
                      'showGroups': false,
                      'groups': [
                        {
                          'name': 'Group 1'
                        }, {
                          'name': 'Group 2'
                        }
                      ]
                    },
                    model = new GroupConfiguration(serverModelSpec);

                expect(deepAttributes(model)).toEqual(clientModelSpec);
                expect(model.toJSON()).toEqual(serverModelSpec);
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new GroupConfiguration({ name: '' });

                expect(model.isValid()).toBeFalsy();
            });

            it('requires at least one group', function() {
                var model = new GroupConfiguration({ name: 'foo' });
                model.get('groups').reset();

                expect(model.isValid()).toBeFalsy();
            });

            it('requires a valid group', function() {
                var group = new Group(),
                    model = new GroupConfiguration({ name: 'foo' });

                group.isValid = function() { return false; };
                model.get('groups').reset([group]);

                expect(model.isValid()).toBeFalsy();
            });

            it('requires all groups to be valid', function() {
                var group1 = new Group(),
                    group2 = new Group(),
                    model = new GroupConfiguration({ name: 'foo' });

                group1.isValid = function() { return true; };
                group2.isValid = function() { return false; };
                model.get('groups').reset([group1, group2]);

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var group = new Group(),
                    model = new GroupConfiguration({ name: 'foo' });

                group.isValid = function() { return true; };
                model.get('groups').reset([group]);

                expect(model.isValid()).toBeTruthy();
            });
        });
    });

    describe('Group model', function() {
        beforeEach(function() {
            this.model = new Group();
        });

        describe('Basic', function() {
            it('should have a name by default', function() {
                expect(this.model.get('name')).toEqual('');
            });

            it('should be empty by default', function() {
                expect(this.model.isEmpty()).toBeTruthy();
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new Group({ name: '' });

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new Group({ name: 'a' });

                expect(model.isValid()).toBeTruthy();
            });
        });
    });

    describe('Group collection', function() {
        beforeEach(function() {
            this.collection = new GroupSet();
        });

        it('is empty by default', function() {
            expect(this.collection.isEmpty()).toBeTruthy();
        });

        it('is empty if all groups are empty', function() {
            this.collection.add([{}, {}, {}]);

            expect(this.collection.isEmpty()).toBeTruthy();
        });

        it('is not empty if a group is not empty', function() {
            this.collection.add([{}, { name: 'full' }, {} ]);

            expect(this.collection.isEmpty()).toBeFalsy();
        });
    });
});
