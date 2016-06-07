"""
Search overrides for courseware search
Implement overrides for:
* SearchResultProcessor
    - to mix in path to result
    - to provide last-ditch access check
* SearchFilterGenerator
    - to provide additional filter fields (for cohorted values etc.)
    - to inject specific field restrictions if/when desired
"""
