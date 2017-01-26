// Jasmine Test Suite: Certificate List View

define([ // jshint ignore:line
    'underscore',
    'js/models/course',
    'js/certificates/collections/certificates',
    'js/certificates/models/certificate',
    'js/certificates/views/certificate_details',
    'js/certificates/views/certificate_editor',
    'js/certificates/views/certificate_item',
    'js/certificates/views/certificates_list',
    'js/certificates/views/certificate_preview',
    'common/js/components/views/feedback_notification',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers',
    'js/certificates/spec/custom_matchers'
],
function(_, Course, CertificatesCollection, CertificateModel, CertificateDetailsView, CertificateEditorView,
         CertificateItemView, CertificatesListView, CertificatePreview,  Notification, AjaxHelpers, TemplateHelpers,
         CustomMatchers) {
    'use strict';

    var SELECTORS = {
        itemView: '.certificates-list-item',
        itemEditView: '.certificate-edit',
        noContent: '.no-content',
        newCertificateButton: '.new-button'
    };

    describe('Certificates list view', function() {
        var emptyMessage = 'You have not created any certificates yet.';

        beforeEach(function() {
            TemplateHelpers.installTemplates(
                ['certificate-editor', 'list']
            );

            window.course = new Course({
                id: '5',
                name: 'Course Name',
                url_name: 'course_name',
                org: 'course_org',
                num: 'course_num',
                revision: 'course_rev'
            });
            window.certWebPreview = new CertificatePreview({
                course_modes: ['honor', 'test'],
                certificate_web_view_url: '/users/1/courses/orgX/009/2016'
            });
            window.CMS.User = {isGlobalStaff: true};

            this.model = new CertificateModel({
                course_title: 'Test Course Title Override'
            }, {add: true});

            this.collection = new CertificatesCollection([], {
                certificateUrl: '/certificates/'+ window.course.id
            });
            this.model.set('id', 0);
            this.view = new CertificatesListView({
                collection: this.collection
            });
            appendSetFixtures(this.view.render().el);
            CustomMatchers(); // jshint ignore:line
        });

        afterEach(function() {
            delete window.course;
            delete window.certWebPreview;
            delete window.CMS.User;
        });

        describe('empty template', function () {
            it('should be rendered if no certificates', function() {
                expect(this.view.$(SELECTORS.noContent)).toExist();
                expect(this.view.$(SELECTORS.noContent)).toContainText(emptyMessage);
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

            it('should open in edit mode if model has editing attribute', function() {
                this.model.set({editing: true});
                this.collection.add(this.model);
                expect(this.view.$(SELECTORS.itemEditView)).toExist();
            });

        });
    });
});
