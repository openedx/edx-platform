/*
 * jQuery inlineEdit
 *
 * Copyright (c) 2009 Ca-Phun Ung <caphun at yelotofu dot com>
 * Licensed under the MIT (MIT-LICENSE.txt) license.
 *
 * http://github.com/caphun/jquery.inlineedit/
 *
 * Inline (in-place) editing.
 */

(function($) {

// cached values
var namespace = '.inlineedit',
    placeholderClass = 'inlineEdit-placeholder';

// define inlineEdit method
$.fn.inlineEdit = function( options ) {
    var self = this;

    return this
    
        .each( function() {
            $.inlineEdit.getInstance( this, options ).initValue();
        })

        .live( ['click', 'mouseenter','mouseleave'].join(namespace+' '), function( event ) {

            var widget = $.inlineEdit.getInstance( this, options ),
                editableElement = widget.element.find( widget.options.control ),
                mutated = !!editableElement.length;

            widget.element.removeClass( widget.options.hover );
            
            if ( event.target !== editableElement[0] ) {
                switch ( event.type ) {
                    case 'click':
                        widget[ mutated ? 'mutate' : 'init' ]();
                        break;

                    case 'mouseover': // jquery 1.4.x
                    case 'mouseout': // jquery 1.4.x
                    case 'mouseenter':
                    case 'mouseleave':
                        if ( !mutated ) {
                            widget.hoverClassChange( event );
                        }
                        break;
                }
            }

        });
}

// plugin constructor
$.inlineEdit = function( elem, options ) {

    // deep extend
    this.options = $.extend( true, {}, $.inlineEdit.defaults, options );

    // the original element
    this.element = $( elem );

}

// plugin instance
$.inlineEdit.getInstance = function( elem, options ) {
    return ( $.inlineEdit.initialised( elem ) ) 
    ? $( elem ).data( 'widget' + namespace )
    : new $.inlineEdit( elem, options );
}

// check if plugin initialised
$.inlineEdit.initialised = function( elem ) {
    var init = $( elem ).data( 'init' + namespace );
    return init !== undefined && init !== null ? true : false;
}

// plugin defaults
$.inlineEdit.defaults = {
    hover: 'ui-state-hover',
    value: '',
    save: '',
    buttons: '<button class="save">✔</button> <button class="cancel">✘</button>',
    placeholder: 'Click to edit',
    control: 'input',
    cancelOnBlur: false,
    saveOnBlur: false
};

// plugin prototypes
$.inlineEdit.prototype = {

    // initialisation
    init: function() {

        // set initialise flag
        this.element.data( 'init' + namespace, true );
    
        // initialise value
        this.initValue();

        // mutate
        this.mutate();
    
        // save widget data
        this.element.data( 'widget' + namespace, this );

    },

    initValue: function() {
        this.value( $.trim( this.element.text() ) || this.options.value );
    
        if ( !this.value() ) {
            this.element.html( $( this.placeholderHtml() ) );
        } else if ( this.options.value ) {
            this.element.html( this.options.value );
        }
    },
    
    mutate: function() {
        var self = this;

        return self
            .element
            .html( self.mutatedHtml( self.value() ) )
            .find( 'button.save' )
                .bind( 'click', function( event ) {
                    self.save( self.element, event );
                    self.change( self.element, event );
                    return false;
                })
            .end()
            .find( 'button.cancel' )
                .bind( 'click', function( event ) {
                    self.change( self.element, event );
                    return false;
                })
            .end()
            .find( self.options.control )
                .bind( 'blur', function( event ) {
                  if (self.options.cancelOnBlur === true)
                    self.change( self.element, event );
                  else if (self.options.saveOnBlur == true){
                    self.save( self.element, event );
                    self.change( self.element, event );
                  }
                })
                .bind( 'keyup', function( event ) {
                    switch ( event.keyCode ) {
                        case 13: // save on ENTER
                            if (self.options.control !== 'textarea') {
                                self.save( self.element, event );
                                self.change( self.element, event );
                            }
                            break;
                        case 27: // cancel on ESC
                            self.change( self.element, event );
                            break;
                    }
                })
                .focus()
            .end();
    },
    
    value: function( newValue ) {
        if ( arguments.length ) {
            var value = newValue === this.options.placeholder ? '' : newValue;
            this.element.data( 'value' + namespace, $( '.' + placeholderClass, this ).length ? '' : value && this.encodeHtml( value.replace( /\n/g,"<br />" ) ) );
        }
        return this.element.data( 'value' + namespace );
    },

    mutatedHtml: function( value ) {
        return this.controls[ this.options.control ].call( this, value );
    },

    placeholderHtml: function() {
        return '<span class="'+ placeholderClass +'">'+ this.options.placeholder +'</span>';
    },

    buttonHtml: function( options ) {
        var o = $.extend({}, {
            before: ' ',
            buttons: this.options.buttons,
            after: ''
        }, options);
        
        return o.before + o.buttons + o.after;
    },
    
    save: function( elem, event ) {
        var $control = this.element.find( this.options.control ), 
            hash = {
                value: this.encodeHtml( $control.val() )
            };

        // save value back to control to avoid XSS
        $control.val(hash.value);
        
        if ( ( $.isFunction( this.options.save ) && this.options.save.call( this.element[0], event, hash ) ) !== false || !this.options.save ) {
            this.value( hash.value );
        }
    },
    
    change: function( elem, event ) {
        var self = this;
        
        if ( this.timer ) {
            window.clearTimeout( this.timer );
        }

        this.timer = window.setTimeout( function() {
            self.element.html( self.value() || self.placeholderHtml() );
            self.element.removeClass( self.options.hover );
        }, 200 );

    },

    controls: {
        textarea: function( value ) {
            return '<textarea>'+ value.replace(/<br\s?\/?>/g,"\n") +'</textarea>' + this.buttonHtml( { before: '<br />' } );
        },
        input: function( value ) {
            return '<input type="text" value="'+ value.replace(/(\u0022)+/g, '') +'">' + this.buttonHtml();
        }
    },

    hoverClassChange: function( event ) {
        $( event.target )[ /mouseover|mouseenter/.test( event.type ) ? 'addClass':'removeClass']( this.options.hover );
    },
    
    encodeHtml: function( s ) {
        var encoding = [
              {key: /</g, value: '&lt;'}, 
              {key: />/g, value: '&gt;'}, 
              {key: /"/g, value: '&quot;'}
            ],
            value = s;

        $.each(encoding, function(i,n) {
          value = value.replace(n.key, n.value);
        });

        return value;
    }

};

})(jQuery);
