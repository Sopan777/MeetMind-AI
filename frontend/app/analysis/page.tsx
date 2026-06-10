"use client";

import { useCallback, useState } from "react";
import { MeetingTopBar } from "@/components/MeetingTopBar";
import { SharedScreenPanel } from "@/components/SharedScreenPanel";
import { TranscriptPanel } from "@/components/TranscriptPanel";
import { InsightsPanels } from "@/components/InsightsPanels";
import { LiveSummaryPanel } from "@/components/LiveSummaryPanel";
import { useMeetingAnalysis } from "@/hooks/useMeetingAnalysis";
import { useVAD } from "@/hooks/useVAD";
import { requestScreenShare } from "@/lib/audioCapture"; // Only used for getting the stream now

export default function AnalysisPage() {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isSharing, setIsSharing] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [audioWarning, setAudioWarning] = useState<string | null>(null);

  const {
    status,
    transcript,
    insights,
    droppedFrames,
    connect,
    disconnect,
    sendUtterance,
    requestAnalysis,
  } = useMeetingAnalysis();

  const {
    start: startVAD,
    stop: stopVAD,
    isSpeaking,
    error: vadError
  } = useVAD({
    onUtterance: (wavBuffer, durationMs, speechStartMs, speechEndMs) => {
      sendUtterance(wavBuffer, speechStartMs, speechEndMs);
    }
  });

  const handleShareScreen = useCallback(async () => {
    setAudioWarning(null);
    const mediaStream = await requestScreenShare();

    if (!mediaStream) return;

    setStream(mediaStream);
    setIsSharing(true);

    // Listen for the user stopping the share via browser UI
    mediaStream.getVideoTracks()[0]?.addEventListener("ended", () => {
      handleStopSharing();
    });

    // Check if audio is available
    const audioTracks = mediaStream.getAudioTracks();
    if (audioTracks.length === 0) {
      setAudioWarning(
        "No audio detected. When sharing, make sure to check \"Share tab audio\" or \"Share system audio\" in the browser dialog."
      );
    }
  }, []);

  const handleStopSharing = useCallback(() => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
    setStream(null);
    setIsSharing(false);
    setAudioWarning(null);

    // Also stop analysis if it was running
    if (isAnalyzing) {
      handleStopAnalysis();
    }
  }, [stream, isAnalyzing]);

  const handleStartAnalysis = useCallback(async () => {
    if (!stream) return;

    // Connect WebSocket
    connect();
    
    // Start VAD pipeline
    const success = await startVAD(stream);
    
    if (success) {
      setIsAnalyzing(true);
      setAudioWarning(null);
    } else {
      // vadError state will be set by the hook, but we can clear the UI state
      setIsAnalyzing(false);
      disconnect();
    }
  }, [stream, connect, disconnect, startVAD]);

  const handleStopAnalysis = useCallback(() => {
    stopVAD();
    disconnect();
    setIsAnalyzing(false);
  }, [stopVAD, disconnect]);

  // Combine websocket status with VAD status for the UI
  const displayStatus = isAnalyzing ? status : isSharing ? "connected" : "ready";

  return (
    <div className="flex flex-col h-screen">
      <MeetingTopBar
        status={displayStatus as any}
        isSharing={isSharing}
        isAnalyzing={isAnalyzing}
        isSpeaking={isSpeaking}
        onShareScreen={handleShareScreen}
        onStopSharing={handleStopSharing}
        onStartAnalysis={handleStartAnalysis}
        onStopAnalysis={handleStopAnalysis}
        onAnalyzeNow={requestAnalysis}
      />

      {/* Dropped frames warning */}
      {droppedFrames > 0 && (
        <div className="bg-orange-900/30 border-b border-orange-700/50 px-6 py-2.5 text-sm text-orange-200 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {droppedFrames} audio {droppedFrames === 1 ? "frame was" : "frames were"} dropped during reconnection. Transcript may have gaps.
        </div>
      )}

      {/* Audio warning */}
      {audioWarning && (
        <div className="bg-yellow-900/30 border-b border-yellow-700/50 px-6 py-2.5 text-sm text-yellow-200 flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          {audioWarning}
          <button
            onClick={() => setAudioWarning(null)}
            className="ml-auto text-yellow-400 hover:text-yellow-200"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Screen preview */}
        <SharedScreenPanel stream={stream} />

        {/* Transcript */}
        <TranscriptPanel segments={transcript} />

        {/* Insights */}
        <InsightsPanels
          actionItems={insights.action_items}
          decisions={insights.decisions}
          risks={insights.risks}
        />

        {/* Summary */}
        <LiveSummaryPanel summary={insights.summary} />
      </div>
    </div>
  );
}
