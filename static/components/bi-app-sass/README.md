## Bi App Sass
bi-app lets you write your stylesheets once, and have them compiled into 2 different stylesheets one for `left-to-right` layout, and the other for `right-to-left` layouts

## Why
usually when writing stylesheets for bi-directional sites/apps, both `ltr` & `rtl` stylesheets mostly will look the same, except for direction related properties (`float, text-align, padding, margin ..etc` ), so when you write a `float: left` in some `ltr` stylesheet, you'll have to write it again as `float: right` for the `rtl` one

when using **bi-app-sass** , all you have to do is to write your stylesheets once using a predefined mixins for those direction related properties, and once you compile your stylesheets, you'll have a ready two stylesheets for your bi-directional app

## How to use it
create three Sass files
```js
app-ltr.scss    // ltr interface to be compiled
app-rtl.scss    // rtl interface
_app.scss       // private file where you will write your styles (won't be compiled)
```
in the `app-ltr.scss` only include the following
```css
@import 'bi-app-ltr';
@import 'app';
```

same for `app-rtl.scss`
```css
@import 'bi-app-rtl';
@import 'app';
```

now you can write your styles in `_app.scss`, using bi-app mixins, as you were styling for only `ltr` layouts, and the `rtl` styles will be compiled automatically!
```css
.foo {
  display: block;
  @include float(left);
  @include border-left(1px solid white);
  ...
}
```

the result will be ..

in `app-ltr.css`
```css
.foo {
  display: block;
  float: left;
  border-left: 1px solid white;
  ...
}
```

in `app-rtl.css`
```css
.foo {
  display: block;
  float: right;
  border-right: 1px solid white;
  ...
}
```
## Installing via npm
```
npm install bi-app-sass
```

## Installing via Bower
```
bower install bi-app-sass
```

## Installing via Yeoman
```
yeoman install bi-app-sass
```

## Reference
a list of available mixins for CSS properties
```
// padding
padding-left(distance)
padding-right(distance)
padding(top, right, bottom, left)

// margin
margin-left(distance)
margin-right(distance)
margin(top, right, bottom, left)

// float
float(direction)			// left || right || none

// text align
text-align(direction)		// left || right || center

// clear
clear(direction)			// left || right || both

// left / right
left(distance)
right(distance)

// border
border-left(border-style)
border-right(border-style)

// border width
border-left-width(width)
border-right-width(width)
border-width(top, right, bottom, left)

// border style
border-left-style(style)
border-right-style(style)
border-style(top, right, bottom, left)

// border color
border-left-color(color)
border-right-color(color)
border-color(top, right, bottom, left)

// border radius
border-top-left-radius(radius)
border-top-right-radius(radius)
border-bottom-left-radius(radius)
border-bottom-right-radius(radius)
border-left-radius(radius)
border-right-radius(radius)
border-top-radius(radius)
border-bottom-radius(radius)
border-radius(topLeft, topRight, bottomRight, bottomLeft)

// ltr / rtl contents
rtl
ltr
```

## Handling Special Cases

whenever you face a special case, the `rtl` & `ltr` mixins will give you hand :)

```
.some-class {
    @include rtl {
      // what you write here, will appear only in rtl stylesheets
      background-image: url('rtl/some-image.jpg');
      background-position: -10px 30px;
    }

    @include ltr {
      background-image: url('ltr/some-image.jpg');
      background-position: 100% 50%;
    }
}
```

## Credits
created by Anas Nakawa [github](//github.com/anasnakawa), [twitter](//twitter.com/anasnakawa),  
inspired by Victor Zamfir [github](//github.com/viczam), [Victor Zamfir](//twitter.com/victorzamfir)

## License
Released under the [MIT License](http://www.opensource.org/licenses/mit-license.php)
