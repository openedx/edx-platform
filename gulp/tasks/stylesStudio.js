var gulp          = require( 'gulp' ),
    config        = require( '../config' ).stylesStudio,
    handleErrors  = require( '../util/handleErrors' ),
    sass          = require( 'gulp-sass' );


gulp.task('stylesStudio', function () {
    return gulp.src(config.src)
        .pipe(sass())
        .on( 'error', handleErrors )
        .pipe( gulp.dest( config.dest ) );
});
