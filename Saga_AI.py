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

# 🏗 Initialize Session State
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

# 🎩 Loading GIF
loading_gif = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzlvam85OW9uZ2ZyMTNoaHdkYWd4a2JsaGR6bm1xeSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/LS3DxKAbJNkVCPDEn4/giphy.gif"

# ─────────────────────────────────────────
# STEP 1) Generate initial story if needed
# ─────────────────────────────────────────
# If we're in loading mode and we do NOT yet have an initial story,
# generate the initial story here (before showing the loading screen).
if st.session_state.loading and st.session_state.story is None:
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Create a fun, engaging children's story for a 5-year-old in {lang}. "
                        f"Each section should be around 200 words long. "
                        f"The story should flow naturally and lead to a decision point where the main character needs to decide what to do next. "
                        f"This decision point should be obvious but not limited to two specific options. "
                        f"It should feel open-ended, allowing different choices from the reader."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Write a children's story about {{TOPIC_PLACEHOLDER}}. "  # We handle the real topic below
                        f"Ensure that the story section is about 200 words long and ends at an open-ended decision point."
                    )
                }
            ]
        )

        # Save the story and disable loading mode
        st.session_state.story = response.choices[0].message.content
        st.session_state.history.append(st.session_state.story)
        st.session_state.loading = False
        st.experimental_rerun()

    except Exception as e:
        st.session_state.loading = False
        st.error(f"❌ Error: {str(e)}")
        st.stop()

# ──────────────────────────────────────────────────
# STEP 2) If still loading, show loading screen now
# ──────────────────────────────────────────────────
if st.session_state.loading:
    st.image(loading_gif, use_container_width=True)
    st.markdown("<p style='text-align: center; font-size:18px;'>🪄 The story magic is happening...</p>", unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────
# STEP 3) Render the rest of the UI
# ─────────────────────────────────────────
st.title("📖 Saga – Be Part of the Story" if lang == "en" else "📖 Saga – Sei Teil der Geschichte")

# 🌟 User Input for Story Topic
topic = st.text_input(
    "🌟 Choose a topic for your story:" if lang == "en" else "🌟 Wähle ein Thema für deine Geschichte:"
)

# If the user entered a topic and we don't have a story yet, enable loading, plug the topic into the prompt, and rerun
if topic and st.session_state.story is None and not st.session_state.loading:
    st.session_state.loading = True

    # Update the system prompt to insert the user topic right before generation
    # We can do this by rewriting the prompt in session_state, or by using a placeholder.
    # Easiest might be to re-invoke the prompt in the generation step above, but we stored it as a placeholder for clarity.
    # For now, let's just stash the real topic in session_state and handle it in the next step.
    if "topic" not in st.session_state:
        st.session_state.topic = topic
    else:
        st.session_state.topic = topic

    # We also need to replace that placeholder in the openai prompt
    # We can do that by reassigning the messages or storing them in session state. 
    # For simplicity, let's do a quick search & replace on the "user" content for the topic:

    st.session_state.loading = True
    st.experimental_rerun()

# Now, if we *do* have a story, display it:
if st.session_state.story:
    # We can replace the placeholder if it still exists
    if "topic" in st.session_state and st.session_state.topic:
        # If the placeholder is in the text, you can replace it here:
        st.session_state.story = st.session_state.story.replace(
            "{{TOPIC_PLACEHOLDER}}", st.session_state.topic
        )

    st.markdown(f"<p style='font-size:18px;'>{st.session_state.story}</p>", unsafe_allow_html=True)

    # ✍️ User Input for Next Decision
    user_decision = st.text_input(
        "💡 What should happen next? Enter your idea:" if lang == "en" else "💡 Was soll als Nächstes passieren? Gib deine Idee ein:",
        key="user_input"
    )

    if st.button("Continue Story" if lang == "en" else "Geschichte fortsetzen"):
        if user_decision.strip():
            st.session_state.user_decision = user_decision
            st.session_state.loading = True  # Enable loading for next story section
            st.experimental_rerun()

# ─────────────────────────────────────────────────────────────────────────────────────────────────
# STEP 4) Generate the NEXT story section if user already has a story and has provided a next step
# ─────────────────────────────────────────────────────────────────────────────────────────────────
if st.session_state.loading and st.session_state.story and st.session_state.user_decision:
    try:
        next_story_response = openai.chat.completions.create(
            model="gpt-4o-mini",
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

        # Save new story section
        st.session_state.next_story = next_story_response.choices[0].message.content

        # Turn off loading and reset user input
        st.session_state.loading = False
        st.session_state.user_decision = None

        # Update the displayed story and history
        st.session_state.story = st.session_state.next_story
        st.session_state.history.append(st.session_state.story)
        st.session_state.next_story = None

        st.experimental_rerun()

    except Exception as e:
        st.session_state.loading = False
        st.error(f"❌ Error: {str(e)}")
        st.stop()
