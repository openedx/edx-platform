/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import EntitlementUnenrollmentView from './views/entitlement_unenrollment_view';

function EntitlementUnenrollmentFactory(options) {
    return new EntitlementUnenrollmentView(options);
}

export { EntitlementUnenrollmentFactory }; // eslint-disable-line import/prefer-default-export
