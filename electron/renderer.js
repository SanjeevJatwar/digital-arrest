const state = {
  transcript: [],
  voice: {
    emotion: 'neutral',
    stress: 18,
    pace: 'steady',
    energy: 0.35
  },
  face: {
    emotion: 'neutral',
    gaze: 'center',
    blink_rate: 0.12
  },
  insight: 'Waiting for the first context window.',
  arrest: {
    score: 0,
    verdict: 'monitoring',
    confidence: 'low',
    signals: []
  },
  captureMode: 'synthetic'
};

function clampTranscript() {
  if (state.transcript.length > 30) {
    state.transcript = state.transcript.slice(-30);
  }
}

function el(id) {
  return document.getElementById(id);
}

function pct(value, max = 100) {
  return `${Math.max(0, Math.min(100, (value / max) * 100))}%`;
}

function renderTranscript() {
  const container = el('transcriptList');
  container.innerHTML = state.transcript
    .map((line) => `
      <div class="transcript-line ${line.source}">
        <span class="ts">${line.timestamp}</span>
        <span class="speaker">${line.speaker}</span>
        <span class="text">${line.text}</span>
      </div>
    `)
    .join('');
}

function renderEmotionPanel() {
  el('voiceEmotion').textContent = state.voice.emotion;
  el('voiceStress').textContent = `${state.voice.stress}`;
  el('voicePace').textContent = state.voice.pace;
  el('voiceEnergy').textContent = `${Math.round(state.voice.energy * 100)}%`;
  el('voiceBar').style.width = pct(state.voice.stress);

  el('faceEmotion').textContent = state.face.emotion;
  el('faceGaze').textContent = state.face.gaze;
  el('faceBlink').textContent = `${Math.round(state.face.blink_rate * 100)} bpm`;
  el('faceBar').style.width = pct(Math.round(state.face.blink_rate * 100), 30);
}

function renderInsightPanel() {
  el('insightText').textContent = state.insight;
}

function renderAlertPanel() {
  el('arrestScore').textContent = `${state.arrest.score}`;
  el('arrestVerdict').textContent = state.arrest.verdict;
  el('arrestConfidence').textContent = state.arrest.confidence;
  el('arrestSignals').textContent = state.arrest.signals.join(' · ') || 'No high-risk signals yet';
  el('arrestBadge').classList.toggle('active', state.arrest.score >= 65);
}

function renderAll() {
  clampTranscript();
  renderTranscript();
  renderEmotionPanel();
  renderInsightPanel();
  renderAlertPanel();
}

function addTranscriptLine(payload) {
  state.transcript.push({
    source: payload.source || 'mic',
    speaker: payload.speaker || 'SPEAKER',
    text: payload.text || '',
    timestamp: payload.timestamp || new Date().toLocaleTimeString()
  });
}

function updateStatus(payload) {
  const bridge = el('bridgeStatus');
  const backend = el('backendStatus');
  const pointer = el('pointerStatus');
  const capture = el('captureStatus');
  const media = el('mediaStatus');

  if (payload.type === 'window') {
    bridge.textContent = 'Overlay ready';
    backend.textContent = 'Waiting for backend';
    return;
  }

  if (payload.type === 'bridge') {
    bridge.textContent = payload.state === 'connected' ? 'Live bridge' : 'Bridge offline';
    bridge.className = `pill ${payload.state === 'connected' ? 'ok' : 'warn'}`;
    return;
  }

  if (payload.type === 'backend-log') {
    backend.textContent = payload.message;
    backend.className = 'pill ok';
    return;
  }

  if (payload.type === 'backend-error') {
    backend.textContent = payload.message || 'Backend error';
    backend.className = 'pill warn';
    return;
  }

  if (payload.type === 'backend-exit') {
    backend.textContent = `Exited with ${payload.code}`;
    backend.className = 'pill warn';
    return;
  }

  if (payload.type === 'overlay-pointer' && pointer) {
    pointer.textContent = payload.state === 'pass-through' ? 'Click-through' : 'Interactive';
    pointer.className = `pill ${payload.state === 'pass-through' ? 'ok' : 'warn'}`;
    return;
  }

  if (payload.type === 'capture-mode' && capture) {
    state.captureMode = payload.state === 'real' ? 'real' : 'synthetic';
    capture.textContent = state.captureMode === 'real' ? 'Real capture' : 'Synthetic capture';
    capture.className = `pill ${state.captureMode === 'real' ? 'ok' : 'warn'}`;
    const captureToggle = el('captureToggle');
    if (captureToggle) {
      captureToggle.textContent = state.captureMode === 'real' ? 'Disable real capture' : 'Enable real capture';
    }
    return;
  }

  if (payload.type === 'media-permission' && media) {
    media.textContent = payload.state === 'granted' ? 'Browser media granted' : 'Browser media locked';
    media.className = `pill ${payload.state === 'granted' ? 'ok' : 'warn'}`;
  }
}

function handleEvent(payload) {
  switch (payload.type) {
    case 'transcript_line':
      addTranscriptLine(payload);
      renderTranscript();
      break;
    case 'voice_emotion':
      state.voice = {
        emotion: payload.emotion || state.voice.emotion,
        stress: payload.stress_score ?? state.voice.stress,
        pace: payload.pace || state.voice.pace,
        energy: payload.energy ?? state.voice.energy
      };
      renderEmotionPanel();
      break;
    case 'face_emotion':
      state.face = {
        emotion: payload.emotion || state.face.emotion,
        gaze: payload.gaze || state.face.gaze,
        blink_rate: payload.blink_rate ?? state.face.blink_rate
      };
      renderEmotionPanel();
      break;
    case 'llm_start':
      state.insight = '';
      renderInsightPanel();
      break;
    case 'llm_token':
      state.insight = `${state.insight}${state.insight ? ' ' : ''}${payload.token || ''}`.trim();
      renderInsightPanel();
      break;
    case 'llm_insight':
      state.insight = payload.insight || state.insight;
      renderInsightPanel();
      break;
    case 'arrest_alert':
      state.arrest = {
        score: payload.arrest_score ?? state.arrest.score,
        verdict: payload.verdict || state.arrest.verdict,
        confidence: payload.confidence || state.arrest.confidence,
        signals: Array.isArray(payload.signals) ? payload.signals : state.arrest.signals
      };
      renderAlertPanel();
      break;
    default:
      break;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  renderAll();

  window.hud.onStatus(updateStatus);
  window.hud.onEvent(handleEvent);

  const mediaPermissionButton = el('mediaPermissionButton');
  if (mediaPermissionButton) {
    mediaPermissionButton.addEventListener('click', async () => {
      if (!navigator.mediaDevices || typeof navigator.mediaDevices.getUserMedia !== 'function') {
        mediaPermissionButton.textContent = 'Media unavailable';
        return;
      }

      mediaPermissionButton.disabled = true;
      mediaPermissionButton.textContent = 'Requesting...';

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });
        stream.getTracks().forEach((track) => track.stop());
        mediaPermissionButton.textContent = 'Permission granted';

        const mediaStatus = el('mediaStatus');
        if (mediaStatus) {
          mediaStatus.textContent = 'Browser media granted';
          mediaStatus.className = 'pill ok';
        }
      } catch (error) {
        mediaPermissionButton.textContent = 'Permission denied';

        const mediaStatus = el('mediaStatus');
        if (mediaStatus) {
          mediaStatus.textContent = 'Browser media locked';
          mediaStatus.className = 'pill warn';
        }
      } finally {
        setTimeout(() => {
          mediaPermissionButton.disabled = false;
          if (mediaPermissionButton.textContent === 'Permission granted') {
            mediaPermissionButton.textContent = 'Request permission';
          }
        }, 1500);
      }
    });
  }

  const captureToggle = el('captureToggle');
  if (captureToggle) {
    captureToggle.addEventListener('click', () => {
      const next = state.captureMode !== 'real';
      window.hud.setRealCapture(next);
      captureToggle.textContent = next ? 'Disable real capture' : 'Enable real capture';
    });
  }
});