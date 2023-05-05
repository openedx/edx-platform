/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import CourseEntitlementView from './views/course_entitlement_view';

function EntitlementFactory(options) {
    return new CourseEntitlementView(options);
}

export { EntitlementFactory }; // eslint-disable-line import/prefer-default-export
