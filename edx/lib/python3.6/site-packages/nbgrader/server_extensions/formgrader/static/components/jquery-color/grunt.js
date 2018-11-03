/*jshint node: true */
module.exports = function( grunt ) {

"use strict";

var max = [ "dist/jquery.color.js", "dist/jquery.color.svg-names.js" ],
	min = [ "dist/jquery.color.min.js", "dist/jquery.color.svg-names.min.js", "dist/jquery.color.plus-names.min.js"],
	combined = "dist/jquery.color.plus-names.js",
	minify = {},
	concat = {};

minify[ min[0] ] = [ "<banner>", max[0] ];
minify[ min[1] ] = [ "<banner:meta.bannerSvg>", max[1] ];
minify[ min[2] ] = [ "<banner:meta.bannerCombined>", combined ];
concat[ combined ] = [ max[0], max[1] ];

grunt.loadNpmTasks( "grunt-compare-size" );
grunt.loadNpmTasks( "grunt-git-authors" );

grunt.initConfig({
	pkg: "<json:package.json>",

	meta: {
		banner: "/*! jQuery Color v@<%= pkg.version %> http://github.com/jquery/jquery-color | jquery.org/license */",
		bannerSvg: "/*! jQuery Color v@<%= pkg.version %> SVG Color Names http://github.com/jquery/jquery-color | jquery.org/license */",
		bannerCombined: "/*! jQuery Color v@<%= pkg.version %> with SVG Color Names http://github.com/jquery/jquery-color | jquery.org/license */"
	},

	lint: {
		src: [ "jquery.color.js", "jquery.color.svg-names.js" ],
		grunt: "grunt.js",
		test: "test/unit/**"
	},

	jshint: (function() {
		function parserc( path ) {
			var rc = grunt.file.readJSON( (path || "") + ".jshintrc" ),
				settings = {
					options: rc,
					globals: rc.globals || {}
				};

			(rc.predef || []).forEach(function( prop ) {
				settings.globals[ prop ] = true;
			});
			delete rc.predef;

			return settings;
		}

		return {
			src: parserc(),
			grunt: parserc(),
			test: parserc( "test/unit/" )
		};
	})(),

	qunit: {
		files: "test/index.html"
	},

	concat: concat,

	min: minify,

	watch: {
		files: [ "<config:lint.src>", "<config:lint.test>", "<config:lint.grunt>" ],
		tasks: "default"
	},

	compare_size: {
		"color": [ max[0], min[0] ],
		"svg-names": [ max[1], min[1] ],
		"combined": [ combined, min[2] ]
	}
});



grunt.registerHelper( "git-date", function( fn ) {
	grunt.utils.spawn({
		cmd: "git",
		args: [ "log", "-1", "--pretty=format:%ad" ]
	}, function( error, result ) {
		if ( error ) {
			grunt.log.error( error );
			return fn( error );
		}

		fn( null, result );
	});
});

grunt.registerTask( "submodules", function() {
	var done = this.async();

	grunt.verbose.write( "Updating submodules..." );

	grunt.utils.spawn({
		cmd: "git",
		args: [ "submodule", "update", "--init" ]
	}, function( err, result ) {
		if ( err ) {
			grunt.verbose.error();
			done( err );
			return;
		}

		grunt.log.writeln( result );

		done();
	});
});

grunt.registerTask( "max", function() {
	var done = this.async(),
		version = grunt.config( "pkg.version" );

	if ( process.env.COMMIT ) {
		version += " " + process.env.COMMIT;
	}
	grunt.helper( "git-date", function( error, date ) {
		if ( error ) {
			return done( false );
		}

		max.forEach( function( dist ) {
			grunt.file.copy( dist.replace( "dist/", "" ), dist, {
				process: function( source ) {
					return source
						.replace( /@VERSION/g, version )
						.replace( /@DATE/g, date );
				}
			});
		});


		done();
	});
});

grunt.registerTask( "testswarm", function( commit, configFile ) {
	var testswarm = require( "testswarm" ),
		config = grunt.file.readJSON( configFile ).jquerycolor;
	config.jobName = "jQuery Color commit #<a href='https://github.com/jquery/jquery-color/commit/" + commit + "'>" + commit.substr( 0, 10 ) + "</a>";
	config["runNames[]"] = "jQuery color";
	config["runUrls[]"] = config.testUrl + commit + "/test/index.html";
	config["browserSets[]"] = ["popular"];
	testswarm({
		url: config.swarmUrl,
		pollInterval: 10000,
		timeout: 1000 * 60 * 30,
		done: this.async()
	}, config);
});

grunt.registerTask( "manifest", function() {
	var pkg = grunt.config( "pkg" );
	grunt.file.write( "color.jquery.json", JSON.stringify({
		name: "color",
		title: pkg.title,
		description: pkg.description,
		keywords: pkg.keywords,
		version: pkg.version,
		author: {
			name: pkg.author.name,
			url: pkg.author.url.replace( "master", pkg.version )
		},
		maintainers: pkg.maintainers,
		licenses: pkg.licenses.map(function( license ) {
			license.url = license.url.replace( "master", pkg.version );
			return license;
		}),
		bugs: pkg.bugs,
		homepage: pkg.homepage,
		docs: pkg.homepage,
		download: "http://code.jquery.com/#color",
		dependencies: {
			jquery: ">=1.5"
		}
	}, null, "\t" ) );
});

grunt.registerTask( "default", "lint submodules qunit build compare_size" );
grunt.registerTask( "build", "max concat min" );

};
