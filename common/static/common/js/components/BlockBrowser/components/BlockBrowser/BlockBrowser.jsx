/* global gettext */
import { Button, Icon } from '@edx/paragon';
import classNames from 'classnames';
import PropTypes from 'prop-types';
import React from 'react';

const RightIcon = (
    <Icon
        className={['fa', 'fa-arrow-right']}
        screenReaderText={gettext('View child items')}
    />
);

const UpIcon = (
    <Icon
        className={['fa', 'fa-arrow-up']}
        screenReaderText={gettext('Navigate up')}
    />
);

const BLOCK_TYPE_NAME = {
    course: 'Course',
    chapter: 'Section',
    sequential: 'Sub-section',
    vertical: 'Unit',
};

const BlockType = PropTypes.shape({
    children: PropTypes.array,
    display_name: PropTypes.string.isRequired,
    id: PropTypes.string.isRequired,
    parent: PropTypes.string,
    type: PropTypes.string.isRequired,
});

export const BlockList = ({ blocks, selectedBlock, onSelectBlock, onChangeRoot }) => (
    <ul className="block-list">
        {blocks.map(block => (
            <li
                key={block.id}
                className={classNames(`block-type-${block.type}`, { selected: block.id === selectedBlock })}
            >
                <Button
                    className={['block-name']}
                    onClick={() => onSelectBlock(block.id)}
                    label={block.display_name}
                />
                {block.children &&
        <Button
            onClick={() => onChangeRoot(block.id)}
            label={RightIcon}
        />
                }
            </li>
        ))}
    </ul>
);

BlockList.propTypes = {
    blocks: PropTypes.arrayOf(BlockType),
    selectedBlock: PropTypes.string,
    onSelectBlock: PropTypes.func.isRequired,
    onChangeRoot: PropTypes.func.isRequired,
};

BlockList.defaultProps = {
    blocks: null,
    selectedBlock: null,
};


export const BlockBrowser = ({ blocks, selectedBlock, onSelectBlock, onChangeRoot, className }) =>
    !!blocks && (
        <div className={classNames('block-browser', className)}>
            <div className="header">
                <Button
                    disabled={!blocks.parent}
                    onClick={() => blocks.parent && onChangeRoot(blocks.parent)}
                    label={UpIcon}
                />
                <span className="title">
                    {gettext('Browsing')} {gettext(BLOCK_TYPE_NAME[blocks.type])} &quot;
                    <a
                        href="#_"
                        onClick={(event) => {
                            event.preventDefault();
                            onSelectBlock(blocks.id);
                        }}
                        title={`${gettext('Select')} ${gettext(BLOCK_TYPE_NAME[blocks.type])}`}
                    >
                        {blocks.display_name}
                    </a>&quot;:
                </span>
            </div>
            <BlockList
                blocks={blocks.children}
                selectedBlock={selectedBlock}
                onSelectBlock={onSelectBlock}
                onChangeRoot={onChangeRoot}
            />
        </div>
    );

BlockBrowser.propTypes = {
    blocks: BlockType,
    selectedBlock: PropTypes.string,
    onSelectBlock: PropTypes.func.isRequired,
    onChangeRoot: PropTypes.func.isRequired,
};

BlockBrowser.defaultProps = {
    blocks: null,
    selectedBlock: null,
};
