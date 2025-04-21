'use strict';
import $ from 'jquery';

/**
 * VideoBumper module.
 *
 * @param {Function} player - The player factory function.
 * @param {Object} state - Object containing the video state and DOM refs.
 * @returns {Promise} A jQuery promise that resolves when bumper ends.
 */
export default class VideoBumper {
    constructor(player, state) {
        this.dfd = $.Deferred();
        this.element = state.el;
        this.player = player;
        this.state = state;
        this.doNotShowAgain = false;
        this.maxBumperDuration = 35; // seconds

        // Attach bumper instance to state for external reference
        this.state.videoBumper = this;

        // Style and initialize
        this.element.addClass('is-bumper');

        // Bind class methods to `this`
        this.showMainVideoHandler = this.showMainVideoHandler.bind(this);
        this.destroy = this.destroy.bind(this);
        this.skipByDuration = this.skipByDuration.bind(this);
        this.destroyAndResolve = this.destroyAndResolve.bind(this);

        this.bindHandlers();
        this.initialize();
    }

    initialize() {
        this.player();
    }

    getPromise() {
        return this.dfd.promise();
    }

    showMainVideoHandler() {
        this.state.storage.setItem('isBumperShown', true);
        setTimeout(() => {
            this.saveState();
            this.showMainVideo();
        }, 20);
    }

    destroyAndResolve() {
        this.destroy();
        this.dfd.resolve();
    }

    showMainVideo() {
        if (this.state.videoPlayer) {
            this.destroyAndResolve();
        } else {
            this.element.on('initialize', this.destroyAndResolve);
        }
    }

    skip() {
        this.element.trigger('skip', [this.doNotShowAgain]);
        this.showMainVideoHandler();
    }

    skipAndDoNotShowAgain() {
        this.doNotShowAgain = true;
        this.skip();
    }

    skipByDuration(event, time) {
        if (time > this.maxBumperDuration) {
            this.element.trigger('ended');
        }
    }

    bindHandlers() {
        this.element.on('ended error', this.showMainVideoHandler);
        this.element.on('timeupdate', this.skipByDuration);
    }

    saveState() {
        const info = { bumper_last_view_date: true };
        if (this.doNotShowAgain) {
            Object.assign(info, { bumper_do_not_show_again: true });
        }

        if (this.state.videoSaveStatePlugin) {
            this.state.videoSaveStatePlugin.saveState(true, info);
        }
    }

    destroy() {
        this.element.off('ended error', this.showMainVideoHandler);
        this.element.off({
            timeupdate: this.skipByDuration,
            initialize: this.destroyAndResolve
        });
        this.element.removeClass('is-bumper');

        if (typeof this.state.videoPlayer?.destroy === 'function') {
            this.state.videoPlayer.destroy();
        }

        delete this.state.videoBumper;
    }
}
