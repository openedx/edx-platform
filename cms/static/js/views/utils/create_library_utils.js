/**
 * Provides utilities for validating libraries during creation.
 */
// eslint-disable-next-line no-undef
define(['jquery', 'gettext', 'common/js/components/utils/view_utils', 'js/views/utils/create_utils_base'],
    function($, gettext, ViewUtils, CreateUtilsFactory) {
        'use strict';

        return function(selectors, classes) {
            // eslint-disable-next-line no-var
            var keyLengthViolationMessage = gettext('The combined length of the organization and library code fields'
              + ' cannot be more than <%- limit %> characters.');
            // eslint-disable-next-line no-var
            var keyFieldSelectors = [selectors.org, selectors.number];
            // eslint-disable-next-line no-var
            var nonEmptyCheckFieldSelectors = [selectors.name, selectors.org, selectors.number];

            CreateUtilsFactory.call(this, selectors, classes, keyLengthViolationMessage, keyFieldSelectors, nonEmptyCheckFieldSelectors);

            this.create = function(libraryInfo, errorHandler) {
                $.postJSON(
                    '/library/',
                    libraryInfo
                ).done(function(data) {
                    ViewUtils.redirect(data.url);
                }).fail(function(jqXHR, textStatus, errorThrown) {
                    // eslint-disable-next-line no-var
                    var reason = errorThrown;
                    if (jqXHR.responseText) {
                        try {
                            // eslint-disable-next-line no-var
                            var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                            if (detailedReason) {
                                reason = detailedReason;
                            }
                        // eslint-disable-next-line no-empty
                        } catch (e) {}
                    }
                    errorHandler(reason);
                });
            };
        };
    });
