"use client";

import { useEffect, useRef } from "react";
import styles from "./AudioWaveform.module.css";

interface AudioWaveformProps {
  isRecording?: boolean;
  isPlaying?: boolean;
  analyserNode?: AnalyserNode | null;
  width?: number;
  height?: number;
  barCount?: number;
  showStatus?: boolean;
}

export default function AudioWaveform({
  isRecording = false,
  isPlaying = false,
  analyserNode = null,
  width = 360,
  height = 56,
  barCount = 36,
  showStatus = true,
}: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationFrameRef = useRef<number | null>(null);
  const smoothedHeightsRef = useRef<number[]>(new Array(barCount).fill(4));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Retina display scaling
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);

    let dataArray: Uint8Array | null = null;
    if (analyserNode) {
      analyserNode.fftSize = 128;
      const bufferLength = analyserNode.frequencyBinCount;
      dataArray = new Uint8Array(bufferLength);
    }

    let phase = 0;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      const barSpacing = width / barCount;
      const barWidth = Math.max(3, barSpacing * 0.55);
      const centerY = height / 2;
      const smoothed = smoothedHeightsRef.current;

      if (isRecording && analyserNode && dataArray) {
        analyserNode.getByteFrequencyData(dataArray as any);

        for (let i = 0; i < barCount; i++) {
          const binIndex = Math.floor((i / barCount) * (dataArray.length * 0.75));
          const val = dataArray[binIndex] || 0;
          const targetHeight = Math.max(4, (val / 255) * (height - 8));
          smoothed[i] += (targetHeight - smoothed[i]) * 0.3; // smooth easing
        }
      } else if (isRecording) {
        // Simulated voice fluctuations if analyser node is absent
        phase += 0.08;
        for (let i = 0; i < barCount; i++) {
          const wave1 = Math.sin(phase + i * 0.35);
          const wave2 = Math.cos(phase * 1.5 + i * 0.2);
          const raw = (Math.abs(wave1 * 0.6 + wave2 * 0.4)) * (height - 12);
          const targetHeight = Math.max(6, raw);
          smoothed[i] += (targetHeight - smoothed[i]) * 0.25;
        }
      } else if (isPlaying) {
        // Assistant speech playback dynamic harmonic rhythm
        phase += 0.06;
        for (let i = 0; i < barCount; i++) {
          const centerDist = Math.abs(i - barCount / 2) / (barCount / 2);
          const bellCurve = Math.cos(centerDist * Math.PI * 0.45);
          const harmonic = Math.sin(phase * 2 + i * 0.3) * 0.5 + Math.cos(phase * 1.2 + i * 0.15) * 0.5;
          const targetHeight = Math.max(5, (Math.abs(harmonic) * (height - 10)) * bellCurve);
          smoothed[i] += (targetHeight - smoothed[i]) * 0.2;
        }
      } else {
        // Idle gentle breathing state
        phase += 0.02;
        for (let i = 0; i < barCount; i++) {
          const wave = Math.sin(phase + i * 0.18);
          const targetHeight = 4 + Math.abs(wave) * 6;
          smoothed[i] += (targetHeight - smoothed[i]) * 0.1;
        }
      }

      // Draw mirrored rounded bars centered vertically
      for (let i = 0; i < barCount; i++) {
        const h = smoothed[i];
        const x = i * barSpacing + (barSpacing - barWidth) / 2;
        const y = centerY - h / 2;

        // Gradient color for each bar
        const gradient = ctx.createLinearGradient(x, y, x, y + h);
        if (isRecording) {
          gradient.addColorStop(0, "#c084fc"); // neon purple top
          gradient.addColorStop(0.5, "#8b5cf6"); // brand purple
          gradient.addColorStop(1, "#06b6d4"); // cyan bottom
        } else if (isPlaying) {
          gradient.addColorStop(0, "#38bdf8"); // bright sky blue
          gradient.addColorStop(0.5, "#06b6d4"); // teal cyan
          gradient.addColorStop(1, "#8b5cf6"); // purple
        } else {
          gradient.addColorStop(0, "rgba(139, 92, 246, 0.3)");
          gradient.addColorStop(1, "rgba(6, 182, 212, 0.2)");
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        const r = barWidth / 2;
        ctx.roundRect(x, y, barWidth, h, r);
        ctx.fill();

        // Glowing cap dot on high peaks during recording or playing
        if ((isRecording || isPlaying) && h > height * 0.55) {
          ctx.beginPath();
          ctx.arc(x + r, y - 2, 1.5, 0, Math.PI * 2);
          ctx.fillStyle = "#ffffff";
          ctx.shadowColor = "#06b6d4";
          ctx.shadowBlur = 6;
          ctx.fill();
          ctx.shadowBlur = 0; // reset
        }
      }

      animationFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isRecording, isPlaying, analyserNode, width, height, barCount]);

  return (
    <div className={styles.waveformContainer}>
      <canvas
        ref={canvasRef}
        className={`${styles.canvas} ${isRecording ? styles.recording : ""} ${
          isPlaying ? styles.playing : ""
        }`}
      />
      {showStatus && (
        <div className={styles.statusPill}>
          <span
            className={`${styles.statusDot} ${
              isRecording ? styles.recording : isPlaying ? styles.playing : ""
            }`}
          />
          <span>
            {isRecording
              ? "Listening to voice input..."
              : isPlaying
              ? "Voxora AI speaking..."
              : "Voice ready"}
          </span>
        </div>
      )}
    </div>
  );
}
