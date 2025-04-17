import $ from 'jquery';
import _ from 'underscore';

'use strict';

/**
 * Video commands module.
 *
 * @constructor
 * @param {Object} state - The object containing the state of the video
 * @param {Object} i18n - The object containing strings with translations
 * @return {jQuery.Promise} - A resolved jQuery promise
 */
function VideoCommands(state, i18n) {
    if (!(this instanceof VideoCommands)) {
        return new VideoCommands(state, i18n);
    }

    _.bindAll(this, 'destroy');
    this.state = state;
    this.state.videoCommands = this;
    this.i18n = i18n;
    this.commands = [];
    this.initialize();

    return $.Deferred().resolve().promise();
}

VideoCommands.prototype = {
    /**
     * Initializes the module by loading commands and binding events.
     */
    initialize: function () {
        this.commands = this.getCommands();
        this.state.el.on('destroy', this.destroy);
    },

    /**
     * Cleans up the module by removing event handlers and deleting the instance.
     */
    destroy: function () {
        this.state.el.off('destroy', this.destroy);
        delete this.state.videoCommands;
    },

    /**
     * Executes a given command with optional arguments.
     *
     * @param {String} command - The name of the command to execute
     * @param {...*} args - Additional arguments to pass to the command
     */
    execute: function (command, ...args) {
        if (_.has(this.commands, command)) {
            this.commands[command].execute(this.state, ...args);
        } else {
            console.log(`Command "${command}" is not available.`);
        }
    },

    /**
     * Returns the available commands as an object.
     *
     * @return {Object} - A dictionary of available commands
     */
    getCommands: function () {
        const commands = {};
        const commandsList = [
            playCommand,
            pauseCommand,
            togglePlaybackCommand,
            toggleMuteCommand,
            toggleFullScreenCommand,
            setSpeedCommand,
            skipCommand,
        ];

        _.each(commandsList, (command) => {
            commands[command.name] = command;
        });

        return commands;
    },
};

/**
 * Command constructor.
 *
 * @constructor
 * @param {String} name - The name of the command
 * @param {Function} execute - The function to execute the command
 */
function Command(name, execute) {
    this.name = name;
    this.execute = execute;
}

// Individual command definitions
const playCommand = new Command('play', (state) => {
    state.videoPlayer.play();
});

const pauseCommand = new Command('pause', (state) => {
    state.videoPlayer.pause();
});

const togglePlaybackCommand = new Command('togglePlayback', (state) => {
    if (state.videoPlayer.isPlaying()) {
        pauseCommand.execute(state);
    } else {
        playCommand.execute(state);
    }
});

const toggleMuteCommand = new Command('toggleMute', (state) => {
    state.videoVolumeControl.toggleMute();
});

const toggleFullScreenCommand = new Command('toggleFullScreen', (state) => {
    state.videoFullScreen.toggle();
});

const setSpeedCommand = new Command(
    'speed',
    (state, speed) => {
        state.videoSpeedControl.setSpeed(state.speedToString(speed));
    }
);

const skipCommand = new Command('skip', (state, doNotShowAgain) => {
    if (doNotShowAgain) {
        state.videoBumper.skipAndDoNotShowAgain();
    } else {
        state.videoBumper.skip();
    }
});

export {VideoCommands};
