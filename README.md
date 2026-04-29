# Digital Arrest

Realtime risk-monitoring overlay with an Electron frontend and a Python backend.

## Prerequisites

- Node.js 18+
- Python 3.10+
- Windows, macOS, or Linux

## Setup

1. Create and activate a virtual environment:

```powershell
cd python
python -m venv ..\venv
..\venv\Scripts\Activate.ps1
```

2. Install backend dependencies:

```powershell
pip install -r requirements.txt
```

3. Optional: install real-model dependencies:

```powershell
pip install -r requirements-real.txt
```

4. Install Electron dependencies:

```powershell
cd ..\electron
npm install
```

## Running

1. From `electron/`, start the app:

```powershell
npm start
```

2. Optional environment variables:

- `DIGITAL_ARREST_PORT` (default: `8765`)
- `DIGITAL_ARREST_ENABLE_REAL_MODELS` (`1` or `0`)
- `DIGITAL_ARREST_ENABLE_REAL_CAPTURE` (`1` or `0`)
- `DIGITAL_ARREST_LLM_MODEL_PATH` (required for llama-cpp real LLM mode)

Example:

```powershell
$env:DIGITAL_ARREST_LLM_MODEL_PATH = "D:\models\phi-3-mini.gguf"
$env:DIGITAL_ARREST_ENABLE_REAL_MODELS = "1"
```

Without `DIGITAL_ARREST_LLM_MODEL_PATH`, the app falls back to synthetic LLM insights.
