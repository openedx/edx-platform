import React from 'react';
import { Provider } from 'react-redux';

import store from './data/store';
import CSVViewerContainer from './components/CSVViewer/CSVViewerContainer.jsx';

export const CSVViewer = props => (
  <Provider store={store}>
    <CSVViewerContainer {...props} />
  </Provider>
);
