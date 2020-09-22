import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import store from './data/store';
import { VideoBlockEditorContainer } from './components/VideoBlockEditor';

window.videoBlockInit = (runtime, element) => {
  ReactDOM.render(
      <Provider store={store}>
        <VideoBlockEditorContainer xblockElement={element} runtime={runtime} />
      </Provider>,
      element,
  );
}

// We're not able to import the full instrumentation of the micro front end libraries because they'll cause problems
// with the installed JS depedencies here. These functions will exist in the CMS but may need to be provided in whatever
// target runtime this code is executed in. For now, ensure these exist in some fashion. Question: Is i18n available
// as a front-end XBlock runtime service? Should it be?
if (!window.gettext) {
  window.gettext = (val) => val
}

if (!window.ngettext) {
  window.ngettext = (singular, plural, num) => (num === 1 ? singular : plural );
}
