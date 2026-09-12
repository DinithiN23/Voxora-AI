"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface UseVoiceOptions {
  onTranscriptComplete?: (finalText: string) => void;
  lang?: string;
  silenceTimeoutMs?: number;
}

export function useVoice({
  onTranscriptComplete,
  lang = "en-US",
  silenceTimeoutMs = 3000,
}: UseVoiceOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [interimTranscript, setInterimTranscript] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speakingId, setSpeakingId] = useState<string | null>(null);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef<any>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const latestSpokenRef = useRef("");
  const isSubmittingRef = useRef(false);
  const customCallbackRef = useRef<((text: string) => void) | undefined>(undefined);
  const onCompleteRef = useRef(onTranscriptComplete);
  onCompleteRef.current = onTranscriptComplete;

  useEffect(() => {
    if (typeof window !== "undefined") {
      const hasSpeech =
        "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
      setIsSupported(hasSpeech);

      // Preload available voices for natural speech synthesis
      if ("speechSynthesis" in window) {
        window.speechSynthesis.getVoices();
        window.speechSynthesis.onvoiceschanged = () => {
          window.speechSynthesis.getVoices();
        };
      }
    }
  }, []);

  // Clear silence detection timer
  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  // Cleanup microphone & Web Audio context
  const cleanupAudio = useCallback(() => {
    clearSilenceTimer();
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore track close error
        }
      });
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      try {
        audioContextRef.current.close().catch(() => {});
      } catch {
        // ignore audio context close
      }
      audioContextRef.current = null;
    }
    setAnalyser(null);
  }, [clearSilenceTimer]);

  // Stop Text-to-Speech playback
  const stopSpeaking = useCallback(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setSpeakingId(null);
  }, []);

  // Stop Listening immediately without auto-submitting
  const stopListening = useCallback(() => {
    clearSilenceTimer();
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {
        // ignore if already aborted
      }
      recognitionRef.current = null;
    }
    cleanupAudio();
    setIsListening(false);
    setInterimTranscript("");
  }, [cleanupAudio, clearSilenceTimer]);

  // Finalize speech and automatically dispatch the query
  const finalizeAndSubmit = useCallback(() => {
    clearSilenceTimer();
    if (isSubmittingRef.current) return;

    const finalText = latestSpokenRef.current.trim();
    if (!finalText) {
      stopListening();
      return;
    }

    isSubmittingRef.current = true;
    setTranscript(finalText);
    setInterimTranscript("");
    setIsListening(false);

    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }
    cleanupAudio();

    if (customCallbackRef.current) {
      customCallbackRef.current(finalText);
    } else if (onCompleteRef.current) {
      onCompleteRef.current(finalText);
    }
  }, [cleanupAudio, clearSilenceTimer, stopListening]);

  // Start Listening with automated end-of-speech detection
  const startListening = useCallback(
    (customCallback?: (text: string) => void) => {
      if (typeof window === "undefined") return;

      // Barge-in: immediately stop any assistant speaking
      stopSpeaking();
      clearSilenceTimer();
      setError(null);
      setTranscript("");
      setInterimTranscript("");
      latestSpokenRef.current = "";
      isSubmittingRef.current = false;
      customCallbackRef.current = customCallback;

      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        setError("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
        setIsListening(false);
        return;
      }

      // 1. Initialize Web Speech Recognition
      try {
        // Abort previous instance if any
        if (recognitionRef.current) {
          try {
            recognitionRef.current.abort();
          } catch {
            // ignore
          }
        }

        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        recognition.lang = lang;
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;

        recognition.onstart = () => {
          setIsListening(true);
          setError(null);
        };

        recognition.onresult = (event: any) => {
          let combined = "";

          for (let i = 0; i < event.results.length; ++i) {
            combined += event.results[i][0].transcript;
          }

          const cleaned = combined.trim();
          if (cleaned) {
            latestSpokenRef.current = cleaned;
            setInterimTranscript(cleaned);

            // Reset silence timer: automatically submit after user stops speaking for silenceTimeoutMs
            clearSilenceTimer();
            silenceTimerRef.current = setTimeout(() => {
              finalizeAndSubmit();
            }, silenceTimeoutMs);
          }
        };

        recognition.onerror = (event: any) => {
          console.warn("Speech recognition status:", event.error);
          if (event.error === "not-allowed") {
            setError("Microphone permission was denied. Please allow microphone access in your browser.");
            setIsListening(false);
            cleanupAudio();
          } else if (event.error === "audio-capture") {
            setError("No microphone was detected or it is in use by another app.");
            setIsListening(false);
            cleanupAudio();
          } else if (event.error === "no-speech") {
            // If silence occurred but we already heard words, finalize now
            if (latestSpokenRef.current.trim()) {
              finalizeAndSubmit();
            }
            // If nothing was spoken, keep listening or wait quietly (never inject fake questions)
          } else if (event.error !== "aborted") {
            setError(`Voice error: ${event.error}`);
          }
        };

        recognition.onend = () => {
          // If ended and user has spoken words, automatically send
          if (latestSpokenRef.current.trim() && !isSubmittingRef.current) {
            finalizeAndSubmit();
          } else {
            setIsListening(false);
            cleanupAudio();
          }
        };

        recognition.start();
        setIsListening(true);
      } catch (err: any) {
        console.warn("Failed to start SpeechRecognition:", err);
        setError("Could not start voice recognition. Please try clicking the microphone again.");
        setIsListening(false);
        return;
      }

      // 2. Setup AudioContext and AnalyserNode in background for live waveform visualizer
      (async () => {
        try {
          if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            const stream = await navigator.mediaDevices.getUserMedia({
              audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
              },
            });
            mediaStreamRef.current = stream;

            const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
            if (AudioCtx) {
              const audioCtx = new AudioCtx();
              audioContextRef.current = audioCtx;
              if (audioCtx.state === "suspended") {
                await audioCtx.resume();
              }
              const source = audioCtx.createMediaStreamSource(stream);
              const node = audioCtx.createAnalyser();
              node.smoothingTimeConstant = 0.8;
              source.connect(node);
              setAnalyser(node);
            }
          }
        } catch {
          // If getUserMedia fails or is restricted, SpeechRecognition still operates normally
        }
      })();
    },
    [lang, silenceTimeoutMs, stopSpeaking, clearSilenceTimer, cleanupAudio, finalizeAndSubmit]
  );

  // Read assistant response aloud with natural executive cadence
  const speak = useCallback(
    (text: string, id: string = "default", onEnd?: () => void) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

      // If already speaking this message, toggle off
      if (isSpeaking && speakingId === id) {
        stopSpeaking();
        return;
      }

      stopSpeaking();

      // Clean markdown, symbols, code blocks, and tables for natural speech flow
      const cleaned = text
        .replace(/```[\s\S]*?```/g, "")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/[#*_~|>-]/g, " ")
        .replace(/\n+/g, ". ")
        .replace(/\s+/g, " ")
        .trim();

      if (!cleaned) return;

      // Limit utterance length to avoid browser synthesis cutoffs
      const readableSlice = cleaned.slice(0, 500);

      const utterance = new SpeechSynthesisUtterance(readableSlice);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) =>
          v.lang.startsWith("en") &&
          (v.name.includes("Natural") ||
            v.name.includes("Samantha") ||
            v.name.includes("Google") ||
            v.name.includes("Daniel") ||
            v.name.includes("Karen") ||
            v.name.includes("Alex"))
      ) || voices.find((v) => v.lang.startsWith("en"));

      if (preferred) {
        utterance.voice = preferred;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
        setSpeakingId(id);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
        setSpeakingId(null);
        if (onEnd) onEnd();
      };

      utterance.onerror = () => {
        setIsSpeaking(false);
        setSpeakingId(null);
      };

      window.speechSynthesis.speak(utterance);
    },
    [isSpeaking, speakingId, stopSpeaking]
  );

  // Barge-In: immediately interrupt assistant voice and open microphone for user
  const bargeIn = useCallback(
    (callback?: (text: string) => void) => {
      stopSpeaking();
      startListening(callback);
    },
    [stopSpeaking, startListening]
  );

  // Unmount cleanup
  useEffect(() => {
    return () => {
      stopSpeaking();
      stopListening();
    };
  }, [stopSpeaking, stopListening]);

  return {
    isListening,
    transcript,
    interimTranscript,
    isSpeaking,
    speakingId,
    analyser,
    error,
    isSupported,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    bargeIn,
  };
}
