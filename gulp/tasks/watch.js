var gulp     = require('gulp');
var config   = require('../config');

gulp.task('watch', function(callback) {
  gulp.watch(config.stylesStudio.src, ['stylesStudio']);
});
