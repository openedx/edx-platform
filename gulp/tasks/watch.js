var gulp     = require('gulp');
var config   = require('../config');

gulp.task('watch', ['browserSync'], function(callback) {
  gulp.watch(config.studio_styles.src, ['studio_styles']);
});
