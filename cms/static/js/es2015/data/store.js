import { createStore } from 'redux';
import { syncCollections } from 'backbone-redux';

import rootReducer from './reducers';

const StudioStore = createStore(
  () => {},
);

syncCollections({
  TextbooksCollection: window.models.TextbookCollection,
}, StudioStore);

export { StudioStore };
