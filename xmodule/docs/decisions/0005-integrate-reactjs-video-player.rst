Integrate ReactJS and Video.js based video player into Video xBlock
####################################################################

Context
*******

One of the most critical components of Open edX content delivery is the video player. The existing video player has several limitations and pain points that have been identified through partners interviews and analysis of the "Platform Map", see `Approach Memo - React-based Video Player`_. These limitations include a complex video upload process, lack of modern features for video player, and insufficient support for accessibility standards like providing Audio Description track. Additionally, the current architecture does not easily allow for the integration of newer technologies or third-party services, limiting the platform's ability to evolve and meet the needs of a diverse and growing community around Open edX.

The `Approach Memo - React-based Video Player`_ document outlines an extensive plan to address these issues by implementing a new, modernized video player using ReactJS.
During the `Initial Technical Discovery`_  placed by edX, the decision was made to use `Video.js`_ library as a core for the new video player, as this option is best suited to handle edX’s accessibility requirements (WCAG 2.1) - https://www.w3.org/TR/WCAG21/.
Axim’s recommendation is also for option three, video.js.  It is not only the more mature project, but also the more consistently maintained one stated in the `Approach Memo - React-based Video Player`_.

The plan proposes the integration of ReactJS for the frontend and Video.js as the core of the new video player. ReactJS offers a robust framework for building user interfaces, while Video.js provides a flexible and feature-rich HTML5 video player that is widely adopted and community-supported. This combination will allow for a more interactive and user-friendly experience.

It is essential to achieve feature parity first in the new video player integration to ensure a smooth transition and maintain user trust. As we move towards a more modern and robust video delivery system, it is essential that all the functionalities that users have come to rely on in the current system are seamlessly available in the new one. This includes basic video playback, captioning, and accessibility features, as well as advanced functionalities like variable playback speeds, and analytics tracking. Please see `Parity with Current Video Player`_ for the list of the most important current video player features.

Moreover, the new architecture aims to be modular, enabling easier future integrations with third-party services like Vimeo or additional accessibility features. It also plans to support various video formats like HLS, DASH, MP4, and even YouTube videos, making it versatile and ready for future technologies.

One of the significant challenges in implementing this change is the migration process. The existing video content, along with its metadata, needs to be seamlessly transferred to the new system without causing disruptions to the current courses or the learner experience. This migration process is complex and requires careful planning to ensure data integrity and system stability.

Another crucial aspect is the rollout strategy. Given the platform's extensive user base, any changes to such a critical component must be introduced gradually to monitor performance and gather user feedback. The approach memo suggests the use of feature toggles to enable the new video player selectively. This will allow platform administrators to test the new features in a controlled environment before a full-scale rollout.

Accessibility is a key focus area, and the new player aims to be compliant with the latest WCAG guidelines. This includes providing Audio Descriptions, focus state visibility, and other accessibility features, which are currently either lacking or not up to the mark in the existing system. The new architecture aims to rectify this by integrating these features into the core of the new Video Player.

In summary, the context for this Architecture Decision Record (ADR) is introduction of the new Video xBlock aims to address multiple pain points, ranging from user experience and accessibility to extensibility and modernization of the tech stack. It represents a significant step forward in aligning the platform with modern web standards and user expectations, while also laying the groundwork for future enhancements.


Decision
********

1. **Move out current Video xBlock from xmodules and place it in a separate repository**

We have decided to extract the current Video xBlock from the `xmodule` directory and relocate it into its own dedicated repository within the `github.com/openedx <https://github.com/openedx>`_ organization. This decision is driven by the need for improved modularity, maintainability, and the facilitation of continuous integration and deployment practices.

* A new repository will be created under the Open edX GitHub organization.
* The repository will adhere to Open edX's best practices, including code quality, testing, and documentation.
* The proposed approach for installing and using new xBlock is the following:

  + The current video block stored in the xmodule will be moved to a new repository as is.
  + The xBlock will have two frontend implementations, current Vanila JS version, and the new one using ReactJS and Video.JS libraries. Both frontend packages will be using the same backend.
  + In the case new changes into backend for ReactJS frontend are required, they should be added in a modular way, e.g., using feature flag to provide full backward compatibility for the current Vanila JS frontend.
  + New ReactJS Video Player component will be build with NPM into JS package which can be distributed via npm package registry for installing into Course-Authoring and Library-Authoring MFEs.
  + The xBlock itself will be installed into edx-platform using PIP package manager.
  + The package will be released using SemVer approach, the frontend and backend counterparts should be published with the same version at all times.

.. image:: xmodule/docs/decisions/0005-integrate-reactjs-video-player/video_xblock_architecture.png
   :alt: Proposed Architecture

2. **ReactJS and Video.js Integration**

* ReactJS will be used to build a responsive, accessible frontend for a new xBlock.
* Typescript should be used to implement a new frontend, during implementation the following `ADR in frontend-build repository <github.com/openedx/frontend-build/pull/412>`_ should be used as the main guidance.
* The solution will partially follow approach which is described in the https://github.com/openedx/xBlock/issues/635, however the main difference is that xBlock will still be rendered in the legacy interface LMS and displayed through the Iframe in the frontend-app-learning.
* Video.js will be integrated for video playback, following the official guidelines from (`Video.js Docs <https://docs.videojs.com/>`_).
* An NPM package will be created for the Video player component and published to npm registry.
* Video player component should accept video metadata and configuration options via the component props, so it can be used in an MFE directly.

3. **Feature Toggle in edx-platform**

* To address the requirement for the gradual rollout of the new Video Player, a new feature toggle will be introduced using Django Waffle flags. This will allow for a manual rollout and the ability to quickly revert to the old player if issues arise.
* There will be a possibility to manage a feature toggle on a course level or organization level by applying `WaffleFlagCourseOverrideModel` and `WaffleFlagOrgOverrideModel`.
* The Feature toggle will be used to determine which frontend for the Video Block should be used, whether its legacy or the new one.

4. **Integration into Legacy Interface and Course Authoring**

* The new xBlock will be embedded in iframes in the legacy interface.
* In the Course Authoring MFE, the xBlock will be integrated natively using ReactJS components.

5. **Default Functionality Supported by Video.js**

* It's necessary to achieve the feature parity with the current video xBlock.
* Support for HLS, DASH, MP4, and YouTube will be provided out-of-the-box.
* More details regarding video.js functionality for extensibility will be included in the follow up ADR.


Rejected Alternatives
*********************

1. **Creating a Separate Frontend-Component**: We considered developing a standalone frontend-component for the video player, which would be integrated into the Open edX platform as an independent module. This approach was rejected for several reasons:

   * **Integration Complexity**: The standalone component would require additional overhead to ensure compatibility with the existing backend infrastructure, potentially leading to a fragmented codebase and increased maintenance challenges.

   * **Feature Inconsistency**: There was a risk of feature divergence between the frontend component and the backend xBlock, which could lead to inconsistencies in user experience and functionality.

   * **Deployment Overhead**: Deploying a separate frontend-component would necessitate a parallel deployment process, complicating the continuous integration and delivery pipelines.

2. **Creating a New Video xBlock to Coexist with the Current Block**: Another alternative was to develop a new Video xBlock from scratch, which would exist alongside the current video block. This option was also set aside due to:

   * Resource Duplication: Maintaining two separate video blocks would duplicate efforts in development, testing, and maintenance, reducing efficiency and increasing the potential for codebase bloat.
   * User Confusion: Having two video blocks available could confuse course creators and learners, leading to a disjointed experience and difficulty in managing course content.
   * Migration Complexity: Eventually, a decision would need to be made about migrating from the old to the new block, which would introduce additional complexity and potential disruption for existing courses.

Consequences
************

1. The new xBlock will provide a better user experience and will be easier to maintain and extend.
2. The feature toggle will mitigate risks during the rollout.

References
**********

- Video.js Documentation: https://docs.videojs.com/
- ReactJS Documentation: https://reactjs.org/docs/getting-started.html
- Django Waffle: https://waffle.readthedocs.io/en/stable/
- GitHub Issue for NPM Package Management: https://github.com/openedx/xBlock/issues/ID


.. _Approach Memo - React-based Video Player: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3811901443/DRAFT+New+video+player+architecture
.. _Initial Technical Discovery: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3675521033
.. _Video.js: https://videojs.com/
.. _Parity with Current Video Player: https://openedx.atlassian.net/wiki/spaces/OEPM/pages/3674734593/Approach+Memo+Technical+Discovery+React-based+Video+Player#Parity-with-Current-Video-Player
