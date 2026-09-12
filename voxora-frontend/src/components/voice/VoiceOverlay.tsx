"use client";

import AudioWaveform from "./AudioWaveform";
import styles from "./VoiceOverlay.module.css";

interface VoiceOverlayProps {
  isListening: boolean;
  isSpeaking: boolean;
  transcript: string;
  interimTranscript: string;
  analyser: AnalyserNode | null;
  onCancel: () => void;
  onBargeIn: () => void;
}

export default function VoiceOverlay({
  isListening,
  isSpeaking,
  transcript,
  interimTranscript,
  analyser,
  onCancel,
  onBargeIn,
}: VoiceOverlayProps) {
  if (!isListening && !isSpeaking) return null;

  const currentDisplay = interimTranscript || transcript;

  return (
    <div className={styles.overlayContainer}>
      <div className={styles.voiceCard}>
        <div className={styles.headerRow}>
          {isListening ? (
            <span className={styles.modeBadge}>
              <span className={styles.pulseMic} />
              Live Voice Recognition
            </span>
          ) : (
            <span className={styles.bargeInBadge}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5" />
                <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
              </svg>
              <span>Voxora Assistant Speaking</span>
            </span>
          )}

          {isSpeaking && (
            <button
              type="button"
              className={styles.btnBargeIn}
              onClick={onBargeIn}
              title="Interrupt and speak now"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              </svg>
              <span>Barge-in / Interrupt</span>
            </button>
          )}
        </div>

        {/* Real-time Audio Waveform Canvas */}
        <AudioWaveform
          isRecording={isListening}
          isPlaying={isSpeaking}
          analyserNode={analyser}
          height={48}
          barCount={40}
          showStatus={false}
        />

        {/* Live transcript or speaking prompt */}
        <div className={styles.transcriptBox}>
          {isListening ? (
            currentDisplay ? (
              <span className={styles.interimText}>"{currentDisplay}"</span>
            ) : (
              <span className={styles.placeholderText}>
                Listening to your voice... Speak naturally.
              </span>
            )
          ) : (
            <span className={styles.placeholderText}>
              Reading answer aloud. Tap "Barge-in" to interrupt and speak anytime.
            </span>
          )}
        </div>

        {/* Action controls & Auto-send hint */}
        {isListening && (
          <div className={styles.actionsRow}>
            <div className={styles.autoSendHint}>
              <span className={styles.autoSendDot} />
              <span>
                {currentDisplay.trim()
                  ? "Speaking detected • Pausing will automatically send"
                  : "Listening... System sends automatically when you stop speaking"}
              </span>
            </div>
            <button
              type="button"
              className={styles.btnCancel}
              onClick={onCancel}
              title="Cancel voice input"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
