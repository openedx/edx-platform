var gulp     = require('gulp'),
    config   = require('../config');

gulp.task( 'watch', function(callback) {
    gulp.watch( config.styles.lms.src, ['stylesLMS'] );
    gulp.watch( config.styles.studio.src, ['stylesStudio'] );
});
