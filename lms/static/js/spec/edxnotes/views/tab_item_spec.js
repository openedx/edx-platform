define([
    'jquery', 'js/common_helpers/template_helpers', 'js/edxnotes/collections/tabs',
    'js/edxnotes/views/tabs_list', 'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function($, TemplateHelpers, TabsCollection, TabsListView, customMatchers) {
    'use strict';
    describe('EdxNotes TabItemView', function() {
        beforeEach(function () {
            customMatchers(this);
            TemplateHelpers.installTemplate('templates/edxnotes/tab-item');
            this.collection = new TabsCollection([
                {'class_name': 'first-item'},
                {
                    'class_name': 'second-item',
                    'is_closable': true
                }
            ]);
            this.tabsList = new TabsListView({
                collection: this.collection
            }).render();
        });

        it('can navigate between tabs', function () {
            var firstItem = this.tabsList.$('.first-item'),
                secondItem = this.tabsList.$('.second-item');

            expect(firstItem).toHaveClass('is-active'); // first tab is active
            expect(secondItem).not.toHaveClass('is-active'); // second tab is not active
            secondItem.click();
            expect(firstItem).not.toHaveClass('is-active'); // first tab is not active
            expect(secondItem).toHaveClass('is-active'); // second tab is active
        });

        it('can close the tab', function () {
            var secondItem = this.tabsList.$('.second-item');

            expect(this.tabsList.$('.tab-item')).toHaveLength(2);
            secondItem.find('.btn-close').click();
            expect(this.tabsList.$('.tab-item')).toHaveLength(1);
        });
    });
});
