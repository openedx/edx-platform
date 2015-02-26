var gulp          = require('gulp');
var config        = require('../config').studio_styles;
var handleErrors  = require('../util/handleErrors');

gulp.task('styles-studio', function () {
  return gulp.src(config.src)
    .on('error', handleErrors)
    .pipe(gulp.dest(config.dest))
});
