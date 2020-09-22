class TransitionalService(object):
    """
    An XBlock service to be used for flagging that the runtime environment supports transitional
    features, not yet finalized.

    This will primarily be used for the Video and Problem blocks in order for them to know they can safely
    run their experimental studio views compatible with the new Micro Front Ends.
    """

    def load_new_editor_for_block(self, _xblock):
        # Right now we're only loading this service in Blockstore, so it should always be true.
        return True
