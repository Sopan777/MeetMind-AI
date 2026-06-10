"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { MeetingWebSocketClient } from "../lib/websocketClient";

interface TranscriptSegment {
  timestamp: string;
  speaker: string;
  text: string;
}

interface ActionItem {
  owner: string;
  task: string;
  deadline: string;
}

interface Decision {
  decision: string;
  timestamp: string;
}

interface Risk {
  description: string;
  timestamp: string;
}

interface MeetingInsights {
  action_items: ActionItem[];
  decisions: Decision[];
  risks: Risk[];
  summary: string;
}

type MeetingStatus = "ready" | "connecting" | "connected" | "recording" | "processing" | "reconnecting" | "disconnected";

interface UseMeetingAnalysisReturn {
  status: MeetingStatus;
  transcript: TranscriptSegment[];
  insights: MeetingInsights;
  isConnected: boolean;
  droppedFrames: number;
  connect: (meetingId?: string) => void;
  disconnect: () => void;
  sendUtterance: (wavBuffer: ArrayBuffer, speechStartMs: number, speechEndMs: number) => void;
  requestAnalysis: () => void;
}

const EMPTY_INSIGHTS: MeetingInsights = {
  action_items: [],
  decisions: [],
  risks: [],
  summary: "",
};

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8001/ws/analyze";

export function useMeetingAnalysis(): UseMeetingAnalysisReturn {
  const [status, setStatus] = useState<MeetingStatus>("ready");
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  const [insights, setInsights] = useState<MeetingInsights>(EMPTY_INSIGHTS);
  const [droppedFrames, setDroppedFrames] = useState(0);

  const clientRef = useRef<MeetingWebSocketClient | null>(null);

  const cleanup = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
    }
    setStatus("ready");
  }, []);

  const connect = useCallback((meetingId?: string) => {
    cleanup();

    const id = meetingId || crypto.randomUUID();

    const client = new MeetingWebSocketClient({
      url: WS_URL,
      meetingId: id,
      onTranscript: (data) => {
        setTranscript((prev) => [...prev, data]);
      },
      onInsights: (data) => {
        setInsights(data);
      },
      onStatus: (newStatus) => {
        setStatus(newStatus as MeetingStatus);
      },
      onDroppedFrame: () => {
        setDroppedFrames((n) => n + 1);
      },
      onError: (err) => {
        console.error("Analysis Error:", err);
      },
    });

    clientRef.current = client;
    client.connect();
  }, [cleanup]);

  const disconnect = useCallback(() => {
    cleanup();
    setTranscript([]);
    setInsights(EMPTY_INSIGHTS);
    setDroppedFrames(0);
  }, [cleanup]);

  const sendUtterance = useCallback((wavBuffer: ArrayBuffer, speechStartMs: number, speechEndMs: number) => {
    if (clientRef.current) {
      clientRef.current.sendUtterance(wavBuffer, speechStartMs, speechEndMs);
    }
  }, []);

  const requestAnalysis = useCallback(() => {
    if (clientRef.current) {
      clientRef.current.requestAnalysis();
    }
  }, []);

  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  return {
    status,
    transcript,
    insights,
    droppedFrames,
    isConnected: status === "connected" || status === "recording" || status === "processing",
    connect,
    disconnect,
    sendUtterance,
    requestAnalysis,
  };
}
