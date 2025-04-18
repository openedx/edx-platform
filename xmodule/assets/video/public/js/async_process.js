/**
 * Provides a convenient way to process a large amount of data without UI blocking.
 * 
 * @param {Array} list - The array to process.
 * @param {Function} process - The function to execute on each item.
 * @returns {Promise<Array>} - Resolves with the processed array.
 */
export const AsyncProcess = {
    array(list, process) {
        // Validate input
        if (!Array.isArray(list)) {
            return Promise.reject(new Error('Input is not an array'));
        }

        if (typeof process !== 'function' || list.length === 0) {
            return Promise.resolve(list);
        }

        const MAX_DELAY = 50;
        const result = [];
        let index = 0;
        const len = list.length;

        const handler = (resolve) => {
            const start = Date.now();

            while (index < len && Date.now() - start < MAX_DELAY) {
                result[index] = process(list[index], index);
                index++;
            }

            if (index < len) {
                setTimeout(() => handler(resolve), 25);
            } else {
                resolve(result);
            }
        };

        return new Promise((resolve) => {
            setTimeout(() => handler(resolve), 25);
        });
    }
};
