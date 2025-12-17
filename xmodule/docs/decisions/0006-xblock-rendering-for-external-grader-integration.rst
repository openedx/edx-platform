# 6. Event-based XBlock Rendering for External Grader Integration
#################################################################

Status
******

**Provisional** *2025-03-18*

Implemented by: https://github.com/openedx/edx-platform/pull/34888

Context
*******

The Open edX platform currently renders XBlocks with scoring data through
synchronous HTTP callback requests from XQueue. This approach introduces
several challenges:

1. **Tight Coupling**: The XQueue service must know the specific callback URL
   for each XBlock, creating unnecessary coupling between services.

2. **HTTP Dependency**: Reliance on synchronous HTTP requests introduces
   potential points of failure, latency issues, and timeouts.

3. **Complex State Management**: Managing state across multiple services via
   HTTP callbacks makes tracking submission progress more difficult.

4. **Limited Scalability**: The callback model doesn't scale well in
   distributed environments, particularly with high loads.

5. **Consistency Issues**: HTTP failures can lead to discrepancies
   between the actual submission state and what's displayed to learners.

This ADR addresses the final component of the XQueue migration initiative,
building upon previous decisions that established

Decision
********

We will implement an event-driven approach to render XBlocks with scoring data,
replacing the traditional HTTP callback mechanism. This involves:

1. **Event Handler Implementation**:

   - Create a specialized event handler in the LMS to process the
     ``EXTERNAL_GRADER_SCORE_SUBMITTED`` signal.
   - Implement a signal handler in ``handlers.py`` to react to score
     submission events.
   - Develop a dedicated XBlock loader in ``score_render.py`` that can render
     blocks without HTTP requests.

2. **Integration with Existing Event Structure**:

   - Leverage the previously defined ``EXTERNAL_GRADER_SCORE_SUBMITTED``
     signal from edx-submissions.
   - Ensure propagation of the ``queue_key`` identifier across the submission
     pipeline.
   - Register appropriate URL handlers in the LMS for submission processing.

3. **Asynchronous Rendering Flow**:

   - When a score is set via the edx-submissions service, emit the
     ``EXTERNAL_GRADER_SCORE_SUBMITTED`` event.
   - The LMS event handler receives this event and initiates the XBlock
     rendering process.
   - The XBlock loader retrieves the necessary scoring data and updates
     the XBlock state.
   - The rendered XBlock is presented to the learner with updated scoring
     information.

Technical Components:

.. code-block:: python

    # Signal handler registration
    @receiver(EXTERNAL_GRADER_SCORE_SUBMITTED)
    def handle_external_grader_score(sender, **kwargs):
        """
        Handle the external grader score submitted event.
        Retrieves the scoring data and initiates XBlock rendering.
        """
        score_data = kwargs.get('score_data')
        # Process score data and render XBlock
        render_xblock_with_score(score_data)

.. code-block:: python

    def render_xblock_with_score(score_data):
        """
        Render an XBlock with the provided scoring data.
        This replaces the traditional HTTP callback approach.
        """
        # Retrieve the XBlock
        xblock = get_xblock_by_module_id(score_data.module_id)

        # Update XBlock state with score information
        update_xblock_state(xblock, score_data)

        # Trigger rendering process
        render_xblock(xblock)

Consequences
************

Positive:
---------

1. **Architectural Improvements**:

   - Elimination of synchronous HTTP dependencies between services to
     render score.
   - More robust error handling.
   - Improved system observability through event tracking.

2. **Performance Benefits**:

   - Reduced latency in score rendering and feedback presentation.
   - Better scalability in high-load environments.
   - More efficient resource utilization without blocking HTTP calls.

3. **User Experience**:

   - More consistent experience for learners with faster score updates.
   - Reduced likelihood of rendering failures affecting feedback display.
   - Improved reliability in handling scoring events.

Negative:
---------

1. **Implementation Complexity**:

   - Requires additional signal handling infrastructure.
   - More complex testing scenarios to validate event-based flows.

2. **Operational Considerations**:

   - Requires monitoring of event emission and consumption.
   - Debugging complexity increases with asynchronous flows.
   - Need for proper error recovery mechanisms if events are missed.

3. **Transition Challenges**:

   - Temporary increased system complexity during migration period.
   - Careful coordination needed between edx-submissions and LMS changes.

Neutral:
--------

1. **Documentation Needs**:

   - Updated developer documentation for event-based architecture.
   - Event schema documentation for future integrations.


References
**********

Pull Requests:

   * Initial Event Definition:
     https://github.com/openedx/edx-submissions/pull/283
   * ExternalGraderDetail Implementation:
     https://github.com/openedx/edx-submissions/pull/283
   * SubmissionFile Implementation:
     https://github.com/openedx/edx-submissions/pull/286
   * XQueueViewSet Implementation:
     https://github.com/openedx/edx-submissions/pull/287
   * Event Emission Implementation:
     https://github.com/openedx/edx-submissions/pull/292

Related Documentation:

   * XQueue Migration Plan:
     https://github.com/openedx/edx-platform/pull/36258
   * Django Signals Documentation:
     https://docs.djangoproject.com/en/stable/topics/signals/
   * Open edX Events Framework: https://github.com/openedx/openedx-events

Architecture Guidelines:

   * Open edX Architecture Guidelines:
     https://openedx.atlassian.net/wiki/spaces/AC/pages/124125264/Architecture+Guidelines
   * OEP-19: Developer Documentation:
     https://open-edx-proposals.readthedocs.io/en/latest/oep-0019-bp-developer-documentation.html
