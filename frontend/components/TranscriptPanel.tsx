"use client";

import { useEffect, useRef } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TranscriptSegment {
  timestamp: string;
  speaker: string;
  confidence?: number;
  text: string;
}

interface TranscriptPanelProps {
  segments: TranscriptSegment[];
}

const SPEAKER_COLORS = [
  "text-blue-500",    // Speaker_0
  "text-emerald-500", // Speaker_1
  "text-amber-500",   // Speaker_2
  "text-pink-500",    // Speaker_3
  "text-purple-500",  // Speaker_4
  "text-orange-500",  // Speaker_5
];

function getSpeakerColorClass(label: string): string {
  if (label === "Unknown") return "text-slate-400";
  const match = label.match(/Speaker_(\d+)/);
  if (match) {
    const idx = parseInt(match[1], 10) % SPEAKER_COLORS.length;
    return SPEAKER_COLORS[idx];
  }
  return "text-slate-400";
}

export function TranscriptPanel({ segments }: TranscriptPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [segments]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
          Transcript
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="max-h-[400px] overflow-auto">
          {segments.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-sm text-muted-foreground">
              Waiting for transcript…
            </div>
          ) : (
            <div className="space-y-4 pr-3">
              {segments.map((segment, i) => {
                const colorClass = getSpeakerColorClass(segment.speaker);
                const isUncertain = segment.confidence !== undefined && segment.confidence < 0.75;
                const displayName = segment.speaker === "Unknown" ? "—" : (isUncertain ? `${segment.speaker}?` : segment.speaker);
                const tooltipText = isUncertain ? "Low confidence speaker match" : "";
                
                return (
                <div key={i} className="space-y-1">
                  <div className="flex items-baseline gap-2">
                    <span className="text-xs text-muted-foreground font-mono">
                      {segment.timestamp}
                    </span>
                    <span 
                      className={`text-sm font-semibold ${colorClass} ${isUncertain ? 'opacity-70' : ''}`}
                      title={tooltipText}
                    >
                      {displayName}
                    </span>
                  </div>
                  <p className="text-sm text-muted-foreground leading-relaxed pl-0">
                    {segment.text}
                  </p>
                </div>
                );
              })}
              <div ref={bottomRef} />
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}

export type { TranscriptSegment };
