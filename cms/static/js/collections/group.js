define([
    'underscore', 'underscore.string', 'backbone', 'gettext', 'js/models/group'
],
function(_, str, Backbone, gettext, GroupModel) {
    'use strict';
    var GroupCollection = Backbone.Collection.extend({
        model: GroupModel,
        comparator: 'order',
        /*
         * Return next index for the model.
         * @return {Number}
         */
        nextOrder: function() {
            if (!this.length) {
                return 0;
            }

            return this.last().get('order') + 1;
        },
        /**
         * Indicates if the collection is empty when all the models are empty
         * or the collection does not include any models.
         **/
        isEmpty: function() {
            return this.length === 0 || this.every(function(m) {
                return m.isEmpty();
            });
        },

        /*
         * Return default name for the group.
         * @return {String}
         * @examples
         * Group A, Group B, Group AA, Group ZZZ etc.
         */
        getNextDefaultGroupName: function() {
            var index = this.nextOrder(),
                usedNames = _.pluck(this.toJSON(), 'name'),
                name = '';

            do {
                name = str.sprintf(gettext('Group %s'), this.getGroupId(index));
                index ++;
            } while (_.contains(usedNames, name));

            return name;
        },

        /*
         * Return group id for the default name of the group.
         * @param {Number} number Current index of the model in the collection.
         * @return {String}
         * @examples
         * A, B, AA in Group A, Group B, ..., Group AA, etc.
         */
        getGroupId: (function() {
            /*
                Translators: Dictionary used for creation ids that are used in
                default group names. For example: A, B, AA in Group A,
                Group B, ..., Group AA, etc.
            */
            var dict = gettext('ABCDEFGHIJKLMNOPQRSTUVWXYZ').split(''),
                len = dict.length,
                divide;

            divide = function(numerator, denominator) {
                if (!_.isNumber(numerator) || !denominator) {
                    return null;
                }

                return {
                    quotient: numerator / denominator,
                    remainder: numerator % denominator
                };
            };

            return function getId(number) {
                var accumulatedValues = '',
                    result = divide(number, len),
                    index;

                if (result) {
                    // subtract 1 to start the count with 0.
                    index = Math.floor(result.quotient) - 1;

                    // Proceed by dividing the non-remainder part of the
                    // dividend by the desired base until the result is less
                    // than one.
                    if (index < len) {
                        // if index < 0, we do not need an additional power.
                        if (index > -1) {
                            // Get value for the next power.
                            accumulatedValues += dict[index];
                        }
                    } else {
                        // If we need more than 1 additional power.
                        // Get value for the next powers.
                        accumulatedValues += getId(index);
                    }

                    // Accumulated values + the current reminder
                    return accumulatedValues + dict[result.remainder];
                }

                return String(number);
            };
        }())
    });

    return GroupCollection;
});
