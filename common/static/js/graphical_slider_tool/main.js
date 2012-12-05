// Wrapper for RequireJS. It will make the standard requirejs(), require(), and
// define() functions from Require JS available inside the anonymous function.
(function (requirejs, require, define) {

// For documentation please check:
//     http://requirejs.org/docs/api.html
requirejs.config({
    // Because require.js is included as a simple <script> tag (and is
    // forcefully namespaced) it does not get it's configuration from a
    // predefined 'data-main' attribute. Therefore, from the start, it assumes
    // that the 'baseUrl' is the same directory that require.js itself is
    // contained in - i.e. in '/static/js/vendor'. So, we must specify a
    // correct 'baseUrl'.
    //
    // Require JS initially searches this directory for all of the specified
    // dependencies. If the dependency is
    //
    //     'sylvester'
    //
    // then it will try to get it from
    //
    //     baseUrl + '/' + 'sylvester' + '.js'
    //
    // If the dependency is
    //
    //     'vendor_libs/sylvester'
    //
    // then it will try to get it from
    //
    //     baseUrl + '/' + 'vendor_libs/sylvester' + '.js'
    //
    // This means two things. One - you can use sub-folders to separate your
    // code. Two - don't include the '.js' suffix when specifying a dependency.
    //
    // For documentation please check:
    //     http://requirejs.org/docs/api.html#config-baseUrl
    'baseUrl': '/static/js/graphical_slider_tool',

    // If you need to load from another path, you can specify it here on a
    // per-module basis. For example you can specify CDN sources here, or
    // absolute paths that lie outside of the 'baseUrl' directory.
    //
    // For documentation please check:
    //     http://requirejs.org/docs/api.html#config-paths
    'paths': {

    },

    // Since all of the modules that we require are not aware of our custom
    // RequireJS solution, that means all of them will be working in the
    // "old mode". I.e. they will populate the global namespace with their
    // module object.
    //
    // For each module that we will use, we will specify what is exports into
    // the global namespace, and, if necessary, other modules that it depends.
    // on. Module dependencies  (downloading them, inserting into the document,
    // etc.) are handled by RequireJS.
    //
    // For documentation please check:
    //     http://requirejs.org/docs/api.html#config-shim
    'shim': {

    }
}); // End-of: requirejs.config({

// Start the main app logic.
requirejs(['gst_module'], function (GstModule) {
    console.log(GstModule);
}); // End-of: requirejs(['gst_module'], function (GstModule)

// End of wrapper for RequireJS. As you can see, we are passing
// namespaced Require JS variables to an anonymous function. Within
// it, you can use the standard requirejs(), require(), and define()
// functions as if they were in the global namespace.
}(RequireJS.requirejs, RequireJS.require, RequireJS.define)); // End-of: (function (requirejs, require, define)
