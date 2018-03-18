import * as React from 'react';
import * as PropTypes from 'prop-types';
import * as classnames from 'classnames';


const BlockList = ({blocks, selectedBlock, onSelectBlock, onChangeRoot}) => (
    <ul className="block-list">
        {blocks.map(block => (
            <li key={block.id}
                className={classnames(`block-type-${block.type}`, {selected: block.id === selectedBlock})}>
                <button className="block-name" onClick={() => onSelectBlock(block.id)}>
                    {block.display_name}
                </button>
                {block.children &&
                <button className="block-child" onClick={() => onChangeRoot(block.id)}>&gt;</button>}
            </li>
        ))}
    </ul>
);

export const BlockBrowser = ({blocks, selectedBlock, onSelectBlock, onChangeRoot, className}) =>
    !!blocks && (
        <div className={classnames("block-browser", className)}>
            <div className="header">
                <button className="block-child"
                        onClick={() => blocks.parent && onChangeRoot(blocks.parent)}>
                    ^
                </button>
                <span className="block-type">{blocks.type}: </span>
                <span className="block-name">{blocks.display_name}</span>
            </div>
            <BlockList blocks={blocks.children}
                       selectedBlock={selectedBlock}
                       onSelectBlock={onSelectBlock}
                       onChangeRoot={onChangeRoot}/>
            </div>
    );

BlockBrowser.propTypes = {
    blocks: PropTypes.object,
    selectedBlock: PropTypes.string,
    onSelectBlock: PropTypes.func.isRequired,
    onChangeRoot: PropTypes.func.isRequired,
};
