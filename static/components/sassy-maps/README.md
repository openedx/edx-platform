# Sassy Maps [![Gem Version](https://badge.fury.io/rb/sassy-maps.png)](http://badge.fury.io/rb/sassy-maps) [![Build Status](https://travis-ci.org/Team-Sass/Sassy-Maps.png?branch=0.x.x)](https://travis-ci.org/Team-Sass/Sassy-Maps)
Sassy Maps adds a variety of functions aimed at helping you work with Sass 3.3 maps much easier.

## Table of Contents

1. [Requirements](#requirements)
2. [Installation](#installation)
3. [Using Sassy Maps](#using-sassy-maps)
4. [Functions](#functions)
5. [Optional Modules](#optional-modules)
	* [Memo](#memo)

## Requirements

Sassy Maps is a Sass extension, so you're going to need Sass installed. If you do not already have Sass installed, please read [Install Sass](http://sass-lang.com/install). Sassy Maps 0.3.x requires *Sass 3.3.0* or higher.

**It is HIGHLY RECOMMENDED that you run all Sass (or Compass if using it) commands through [Bundler](http://bundler.io/)**

If the compiler you are using is not compatible with the above minimum versions, it will not compile correctly.

**BE AWARE that CodeKit and most other GUI compilers *do not support Bundler* and are therefore NOT RECOMMENDED**

## Installation

The preferred way to install and use Sassy Maps is through Bundler. To do so, add the following to your Gemfile (Sass provided to ensure the correct versions are used):

```ruby
gem "sass", "~>3.3.0"
gem "sassy-maps", "~>0.3.2"
```

Once you have done so, run `bundle install` to install your dependencies, and remember to run all of your compilation through `bundle exec`.

You can also install Sassy Maps through [Bower](http://bower.io/) as it has no Ruby requirements. To do so, run the following command:

```bash
bower install sassy-maps --save-dev
```

*BE AWARE* that while you can install Sassy Maps through Bower, Sassy Maps still only works with Sass compilers that have full compatibility with Sass 3.3.x and greater. If using Compass, you are also going to need to add the folder using Compass's [`add_import_path`](http://compass-style.org/help/tutorials/configuration-reference/) config option instead of the standard `require`.

## Using Sassy Maps

If you already have a project made and you'd like to use Sassy Maps with it, add the following to your `config.rb` file:

`require 'sassy-maps'`

Then, add the following to your Sass file towards the top:

`@import "sassy-maps";`

## Functions

* `map-get-deep($map, $keys...)` - Returns the value of the final item in `$keys` from the map `$map`. Will return `null` if no value is present and will warn of errors in search (such as if an intermediate depth is `null` or not a `map`).
* `map-set($map, $key, $value)` - Returns a map that has the `$key` in `$map` set to the to given `$value`.
* `map-set-deep($map, $keys, $value)` - Returns a map that has the `$key` in `$map` set to the given `$value`. `$key` should be single-depth list of keys, for instance `map-set-deep($map, ('foo' 'bar' 'baz'), "Hello World")`.
* `map-to-string($map)` - Returns a string representation of the given `$map`.


## Optional Modules

Sassy Maps comes with optional modules that extend upon the base functionality of Sassy Maps to provide additional map-based functionality. The following are optional modules available with Sassy Maps:

* [Memo](#memo)

### Memo

Memo is a [Memoization](http://en.wikipedia.org/wiki/Memoization) framework for Sass. Designed with framework developers in mind, it makes it easy to store and retrieve the output of functions quickly and easily without needing to run the function again. For complex functions this should greatly speed up overall compilation time for repeat function calls with identical input.

To use Memo, simply include `@import "memo";` and you're good to go (normal [Sassy Maps installation](#installation) still applies). Memo comes with two functions:

* `memo-set($module, $key, $value)` - Sets a memoization `$key` to the given `$value` for the prescribed `$module` (framework). The function will return `true`. Also available as a mixin (`@include memo-set($module, $key, $value)`).
* `memo-get($module, $key)` - Returns the value of the memoization `$key` for the prescribed `$module`.

Using Memo is fairly simple, just check to see if there is a memoization value for your key (and it's not `null`); if there is, return that, if not, run through the function, set the memoization, and return that result. The following example stores whether Memo is available in a variable and uses the function name as the memoization module, but if building a framework such as [Breakpoint](http://github.com/team-sass/breakpoint), that framework should be the name of the memoization module.

```scss
$Memo-Exists: function-exists(memo-get) and function-exists(memo-set);

@function percentage($target, $context) {
  @if $Memo-Exists {
    $result: memo-get(percentage, $target $context);

    @if $result != null {
      @return $result;
    }
  }

  $result: $target / $context * 100%;

  @if $Memo-Exists {
    $holder: memo-set(percentage, $target $context, $result);
  }

  @return $result;
}

$half: percentage(20px, 40px); // No memoization exists, will run through the function
$half-again: percentage(20px, 40px); // Memoization exists, will just return that result
```
