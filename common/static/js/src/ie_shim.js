/*
 * This file is used for keeping compatibility with Internet Explorer.
 * As starting with IE10, the conditional comments are not supported, this file
 * will always be loaded whether the browser is IE or not. Therefore, the code
 * here should not make any assumption and should always detect the execution
 * conditions itself.
 */

// Shim name: Create the attribute of 'window.location.origin'
// IE version: 11 or earlier, 12 or later not tested
// Internet Explorer does not have built-in property 'window.location.origin',
// we need to create one here as some vendor code such as TinyMCE uses this.
if (!window.location.origin) {
    window.location.origin = window.location.protocol + '//' + window.location.hostname
                           + (window.location.port ? ':' + window.location.port : '');
}
