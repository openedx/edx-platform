import React from 'react';

import {Provider} from 'react-redux';
import store from 'BlockBrowser/data/store';

import MainContainer from './components/Main/MainContainer.jsx';

export const ProblemBrowser = props => (
    <Provider store={store}>
        <MainContainer {...props} />
    </Provider>
);
