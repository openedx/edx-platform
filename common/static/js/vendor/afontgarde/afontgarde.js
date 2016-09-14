/*! afontgarde - v0.1.6 - 2015-03-13
 * https://github.com/filamentgroup/a-font-garde
 * Copyright (c) 2015 Filament Group c/o Zach Leatherman
 * MIT License */

/*! fontfaceonload - v0.1.6 - 2015-03-13
 * https://github.com/zachleat/fontfaceonload
 * Copyright (c) 2015 Zach Leatherman (@zachleat)
 * MIT License */

;(function( win, doc ) {
    "use strict";

    var TEST_STRING = 'AxmTYklsjo190QW',
        SANS_SERIF_FONTS = 'sans-serif',
        SERIF_FONTS = 'serif',

        // lighter and bolder not supported
        weightLookup = {
            normal: '400',
            bold: '700'
        },

        defaultOptions = {
            tolerance: 2, // px
            delay: 100,
            glyphs: '',
            success: function() {},
            error: function() {},
            timeout: 5000,
            weight: '400', // normal
            style: 'normal'
        },

        // See https://github.com/typekit/webfontloader/blob/master/src/core/fontruler.js#L41
        style = [
            'display:block',
            'position:absolute',
            'top:-999px',
            'left:-999px',
            'font-size:48px',
            'width:auto',
            'height:auto',
            'line-height:normal',
            'margin:0',
            'padding:0',
            'font-variant:normal',
            'white-space:nowrap'
        ],
        html = '<div style="%s">' + TEST_STRING + '</div>';

    var FontFaceOnloadInstance = function() {
        this.fontFamily = '';
        this.appended = false;
        this.serif = undefined;
        this.sansSerif = undefined;
        this.parent = undefined;
        this.options = {};
    };

    FontFaceOnloadInstance.prototype.getMeasurements = function () {
        return {
            sansSerif: {
                width: this.sansSerif.offsetWidth,
                height: this.sansSerif.offsetHeight
            },
            serif: {
                width: this.serif.offsetWidth,
                height: this.serif.offsetHeight
            }
        };
    };

    FontFaceOnloadInstance.prototype.load = function () {
        var startTime = new Date(),
            that = this,
            serif = that.serif,
            sansSerif = that.sansSerif,
            parent = that.parent,
            appended = that.appended,
            dimensions,
            options = this.options,
            ref = options.reference;

        function getStyle( family ) {
            return style
                .concat( [ 'font-weight:' + options.weight, 'font-style:' + options.style ] )
                .concat( "font-family:" + family )
                .join( ";" );
        }

        var sansSerifHtml = html.replace( /\%s/, getStyle( SANS_SERIF_FONTS ) ),
            serifHtml = html.replace( /\%s/, getStyle(  SERIF_FONTS ) );

        if( !parent ) {
            parent = that.parent = doc.createElement( "div" );
        }

        parent.innerHTML = sansSerifHtml + serifHtml;
        sansSerif = that.sansSerif = parent.firstChild;
        serif = that.serif = sansSerif.nextSibling;

        if( options.glyphs ) {
            sansSerif.innerHTML += options.glyphs;
            serif.innerHTML += options.glyphs;
        }

        function hasNewDimensions( dims, el, tolerance ) {
            return Math.abs( dims.width - el.offsetWidth ) > tolerance ||
                    Math.abs( dims.height - el.offsetHeight ) > tolerance;
        }

        function isTimeout() {
            return ( new Date() ).getTime() - startTime.getTime() > options.timeout;
        }

        (function checkDimensions() {
            if( !ref ) {
                ref = doc.body;
            }
            if( !appended && ref ) {
                ref.appendChild( parent );
                appended = that.appended = true;

                dimensions = that.getMeasurements();

                // Make sure we set the new font-family after we take our initial dimensions:
                // handles the case where FontFaceOnload is called after the font has already
                // loaded.
                sansSerif.style.fontFamily = that.fontFamily + ', ' + SANS_SERIF_FONTS;
                serif.style.fontFamily = that.fontFamily + ', ' + SERIF_FONTS;
            }

            if( appended && dimensions &&
                ( hasNewDimensions( dimensions.sansSerif, sansSerif, options.tolerance ) ||
                    hasNewDimensions( dimensions.serif, serif, options.tolerance ) ) ) {

                options.success();
            } else if( isTimeout() ) {
                options.error();
            } else {
                if( !appended && "requestAnimationFrame" in window ) {
                    win.requestAnimationFrame( checkDimensions );
                } else {
                    win.setTimeout( checkDimensions, options.delay );
                }
            }
        })();
    }; // end load()

    FontFaceOnloadInstance.prototype.checkFontFaces = function( timeout ) {
        var _t = this;
        doc.fonts.forEach(function( font ) {
            if( font.family.toLowerCase() === _t.fontFamily.toLowerCase() &&
                ( weightLookup[ font.weight ] || font.weight ) === ''+_t.options.weight &&
                font.style === _t.options.style ) {
                font.load().then(function() {
                    _t.options.success();
                    win.clearTimeout( timeout );
                });
            }
        });
    };

    FontFaceOnloadInstance.prototype.init = function( fontFamily, options ) {
        var timeout;

        for( var j in defaultOptions ) {
            if( !options.hasOwnProperty( j ) ) {
                options[ j ] = defaultOptions[ j ];
            }
        }

        this.options = options;
        this.fontFamily = fontFamily;

        // For some reason this was failing on afontgarde + icon fonts.
        if( !options.glyphs && "fonts" in doc ) {
            if( options.timeout ) {
                timeout = win.setTimeout(function() {
                    options.error();
                }, options.timeout );
            }

            this.checkFontFaces( timeout );
        } else {
            this.load();
        }
    };

    var FontFaceOnload = function( fontFamily, options ) {
        var instance = new FontFaceOnloadInstance();
        instance.init(fontFamily, options);

        return instance;
    };

    // intentional global
    win.FontFaceOnload = FontFaceOnload;
})( this, this.document );

/*
 * A Font Garde
 */

;(function( w ) {

    var doc = w.document,
        ref,
        css = ['.FONT_NAME.supports-generatedcontent .icon-fallback-text .icon { display: inline-block; }',
            '.FONT_NAME.supports-generatedcontent .icon-fallback-text .text { clip: rect(0 0 0 0); overflow: hidden; position: absolute; height: 1px; width: 1px; }',
            '.FONT_NAME .icon-fallback-glyph .icon:before { font-size: 1em; font-size: inherit; line-height: 1; line-height: inherit; }'];

    function addEvent( type, callback ) {
        if( 'addEventListener' in w ) {
            return w.addEventListener( type, callback, false );
        } else if( 'attachEvent' in w ) {
            return w.attachEvent( 'on' + type, callback );
        }
    }

    // options can be a string of glyphs or an options object to pass into FontFaceOnload
    AFontGarde = function( fontFamily, options ) {
        var fontFamilyClassName = fontFamily.toLowerCase().replace( /\s/g, '' ),
            executed = false;

        function init() {
            if( executed ) {
                return;
            }
            executed = true;

            if( typeof FontFaceOnload === 'undefined' ) {
                throw 'FontFaceOnload is a prerequisite.';
            }

            if( !ref ) {
                ref = doc.getElementsByTagName( 'script' )[ 0 ];
            }
            var style = doc.createElement( 'style' ),
                cssContent = css.join( '\n' ).replace( /FONT_NAME/gi, fontFamilyClassName );

            style.setAttribute( 'type', 'text/css' );
            if( style.styleSheet ) {
                style.styleSheet.cssText = cssContent;
            } else {
                style.appendChild( doc.createTextNode( cssContent ) );
            }
            ref.parentNode.insertBefore( style, ref );

            var opts = {
                timeout: 5000,
                success: function() {
                    // If you’re using more than one icon font, change this classname (and in a-font-garde.css)
                    doc.documentElement.className += ' ' + fontFamilyClassName;

                    if( options && options.success ) {
                        options.success();
                    }
                }
            };

            // These characters are a few of the glyphs from the font above */
            if( typeof options === "string" ) {
                opts.glyphs = options;
            } else {
                for( var j in options ) {
                    if( options.hasOwnProperty( j ) && j !== "success" ) {
                        opts[ j ] = options[ j ];
                    }
                }
            }

            FontFaceOnload( fontFamily, opts );
        }

        // MIT credit: filamentgroup/shoestring
        addEvent( "DOMContentLoaded", init );
        addEvent( "readystatechange", init );
        addEvent( "load", init );

        if( doc.readyState === "complete" ){
            init();
        }
    };

})( this );