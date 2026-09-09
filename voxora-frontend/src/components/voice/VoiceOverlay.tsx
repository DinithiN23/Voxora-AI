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
  onSend: () => void;
  onBargeIn: () => void;
}

export default function VoiceOverlay({
  isListening,
  isSpeaking,
  transcript,
  interimTranscript,
  analyser,
  onCancel,
  onSend,
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
              <span>🔊</span>
              Voxora Assistant Speaking
            </span>
          )}

          {isSpeaking && (
            <button
              type="button"
              className={styles.btnBargeIn}
              onClick={onBargeIn}
              title="Interrupt and speak now"
            >
              🎙️ Barge-in / Interrupt
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
                Listening... Say a question like "Show monthly revenue trends"
              </span>
            )
          ) : (
            <span className={styles.placeholderText}>
              Reading executive briefing aloud. Tap "Barge-in" to interrupt anytime.
            </span>
          )}
        </div>

        {/* Action controls */}
        {isListening && (
          <div className={styles.actionsRow}>
            <button
              type="button"
              className={styles.btnCancel}
              onClick={onCancel}
            >
              Cancel
            </button>
            <button
              type="button"
              className={styles.btnSend}
              onClick={onSend}
              disabled={!currentDisplay.trim()}
            >
              Send Query ➤
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
