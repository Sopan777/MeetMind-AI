import { MicVAD } from '@ricky0123/vad-web';
import { encodeWAV } from './wavEncoder';

export interface VADPipelineOptions {
  onUtterance: (wavBuffer: ArrayBuffer, durationMs: number, speechStartMs: number, speechEndMs: number) => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  onMisfire?: () => void;
}

export class VADPipeline {
  private vad: MicVAD | null = null;
  private options: VADPipelineOptions;
  private currentSpeechStartMs: number = 0;

  constructor(options: VADPipelineOptions) {
    this.options = options;
  }

  async start(stream: MediaStream): Promise<void> {
    try {
      this.vad = await MicVAD.new({
        getStream: async () => stream,
        resumeStream: async () => stream,
        pauseStream: async () => {},

        baseAssetPath: '/',
        onnxWASMBasePath: '/',

        ortConfig: (ort) => {
          ort.env.wasm.numThreads = 1;
        },

        positiveSpeechThreshold: 0.8,
        negativeSpeechThreshold: 0.3,
        submitUserSpeechOnPause: true,

        onSpeechStart: () => {
          this.currentSpeechStartMs = Date.now();
          this.options.onSpeechStart?.();
        },
        onSpeechEnd: (audio: Float32Array) => {
          const speechEndMs = Date.now();
          this.options.onSpeechEnd?.();

          const sampleRate = 16000;
          const wavBuffer = encodeWAV(audio, sampleRate);
          const durationMs = (audio.length / sampleRate) * 1000;

          this.options.onUtterance(wavBuffer, durationMs, this.currentSpeechStartMs, speechEndMs);
          this.currentSpeechStartMs = 0;
        },
        onVADMisfire: () => {
          this.currentSpeechStartMs = 0;
          this.options.onMisfire?.();
        }
      });
      this.vad.start();
    } catch (err) {
      console.error('Failed to start VAD pipeline', err);
      throw err;
    }
  }

  pause(): void {
    this.vad?.pause();
  }

  resume(): void {
    this.vad?.start();
  }

  destroy(): void {
    if (this.vad) {
      this.vad.destroy();
      this.vad = null;
    }
  }
}
