/*
 * responsive-carousel keyboard extension
 * https://github.com/filamentgroup/responsive-carousel
 *
 * Copyright (c) 2012 Filament Group, Inc.
 * Licensed under the MIT, GPL licenses.
 */

(function($) {
  var pluginName = "carousel",
    initSelector = "." + pluginName,
    navSelector = "." + pluginName + "-nav a",
    buffer,
    keyNav = function( e ) {
      clearTimeout( buffer );
      buffer = setTimeout(function() {
        var $carousel = $( e.target ).closest( initSelector );

        if( e.keyCode === 39 || e.keyCode === 40 ){
          $carousel[ pluginName ]( "next" );
        }
        else if( e.keyCode === 37 || e.keyCode === 38 ){
          $carousel[ pluginName ]( "prev" );
        }
      }, 200 );

      if( 37 <= e.keyCode <= 40 ) {
        e.preventDefault();
      }
    };

  // Touch handling
  $( document )
    .on( "click", navSelector, function( e ) {
      $( e.target )[ 0 ].focus();
    })
    .on( "keydown", navSelector, keyNav );
}(jQuery));
