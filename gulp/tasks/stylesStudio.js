var gulp          = require( 'gulp' ),
    config        = require( '../config' ).stylesStudio,
    handleErrors  = require( '../util/handleErrors' ),
    sass          = require( 'gulp-ruby-sass' );


gulp.task('stylesStudio', function () {
    return sass( config.src, {
            // loadPath: require('node-bourbon').includePaths,
            lineNumbers: true,
            verbose: true,
            trace: true
        })
        .on( 'error', handleErrors )
        .pipe( gulp.dest( config.dest ) );
});
