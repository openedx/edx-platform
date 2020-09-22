import React, {useState} from "react";
import PropTypes from 'prop-types';
import {Button, InputText} from "@edx/paragon/src";

/**
 * VideoList template. See VideoListContainer below.
 */
export const VideoList = ({name, label, value, setExpanded, expanded, updatePosition}) => {
    return (
        <React.Fragment>
          <InputText
            name={name}
            label={label}
            value={value[0]}
            onChange={updatePosition(0)}
            description={gettext('The URL for your video. This can be a YouTube URL or a link to an .mp4, .ogg, or .webm video file hosted elsewhere on the Internet.')}
          />
          <div>
              <Button onClick={() => setExpanded(!expanded)} label={gettext('Add backup URLs')} />
          </div>
            {expanded && (
              <div>
                <p>
                  {gettext('To be sure all students can access the video, we recommend providing both an .mp4 and a .webm version of your video. Click below to add a URL for another version. These URLs cannot be YouTube URLs. The first listed video that\'s compatible with the student\'s computer will play.')}
                </p>
                <div>
                  <InputText
                    name={`${name}_1`}
                    label=""
                    value={value[1]}
                    onChange={updatePosition(1)}
                  />
                </div>
                <div>
                  <InputText
                    name={`${name}_2`}
                    label=""
                    value={value[2]}
                    onChange={updatePosition(2)}
                  />
                </div>
              </div>
            )}
        </React.Fragment>
    )
}

VideoList.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.arrayOf(PropTypes.string).isRequired,
  updatePosition: PropTypes.func.isRequired,
  expanded: PropTypes.bool.isRequired,
  setExpanded: PropTypes.func.isRequired,
}

/**
 * VideoListContainer
 * This function is a react component that handles the 'video_url' field, which, despite its name, is array of video
 * urls, not just one. It's also dynamically constructed by the backend based on the set YoutubeID and the backup
 * HTML5 sources.
 *
 * This component isn't complete-- it matches the functionality of the 'Basic' tab in studio, but either a different
 * component needs to be made to handle the 'Advanced' tab's functionality or else this component needs to be
 * refactored/split up.
 */
export const VideoListContainer = ({name, label, value, update}) => {
    const updatePosition = (position) => (value) => {
      const revised = [...value]
      revised[position] = value;
      update(revised);
    }
    const [expanded, setExpanded] = useState(false)
    return (
      <VideoList
        expanded={expanded}
        setExpanded={setExpanded}
        updatePosition={updatePosition}
        name={name}
        label={label}
        value={value}
      />
    )
}

VideoListContainer.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  value: PropTypes.arrayOf(PropTypes.string).isRequired,
  update: PropTypes.func.isRequired,
}
