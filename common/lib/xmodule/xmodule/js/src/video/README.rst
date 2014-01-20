Video player persists some user preferences between videos and these
preferences are stored on server.

Content for sequential positions is loaded just once on page load and is not
updated when the user navigates between sequential positions. So, we doesn't
have an actual data from server.
To resolve this issue, cookies are used as temporary storage and are removed
on page unload.

How it works:
1) On page load: cookies are empty and player get an actual data from server.
2) When user change some preferences, new value is stored to cookie;
3) If we navigate to another sequential position, video player get an actual data
from cookies.
4) Close the page: `unload` event fires and we clear our cookies and send user
preferences to the server.
