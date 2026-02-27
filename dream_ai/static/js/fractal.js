(function () {
  const canvas = document.getElementById('fractalCanvas');
  const gl = canvas.getContext('webgl');
  let emotion = 0.5;

  function resize() {
    canvas.width = innerWidth;
    canvas.height = innerHeight;
    if (gl) gl.viewport(0, 0, canvas.width, canvas.height);
  }
  addEventListener('resize', resize);
  resize();

  if (!gl) {
    const ctx = canvas.getContext('2d');
    let t = 0;
    (function draw2d() {
      t += 0.01;
      const g = ctx.createRadialGradient(
        canvas.width * (0.5 + 0.1 * Math.sin(t)),
        canvas.height * 0.5,
        50,
        canvas.width / 2,
        canvas.height / 2,
        canvas.width
      );
      g.addColorStop(0, `hsla(${240 + 120 * emotion},90%,65%,0.55)`);
      g.addColorStop(1, '#020005');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      requestAnimationFrame(draw2d);
    })();
    window.setFractalEmotion = (v) => { emotion = Number(v) || 0.5; };
    return;
  }

  const vs = `attribute vec2 p; void main(){gl_Position=vec4(p,0.,1.);}`;
  const fs = `precision mediump float;
  uniform vec2 r; uniform float t; uniform float e;
  vec3 pal(float x){ return 0.5+0.5*cos(6.2831*(vec3(0.2,0.4,0.7)+x)); }
  void main(){
    vec2 uv=(gl_FragCoord.xy-r*0.5)/min(r.x,r.y);
    vec2 z=uv; float acc=0.0;
    for(int i=0;i<60;i++){
      z=vec2(z.x*z.x-z.y*z.y,2.0*z.x*z.y)+vec2(0.2*sin(t*.2),0.2*cos(t*.15+e*2.0));
      acc += exp(-dot(z,z)*1.5);
    }
    vec3 c=pal(acc*0.12+e*0.5+t*0.03);
    gl_FragColor=vec4(c*acc*1.2,1.0);
  }`;

  function compile(type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return s;
  }
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, vs));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, fs));
  gl.linkProgram(prog);
  gl.useProgram(prog);

  const buf = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
  const loc = gl.getAttribLocation(prog, 'p');
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  const rLoc = gl.getUniformLocation(prog, 'r');
  const tLoc = gl.getUniformLocation(prog, 't');
  const eLoc = gl.getUniformLocation(prog, 'e');

  function render(ms) {
    gl.uniform2f(rLoc, canvas.width, canvas.height);
    gl.uniform1f(tLoc, ms * 0.001);
    gl.uniform1f(eLoc, emotion);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    requestAnimationFrame(render);
  }
  requestAnimationFrame(render);

  window.setFractalEmotion = (v) => { emotion = Number(v) || 0.5; };
})();
