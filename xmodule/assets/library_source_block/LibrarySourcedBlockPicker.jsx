/* globals gettext */

import 'whatwg-fetch';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'underscore';
import styles from './style.css';

class LibrarySourcedBlockPicker extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            libraries: [],
            xblocks: [],
            searchedLibrary: '',
            libraryLoading: false,
            xblocksLoading: false,
            selectedLibrary: undefined,
            selectedXblocks: new Set(this.props.selectedXblocks),
        };
        this.onLibrarySearchInput = this.onLibrarySearchInput.bind(this);
        this.onXBlockSearchInput = this.onXBlockSearchInput.bind(this);
        this.onLibrarySelected = this.onLibrarySelected.bind(this);
        this.onXblockSelected = this.onXblockSelected.bind(this);
        this.onDeleteClick = this.onDeleteClick.bind(this);
    }

    componentDidMount() {
        this.fetchLibraries();
    }

    fetchLibraries(textSearch='', page=1, append=false) {
        this.setState({
            libraries: append ? this.state.libraries : [],
            libraryLoading: true,
        }, async function() {
            try {
                let res = await fetch(`/api/libraries/v2/?pagination=true&page=${page}&text_search=${textSearch}`);
                res = await res.json();
                this.setState({
                    libraries: this.state.libraries.concat(res.results),
                    libraryLoading: false,
                }, () => {
                    if (res.next) {
                        this.fetchLibraries(textSearch, page+1, true);
                    }
                });
            } catch (error) {
                $('#library-sourced-block-picker').trigger('error', {
                    title: 'Could not fetch library',
                    message: error,
                });
                this.setState({
                    libraries: [],
                    libraryLoading: false,
                });
            }
        });
    }

    fetchXblocks(library, textSearch='', page=1, append=false) {
        this.setState({
            xblocks: append ? this.state.xblocks : [],
            xblocksLoading: true,
        }, async function() {
            try {
                let res = await fetch(`/api/libraries/v2/${library}/blocks/?pagination=true&page=${page}&text_search=${textSearch}`);
                res = await res.json();
                this.setState({
                    xblocks: this.state.xblocks.concat(res.results),
                    xblocksLoading: false,
                }, () => {
                    if (res.next) {
                        this.fetchXblocks(library, textSearch, page+1, true);
                    }
                });
            } catch (error) {
                $('#library-sourced-block-picker').trigger('error', {
                    title: 'Could not fetch xblocks',
                    message: error,
                });
                this.setState({
                    xblocks: [],
                    xblocksLoading: false,
                });
            }
        });
    }

    onLibrarySearchInput(event) {
        event.persist()
        this.setState({
            searchedLibrary: event.target.value,
        });
        if (!this.debouncedFetchLibraries) {
            this.debouncedFetchLibraries =  _.debounce(value => {
                this.fetchLibraries(value);
            }, 300);
        }
        this.debouncedFetchLibraries(event.target.value);
    }

    onXBlockSearchInput(event) {
        event.persist()
        if (!this.debouncedFetchXblocks) {
            this.debouncedFetchXblocks =  _.debounce(value => {
                this.fetchXblocks(this.state.selectedLibrary, value);
            }, 300);
        }
        this.debouncedFetchXblocks(event.target.value);
    }

    onLibrarySelected(event) {
        this.setState({
            selectedLibrary: event.target.value,
        });
        this.fetchXblocks(event.target.value);
    }

    onXblockSelected(event) {
        let state = new Set(this.state.selectedXblocks);
        if (event.target.checked) {
            state.add(event.target.value);
        } else {
            state.delete(event.target.value);
        }
        this.setState({
            selectedXblocks: state,
        }, this.updateList);
    }

    onDeleteClick(event) {
        let value;
        if (event.target.tagName == 'SPAN') {
            value = event.target.parentElement.dataset.value;
        } else {
            value = event.target.dataset.value;
        }
        let state = new Set(this.state.selectedXblocks);
        state.delete(value);
        this.setState({
            selectedXblocks: state,
        }, this.updateList);
    }

    updateList(list) {
        $('#library-sourced-block-picker').trigger('selected-xblocks', {
            sourceBlockIds: Array.from(this.state.selectedXblocks),
        });
    }

    render() {
        return (
            <section>
                <div className="container-message wrapper-message">
                    <div className="message has-warnings" style={{margin: 0, color: "white"}}>
                        <p className="warning">
                            <span className="icon fa fa-warning" aria-hidden="true"></span>
                Hitting 'Save and Import' will import the latest versions of the selected blocks, overwriting any changes done to this block post-import.
                        </p>
                    </div>
                </div>
                <div style={{display: "flex", flexDirection: "row", justifyContent: "center"}}>
                    <div className={styles.column}>
                        <input type="text" className={[styles.search]} aria-label="Search for library" placeholder="Search for library" label="Search for library" name="librarySearch" onChange={this.onLibrarySearchInput}/>
                        <div className={styles.elementList} onChange={this.onLibrarySelected}>
                            {
                                this.state.libraries.map(lib => (
                                    <div key={lib.id} className={styles.element}>
                                        <input id={`sourced-library-${lib.id}`} type="radio" value={lib.id} name="library"/>
                                        <label className={styles.elementItem} htmlFor={`sourced-library-${lib.id}`}>{lib.title}</label>
                                    </div>
                                ))
                            }
                            { this.state.libraryLoading && <span>{gettext('Loading...')}</span> }
                        </div>
                    </div>
                    <div className={styles.column}>
                        <input type="text" className={[styles.search]} aria-label="Search for XBlocks" placeholder="Search for XBlocks" name="xblockSearch" onChange={this.onXBlockSearchInput} disabled={!this.state.selectedLibrary || this.state.libraryLoading}/>
                        <div className={styles.elementList} onChange={this.onXblockSelected}>
                            {
                                this.state.xblocks.map(block => (
                                    <div key={block.id} className={styles.element}>
                                        <input id={`sourced-block-${block.id}`} type="checkbox" value={block.id} name="block" checked={this.state.selectedXblocks.has(block.id)} readOnly/>
                                        <label className={styles.elementItem} htmlFor={`sourced-block-${block.id}`}>{block.display_name} ({block.id})</label>
                                    </div>
                                ))
                            }
                            { this.state.xblocksLoading && <span>{gettext('Loading...')}</span> }
                        </div>
                    </div>
                    <div className={styles.column}>
                        <h4 className={styles.selectedBlocks}>{gettext('Selected blocks')}</h4>
                        <ul>
                            {
                                Array.from(this.state.selectedXblocks).map(block => (
                                    <li key={block} className={styles.element} style={{display: "flex"}}>
                                        <label className={styles.elementItem}>
                                            {block}
                                        </label>
                                        <button className={[styles.remove]} data-value={block} onClick={this.onDeleteClick} aria-label="Remove block">
                                            <span aria-hidden="true" className="icon fa fa-times"></span>
                                        </button>
                                    </li>
                                ))
                            }
                        </ul>
                    </div>
                </div>
            </section>
        );
    }
}

LibrarySourcedBlockPicker.propTypes = {
    selectedXblocks: PropTypes.array,
};

LibrarySourcedBlockPicker.defaultProps = {
    selectedXblocks: [],
};

export { LibrarySourcedBlockPicker }; // eslint-disable-line import/prefer-default-export
