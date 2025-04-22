import { bindAll, once } from 'underscore';
import { Player as HTML5Player } from './02_html5_video.js';
import Hls from 'hls.js';

export class HLSVideoPlayer extends HTML5Player {
    constructor(el, config) {
        super();

        this.config = config;
        this.init(el, config);

        bindAll(this, 'playVideo', 'pauseVideo', 'onReady');

        // Handle unsupported HLS
        if (config.HLSOnlySources && !config.canPlayHLS) {
            this.showErrorMessage(null, '.video-hls-error');
            return;
        }

        // Setup on initialize
        const onInitialize = once(() => {
            console.log('[HLS Video]: HLS Player initialized');
            this.showPlayButton();
        });
        config.state.el.addEventListener('initialize', onInitialize);

        // Handle native Safari HLS
        if (config.browserIsSafari) {
            this.videoEl.setAttribute('src', config.videoSources[0]);
        } else {
            this.hls = new Hls({
                autoStartLoad: config.state.auto_advance ?? false
            });

            this.hls.loadSource(config.videoSources[0]);
            this.hls.attachMedia(this.video);

            this.hls.on(Hls.Events.ERROR, this.onError.bind(this));

            this.hls.on(Hls.Events.MANIFEST_PARSED, (event, data) => {
                console.log('[HLS Video]: MANIFEST_PARSED, qualityLevelsInfo:',
                    data.levels.map(level => ({
                        bitrate: level.bitrate,
                        resolution: `${level.width}x${level.height}`
                    }))
                );
                this.config.onReadyHLS?.();
            });

            this.hls.on(Hls.Events.LEVEL_SWITCHED, (event, data) => {
                const level = this.hls.levels[data.level];
                console.log('[HLS Video]: LEVEL_SWITCHED, qualityLevelInfo:', {
                    bitrate: level.bitrate,
                    resolution: `${level.width}x${level.height}`
                });
            });
        }
    }

    playVideo() {
        super.updatePlayerLoadingState('show');
        if (!this.config.browserIsSafari) {
            this.hls.startLoad();
        }
        super.playVideo();
    }

    pauseVideo() {
        super.pauseVideo();
        super.updatePlayerLoadingState('hide');
    }

    onPlaying() {
        super.onPlaying();
        super.updatePlayerLoadingState('hide');
    }

    onReady() {
        this.config.events.onReady?.(null);
    }

    onError(event, data) {
        if (!data.fatal) return;

        switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
                console.error('[HLS Video]: Fatal network error. Details:', data.details);
                this.hls.startLoad();
                break;
            case Hls.ErrorTypes.MEDIA_ERROR:
                console.error('[HLS Video]: Fatal media error. Details:', data.details);
                this.hls.recoverMediaError();
                break;
            default:
                console.error('[HLS Video]: Unrecoverable error. Details:', data.details);
                break;
        }
    }
}
