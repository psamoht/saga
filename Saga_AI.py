import streamlit as st
import openai
import locale
import speech_recognition as sr
import os
import tempfile
import io
import wave
from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
from streamlit_mic_recorder import mic_recorder

# OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getdefaultlocale()[0]
default_lang = "de" if user_locale and "de" in user_locale else "en"

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}
selected_lang = st.selectbox("🌍 Select Language / Sprache wählen:", list(lang_options.keys()), index=0 if default_lang == "en" else 1)
lang = lang_options[selected_lang]

# 🏗 Session State Initialization
if "story" not in st.session_state:
    st.session_state.story = ""
if "history" not in st.session_state:
    st.session_state.history = []
if "user_decision" not in st.session_state:
    st.session_state.user_decision = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

# 🎙️ Speech-to-Text Function (Fixed)
def transcribe_audio(audio_numpy):
    if audio_numpy is None:
        st.warning("⚠️ No audio detected. Please try speaking again.")
        return None

    recognizer = sr.Recognizer()
    
    # Convert NumPy array to WAV format
    with io.BytesIO() as temp_audio:
        with wave.open(temp_audio, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono audio
            wav_file.setsampwidth(2)  # 16-bit audio
            wav_file.setframerate(44100)  # Sample rate
            wav_file.writeframes(audio_numpy.tobytes())  # Convert NumPy to bytes
        
        temp_audio.seek(0)  # Reset pointer for reading

        # Process with SpeechRecognition
        with sr.AudioFile(temp_audio) as source:
            audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language="de-DE" if lang == "de" else "en-US")
            return text
        except sr.UnknownValueError:
            st.warning("⚠️ Could not understand the audio. Try speaking more clearly.")
            return None
        except sr.RequestError:
            st.error("❌ Error: Could not connect to speech recognition service.")
            return None

# 🔊 Text-to-Speech Function
def text_to_speech(text):
    tts = gTTS(text, lang="de" if lang == "de" else "en")
    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp_audio.name)
    return temp_audio.name

# 📜 UI Title
st.title("🎙️ Saga – Be Part of the Story" if lang == "en" else "🎙️ Saga – Sei Teil der Geschichte")

# 🎤 Welcome Message & Voice Input for Topic
if not st.session_state.story:
    st.info("📢 Welcome! Please speak a topic for your story.")
    audio_bytes = mic_recorder(start_prompt="🎤 Speak Topic" if lang == "en" else "🎤 Thema sprechen")
    
    if audio_bytes is not None:
        topic = transcribe_audio(audio_bytes)
        if topic:
            st.success(f"✅ You said: {topic}")
            st.session_state.story = f"Generating a story about {topic}..."
            st.rerun()

# 🌟 Generate Initial Story
if st.session_state.story and st.session_state.story.startswith("Generating a story"):
    topic = st.session_state.story.replace("Generating a story about ", "").strip()
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                                              f"Each section should be around 200 words long. "
                                              f"The story should flow naturally and lead to a decision point where the main character needs to decide what to do next. "
                                              f"This decision point should be obvious but not limited to two specific options. "
                                              f"It should feel open-ended, allowing different choices from the reader."},
                {"role": "user", "content": f"Write a children's story about {topic}. "
                                            f"Ensure that the story section is about 200 words long and ends at an open-ended decision point."}
            ]
        )

        # Save the story and reset state
        st.session_state.story = response.choices[0].message.content
        st.session_state.history.append(st.session_state.story)

        # Convert story to speech
        st.session_state.audio_file = text_to_speech(st.session_state.story)
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# 📖 Play and Display Story
if st.session_state.story and st.session_state.audio_file:
    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)
    st.audio(st.session_state.audio_file, format="audio/mp3")

    # 🎤 Ask for Next Decision
    st.info("🎤 What should happen next? Speak your decision.")
    audio_bytes = mic_recorder(start_prompt="🎤 Speak Decision" if lang == "en" else "🎤 Entscheidung sprechen")
    
    if audio_bytes is not None:
        user_decision = transcribe_audio(audio_bytes)
        if user_decision:
            st.success(f"✅ You said: {user_decision}")
            st.session_state.user_decision = user_decision
            st.rerun()

# 🔄 Generate Next Story Section
if st.session_state.user_decision:
    try:
        next_story_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Continue the children's story in {lang}, maintaining a fun, engaging tone. "
                                              f"Each section should be around 200 words long and lead to another open-ended decision point. "
                                              f"The decision should be implied by the story's events, rather than explicitly listing choices."},
                {"role": "user", "content": f"The story so far:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                                            f"The reader suggested: {st.session_state.user_decision}\n\n"
                                            f"Continue the story based on this input, keeping the storytelling immersive and natural."}
            ]
        )

        # Save new story section
        new_story = next_story_response.choices[0].message.content
        st.session_state.history.append(new_story)
        st.session_state.story = new_story

        # Convert to speech
        st.session_state.audio_file = text_to_speech(new_story)
        st.session_state.user_decision = None
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
