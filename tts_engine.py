import asyncio
import os
import tempfile
import edge_tts
from gtts import gTTS

# Available Tamil Neural Voices in Edge TTS
TAMIL_VOICES = {
    "Pallavi (India Female - Natural)": "ta-IN-PallaviNeural",
    "Valluvar (India Male - Natural)": "ta-IN-ValluvarNeural",
    "Saranya (Sri Lanka Female)": "ta-LK-SaranyaNeural",
    "Kumar (Sri Lanka Male)": "ta-LK-KumarNeural",
    "Kani (Malaysia Female)": "ta-MY-KaniNeural",
    "Surya (Malaysia Male)": "ta-MY-SuryaNeural"
}

def get_tamil_voices():
    """Returns a dictionary of human-readable Tamil voice names to voice identifiers."""
    return TAMIL_VOICES

async def _generate_edge_tts_async(text: str, voice_id: str, speed_pct: int, output_path: str):
    """Internal async generator for edge-tts."""
    rate_str = f"{'+' if speed_pct >= 0 else ''}{speed_pct}%"
    communicate = edge_tts.Communicate(text, voice_id, rate=rate_str)
    await communicate.save(output_path)

def generate_speech(text: str, voice_id: str = "ta-IN-PallaviNeural", speed_pct: int = 0, output_path: str = None) -> str:
    """
    Generates Tamil speech audio file (.mp3) from text.
    Tries edge-tts (high quality neural voice) first, falls back to gTTS.
    
    :param text: Tamil text content
    :param voice_id: Neural voice ID
    :param speed_pct: Speed adjustment percentage (-50 to +100)
    :param output_path: Optional destination MP3 path
    :return: File path to generated MP3 file
    """
    if not text or not text.strip():
        raise ValueError("Text content cannot be empty.")
        
    if output_path is None:
        temp_dir = tempfile.gettempdir()
        output_path = os.path.join(temp_dir, f"vizhi_audio_{os.urandom(4).hex()}.mp3")
        
    cleaned_text = text.strip()

    try:
        # Run async edge-tts inside synchronous call
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_edge_tts_async(cleaned_text, voice_id, speed_pct, output_path))
        loop.close()
        return output_path
    except Exception as edge_err:
        print(f"[TTS Warning] Edge TTS failed: {edge_err}. Falling back to gTTS...")
        try:
            tts = gTTS(text=cleaned_text, lang='ta', slow=(speed_pct < -20))
            tts.save(output_path)
            return output_path
        except Exception as gtts_err:
            raise RuntimeError(f"Both Edge TTS and gTTS failed: {gtts_err}")

def combine_audio_files(file_list: list, output_path: str) -> str:
    """
    Combines multiple MP3 audio files into a single full-chapter MP3 file.
    Supports pydub or raw binary MP3 concatenation as fallback.
    """
    if not file_list:
        raise ValueError("No audio files provided to combine.")

    try:
        from pydub import AudioSegment
        combined = AudioSegment.empty()
        for fpath in file_list:
            if os.path.exists(fpath):
                segment = AudioSegment.from_mp3(fpath)
                combined += segment + AudioSegment.silent(duration=500) # 500ms pause between pages
        combined.export(output_path, format="mp3")
        return output_path
    except Exception:
        # Fallback to simple stream concatenation if pydub/ffmpeg is absent
        with open(output_path, 'wb') as outfile:
            for fpath in file_list:
                if os.path.exists(fpath):
                    with open(fpath, 'rb') as infile:
                        outfile.write(infile.read())
        return output_path
