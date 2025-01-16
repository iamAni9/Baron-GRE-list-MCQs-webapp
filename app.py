import streamlit as st
import pandas as pd
import os
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

# Function to generate a question
def generate_question():
    try:
        word_row = current_list.sample(1).iloc[0]
        word, meaning = word_row['Word'], word_row['Meaning']
        prompt = f"""
        You are helping me to learn the vocabulary. For this you need to create a multiple-choice question based on the following word and its meaning:
        Word: {word}
        Meaning: {meaning}
        
        The question should ask for the meaning of the word. Provide:
        1. A question based on the word.
        2. Four options (one correct and three plausible incorrect options).
        3. Clearly indicate the correct option.
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
        question = lines[2].replace("1. ", "").strip()
        options = [
            line.replace("   ", "").strip()
            for line in lines[5:9]
        ]
        correct_option = lines[-1].replace("3. The correct option is: **", "").strip()

        # print(f"Q = {question}")
        # print(options)
        # print(correct_option)
        # Update the session state
        st.session_state['question'] = question
        st.session_state['options'] = options
        st.session_state['correct_option'] = correct_option
    except Exception as e:
        st.error(f"Error generating question: {e}")

# Generate question on load or when 'Next Question' is clicked
if st.button("Next Question") or st.session_state['question'] is None:
    generate_question()

# Display question and options
if st.session_state['question']:
    st.write(st.session_state['question'])
    user_choice = st.radio("Options", st.session_state['options'], key="user_choice")
    # print(f"User Choice = {user_choice}")
    if st.button("Submit"):
        if user_choice in st.session_state['correct_option']:
            st.success("Correct!")
        else:
            st.error(f"Incorrect. The correct answer is: {st.session_state['correct_option']}")