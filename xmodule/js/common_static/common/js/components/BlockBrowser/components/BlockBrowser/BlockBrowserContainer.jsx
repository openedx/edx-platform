import { connect } from 'react-redux';
import { changeRoot } from '../../data/actions/courseBlocks';
import { getActiveBlockTree } from '../../data/selectors/index';
import { BlockBrowser } from './BlockBrowser';

const mapStateToProps = state => ({
  blocks: getActiveBlockTree(state),
  selectedBlock: state.selectedBlock,
});


const mapDispatchToProps = dispatch => ({
  onChangeRoot: blockId => dispatch(changeRoot(blockId)),
});


const BlockBrowserContainer = connect(
  mapStateToProps,
  mapDispatchToProps,
)(BlockBrowser);

export default BlockBrowserContainer;
