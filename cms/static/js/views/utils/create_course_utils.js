/**
 * Provides utilities for validating courses during creation, for both new courses and reruns.
 */
// eslint-disable-next-line no-undef
define(['jquery', 'gettext', 'common/js/components/utils/view_utils', 'js/views/utils/create_utils_base'],
    function($, gettext, ViewUtils, CreateUtilsFactory) {
        'use strict';

        return function(selectors, classes) {
            // eslint-disable-next-line no-var
            var keyLengthViolationMessage = gettext('The combined length of the organization, course number, '
              + 'and course run fields cannot be more than <%- limit %> characters.');
            // eslint-disable-next-line no-var
            var keyFieldSelectors = [selectors.org, selectors.number, selectors.run];
            // eslint-disable-next-line no-var
            var nonEmptyCheckFieldSelectors = [selectors.name, selectors.org, selectors.number, selectors.run];

            CreateUtilsFactory.call(this, selectors, classes, keyLengthViolationMessage, keyFieldSelectors, nonEmptyCheckFieldSelectors);

            this.setupOrgAutocomplete = function() {
                $.getJSON('/organizations', function(data) {
                    $(selectors.org).autocomplete({
                        source: data
                    });
                });
            };

            this.create = function(courseInfo, errorHandler) {
                $.postJSON(
                    '/course/',
                    courseInfo,
                    function(data) {
                        if (data.url !== undefined) {
                            ViewUtils.redirect(data.url);
                        } else if (data.ErrMsg !== undefined) {
                            errorHandler(data.ErrMsg);
                        }
                    }
                );
            };
        };
    });
