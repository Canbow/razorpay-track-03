'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { Layers, Network, ShieldCheck, CheckCircle, BarChart3, ArrowRight, Clock, Smartphone, AlertOctagon, Terminal } from 'lucide-react';
import RecoveryComparisonChart from './RecoveryComparisonChart';
import { BenchmarkKPIs } from '@/lib/types';

interface ThreeVisualizerProps {
  activeNode?: string | null;
  className?: string;
  kpis?: BenchmarkKPIs;
}

export default function ThreeVisualizer({ activeNode, className = '', kpis }: ThreeVisualizerProps) {
  // Mode: 'BAR_CHART' (Default visual 2D bar chart), '2D_FLOW' (4-stage node graph), or '3D_TOPOLOGY'
  const [viewMode, setViewMode] = useState<'BAR_CHART' | '2D_FLOW' | '3D_TOPOLOGY'>('BAR_CHART');
  const [active2DStage, setActive2DStage] = useState<string>('DIAGNOSE');

  const containerRef = useRef<HTMLDivElement>(null);
  const [isAutoRotate, setIsAutoRotate] = useState(true);

  // 3D Three.js Lifecycle
  useEffect(() => {
    if (viewMode !== '3D_TOPOLOGY') return;

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

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);

    // 2. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
    scene.add(ambientLight);

    const coreLight = new THREE.PointLight(0x00b9f1, 2.5, 60);
    coreLight.position.set(0, 0, 0);
    scene.add(coreLight);

    const dirLight = new THREE.DirectionalLight(0x0082ff, 1.2);
    dirLight.position.set(15, 20, 20);
    scene.add(dirLight);

    // 3. Central AI Recovery Core
    const coreGroup = new THREE.Group();

    const coreGeo = new THREE.IcosahedronGeometry(4.2, 2);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x002244,
      emissive: 0x0082ff,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.7,
    });
    const coreMesh = new THREE.Mesh(coreGeo, coreMat);
    coreGroup.add(coreMesh);

    const wireGeo = new THREE.IcosahedronGeometry(4.7, 1);
    const wireMat = new THREE.MeshBasicMaterial({
      color: 0x00b9f1,
      wireframe: true,
      transparent: true,
      opacity: 0.4,
    });
    const wireMesh = new THREE.Mesh(wireGeo, wireMat);
    coreGroup.add(wireMesh);

    const ringGeo1 = new THREE.TorusGeometry(6.5, 0.08, 16, 100);
    const ringMat1 = new THREE.MeshBasicMaterial({ color: 0x10b981, transparent: true, opacity: 0.6 });
    const ring1 = new THREE.Mesh(ringGeo1, ringMat1);
    ring1.rotation.x = Math.PI / 2.5;
    coreGroup.add(ring1);

    const ringGeo2 = new THREE.TorusGeometry(7.5, 0.06, 16, 100);
    const ringMat2 = new THREE.MeshBasicMaterial({ color: 0x00b9f1, transparent: true, opacity: 0.5 });
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
      const y = Math.sin(node.angle * 2) * 1.5;

      const nGeo = new THREE.SphereGeometry(1.3, 32, 32);
      const nMat = new THREE.MeshStandardMaterial({
        color: node.color,
        emissive: node.color,
        emissiveIntensity: 0.45,
        roughness: 0.3,
        metalness: 0.7,
      });
      const nMesh = new THREE.Mesh(nGeo, nMat);
      nMesh.position.set(x, y, z);
      nodesGroup.add(nMesh);

      const hGeo = new THREE.TorusGeometry(1.9, 0.05, 16, 64);
      const hMat = new THREE.MeshBasicMaterial({ color: node.color, transparent: true, opacity: 0.45 });
      const hMesh = new THREE.Mesh(hGeo, hMat);
      hMesh.position.set(x, y, z);
      hMesh.rotation.x = Math.PI / 2;
      nodesGroup.add(hMesh);

      const curve = new THREE.QuadraticBezierCurve3(
        new THREE.Vector3(x, y, z),
        new THREE.Vector3(x * 0.5, y + 3, z * 0.5),
        new THREE.Vector3(0, 0, 0)
      );
      curves.push(curve);

      const points = curve.getPoints(40);
      const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
      const lineMat = new THREE.LineBasicMaterial({ color: node.color, transparent: true, opacity: 0.3 });
      const line = new THREE.Line(lineGeo, lineMat);
      scene.add(line);
    });

    scene.add(nodesGroup);

    // 5. Flowing Particle Streams
    const particleCountPerCurve = 14;
    const particleGeos: { curve: THREE.QuadraticBezierCurve3; t: number; speed: number; mesh: THREE.Mesh }[] = [];
    const pGeo = new THREE.SphereGeometry(0.2, 12, 12);

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

    // 6. Floating Ambient Dust
    const dustCount = 200;
    const dustGeo = new THREE.BufferGeometry();
    const dustPos = new Float32Array(dustCount * 3);
    for (let i = 0; i < dustCount * 3; i += 3) {
      dustPos[i] = (Math.random() - 0.5) * 80;
      dustPos[i + 1] = (Math.random() - 0.5) * 40;
      dustPos[i + 2] = (Math.random() - 0.5) * 80;
    }
    dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
    const dustMat = new THREE.PointsMaterial({ color: 0x64748b, size: 0.35, transparent: true, opacity: 0.4 });
    const dust = new THREE.Points(dustGeo, dustMat);
    scene.add(dust);

    // 7. Mouse Orbiting Interaction (FIXED CAMERA RADIUS TO PREVENT ZOOM COLLAPSE)
    let isDragging = false;
    let prevMouseX = 0;
    let prevMouseY = 0;
    let rotationAngleY = 0.5;
    let rotationAngleX = 0.35;
    let cameraRadius = 46;

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
        rotationAngleX = Math.max(-0.35, Math.min(0.75, rotationAngleX + deltaY * 0.005));
        prevMouseX = e.clientX;
        prevMouseY = e.clientY;
      }
    };

    const handleMouseUp = () => {
      isDragging = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      cameraRadius = Math.max(30, Math.min(70, cameraRadius + e.deltaY * 0.04));
    };

    container.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    container.addEventListener('wheel', handleWheel, { passive: false });

    // 8. Animation Loop
    let animationFrameId: number;
    const clock = new THREE.Clock();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const elapsedTime = clock.getElapsedTime();

      if (isAutoRotate && !isDragging) {
        rotationAngleY += 0.0018;
      }

      camera.position.x = cameraRadius * Math.sin(rotationAngleY) * Math.cos(rotationAngleX);
      camera.position.y = cameraRadius * Math.sin(rotationAngleX) + 3;
      camera.position.z = cameraRadius * Math.cos(rotationAngleY) * Math.cos(rotationAngleX);
      camera.lookAt(0, 0, 0);

      coreMesh.rotation.y = elapsedTime * 0.3;
      coreMesh.rotation.x = elapsedTime * 0.15;
      wireMesh.rotation.y = -elapsedTime * 0.25;
      ring1.rotation.z = elapsedTime * 0.4;
      ring2.rotation.x = -elapsedTime * 0.35;

      const pulseScale = 1 + Math.sin(elapsedTime * 2.5) * 0.025;
      coreMesh.scale.set(pulseScale, pulseScale, pulseScale);

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
  }, [viewMode, isAutoRotate]);

  return (
    <div className={`glass-panel rounded-2xl p-5 border border-brand-border/80 relative overflow-hidden ${className}`}>
      {/* Visualizer Header with 3-Mode Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-brand-blue to-brand-cyan flex items-center justify-center text-white font-bold">
            {viewMode === 'BAR_CHART' ? <BarChart3 className="w-4 h-4" /> : <Network className="w-4 h-4" />}
          </div>
          <div>
            <h2 className="text-base font-semibold text-white flex items-center space-x-2">
              <span>
                {viewMode === 'BAR_CHART' && 'Financial Recovery Comparison Charts'}
                {viewMode === '2D_FLOW' && 'Autonomous Decision Routing Engine'}
                {viewMode === '3D_TOPOLOGY' && '3D Payment Rail Topology Mesh'}
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
                LIVE
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              {viewMode === 'BAR_CHART' && '2D Visual Bar Charts: Naive Retries (6.4%) vs. Autonomous AI Engine (61.8%)'}
              {viewMode === '2D_FLOW' && 'Interactive 2D Decision Flow Graph: Ingestion → Diagnosis → Guardrails → Multi-Rail Execution'}
              {viewMode === '3D_TOPOLOGY' && 'Three.js 3D Financial Network Topology: Orbiting Switches & Active Spline Streams'}
            </p>
          </div>
        </div>

        {/* 3-Way Mode Toggle Buttons */}
        <div className="flex items-center space-x-1.5 bg-slate-900/90 p-1 rounded-xl border border-slate-700/80 self-start sm:self-auto">
          <button
            onClick={() => setViewMode('BAR_CHART')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              viewMode === 'BAR_CHART'
                ? 'bg-gradient-to-r from-brand-blue to-brand-cyan text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>2D Bar Charts</span>
          </button>
          <button
            onClick={() => setViewMode('2D_FLOW')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              viewMode === '2D_FLOW'
                ? 'bg-gradient-to-r from-brand-blue to-brand-cyan text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>2D Flow Graph</span>
          </button>
          <button
            onClick={() => setViewMode('3D_TOPOLOGY')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition ${
              viewMode === '3D_TOPOLOGY'
                ? 'bg-gradient-to-r from-brand-blue to-brand-cyan text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Network className="w-3.5 h-3.5" />
            <span>3D Topology</span>
          </button>
        </div>
      </div>

      {/* VIEW MODE 1: VISUAL 2D FINANCIAL RECOVERY BAR CHARTS (DEFAULT) */}
      {viewMode === 'BAR_CHART' && (
        <div className="animate-in fade-in duration-300">
          <RecoveryComparisonChart
            baselineRecovered={kpis?.baseline_recovered || 16700}
            aiRecovered={kpis?.total_recovered || 162300}
            totalAtRisk={kpis?.total_at_risk || 262800}
            baselinePercentage={kpis?.baseline_percentage || 6.4}
            aiPercentage={kpis?.recovery_percentage || 61.8}
            netUplift={kpis?.net_uplift || 145600}
          />
        </div>
      )}

      {/* VIEW MODE 2: INTERACTIVE 2D DECISION FLOW GRAPH */}
      {viewMode === '2D_FLOW' && (
        <div className="space-y-4 animate-in fade-in duration-300">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 relative">
            <div
              onClick={() => setActive2DStage('DIAGNOSE')}
              className={`p-4 rounded-xl border cursor-pointer transition ${
                active2DStage === 'DIAGNOSE'
                  ? 'bg-blue-950/40 border-brand-blue shadow-lg shadow-brand-blue/10 node-active'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-blue-400 font-mono">
                  STAGE 01
                </span>
                <span className="w-2 h-2 rounded-full bg-blue-400" />
              </div>
              <div className="font-bold text-white text-sm mb-1">diagnose_node</div>
              <p className="text-xs text-slate-400 mb-3">
                Inspects error code & classifies into 4 deterministic operational cohorts.
              </p>
              <div className="space-y-1 text-[11px] font-mono text-slate-300">
                <div className="flex justify-between">
                  <span>Transient:</span> <span className="text-emerald-400">25 (89.8% rec)</span>
                </div>
                <div className="flex justify-between">
                  <span>Actionable:</span> <span className="text-purple-400">20 (59.0% rec)</span>
                </div>
                <div className="flex justify-between">
                  <span>Terminal:</span> <span className="text-rose-400">15 (0% dropped)</span>
                </div>
              </div>
            </div>

            <div
              onClick={() => setActive2DStage('GUARD')}
              className={`p-4 rounded-xl border cursor-pointer transition ${
                active2DStage === 'GUARD'
                  ? 'bg-amber-950/40 border-amber-500 shadow-lg shadow-amber-500/10 node-active'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-amber-400 font-mono">
                  STAGE 02
                </span>
                <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
              </div>
              <div className="font-bold text-white text-sm mb-1">policy_guard_node</div>
              <p className="text-xs text-slate-400 mb-3">
                Evaluates 3 non-negotiable deterministic safety gates before any side effect.
              </p>
              <div className="space-y-1 text-[11px] font-mono text-slate-300">
                <div className="flex justify-between">
                  <span>Max Retries:</span> <span className="text-amber-300">Limit &lt; 2 attempts</span>
                </div>
                <div className="flex justify-between">
                  <span>TRAI Window:</span> <span className="text-emerald-300">08:00–20:00 IST</span>
                </div>
                <div className="flex justify-between">
                  <span>Double-Debit:</span> <span className="text-emerald-400">100% Guarded</span>
                </div>
              </div>
            </div>

            <div
              onClick={() => setActive2DStage('EXECUTION')}
              className={`p-4 rounded-xl border cursor-pointer transition ${
                active2DStage === 'EXECUTION'
                  ? 'bg-emerald-950/40 border-emerald-500 shadow-lg shadow-emerald-500/10 node-active'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 font-mono">
                  STAGE 03
                </span>
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
              </div>
              <div className="font-bold text-white text-sm mb-1">execution_node</div>
              <p className="text-xs text-slate-400 mb-3">
                Sequences optimal recovery rail based on classified root-cause failure.
              </p>
              <div className="space-y-1 text-[11px] font-mono text-slate-300">
                <div className="flex justify-between">
                  <span>Bank Outage:</span> <span className="text-blue-300">Silent (+12h)</span>
                </div>
                <div className="flex justify-between">
                  <span>Card Depleted:</span> <span className="text-purple-300">UPI Intent Link</span>
                </div>
                <div className="flex justify-between">
                  <span>Limit / Dead:</span> <span className="text-rose-400">Graceful Abort</span>
                </div>
              </div>
            </div>

            <div
              onClick={() => setActive2DStage('AUDIT')}
              className={`p-4 rounded-xl border cursor-pointer transition ${
                active2DStage === 'AUDIT'
                  ? 'bg-purple-950/40 border-purple-500 shadow-lg shadow-purple-500/10 node-active'
                  : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] uppercase font-bold tracking-wider text-purple-400 font-mono">
                  STAGE 04
                </span>
                <Terminal className="w-3.5 h-3.5 text-purple-400" />
              </div>
              <div className="font-bold text-white text-sm mb-1">audit_logger</div>
              <p className="text-xs text-slate-400 mb-3">
                Thread-safe immutable JSONL audit recording every transition microsecond-by-microsecond.
              </p>
              <div className="space-y-1 text-[11px] font-mono text-slate-300">
                <div className="flex justify-between">
                  <span>Format:</span> <span className="text-slate-200">recovery_audit_trail</span>
                </div>
                <div className="flex justify-between">
                  <span>Precision:</span> <span className="text-brand-cyan">ISO 8601 Microsec</span>
                </div>
                <div className="flex justify-between">
                  <span>Invariants:</span> <span className="text-emerald-400">Conserved 100%</span>
                </div>
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-brand-blue/20 text-brand-cyan flex items-center justify-center font-bold">
                {active2DStage === 'DIAGNOSE' && <Layers className="w-4 h-4" />}
                {active2DStage === 'GUARD' && <ShieldCheck className="w-4 h-4" />}
                {active2DStage === 'EXECUTION' && <Smartphone className="w-4 h-4" />}
                {active2DStage === 'AUDIT' && <Terminal className="w-4 h-4" />}
              </div>
              <div>
                <span className="font-bold text-white block">
                  {active2DStage === 'DIAGNOSE' && 'Failure Diagnostic Engine (Root-Cause Taxonomy)'}
                  {active2DStage === 'GUARD' && 'Deterministic Compliance & Idempotency Guardrails'}
                  {active2DStage === 'EXECUTION' && 'Dynamic Execution Sequencer & Multi-Rail Fallback'}
                  {active2DStage === 'AUDIT' && 'Thread-Safe Microsecond Audit & Financial Invariants'}
                </span>
                <span className="text-slate-400 text-[11px]">
                  {active2DStage === 'DIAGNOSE' && 'Differentiates transient bank infrastructure downtimes from customer-actionable card declines.'}
                  {active2DStage === 'GUARD' && 'Enforces MAX_RETRY_LIMIT=2, TRAI 08:00–20:00 IST active window, and atomic idempotency locks.'}
                  {active2DStage === 'EXECUTION' && 'Routes to silent background retry (+12h off-peak) or dynamic 1-tap UPI Intent link.'}
                  {active2DStage === 'AUDIT' && 'Preserves mathematical balance (Total at Risk == Recovered + Guarded) with 0.00 currency drift.'}
                </span>
              </div>
            </div>
            <div className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg self-start sm:self-auto flex items-center space-x-1.5">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Closed-Loop Enforced</span>
            </div>
          </div>
        </div>
      )}

      {/* VIEW MODE 3: FIXED 3D THREE.JS TOPOLOGY MESH */}
      {viewMode === '3D_TOPOLOGY' && (
        <div className="relative w-full h-[440px] rounded-xl overflow-hidden bg-slate-950/60 border border-slate-800 animate-in fade-in duration-300">
          <div ref={containerRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

          <div className="absolute top-3 left-3 z-10 flex items-center space-x-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700/80 text-xs">
            <div className="w-2 h-2 rounded-full bg-brand-cyan animate-pulse" />
            <span className="font-semibold text-white">Three.js 3D Topology</span>
            <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">(Fixed Distance 46)</span>
          </div>

          <div className="absolute top-3 right-3 z-10 flex items-center space-x-2">
            <button
              onClick={() => setIsAutoRotate(!isAutoRotate)}
              className="px-2.5 py-1 rounded-lg bg-slate-800/90 hover:bg-slate-700 text-[11px] text-slate-300 border border-slate-700 transition"
            >
              {isAutoRotate ? 'Pause Rotation' : 'Auto Rotate'}
            </button>
          </div>

          <div className="absolute bottom-3 left-3 right-3 z-10 flex flex-wrap items-center justify-between gap-2 bg-slate-900/90 backdrop-blur-md px-4 py-2 rounded-xl border border-slate-800 text-[11px]">
            <div className="flex items-center space-x-3">
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-slate-300">UPI Switch</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-brand-blue" />
                <span className="text-slate-300">HDFC/SBI CBS</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-amber-400" />
                <span className="text-slate-300">e-NACH</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="w-2 h-2 rounded-full bg-purple-400" />
                <span className="text-slate-300">Dynamic Links</span>
              </span>
            </div>
            <div className="text-slate-400 text-[10px] italic">
              Smooth Drag to Orbit | Scroll to Zoom (clamped 30–70)
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

