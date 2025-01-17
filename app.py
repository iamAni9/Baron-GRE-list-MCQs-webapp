import streamlit as st
import pandas as pd
import os
import json
# from dotenv import load_dotenv

# load_dotenv()
groq_api = os.getenv("GROQ_API_KEY")

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

llm = ChatGroq(groq_api_key=groq_api, model_name="llama-3.3-70b-versatile")

# App UI
st.title("Baron Sheet MCQ Practice")
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
        You are assisting me in learning vocabulary by creating multiple-choice questions. Follow these instructions carefully:

        1. **Word and Meaning**:
            - Word: {word}
            - Meaning: {meaning}

        2. **Question**: 
            - Create a creative and clear question that shows and highlight the word and asks for the meaning of the word.
            - Also highlight the {word} you are using in question within inverted commas.
        3. **Options**:
            - Provide four options: one correct answer and three plausible incorrect answers.
            - Ensure the incorrect options are related but clearly incorrect.

        4. **Correct Option**:
            - Randomize the placement of the correct option among A, B, C, D to avoid patterns. 
            - Do not repeat the same position everytime. Previous position = {prev_pos}
            - Clearly indicate which option is correct.

        5. **Example Output Format**: Provide the question and options in the following JSON structure:
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
        lines = result.split("\n")
        # print(lines)
        # Remove empty lines and trim whitespace
        lines = [line.strip() for line in lines if line.strip()]

        # Extract JSON block
        json_start = lines.index("```") + 1
        json_end = lines.index("```", json_start)
        json_block = "\n".join(lines[json_start:json_end])

        # Parse the JSON
        data = json.loads(json_block)

        # Extract question, options, and correct option
        question = data.get("question", "").strip()
        options = data.get("options", {})
        correct_option = data.get("correct_option", "").strip()
        # print(correct_option)

        # Update the session state
        st.session_state['question'] = question
        st.session_state['options'] = [f"{key}) {value}" for key, value in options.items()]
        st.session_state['correct_option'] = correct_option
    except Exception as e:
        st.error(f"Error generating question: {e}")

# Generate question on load or when 'Next Question' is clicked
if st.button("Next Question") or st.session_state['question'] is None:
    generate_question()

# Display question and options
if st.session_state['question']:
    st.write(f"{st.session_state['cnt']}. {st.session_state['question']}")
    user_choice = st.radio("Options", st.session_state['options'], key="user_choice")
    print(f"User Choice = {user_choice}")
    if st.button("Submit"):
        st.session_state['cnt'] += 1
        if st.session_state['correct_option']+')' in user_choice:
            st.success("Correct!")
        else:
            st.error(f"Incorrect. The correct answer is: {st.session_state['correct_option']}")