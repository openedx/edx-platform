(function(define, undefined) {
    'use strict';
    define(['jquery', 'annotator_1.2.9'], function($, Annotator) {
    /**
     * LlmSummarize plugin adds a button to the annotatorjs adder in order to
     * summarize the text selected and save as annotation.
     **/
        Annotator.Plugin.LlmSummarize = function() {
            Annotator.Plugin.apply(this, arguments);
        };

        $.extend(Annotator.Plugin.LlmSummarize.prototype, new Annotator.Plugin(), {
            pluginInit: function() {
                // Overrides of annotatorjs HTML/CSS to add summarize button.
                var style = document.createElement('style');
                style.innerHTML = `
                    .annotator-adder::before {
                        content: '';
                        width: 10px;
                        height: 10px;
                        background-color: white;
                        display: block;
                        position: absolute;
                        top: 100%;
                        left: 5px;
                        border-bottom: 1px solid gray;
                        border-right: 1px solid gray;
                        z-index: 0;
                        transform: translateY(-50%) rotate(45deg);
                    }

                    .annotator-adder button::before,
                    .annotator-adder button::after {
                        display: none !important;
                    }

                    .annotator-adder #annotateButton,
                    .annotator-adder #summarizeButton {
                        border: none !important;
                        background: rgb(0, 48, 87) !important;
                        box-shadow: none !important;
                        width: initial;
                        transition: color .1s;
                        text-indent: initial;
                        font-size: 20px;
                        padding: 0;
                        height: fit-content;
                        color: white;
                        border-radius: 5px;
                        padding-left: 5px;
                        padding-right: 5px;
                        font-weight: normal;
                        display: inline-block;
                    }

                    .annotator-adder #summarizeButton {
                        margin-left: 3px;
                    }

                    .annotator-adder button i.fa {
                        font-style: normal;
                    }

                    .annotator-adder {
                        width: fit-content;
                        height: fit-content;
                        padding: 5px;
                        background-color: white;
                        border: 1px solid gray;
                    }
                `;
                document.head.appendChild(style);
                var annotator = this.annotator;
                annotator.adder[0].children[0].id = 'annotateButton';
                annotator.adder[0].children[0].innerHTML = '<i class="fa fa-pencil" aria-hidden="true"></i>';
                annotator.adder[0].innerHTML += `
                <button class="summarize-button" id="summarizeButton" title="${gettext('Summarize text using AI.')}">
                    <i class="fa fa-star" aria-hidden="true"></i>
                </button>
                `;
            },
        });
    });
}).call(this, define || RequireJS.define);
