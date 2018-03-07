import { connect } from 'react-redux';
import NoTextbooks from '../components/NoTextbooks';

const mapStateToProps = state => (
  {
    TextbooksCollection: state.TextbooksCollection,
  }
);

const WrappedNoTextbooks = connect(
  mapStateToProps,
)(NoTextbooks);

export { WrappedNoTextbooks };
