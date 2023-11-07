ADR 004: New Video XBlock with React.js and Video.js Integration
==============================================================================

Context
-------

One of the most critical components of Open edX content delivery is the video player. The existing video player has several limitations and pain points that have been identified through partners interviews and analysis of the "Platform Map" (see `Approach Memo - React-based Video Player`_ ). These limitations include a complex video upload process, lack of modern features for video player, and insufficient support for accessibility standards like providing Audio Description track. Additionally, the current architecture does not easily allow for the integration of newer technologies or third-party services, limiting the platform's ability to evolve and meet the needs of a diverse and growing community around Open edX.

The `Approach Memo - React-based Video Player`_ document outlines an extensive plan to address these issues by implementing a new, modernized video player using React.js.
During the `Initial Technical Discovery`_  placed by edX, the decision was made to use `Video.js`_ library as a core for the new video player, as this option is best suited to handle edX’s accessibility requirements (WCAG 2.1) - https://www.w3.org/TR/WCAG21/.
Axim’s recommendation is also for option three, video.js.  It is not only the more mature project, but also the more consistently maintained one stated in the `Approach Memo - React-based Video Player`_.

The plan proposes the integration of React.js for the frontend and Video.js as the core of the new video player. React.js offers a robust framework for building user interfaces, while Video.js provides a flexible and feature-rich HTML5 video player that is widely adopted and community-supported. This combination will allow for a more interactive and user-friendly experience.

It is essential to achieve feature parity first in the new video player integration to ensure a smooth transition and maintain user trust. As we move towards a more modern and robust video delivery system, it is essential that all the functionalities that users have come to rely on in the current system are seamlessly available in the new one. This includes basic video playback, captioning, and accessibility features, as well as advanced functionalities like variable playback speeds, and analytics tracking. Please see `Parity with Current Video Player`_ for the list of the most important current video player features.

Moreover, the new architecture aims to be modular, enabling easier future integrations with third-party services like Vimeo or additional accessibility features. It also plans to support various video formats like HLS, DASH, MP4, and even YouTube videos, making it versatile and ready for future technologies.

One of the significant challenges in implementing this change is the migration process. The existing video content, along with its metadata, needs to be seamlessly transferred to the new system without causing disruptions to the current courses or the learner experience. This migration process is complex and requires careful planning to ensure data integrity and system stability.

Another crucial aspect is the rollout strategy. Given the platform's extensive user base, any changes to such a critical component must be introduced gradually to monitor performance and gather user feedback. The approach memo suggests the use of feature toggles to enable the new video player selectively. This will allow platform administrators to test the new features in a controlled environment before a full-scale rollout.

Accessibility is a key focus area, and the new player aims to be compliant with the latest WCAG guidelines. This includes providing Audio Descriptions, focus state visibility, and other accessibility features, which are currently either lacking or not up to the mark in the existing system. The new architecture aims to rectify this by integrating these features into the core of the new Video Player.

In summary, the context for this Architecture Decision Record (ADR) is introduction of the new Video XBlock aims to address multiple pain points, ranging from user experience and accessibility to extensibility and modernization of the tech stack. It represents a significant step forward in aligning the platform with modern web standards and user expectations, while also laying the groundwork for future enhancements.


Decision
--------

1. **Move out current Video XBlock from xmodules and place it in a separate repository**

   We have decided to extract the current Video XBlock from the xmodules directory and relocate it into its own dedicated repository within the github.com/openedx organization. This decision is driven by the need for improved modularity, maintainability, and the facilitation of continuous integration and deployment practices.
   * A new repository will be created under the Open edX GitHub organization.
   * The repository will adhere to Open edX's best practices, including code quality, testing, and documentation.
   * The new XBlock will be hosted within the Open edX organization on GitHub, ensuring community involvement and adherence to Open edX standards.
   * The proposed architecture for installing and using new xblock is the following:

     .. image:: ./Architecture.png

2. **React.js and Video.js Integration**
   * React.js will be used to build a responsive, accessible frontend for a new Xblock as proposed in https://github.com/openedx/XBlock/issues/635 and prototyped in https://github.com/openedx/XBlock/issues/634.
   * Video.js will be integrated for video playback, following the official guidelines (`Video.js Docs <https://docs.videojs.com/>`_).
   * An NPM package will be created for the frontend, and it will be versioned and published (`Issue 635 <https://github.com/openedx/XBlock/issues/635>`_).

3. **Feature Toggle in edx-platform**
   * A feature toggle will be introduced using Django Waffle flags.
   * This will allow for a manual rollout and the ability to quickly revert to the old player if issues arise.

4. **Integration into Legacy Interface and Course Authoring**
   * The new XBlock will be embedded in iframes in the legacy interface.
   * In the Course Authoring MFE, the XBlock will be integrated natively using React.js components.

5. **Migration Necessity**
  * The data migration will not be required as long as the current video block backend is used.
  * Data and metadata will be preserved during the migration.

6. **Default Functionality Supported by Video.js**
   * Support for HLS, DASH, MP4, and YouTube will be provided out-of-the-box.

7. **Extension with Vimeo Backend**
   * A plugin will be developed to extend Video.js to support Vimeo videos.

Rejected Alternatives
---------------------

1. **Creating a Separate Frontend-Component**: We considered developing a standalone frontend-component for the video player, which would be integrated into the Open edX platform as an independent module. This approach was rejected for several reasons:

   * **Integration Complexity**: The standalone component would require additional overhead to ensure compatibility with the existing backend infrastructure, potentially leading to a fragmented codebase and increased maintenance challenges.

   * **Feature Inconsistency**: There was a risk of feature divergence between the frontend component and the backend XBlock, which could lead to inconsistencies in user experience and functionality.

   * **Deployment Overhead**: Deploying a separate frontend-component would necessitate a parallel deployment process, complicating the continuous integration and delivery pipelines.

2. **Creating a New Video XBlock to Coexist with the Current Block**: Another alternative was to develop a new Video XBlock from scratch, which would exist alongside the current video block. This option was also set aside due to:

   * **Resource Duplication**: Maintaining two separate video blocks would duplicate efforts in development, testing, and maintenance, reducing efficiency and increasing the potential for codebase bloat.

   * **User Confusion**: Having two video blocks available could confuse course creators and learners, leading to a disjointed experience and difficulty in managing course content.

   * **Migration Complexity**: Eventually, a decision would need to be made about migrating from the old to the new block, which would introduce additional complexity and potential disruption for existing courses.

Consequences
------------

1. The new XBlock will provide a better user experience and will be easier to maintain and extend.
2. The feature toggle will mitigate risks during the rollout.

References
----------

- Video.js Documentation: https://docs.videojs.com/
- React.js Documentation: https://reactjs.org/docs/getting-started.html
- Django Waffle: https://waffle.readthedocs.io/en/stable/
- GitHub Issue for NPM Package Management: https://github.com/openedx/XBlock/issues/ID


.. _Approach Memo - React-based Video Player: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3811901443/DRAFT+New+video+player+architecture
.. _Initial Technical Discovery: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3675521033
.. _Video.js: https://videojs.com/
.. _Parity with Current Video Player: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3674734593/Approach+Memo+Technical+Discovery+React-based+Video+Player#Parity-with-Current-Video-Player
