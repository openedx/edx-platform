define(['js/views/license', 'js/models/license', 'common/js/spec_helpers/template_helpers'],
    function(LicenseView, LicenseModel, TemplateHelpers) {
        describe('License view', function() {
            beforeEach(function() {
                TemplateHelpers.installTemplate('license-selector', true);
                this.model = new LicenseModel();
                this.view = new LicenseView({model: this.model});
            });

            it('renders with no license', function() {
                this.view.render();
                expect(this.view.$('li[data-license=all-rights-reserved] button'))
                    .toHaveText('All Rights Reserved');
                expect(this.view.$('li[data-license=all-rights-reserved] button'))
                    .not.toHaveClass('is-selected');
                expect(this.view.$('li[data-license=creative-commons] button'))
                    .toHaveText('Creative Commons');
                expect(this.view.$('li[data-license=creative-commons] button'))
                    .not.toHaveClass('is-selected');
            });

            it('renders with the right license selected', function() {
                this.model.set('type', 'all-rights-reserved');
                expect(this.view.$('li[data-license=all-rights-reserved] button'))
                    .toHaveClass('is-selected');
                expect(this.view.$('li[data-license=creative-commons] button'))
                    .not.toHaveClass('is-selected');
            });

            it('switches license type on click', function() {
                var arrBtn = this.view.$('li[data-license=all-rights-reserved] button');
                expect(this.model.get('type')).toBeNull();
                arrBtn.click();
                expect(this.model.get('type')).toEqual('all-rights-reserved');
                // view has re-rendered, so get a new reference to the button
                arrBtn = this.view.$('li[data-license=all-rights-reserved] button');
                expect(arrBtn).toHaveClass('is-selected');
                // now switch to creative commons
                var ccBtn = this.view.$('li[data-license=creative-commons] button');
                ccBtn.click();
                expect(this.model.get('type')).toEqual('creative-commons');
                // update references again
                arrBtn = this.view.$('li[data-license=all-rights-reserved] button');
                ccBtn = this.view.$('li[data-license=creative-commons] button');
                expect(arrBtn).not.toHaveClass('is-selected');
                expect(ccBtn).toHaveClass('is-selected');
            });

            it('sets default license options when switching license types', function() {
                expect(this.model.get('options')).toEqual({});
                var ccBtn = this.view.$('li[data-license=creative-commons] button');
                ccBtn.click();
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: true, SA: false}
                );
                var arrBtn = this.view.$('li[data-license=all-rights-reserved] button');
                arrBtn.click();
                expect(this.model.get('options')).toEqual({});
            });

            it('renders license options', function() {
                this.model.set({type: 'creative-commons'});
                expect(this.view.$('ul.license-options li[data-option=BY]'))
                    .toContainText('Attribution');
                expect(this.view.$('ul.license-options li[data-option=NC]'))
                    .toContainText('Noncommercial');
                expect(this.view.$('ul.license-options li[data-option=ND]'))
                    .toContainText('No Derivatives');
                expect(this.view.$('ul.license-options li[data-option=SA]'))
                    .toContainText('Share Alike');
                expect(this.view.$('ul.license-options li').length).toEqual(4);
            });

            it('toggles boolean options on click', function() {
                this.view.$('li[data-license=creative-commons] button').click();
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: true, SA: false}
                );
                // toggle NC option
                this.view.$('li[data-option=NC]').click();
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: false, ND: true, SA: false}
                );
            });

            it("doesn't toggle disabled options", function() {
                this.view.$('li[data-license=creative-commons] button').click();
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: true, SA: false}
                );
                var BY = this.view.$('li[data-option=BY]');
                expect(BY).toHaveClass('is-disabled');
                // try to toggle BY option
                BY.click();
                // no change
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: true, SA: false}
                );
            });

            it("doesn't allow simultaneous conflicting options", function() {
                this.view.$('li[data-license=creative-commons] button').click();
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: true, SA: false}
                );
                // SA and ND conflict
                var SA = this.view.$('li[data-option=SA]');
                // try to turn on SA option
                SA.click();
                // ND should no longer be selected
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: false, SA: true}
                );

                // try to turn on ND option
                ND = this.view.$('li[data-option=ND]');
                ND.click();
                expect(this.model.get('options')).toEqual(
                    {ver: '4.0', BY: true, NC: true, ND: true, SA: false}
                );
            });

            it('has no preview by default', function() {
                this.view.render();
                expect(this.view.$('.license-preview').length).toEqual(0);
                this.view.$('li[data-license=creative-commons] button').click();
                expect(this.view.$('.license-preview').length).toEqual(0);
            });

            it('displays a preview if showPreview is true', function() {
                this.view = new LicenseView({model: this.model, showPreview: true});
                this.view.render();
                expect(this.view.$('.license-preview').length).toEqual(1);
	    // Expect default text to be "All Rights Reserved"
                expect(this.view.$('.license-preview')).toContainText('All Rights Reserved');
                this.view.$('li[data-license=creative-commons] button').click();
                expect(this.view.$('.license-preview').length).toEqual(1);
                expect(this.view.$('.license-preview')).toContainText('Some Rights Reserved');
            });
        });
    });
