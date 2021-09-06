(function(define, undefined) {
    'use strict';
    define([
        'gettext',
        'jquery',
        'underscore',
        'common/js/components/views/tabbed_view',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/student_account/views/account_section_view',
        'text!templates/student_account/account_settings.underscore'
    ], function(gettext, $, _, TabbedView, HtmlUtils, AccountSectionView, accountSettingsTemplate) {
        var AccountSettingsView = TabbedView.extend({

            navLink: '.account-nav-link',
            activeTab: 'aboutTabSections',
            events: {
                'click .account-nav-link': 'switchTab',
                'keydown .account-nav-link': 'keydownHandler',
                'click .btn-alert-primary': 'revertValue'
            },

            initialize: function(options) {
                this.options = options;
                _.bindAll(this, 'render', 'switchTab', 'setActiveTab', 'showLoadingError');
            },

            render: function() {
                var tabName, betaLangMessage, helpTranslateText, helpTranslateLink, betaLangCode, oldLangCode,
                    view = this;
                var accountSettingsTabs = [
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
                    }
                ];
                if (!view.options.disableOrderHistoryTab) {
                    accountSettingsTabs.push({
                        name: 'ordersTabSections',
                        id: 'orders-tab',
                        label: gettext('Order History'),
                        tabindex: -1,
                        selected: false,
                        expanded: false
                    });
                }

                if (!_.isEmpty(view.options.betaLanguage) && $.cookie('old-pref-lang')) {
                    betaLangMessage = HtmlUtils.interpolateHtml(
                        gettext('You have set your language to {beta_language}, which is currently not fully translated. You can help us translate this language fully by joining the Transifex community and adding translations from English for learners that speak {beta_language}.'),  // eslint-disable-line max-len
                        {
                            beta_language: view.options.betaLanguage.name
                        }
                    );
                    helpTranslateText = HtmlUtils.interpolateHtml(
                        gettext('Help Translate into {beta_language}'),
                        {
                            beta_language: view.options.betaLanguage.name
                        }
                    );
                    betaLangCode = this.options.betaLanguage.code.split('-');
                    if (betaLangCode.length > 1) {
                        betaLangCode = betaLangCode[0] + '_' + betaLangCode[1].toUpperCase();
                    } else {
                        betaLangCode = betaLangCode[0];
                    }
                    helpTranslateLink = 'https://www.transifex.com/open-edx/edx-platform/translate/#' + betaLangCode;
                    oldLangCode = $.cookie('old-pref-lang');
                    // Deleting the cookie
                    document.cookie = 'old-pref-lang=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/account;';

                    $.cookie('focus_id', '#beta-language-message');
                }
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(accountSettingsTemplate)({
                    accountSettingsTabs: accountSettingsTabs,
                    HtmlUtils: HtmlUtils,
                    message: betaLangMessage,
                    helpTranslateText: helpTranslateText,
                    helpTranslateLink: helpTranslateLink,
                    oldLangCode: oldLangCode
                }));
                _.each(accountSettingsTabs, function(tab) {
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
            },

            revertValue: function(event) {
                this.options.userPreferencesModel.trigger('revertValue', event);
            }
        });

        return AccountSettingsView;
    });
}).call(this, define || RequireJS.define);
