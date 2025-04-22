/**
 * Handles video completion logic.
 * @param {Object} state - The shared video state object.
 * @returns {Promise<void>}
 */

const VideoCompletionHandler = (state) => {
    const handler = new CompletionHandler(state);
    state.completionHandler = handler;
    return Promise.resolve();
}

class CompletionHandler {
    constructor(state) {
        this.state = state;
        this.el = state.el; // Should be a DOM element
        this.lastSentTime = undefined;
        this.isComplete = false;
        this.completionPercentage = state.config.completionPercentage;
        this.startTime = state.config.startTime;
        this.endTime = state.config.endTime;
        this.isEnabled = state.config.completionEnabled;

        if (this.endTime) {
            this.completeAfterTime = this.calculateCompleteAfterTime(this.startTime, this.endTime);
        }

        if (this.isEnabled) {
            this.bindHandlers();
        }
    }

    destroy() {
        this.el.removeEventListener('timeupdate', this._onTimeUpdate);
        this.el.removeEventListener('ended', this._onEnded);
        this.el.removeEventListener('metadata_received', this._onMetadataReceived);
        delete this.state.completionHandler;
    }

    bindHandlers() {
        this._onEnded = this.handleEnded.bind(this);
        this._onTimeUpdate = (e) => this.handleTimeUpdate(e.detail);
        this._onMetadataReceived = this.checkMetadata.bind(this);

        this.el.addEventListener('ended', this._onEnded);
        this.el.addEventListener('timeupdate', this._onTimeUpdate);
        this.el.addEventListener('metadata_received', this._onMetadataReceived);
    }

    handleEnded() {
        if (!this.isComplete) {
            this.markCompletion();
        }
    }

    handleTimeUpdate(currentTime) {
        if (this.isComplete) return;

        const now = Date.now() / 1000;

        if (
            this.lastSentTime !== undefined &&
            currentTime - this.lastSentTime < this.repostDelaySeconds()
        ) {
            return;
        }

        if (this.completeAfterTime === undefined) {
            const duration = this.state.videoPlayer.duration?.();
            if (!duration) return;
            this.completeAfterTime = this.calculateCompleteAfterTime(this.startTime, duration);
        }

        if (currentTime > this.completeAfterTime) {
            this.markCompletion(currentTime);
        }
    }

    checkMetadata() {
        const metadata = this.state.metadata?.[this.state.youtubeId()];
        const ytRating = metadata?.contentRating?.ytRating;

        if (ytRating === 'ytAgeRestricted' && !this.isComplete) {
            this.markCompletion();
        }
    }

    async markCompletion(currentTime) {
        this.isComplete = true;
        this.lastSentTime = currentTime;

        this.el.dispatchEvent(new CustomEvent('complete'));

        const url = this.state.config.publishCompletionUrl;

        if (!url) {
            console.warn('publishCompletionUrl not defined');
            return;
        }

        try {
            const res = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ completion: 1.0 })
            });

            if (!res.ok) {
                const error = await res.json();
                throw new Error(error?.error || 'Unknown error');
            }

            this.el.removeEventListener('timeupdate', this._onTimeUpdate);
            this.el.removeEventListener('ended', this._onEnded);
        } catch (err) {
            console.warn('Failed to submit completion:', err.message);
            this.isComplete = false;
        }
    }

    calculateCompleteAfterTime(startTime, endTime) {
        return startTime + (endTime - startTime) * this.completionPercentage;
    }

    repostDelaySeconds() {
        return 3.0;
    }
}

export { VideoCompletionHandler }