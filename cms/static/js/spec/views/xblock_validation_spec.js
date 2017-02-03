define(['jquery', 'js/models/xblock_validation', 'js/views/xblock_validation', 'common/js/spec_helpers/template_helpers'],
    function($, XBlockValidationModel, XBlockValidationView, TemplateHelpers) {
        beforeEach(function() {
            TemplateHelpers.installTemplate('xblock-validation-messages');
        });

        describe('XBlockValidationView helper methods', function() {
            var model, view;

            beforeEach(function() {
                model = new XBlockValidationModel({parse: true});
                view = new XBlockValidationView({model: model});
                view.render();
            });

            it('has a getIcon method', function() {
                var getIcon = view.getIcon.bind(view);

                expect(getIcon(model.WARNING)).toBe('fa-exclamation-triangle');
                expect(getIcon(model.NOT_CONFIGURED)).toBe('fa-exclamation-triangle');
                expect(getIcon(model.ERROR)).toBe('fa-exclamation-circle');
                expect(getIcon('unknown')).toBeNull();
            });

            it('has a getDisplayName method', function() {
                var getDisplayName = view.getDisplayName.bind(view);

                expect(getDisplayName(model.WARNING)).toBe('Warning');
                expect(getDisplayName(model.NOT_CONFIGURED)).toBe('Warning');
                expect(getDisplayName(model.ERROR)).toBe('Error');
                expect(getDisplayName('unknown')).toBeNull();
            });

            it('can add additional classes', function() {
                var noContainerContent = 'no-container-content', notConfiguredModel, nonRootView, rootView;

                expect(view.getAdditionalClasses()).toBe('');
                expect(view.$('.validation')).not.toHaveClass(noContainerContent);

                notConfiguredModel = new XBlockValidationModel({
                    'empty': false, 'summary': {'text': 'Not configured', 'type': model.NOT_CONFIGURED},
                    'xblock_id': 'id'
                },
                    {parse: true}
                );
                nonRootView = new XBlockValidationView({model: notConfiguredModel});
                nonRootView.render();
                expect(nonRootView.getAdditionalClasses()).toBe('');
                expect(view.$('.validation')).not.toHaveClass(noContainerContent);

                rootView = new XBlockValidationView({model: notConfiguredModel, root: true});
                rootView.render();
                expect(rootView.getAdditionalClasses()).toBe(noContainerContent);
                expect(rootView.$('.validation')).toHaveClass(noContainerContent);
            });
        });

        describe('XBlockValidationView rendering', function() {
            var model, view;

            beforeEach(function() {
                model = new XBlockValidationModel({
                    'empty': false,
                    'summary': {
                        'text': 'Summary message', 'type': 'error',
                        'action_label': 'Summary Action', 'action_class': 'edit-button'
                    },
                    'messages': [
                        {
                            'text': 'First message', 'type': 'warning',
                            'action_label': 'First Message Action', 'action_runtime_event': 'fix-up'
                        },
                         {'text': 'Second message', 'type': 'error'}
                    ],
                    'xblock_id': 'id'
                });
                view = new XBlockValidationView({model: model});
                view.render();
            });

            it('renders summary and detailed messages types', function() {
                var details;

                expect(view.$('.xblock-message')).toHaveClass('has-errors');
                details = view.$('.xblock-message-item');
                expect(details.length).toBe(2);
                expect(details[0]).toHaveClass('warning');
                expect(details[1]).toHaveClass('error');
            });

            it('renders summary and detailed messages text', function() {
                var details;

                expect(view.$('.xblock-message').text()).toContain('Summary message');

                details = view.$('.xblock-message-item');
                expect(details.length).toBe(2);
                expect($(details[0]).text()).toContain('Warning');
                expect($(details[0]).text()).toContain('First message');
                expect($(details[1]).text()).toContain('Error');
                expect($(details[1]).text()).toContain('Second message');
            });

            it('renders action info', function() {
                expect(view.$('a.edit-button .action-button-text').text()).toContain('Summary Action');

                expect(view.$('a.notification-action-button .action-button-text').text()).
                    toContain('First Message Action');
                expect(view.$('a.notification-action-button').data('notification-action')).toBe('fix-up');
            });

            it('renders a summary only', function() {
                var summaryOnlyModel = new XBlockValidationModel({
                        'empty': false,
                        'summary': {'text': 'Summary message', 'type': 'warning'},
                        'xblock_id': 'id'
                    }), summaryOnlyView, details;

                summaryOnlyView = new XBlockValidationView({model: summaryOnlyModel});
                summaryOnlyView.render();

                expect(summaryOnlyView.$('.xblock-message')).toHaveClass('has-warnings');
                expect(view.$('.xblock-message').text()).toContain('Summary message');

                details = summaryOnlyView.$('.xblock-message-item');
                expect(details.length).toBe(0);
            });
        });
    }
);
