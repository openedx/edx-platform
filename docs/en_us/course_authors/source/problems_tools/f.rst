.. _Appendix F:

Files for the Example Custom JavaScript Display and Grading Problem
================================================================================

For the example :ref:`Custom JavaScript Display and Grading` problem, you need the following files. You can find
instructions for obtaining each
of these files below. After you obtain the files, add all of them to the **Files & Uploads** page in Studio.

- :ref:`webGLDemo.html`
- :ref:`webGLDemo.css`
- :ref:`webGLDemo.js`
- `three.min.js <http://threejs.org>`_

For the **webGLDemo.html**, **webGLDemo.js**, and **webGLDemo.css** files, copy the code provided
for each file into a text editor, and then save each file. Make sure to use the correct
file name extension when you save each file.

For the **three.min.js** library file, go to the `three.js home page <http://threejs.org>`_ page,
and then click **Download** in
the left pane. After the .zip file has finished downloading, open the .zip file, and then
open the **build** folder to access the **three.min.js** file.

.. note:: If you need to bypass the same-origin policy (SOP), you also need the
          `jschannel.js <https://github.com/mozilla/jschannel/blob/master/src/jschannel.js>`_ file. On
          the `jschannel.js <https://github.com/mozilla/jschannel/blob/master/src/jschannel.js>`_
          web page, copy the code for the file into a text editor, and then save the file as **jschannel.js**.

.. _webGLDemo.html:

webGLDemo.html
--------------

If you **don't** need to bypass the SOP, use the following code.

::

    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" type="text/css" href="webGLDemo.css">
        <script src="three.min.js"></script>
        <script src="webGLDemo.js" defer='defer'></script>
    </head>
    <body>
        <div id="container"></div>
    </body>
    </html>

If you need to bypass the SOP, use the following code.

::

    <!DOCTYPE html>
    <html>
    <head>
        <link rel="stylesheet" type="text/css" href="webGLDemo.css">
        <script src="jschannel.js"></script>
        <script src="three.min.js"></script>
        <script src="webGLDemo.js" defer='defer'></script>
    </head>
    <body>
        <div id="container"></div>
    </body>
    </html>

.. _webGLDemo.css:

webGLDemo.css
-------------

::

    #container {
    background-color: black;
    width: 400px;
    height:400px;
    }


.. _webGLDemo.js:

webGLDemo.js
------------

::

    var WebGLDemo = (function() {

        var width = 400, height = 400;
        var container, renderer, scene, camera, projector,
            ambientlight, directionalLight,
            cylinder, cube, nonSelectedMaterial, selectedMaterial;
        // Revolutions per second
        var angularSpeed = 0.5, lastTime = 0;
        var state = {
                'selectedObjects': {
                    'cylinder': false,
                    'cube': false
                }
            },
            channel;

        // Establish a channel only if this application is embedded in an iframe.
        // This will let the parent window communicate with this application using
        // RPC and bypass SOP restrictions.
        if (window.parent !== window) {
            channel = Channel.build({
                window: window.parent,
                origin: "*",
                scope: "JSInput"
            });

            channel.bind("getGrade", getGrade);
            channel.bind("getState", getState);
            channel.bind("setState", setState);
        }

        function init() {
            container = document.getElementById('container');
            // Renderer
            // First check if WebGL is supported. If not, rely on the canvas
            // render and use a scene with less triangles as it is slow.
            var testCanvas = document.createElement("canvas");
            var webglContext = null;
            var contextNames = ["experimental-webgl", "webgl", "moz-webgl",
                                "webkit-3d"];
            var radiusSegments, heightSegments;
            for (var i = 0; i < contextNames.length; i++) {
                try {
                    webglContext = testCanvas.getContext(contextNames[i]);
                    if (webglContext) {
                        break;
                    }
                }
                catch (e) {
                }
            }

            if (webglContext) {
                renderer = new THREE.WebGLRenderer({antialias:true});
                radiusSegments = 50;
                heightSegments = 50;
            }
            else {
                renderer = new THREE.CanvasRenderer();
                radiusSegments = 10;
                heightSegments = 10;
            }

            renderer.setSize(width, height);
            renderer.setClearColor(0x000000, 1);
            container.appendChild(renderer.domElement);

            // Scene
            scene = new THREE.Scene();

            // Camera
            camera = new THREE.PerspectiveCamera(45, width/height, 1, 1000);
            camera.position.z = 700;

            // Materials
            unselectedMaterial = new THREE.MeshPhongMaterial({
                specular: '#a9fcff',
                color: '#00abb1',
                emissive: '#006063',
                shininess: 100
            });

            selectedMaterial = new THREE.MeshPhongMaterial({
                specular: '#a9fcff',
                color: '#abb100',
                emissive: '#606300',
                shininess: 100
            });

            if (!webglContext) {
                unselectedMaterial.overdraw = 1.0;
                selectedMaterial.overdraw = 1.0;
            }

            // Cylinder: bottomRadius, topRadius, height, segmentsRadius,
            //           segmentsHeight
            cylinder = new THREE.Mesh(new THREE.CylinderGeometry(0, 100, 150,
                                                                radiusSegments,
                                                                heightSegments,
                                                                false),
                                                                unselectedMaterial);
            cylinder.position.x = -125;
            cylinder.overdraw = true;
            scene.add(cylinder);

            // Cube
            cube = new THREE.Mesh(new THREE.CubeGeometry(120, 120, 120),
                                                        unselectedMaterial);
            cube.position.x = 125;
            cube.overdraw = true;
            scene.add(cube);

            // Ambient light
            ambientLight = new THREE.AmbientLight(0x222222);
            scene.add(ambientLight);

            // Directional light
            directionalLight = new THREE.DirectionalLight(0xffffff);
            directionalLight.position.set(1, 1, 1).normalize();
            scene.add(directionalLight);

            // Used to select element with mouse click
            projector = new THREE.Projector();

            renderer.domElement.addEventListener('click', onMouseClick, false);

            // Start animation
            animate();
        }

        // This function is executed on each animation frame
        function animate() {
            // Request new frame
            requestAnimationFrame(animate);
            render();
        }

        function render() {
            // Update
            var time = (new Date()).getTime(),
                timeDiff = time - lastTime,
                angleChange = angularSpeed * timeDiff * 2 * Math.PI / 1000;
            cylinder.rotation.x += angleChange;
            cylinder.rotation.z += angleChange;
            cube.rotation.x += angleChange;
            cube.rotation.y += angleChange;
            lastTime = time;

            // Render
            renderer.render(scene, camera);
        }

        function onMouseClick(event) {
            var vector, raycaster, intersects;

            vector = new THREE.Vector3((event.clientX / width) * 2 - 1,
                                    -(event.clientY / height) * 2 + 1, 1);
            projector.unprojectVector(vector, camera);
            raycaster = new THREE.Raycaster(camera.position,
                                            vector.sub(camera.position).normalize());
            intersects = raycaster.intersectObjects(scene.children);

            if (intersects.length > 0) {
                if (intersects[0].object === cylinder) {
                    state.selectedObjects.cylinder = !state.selectedObjects.cylinder;
                }
                else if (intersects[0].object === cube) {
                    state.selectedObjects.cube = !state.selectedObjects.cube;
                }
                updateMaterials();
            }
        }

        function updateMaterials() {
            if (state.selectedObjects.cylinder) {
                cylinder.material =  selectedMaterial;
            }
            else {
                cylinder.material =  unselectedMaterial;
            }

            if (state.selectedObjects.cube) {
                cube.material =  selectedMaterial;
            }
            else {
                cube.material =  unselectedMaterial;
            }
        }

        init();

        function getGrade() {
            // The following return value may or may not be used to grade
            // server-side.
            // If getState and setState are used, then the Python grader also gets
            // access to the return value of getState and can choose it instead to
            // grade.
            return JSON.stringify(state['selectedObjects']);
        }

        function getState() {
            return JSON.stringify(state);
        }

        // This function will be called with 1 argument when JSChannel is not used,
        // 2 otherwise. In the latter case, the first argument is a transaction
        // object that will not be used here
        // (see http://mozilla.github.io/jschannel/docs/)
        function setState() {
            stateStr = arguments.length === 1 ? arguments[0] : arguments[1];
            state = JSON.parse(stateStr);
            updateMaterials();
        }

        return {
            getState: getState,
            setState: setState,
            getGrade: getGrade
        };
    }());
