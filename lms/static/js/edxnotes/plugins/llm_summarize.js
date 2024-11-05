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
                const style = document.createElement('style');
                style.innerHTML = `
                    form.annotator-widget {
                        width: fit-content;
                    }

                    .annotator-invert-x .annotator-widget {
                        left: -18px;
                    }

                    @media (max-width: 768px) {
                        .annotator-widget textarea{
                            max-height: 380px;
                        }
                    }

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

                    // Defining content loader since fontawesome icons don't work
                    // inside the annotatorjs modal.
                    .loader {
                        width: 5em !important;
                        border-color: red !important;
                    }

                    @keyframes rotation {
                    0% {
                        transform: rotate(0deg);
                    }
                    100% {
                        transform: rotate(360deg);
                    }
                `;
                let annotator = this.annotator;
                document.head.appendChild(style);
                this.modifyDom(this.annotator);
                annotator.editor.options.llmSummarize = annotator.options.llmSummarize
                const summarizeButton = document.getElementById('summarizeButton');

                summarizeButton.addEventListener('click', function(ev) {
                    annotator.editor.options.isSummarizing = true;
                });
                annotator.subscribe('annotationEditorShown', this.handleSummarize);
                annotator.subscribe('annotationEditorHidden', this.cleanupSummarize);
            },
            handleSummarize: function (editor, annotation) {
                if (!editor.options || !editor.options.isSummarizing) return;

                function toggleLoader() {
                    const saveButton = document.querySelector('.annotator-controls .annotator-save');
                    const loaderWrapper = document.querySelector('.summarize-loader-wrapper');
                    editor.fields[0].element.children[0].classList.toggle('d-none');
                    loaderWrapper.classList.toggle('d-none');
                    saveButton.disabled = !saveButton.disabled;
                }

                const container = document.querySelector('.edx-notes-wrapper-content')
                const textAreaWrapper = editor.fields[0].element;
                const request = new Request('/pearson-core/llm-assistance/api/v0/summarize-text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': $.cookie('csrftoken'),
                    },
                    body: JSON.stringify({
                        text_to_summarize: annotation.quote,
                        course_id: editor.options && editor.options.llmSummarize && editor.options.llmSummarize.courseId,
                    }),
                });

                editor.fields[1].element.children[0].value = 'ai_summary';
                toggleLoader(editor);
                fetch(request)
                .then((response) => {
                    toggleLoader();
                    if (response.ok) return response.json();
                    throw new Error(gettext('There was an error while summarizing the content.'));
                })
                .then((data) => {
                    const annotatorEditor = editor.element[0];
                    const annotatorForm = annotatorEditor.children[0];
                    const controlsHeight = annotatorForm.children[1].offsetHeight;
                    const editorTop = parseInt(annotatorEditor.style.getPropertyValue('top'));
                    const tagFieldHeight = editor.fields[1].element.offsetHeight;
                    const textArea = textAreaWrapper.children[0];

                    annotatorEditor.style.left = '0px'
                    textArea.setAttribute('style', `
                        background-color: #f7f7f7 !important;
                        border-radius: 5px;
                        font-size: 12px !important;
                        width: ${container.offsetWidth}px !important;
                        height: auto;
                        overflow-y: auto;
                    `);
                    textArea.value = data.summary;
                    textArea.style.height = `${textArea.scrollHeight}px`;
                    textAreaWrapper.querySelector(".annotator-resize").remove();

                    if (annotatorForm.offsetHeight > editorTop){
                        textArea.style.maxHeight = `${editorTop - controlsHeight - tagFieldHeight}px`;
                    }

                    annotatorForm.setAttribute('tabindex', '-1');
                    annotatorForm.scrollIntoView({behavior: 'smooth', block: 'start'});
                })
                .catch((error) => {
                    alert(error.message);
                    editor.hide();
                });
            },
            cleanupSummarize: function(editor) {
                const textAreaWrapper = editor.fields[0].element;
                const textArea = textAreaWrapper.children[0]
                const loaderWrapper = document.querySelector('.summarize-loader-wrapper');

                textArea.value = '';
                textAreaWrapper.children[1].value = '';
                editor.options.isSummarizing = false;
                loaderWrapper.classList.add('d-none');
                textArea.removeAttribute('style');
            },
            modifyDom: function(annotator) {
                const textAreaWrapper = annotator.editor.fields[0].element;

                annotator.adder[0].children[0].id = 'annotateButton';
                annotator.adder[0].children[0].innerHTML = '<i class="fa fa-pencil" aria-hidden="true"></i>';
                annotator.adder[0].innerHTML += `
                <button class="summarize-button" id="summarizeButton" title="${gettext('Summarize text using AI.')}">
                    <i class="fa fa-star" aria-hidden="true"></i>
                </button>
                `;
                // Style is being defined here since classes styling not working
                // for this element.
                textAreaWrapper.innerHTML += `
                <div class="summarize-loader-wrapper d-none">
                    <span class="loader" style="
                        width: 1.2em;
                        height: 1.2em;
                        border: 3px solid rgb(0, 48, 87);
                        border-bottom-color: white;
                        border-radius: 50%;
                        display: inline-block;
                        box-sizing: border-box;
                        animation: rotation 3s linear infinite;
                        margin-right: 5px;
                        transform-origin: center;">
                    </span>
                    <span style="font-size: 1.2em; color: rgb(0, 48, 87);">
                        ${gettext('Summarizing...')}
                    </span>
                </div>`;
            },
        });
    });
}).call(this, define || RequireJS.define);
