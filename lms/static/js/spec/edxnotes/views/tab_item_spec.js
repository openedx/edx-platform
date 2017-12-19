define([
    'jquery', 'common/js/spec_helpers/template_helpers', 'js/edxnotes/collections/tabs',
    'js/edxnotes/views/tabs_list'
], function($, TemplateHelpers, TabsCollection, TabsListView) {
    'use strict';
    describe('EdxNotes TabItemView', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplate('templates/edxnotes/tab-item');
            this.collection = new TabsCollection([
                {identifier: 'first-item'},
                {
                    identifier: 'second-item',
                    is_closable: true,
                    icon: 'icon-class'
                }
            ]);
            this.tabsList = new TabsListView({
                collection: this.collection
            }).render();
        });

        it('can contain an icon', function() {
            var firstItem = this.tabsList.$('#first-item'),
                secondItem = this.tabsList.$('#second-item');

            expect(firstItem.find('.icon')).not.toExist();
            expect(secondItem.find('.icon')).toHaveClass('icon-class');
        });

        it('can navigate between tabs', function() {
            var firstItem = this.tabsList.$('#first-item'),
                secondItem = this.tabsList.$('#second-item');

            expect(firstItem).toHaveClass('is-active'); // first tab is active
            expect(firstItem).toContainText('Current tab');
            expect(secondItem).not.toHaveClass('is-active'); // second tab is not active
            expect(secondItem).not.toContainText('Current tab');
            secondItem.click();
            expect(firstItem).not.toHaveClass('is-active'); // first tab is not active
            expect(firstItem).not.toContainText('Current tab');
            expect(secondItem).toHaveClass('is-active'); // second tab is active
            expect(secondItem).toContainText('Current tab');
        });

        it('can close the tab', function() {
            var secondItem = this.tabsList.$('#second-item');

            expect(this.tabsList.$('.tab')).toHaveLength(2);
            secondItem.find('.action-close').click();
            expect(this.tabsList.$('.tab')).toHaveLength(1);
        });
    });
});
