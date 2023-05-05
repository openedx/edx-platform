/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import ProgramDetailsView from './views/program_details_view';

function ProgramDetailsFactory(options) {
    return new ProgramDetailsView(options);
}

export { ProgramDetailsFactory }; // eslint-disable-line import/prefer-default-export
