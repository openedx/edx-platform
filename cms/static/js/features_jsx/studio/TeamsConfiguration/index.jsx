import React from 'react';
import { Provider } from 'react-redux';
import TeamsConfigurationContainer from './components/TeamsConfiguration/TeamsConfigurationContainer';
import store from './data/store';
import TeamSet from './components/TeamsConfiguration/TeamSet';

console.log('TeamSet', TeamSet);

export const TeamsConfiguration = props => (
  <Provider store={store}>
    <TeamsConfigurationContainer {...props} />
  </Provider>
);
