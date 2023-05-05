/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import UnenrollView from './views/unenroll_view';

function UnenrollmentFactory(options) {
    return new UnenrollView(options);
}

export { UnenrollmentFactory }; // eslint-disable-line import/prefer-default-export
