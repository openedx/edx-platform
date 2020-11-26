
import '../../../../static/js/src/ajax_prefix.js';
import '../../../../static/common/js/vendor/underscore.js';
import '../../../../static/common/js/vendor/backbone.js';
import '../../../../static/js/vendor/CodeMirror/codemirror.js';
import '../../../../static/js/vendor/draggabilly.js';
import '../../../../static/common/js/vendor/jquery.js';
import '../../../../static/common/js/vendor/jquery-migrate.js';
import '../../../../static/js/vendor/jquery.cookie.js';
import '../../../../static/js/vendor/jquery.leanModal.js';
import '../../../../static/js/vendor/jquery.timeago.js';
import '../../../../static/js/vendor/jquery-ui.min.js';
import '../../../../static/js/vendor/jquery.ui.draggable.js';
import '../../../../static/js/vendor/json2.js';
// import '../../../../static/common/js/vendor/moment-with-locales.js';
import '../../../../static/js/vendor/tinymce/js/tinymce/jquery.tinymce.min.js';
import '../../../../static/js/vendor/tinymce/js/tinymce/tinymce.full.min.js';
import '../../../../static/js/src/accessibility_tools.js';
import '../../../../static/js/src/logger.js';
import '../../../../static/js/src/utility.js';
import '../../../../static/js/test/add_ajax_prefix.js';
import '../../../../static/js/test/i18n.js';
import '../../../../static/common/js/vendor/hls.js';
import '../assets/vertical/public/js/vertical_student_view.js';


import '../../../../static/js/vendor/jasmine-imagediff.js';
import '../../../../static/common/js/spec_helpers/jasmine-waituntil.js';
import '../../../../static/common/js/spec_helpers/jasmine-extensions.js';
import '../../../../static/common/js/vendor/sinon.js';

// These libraries are used by the tests (and the code under test)
// but not explicitly imported
import 'jquery.ui';

// These
import './src/video/10_main.js'
import './spec/helper.js'
import './spec/video_helper.js'

// These are the tests that will be run
import './spec/video/async_process_spec.js';
import './spec/video/completion_spec.js';
import './spec/video/events_spec.js';
import './spec/video/general_spec.js';
import './spec/video/html5_video_spec.js';
import './spec/video/initialize_spec.js';
import './spec/video/iterator_spec.js';
import './spec/video/resizer_spec.js';
import './spec/video/sjson_spec.js';
import './spec/video/video_autoadvance_spec.js';
import './spec/video/video_bumper_spec.js';
import './spec/video/video_caption_spec.js';
import './spec/video/video_context_menu_spec.js';
import './spec/video/video_control_spec.js';
import './spec/video/video_events_bumper_plugin_spec.js';
import './spec/video/video_events_plugin_spec.js';
import './spec/video/video_focus_grabber_spec.js';
import './spec/video/video_full_screen_spec.js';
import './spec/video/video_player_spec.js';
import './spec/video/video_play_pause_control_spec.js';
import './spec/video/video_play_placeholder_spec.js';
import './spec/video/video_play_skip_control_spec.js';
import './spec/video/video_poster_spec.js';
import './spec/video/video_progress_slider_spec.js';
import './spec/video/video_quality_control_spec.js';
import './spec/video/video_save_state_plugin_spec.js';
import './spec/video/video_skip_control_spec.js';
import './spec/video/video_speed_control_spec.js';
import './spec/video/video_storage_spec.js';
import './spec/video/video_volume_control_spec.js';
import './spec/time_spec.js';

// overwrite the loaded method and manually start the karma after a delay
// Somehow the code initialized in jQuery's onready doesn't get called before karma auto starts

'use strict';
window.__karma__.loaded = function () {
    setTimeout(function () {
        window.__karma__.start();
    }, 1000);
};
