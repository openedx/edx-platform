def preprocessing_filter_spec(endpoints):
    filtered = []
    for (path, path_regex, method, callback) in endpoints:
        # Remove all but DRF API endpoints
        if (
            path.startswith("/api/contentstore/v1/xblock") or
            path.startswith("/api/contentstore/v1/videos") or
            path.startswith("/api/contentstore/v1/video_transcripts") or
            path.startswith("/api/contentstore/v1/file_assets")
        ):
            filtered.append((path, path_regex, method, callback))
    return filtered
