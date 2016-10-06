(function(define, undefined) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'common/js/components/views/tabbed_view',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/student_account/views/account_section_view',
        'text!student_account/account_settings.underscore'
    ], function(gettext, $, _, TabbedView, HtmlUtils, AccountSectionView, accountSettingsTemplate) {
        var AccountSettingsView = TabbedView.extend({

            navLink: '.account-nav-link',
            activeTab: 'aboutTabSections',
            accountSettingsTabs: [
                {
                    name: 'aboutTabSections',
                    id: 'about-tab',
                    label: gettext('Account Information'),
                    class: 'active',
                    tabindex: 0,
                    selected: true,
                    expanded: true
                },
                {
                    name: 'accountsTabSections',
                    id: 'accounts-tab',
                    label: gettext('Linked Accounts'),
                    tabindex: -1,
                    selected: false,
                    expanded: false
                },
                {
                    name: 'ordersTabSections',
                    id: 'orders-tab',
                    label: gettext('Order History'),
                    tabindex: -1,
                    selected: false,
                    expanded: false
                }
            ],
            events: {
                'click .account-nav-link': 'switchTab',
                'keydown .account-nav-link': 'keydownHandler'
            },

            initialize: function(options) {
                this.options = options;
                _.bindAll(this, 'render', 'switchTab', 'setActiveTab', 'showLoadingError');
            },

            render: function() {
                var tabName,
                    view = this;
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(accountSettingsTemplate)({
                    accountSettingsTabs: this.accountSettingsTabs
                }));
                _.each(view.accountSettingsTabs, function(tab) {
                    tabName = tab.name;
                    view.renderSection(view.options.tabSections[tabName], tabName, tab.label);
                });
                return this;
            },

            switchTab: function(e) {
                var $currentTab,
                    $accountNavLink = $('.account-nav-link');

                if (e) {
                    e.preventDefault();
                    $currentTab = $(e.target);
                    this.activeTab = $currentTab.data('name');

                    _.each(this.$('.account-settings-tabpanels'), function(tabPanel) {
                        $(tabPanel).addClass('hidden');
                    });

                    $('#' + this.activeTab + '-tabpanel').removeClass('hidden');

                    $accountNavLink.attr('tabindex', -1);
                    $accountNavLink.attr('aria-selected', false);
                    $accountNavLink.attr('aria-expanded', false);

                    $currentTab.attr('tabindex', 0);
                    $currentTab.attr('aria-selected', true);
                    $currentTab.attr('aria-expanded', true);

                    $(this.navLink).removeClass('active');
                    $currentTab.addClass('active');
                }
            },

            setActiveTab: function() {
                this.switchTab();
            },

            renderSection: function(tabSections, tabName, tabLabel) {
                var accountSectionView = new AccountSectionView({
                    tabName: tabName,
                    tabLabel: tabLabel,
                    sections: tabSections,
                    el: '#' + tabName + '-tabpanel'
                });

                accountSectionView.render();
            },

            showLoadingError: function() {
                this.$('.ui-loading-error').removeClass('is-hidden');
            }
        });

        return AccountSettingsView;
    });
}).call(this, define || RequireJS.define);
