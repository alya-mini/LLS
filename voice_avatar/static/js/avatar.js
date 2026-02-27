export class AvatarStudio {
  constructor(canvas) {
    this.canvas = canvas;
    this.scene = new THREE.Scene();
    this.clock = new THREE.Clock();
    this.mouth = { influence: 0 };

    this.camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    this.camera.position.set(0, 1.4, 3.4);

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));

    const hemi = new THREE.HemisphereLight(0x99bbff, 0x220022, 1.2);
    const key = new THREE.DirectionalLight(0xffffff, 1.1);
    key.position.set(3, 4, 2);
    this.scene.add(hemi, key);

    this.model = null;
    this.mixer = null;
    this.loader = new THREE.GLTFLoader();
    this.resize();
    window.addEventListener("resize", () => this.resize());
    this.animate();
  }

  async loadAvatar(url) {
    if (this.model) this.scene.remove(this.model);
    const gltf = await this.loader.loadAsync(url);
    this.model = gltf.scene;
    this.model.position.y = -1;
    this.scene.add(this.model);

    if (gltf.animations?.length) {
      this.mixer = new THREE.AnimationMixer(this.model);
      const idle = this.mixer.clipAction(gltf.animations[0]);
      idle.play();
    }
  }

  applyMorphs({ smile = 0, brow = 0, mouth = 0 }) {
    if (!this.model) return;
    this.model.traverse((obj) => {
      if (!obj.morphTargetInfluences) return;
      obj.morphTargetInfluences[0] = mouth;
      obj.morphTargetInfluences[1] = smile;
      obj.morphTargetInfluences[2] = brow;
    });
  }

  resize() {
    const w = this.canvas.clientWidth || this.canvas.parentElement.clientWidth;
    const h = this.canvas.clientHeight || this.canvas.parentElement.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h, false);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    const dt = this.clock.getDelta();
    this.mixer?.update(dt);
    if (this.model) this.model.rotation.y += 0.001;
    this.renderer.render(this.scene, this.camera);
  }
}

export async function fetchAvatars() {
  const res = await fetch('/api/avatars');
  const data = await res.json();
  return data.avatars;
}
