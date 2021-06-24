

/**
 * Simple selector factory.
 * Takes a list of string keys, and returns a simple slector for each.
 *
 * @function
 * @param {Object|string[]} keys - If passed as object, Object.keys(keys) is used.
 * @return {Object} - object of `{[key]: ({key}) => key}`
 */
 const simpleSelectorFactory = (transformer, keys) => {
   const selKeys = Array.isArray(keys) ? keys : Object.keys(keys);
   return selKeys.reduce(
	  (obj, key) => ({
    ...obj, [key]: state => transformer(state)[key],
	  }),
	  { root: state => transformer(state) },
	);
 };
