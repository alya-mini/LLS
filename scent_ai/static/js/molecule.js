window.MoleculeModule = (() => {
  let scene, camera, renderer, atoms = [];

  function init() {
    const host = document.getElementById('moleculeViewport');
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(55, host.clientWidth / host.clientHeight, 0.1, 1000);
    camera.position.z = 7;

    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(host.clientWidth, host.clientHeight);
    host.innerHTML = '';
    host.appendChild(renderer.domElement);

    const light = new THREE.PointLight(0x7dd3fc, 1.4);
    light.position.set(3, 4, 5);
    scene.add(light);
    scene.add(new THREE.AmbientLight(0xffffff, 0.6));

    rebuild('hex-ring');
    animate();
  }

  function rebuild(style = 'hex-ring') {
    atoms.forEach((a) => scene.remove(a));
    atoms = [];
    const count = style === 'double-helix' ? 26 : style === 'orbital' ? 20 : 14;

    for (let i = 0; i < count; i++) {
      const atom = new THREE.Mesh(
        new THREE.SphereGeometry(0.17, 16, 16),
        new THREE.MeshStandardMaterial({ color: i % 2 ? 0x22d3ee : 0xa78bfa })
      );
      atom.position.set(
        Math.sin(i * 0.6) * (style === 'orbital' ? 3 : 2),
        style === 'double-helix' ? (i - count / 2) * 0.25 : Math.cos(i * 0.6) * 1.4,
        Math.cos(i * 0.6) * (style === 'orbital' ? 2 : 1)
      );
      scene.add(atom);
      atoms.push(atom);
    }
  }

  function animate() {
    requestAnimationFrame(animate);
    atoms.forEach((a, i) => {
      a.rotation.x += 0.01;
      a.rotation.y += 0.01;
      a.position.z += Math.sin(Date.now() * 0.001 + i) * 0.001;
    });
    renderer.render(scene, camera);
  }

  return { init, rebuild };
})();
