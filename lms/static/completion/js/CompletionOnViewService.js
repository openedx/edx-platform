import { ViewedEventTracker } from './ViewedEvent';

const completedBlocksKeys = new Set();

export function markBlocksCompletedOnViewIfNeeded(runtime, containerElement) {
    const blockElements = $(containerElement).find(
        '.xblock-student_view[data-mark-completed-on-view-after-delay]',
    ).get();

    if (blockElements.length > 0) {
        const tracker = new ViewedEventTracker();

        blockElements.forEach((blockElement) => {
            const markCompletedOnViewAfterDelay = parseInt(
                blockElement.dataset.markCompletedOnViewAfterDelay, 10,
            );
            if (markCompletedOnViewAfterDelay >= 0) {
                tracker.addElement(blockElement, markCompletedOnViewAfterDelay);
            }
        });

        tracker.addHandler((blockElement, event) => {
            const blockKey = blockElement.dataset.usageId;
            if (blockKey && !completedBlocksKeys.has(blockKey)) {
                if (event.elementHasBeenViewed) {
                    $.ajax({
                        type: 'POST',
                        url: runtime.handlerUrl(blockElement, 'publish_completion'),
                        data: JSON.stringify({
                            completion: 1.0,
                        }),
                    }).then(
                        () => {
                            completedBlocksKeys.add(blockKey);
                            blockElement.dataset.markCompletedOnViewAfterDelay = 0;
                        },
                    );
                }
            }
        });
    }
}
