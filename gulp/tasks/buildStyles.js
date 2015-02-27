var gulp = require('gulp'),
    runSequence = require('run-sequence');

gulp.task( 'buildStyles', function() {
    runSequence( 'clean',
                ['stylesStudio', 'stylesLMS'] );
});
