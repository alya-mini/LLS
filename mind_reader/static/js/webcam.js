window.App = window.App || {};
(() => {
  const setupWebcam = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' }, audio: true });
      App.state.localStream = stream;
      App.addVideo('local', stream, `${App.state.name} (sen)`);

      const hiddenVideo = document.createElement('video');
      hiddenVideo.srcObject = stream;
      hiddenVideo.play();

      const faceMesh = new FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
      });
      faceMesh.setOptions({ maxNumFaces: 1, refineLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
      faceMesh.onResults((results) => {
        if (results.multiFaceLandmarks?.[0]) {
          App.latestLandmarks = results.multiFaceLandmarks[0];
        }
      });

      const cam = new Camera(hiddenVideo, {
        onFrame: async () => {
          await faceMesh.send({ image: hiddenVideo });
        },
        width: 640,
        height: 480
      });
      cam.start();
    } catch (e) {
      document.getElementById('status').textContent = `Kamera hatası: ${e.message}`;
    }
  };

  App.setupWebcam = setupWebcam;
})();
