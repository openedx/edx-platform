jasmine.getFixtures().fixturesPath = '/base/templates';

import 'common/js/spec_helpers/jasmine-extensions';
import 'common/js/spec_helpers/jasmine-stealth';
import 'common/js/spec_helpers/jasmine-waituntil';

// These libraries are used by the tests (and the code under test)
// but not explicitly imported
import 'jquery.ui';

import _ from 'underscore';
import str from 'underscore.string';
import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';
window._ = _;
window._.str = str;
window.edx = window.edx || {};
window.edx.HtmlUtils = HtmlUtils;
window.edx.StringUtils = StringUtils;

// These are the tests that will be run
import './xblock/cms.runtime.v1_spec.js';
import '../../../js/spec/factories/xblock_validation_spec.js';
import '../../../js/spec/views/container_spec.js';
import '../../../js/spec/views/modals/edit_xblock_spec.js';
import '../../../js/spec/views/module_edit_spec.js';
import '../../../js/spec/views/move_xblock_spec.js';
import '../../../js/spec/views/pages/container_spec.js';
import '../../../js/spec/views/pages/container_subviews_spec.js';
import '../../../js/spec/views/pages/course_outline_spec.js';
import '../../../js/spec/views/xblock_editor_spec.js';
import '../../../js/spec/views/xblock_string_field_editor_spec.js';

window.__karma__.start();  // eslint-disable-line no-underscore-dangle
