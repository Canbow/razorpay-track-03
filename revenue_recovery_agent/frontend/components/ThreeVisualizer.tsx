'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

interface ThreeVisualizerProps {
  activeNode?: string | null;
  className?: string;
}

export default function ThreeVisualizer({ activeNode, className = '' }: ThreeVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [isAutoRotate, setIsAutoRotate] = useState(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 1. Scene, Camera, Renderer
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      1000
    );
    camera.position.set(0, 18, 42);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const coreLight = new THREE.PointLight(0x00b9f1, 3, 50);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);

    const dirLight = new THREE.DirectionalLight(0x0082ff, 1.5);
    dirLight.position.set(10, 20, 15);
    scene.add(dirLight);

    // 3. Central AI Recovery Core
    const coreGroup = new THREE.Group();

    // Central Icosahedron
    const coreGeo = new THREE.IcosahedronGeometry(4.2, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x002244,
      emissive: 0x0082ff,
      emissiveIntensity: 0.6,
      roughness: 0.2,
      metalness: 0.8,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(coreMesh);

    // Wireframe Cage
    const wireGeo = new THREE.IcosahedronGeometry(4.8, 1);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x00b9f1,
      wireframe: true,
      transparent: true,
      opacity: 0.4,
    });
    const wireMesh = new THREE.Mesh(wireGeo, wireMat);
    coreGroup.add(wireMesh);

    // Outer Rotating Energy Rings
    const ringGeo1 = new THREE.TorusGeometry(6.5, 0.08, 16, 100);
    const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.7 });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 2.5;
    coreGroup.add(ring1);

    const ringGeo2 = new THREE.TorusGeometry(7.5, 0.06, 16, 100);
    const ringMat2 = new THREE.MeshBasicMaterial({ color: 0x00b9f1, transparent: true, opacity: 0.6 });
    const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
    ring2.rotation.y = Math.PI / 3;
    coreGroup.add(ring2);

    scene.add(coreGroup);

    // 4. Orbiting Financial Rail Nodes
    interface RailNodeInfo {
      name: string;
      label: string;
      color: number;
      angle: number;
      distance: number;
      mesh?: THREE.Mesh;
    }

    const railNodes: RailNodeInfo[] = [
      { name: 'NPCI_UPI', label: 'NPCI UPI Switch', color: 0x10b981, angle: 0, distance: 16 },
      { name: 'HDFC_CBS', label: 'HDFC Bank CBS', color: 0x0082ff, angle: (Math.PI * 2) / 5, distance: 17 },
      { name: 'SBI_SWITCH', label: 'SBI Gateway', color: 0x00b9f1, angle: (Math.PI * 4) / 5, distance: 16 },
      { name: 'MANDATE_CLEAR', label: 'e-NACH Mandate', color: 0xf59e0b, angle: (Math.PI * 6) / 5, distance: 18 },
      { name: 'DYNAMIC_PORTAL', label: 'Dynamic Link Fallback', color: 0xa855f7, angle: (Math.PI * 8) / 5, distance: 17 },
    ];

    const nodesGroup = new THREE.Group();
    const curves: THREE.QuadraticBezierCurve3[] = [];

    railNodes.forEach((node) => {
      const x = Math.cos(node.angle) * node.distance;
      const z = Math.sin(node.angle) * node.distance;
      const y = Math.sin(node.angle * 2) * 2;

      // Node Sphere
      const nGeo = new THREE.SphereGeometry(1.4, 32, 32);
      const nMat = new THREE.MeshStandardMaterial({
        color: node.color,
        emissive: node.color,
        emissiveIntensity: 0.5,
        roughness: 0.3,
        metalness: 0.7,
      });
      const nMesh = new THREE.Mesh(nGeo, nMat);
      nMesh.position.set(x, y, z);
      nMesh.userData = { name: node.name, label: node.label };
      nodesGroup.add(nMesh);
      node.mesh = nMesh;

      // Outer Halo Ring
      const hGeo = new THREE.TorusGeometry(2.0, 0.05, 16, 64);
      const hMat = new THREE.MeshBasicMaterial({ color: node.color, transparent: true, opacity: 0.5 });
      const hMesh = new THREE.Mesh(hGeo, hMat);
      hMesh.position.set(x, y, z);
      hMesh.rotation.x = Math.PI / 2;
      nodesGroup.add(hMesh);

      // Curve connecting to core
      const curve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(x, y, z),
        new THREE.Vector3(x * 0.5, y + 4, z * 0.5),
        new THREE.Vector3(0, 0, 0)
      );
      curves.push(curve);

      // Spline visualization line
      const points = curve.getPoints(40);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({ color: node.color, transparent: true, opacity: 0.35 });
      const line = new THREE.Line(lineGeo, lineMat);
      scene.add(line);
    });

    scene.add(nodesGroup);

    // 5. Flowing Particle Streams Along Curves
    const particleCountPerCurve = 15;
    const particleGeos: { curve: THREE.QuadraticBezierCurve3; t: number; speed: number; mesh: THREE.Mesh }[] = [];
    const pGeo = new THREE.SphereGeometry(0.22, 12, 12);

    curves.forEach((curve, cIdx) => {
      const col = railNodes[cIdx].color;
      const pMat = new THREE.MeshBasicMaterial({ color: col });
      for (let i = 0; i < particleCountPerCurve; i++) {
        const pMesh = new THREE.Mesh(pGeo, pMat);
        scene.add(pMesh);
        particleGeos.push({
          curve,
          t: (i / particleCountPerCurve) + Math.random() * 0.05,
          speed: 0.003 + Math.random() * 0.002,
          mesh: pMesh,
        });
      }
    });

    // 6. Starfield / Floating Particle Dust
    const dustCount = 300;
    const dustGeo = new THREE.BufferGeometry();
    const dustPos = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount * 3; i += 3) {
      dustPos[i] = (Math.random() - 0.5) * 80;
      dustPos[i + 1] = (Math.random() - 0.5) * 40;
      dustPos[i + 2] = (Math.random() - 0.5) * 80;
    }
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    const dustMat = new THREE.PointsMaterial({ color: 0x64748b, size: 0.35, transparent: true, opacity: 0.5 });
    const dust = new THREE.Points(dustGeo, dustMat);
    scene.add(dust);

    // 7. Mouse Orbiting Interaction
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let rotationAngleY = 0;
    let rotationAngleX = 0.3;

    const handleMouseDown = (e: MouseEvent) => {
      isDragging = true;
      prevMouseX = e.clientX;
      prevMouseY = e.clientY;
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging) {
        const deltaX = e.clientX - prevMouseX;
        const deltaY = e.clientY - prevMouseY;
        rotationAngleY += deltaX * 0.005;
        rotationAngleX = Math.max(-0.5, Math.min(1.2, rotationAngleX + deltaY * 0.005));
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const zoomDelta = e.deltaY * 0.03;
      camera.position.z = Math.max(25, Math.min(65, camera.position.z + zoomDelta));
    };

    container.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    container.addEventListener('wheel', handleWheel, { passive: false });

    // 8. Animation Loop
    let animationFrameId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      // Auto-rotation when not manually dragging
      if (isAutoRotate && !isDragging) {
        rotationAngleY += 0.002;
      }

      // Camera Orbit Position calculation
      const radius = camera.position.z;
      camera.position.x = radius * Math.sin(rotationAngleY) * Math.cos(rotationAngleX);
      camera.position.y = radius * Math.sin(rotationAngleX) + 6;
      camera.position.z = radius * Math.cos(rotationAngleY) * Math.cos(rotationAngleX);
      camera.lookAt(0, 2, 0);

      // Pulse Core
      coreMesh.rotation.y = elapsedTime * 0.4;
      coreMesh.rotation.x = elapsedTime * 0.2;
      wireMesh.rotation.y = -elapsedTime * 0.3;
      ring1.rotation.z = elapsedTime * 0.6;
      ring2.rotation.x = -elapsedTime * 0.5;

      const pulseScale = 1 + Math.sin(elapsedTime * 3) * 0.03;
      coreMesh.scale.set(pulseScale, pulseScale, pulseScale);

      // Animate flowing transaction particles
      particleGeos.forEach((p) => {
        p.t += p.speed;
        if (p.t > 1) p.t = 0;
        const pos = p.curve.getPoint(p.t);
        p.mesh.position.copy(pos);
      });

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize Handling
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    // 10. Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      container.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      container.removeEventListener('wheel', handleWheel);
      window.removeEventListener('resize', handleResize);

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [isAutoRotate]);

  return (
    <div className={`relative w-full h-[460px] glass-panel rounded-2xl overflow-hidden border border-brand-border/80 ${className}`}>
      <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Overlay UI Controls */}
      <div className="absolute top-4 left-4 z-10 flex items-center space-x-2 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700/80 text-xs">
        <div className="w-2 h-2 rounded-full bg-brand-cyan animate-ping" />
        <span className="font-semibold text-white">Three.js 3D Financial Network Topology</span>
        <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">(Interactive 360° Orbit)</span>
      </div>

      <div className="absolute top-4 right-4 z-10 flex items-center space-x-2">
        <button
          onClick={() => setIsAutoRotate(!isAutoRotate)}
          className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-[11px] text-slate-300 border border-slate-700 transition"
        >
          {isAutoRotate ? 'Pause Rotation' : 'Auto Rotate'}
        </button>
      </div>

      {/* 3D Legend Strip */}
      <div className="absolute bottom-3 left-4 right-4 z-10 flex flex-wrap items-center justify-between gap-2 bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-800 text-[11px]">
        <div className="flex items-center space-x-4">
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span className="text-slate-300">NPCI UPI Intent (60% Conv)</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-brand-blue" />
            <span className="text-slate-300">HDFC/SBI Cooldown Retries (+12h)</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="text-slate-300">e-NACH Mandates</span>
          </span>
          <span className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400" />
            <span className="text-slate-300">Dynamic Multi-Rail Links</span>
          </span>
        </div>
        <div className="text-slate-400 text-[10px] italic">
          Tip: Drag with mouse to rotate scene | Scroll to zoom
        </div>
      </div>
    </div>
  );
}
