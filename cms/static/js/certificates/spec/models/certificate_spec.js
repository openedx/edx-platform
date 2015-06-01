// Jasmine Test Suite: Certifiate Model

define([ // jshint ignore:line
    'js/certificates/models/certificate',
    'js/certificates/collections/certificates'
],
function(CertificateModel, CertificateCollection) {
    'use strict';

    describe('CertificateModel', function() {
        beforeEach(function() {
            this.newModelOptions = {add: true};
            this.model = new CertificateModel({editing: true}, this.newModelOptions);
            this.collection = new CertificateCollection([ this.model ], {certificateUrl: '/outline'});
        });

        describe('Basic', function() {
            it('certificate should have name by default', function() {
                expect(this.model.get('name')).toEqual('Name of the certificate');
            });

            it('certificate should have description by default', function() {
                expect(this.model.get('description')).toEqual('Description of the certificate');
            });

            it('certificate should be able to reset itself', function() {
                var originalName = 'Original Name',
                    model = new CertificateModel({name: originalName}, this.newModelOptions);
                model.set({name: 'New Name'});
                model.reset();
                expect(model.get('name')).toEqual(originalName);
            });

            it('certificate should have signatories in its relations', function() {
                var relation = this.model.getRelations()[0];
                expect(relation.key).toEqual('signatories');
            });
        });

        describe('Validation', function() {
            it('requires a name', function() {
                var model = new CertificateModel({ name: '' }, this.newModelOptions);

                expect(model.isValid()).toBeFalsy();
            });

            it('can pass validation', function() {
                var model = new CertificateModel({ name: 'foo' }, this.newModelOptions);

                expect(model.isValid()).toBeTruthy();
            });

        });
    });

});
