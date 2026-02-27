window.App = window.App || {};
(() => {
  const softEmotionFromLandmarks = () => {
    const lm = App.latestLandmarks;
    if (!lm) return [0.33, 0.33, 0.34];
    const mouthOpen = Math.abs(lm[13].y - lm[14].y);
    const browRaise = Math.abs(lm[70].y - lm[105].y);
    const surprise = Math.min(1, mouthOpen * 25 + browRaise * 15);
    const happy = Math.min(1, Math.max(0, 1 - mouthOpen * 10));
    const sad = Math.min(1, Math.max(0, browRaise * 8));
    const sum = happy + sad + surprise || 1;
    return [happy / sum, sad / sum, surprise / sum];
  };

  const estimatePupil = () => {
    const lm = App.latestLandmarks;
    if (!lm) return 0.5;
    const leftEye = Math.abs(lm[159].y - lm[145].y);
    const rightEye = Math.abs(lm[386].y - lm[374].y);
    return Math.max(0, Math.min(1, ((leftEye + rightEye) * 45)));
  };

  const startEmotionLoop = () => {
    setInterval(() => {
      App.currentEmotion = softEmotionFromLandmarks();
      App.currentPupil = estimatePupil();
    }, 150);
  };

  App.startEmotionLoop = startEmotionLoop;
})();
