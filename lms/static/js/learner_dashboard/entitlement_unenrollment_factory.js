import EntitlementUnenrollmentView from './views/entitlement_unenrollment_view';

function EntitlementUnenrollmentFactory(options) {
  return new EntitlementUnenrollmentView(options);
}

export { EntitlementUnenrollmentFactory }; // eslint-disable-line import/prefer-default-export
