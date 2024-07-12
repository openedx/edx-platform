"""
The xblock_storage_handlers folder contains service methods that implement the business logic for view endpoints
located in contentstore/views/block.py. It is renamed to xblock_storage_handlers to reflect its responsibility
of handling storage-related operations of xblocks, such as creation, retrieval, and deletion.

The view_handlers.py file includes business methods called by the view endpoints.
These methods, such as handle_xblock, delete_orphans, etc., interact with the required modulestore methods,
handle any errors, and aggregate and serialize data for the response.
"""
