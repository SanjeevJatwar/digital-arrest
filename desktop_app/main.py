import sys
import os
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import ctypes
import time

# Add workspace root to Python path
workspace_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

import requests
import numpy as np

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QScrollArea,
    QGridLayout,
    QSystemTrayIcon,
    QMenu,
    QStyle,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QTextCursor, QAction

from desktop_app.audio.mic_listener import MicListener
from desktop_app.audio.system_audio_listener import SystemAudioListener
from desktop_app.video.webcam_monitor import WebcamMonitor


BACKEND_ANALYZE_URL = "http://127.0.0.1:8000/analyze"
BACKEND_TRANSCRIBE_ANALYZE_URL = "http://127.0.0.1:8000/transcribe-analyze"
BACKEND_RESET_URL = "http://127.0.0.1:8000/reset-conversation"

class MiniShieldWidget(QWidget):
    def __init__(self, dashboard):
        super().__init__()

        self.dashboard = dashboard

        self.setWindowTitle("Praesidium Mini Shield")
        self.setFixedSize(320, 210)

        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )

        self.setup_ui()
        self.update_status("LOW", "Praesidium is ready")

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.title_label = QLabel("🛡 Praesidium Mini Shield")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("""
            font-size: 17px;
            font-weight: bold;
            color: white;
        """)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #22c55e;
            font-weight: bold;
        """)

        self.start_button = QPushButton("Start Shield")
        self.start_button.clicked.connect(self.dashboard.start_monitoring)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.dashboard.stop_monitoring)

        self.open_button = QPushButton("Open Dashboard")
        self.open_button.clicked.connect(self.open_dashboard)

        for button in [
            self.start_button,
            self.stop_button,
            self.open_button
        ]:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #1f8f3a;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 9px;
                    font-size: 13px;
                    font-weight: bold;
                }

                QPushButton:hover {
                    background-color: #249c40;
                }
            """)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.open_button)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: #020617;
                border: 1px solid #334155;
                border-radius: 12px;
                font-family: Arial;
            }
        """)

    def open_dashboard(self):
        self.dashboard.show()
        self.dashboard.raise_()
        self.dashboard.activateWindow()

    def update_status(self, threat_status, message):
        if threat_status == "HIGH":
            self.status_label.setText(
                "🚨 Digital Arrest Scam Detected\nDisconnect Immediately"
            )
            self.status_label.setStyleSheet("""
                font-size: 15px;
                color: white;
                font-weight: bold;
                background-color: #c70024;
                border-radius: 8px;
                padding: 8px;
            """)
            self.setStyleSheet("""
                QWidget {
                    background-color: #450a0a;
                    border: 2px solid #ff4d4d;
                    border-radius: 12px;
                    font-family: Arial;
                }
            """)

        elif threat_status == "MEDIUM":
            self.status_label.setText(
                "⚠ Suspicious Activity Detected\nVerify Before Acting"
            )
            self.status_label.setStyleSheet("""
                font-size: 15px;
                color: #111827;
                font-weight: bold;
                background-color: orange;
                border-radius: 8px;
                padding: 8px;
            """)
            self.setStyleSheet("""
                QWidget {
                    background-color: #422006;
                    border: 2px solid orange;
                    border-radius: 12px;
                    font-family: Arial;
                }
            """)

        else:
            self.status_label.setText("🛡 Monitoring Ready / No Major Threat")
            self.status_label.setStyleSheet("""
                font-size: 14px;
                color: #22c55e;
                font-weight: bold;
                background-color: #0f172a;
                border-radius: 8px;
                padding: 8px;
            """)
            self.setStyleSheet("""
                QWidget {
                    background-color: #020617;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    font-family: Arial;
                }
            """)

class PraesidiumDesktop(QWidget):
    backend_result_ready = pyqtSignal(str, object)
    volume_ready = pyqtSignal(str, float)
    backend_error = pyqtSignal(str)
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Praesidium Desktop Shield")
        self.resize(1500, 950)
        self.setMinimumSize(1280, 820)

        # ================= SERVICES =================
        self.mic_listener = MicListener()
        self.system_listener = SystemAudioListener()
        self.webcam_monitor = WebcamMonitor()

        self.latest_webcam_result = {
            "face_detected": False,
            "stress_level": "UNKNOWN",
            "attention_status": "UNKNOWN",
        }

        self.transcript_lines = deque(maxlen=60)
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.mic_processing = False
        self.system_processing = False
        self.is_monitoring_active = False
        self.last_detected_call_window = ""
        self.call_prompt_shown = False
        self.last_call_prompt_time = 0
        self.call_prompt_cooldown_seconds = 60
        self.backend_result_ready.connect(self.handle_backend_result)
        self.volume_ready.connect(self.handle_volume_update)
        self.backend_error.connect(self.handle_backend_error)

        self.timer = QTimer()
        self.timer.timeout.connect(self.process_audio)
        self.call_watch_timer = QTimer()
        self.call_watch_timer.timeout.connect(self.check_for_call_window)
        self.call_watch_timer.start(3000)

        self.setup_ui()
        self.reset_display()
        self.mini_widget = MiniShieldWidget(self)
        self.allow_exit = False
        self.setup_system_tray()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_dashboard()

    def show_dashboard(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def exit_application(self):
        self.allow_exit = True

        try:
            self.stop_monitoring()
        except Exception:
            pass

        try:
            self.executor.shutdown(wait=False)
        except Exception:
            pass

        try:
            self.mini_widget.close()
        except Exception:
            pass

        try:
            self.tray_icon.hide()
        except Exception:
            pass
        try:
            self.call_watch_timer.stop()
        except Exception:
            pass    

        QApplication.quit()

    # ====================================================
    # UI HELPERS
    # ====================================================

    def create_card(self, title_text):
        card = QFrame()
        card.setObjectName("card")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("cardTitle")

        layout.addWidget(title)

        return card, layout

    def create_value_label(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setObjectName("valueLabel")
        return label

    def set_badge_text(self, label, title, value):
        label.setText(f"<b>{title}:</b> {value}")

    def format_attention_text(self, attention):
        mapping = {
            "LOOKING_AT_SCREEN": "Looking at screen",
            "DISTRACTED": "Looking away / distracted",
            "DISTRACTED_OR_LOOKING_AWAY": "Looking away / distracted",
            "FACE_NOT_VISIBLE": "Face not visible",
            "UNKNOWN": "Not available",
            "Not started": "Not started",
        }
        return mapping.get(attention, str(attention).replace("_", " ").title())

    def format_visual_signal(self, level):
        mapping = {
            "HIGH": "Support recommended",
            "MEDIUM": "Possible concern",
            "LOW": "Low concern",
            "UNKNOWN": "Not available",
            "Not started": "Not started",
        }
        return mapping.get(level, str(level).replace("_", " ").title())

    def update_alert_banner(self, threat_status, message):
        if threat_status == "HIGH":
            self.alert_banner.setText(
                "🚨 HIGH RISK DIGITAL ARREST SCAM DETECTED — DISCONNECT IMMEDIATELY"
            )
            self.alert_banner.setStyleSheet("""
                QLabel {
                    background-color: #c70024;
                    color: white;
                    border: 2px solid #ff5c75;
                    border-radius: 12px;
                    padding: 12px;
                    font-size: 18px;
                    font-weight: bold;
                }
            """)
        elif threat_status == "MEDIUM":
            self.alert_banner.setText(
                "⚠ Suspicious activity detected — pause and verify before taking action"
            )
            self.alert_banner.setStyleSheet("""
                QLabel {
                    background-color: #f59e0b;
                    color: #111827;
                    border: 2px solid #fbbf24;
                    border-radius: 12px;
                    padding: 12px;
                    font-size: 17px;
                    font-weight: bold;
                }
            """)
        else:
            self.alert_banner.setText("🛡 Praesidium is standing by")
            self.alert_banner.setStyleSheet("""
                QLabel {
                    background-color: #111827;
                    color: #22c55e;
                    border: 1px solid #334155;
                    border-radius: 12px;
                    padding: 12px;
                    font-size: 17px;
                    font-weight: bold;
                }
            """)

        if hasattr(self, "mini_widget"):
            self.mini_widget.update_status(threat_status, message)

    # ====================================================
    # SETUP UI
    # ====================================================

    def setup_ui(self):
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(14, 14, 14, 14)
        root_layout.setSpacing(12)

        # ================= HEADER =================
        header_layout = QVBoxLayout()
        header_layout.setSpacing(6)

        self.title_label = QLabel("Praesidium Desktop Shield")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("mainTitle")

        self.subtitle_label = QLabel("Real-Time Digital Arrest Fraud Detection")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setObjectName("subTitle")

        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setObjectName("statusLabel")

        self.alert_banner = QLabel("🛡 Praesidium is standing by")
        self.alert_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.subtitle_label)
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.alert_banner)

        root_layout.addLayout(header_layout)

        # ================= MAIN TWO-COLUMN BODY =================
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        # ----------------------------------------------------
        # LEFT PANEL
        # ----------------------------------------------------
        left_panel = QVBoxLayout()
        left_panel.setSpacing(12)

        # Live Monitoring Card
        live_card, live_layout = self.create_card("Live Monitoring")

        monitoring_grid = QGridLayout()
        monitoring_grid.setHorizontalSpacing(18)
        monitoring_grid.setVerticalSpacing(8)

        self.mic_status_label = self.create_value_label("Microphone: Idle")
        self.caller_status_label = self.create_value_label("Caller Audio: Idle")
        self.face_status_label = self.create_value_label("Face Visibility: Not started")
        self.attention_label = self.create_value_label("Attention: Not started")
        self.visual_signal_label = self.create_value_label("Visual Support Signal: Not started")
        self.mic_volume_label = self.create_value_label("Your Audio Level: 0.00")
        self.caller_volume_label = self.create_value_label("Caller Audio Level: 0.00")

        monitoring_grid.addWidget(self.mic_status_label, 0, 0)
        monitoring_grid.addWidget(self.caller_status_label, 0, 1)
        monitoring_grid.addWidget(self.face_status_label, 1, 0)
        monitoring_grid.addWidget(self.attention_label, 1, 1)
        monitoring_grid.addWidget(self.visual_signal_label, 2, 0)
        monitoring_grid.addWidget(self.mic_volume_label, 3, 0)
        monitoring_grid.addWidget(self.caller_volume_label, 3, 1)

        live_layout.addLayout(monitoring_grid)
        left_panel.addWidget(live_card)

        # Transcript Card
        transcript_card, transcript_layout = self.create_card("Conversation Monitor")

        self.transcript_box = QPlainTextEdit()
        self.transcript_box.setReadOnly(True)
        self.transcript_box.setPlaceholderText(
            "Live caller and victim conversation will appear here..."
        )
        self.transcript_box.setObjectName("transcriptBox")
        self.transcript_box.setMinimumHeight(360)

        transcript_hint = QLabel(
            "Tip: Praesidium listens for caller pressure, victim confusion, and scam indicators in real time."
        )
        transcript_hint.setObjectName("hintLabel")
        transcript_hint.setWordWrap(True)

        transcript_layout.addWidget(self.transcript_box)
        transcript_layout.addWidget(transcript_hint)

        left_panel.addWidget(transcript_card, stretch=1)

        # Buttons Card
        buttons_card, buttons_layout = self.create_card("Actions")

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.start_button = QPushButton("Start Monitoring")
        self.start_button.clicked.connect(self.start_monitoring)

        self.stop_button = QPushButton("Stop Monitoring")
        self.stop_button.clicked.connect(self.stop_monitoring)

        self.run_demo_button = QPushButton("Run Demo")
        self.run_demo_button.clicked.connect(self.run_demo)

        self.analyze_button = QPushButton("Analyze Transcript")
        self.analyze_button.clicked.connect(self.analyze_transcript)

        self.clear_button = QPushButton("Clear Session")
        self.clear_button.clicked.connect(self.clear_all)
        self.mini_button = QPushButton("Mini Shield")
        self.mini_button.clicked.connect(self.show_mini_widget)

        for button in [
            self.start_button,
            self.stop_button,
            self.run_demo_button,
            self.analyze_button,
            self.clear_button,
            self.mini_button,
        ]:
            button.setObjectName("primaryButton")
            button_row.addWidget(button)

        buttons_layout.addLayout(button_row)
        left_panel.addWidget(buttons_card)

        # ----------------------------------------------------
        # RIGHT PANEL
        # ----------------------------------------------------
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setObjectName("rightScroll")

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(4, 4, 4, 4)
        right_layout.setSpacing(12)

        # Safety Overview
        overview_card, overview_layout = self.create_card("Safety Overview")

        self.threat_status_label = self.create_value_label("Threat Status: Not analyzed")
        self.scam_type_label = self.create_value_label("Scam Type: Not analyzed")
        self.confidence_label = self.create_value_label("Alert Confidence: Not available")
        self.victim_support_label = self.create_value_label("Victim Support Status: Not available")

        overview_layout.addWidget(self.threat_status_label)
        overview_layout.addWidget(self.scam_type_label)
        overview_layout.addWidget(self.confidence_label)
        overview_layout.addWidget(self.victim_support_label)

        right_layout.addWidget(overview_card)

        # Immediate Guidance
        guidance_card, guidance_layout = self.create_card("Safety Guidance")

        self.primary_guidance_label = self.create_value_label(
            "Recommended Action: Waiting for analysis"
        )
        self.support_guidance_label = self.create_value_label(
            "Support Guidance: Not available"
        )

        guidance_layout.addWidget(self.primary_guidance_label)
        guidance_layout.addWidget(self.support_guidance_label)

        right_layout.addWidget(guidance_card)

        # Observed Signals
        signals_card, signals_layout = self.create_card("Observed Signals")

        self.detected_patterns_label = self.create_value_label("Scam Signals: None")
        self.observed_signals_label = self.create_value_label("Victim Signals: Not available")

        signals_layout.addWidget(self.detected_patterns_label)
        signals_layout.addWidget(self.observed_signals_label)

        right_layout.addWidget(signals_card)

        # Reasoning
        reasoning_card, reasoning_layout = self.create_card("Praesidium Explanation")

        self.reasoning_label = self.create_value_label("Reasoning: Waiting for evidence")
        self.guardian_label = self.create_value_label("Safety Guidance Summary: Waiting for risk signal")
        self.llm_reasoning_label = self.create_value_label("AI Explanation: Not available")

        reasoning_layout.addWidget(self.reasoning_label)
        reasoning_layout.addWidget(self.guardian_label)
        reasoning_layout.addWidget(self.llm_reasoning_label)

        right_layout.addWidget(reasoning_card)

        # Detailed Guidance
        details_card, details_layout = self.create_card("Additional Guidance")

        self.guidance_steps_label = self.create_value_label("Guidance Steps: Not available")

        details_layout.addWidget(self.guidance_steps_label)

        right_layout.addWidget(details_card)
        right_layout.addStretch()

        right_scroll.setWidget(right_container)

        # Add to main body
        body_layout.addLayout(left_panel, stretch=7)
        body_layout.addWidget(right_scroll, stretch=5)

        root_layout.addLayout(body_layout)
        self.setLayout(root_layout)

        # ================= STYLES =================
        self.setStyleSheet("""
            QWidget {
                background-color: #020617;
                color: #e5e7eb;
                font-family: Arial, Helvetica, sans-serif;
                font-size: 14px;
            }

            QLabel#mainTitle {
                font-size: 28px;
                font-weight: bold;
                color: white;
            }

            QLabel#subTitle {
                font-size: 15px;
                color: #cbd5e1;
            }

            QLabel#statusLabel {
                font-size: 16px;
                font-weight: bold;
                color: #22c55e;
            }

            QFrame#card {
                background-color: #0f172a;
                border: 1px solid #1e293b;
                border-radius: 14px;
            }

            QLabel#cardTitle {
                font-size: 16px;
                font-weight: bold;
                color: #f8fafc;
                padding-bottom: 4px;
            }

            QLabel#valueLabel {
                background-color: #0b1220;
                border: 1px solid #1f2937;
                border-radius: 10px;
                padding: 10px 12px;
                color: #e5e7eb;
                font-size: 14px;
            }

            QLabel#hintLabel {
                color: #94a3b8;
                font-size: 13px;
                padding-top: 4px;
            }

            QPlainTextEdit#transcriptBox {
                background-color: #111827;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                selection-background-color: #1d4ed8;
            }

            QPushButton#primaryButton {
                background-color: #1f8f3a;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 14px;
                font-weight: bold;
                min-height: 22px;
            }

            QPushButton#primaryButton:hover {
                background-color: #249c40;
            }

            QPushButton#primaryButton:pressed {
                background-color: #176d2c;
            }

            QScrollArea#rightScroll {
                background-color: transparent;
                border: none;
            }
        """)

    # ====================================================
    # DISPLAY RESET
    # ====================================================

    def reset_display(self):
        self.status_label.setText("Status: Idle")
        self.update_alert_banner("LOW", "")

        self.mic_status_label.setText("Microphone: Idle")
        self.caller_status_label.setText("Caller Audio: Idle")
        self.face_status_label.setText("Face Visibility: Not started")
        self.attention_label.setText("Attention: Not started")
        self.visual_signal_label.setText("Visual Support Signal: Not started")
        self.mic_volume_label.setText("Your Audio Level: 0.00")
        self.caller_volume_label.setText("Caller Audio Level: 0.00")

        self.threat_status_label.setText("Threat Status: Not analyzed")
        self.scam_type_label.setText("Scam Type: Not analyzed")
        self.confidence_label.setText("Alert Confidence: Not available")
        self.victim_support_label.setText("Victim Support Status: Not available")

        self.primary_guidance_label.setText("Recommended Action: Waiting for analysis")
        self.support_guidance_label.setText("Support Guidance: Not available")

        self.detected_patterns_label.setText("Scam Signals: None")
        self.observed_signals_label.setText("Victim Signals: Not available")

        self.reasoning_label.setText("Reasoning: Waiting for evidence")
        self.guardian_label.setText("Safety Guidance Summary: Waiting for risk signal")
        self.llm_reasoning_label.setText("AI Explanation: Not available")
        self.guidance_steps_label.setText("Guidance Steps: Not available")

    # ====================================================
    # MONITORING CONTROL
    # ====================================================

    def start_monitoring(self):
        try:
            self.mic_listener.start()
            self.system_listener.start()
            self.webcam_monitor.start()

            self.status_label.setText("Status: Monitoring active")
            self.mic_status_label.setText("Microphone: Active")
            self.caller_status_label.setText("Caller Audio: Active")
            self.is_monitoring_active = True
            self.call_prompt_shown = True

            self.timer.start(5000)
        except Exception as e:
            self.status_label.setText(f"Status: Failed to start monitoring ({str(e)})")

    def stop_monitoring(self):
        self.timer.stop()

        try:
            self.mic_listener.stop()
        except Exception:
            pass

        try:
            self.system_listener.stop()
        except Exception:
            pass

        try:
            self.webcam_monitor.stop()
        except Exception:
            pass

        self.status_label.setText("Status: Idle")
        self.mic_status_label.setText("Microphone: Idle")
        self.caller_status_label.setText("Caller Audio: Idle")
        self.is_monitoring_active = False
        self.call_prompt_shown = False

    # ====================================================
    # AUDIO / VIDEO LOOP
    # ====================================================

    def process_audio(self):
        self.process_webcam()
        if not self.mic_processing:
            self.mic_processing = True
            self.executor.submit(
                self.process_single_audio_stream_worker,
                self.mic_listener,
                 "Victim"
            )
        if not self.system_processing:
            self.system_processing = True
            self.executor.submit(
                self.process_single_audio_stream_worker,
                self.system_listener,
                "Suspicious_Caller"
            )

    def process_webcam(self):
        result = self.webcam_monitor.analyze_frame()
        self.latest_webcam_result = result

        face_detected = result.get("face_detected", False)
        attention = result.get("attention_status", "UNKNOWN")
        stress = result.get("stress_level", "UNKNOWN")

        self.face_status_label.setText(
            f"Face Visibility: {'Visible' if face_detected else 'Not visible'}"
        )
        self.attention_label.setText(
            f"Attention: {self.format_attention_text(attention)}"
        )
        self.visual_signal_label.setText(
            f"Visual Support Signal: {self.format_visual_signal(stress)}"
        )

    # ====================================================
    # TRANSCRIPT HELPERS
    # ====================================================

    def append_transcript_line(self, speaker_label, transcript):
        if not transcript:
            return

        if speaker_label == "Victim":
            prefix = "You"
        else:
            prefix = "Caller"

        line = f"{prefix}: {transcript.strip()}"

        if self.transcript_lines and self.transcript_lines[-1] == line:
            return

        self.transcript_lines.append(line)
        self.transcript_box.setPlainText("\n".join(self.transcript_lines))

        cursor = self.transcript_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transcript_box.setTextCursor(cursor)

    # ====================================================
    # BACKEND COMMUNICATION
    # ====================================================

    def process_single_audio_stream_worker(self, listener, speaker_label):
        wav_path = None

        try:
            audio_chunk = listener.get_audio_chunk()

            if audio_chunk is None:
                return

            volume = float(np.abs(audio_chunk).mean())

            # Send volume update safely to UI thread
            self.volume_ready.emit(speaker_label, volume)

            if speaker_label == "Victim":
                min_volume = 25
            else:
                min_volume = 0.03

            if volume < min_volume:
                return

            wav_path = listener.save_chunk_to_wav(audio_chunk)

            webcam_context = self.latest_webcam_result

            with open(wav_path, "rb") as audio_file:
                files = {
                    "file": ("audio_chunk.wav", audio_file, "audio/wav")
                }

                response = requests.post(
                    BACKEND_TRANSCRIBE_ANALYZE_URL,
                    files=files,
                    data={
                        "speaker": speaker_label,
                        "face_detected": str(webcam_context.get("face_detected", False)),
                        "visual_stress_level": webcam_context.get("stress_level", "UNKNOWN"),
                        "attention_status": webcam_context.get("attention_status", "UNKNOWN"),
                    },
                    timeout=90
                )

            response.raise_for_status()
            data = response.json()

            # Send backend result safely to UI thread
            self.backend_result_ready.emit(speaker_label, data)

        except Exception as e:
            self.backend_error.emit(
                f"{speaker_label} analysis failed: {str(e)}"
            )

        finally:
            # Allow next chunk for that stream
            if speaker_label == "Victim":
                self.mic_processing = False
            else:
                self.system_processing = False

            # Clean temporary wav file
            try:
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass

    def handle_volume_update(self, speaker_label, volume):
        if speaker_label == "Victim":
            self.mic_volume_label.setText(f"Your Audio Level: {volume:.2f}")
        else:
            self.caller_volume_label.setText(f"Caller Audio Level: {volume:.2f}")

    def handle_backend_error(self, message):
        self.primary_guidance_label.setText(
            f"Recommended Action: {message}"
        )

    def handle_backend_result(self, speaker_label, data):
        transcript = data.get("transcript", "")
        fused_analysis = data.get("fused_analysis", {})
        scam_reasoning = data.get("scam_reasoning", {})
        live_guidance = data.get("live_guidance", {})
        llm_reasoning = data.get("llm_reasoning", {})
        victim_support = data.get("victim_support", {})

        if transcript:
            self.append_transcript_line(speaker_label, transcript)

        threat_status = fused_analysis.get("fused_risk_level", "LOW")
        confidence = scam_reasoning.get("confidence", "Not available")
        scam_type = scam_reasoning.get("scam_type", "Unknown")

        action = live_guidance.get(
            "primary_message",
            fused_analysis.get("final_action", "Continue monitoring.")
        )

        self.threat_status_label.setText(f"Threat Status: {threat_status}")
        self.scam_type_label.setText(f"Scam Type: {scam_type}")
        self.confidence_label.setText(f"Alert Confidence: {confidence}")

        self.victim_support_label.setText(
            f"Victim Support Status: {victim_support.get('support_status', 'Not available')}"
        )

        self.primary_guidance_label.setText(
            f"Recommended Action: {action}"
        )

        supportive_interventions = victim_support.get("supportive_interventions", [])

        if supportive_interventions:
            self.support_guidance_label.setText(
                "Support Guidance: " + " | ".join(supportive_interventions[:3])
            )
        else:
            self.support_guidance_label.setText("Support Guidance: Not available")

        patterns = data.get("analysis", {}).get("detected_patterns", [])

        self.detected_patterns_label.setText(
            "Scam Signals: " + (", ".join(patterns) if patterns else "None")
        )

        observed_signals = victim_support.get("observed_signals", [])

        if observed_signals:
            self.observed_signals_label.setText(
                "Victim Signals: " + " | ".join(observed_signals[:3])
            )
        else:
            self.observed_signals_label.setText("Victim Signals: Not available")

        reasoning_summary = scam_reasoning.get(
            "reasoning_summary",
            "No reasoning available"
        )

        self.reasoning_label.setText(f"Reasoning: {reasoning_summary}")

        guidance_steps = live_guidance.get("guidance_steps", [])

        self.guardian_label.setText(
            "Safety Guidance Summary: "
            + (guidance_steps[0] if guidance_steps else "No guidance available")
        )

        self.llm_reasoning_label.setText(
            f"AI Explanation: {llm_reasoning.get('llm_summary', 'No AI reasoning available')}"
        )

        if guidance_steps:
            self.guidance_steps_label.setText(
                "Guidance Steps: " + " | ".join(guidance_steps[:4])
            )
        else:
            self.guidance_steps_label.setText("Guidance Steps: Not available")

        self.update_alert_banner(threat_status, action)

        # -------- Main threat state --------
        threat_status = fused_analysis.get("fused_risk_level", "LOW")
        confidence = scam_reasoning.get("confidence", "Not available")
        scam_type = scam_reasoning.get("scam_type", "Unknown")

        action = live_guidance.get(
            "primary_message",
            fused_analysis.get("final_action", "Continue monitoring.")
        )

        self.threat_status_label.setText(
            f"Threat Status: {threat_status}"
        )

        self.scam_type_label.setText(
            f"Scam Type: {scam_type}"
        )

        self.confidence_label.setText(
            f"Alert Confidence: {confidence}"
        )

        self.victim_support_label.setText(
            f"Victim Support Status: {victim_support.get('support_status', 'Not available')}"
        )

        self.primary_guidance_label.setText(
            f"Recommended Action: {action}"
        )

        supportive_interventions = victim_support.get("supportive_interventions", [])

        if supportive_interventions:
            self.support_guidance_label.setText(
                "Support Guidance: " + " | ".join(supportive_interventions[:3])
            )
        else:
            self.support_guidance_label.setText(
                "Support Guidance: Not available"
            )

        patterns = data.get("analysis", {}).get("detected_patterns", [])

        self.detected_patterns_label.setText(
            "Scam Signals: " + (", ".join(patterns) if patterns else "None")
        )

        observed_signals = victim_support.get("observed_signals", [])

        if observed_signals:
            self.observed_signals_label.setText(
                "Victim Signals: " + " | ".join(observed_signals[:3])
            )
        else:
            self.observed_signals_label.setText(
                "Victim Signals: Not available"
            )

        reasoning_summary = scam_reasoning.get(
            "reasoning_summary",
            "No reasoning available"
        )

        self.reasoning_label.setText(
            f"Reasoning: {reasoning_summary}"
        )

        guidance_steps = live_guidance.get("guidance_steps", [])

        self.guardian_label.setText(
            "Safety Guidance Summary: "
            + (guidance_steps[0] if guidance_steps else "No guidance available")
        )

        self.llm_reasoning_label.setText(
            f"AI Explanation: {llm_reasoning.get('llm_summary', 'No AI reasoning available')}"
        )

        if guidance_steps:
            self.guidance_steps_label.setText(
                "Guidance Steps: " + " | ".join(guidance_steps[:4])
            )
        else:
            self.guidance_steps_label.setText(
                "Guidance Steps: Not available"
            )

        self.update_alert_banner(threat_status, action)

    # ====================================================
    # MANUAL ANALYZE
    # ====================================================

    def analyze_transcript(self):
        text = self.transcript_box.toPlainText().strip()

        if not text:
            self.primary_guidance_label.setText(
                "Recommended Action: Please enter or capture a transcript first."
            )
            return

        try:
            response = requests.post(
                BACKEND_ANALYZE_URL,
                json={"text": text},
                timeout=15
            )
            response.raise_for_status()

            data = response.json()

            risk_level = data.get("risk_level", "UNKNOWN")
            risk_score = data.get("risk_score", 0)
            patterns = data.get("detected_patterns", [])
            action = data.get("recommended_action", "No recommendation available.")

            if risk_level == "HIGH":
                confidence = "High"
            elif risk_level == "MEDIUM":
                confidence = "Medium"
            else:
                confidence = "Low"

            self.threat_status_label.setText(f"Threat Status: {risk_level}")
            self.scam_type_label.setText("Scam Type: Preliminary transcript analysis")
            self.confidence_label.setText(f"Alert Confidence: {confidence} ({risk_score}/100)")
            self.primary_guidance_label.setText(f"Recommended Action: {action}")
            self.detected_patterns_label.setText(
                "Scam Signals: " + (", ".join(patterns) if patterns else "None")
            )

            self.update_alert_banner(risk_level, action)

        except Exception as e:
            self.primary_guidance_label.setText(
                f"Recommended Action: Backend connection failed - {str(e)}"
            )

    # ====================================================
    # DEMO
    # ====================================================

    def run_demo(self):
        demo_lines = [
            "Caller: Hello, this is from Delhi Police Cyber Crime Division.",
            "Caller: Your Aadhaar card is linked with money laundering activities.",
            "Caller: You are under digital arrest.",
            "Caller: Do not disconnect this video call.",
            "Caller: Transfer money immediately for account verification.",
            "You: I have not done anything. What should I do?"
        ]

        self.transcript_lines.clear()
        for line in demo_lines:
            self.transcript_lines.append(line)

        self.transcript_box.setPlainText("\n".join(self.transcript_lines))
        self.analyze_transcript()

    # ====================================================
    # CLEAR
    # ====================================================

    def clear_all(self):
        try:
            requests.post(BACKEND_RESET_URL, timeout=5)
        except Exception:
            pass

        self.transcript_lines.clear()
        self.transcript_box.clear()
        self.reset_display()

    def show_mini_widget(self):
        self.mini_widget.show()
        self.mini_widget.raise_()
        self.mini_widget.activateWindow()
        self.hide()
    def setup_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = QApplication.style().standardIcon(
            QStyle.StandardPixmap.SP_ComputerIcon
        )
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Praesidium Desktop Shield")
        tray_menu = QMenu()
        open_dashboard_action = QAction("Open Dashboard", self)
        open_dashboard_action.triggered.connect(self.show_dashboard)
        mini_shield_action = QAction("Open Mini Shield", self)
        mini_shield_action.triggered.connect(self.show_mini_widget)
        start_action = QAction("Start Monitoring", self)
        start_action.triggered.connect(self.start_monitoring)
        stop_action = QAction("Stop Monitoring", self)
        stop_action.triggered.connect(self.stop_monitoring)
        hide_action = QAction("Hide Dashboard", self)
        hide_action.triggered.connect(self.hide)
        exit_action = QAction("Exit Praesidium", self)
        exit_action.triggered.connect(self.exit_application)
        tray_menu.addAction(open_dashboard_action)
        tray_menu.addAction(mini_shield_action)
        tray_menu.addSeparator()
        tray_menu.addAction(start_action)
        tray_menu.addAction(stop_action)
        tray_menu.addSeparator()
        tray_menu.addAction(hide_action)
        tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
    def get_active_window_title(self):
        try:
            user32 = ctypes.windll.user32

            window = user32.GetForegroundWindow()

            length = user32.GetWindowTextLengthW(window)

            buffer = ctypes.create_unicode_buffer(length + 1)

            user32.GetWindowTextW(window, buffer, length + 1)

            return buffer.value

        except Exception:
             return ""
    def check_for_call_window(self):
        if self.is_monitoring_active:
            return

        title = self.get_active_window_title()

        if not title:
            return

        title_lower = title.lower()

        call_keywords = [
            "zoom",
            "google meet",
            "meet",
            "whatsapp",
            "microsoft teams",
            "teams",
            "video call",
            "meeting",
        ]

        detected = any(keyword in title_lower for keyword in call_keywords)

        if not detected:
            return
        current_time = time.time()
          # Avoid repeated notification spam
        if (
            self.call_prompt_shown
            and current_time - self.last_call_prompt_time < self.call_prompt_cooldown_seconds
        ):
            return
        self.call_prompt_shown = True
        self.last_call_prompt_time = current_time
        self.last_detected_call_window = title
        self.show_mini_widget()
        if hasattr(self, "tray_icon"):
            self.tray_icon.showMessage(
                "Praesidium Shield",
                "Communication window detected. Start Praesidium Shield if this call feels suspicious.",
                QSystemTrayIcon.MessageIcon.Information,
                5000
            ) 


    
    # ====================================================
    # CLOSE EVENT
    # ====================================================

    def closeEvent(self, event):
        if self.allow_exit:
            try:
                self.stop_monitoring()
            except Exception:
                pass

            try:
                self.executor.shutdown(wait=False)
            except Exception:
                pass

            event.accept()
        else:
            event.ignore()
            self.hide()

            if hasattr(self, "tray_icon"):
                self.tray_icon.showMessage(
                    "Praesidium is still running",
                    "Praesidium has been minimized to the system tray.",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )


# ========================================================
# MAIN
# ========================================================

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = PraesidiumDesktop()
    window.show()
    sys.exit(app.exec())