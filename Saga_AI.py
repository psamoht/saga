import streamlit as st
import openai
import locale

# OpenAI API Key
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Detect system language for default selection
user_locale = locale.getdefaultlocale()[0]
default_lang = "de" if user_locale and "de" in user_locale else "en"

# 🌐 Language Selection Dropdown
lang_options = {"English": "en", "Deutsch": "de"}
selected_lang = st.selectbox(
    "🌍 Select Language / Sprache wählen:",
    list(lang_options.keys()),
    index=0 if default_lang == "en" else 1
)
lang = lang_options[selected_lang]

# ─────────────────────────────────────────
# Session State Initialization
# ─────────────────────────────────────────
if "story" not in st.session_state:
    st.session_state.story = None
if "history" not in st.session_state:
    st.session_state.history = []
if "loading" not in st.session_state:
    st.session_state.loading = False
if "user_decision" not in st.session_state:
    st.session_state.user_decision = None
if "next_story" not in st.session_state:
    st.session_state.next_story = None
if "topic" not in st.session_state:
    st.session_state.topic = None

# 🎩 Loading GIF
loading_gif = (
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzlvam85OW9uZ2Zy"
    "MTNoaHdkYWd4a2JsaGR6bm1xeSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/"
    "LS3DxKAbJNkVCPDEn4/giphy.gif"
)

# ─────────────────────────────────────────
# STEP 1) Generate the INITIAL story if needed
# ─────────────────────────────────────────
if st.session_state.loading and st.session_state.story is None:
    try:
        # Use your custom model if you have it, otherwise "gpt-3.5-turbo" is common.
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # <-- Replace with "gpt-3.5-turbo" or "gpt-4" if needed
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                        f"Each section should be around 200 words long. "
                        f"The story should flow naturally and lead to a decision point where the main character "
                        f"needs to decide what to do next. This decision point should be obvious but not limited "
                        f"to two specific options. It should feel open-ended, allowing different choices from the reader."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a children's story about {st.session_state.topic}. "
                        f"Ensure that the story section is about 200 words long and ends at an open-ended decision point."
                    )
                }
            ]
        )

        st.session_state.story = response.choices[0].message.content
        st.session_state.history.append(st.session_state.story)
        st.session_state.loading = False
        st.experimental_rerun()

    except Exception as e:
        st.session_state.loading = False
        st.error(f"❌ Error: {str(e)}")
        st.stop()

# ─────────────────────────────────────────
# STEP 2) If still loading, show spinner
# ─────────────────────────────────────────
if st.session_state.loading:
    st.image(loading_gif, use_container_width=True)
    st.markdown(
        "<p style='text-align: center; font-size:18px;'>🪄 The story magic is happening...</p>",
        unsafe_allow_html=True
    )
    st.stop()

# ─────────────────────────────────────────
# STEP 3) Main UI
# ─────────────────────────────────────────
st.title(
    "📖 Saga – Be Part of the Story" if lang == "en" else "📖 Saga – Sei Teil der Geschichte"
)

topic = st.text_input(
    "🌟 Choose a topic for your story:" if lang == "en" else "🌟 Wähle ein Thema für deine Geschichte:"
)

# If user enters a topic, we have no story, and not currently loading -> load the story
if topic and st.session_state.story is None and not st.session_state.loading:
    st.session_state.topic = topic
    st.session_state.loading = True
    st.experimental_rerun()

# If we have a story, display it
if st.session_state.story:
    st.markdown(
        f"<p style='font-size:18px;'>{st.session_state.story}</p>",
        unsafe_allow_html=True
    )

    # ✍️ Decision input
    decision_input = st.text_input(
        "💡 What should happen next? Enter your idea:"
        if lang == "en"
        else "💡 Was soll als Nächstes passieren? Gib deine Idee ein:",
        key="decision_input_key"
    )

    # Button to continue
    if st.button("Continue Story" if lang == "en" else "Geschichte fortsetzen"):
        if decision_input.strip():
            st.session_state.user_decision = decision_input
            st.session_state.loading = True
            st.experimental_rerun()

# ─────────────────────────────────────────
# STEP 4) Generate the NEXT story section
# ─────────────────────────────────────────
if (
    st.session_state.loading
    and st.session_state.story
    and st.session_state.user_decision
):
    try:
        next_story_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # again, replace if needed
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Continue the children's story in {lang}, maintaining a fun, engaging tone. "
                        f"Each section should be around 200 words long and lead to another open-ended decision point. "
                        f"The decision should be implied by the story's events, rather than explicitly listing choices."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"The story so far:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                        f"The reader suggested: {st.session_state.user_decision}\n\n"
                        f"Continue the story based on this input, keeping the storytelling immersive and natural."
                    )
                }
            ]
        )

        # Save the new story section
        st.session_state.next_story = next_story_response.choices[0].message.content

        # Turn off loading, reset decision
        st.session_state.loading = False
        st.session_state.user_decision = None

        # Update displayed story and history
        st.session_state.story = st.session_state.next_story
        st.session_state.history.append(st.session_state.story)
        st.session_state.next_story = None

        st.experimental_rerun()

    except Exception as e:
        st.session_state.loading = False
        st.error(f"❌ Error: {str(e)}")
        st.stop()
