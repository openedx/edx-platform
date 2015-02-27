var gulp          = require( 'gulp' ),
    bless         = require('gulp-bless'),
    config        = require( '../config' ).stylesStudio,
    handleErrors  = require( '../util/handleErrors' ),
    sass          = require( 'gulp-sass' );


gulp.task('stylesStudio', function () {
    return gulp.src( config.src )
        .pipe( sass() )
        .pipe( bless() )
        .on( 'error', handleErrors )
        .pipe( gulp.dest( config.dest ) );
});
