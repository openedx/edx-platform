class CourseRelativeMember:
    def __init__(self, location, idx):
        self.course_location = location     # a Location obj
        self.idx = idx                   # which milestone this represents. Hopefully persisted # so we don't have race conditions
    
### ??? If 2+ courses use the same textbook or other asset, should they point to the same db record?        
class linked_asset(CourseRelativeMember):
    """
    Something uploaded to our asset lib which has a name/label and location. Here it's tracked by course and index, but
    we could replace the label/url w/ a pointer to a real asset and keep the join info here.
    """
    def __init__(self, location, idx):
        CourseRelativeMember.__init__(self, location, idx)
        self.label = ""
        self.url = None
        
class summary_detail_pair(CourseRelativeMember):
    """
    A short text with an arbitrary html descriptor used for paired label - details elements.
    """
    def __init__(self, location, idx):
        CourseRelativeMember.__init__(self, location, idx)
        self.summary = ""
        self.detail = ""
        