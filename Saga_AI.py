import streamlit as st
import openai
import locale

# Use a valid OpenAI model that you have access to:
MODEL_NAME = "gpt-3.5-turbo"
# If you do have GPT-4 access, you can switch to "gpt-4"

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
    st.session_state["story"] = None
if "history" not in st.session_state:
    st.session_state["history"] = []

# ─────────────────────────────────────────
# Title and Topic Input
# ─────────────────────────────────────────
st.title(
    "📖 Saga – Be Part of the Story" if lang == "en" else "📖 Saga – Sei Teil der Geschichte"
)

topic = st.text_input(
    "🌟 Choose a topic for your story:" if lang == "en" else "🌟 Wähle ein Thema für deine Geschichte:"
)

# ─────────────────────────────────────────
# Generate the INITIAL story (once)
# ─────────────────────────────────────────
if topic and not st.session_state["story"]:
    with st.spinner("🪄 Creating your story..."):
        try:
            # Use the new interface: openai.Chat.create()
            response = openai.Chat.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                            f"Each section should be ~200 words long. "
                            f"The story should flow naturally and end with an open-ended decision point."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Write a children's story about {topic}, ~200 words, "
                            f"ending at a natural decision point where the character must decide what to do next."
                        )
                    }
                ]
            )

            # Extract the generated content
            story_part = response.choices[0].message.content
            st.session_state["story"] = story_part
            st.session_state["history"].append(story_part)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ─────────────────────────────────────────
# Show the story if we have one
# ─────────────────────────────────────────
if st.session_state["story"]:
    # Display current story content
    st.markdown(
        f"<p style='font-size:18px;'>{st.session_state['story']}</p>",
        unsafe_allow_html=True
    )

    # ─────────────────────────────────────
    # Let the user decide what happens next
    # ─────────────────────────────────────
    user_decision = st.text_input(
        "💡 What should happen next? Enter your idea:" if lang == "en" else "💡 Was soll als Nächstes passieren? Gib deine Idee ein:"
    )

    # Button to continue the story
    if st.button("Continue Story" if lang == "en" else "Geschichte fortsetzen"):
        if user_decision.strip():
            with st.spinner("🪄 Continuing the story..."):
                try:
                    next_response = openai.Chat.create(
                        model=MODEL_NAME,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    f"Continue this children's story in {lang}, ~200 words, "
                                    f"ending on a new open-ended decision point."
                                )
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"The story so far:\n\n{'\n\n'.join(st.session_state['history'])}\n\n"
                                    f"The reader suggested: {user_decision}\n\n"
                                    f"Continue the story in a fun, immersive way."
                                )
                            }
                        ]
                    )

                    # Extract the new story content
                    next_section = next_response.choices[0].message.content
                    st.session_state["story"] = next_section
                    st.session_state["history"].append(next_section)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            # After the spinner, the new story is in session_state["story"],
            # so we can display it directly in the same run:
            st.markdown(
                f"<p style='font-size:18px;'>{st.session_state['story']}</p>",
                unsafe_allow_html=True
            )
