
// Register controller input component
AFRAME.registerComponent('controller-input', {
    init: function () {
        const el = this.el;
        const debugText = document.getElementById('debug-text');

        function log(msg) {
            console.log(msg);
            if (debugText) {
                debugText.setAttribute('value', msg);
            }
        }

        // Button A (Right Hand usually)
        el.addEventListener('abuttondown', function (evt) {
            log("Button A pressed");
        });
        el.addEventListener('abuttonup', function (evt) {
            log("Button A released");
        });

        // Button B (Right Hand usually)
        el.addEventListener('bbuttondown', function (evt) {
            log("Button B pressed");
        });
        el.addEventListener('bbuttonup', function (evt) {
            log("Button B released");
        });

        // Button X (Left Hand usually)
        el.addEventListener('xbuttondown', function (evt) {
            log("Button X pressed");
        });
        el.addEventListener('xbuttonup', function (evt) {
            log("Button X released");
        });

        // Button Y (Left Hand usually)
        el.addEventListener('ybuttondown', function (evt) {
            log("Button Y pressed");
        });
        el.addEventListener('ybuttonup', function (evt) {
            log("Button Y released");
        });

        // Menu Button
        el.addEventListener('menubuttondown', function (evt) {
            log("Menu Button pressed");
        });
        el.addEventListener('menubuttonup', function (evt) {
            log("Menu Button released");
        });

        // Thumbstick Moved
        el.addEventListener('thumbstickmoved', function (evt) {
            let x = evt.detail.x;
            let y = evt.detail.y;
            if (Math.abs(x) > 0.1 || Math.abs(y) > 0.1) {
                log(`Thumbstick: ${x.toFixed(2)}, ${y.toFixed(2)}`);
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', () => {
    // Get video players and control elements
    const vr180Player = document.getElementById('vr180-player');
    const vr360Player = document.getElementById('vr360-player');
    const playPauseBtn = document.getElementById('play-pause-btn');
    const volumeControl = document.getElementById('volume-control');
    // Get the video elements
    const vrVideo = document.querySelector('#vr-video');

    function setPlayUrl(url) {
        if (vrVideo.src !== url) {
            vrVideo.src = url;
            vrVideo.load(); // 确保加载视频
        }
    }

    // Function to play/pause video
    function togglePlayPause() {
        if (vrVideo.paused) {
            vrVideo.play();
            playPauseBtn.setAttribute('text', 'value', 'Pause');
            VRUtils.updatePlayButtonVisuals('play-pause-btn', true);
        } else {
            vrVideo.pause();
            playPauseBtn.setAttribute('text', 'value', 'Play');
            VRUtils.updatePlayButtonVisuals('play-pause-btn', false);
        }
    }

    // Function to adjust volume
    function changeVolume(evt) {
        // Note: This relies on a component emitting 'input' or 'change' on the cylinder which is not standard.
        // Leaving as is per user code, but ensuring 'evt.detail.target.value' exists would be needed.
        if (evt.detail && evt.detail.target && evt.detail.target.value !== undefined) {
            let volume = evt.detail.target.value;
            vrVideo.volume = volume;
        }
    }

    // Function to detect VR180 and VR360 videos based on the file name (simple check)
    function isVR180(videoPath) {
        return videoPath.toLowerCase().includes("vr180");
    }

    var inited = false;

    function initVideo() {
        const videoPath = "/static/upload/video/[MMD][愛包ダンスホール][FUWAMOCO][VR180][8K].mp4"; // Update with actual path
        if (!inited) {
            setPlayUrl(videoPath)
            if (isVR180(videoPath)) {
                document.getElementById('vr180').setAttribute('visible', 'true');
                document.getElementById('vr360').setAttribute('visible', 'false');
            } else {
                document.getElementById('vr180').setAttribute('visible', 'false');
                document.getElementById('vr360').setAttribute('visible', 'true');
            }
            inited = true;
        }
    }

    // JavaScript to toggle between VR180 and VR360 video
    const scene = document.querySelector('a-scene');
    if (scene) {
        scene.addEventListener('click', initVideo);
    }

    // Controller support for initialization (trigger press)
    // Wait for components to initialize or just attach listener
    const controllers = document.querySelectorAll('[laser-controls]');
    controllers.forEach(controller => {
        controller.addEventListener('triggerdown', initVideo);
    });

    // Add event listeners for controls
    if (playPauseBtn) playPauseBtn.addEventListener('click', togglePlayPause);
    if (volumeControl) volumeControl.addEventListener('input', changeVolume);
});


