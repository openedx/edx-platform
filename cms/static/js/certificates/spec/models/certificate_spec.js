define([
    'backbone', 'coffee/src/main', 'js/certificates/models', 'squire'
], function(
    Backbone, main, CertificateModel, Squire
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

    describe('CertificateModel', function() {
        beforeEach(function() {
            main();
            this.model = new CertificateModel();
        });

        describe('Basic', function() {
            it('should have an empty name by default', function() {
                expect(this.model.get('name')).toEqual('');
            });

            it('should have an empty description by default', function() {
                expect(this.model.get('description')).toEqual('');
            });

            it('should be able to reset itself', function() {
                var originalName = 'Original Name',
                    model = new CertificateModel({name: originalName});
                model.set({name: 'New Name'});
                model.reset();

                expect(model.get('name')).toEqual(originalName);
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
                        'name': 'My Certificate',
                        'description': 'Some description',
                        'version': 2,
                    },
                    clientModelSpec = {
                        'id': 10,
                        'name': 'My Certificate',
                        'description': 'Some description',
                        'version': 2,
                    },
                    model = new CertificateModel(
                        serverModelSpec, { parse: true }
                    );

                expect(deepAttributes(model)).toEqual(clientModelSpec);
                expect(model.toJSON()).toEqual(serverModelSpec);
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new CertificateModel({ name: '' });

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new CertificateModel({ name: 'foo' });

                expect(model.isValid()).toBeTruthy();
            });

        });
    });

});
