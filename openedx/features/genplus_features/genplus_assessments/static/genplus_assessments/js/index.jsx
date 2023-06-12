import React from 'react';
import { Provider } from 'react-redux';

import store from './data/store';
import MainContainer from './MainContainer';

export const SkillAssessmentAdmin = props => (
    <Provider store={store}>
        <MainContainer {...props} />
    </Provider>
);
