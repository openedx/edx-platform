import PropTypes from 'prop-types';

export const SettingsShape = PropTypes.shape({
  display_name: PropTypes.string.isRequired,
  video_url: PropTypes.arrayOf(PropTypes.string),
  video_id: PropTypes.string.isRequired,
  only_on_web: PropTypes.bool.isRequired,
  download_track: PropTypes.bool.isRequired,
  download_video: PropTypes.bool.isRequired,
  track: PropTypes.string.isRequired,
  edx_video_id: PropTypes.string.isRequired,
  start_time: PropTypes.string.isRequired,
  end_time: PropTypes.string.isRequired,
})
