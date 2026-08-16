import streamlit as st
import os
import io
import tempfile
from PIL import Image

from ocr_engine import extract_pdf_pages_data, perform_ocr_on_image, clean_tamil_text
from tts_engine import get_tamil_voices, generate_speech, combine_audio_files
from vision_engine import describe_diagram_in_tamil
from utils import get_high_contrast_css, create_audio_zip

# Page setup
st.set_page_config(
    page_title="VizhiScribe - Tamil PDF to Voice for Visually Impaired",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'pages_data' not in st.session_state:
    st.session_state['pages_data'] = []
if 'edited_texts' not in st.session_state:
    st.session_state['edited_texts'] = {}
if 'generated_audios' not in st.session_state:
    st.session_state['generated_audios'] = {}
if 'high_contrast' not in st.session_state:
    st.session_state['high_contrast'] = False

# Sidebar Configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/reading.png", width=70)
    st.title("⚙️ அமைப்புகள் (Settings)")
    
    # Accessibility Mode
    high_contrast = st.toggle("👁️ High Contrast Mode (உயர் மாறுபாடு)", value=st.session_state['high_contrast'])
    st.session_state['high_contrast'] = high_contrast

    st.markdown("---")
    st.subheader("🗣️ Tamil Neural Voice (குரல் தேர்வு)")
    voices_dict = get_tamil_voices()
    selected_voice_label = st.selectbox(
        "Choose Voice:",
        options=list(voices_dict.keys()),
        index=0,
        help="Select natural Tamil voice actor"
    )
    selected_voice_id = voices_dict[selected_voice_label]

    st.markdown("---")
    st.subheader("⏩ Speech Speed (வாசிக்கும் வேகம்)")
    speed_pct = st.slider(
        "Speed percentage adjustment:",
        min_value=-40,
        max_value=80,
        value=0,
        step=10,
        format="%d%%",
        help="Negative = Slower speech. Positive = Faster speech for experienced listeners."
    )

    st.markdown("---")
    st.subheader("🤖 Vision AI for Diagrams (விருப்பத்தேர்வு)")
    api_provider = st.radio("AI Provider:", ["Gemini", "OpenAI"], index=0)
    api_key_input = st.text_input(
        "API Key (Optional for Diagram Description):",
        type="password",
        help="Enter API key to enable AI-powered Tamil descriptions of charts, diagrams, and figures."
    )

# Inject High Contrast CSS if enabled
st.markdown(get_high_contrast_css(st.session_state['high_contrast']), unsafe_allow_html=True)

# Main Application Title
st.markdown('<div class="main-header">🎙️ VizhiScribe (விழி-ஸ்கிரைப்)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">பார்வையற்ற மாணவர்களுக்கான பாடநூல் - தமிழ் ஒலிப் பதிவு கருவி (Tamil PDF & Diagram to Voice Converter)</div>', unsafe_allow_html=True)

# Application Tabs
tab1, tab2, tab3 = st.tabs(["📚 1. Document Reader & Audio (வாசிக்கும் பகுதி)", "📦 2. Full Chapter Export (முழு அத்தியாயம்)", "ℹ️ 3. Guide & Help (உதவி)"])

with tab1:
    st.markdown("### 📤 Step 1: Upload Book PDF or Image Pages")
    uploaded_file = st.file_uploader(
        "Choose PDF textbook or image file (PDF, PNG, JPG):",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload document file to start converting page text and images into voice notes"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()

        # Load PDF or Image data into session state
        if 'last_uploaded_name' not in st.session_state or st.session_state['last_uploaded_name'] != uploaded_file.name:
            with st.spinner("Processing document pages and extracting text..."):
                if file_name.endswith('.pdf'):
                    pages_data = extract_pdf_pages_data(file_bytes)
                else:
                    img = Image.open(io.BytesIO(file_bytes))
                    pages_data = [{
                        "page_num": 1,
                        "text": "",
                        "image": img,
                        "embedded_images": [img],
                        "is_scanned": True
                    }]
                
                st.session_state['pages_data'] = pages_data
                st.session_state['last_uploaded_name'] = uploaded_file.name
                st.session_state['edited_texts'] = {p['page_num']: p['text'] for p in pages_data}
                st.session_state['generated_audios'] = {}
            st.success(f"Successfully loaded {len(st.session_state['pages_data'])} page(s)!")

    # Page Navigation & Reader Section
    if st.session_state['pages_data']:
        pages_count = len(st.session_state['pages_data'])
        st.markdown("---")
        
        col_nav1, col_nav2 = st.columns([1, 3])
        with col_nav1:
            current_page_num = st.number_input(
                f"Select Page (1 of {pages_count}):",
                min_value=1,
                max_value=pages_count,
                value=1,
                step=1
            )
        with col_nav2:
            st.write("")
            st.write("")
            st.markdown(f"**Current Page Status:** Page {current_page_num} of {pages_count}")

        page_info = st.session_state['pages_data'][current_page_num - 1]

        # Layout Split: Original View (Left) vs Tamil Text & Controls (Right)
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader(f"🖼️ Page {current_page_num} Original View")
            st.image(page_info['image'], use_container_width=True)

            # Diagram & Embedded Images Section
            if page_info.get('embedded_images'):
                st.markdown(f"**Found {len(page_info['embedded_images'])} embedded diagram/figure(s) on this page:**")
                
                for idx, emb_img in enumerate(page_info['embedded_images']):
                    st.image(emb_img, caption=f"Diagram #{idx+1}", width=250)
                    
                    btn_key = f"describe_btn_{current_page_num}_{idx}"
                    if st.button(f"🔍 Describe Diagram #{idx+1} in Tamil", key=btn_key):
                        with st.spinner("Analyzing visual diagram with AI..."):
                            diagram_desc = describe_diagram_in_tamil(
                                emb_img, 
                                api_key=api_key_input, 
                                provider=api_provider
                            )
                            # Append description to current edited text
                            curr_text = st.session_state['edited_texts'].get(current_page_num, "")
                            updated_text = curr_text + f"\n\n[வரைபட விளக்கம் #{idx+1}]\n" + diagram_desc
                            st.session_state['edited_texts'][current_page_num] = updated_text
                            st.rerun()

        with col_right:
            st.subheader("📝 Extracted Tamil Text & Scribe Notes")

            # OCR Button Trigger
            if page_info['is_scanned'] or not st.session_state['edited_texts'].get(current_page_num):
                st.info("💡 Scanned image page detected or no text found automatically.")
                if st.button(f"⚡ Run Tamil OCR on Page {current_page_num}", key=f"ocr_btn_{current_page_num}"):
                    with st.spinner("Running Tamil OCR on scanned page..."):
                        ocr_result = perform_ocr_on_image(page_info['image'], api_key=api_key_input)
                        st.session_state['edited_texts'][current_page_num] = ocr_result
                        st.rerun()

            # Text Area for Scribe Editing
            initial_text_val = st.session_state['edited_texts'].get(current_page_num, "")
            
            edited_text = st.text_area(
                "Review & Edit Tamil Text before generating Voice:",
                value=initial_text_val,
                height=320,
                key=f"text_area_{current_page_num}",
                help="Scribe can edit typos, expand abbreviations, or add notes here."
            )
            # Update session state text
            st.session_state['edited_texts'][current_page_num] = edited_text

            st.markdown("---")
            st.subheader("🔊 Voice Note Generator (ஒலி பதிவு)")

            gen_col1, gen_col2 = st.columns([1, 1])

            with gen_col1:
                gen_btn = st.button(f"🎙️ Generate Voice for Page {current_page_num}", type="primary", use_container_width=True)

            if gen_btn:
                if not edited_text.strip():
                    st.warning("⚠️ Please provide text before generating voice.")
                else:
                    with st.spinner("Synthesizing natural Tamil speech..."):
                        try:
                            audio_path = generate_speech(
                                text=edited_text,
                                voice_id=selected_voice_id,
                                speed_pct=speed_pct
                            )
                            st.session_state['generated_audios'][current_page_num] = audio_path
                            st.success("✅ Voice note generated successfully!")
                        except Exception as err:
                            st.error(f"Error generating speech: {err}")

            # Audio Player & Download
            if current_page_num in st.session_state['generated_audios']:
                audio_file_path = st.session_state['generated_audios'][current_page_num]
                
                if os.path.exists(audio_file_path):
                    st.audio(audio_file_path, format="audio/mp3")
                    
                    with open(audio_file_path, "rb") as f:
                        audio_bytes = f.read()
                        
                    st.download_button(
                        label=f"⬇️ Download Page {current_page_num} Audio (.mp3)",
                        data=audio_bytes,
                        file_name=f"Page_{current_page_num}_Audio_Note.mp3",
                        mime="audio/mp3",
                        use_container_width=True
                    )

    else:
        st.info("👆 Please upload a Tamil textbook PDF or image file above to begin.")

with tab2:
    st.subheader("📦 Full Book / Chapter Audio Exporter")
    st.write("Generate and download all pages combined into a single chapter MP3 or ZIP bundle for offline listening.")

    if not st.session_state['pages_data']:
        st.warning("Please upload a document in Tab 1 first.")
    else:
        total_p = len(st.session_state['pages_data'])
        st.markdown(f"**Total Pages Loaded:** {total_p}")
        st.markdown(f"**Generated Page Audios:** {len(st.session_state['generated_audios'])} / {total_p}")

        col_batch1, col_batch2 = st.columns([1, 1])

        with col_batch1:
            if st.button("🎙️ Generate Audio for ALL Pages", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, page in enumerate(st.session_state['pages_data']):
                    p_num = page['page_num']
                    text_content = st.session_state['edited_texts'].get(p_num, page['text'])
                    
                    if not text_content.strip():
                        text_content = f"பக்கம் {p_num}. இந்த பக்கத்தில் உரை எதுவும் இல்லை."

                    status_text.text(f"Generating voice for Page {p_num} of {total_p}...")
                    try:
                        audio_p = generate_speech(
                            text=text_content,
                            voice_id=selected_voice_id,
                            speed_pct=speed_pct
                        )
                        st.session_state['generated_audios'][p_num] = audio_p
                    except Exception as e:
                        st.error(f"Page {p_num} error: {e}")
                        
                    progress_bar.progress((idx + 1) / total_p)

                status_text.text("✅ Finished generating all page audio notes!")
                st.rerun()

        if st.session_state['generated_audios']:
            st.markdown("---")
            st.subheader("⬇️ Download Chapter Bundles")
            
            exp_col1, exp_col2 = st.columns([1, 1])

            with exp_col1:
                # Combined MP3
                temp_dir = tempfile.gettempdir()
                combined_mp3_path = os.path.join(temp_dir, "Vizhi_Full_Chapter.mp3")
                sorted_files = [st.session_state['generated_audios'][k] for k in sorted(st.session_state['generated_audios'].keys())]
                
                with st.spinner("Combining audio files into full chapter MP3..."):
                    combine_audio_files(sorted_files, combined_mp3_path)
                    
                with open(combined_mp3_path, "rb") as f:
                    combined_bytes = f.read()

                st.download_button(
                    label="🎧 Download Full Chapter Audio (.mp3)",
                    data=combined_bytes,
                    file_name="Vizhi_Full_Chapter_Audio.mp3",
                    mime="audio/mp3",
                    use_container_width=True
                )

            with exp_col2:
                # ZIP Bundle
                zip_path = create_audio_zip(st.session_state['generated_audios'])
                with open(zip_path, "rb") as zf:
                    zip_bytes = zf.read()

                st.download_button(
                    label="📁 Download All Pages ZIP (.zip)",
                    data=zip_bytes,
                    file_name="Vizhi_Page_Audio_Notes.zip",
                    mime="application/zip",
                    use_container_width=True
                )

with tab3:
    st.subheader("ℹ️ Scribe & Student Guide (உதவி & வழிகாட்டி)")
    st.markdown("""
    ### VizhiScribe செயலியை எவ்வாறு பயன்படுத்துவது?
    
    1. **ஆவணத்தை பதிவேற்றவும் (Upload PDF/Image)**:
       - '1. Document Reader' பகுதியில் உங்கள் தமிழ் பாடநூல் PDF அல்லது பக்கத்தின் புகைப்படத்தை பதிவேற்றவும்.
       
    2. **உரையை சரிபார்க்கவும் (Review Text)**:
       - பக்கத்தில் உள்ள உரை வலது புறத்தில் தோன்றும். தேவைப்பட்டால் எழுத்துப் பிழைகளை திருத்தலாம்.
       - வரைபடங்கள் (Diagrams) இருந்தால், **'Describe Diagram in Tamil'** பொத்தானை அழுத்தி AI மூலம் வரைபடத்திற்கான தமிழ் விளக்கத்தைப் பெறலாம்.
       
    3. **குரல் பதிவு உருவாக்குதல் (Generate Voice)**:
       - **'Generate Voice'** பொத்தானை அழுத்தினால் பக்கத்திற்கான தமிழ் குரல் பதிவு (.mp3) உருவாகும்.
       - தேவையான வேகத்தில் (0.75x முதல் 1.5x வரை) கேட்டு மகிழலாம்.
       
    4. **உயர் மாறுபாடு பயன்முறை (High Contrast Mode)**:
       - குறைந்த பார்வைத் திறன் கொண்ட மாணவர்கள் (Low Vision Students) எளிதாகப் படிக்க இடது பக்க மெனுவில் **High Contrast Mode**-ஐ ஆன் செய்யவும் (மஞ்சள் மற்றும் கருப்பு வர்ணம்).
    """)
