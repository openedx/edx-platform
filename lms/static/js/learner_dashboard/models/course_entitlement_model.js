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
