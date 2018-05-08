import store from './data/store';
import React from 'react';

import { Provider } from 'react-redux';

import MainContainer from './components/Main/MainContainer';

export const ProblemBrowser = props => (
  <Provider store={store}>
    <MainContainer {...props} />
  </Provider>
);
