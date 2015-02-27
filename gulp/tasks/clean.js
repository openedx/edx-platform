var gulp = require('gulp'),
    config   = require('../config'),
    del = require('del');

gulp.task( 'clean', function(cb) {
    del([
        config.styles.lms.clean,
        config.styles.studio.dest
    ], cb);
});
