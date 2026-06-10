"use client";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface MeetingTopBarProps {
  status: "ready" | "recording" | "processing" | "connected" | "connecting" | "reconnecting" | "disconnected";
  isSharing: boolean;
  isAnalyzing: boolean;
  isSpeaking?: boolean;
  onShareScreen: () => void;
  onStopSharing: () => void;
  onStartAnalysis: () => void;
  onStopAnalysis: () => void;
  onAnalyzeNow?: () => void;
}

const statusConfig: Record<
  MeetingTopBarProps["status"],
  { color: string; label: string }
> = {
  ready: { color: "bg-gray-400", label: "Ready" },
  connecting: { color: "bg-blue-400", label: "Connecting..." },
  connected: { color: "bg-blue-500", label: "Connected" },
  recording: { color: "bg-green-500", label: "Listening" },
  processing: { color: "bg-yellow-500", label: "Processing" },
  reconnecting: { color: "bg-orange-500", label: "Reconnecting..." },
  disconnected: { color: "bg-red-500", label: "Disconnected" },
};

export function MeetingTopBar({
  status,
  isSharing,
  isAnalyzing,
  isSpeaking,
  onShareScreen,
  onStopSharing,
  onStartAnalysis,
  onStopAnalysis,
  onAnalyzeNow,
}: MeetingTopBarProps) {
  const { color, label } = statusConfig[status] || statusConfig.ready;

  return (
    <div className="flex items-center justify-between bg-card border-b border-border px-6 py-3">
      <div className="flex items-center gap-4">
        <span className="text-base font-semibold tracking-tight text-foreground">
          MeetingMind AI
        </span>
        <Badge variant="outline" className="gap-1.5 flex items-center">
          <span
            className={`inline-block h-2 w-2 rounded-full ${color}`}
            aria-hidden="true"
          />
          {label}
          
          {/* Active Speaking Indicator */}
          {isAnalyzing && isSpeaking && (
            <span className="ml-2 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-2 w-2 rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
            </span>
          )}
        </Badge>
      </div>

      <div className="flex items-center gap-2">
        {isSharing ? (
          <Button variant="destructive" size="sm" onClick={onStopSharing}>
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
              className="mr-2"
            >
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
              <line x1="2" y1="3" x2="22" y2="17" />
            </svg>
            Stop Sharing
          </Button>
        ) : (
          <Button variant="outline" size="sm" onClick={onShareScreen}>
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
              className="mr-2"
            >
              <rect x="2" y="3" width="20" height="14" rx="2" />
              <line x1="8" y1="21" x2="16" y2="21" />
              <line x1="12" y1="17" x2="12" y2="21" />
            </svg>
            Share Screen
          </Button>
        )}

        {isAnalyzing ? (
          <>
            {onAnalyzeNow && (
              <Button variant="outline" size="sm" onClick={onAnalyzeNow}>
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
                  className="mr-2"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                Analyze Now
              </Button>
            )}
            <Button variant="destructive" size="sm" onClick={onStopAnalysis}>
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
                className="mr-2"
              >
                <rect x="6" y="6" width="12" height="12" rx="2" />
              </svg>
              Stop Analysis
            </Button>
          </>
        ) : (
          <Button
            variant="default"
            size="sm"
            onClick={onStartAnalysis}
            disabled={!isSharing}
          >
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
              className="mr-2"
            >
              <polygon points="6 3 20 12 6 21 6 3" />
            </svg>
            Start Analysis
          </Button>
        )}
      </div>
    </div>
  );
}
