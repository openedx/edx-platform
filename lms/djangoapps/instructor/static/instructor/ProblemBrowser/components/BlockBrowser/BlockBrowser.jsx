/* global gettext */
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
                <button className="block-child" onClick={() => onChangeRoot(block.id)}>
                    <span className="icon fa fa-arrow-right" aria-hidden="true"/>
                    <span className="sr">{gettext('View child items')}</span>
                </button>}
            </li>
        ))}
    </ul>
);

export const BlockBrowser = ({blocks, selectedBlock, onSelectBlock, onChangeRoot, className}) =>
    !!blocks && (
        <div className={classnames("block-browser", className)}>
            <div className="header">
                <button className="block-parent"
                        disabled={!blocks.parent}
                        onClick={() => blocks.parent && onChangeRoot(blocks.parent)}>
                    <span className="icon fa fa-arrow-up" aria-hidden="true"/>
                    <span className="sr">{gettext('Navigate up')}</span>
                </button>
                <span className="title">
                    {gettext(`Browsing ${blocks.type}`)} "{blocks.display_name}":
                </span>
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
