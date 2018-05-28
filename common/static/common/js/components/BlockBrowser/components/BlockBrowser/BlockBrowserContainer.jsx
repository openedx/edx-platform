import {connect} from 'react-redux';

import {BlockBrowser} from './BlockBrowser.jsx';
import {changeRoot} from "../../data/actions/courseBlocks";
import {getActiveBlockTree} from '../../data/selectors/index';

const mapStateToProps = state => ({
    blocks: getActiveBlockTree(state),
    selectedBlock: state.selectedBlock
});


const mapDispatchToProps = dispatch => ({
    onChangeRoot: blockId => dispatch(changeRoot(blockId)),
});


export const BlockBrowserContainer = connect(
    mapStateToProps,
    mapDispatchToProps,
)(BlockBrowser);
