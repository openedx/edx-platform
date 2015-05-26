// Jasmine Test Suite: Certificate List View

define([
    'underscore',
    'js/models/course',
    'js/certificates/collections/certificates',
    'js/certificates/models/certificate',
    'js/certificates/views/certificate_details',
    'js/certificates/views/certificate_editor',
    'js/certificates/views/certificate_item',
    'js/certificates/views/certificates_list',
    'js/views/feedback_notification',
    'js/common_helpers/ajax_helpers',
    'js/common_helpers/template_helpers',
    'js/certificates/spec/custom_matchers'
],
function(_, Course, CertificatesCollection, CertificateModel, CertificateDetailsView, CertificateEditorView,
         CertificateItemView, CertificatesListView, Notification, AjaxHelpers, TemplateHelpers, CustomMatchers) {
    'use strict';

    var SELECTORS = {
        itemView: '.certificates-list-item',
        noContent: '.no-content',
        newCertificateButton: '.new-button'

    };

    beforeEach(function() {
        window.course = new Course({
            id: '5',
            name: 'Course Name',
            url_name: 'course_name',
            org: 'course_org',
            num: 'course_num',
            revision: 'course_rev'
        });

    });

    afterEach(function() {
        delete window.course;
    });

    describe('Certificates list view', function() {
        var emptyMessage = 'You have not created any certificates yet.';

        beforeEach(function() {
            TemplateHelpers.installTemplates(
                ['certificate-editor', 'certificate-edit', 'list']
            );

            this.model = new CertificateModel({
                course_title: 'Test Course Title Override'
            }, {add: true});

            this.collection = new CertificatesCollection([], {
                certificateUrl: '/certificates/'+ window.course.id
            });
            this.view = new CertificatesListView({
                collection: this.collection
            });
            appendSetFixtures(this.view.render().el);
            CustomMatchers(this);
        });

        describe('empty template', function () {
            it('should be rendered if no certificates', function() {
                expect(this.view.$(SELECTORS.noContent)).toExist();
                expect(this.view.$(SELECTORS.noContent)).toContainText(emptyMessage);;
                expect(this.view.$(SELECTORS.newCertificateButton)).toExist();
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
            });

            it('should disappear if certificate is added', function() {
                expect(this.view.$el).toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
                this.collection.add(this.model);
                expect(this.view.$el).not.toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).toExist();
            });

            it('should appear if certificate(s) were removed', function() {
                this.collection.add(this.model);
                expect(this.view.$(SELECTORS.itemView)).toExist();
                this.collection.remove(this.model);
                expect(this.view.$el).toContainText(emptyMessage);
                expect(this.view.$(SELECTORS.itemView)).not.toExist();
            });
        });
    });
});
