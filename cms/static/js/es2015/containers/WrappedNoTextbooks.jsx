import { connect } from 'react-redux';
import NoTextbooks from '../components/NoTextbooks';

const mapStateToProps = state => (
  {
    TextbookCollection: state.TextbookCollection.entities,
  }
);

const WrappedNoTextbooks = connect(
  mapStateToProps,
)(NoTextbooks);

export { WrappedNoTextbooks }; // eslint-disable-line import/prefer-default-export
