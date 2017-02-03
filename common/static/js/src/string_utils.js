// String utility methods.
(function(_) {
    /**
     * Takes both a singular and plural version of a templatized string and plugs
     * in the placeholder values. Assumes that internationalization has already been
     * handled if necessary. Note that for text that needs to be internationalized,
     * normally ngettext and interpolate_text would be used instead of this method.
     *
     * Example usage:
     *     interpolate_ntext('(contains {count} student)',  '(contains {count} students)',
     *         expectedCount, {count: expectedCount}
     *     )
     *
     * @param singular the singular version of the templatized text
     * @param plural the plural version of the templatized text
     * @param count the count on which to base singular vs. plural text. Since this method is only
     * intended for text that does not need to be passed through ngettext for internationalization,
     * the simplistic English rule of count == 1 indicating singular is used.
     * @param values the templatized dictionary values
     * @returns the text with placeholder values filled in
     */
    var interpolate_ntext = function(singular, plural, count, values) {
        var text = count === 1 ? singular : plural;
        return _.template(text, {interpolate: /\{(.+?)\}/g})(values);
    };
    this.interpolate_ntext = interpolate_ntext;

    /**
     * Takes a templatized string and plugs in the placeholder values. Assumes that internationalization
     * has already been handled if necessary.
     *
     * Example usages:
     *     interpolate_text('{title} ({count})', {title: expectedTitle, count: expectedCount}
     *     interpolate_text(
     *         ngettext("{numUsersAdded} student has been added to this cohort",
     *             "{numUsersAdded} students have been added to this cohort", numUsersAdded),
     *         {numUsersAdded: numUsersAdded}
     *     );
     *
     * @param text the templatized text
     * @param values the templatized dictionary values
     * @returns the text with placeholder values filled in
     */
    var interpolate_text = function(text, values) {
        return _.template(text, {interpolate: /\{(.+?)\}/g})(values);
    };
    this.interpolate_text = interpolate_text;
}).call(this, _);
