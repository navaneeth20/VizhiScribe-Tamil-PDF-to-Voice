import os
import zipfile
import tempfile

def create_audio_zip(audio_files_dict: dict, zip_name: str = "Vizhi_Audio_Notes.zip") -> str:
    """
    Creates a downloadable ZIP file containing audio notes for each page.
    :param audio_files_dict: Dict mapping page number/title to file path.
    :return: Path to zip file.
    """
    temp_dir = tempfile.gettempdir()
    zip_path = os.path.join(temp_dir, zip_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for page_num, file_path in audio_files_dict.items():
            if file_path and os.path.exists(file_path):
                arcname = f"Page_{page_num}_Audio.mp3"
                zipf.write(file_path, arcname=arcname)
                
    return zip_path

def get_high_contrast_css(enabled: bool = False) -> str:
    """
    Returns accessible custom CSS for low vision users and scribes.
    High Contrast Mode: High-contrast yellow text on black background with large readable fonts.
    """
    if not enabled:
        return """
        <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0F52BA;
            margin-bottom: 0.2rem;
        }
        .sub-header {
            font-size: 1.1rem;
            color: #4A5568;
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: bold;
        }
        .page-badge {
            background-color: #E2E8F0;
            padding: 4px 12px;
            border-radius: 12px;
            font-weight: bold;
            font-size: 0.9rem;
        }
        </style>
        """
    else:
        return """
        <style>
        /* High Contrast Accessibility Mode */
        html, body, [data-testid="stAppViewContainer"] {
            background-color: #000000 !important;
            color: #FFFF00 !important;
            font-size: 1.3rem !important;
        }
        [data-testid="stSidebar"] {
            background-color: #111111 !important;
            color: #00FF00 !important;
            border-right: 2px solid #FFFF00;
        }
        .stTextArea textarea, .stTextInput input {
            background-color: #1A1A1A !important;
            color: #00FF00 !important;
            border: 3px solid #FFFF00 !important;
            font-size: 1.4rem !important;
            font-weight: bold !important;
        }
        .stButton>button {
            background-color: #FFFF00 !important;
            color: #000000 !important;
            font-size: 1.3rem !important;
            font-weight: 900 !important;
            border: 3px solid #FFFFFF !important;
            border-radius: 10px !important;
        }
        .stButton>button:hover {
            background-color: #00FF00 !important;
            color: #000000 !important;
        }
        h1, h2, h3, h4, h5, h6, label, p, span {
            color: #FFFF00 !important;
            font-family: Arial, sans-serif !important;
        }
        .main-header {
            font-size: 2.8rem !important;
            font-weight: 900 !important;
            color: #00FF00 !important;
        }
        audio {
            filter: invert(100%);
        }
        </style>
        """
