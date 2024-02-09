import React from 'react';
import { Provider } from 'react-redux';

import store from './data/store';
import Main from './Main';

export const SkillAssessmentAdmin = props => (
    <Provider store={store}>
        <Main {...props} />
    </Provider>
);
