# jQuery.Color()

Using jQuery Color in Production
--------------------------------
We release jQuery Color by itself, or in a bundle.  The extended names can be inclided as a jQuery Color plugin, or you can download the version of jQuery Color that includes the names.  Choose your build from the following list:

Current Version: 2.1.1

* jQuery Color [Compressed](http://code.jquery.com/color/jquery.color-2.1.1.min.js) [Uncompressed](http://code.jquery.com/color/jquery.color-2.1.1.js)
* jQuery Color Extended Names [Compressed](http://code.jquery.com/color/jquery.color.svg-names-2.1.1.min.js) [Uncompressed](http://code.jquery.com/color/jquery.color.svg-names-2.1.1.js)
* jQuery Color & Extended Names(previous two combined) [Compressed](http://code.jquery.com/color/jquery.color.plus-names-2.1.1.min.js) [Uncompressed](http://code.jquery.com/color/jquery.color.plus-names-2.1.1.js)

How to build and test jQuery Color
----------------------------------

First, get a copy of the git repo by running:

```shell
git clone git://github.com/jquery/jquery-color.git
```

Enter the directory and install the node dependencies:

```shell
cd jquery-color && npm install
```

Make sure you have `grunt` installed by testing:

```shell
grunt -version
```

If not, run:

```shell
npm install -g grunt
```

To run tests locally, run `grunt`, and this will run the tests in PhantomJS.

You can also run the tests in a browser by navigating to the `test/` directory, but first run `grunt` to install submodules.

## Animated colors

This plugins installs a [`cssHook`](http://api.jquery.com/jQuery.cssHooks/) which allows jQuery's [`.animate()`](http://api.jquery.com/animate) to animate between two colors.

Supported Properties
-------
`backgroundColor`, `borderBottomColor`, `borderLeftColor`, `borderRightColor`, `borderTopColor`, `color`, `columnRuleColor`, `outlineColor`, `textDecorationColor`, `textEmphasisColor`

Example Use
-------

```html
<!DOCTYPE html>
<html>
<head>
  <style>
div {
background-color:#bada55;
width:100px;
border:1px solid green;
}
</style>
<script src="http://code.jquery.com/jquery-1.6.1.min.js"></script>
<script src="jquery.color.min.js"></script>
</head>
<body>
<button id="go">Simple</button>
<button id="sat">Desaturate</button>
  <div id="block">Hello!</div>
<script>
jQuery("#go").click(function(){
  jQuery("#block").animate({
      backgroundColor: "#abcdef"
  }, 1500 );
});
jQuery("#sat").click(function(){
  jQuery("#block").animate({
      backgroundColor: jQuery.Color({ saturation: 0 })
  }, 1500 );
});
</script>
</body>
</html>
```

## Supporting other properties
The `jQuery.Color.hook()` function can be called to support additional css properties as colors, and allow them to be animated.

Example Use
-----------
```javascript
// we want to animate SVG fill and stroke properties
jQuery.Color.hook( "fill stroke" );
```

## The jQuery.Color Factory

The `jQuery.Color()` function allows you to create and manipulate color objects that are accepted by jQuery's `.animate()` and `.css()` functions.

* Returns a new Color object, similar to `jQuery()` or `jQuery.Event`
* Accepts many formats to create a new Color object with a `jQuery.Color.fn` prototype

### Example uses:

```javascript
// Parsing String Colors:
jQuery.Color( "#abcdef" );
jQuery.Color( "rgb(100,200,255)" );
jQuery.Color( "rgba(100,200,255,0.5)" );
jQuery.Color( "aqua" );

// Creating Color Objects in Code:
// use null or undefined for values you wish to leave out
jQuery.Color( red, green, blue, alpha );
jQuery.Color([ red, green, blue, alpha ]);
jQuery.Color({ red: red, green: green, blue: blue, alpha: alpha });
jQuery.Color({ hue: hue, saturation: saturation, lightness: lightness, alpha: alpha });

// Helper to get value from CSS
jQuery.Color( element, cssProperty );
```
## jQuery.Color.fn / prototype / the Color Object methods

### Getters / Setters:

```javascript
red()             // returns the "red" component of the color ( Integer from 0 - 255 )
red( val )        // returns a copy of the color object with the red set to val
green()           // returns the "green" component of the color from ( Integer from 0 - 255 )
green( val )      // returns a copy of the color object with the green set to val
blue()            // returns the "blue" component of the color from ( Integer from 0 - 255 )
blue( val )       // returns a copy of the color object with the blue set to val
alpha()           // returns the "alpha" component of the color from ( Float from 0.0 - 1.0 )
alpha( val )      // returns a copy of the color object with the alpha set to val
hue()             // returns the "hue" component of the color ( Integer from 0 - 359 )
hue( val )        // returns a copy of the color object with the hue set to val
saturation()      // returns the "saturation" component of the color ( Float from 0.0 - 1.0 )
saturation( val ) // returns a copy of the color object with the saturation set to val
lightness()       // returns the "lightness" component of the color ( Float from 0.0 - 1.0 )
lightness( val )  // returns a copy of the color object with the lightness set to val
// all of the above values can also take strings in the format of "+=100" or "-=100"

rgba() // returns a rgba "tuple" [ red, green, blue, alpha ]
// rgba() setters: returns a copy of the color with any defined values set to the new value
rgba( red, green, blue, alpha )
rgba({ red: red, green: green, blue: blue, alpha: alpha })
rgba([ red, green, blue, alpha ])

hsla() // returns a HSL tuple [ hue, saturation, lightness, alpha ]
// much like the rgb setter - returns a copy with any defined values set
hsla( hue, saturation, lightness, alpha )
hsla({ hue: hue, saturation: saturation, lightness: lightness, alpha: alpha )
hsla([ hue, saturation, lightness, alpha ])
```

### String Methods:

```javascript
toRgbaString() // returns a css string "rgba(255, 255, 255, 0.4)"
toHslaString() // returns a css string "hsla(330, 75%, 25%, 0.4)"
toHexString( includeAlpha ) // returns a css string "#abcdef", with "includeAlpha" uses "#rrggbbaa" (alpha *= 255)
```

The `toRgbaString` and `toHslaString` methods will only include the alpha channel if it is not `1`. They will return `rgb(...)` and `hsl(...)` strings if the alpha is set to `1`. 
### Working with other colors:

```javascript
transition( othercolor, distance ) // the color distance ( 0.0 - 1.0 ) of the way between this color and othercolor
blend( othercolor ) // Will apply this color on top of the other color using alpha blending
is( othercolor ) // Will determine if this color is equal to all defined properties of othercolor
```

## jQuery.Color properties


## Internals on The Color Object
* Internally, RGBA values are stored as `color._rgba[0] = red, color._rgba[1] = green, color._rgba[2] = blue, color._rgba[3] = alpha`.  However, please remember there are nice convenient setters and getters for each of these properties.
* `undefined`/`null` values for colors indicate non-existence. This signals the `transition()` function to keep whatever value was set in the other end of the transition. For example, animating to `jQuery.Color([ 255, null, null, 1 ])` would only animate the red and alpha values of the color.

###`jQuery.Color.names`

A list of named colors is stored on the `jQuery.Color.names` object.  The value they contain should be parseable by `jQuery.Color()`. All names on this object should be lowercased.  I.E. `jQuery.Color("Red")` is the same as doing `jQuery.Color( jQuery.Color.names["red"] );`

There is also a named color `"_default"` which by default is white, this is used for situations where a color is unparseable.

###`"transparent"`

A special note about the color `"transparent"` - It returns `null` for red green and blue unless you specify colors for these values.

```javascript
jQuery.Color("#abcdef").transition("transparent", 0.5)
```

Animating to or from the value `"transparent"` will still use "#abcdef" for red green and blue.

##HSLA Support

If a color is created using any of the HSLA functions or parsers, it will keep the `_rgba` array up to date as well as having a `_hsla` array.  Once an RGBA operation is performed on HSLA, however, the `_hsla` cache is removed and all operations will continue based off of rgb (unless you go back into HSLA). The `._hsla` array follows the same format as `._rbga`, `[hue, saturation, lightness, alpha ]`.  If you need to build an HSLA color from an HSLA array, `jQuery.Color().hsla( array )` works for that purpose.

**Colors with 0 saturation, or 100%/0% lightness will be stored with a hue of 0**

##Extensibility

It is possible for you to add your own functions to the color object.  For instance, this function will tell you if its better to use black or white on a given background color.


```javascript
// method taken from https://gist.github.com/960189
jQuery.Color.fn.contrastColor = function() {
    var r = this._rgba[0], g = this._rgba[1], b = this._rgba[2];
    return (((r*299)+(g*587)+(b*144))/1000) >= 131.5 ? "black" : "white";
};

// usage examples:
jQuery.Color("#bada55").contrastColor(); // "black"
element.css( "color", jQuery.Color( element, "backgroundColor" ).contrastColor() );
```
