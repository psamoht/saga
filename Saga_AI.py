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
# We only need to store the story and history.
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
# If the user provided a topic AND we have no story yet, call OpenAI inside a spinner.
if topic and not st.session_state["story"]:
    with st.spinner("🪄 Creating your story..."):
        try:
            # Replace "gpt-4o-mini" with "gpt-3.5-turbo" or another valid model if needed
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                            f"Each section should be around 200 words. "
                            f"The story should flow naturally and lead to a decision point where the main character "
                            f"needs to decide what to do next, open-endedly."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Write a children's story about {topic}, about 200 words, "
                            f"ending at a natural decision point."
                        )
                    }
                ]
            )

            story = response.choices[0].message.content
            st.session_state["story"] = story
            st.session_state["history"].append(story)

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
                    next_response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    f"Continue the children's story in {lang}, maintaining a fun, engaging tone. "
                                    f"Each section ~200 words, ending at another open-ended decision point."
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

                    next_section = next_response.choices[0].message.content
                    # Update session state
                    st.session_state["story"] = next_section
                    st.session_state["history"].append(next_section)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            # After the spinner, re-display the new story (no re-run needed, it all happens in one script pass)
            st.markdown(
                f"<p style='font-size:18px;'>{st.session_state['story']}</p>",
                unsafe_allow_html=True
            )
