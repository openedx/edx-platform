"""
Some test content strings. Best to keep them out of the test files because they take up a lot of
text space
"""

from textwrap import dedent

TEST_COURSE_UPDATES_CONTENT = dedent(
    """
    <section>
      <article>
        <h2>April 18, 2014</h2>
        This does not have a paragraph tag around it
      </article>
      <article>
        <h2>April 17, 2014</h2>
        Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag
      </article>
      <article>
        <h2>April 16, 2014</h2>
        Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag<p>one more</p>
      </article>
      <article>
        <h2>April 15, 2014</h2>
        <p>A perfectly</p><p>formatted piece</p><p>of HTML</p>
      </article>
    </section>
    """
)

TEST_COURSE_UPDATES_CONTENT_LEGACY = dedent(
    """
    <ol>
      <li>
        <h2>April 18, 2014</h2>
        This is some legacy content
      </li>
      <li>
        <h2>April 17, 2014</h2>
        Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag
      </li>
      <li>
        <h2>April 16, 2014</h2>
        Some text before paragraph tag<p>This is inside paragraph tag</p>Some text after tag<p>one more</p>
      </li>
      <li>
        <h2>April 15, 2014</h2>
        <p>A perfectly</p><p>formatted piece</p><p>of HTML</p>
      </li>
    </ol>
    """
)

TEST_STATIC_TAB1_CONTENT = dedent(
    """
    <div>This is static tab1</div>
    """
)

TEST_STATIC_TAB2_CONTENT = dedent(
    """
    <div>This is static tab2</div>
    """
)

TEST_COURSE_OVERVIEW_CONTENT = dedent(
    """
    <section class="about">
      <h2>About This Course</h2>
      <p>Include your long course description here. The long course description should contain 150-400 words.</p>

      <p>This is paragraph 2 of the long course description. Add more paragraphs as needed. Make sure to enclose them in paragraph tags.</p>
    </section>

    <section class="prerequisites">
      <h2>Prerequisites</h2>
      <p>Add information about course prerequisites here.</p>
    </section>

    <section class="course-staff">
      <h2>Course Staff</h2>
      <article class="teacher">
        <div class="teacher-image">
          <img src="/images/pl-faculty.png" align="left" style="margin:0 20 px 0" alt="Course Staff Image #1">
        </div>
        <h3>Staff Member #1</h3>
        <p>Biography of instructor/staff member #1</p>
      </article>

      <article class="teacher">
        <div class="teacher-image">
          <img src="/images/pl-faculty.png" align="left" style="margin:0 20 px 0" alt="Course Staff Image #2">
        </div>
        <h3>Staff Member #2</h3>
        <p>Biography of instructor/staff member #2</p>
      </article>

      <article class="author">
        <div class="author-image">
          <img src="/images/pl-author.png" align="left" style="margin:0 20 px 0" alt="Author Name">
        </div>
        <h3>Author Name</h3>
        <p>Biography of Author Name</p>
      </article>
    </section>

    <section class="faq">
        <p>Some text here</p>
    </section>

    <section class="intro-video" data-videoid="foobar">
    </section>
    """
)
