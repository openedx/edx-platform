var gulp          = require( 'gulp' ),
    config        = require( '../config' ).studio_styles,
    handleErrors  = require( '../util/handleErrors' ),
    sass          = require( 'gulp-ruby-sass' );


gulp.task('styles-studio', function () {
    return sass( config.src, {
            loadPath: require('node-bourbon').includePaths,
            lineNumbers: true,
            verbose: true,
            trace: true
        })
        .on( 'error', handleErrors )
        .pipe( gulp.dest( config.dest ) );
});
