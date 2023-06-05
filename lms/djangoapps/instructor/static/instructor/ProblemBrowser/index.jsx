import React from 'react';
import { Provider } from 'react-redux';

import store from './data/store';
import MainContainer from './components/Main/MainContainer';


export const ProblemBrowser = props => (
  <Provider store={store}>
    <MainContainer {...props} />
  </Provider>
);
