import * as TagCountView from 'js/views/tag_count';
import * as TagCountModel from 'js/models/tag_count';

// eslint-disable-next-line no-unused-expressions
'use strict';
export default function TagCountFactory(TagCountJson, el) {
    var model = new TagCountModel(TagCountJson, {parse: true});
    var tagCountView = new TagCountView({el, model});
    tagCountView.setupMessageListener();
    tagCountView.render();
}

export {TagCountFactory};
