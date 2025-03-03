import streamlit as st  # Streamlit for UI
import openai  # OpenAI API for generating stories
import locale  # Locale for detecting system language
import speech_recognition as sr  # Speech-to-text conversion
import os  # File operations
import tempfile  # Temporary file handling
import wave  # WAV audio processing
import io  # Input/output operations
from gtts import gTTS  # Google Text-to-Speech for audio playback

# 1) Import the st_audiorec function from streamlit-audiorec
from st_audiorec import st_audiorec

# 2) Set OpenAI API Key (must be set in Streamlit secrets)
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getlocale()[0]
default_lang = "de" if user_locale and "de" in user_locale else "en"  # Default to German if locale contains 'de', otherwise English

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}  # Language options
selected_lang = st.selectbox(
    "🌍 Select Language / Sprache wählen:",
    list(lang_options.keys()),
    index=0 if default_lang == "en" else 1
)
lang = lang_options[selected_lang]  # Store selected language

# 🏗 **Initialize Session State Variables**
if "story" not in st.session_state:
    st.session_state.story = ""  # Stores the generated story
if "history" not in st.session_state:
    st.session_state.history = []  # Stores story progression
if "user_decision" not in st.session_state:
    st.session_state.user_decision = None  # Stores last user input
if "topic" not in st.session_state:
    st.session_state.topic = None  # Stores the transcribed topic
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = None  # Stores the last transcribed text
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None  # Stores the generated audio file
if "story_generated" not in st.session_state:
    st.session_state.story_generated = False  # 🚀 Prevent infinite loops

# 🎙️ **Function to Validate WAV Files** (can still be useful if you want to check format)
def validate_wav(audio_path):
    """Ensures the recorded WAV file is valid and playable."""
    try:
        with wave.open(audio_path, "rb") as wav_file:
            params = wav_file.getparams()
            num_channels, sampwidth, framerate, nframes = params[:4]
            
            # ✅ Validate PCM WAV format
            if sampwidth != 2:
                st.error("❌ Error: WAV file must be 16-bit PCM.")
                return None
            if num_channels not in [1, 2]:
                st.error("❌ Error: WAV file must be mono or stereo.")
                return None
            if framerate < 8000 or framerate > 48000:
                st.error("❌ Error: WAV file sample rate must be between 8kHz and 48kHz.")
                return None
            
            return audio_path  # Return valid file path if checks pass

    except Exception as e:
        st.error(f"❌ WAV processing error: {str(e)}")
        return None

# 🎙️ **Speech-to-Text (Transcription)**
def transcribe_audio(audio_path):
    """
    Converts speech to text from a WAV file using Google's Speech Recognition API.
    """
    # ✅ Check if the file exists and is not empty
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        st.error("❌ Error: Audio file is empty or not recorded correctly.")
        return None

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language="de-DE" if lang == "de" else "en-US")
        st.session_state.transcribed_text = text
        return text
    except sr.UnknownValueError:
        st.warning("⚠️ Could not understand the audio. Try speaking more clearly.")
        return None
    except sr.RequestError:
        st.error("❌ Error: Could not connect to speech recognition service.")
        return None
    except Exception as e:
        st.error(f"❌ Audio processing error: {str(e)}")
        return None

# 🔊 **Text-to-Speech**
def text_to_speech(text):
    """Generates and saves speech audio from text using gTTS."""
    try:
        if not text or len(text.strip()) == 0:
            st.error("❌ Error: No text provided for speech generation.")
            return None

        tts = gTTS(text, lang="de" if lang == "de" else "en")
        temp_audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
        tts.save(temp_audio_path)

        if os.path.exists(temp_audio_path) and os.path.getsize(temp_audio_path) > 0:
            st.success(f"✅ Speech file successfully generated: {temp_audio_path}")
            return temp_audio_path
        else:
            st.error("❌ TTS Error: Generated file is empty.")
            return None

    except Exception as e:
        st.error(f"❌ TTS Error: {str(e)}")
        return None

# 📜 **UI Title**
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

# ─────────────────────────────────────────────────────────
#  REPLACE FILE-UPLOADER SECTION WITH ST_AUDIOREC SNIPPET
# ─────────────────────────────────────────────────────────
st.info("📢 Record your voice to start your story. Speak a topic (e.g., 'dinosaurs', 'princesses', etc.)")

def record_and_play_audio():
    """
    Shows an audio recorder widget to the user, 
    and once the user finishes recording, displays an audio player for immediate playback.
    """
    # 1. Prompt the user to record audio
    st.subheader("1. Record Audio")
    st.write("Click on the microphone icon below to start recording, and click again to stop.")

    # The st_audiorec function returns audio data (as a WAV buffer) once recording ends.
    audio_data = st_audiorec()

    # 2. If audio data is available, show an audio player
    if audio_data is not None:
        st.subheader("2. Play Recorded Audio")
        st.write("Your recorded audio is ready to play. Click the play button below.")
        st.audio(audio_data, format='audio/wav')

        # 3. Transcribe the audio, if we don't already have a transcribed text
        if not st.session_state.transcribed_text:
            # Save the buffer to a temp file for transcription
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                tmp_wav.write(audio_data)
                tmp_path = tmp_wav.name

            # (Optional) Validate the WAV if desired
            valid_path = validate_wav(tmp_path)
            if valid_path:
                # Now do the transcription
                topic = transcribe_audio(valid_path)
                if topic:
                    st.success(f"✅ You said: {topic}")
                    st.session_state.topic = topic
                    st.session_state.story = f"Generating a story about {topic}..."
                    st.session_state.story_generated = False
                    # We can optionally force a rerun to proceed with story generation
                    st.experimental_rerun()

# Call our new function to handle recording
record_and_play_audio()

# ─────────────────────────────────────────────────────────
#  CONTINUE WITH STORY GENERATION IF WE HAVE A TOPIC
# ─────────────────────────────────────────────────────────
# 🌟 **Generate Initial Story**
if st.session_state.topic and not st.session_state.story_generated:
    topic = st.session_state.topic
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""Create a fun, engaging children's story for a 5-year-old in {lang}.
                Each section should be around 200 words long.
                The story should flow naturally and lead to a decision point where the main character needs to decide what to do next.
                This decision point should be obvious but not limited to two specific options.
                It should feel open-ended, allowing different choices from the reader."""},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"Ensure that the story section is about 200 words long and ends at an open-ended decision point."}
            ]
        )

        st.session_state.story = response.choices[0].message.content
        st.session_state.history.append(st.session_state.story)

        # Generate speech audio
        audio_path = text_to_speech(st.session_state.story)
        if audio_path:
            st.session_state.audio_file = audio_path

        st.session_state.transcribed_text = None
        st.session_state.story_generated = True

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ─────────────────────────────────────────────────────────
#  SHOW & PLAY STORY IF GENERATED
# ─────────────────────────────────────────────────────────
if st.session_state.story:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)

    # Make sure we generate the audio only once
    if "audio_file" not in st.session_state or not st.session_state.audio_file:
        if "audio_generated" not in st.session_state or not st.session_state.audio_generated:
            generated_audio = text_to_speech(st.session_state.story)
            if generated_audio and os.path.exists(generated_audio):
                st.session_state.audio_file = generated_audio
                st.session_state.audio_generated = True
            else:
                st.error("❌ Failed to generate speech audio.")

    audio_path = st.session_state.get("audio_file", None)

    if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
        try:
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
                st.success("✅ Audio playback successful!")

                st.download_button(
                    label="⬇️ Download Speech MP3",
                    data=audio_bytes,
                    file_name="speech.mp3",
                    mime="audio/mpeg",
                    key="download_button",
                    disabled=False
                )
            else:
                st.error("❌ The generated audio file is empty.")
        except Exception as e:
            st.error(f"❌ Error playing audio: {str(e)}")
            st.session_state.audio_file = None
    else:
        st.error("❌ No valid audio file found or it is corrupted.")
