import { combineReducers } from 'redux';

import ContextCourse from './ContextCourse';
import TextbooksFactory from './TextbooksFactory';

const rootReducer = combineReducers({
  ContextCourse,
  TextbooksFactory,
});

export default rootReducer;
