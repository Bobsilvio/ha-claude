"""Voice routes blueprint.

Endpoints:
- GET /api/voice/stats
- POST /api/voice/transcribe
- POST /api/voice/tts
- GET /api/voice/tts/providers
"""

import logging
import os
import tempfile
from flask import Blueprint, request, jsonify, Response as FlaskResponse

logger = logging.getLogger(__name__)

voice_bp = Blueprint('voice', __name__)


@voice_bp.route('/api/voice/stats', methods=['GET'])
def api_voice_stats():
    """Get voice transcription statistics."""
    import api as _api
    try:
        if not _api.VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice transcription not available"}), 501
        transcriber = _api.voice_transcription.get_voice_transcriber()
        return jsonify({"status": "success", "voice_stats": transcriber.get_stats()}), 200
    except Exception as e:
        logger.error(f"Voice stats error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@voice_bp.route('/api/voice/transcribe', methods=['POST'])
def api_voice_transcribe():
    """Transcribe uploaded audio file to text (Groq Whisper -> OpenAI -> Google fallback).

    Multipart: audio file in field 'file'
    """
    import api as _api
    try:
        if not _api.VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice transcription not available"}), 501
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No audio file in request (field: 'file')"}), 400
        audio_file = request.files['file']
        suffix = os.path.splitext(audio_file.filename or 'audio.wav')[1] or '.wav'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            audio_file.save(tmp.name)
            tmp_path = tmp.name
        try:
            transcriber = _api.voice_transcription.get_voice_transcriber()
            success, text, provider = transcriber.transcribe_with_fallback(tmp_path)
        finally:
            os.unlink(tmp_path)
        if success:
            return jsonify({"status": "success", "text": text, "provider": provider}), 200
        else:
            return jsonify({"status": "error", "message": text}), 502
    except Exception as e:
        logger.error(f"Voice transcribe error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@voice_bp.route('/api/voice/tts', methods=['POST'])
def api_voice_tts():
    """Convert text to speech (Edge -> Groq -> OpenAI -> Google fallback).

    JSON body: { "text": "...", "voice": "..." }
    Returns: audio binary or JSON error
    """
    import api as _api
    try:
        if not _api.VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice transcription not available"}), 501
        data = request.json or {}
        text = data.get("text", "")
        if not text:
            return jsonify({"status": "error", "message": "text is required"}), 400
        tts = _api.voice_transcription.get_text_to_speech()
        voice = data.get("voice", _api.TTS_VOICE) or _api.TTS_VOICE
        success, audio_bytes = tts.speak_with_fallback(text, voice=voice)
        if success and audio_bytes:
            # Edge TTS produces mp3, Groq produces wav, OpenAI produces mp3
            # Detect format from first bytes
            if audio_bytes[:4] == b'RIFF':
                mimetype = "audio/wav"
            else:
                mimetype = "audio/mpeg"
            return FlaskResponse(audio_bytes, mimetype=mimetype)
        else:
            available = tts.get_available_providers()
            msg = f"TTS failed — no provider available. Available: {', '.join(available) if available else 'none'}"
            return jsonify({"status": "error", "message": msg}), 502
    except Exception as e:
        logger.error(f"Voice TTS error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@voice_bp.route('/api/voice/tts/providers', methods=['GET'])
def api_voice_tts_providers():
    """Get available TTS providers."""
    import api as _api
    try:
        if not _api.VOICE_TRANSCRIPTION_AVAILABLE:
            return jsonify({"status": "error", "message": "Voice module not available"}), 501
        tts = _api.voice_transcription.get_text_to_speech()
        return jsonify({
            "status": "success",
            "providers": tts.get_available_providers(),
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
