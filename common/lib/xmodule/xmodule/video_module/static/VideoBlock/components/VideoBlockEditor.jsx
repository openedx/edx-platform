import React from 'react';
import PropTypes from 'prop-types';
import { fetchSettings, submitSettings, emit } from '../data/thunks';
import { connect } from "react-redux";
import Tabs from "@edx/paragon/src/Tabs";
// // According to the docs for the version of Paragon installed, this should import versions of the components with
// // style names that are scoped to paragon. This is true, but...
// import {InputText, Button, CheckBox} from "@edx/paragon/static";
// // ...The following import line fails from what appears to be a path issue.
// import "@edx/paragon/static/paragon.min.css"
// // So, we're falling back the base component imports.
import {InputText, Button, CheckBox} from "@edx/paragon/src";
import { VideoListContainer } from "./VideoList";
import {SettingsShape} from "../data/shapes";


export const VideoBlockEditor = ({changes, updateForm, saveSettings, errors}) => {
  return (
    <div className="px-3">
      <Tabs labels={['Basic', 'Advanced']}>
        <div className="row">
          <div className="col col-12">
            <InputText
                value={changes.display_name}
                name="display_name"
                isValid={!errors.display_name}
                validationMessage={errors.display_name}
                description={gettext('The display name for this component.')}
                label={gettext('Component Display Name')}
                onChange={updateForm('display_name')}
            />
          </div>
          <div className="col col-12">
            { /* need to figure out way of handling error messages here. */}
            <VideoListContainer
              name="video_url"
              label={gettext('Default Video URL')}
              value={changes.video_url}
              update={updateForm('video_url')}
            />
          </div>
          <div className="col col-12">
            <InputText
              value={changes.edx_video_id}
              name="video_id"
              label={gettext('Video ID')}
              isValid={!errors.video_id}
              description={gettext('If you were assigned a Video ID by edX for the video to play in this component, enter the ID here. In this case, do not enter values in the Default Video URL, the Video File URLs, and the YouTube ID fields. If you were not assigned a Video ID, enter values in those other fields and ignore this field.')}
              onChange={updateForm('video_id')}
            />
          </div>
        </div>
        <div className="row">
          <div className="col col-12">
            <InputText
              value={changes.display_name}
              name="display_name"
              isValid={!errors.display_name}
              validationMessage={errors.display_name}
              description={gettext('The display name for this component.')}
              label={gettext('Component Display Name')}
              onChange={updateForm('display_name')}
            />
          </div>
          <div className="col col-12">
            <CheckBox
              checked={changes.only_on_web}
              name="only_on_web"
              label={gettext('Video Available on Web Only')}
              isValid={!errors.only_on_web}
              validationMessage={errors.only_on_web}
              description={gettext('Specify whether access to this video is limited to browsers only, or if it can be accessed from other applications including mobile apps.')}
              onChange={updateForm('only_on_web')}
            />
          </div>
          <div className="col col-12">
            <CheckBox
              checked={changes.download_track}
              name="download_track"
              label={gettext('Download Transcript Allowed')}
              isValid={!errors.download_track}
              validationMessage={errors.download_track}
              description={gettext('Allow students to download the timed transcript. A link to download the file appears below the video. By default, the transcript is an .srt or .txt file. If you want to provide the transcript for download in a different format, upload a file by using the Upload Handout field.')}
              onChange={updateForm('download_track')}
            />
          </div>
          <div className="col col-12">
            <CheckBox
              checked={changes.download_video}
              name="download_video"
              label={gettext('Video Download Allowed')}
              isValid={!errors.download_video}
              validationMessage={errors.download_video}
              description={gettext('Allow students to download versions of this video in different formats if they cannot use the edX video player or do not have access to YouTube. You must add at least one non-YouTube URL in the Video File URLs field.')}
              onChange={updateForm('download_video')}
            />
          </div>
          <div className="col col-12">
            <InputText
              value={changes.track}
              name="track"
              isValid={!errors.track}
              validationMessage={errors.track}
              description={gettext('By default, students can download an .srt or .txt transcript when you set Download Transcript Allowed to True. If you want to provide a downloadable transcript in a different format, we recommend that you upload a handout by using the Upload a Handout field. If this isn\'t possible, you can post a transcript file on the Files & Uploads page or on the Internet, and then add the URL for the transcript here. Students see a link to download that transcript below the video.')}
              label={gettext('Downloadable Transcript URL')}
              onChange={updateForm('track')}
            />
          </div>
          <div className="col col-12">
            <InputText
              value={changes.edx_video_id}
              name="edx_video_id"
              label={gettext('Video ID')}
              isValid={!errors.edx_video_id}
              validationMessage={errors.edx_video_id}
              description={gettext('If you were assigned a Video ID by edX for the video to play in this component, enter the ID here. In this case, do not enter values in the Default Video URL, the Video File URLs, and the YouTube ID fields. If you were not assigned a Video ID, enter values in those other fields and ignore this field.')}
              onChange={updateForm('edx_video_id')}
            />
          </div>
          <div className="col col-12">
            <InputText
              value={changes.start_time}
              name="start_time"
              isValid={!errors.start_time}
              validationMessage={errors.start_time}
              label={gettext('Start Time')}
              description={errors.start_time || gettext('Time you want the video to start if you don\'t want the entire video to play. Not supported in the native mobile app: the full video file will play. Formatted as HH:MM:SS. The maximum value is 23:59:59.')}
              onChange={updateForm('start_time')}
            />
          </div>
          <div className="col col-12">
            <InputText
              value={changes.end_time}
              name="end_time"
              label={gettext('End Time')}
              isValid={!errors.end_time}
              validationMessage={errors.end_time}
              description={gettext('Time you want the video to stop if you don\'t want the entire video to play. Not supported in the native mobile app: the full video file will play. Formatted as HH:MM:SS. The maximum value is 23:59:59.')}
              onChange={updateForm('end_time')}
            />
          </div>
        </div>
      </Tabs>
      <div className="xblock-actions">
        <ul>
          <li>
            <Button label="Save" onClick={saveSettings} />
          </li>
        </ul>
      </div>
    </div>
  )
};


export const VideoBlockEditorContainerBase = ({
    fetchSettings, submitSettings, settings, xblockElement, runtime, emit, changes, errors,
}) => {
  if (settings === null) {
    fetchSettings({runtime, xblockElement}).catch((error) => {
      if (runtime.notify) {
        runtime.notify("error", {message: error + ''})
      } else {
        throw error
      }
    })
    return ''
  }
  if (changes === null) {
    // Can happen briefly after settings are first set in the store but before copied into the changes field.
    return ''
  }
  const updateForm = (fieldName) => (newValue) => {
    if (errors[fieldName]) {
      const newErrors = {...errors}
      delete newErrors[fieldName]
      emit('setErrors', {errors: newErrors})
    }
    emit('updateChanges', {changes: {...changes, [fieldName]: newValue}})
  }
  const saveSettings = () => {
    emit('setErrors', {errors: {}})
    submitSettings({runtime, xblockElement, changes}).then((revised) => {
      emit('updateSettings', {settings: revised})
      emit('updateChanges', {changes: revised})
    }).catch(() => undefined)
  }
  const fieldErrors = {}
  // Usability standards suggest only showing one error message per field at a time.
  // If there are multiple, just show one for now.
  Object.keys(errors).map((key) => fieldErrors[key] = errors[key][0])
  return <VideoBlockEditor changes={changes} updateForm={updateForm} saveSettings={saveSettings} errors={fieldErrors} />
};

VideoBlockEditorContainerBase.propDefaults = {
  changes: null,
  settings: null,
}

VideoBlockEditorContainerBase.propTypes = {
  fetchSettings: PropTypes.func.isRequired,
  submitSettings: PropTypes.func.isRequired,
  xblockElement: PropTypes.element.isRequired,
  runtime: PropTypes.shape({
    notify: PropTypes.func,
  }),
  emit: PropTypes.func.isRequired,
  changes: SettingsShape,
  settings: SettingsShape,
}

export const VideoBlockEditorContainer = connect(
  (state) => ({settings: state.settings, changes: state.changes, errors: state.errors}),
  {
    fetchSettings,
    submitSettings,
    emit,
  },
)(VideoBlockEditorContainerBase)

