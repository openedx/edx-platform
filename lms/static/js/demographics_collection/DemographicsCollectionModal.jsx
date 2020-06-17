import React, { useState } from 'react';
import { Modal, Button } from '@edx/paragon/static';

class DemographicsCollectionModal extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      open: true,
      // page values are 1-4
      page: 1,
    };
  }
  render () {
    return (
      <div className="demographics-collection-modal">
      <Modal
        open={open}
        title="Help make edX better for everyone"
        onClose={()=>{}}
        closeText="Finish Later"
        body={
          <div>
            <p>Thanks for registering with edX! Before getting started, please complete the additional information below to help your fellow learners. Your information will never be sold.</p>
            <select>
              <option></option>
            </select>
          </div>
        }
        buttons={[
            <Button
              buttonType="success"
              label="Continue!"></Button>
        ]}
      />
    </div>
    )
  }
}

export { DemographicsCollectionModal };
