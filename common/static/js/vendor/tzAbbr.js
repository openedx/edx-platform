/* Friendly timezone abbreviations in client-side JavaScript

`tzAbbr()` or `tzAbbr(new Date(79,5,24))`
=> "EDT", "CST", "GMT", etc.!

There's no 100% reliable way to get friendly timezone names in all
browsers using JS alone, but this tiny function scours a
stringified date as best it can and returns `null` in the few cases
where no friendly timezone name is found (so far, just Opera).

Device tested & works in:
* IE 6, 7, 8, and 9 (latest versions of all)
* Firefox 3 [through] 16 (16 = latest version to date)
* Chrome 22 (latest version to date)
* Safari 6 (latest version to date)
* Mobile Safari on iOS 5 & 6
* Android 4.0.3 stock browser
* Android 2.3.7 stock browser
* IE Mobile 9 (WP 7.5)

Known to fail in:
* Opera 12 (desktop, latest version to date)

For Opera, I've included (but commented out) a workaround spotted
on StackOverflow that returns a GMT offset when no abbreviation is
found. I haven't found a decent workaround.

If you find any other cases where this method returns null or dodgy
results, please say so in the comments; even if we can't find a
workaround it'll at least help others determine if this approach is
suitable for their project!
*/
define([], function() {
  return function (dateInput) {
    var dateObject = dateInput || new Date(),
      dateString = dateObject + "",
      tzAbbr = (
        // Works for the majority of modern browsers
        dateString.match(/\(([^\)]+)\)$/) ||
        // IE outputs date strings in a different format:
        dateString.match(/([A-Z]+) [\d]{4}$/)
      );

    if (tzAbbr) {
      // Old Firefox uses the long timezone name (e.g., "Central
      // Daylight Time" instead of "CDT")
      tzAbbr = tzAbbr[1].match(/[A-Z]/g).join("");
    }

    // Uncomment these lines to return a GMT offset for browsers
    // that don't include the user's zone abbreviation (e.g.,
    // "GMT-0500".) I prefer to have `null` in this case, but
    // you may not!
    // First seen on: http://stackoverflow.com/a/12496442
    // if (!tzAbbr && /(GMT\W*\d{4})/.test(dateString)) {
    //  return RegExp.$1;
    // }

    return tzAbbr;
  };
});
