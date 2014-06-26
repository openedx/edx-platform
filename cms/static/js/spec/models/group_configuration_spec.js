define([
    'backbone', 'coffee/src/main', 'js/models/group_configuration',
    'js/models/group', 'js/collections/group'
], function(
    Backbone, main, GroupConfigurationModel, GroupModel, GroupCollection
) {
    'use strict';
    beforeEach(function() {
      this.addMatchers({
        toBeInstanceOf: function(expected) {
          return this.actual instanceof expected;
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

            it('should be empty by default', function() {
                var groups = this.model.get('groups');

                expect(groups).toBeInstanceOf(GroupCollection);
                expect(this.model.isEmpty()).toBeTruthy();
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
                      'name': 'My Group Configuration',
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
                      'name': 'My Group Configuration',
                      'description': 'Some description',
                      'showGroups': false,
                      'editing': false,
                      'groups': [
                        {
                          'name': 'Group 1'
                        }, {
                          'name': 'Group 2'
                        }
                      ]
                    },
                    model = new GroupConfigurationModel(serverModelSpec);

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
            this.model = new GroupModel();
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
                var model = new GroupModel({ name: '' });

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new GroupModel({ name: 'a' });

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
            this.collection.add([{}, {}, {}]);

            expect(this.collection.isEmpty()).toBeTruthy();
        });

        it('is not empty if a group is not empty', function() {
            this.collection.add([{}, { name: 'full' }, {} ]);

            expect(this.collection.isEmpty()).toBeFalsy();
        });
    });
});
