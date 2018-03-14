import { createStore } from 'redux';
import { syncCollections } from 'backbone-redux';

const StudioStore = createStore(
  () => {},
);

syncCollections({
  TextbooksCollection: window.models.TextbookCollection,
}, StudioStore);

export { StudioStore }; // eslint-disable-line import/prefer-default-export
