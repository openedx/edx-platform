This static directory is for files that should be included in your kit as plain
static files.

You can ask the runtime for a URL that will retrieve these files with:

    url = self.runtime.local_resource_url(self, "static/js/lib.js")

The default implementation is very strict though, and will not serve files from
the static directory.  It will serve files from a directory named "public".
Create a directory alongside this one named "public", and put files there.
Then you can get a url with code like this:

    url = self.runtime.local_resource_url(self, "public/js/lib.js")

The sample code includes a function you can use to read the content of files
in the static directory, like this:

    frag.add_javascript(self.resource_string("static/js/my_block.js"))

