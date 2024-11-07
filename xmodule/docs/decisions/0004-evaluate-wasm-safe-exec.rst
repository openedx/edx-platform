4. Adopt WebAssembly as an Option for Safe Code Execution
#########################################################

Status
******

**Provisional**

Subject to change due to implementation learnings and stakeholder feedback.

Context
*******

The Open edX platform allows advanced course authors to write customized problem scoring code in Python. This has long been an area of strength, but it comes with significant operational issues, security risk, and long term maintenance burdens for both the authors and platform developers.

Recent advancements in WebAssembly (Wasm) give us an opportunity to give course teams even more powerful capabilities for trusted server-side grading, while being safer, faster, and easier to maintain. Third party package support is not yet at a level where we can make a drop-in replacement for codejail, but we can still build the infrastructure that would make it possible, as well as offer exciting new capabilities.

Why WebAssembly?
================

Code sandboxing currently happens using codejail, an AppArmor-based sandboxing mechanism that either runs on the same server as Studio/LMS, or runs on a separate server. This current system has worked for us for some time, but it has a number of drawbacks that WebAssembly is well positioned to address.

Security
--------

In the current system, simple misconfigurations can be dangerous, since we're running a full instance of Python and relying on properly setting up codejail and AppArmor to constrain it.

WebAssembly was created with safe execution in mind. When running Wasm code, it will by default have no access to the network or host filesystem.

Maintenance
-----------

Content lasts longer than software, and authors don't expect to have to update their scoring code. When Python 2.7 was approaching its end-of-life, it was a large effort to get people to test their content with Python 3. Some of that content is probably forever broken. While this is an extreme example, there will be smaller breakages over time–libraries that get upgraded because the old versions are no longer available, Python versions that get updated because operating systems stop offering end-of-life versions, etc.

The big advantage Wasm provides here is that it can treat these software packages as *data*. If we have a Wasm binary file that holds a compiled version of Python and all relevant packages, then we no longer have to worry about upgrades or whether we can offer exactly those libraries in the future. We just keep the same binary around going forward.

We could still offer upgraded packages for new capabilities, but these would be purely opt-in. You could specify which system you wanted to use in your problem and have confidence that the content would never require updating. So you could specify that this particular problem should use the "python-sci-2024" stack (which maps to a stable Python+libraries release compiled to Wasm), and two years from now, you might make another problem that uses the "python-sci-2026" stack.

Flexibility of Additional Runtimes
----------------------------------

When the sandboxed runtime environment is just a Wasm file, it makes it much easier for us to support multiple runtimes with the same service and add new ones as necessary. These runtimes can even be in different languages.

Operations
----------

The Wasmtime library gives a more precise accounting of the resources being used by allotting computation budget "fuel" and measuring how much a given Wasm program has used. This is more precise than the limits that AppArmor uses, which can sometimes result in problems that work fine most of the time but start failing under elevated system load. The fact that we have precise measurements of how much fuel is being used also means that we can surface this information to content authors, so that they can be aware of the problem.

Cross-Platform Support
----------------------

AppArmor only works in Linux, and cannot run on Linux guest Docker containers on a macOS host machine. This makes it difficult for developers running macOS to develop and test features related to sandboxed code execution. WebAssembly can run on any major operating system.

Decisions
*********

#. We will create a new library in a new repo (``wasm-safe-exec``) for safely executing instructor-authored code using WebAssembly as the execution mechanism.

   * The library will use ``wasmtime-py`` for Wasm code execution.
   * The library must be runnable in edx-platform, meaning that it still needs to support Python 3.8 until edx-platform has been upgraded to 3.11.
   * The library must be able to simultaneously support multiple code execution runtime environments.
   * The library must not make ``edx-platform`` specific assumptions–e.g. ``UsageKeys``. It should be generally reusable for untrusted code execution by other projects.

#. We will use the WebAssembly Component Model and create a Wasm Interface Type (WIT) file defining the interface between the host library and guest code execution runtime environments.

   * It should be possible for third parties to easily create their own runtime environments.

#. We will create two simple runtimes to start: Python 3.11 and JavaScript ES14.

   * Runtime binaries will be created with `componentize-py <https://component-model.bytecodealliance.org/language-support/python.html>`_ for Python and and `jco <https://component-model.bytecodealliance.org/language-support/javascript.html>`_ for JavaScript.
   * Python 3.11 is the first version of Python that officially supports compiling to ``wasm32-wasi``, which is why it's the one we'll start with.
   * The Python runtime must be able to accept a course's ``python_lib.zip`` file.
   * Parity with codejail is not feasible at this time because only a handful of our popular libraries are available. However, we should include numpy (`using Fermyon's instructions <https://www.fermyon.com/blog/introducing-componentize-py>`_) and whatever pure Python libraries are practical to do so.
   * Preamble code (e.g. certain common library imports) will be the responsibility of the runtime environments.
   * For this first iteration, the Wasm runtime binary build process can simply be documented, and does not need to be part of any package or CI. In particular, we do *not* want to add 100 MB+ ``.wasm`` files as a direct dependency of edx-platform.

#. We will add this functionality as an opt-in, experimental feature to edx-platform.

   * There will be a ``CourseWaffleFlag`` toggling the feature as a whole.
   * The ``<script>`` tags used by the ProblemBlock will be extended with two new optional attributes:

     * ``runtime`` will specify the name of the runtime that the problem execution will be dispatched to.
     * ``options`` will allow authors to enter runtime-specific directives, like asking the runtime to use Python 2.x randomization behavior to preserve compatibility.

   * If there is no value for ``runtime`` OR if the feature is not enabled, the problem will use codejail as usual.

#. We will keep the implementation as simple as possible.

   * We will measure the latency and memory aspects of our simple version.
   * We may eventually be able to improve startup times by using `Wizer <https://github.com/bytecodealliance/wizer>_` or forking runtime containers after they've run their preamble, but those sorts of optimizations are out of scope for this initial effort.

It is likely that we will learn a lot from our initial implementation attempts, and that we will have to adjust our approach before we arrive at something that is broadly usable and supportable for the platform over the long term.

Rejected Alternatives
*********************

These rejected alternatives are things we may very well do eventually–they're just out of scope for the initial implementation/evaluation.

Deprecating/Replacing Codejail
  Critical third party libraries like SciPy are not currently built for ``wasm32-wasi``, meaning that it's not practical for us to make a fully compatible replacement for codejail at the moment.

Implementing as a Service
  It's possible to do this evaluation by implementing the code sandboxing functionality in a separate service (as the `codejail service <https://github.com/eduNEXT/codejailservice>`_ does). This library approach was chosen for a few reasons:

  * It simplifies the development and deployment, allowing us to test our ideas and learn our Wasm-specific lessons more quickly.
  * As long as memory usage is reasonable, an in-process approach may be acceptable for many site operators in the long term.
  * Even if a separate service becomes our default long term deployment option, developing this library first is not a wasted effort, since we would almost certainly build on it when creating a service.
