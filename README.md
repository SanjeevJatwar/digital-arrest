# Praesidium Desktop Shield: Digital Arrest Scam Protection

Praesidium is an advanced real-time monitoring and threat detection system designed to protect users from "Digital Arrest" and other sophisticated financial scams. It combines real-time audio analysis, visual stress detection, and large language model (LLM) reasoning to provide immediate guidance to potential victims.

## Key Features

- **Real-time Call Monitoring**: Automatically detects communication windows (Zoom, WhatsApp, Google Meet) and begins monitoring if suspicious activity is detected.
- **Dual-Stream Audio Analysis**: Transcribes both the user (victim) and the caller (potential scammer) to analyze conversation patterns.
- **Multimodal Risk Engine**: Fuses speech analysis (pressure tactics, scam keywords) with visual cues (facial stress, attention levels) to calculate an overall threat score.
- **Live Guardian Advisor**: Provides step-by-step guidance on how to handle suspicious calls, including specific instructions to disconnect and report to authorities.
- **Digital Evidence Collection**: Safely logs suspicious patterns for potential reporting to legal authorities.

## Project Structure

- `backend/`: FastAPI server handling heavy-duty AI processing.
  - `main.py`: Entry point for the FastAPI server and route definitions.
  - `services/`: Specialized modules for analysis.
    - `scam_reasoning_engine.py`: Evaluates conversation logic for scam indicators.
    - `multimodal_risk_engine.py`: Analytical bridge between audio and video data.
    - `transcription_service.py`: Converts audio streams to text using Whisper.
    - `fraud_analyzer.py`: Performs NLP-based threat assessments.
- `desktop_app/`: PyQt6-based dashboard and system monitoring tools.
  - `main.py`: Primary GUI application and monitoring coordinator.
  - `audio/`: Logic for capturing and processing sound.
    - `mic_listener.py`: Dedicated handler for user microphone input.
    - `system_audio_listener.py`: Loopback handler to capture the caller's audio.
  - `video/`: Logic for camera-based visual analytics.
    - `webcam_monitor.py`: Real-time face and expression tracking.
    - `expression_analyzer.py`: Analyzes facial landmarks for stress signals.
- `requirements.txt`: Python package dependencies.
- `.gitignore`: Rules for ignoring unnecessary files in the repository.

## Tech Stack

- **Backend**: Python, FastAPI, Uvicorn, Faster-Whisper, OpenAI/Gemini (LLM Reasoning).
- **Frontend**: PyQt6 (Desktop UI).
- **AI/ML**: MediaPipe (Visual Analysis), NumPy, Scipy.

## Getting Started

### Prerequisites
- Python 3.9+
- Audio devices configured for loopback (to capture system audio).

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/SanjeevJatwar/digital-arrest.git
   cd digital-arrest
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file (see `.env.example`).

### Running the Project
1. **Start the Backend**:
   ```bash
   python backend/main.py
   ```
2. **Start the Desktop App**:
   ```bash
   python desktop_app/main.py
   ```

## Disclaimer
This software is designed as a support tool to help users recognize potential scams. It should not be the sole basis for making financial or legal decisions. Always verify identities through official government channels.
