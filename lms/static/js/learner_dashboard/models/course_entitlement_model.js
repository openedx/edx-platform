/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import Backbone from 'backbone';

/**
 *  Store data for the current entitlement.
 */
class CourseEntitlementModel extends Backbone.Model {
    constructor(attrs, ...args) {
        const defaults = {
            availableSessions: [],
            entitlementUUID: '',
            currentSessionId: '',
            courseName: '',
            expiredAt: null,
            daysUntilExpiration: Number.MAX_VALUE,
        };
        // eslint-disable-next-line prefer-object-spread
        super(Object.assign({}, defaults, attrs), ...args);
    }
}

export default CourseEntitlementModel;
