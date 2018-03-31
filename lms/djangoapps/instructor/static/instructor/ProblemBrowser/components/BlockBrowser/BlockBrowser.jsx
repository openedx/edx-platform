/* global gettext */
import * as React from 'react';
import * as PropTypes from 'prop-types';
import * as classNames from 'classnames';
import {Button} from '@edx/paragon';

const FAIcon = ({iconName, altlabel}) => (
    <div>
        <span className={classNames('icon fa', `fa-${iconName}`)} aria-hidden="true"/>
        <span className="sr">{altlabel}</span>
    </div>
);

const BlockList = ({blocks, selectedBlock, onSelectBlock, onChangeRoot}) => (
    <ul className="block-list">
        {blocks.map(block => (
            <li key={block.id}
                className={classNames(`block-type-${block.type}`, {selected: block.id === selectedBlock})}>
                <Button className={['block-name']}
                        onClick={() => onSelectBlock(block.id)} label={block.display_name}/>
                {block.children &&
                <Button onClick={() => onChangeRoot(block.id)}
                        label={<FAIcon iconName="arrow-right" altlabel={gettext('View child items')}/>}/>}
            </li>
        ))}
    </ul>
);

export const BlockBrowser = ({blocks, selectedBlock, onSelectBlock, onChangeRoot, className}) =>
    !!blocks && (
        <div className={classNames('block-browser', className)}>
            <div className="header">
                <Button disabled={!blocks.parent}
                        onClick={() => blocks.parent && onChangeRoot(blocks.parent)}
                        label={<FAIcon iconName="arrow-up" altlabel={gettext('Navigate up')}/>}/>
                <span className="title">
                    {gettext('Browsing')} {gettext(blocks.type)} "
                    <a href="#"
                       onClick={(event) => {
                           event.preventDefault();
                           onSelectBlock(blocks.id);
                       }}
                       title={gettext('Select') + ' '+ gettext(blocks.type)}>{blocks.display_name}</a>":
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
