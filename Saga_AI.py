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
# Generate the INITIAL story
# ─────────────────────────────────────────
# We only do this once: if there's a topic and no story yet, call text completions.
if topic and not st.session_state["story"]:
    with st.spinner("🪄 Creating your story..."):
        try:
            # We'll use text-davinci-003, which still works in openai>=1.0
            # We craft a prompt that instructs GPT to produce a ~200-word children's story
            # with an open-ended decision point.
            prompt = f"""You are a storyteller creating a fun, engaging children's story for a 5-year-old in {lang}.
The story should be around 200 words long and end with a natural, open-ended decision point where the main character must decide what to do next.
Write the story about this topic: {topic}.

Make sure it's playful, age-appropriate, and sets up a decision without limiting choices.
"""

            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=500,
                temperature=0.7
            )

            story_part = response["choices"][0]["text"].strip()
            st.session_state["story"] = story_part
            st.session_state["history"].append(story_part)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# ─────────────────────────────────────────
# Display the current story, if any
# ─────────────────────────────────────────
if st.session_state["story"]:
    st.markdown(
        f"<p style='font-size:18px;'>{st.session_state['story']}</p>",
        unsafe_allow_html=True
    )

    # ─────────────────────────────────────
    # User input for next decision
    # ─────────────────────────────────────
    user_decision = st.text_input(
        "💡 What should happen next? Enter your idea:" if lang == "en" else "💡 Was soll als Nächstes passieren? Gib deine Idee ein:"
    )

    # Button to continue the story
    if st.button("Continue Story" if lang == "en" else "Geschichte fortsetzen"):
        if user_decision.strip():
            with st.spinner("🪄 Continuing the story..."):
                try:
                    # We'll pass everything so far (the entire story) plus the user decision,
                    # then ask text-davinci-003 to continue about 200 words more.
                    # We keep a similar style and another open-ended decision point.
                    full_history = "\n\n".join(st.session_state["history"])
                    prompt_next = f"""You are continuing a children's story for a 5-year-old in {lang}.
Current story so far:
{full_history}

The reader suggests this next step: {user_decision}

Please continue the story in a fun, imaginative way for ~200 words, ending again on an open-ended decision point. Avoid limiting the reader to just one or two choices; keep it open-ended.
"""

                    next_response = openai.Completion.create(
                        model="text-davinci-003",
                        prompt=prompt_next,
                        max_tokens=700,  # a bit more tokens for continuation
                        temperature=0.7
                    )

                    next_section = next_response["choices"][0]["text"].strip()
                    st.session_state["story"] = next_section
                    st.session_state["history"].append(next_section)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            # Display the newly updated story
            st.markdown(
                f"<p style='font-size:18px;'>{st.session_state['story']}</p>",
                unsafe_allow_html=True
            )
