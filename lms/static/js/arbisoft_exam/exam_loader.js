;(function (define) {
    'use strict';
    define([
            'jquery',
            'js/arbisoft_exam/views/QuestionBlockView'
        ],
        function($, QuestionBlockView) {
            return function(items) {
                new QuestionBlockView(items);
            };
        }
    );
}).call(this, define || RequireJS.define);