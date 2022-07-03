/**
 * Useful functions for dealing with HTML.
 *
 * In particular, these functions default to being safe against
 * Cross Site Scripting (XSS) attacks. You can read more about
 * the best practices for handling proper escaping in the Open edX
 * platform with
 * [Preventing Cross Site Scripting Vulnerabilities][1].
 * [1]: http://edx.readthedocs.org/projects/edx-developer-guide/en/latest/conventions/safe_templates.html
 *
 * @module HtmlUtils
 */
(function(define) {
    'use strict';

    define(['underscore', 'jquery', 'edx-ui-toolkit/js/utils/string-utils'], function(_, $, StringUtils) {
        var HtmlUtils, ensureHtml, interpolateHtml, joinHtml, HTML, template, setHtml, append, prepend;

        /**
         * Creates an HTML snippet.
         *
         * The intention of an HTML snippet is to communicate that the string
         * it represents contains HTML that has been safely escaped as necessary.
         * As an example, this allows `HtmlUtils.interpolate` to understand that
         * it does not need to further escape this HTML.
         *
         * @param {string} htmlString The string of HTML.
         */
        function HtmlSnippet(htmlString) {
            this.text = htmlString;
        }
        HtmlSnippet.prototype.valueOf = function() {
            return this.text;
        };
        HtmlSnippet.prototype.toString = function() {
            return this.text;
        };

        /**
         * Helper function to create an HTML snippet from a string.
         *
         * The intention of an HTML snippet is to communicate that the string
         * it represents contains HTML that has been safely escaped as necessary.
         *
         * @param {string} htmlString The string of HTML.
         * @returns {HtmlSnippet} An HTML snippet that can be safely rendered.
         */
        HTML = function(htmlString) {
            return new HtmlSnippet(htmlString);
        };

        /**
         * Ensures that the provided text is properly HTML-escaped.
         *
         * If a plain text string is provided, then it will be HTML-escaped and
         * returned as an HtmlSnippet. If the parameter is an HTML snippet
         * then it will be returned directly so as not to double escape it.
         *
         * @param {(string|HtmlSnippet)} html Either a plain text string
         * or an HTML snippet.
         * @returns {HtmlSnippet} A safely escaped HTML snippet.
         */
        ensureHtml = function(html) {
            if (html instanceof HtmlSnippet) {
                return html;
            } else {
                return HTML(_.escape(html));
            }
        };

        /**
         * Returns an HTML snippet by interpolating the provided parameters.
         *
         * The text is provided as a tokenized format string where parameters
         * are indicated via curly braces, e.g. `'Hello {name}'`. These tokens are
         * replaced by the parameter value of the same name.
         *
         * Parameter values will be rendered using their toString methods and then
         * HTML-escaped. The only exception is that instances of the class HTML
         * are rendered without escaping as their contract declares that they are
         * already valid HTML.
         *
         * Example:
         *
         *~~~ javascript
         * HtmlUtils.interpolateHtml(
         *     'You are enrolling in {spanStart}{courseName}{spanEnd}',
         *     {
         *         courseName: 'Rock & Roll 101',
         *         spanStart: HtmlUtils.HTML('<span class="course-title">'),
         *         spanEnd: HtmlUtils.HTML('</span>')
         *     }
         * );
         *~~~
         *
         * returns:
         *
         *~~~ javascript
         * 'You are enrolling in <span class="course-title">Rock &amp; Roll 101</span>'
         *~~~
         *
         * Note: typically the formatString will need to be internationalized, in which
         * case it will be wrapped with a call to an i18n lookup function. If using
         * the Django i18n library this would look like:
         *
         *~~~ javascript
         * HtmlUtils.interpolateHtml(
         *     gettext('You are enrolling in {spanStart}{courseName}{spanEnd}'),
         *     ...
         * );
         *~~~
         *
         * @param {string} formatString The string to be interpolated.
         * @param {Object} parameters An optional set of parameters for interpolation.
         * @returns {HtmlSnippet} The resulting safely escaped HTML snippet.
         */
        interpolateHtml = function(formatString, parameters) {
            var result = StringUtils.interpolate(
                ensureHtml(formatString).toString(),
                _.mapObject(parameters, ensureHtml)
            );
            return HTML(result);
        };

        /**
         * Joins multiple strings and/or HTML snippets together to produce
         * a single safely escaped HTML snippet.
         *
         * For each item, if it is provided as an HTML snippet then it is joined
         * directly. If the item is a string then it is assumed to be unescaped and
         * so it is first escaped before being joined.
         *
         * @param {...(string|HtmlSnippet)} items The strings and/or HTML snippets
         * to be joined together.
         * @returns {HtmlSnippet} The resulting safely escaped HTML snippet.
         */
        joinHtml = function() {
            var html = '',
                argumentCount = arguments.length,
                i;
            for (i = 0; i < argumentCount; i += 1) {
                html += ensureHtml(arguments[i]);
            }
            return HTML(html);
        };

        /**
         * Returns a function that renders an Underscore template as an HTML snippet.
         *
         * Note: This helper function makes the following context parameters
         * available to the template in addition to those passed in:
         *
         *   - `HtmlUtils`: the `HtmlUtils` helper class
         *   - `StringUtils`: the `StringUtils` helper class
         *
         * @param {string} text
         * @param {object} settings
         * @returns {function} A function that returns a rendered HTML snippet.
         */
        template = function(text, settings) {
            return function(data) {
                var augmentedData = _.extend(
                    {
                        HtmlUtils: HtmlUtils,
                        StringUtils: StringUtils
                    },
                    data || {}
                );
                return HTML(_.template(text, settings)(augmentedData));
            };
        };

        /**
         * A wrapper for `$.html` that safely escapes the provided HTML.
         *
         * If the HTML is provided as an HTML snippet then it is used directly.
         * If the value is a string then it is assumed to be unescaped and
         * so it is first escaped before being used.
         *
         * @param {element} element The element or elements to be updated.
         * @param {(string|HtmlSnippet)} html The desired HTML, either as a
         * plain string or as an HTML snippet.
         * @returns {JQuery} The JQuery object representing the element or elements.
         */
        setHtml = function(element, html) {
            return $(element).html(ensureHtml(html).toString());
        };

        /**
         * A wrapper for `$.append` that safely escapes the provided HTML.
         *
         * If the HTML is provided as an HTML snippet then it is used directly.
         * If the value is a string then it is assumed to be unescaped and
         * so it is first escaped before being used.
         *
         * @param {element} element The element or elements to be updated.
         * @param {(string|HtmlSnippet)} html The desired HTML, either as a
         * plain string or as an HTML snippet.
         * @returns {JQuery} The JQuery object representing the element or elements.
         */
        append = function(element, html) {
            return $(element).append(ensureHtml(html).toString());
        };

        /**
         * A wrapper for `$.prepend` that safely escapes the provided HTML.
         *
         * If the HTML is provided as an HTML snippet then it is used directly.
         * If the value is a string then it is assumed to be unescaped and
         * so it is first escaped before being used.
         *
         * @param {element} element The element or elements to be updated.
         * @param {(string|HtmlSnippet)} html The desired HTML, either as a
         * plain string or as an HTML snippet.
         * @returns {JQuery} The JQuery object representing the element or elements.
         */
        prepend = function(element, html) {
            return $(element).prepend(ensureHtml(html).toString());
        };

        HtmlUtils = {
            append: append,
            ensureHtml: ensureHtml,
            HTML: HTML,
            HtmlSnippet: HtmlSnippet,
            interpolateHtml: interpolateHtml,
            joinHtml: joinHtml,
            prepend: prepend,
            setHtml: setHtml,
            template: template
        };

        return HtmlUtils;
    });
}).call(
    this,
    // Pick a define function as follows:
    // 1. Use the default 'define' function if it is available
    // 2. If not, use 'RequireJS.define' if that is available
    // 3. else use the GlobalLoader to install the class into the edx namespace
    // eslint-disable-next-line no-nested-ternary
    typeof define === 'function' && define.amd ? define :
        (typeof RequireJS !== 'undefined' ? RequireJS.define :
            edx.GlobalLoader.defineAs('HtmlUtils', 'edx-ui-toolkit/js/utils/html-utils'))
);
