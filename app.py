import streamlit as st
import openai
import locale

# OpenAI API-Schlüssel aus den Streamlit Secrets laden
openai.api_key = st.secrets["OPENAI_API_KEY"]

# 🌍 Automatische Sprachwahl basierend auf Systemsprache des Nutzers
user_locale = locale.getdefaultlocale()[0]
if user_locale and "de" in user_locale:
    lang = "de"
    title = "📖 Saga – Sei Teil der Geschichte"
    input_label = "🌟 Wähle ein Thema für deine Geschichte:"
    button_text = "Erstelle Geschichte"
    decision_prompt = "Was soll die Hauptfigur tun?"
else:
    lang = "en"
    title = "📖 Saga – Be Part of the Story"
    input_label = "🌟 Choose a topic for your story:"
    button_text = "Start Story"
    decision_prompt = "What should the main character do?"

# 🏗 Session State für Story & Entscheidungsoptionen
if "story" not in st.session_state:
    st.session_state.story = ""
if "options" not in st.session_state:
    st.session_state.options = []
if "history" not in st.session_state:
    st.session_state.history = []

# 🌟 UI-Titel & Eingabe für das Thema
st.title(title)
topic = st.text_input(input_label)

if topic and not st.session_state.story:
    try:
        # 🎭 GPT-4o Mini generiert den ersten Story-Abschnitt mit genau zwei Optionen
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Erzähle eine interaktive Kindergeschichte für 5-jährige Kinder "
                                              f"in {lang}. Jeder Abschnitt sollte etwa 300 Wörter lang sein "
                                              f"und mit einem offenen Entscheidungspunkt enden. Nutze eine einfache, "
                                              f"kindgerechte Sprache."},
                {"role": "user", "content": f"Erstelle eine Kindergeschichte über {topic}. "
                                            f"Die Geschichte sollte mit einem klaren Entscheidungspunkt enden, "
                                            f"bei dem die Hauptfigur zwei Optionen hat."}
            ]
        )

        story_response = response.choices[0].message.content
        st.session_state.history.append(story_response)
        st.session_state.story = story_response

        # 🎭 KI generiert zwei sinnvolle Entscheidungsoptionen
        next_response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"Basierend auf der Geschichte, gib exakt zwei sinnvolle Entscheidungsoptionen "
                                              f"für den Nutzer in {lang}. Diese Optionen sollten auf den Entscheidungspunkt "
                                              f"der Geschichte folgen. Schreibe nur die beiden Optionen, nichts anderes."},
                {"role": "user", "content": f"Die Geschichte endet an folgendem Entscheidungspunkt:\n\n{story_response}\n\n"
                                            f"Welche zwei sinnvollen Optionen hat die Hauptfigur jetzt?"}
            ]
        )

        st.session_state.options = next_response.choices[0].message.content.split("\n")

    except Exception as e:
        st.error(f"❌ Fehler: {str(e)}")

# 📖 Zeige die aktuelle Geschichte an
if st.session_state.story:
    st.write(st.session_state.story)

    # 🛤️ Falls Entscheidungsoptionen vorhanden sind, zeige sie als Buttons
    selected_option = None
    if len(st.session_state.options) == 2:
        st.subheader(decision_prompt)
        if st.button(st.session_state.options[0]):
            selected_option = st.session_state.options[0]
        if st.button(st.session_state.options[1]):
            selected_option = st.session_state.options[1]

    # ⏭️ Falls der Nutzer eine Entscheidung getroffen hat, geht die Geschichte weiter
    if selected_option:
        try:
            next_story_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Setze die Geschichte basierend auf der getroffenen Entscheidung fort "
                                                  f"in {lang}. Der nächste Abschnitt sollte wieder etwa 300 Wörter lang sein "
                                                  f"und mit einem offenen Entscheidungspunkt enden."},
                    {"role": "user", "content": f"Die bisherige Geschichte:\n\n{'\n\n'.join(st.session_state.history)}\n\n"
                                                f"Der Nutzer hat sich entschieden für: {selected_option}\n\n"
                                                f"Setze die Geschichte fort und gib am Ende genau zwei neue Entscheidungsoptionen."}
                ]
            )

            new_story_part = next_story_response.choices[0].message.content
            st.session_state.history.append(new_story_part)
            st.session_state.story = new_story_part

            # 🔁 Neue Entscheidungsoptionen generieren
            next_options_response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"Generiere exakt zwei neue Entscheidungsoptionen in {lang}, "
                                                  f"die logisch aus der Geschichte folgen."},
                    {"role": "user", "content": f"Die Geschichte endet an folgendem Punkt:\n\n{new_story_part}\n\n"
                                                f"Welche zwei sinnvollen Optionen gibt es jetzt für die Hauptfigur?"}
                ]
            )

            st.session_state.options = next_options_response.choices[0].message.content.split("\n")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Fehler: {str(e)}")
