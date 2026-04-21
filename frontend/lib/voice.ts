// Voice recording and playback utilities for Jarvis

export interface VoiceCallbacks {
  onTranscription?: (text: string) => void;
  onResponseText?: (text: string) => void;
  onError?: (error: Error) => void;
}

export function createVoiceRecorder(
  jarvisVoiceUrl: string = "/api/jarvis/voice",
  callbacks: VoiceCallbacks = {}
) {
  let mediaRecorder: MediaRecorder | null = null;
  let stream: MediaStream | null = null;
  let isRecording = false;

  async function start() {
    if (isRecording) {
      throw new Error("Already recording");
    }

    // Check if browser supports getUserMedia
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const err = new Error(
        "Microphone access not supported. Please use a modern browser (Chrome, Firefox, Edge, Safari)."
      );
      callbacks.onError?.(err);
      throw err;
    }

    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunks.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        if (stream) {
          stream.getTracks().forEach((track) => track.stop());
        }

        const blob = new Blob(chunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", blob, "input.webm");

        try {
          const res = await fetch(jarvisVoiceUrl, {
            method: "POST",
            body: formData,
          });

          const inputText = res.headers.get("X-Input-Text") || "";
          const responseText = res.headers.get("X-Response-Text") || "";

          if (inputText && callbacks.onTranscription) {
            callbacks.onTranscription(inputText);
          }

          if (responseText && callbacks.onResponseText) {
            callbacks.onResponseText(responseText);
          }

          const audioBlob = await res.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.play();

          audio.onended = () => {
            URL.revokeObjectURL(audioUrl);
          };
        } catch (error) {
          const err = error instanceof Error ? error : new Error("Voice API error");
          callbacks.onError?.(err);
        }
      };

      mediaRecorder.onerror = (event) => {
        callbacks.onError?.(new Error("MediaRecorder error"));
      };

      mediaRecorder.start();
      isRecording = true;
    } catch (error) {
      isRecording = false;
      
      // Provide helpful error messages for common permission issues
      let errorMessage = "Failed to start recording";
      if (error instanceof Error) {
        if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
          errorMessage = "Microphone permission denied. Please allow microphone access in your browser settings and try again.";
        } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
          errorMessage = "No microphone found. Please connect a microphone and try again.";
        } else if (error.name === "NotReadableError" || error.name === "TrackStartError") {
          errorMessage = "Microphone is already in use by another application. Please close other apps using the microphone.";
        } else {
          errorMessage = error.message || errorMessage;
        }
      }
      
      const err = new Error(errorMessage);
      callbacks.onError?.(err);
      throw err;
    }
  }

  function stop() {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      isRecording = false;
    }
  }

  function getIsRecording() {
    return isRecording;
  }

  return {
    start,
    stop,
    isRecording: getIsRecording,
  };
}

