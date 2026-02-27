window.Food3D = {
  init(container) {
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0b1020');

    const camera = new THREE.PerspectiveCamera(50, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 1.2, 4);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    const light = new THREE.DirectionalLight(0xffd89a, 1.3);
    light.position.set(3, 5, 2);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.5));

    const plate = new THREE.Mesh(
      new THREE.CylinderGeometry(1.6, 1.7, 0.15, 48),
      new THREE.MeshStandardMaterial({ color: 0xf8fafc, metalness: 0.2, roughness: 0.3 })
    );
    scene.add(plate);

    const food = new THREE.Mesh(
      new THREE.TorusKnotGeometry(0.55, 0.2, 140, 16),
      new THREE.MeshStandardMaterial({ color: 0xff8a3d, metalness: 0.4, roughness: 0.25 })
    );
    food.position.y = 0.38;
    scene.add(food);

    function animate() {
      requestAnimationFrame(animate);
      food.rotation.y += 0.01;
      renderer.render(scene, camera);
    }
    animate();

    window.addEventListener('resize', () => {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    });
  }
};
