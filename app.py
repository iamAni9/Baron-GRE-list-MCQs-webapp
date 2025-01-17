import streamlit as st
import pandas as pd
import os
import json
# from dotenv import load_dotenv

# load_dotenv()
groq_api = os.getenv("GROQ_API_KEY")

st.sidebar.title("Model Selection")
available_models = ["llama-3.3-70b-versatile", "llama-3.2-1b-preview", "llama-3.2-3b-preview", "llama-3.1-70b-versatile", "llama3-70b-8192", "llama3-8b-8192"]
selected_model = st.sidebar.selectbox("Select Model", options=available_models)

# Load word lists
@st.cache_data
def load_word_lists():
    files = {'A': 'word_lists/A.csv', 'B': 'word_lists/B.csv', 'C': 'word_lists/C.csv',
             'D': 'word_lists/D.csv', 'E': 'word_lists/E.csv', 'F': 'word_lists/F.csv',
             'G': 'word_lists/G.csv', 'H': 'word_lists/H.csv', 'I': 'word_lists/I.csv',
             'J': 'word_lists/J.csv', 'K': 'word_lists/K.csv', 'L': 'word_lists/L.csv',
             'M': 'word_lists/M.csv', 'N': 'word_lists/N.csv', 'O': 'word_lists/O.csv',
             'P': 'word_lists/P.csv', 'Q': 'word_lists/Q.csv', 'R': 'word_lists/R.csv',
             'S': 'word_lists/S.csv', 'T': 'word_lists/T.csv', 'U': 'word_lists/U.csv',
             'W': 'word_lists/W.csv', 'X': 'word_lists/X.csv', 'Y': 'word_lists/Y.csv', 
             'Z': 'word_lists/Z.csv'}  
    word_lists = {k: pd.read_csv(v) for k, v in files.items()}
    all_words = pd.concat(word_lists.values(), ignore_index=True)
    word_lists['ALL'] = all_words
    return word_lists

word_lists = load_word_lists()

try:
    from langchain_groq import ChatGroq
except Exception as e:
    st.error(f"Import Error: {e}")

llm = ChatGroq(groq_api_key=groq_api, model_name=selected_model)

# App UI
st.title("Baron Sheet MCQ Practice")
st.caption(f"Current model: {selected_model}")
if "list_choice" not in st.session_state:
    st.session_state["list_choice"] = "ALL"
list_choice = st.selectbox("Select Word List", options=list(word_lists.keys()))
current_list = word_lists[list_choice]

if 'question' not in st.session_state:
    st.session_state['question'] = None
    st.session_state['options'] = []
    st.session_state['correct_option'] = None
    st.session_state['cnt'] = 1

# Function to generate a question
def generate_question():
    try:
        word_row = current_list.sample(1).iloc[0]
        word, meaning = word_row['Word'], word_row['Meaning']
        prev_pos = st.session_state['correct_option']
        prompt = f"""
        You are creating vocabulary-based multiple-choice questions. Follow these steps:

        1. **Word and Meaning**:
            - Word: {word}
            - Meaning: {meaning}

        2. **Question**:
            - Write a creative question highlighting the word **{word}** and ask for its meaning.

        3. **Options**:
            - Provide four options: one correct and three plausible but incorrect.
            - Ensure the correct answer is randomized (not in position {prev_pos} again).

        4. **Example Output Format**: Provide the question and options in the following JSON structure and must follow this structure otherwise errors will occur:
            ```
            {{
                "question": "What does the word '{word}' mean?",
                "options": {{
                    "A": "option 1",
                    "B": "option 2",
                    "C": "option 3",
                    "D": "option 4"
                }},
                "correct_option": "B"
            }}
            ```
        """
        
        # Call Groq API
        response = llm.invoke(prompt)
        if not response:
            raise ValueError("No response from Groq API")
        
        result = response.content
        # print(result)
        if not result:
            raise ValueError("No 'content' field in the response")

        # Parse the content to extract the question, options, and correct answer
        lines = [line.strip() for line in result.split("\n") if line.strip()]
        # print(lines)

        json_block = None

        # If delimiters are found, extract JSON block using them
        if "```" in lines:
            try:
                json_start = lines.index("```") + 1
                json_end = lines.index("```", json_start)
                json_block = "\n".join(lines[json_start:json_end])
            except ValueError:
                raise ValueError("JSON block delimiters found, but block extraction failed.")
        else:
            # Fallback to detect JSON-like structures in the absence of delimiters
            try:
                json_start = next(i for i, line in enumerate(lines) if line.startswith("{"))
                json_end = next(i for i, line in enumerate(lines[json_start:], start=json_start) if line.endswith("}"))
                json_block = "\n".join(lines[json_start:json_end + 1])
            except StopIteration:
                raise ValueError("JSON block not found within the content.")

        # Sanitize and parse the JSON block
        sanitized_json = json_block.replace(",\n}", "\n}")  # Remove trailing commas before closing braces

        try:
            # Parse the sanitized JSON block
            data = json.loads(sanitized_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {e}")

        # Extract question, options, and correct option
        question = data.get("question", "").strip()
        options = data.get("options", {})
        correct_option = data.get("correct_option", "").strip()

        # print(f"question = {question}")
        # print(f"options = {options}")
        # print(f"correct = {correct_option}")
        # Update the session state
        st.session_state['question'] = question
        st.session_state['options'] = [f"{key}) {value}" for key, value in options.items()]
        st.session_state['correct_option'] = correct_option
    except Exception as e:
        st.error(f"Error generating question: {e}")

# Initialize session state for button text
if "button_text" not in st.session_state:
    st.session_state["button_text"] = "Start"

# Function to handle button click
def handle_button_click():
    if st.session_state["button_text"] == "Start":
        st.session_state["button_text"] = "Next Question"
    generate_question()

# Display the button with dynamic text
if st.button(st.session_state["button_text"]):
    handle_button_click()


# Display question and options
if st.session_state['question']:
    st.write(f"{st.session_state['cnt']}. {st.session_state['question']}")
    user_choice = st.radio("Options", st.session_state['options'], key="user_choice")
    # print(f"User Choice = {user_choice}")
    if st.button("Submit"):
        st.session_state['cnt'] += 1
        if st.session_state['correct_option']+')' in user_choice:
            st.success("Correct!")
        else:
            st.error(f"Incorrect. The correct answer is: {st.session_state['correct_option']}")