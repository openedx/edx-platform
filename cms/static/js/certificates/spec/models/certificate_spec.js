define(['js/certificates/models/certificate'],
    function(CertificateModel) {
    'use strict';

    describe('CertificateModel', function() {
        beforeEach(function() {
            this.model = new CertificateModel();
        });

        describe('Basic', function() {
            it('should have name by default', function() {
                expect(this.model.get('name')).toEqual('Default Name');
            });

            it('should have description by default', function() {
                expect(this.model.get('description')).toEqual('Default Description');
            });

            it('should be able to reset itself', function() {
                var originalName = 'Original Name',
                    model = new CertificateModel({name: originalName});
                model.set({name: 'New Name'});
                model.reset();
                expect(model.get('name')).toEqual(originalName);
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
                        'version': 2
                    },
                    clientModelSpec = {
                        'id': 10,
                        'name': 'My Certificate',
                        'description': 'Some description',
                        'version': 2
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
