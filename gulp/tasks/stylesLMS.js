var gulp          = require( 'gulp' ),
    config        = require( '../config' ).styles.lms,
    handleErrors  = require( '../util/handleErrors' ),
    sass          = require( 'gulp-sass' );


gulp.task( 'stylesLMS', function () {
    return gulp.src( config.src )
        .pipe( sass() )
        .on( 'error', handleErrors )
        .pipe( gulp.dest( config.dest ) );
});
