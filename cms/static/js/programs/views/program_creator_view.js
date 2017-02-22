define([
    'backbone',
    'backbone.validation',
    'jquery',
    'underscore',
    'js/programs/models/organizations_model',
    'js/programs/models/program_model',
    'text!templates/programs/program_creator_form.underscore',
    'edx-ui-toolkit/js/utils/html-utils',
    'gettext',
    'js/programs/utils/validation_config'
],
    function(Backbone, BackboneValidation, $, _, OrganizationsModel, ProgramModel, ListTpl, HtmlUtils) {
        'use strict';

        return Backbone.View.extend({
            parentEl: '.js-program-admin',

            events: {
                'click .js-create-program': 'createProgram',
                'click .js-abort-view': 'abort'
            },

            tpl: HtmlUtils.template(ListTpl),

            initialize: function(options) {
                this.$parentEl = $(this.parentEl);

                this.model = new ProgramModel();
                this.model.on('sync', this.saveSuccess, this);
                this.model.on('error', this.saveError, this);

                // Hook up validation.
                // See: http://thedersen.com/projects/backbone-validation/#validation-binding.
                Backbone.Validation.bind(this);

                this.organizations = new OrganizationsModel();
                this.organizations.on('sync', this.render, this);
                this.organizations.fetch();

                this.router = options.router;
            },

            render: function() {
                HtmlUtils.setHtml(
                    this.$el,
                    this.tpl({
                        orgs: this.organizations.get('results')
                    })
                );

                HtmlUtils.setHtml(this.$parentEl, HtmlUtils.HTML(this.$el));
            },

            abort: function(event) {
                event.preventDefault();
                this.router.goHome();
            },

            createProgram: function(event) {
                var data = this.getData();

                event.preventDefault();
                this.model.set(data);

                // Check if the model is valid before saving. Invalid attributes are looked
                // up by name. The corresponding elements receieve an `invalid` class and a
                // `data-error` attribute. Both are removed when formerly invalid attributes
                // become valid.
                // See: http://thedersen.com/projects/backbone-validation/#isvalid.
                if (this.model.isValid(true)) {
                    this.model.save();
                }
            },

            destroy: function() {
                // Unhook validation.
                // See: http://thedersen.com/projects/backbone-validation/#unbinding.
                Backbone.Validation.unbind(this);

                this.undelegateEvents();
                this.remove();
            },

            getData: function() {
                return {
                    name: this.$el.find('.program-name').val(),
                    subtitle: this.$el.find('.program-subtitle').val(),
                    category: this.$el.find('.program-type').val(),
                    marketing_slug: this.$el.find('.program-marketing-slug').val(),
                    organizations: [{
                        key: this.$el.find('.program-org').val()
                    }]
                };
            },

            goToView: function(uri) {
                Backbone.history.navigate(uri, {trigger: true});
                this.destroy();
            },

            // TODO: add user messaging to show errors
            saveError: function(jqXHR) {
                console.log('saveError: ', jqXHR);
            },

            saveSuccess: function() {
                this.goToView(String(this.model.get('id')));
            }
        });
    }
);
