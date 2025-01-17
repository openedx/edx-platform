// eslint-disable-next-line max-classes-per-file
import React from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';
import {Button} from '@edx/paragon';
import $ from 'jquery';

class AnnouncementSkipLink extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            count: 0
        };
        $.get('/announcements/page/1')
            .then(data => {
                this.setState({
                    count: data.count
                });
            });
    }

    render() {
        return (<div>{'Skip to list of ' + this.state.count + ' announcements'}</div>);
    }
}

// eslint-disable-next-line react/prefer-stateless-function
class Announcement extends React.Component {
    render() {
        return (
            <div
                className="announcement"
                // eslint-disable-next-line react/no-danger
                dangerouslySetInnerHTML={{__html: this.props.content}}
            />
        );
    }
}

Announcement.propTypes = {
    content: PropTypes.string.isRequired,
};

class AnnouncementList extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            page: 1,
            announcements: [],
            // eslint-disable-next-line react/no-unused-state
            num_pages: 0,
            has_prev: false,
            has_next: false,
            start_index: 0,
            end_index: 0,
        };
    }

    retrievePage(page) {
        $.get('/announcements/page/' + page)
            .then(data => {
                this.setState({
                    announcements: data.announcements,
                    has_next: data.next,
                    has_prev: data.prev,
                    // eslint-disable-next-line react/no-unused-state
                    num_pages: data.num_pages,
                    count: data.count,
                    start_index: data.start_index,
                    end_index: data.end_index,
                    page: page
                });
            });
    }

    renderPrevPage() {
        this.retrievePage(this.state.page - 1);
    }

    renderNextPage() {
        this.retrievePage(this.state.page + 1);
    }

    // eslint-disable-next-line react/no-deprecated, react/sort-comp
    componentWillMount() {
        this.retrievePage(this.state.page);
    }

    render() {
        var children = this.state.announcements.map(
            // eslint-disable-next-line react/no-array-index-key
            (announcement, index) => <Announcement key={index} content={announcement.content} />
        );
        if (this.state.has_prev) {
            var prev_button = (
                <div>
                    <Button
                        className={['announcement-button', 'prev']}
                        onClick={() => this.renderPrevPage()}
                        label="← previous"
                    />
                    <span className="sr-only">{this.state.start_index + ' - ' + this.state.end_index + ') of ' + this.state.count}</span>
                </div>
            );
        }
        if (this.state.has_next) {
            var next_button = (
                <div>
                    <Button
                        className={['announcement-button', 'next']}
                        onClick={() => this.renderNextPage()}
                        label="next →"
                    />
                    <span className="sr-only">{this.state.start_index + ' - ' + this.state.end_index + ') of ' + this.state.count}</span>
                </div>
            );
        }
        return (
            <div className="announcements-list">
                {children}
                {prev_button}
                {next_button}
            </div>
        );
    }
}

export default class AnnouncementsView {
    constructor() {
        ReactDOM.render(
            <AnnouncementList />,
            document.getElementById('announcements'),
        );
        ReactDOM.render(
            <AnnouncementSkipLink />,
            document.getElementById('announcements-skip'),
        );
    }
}

export {AnnouncementsView, AnnouncementList, AnnouncementSkipLink};
