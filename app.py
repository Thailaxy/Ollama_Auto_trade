# Import necessary libraries
import streamlit as st
import ollama

# Function to chat with the local Ollama model
def main():
    # Get user input
    model_name = st.sidebar.selectbox('Model Name', ['llama3.1:8b'])
    prompt = st.text_area('System Prompt')
    clear_chat_button = st.button('Clear Chat')

    if clear_chat_button:
        st.session_state['chat_history'] = []

    chat_input = st.chat_input()
    chat_message = st.chat_message()

    # Generate text using the Ollama model
    def generate_text():
        response = ollama.chat(model_name, prompt)
        return response

    # Display the generated text
    if st.button('Generate Text'):
        response = generate_text()
        st.write('Generated Text: ' + str(response))

    # Store chat history in session state
    st.session_state['chat_history'].append(chat_input)

# Main function
if __name__ == '__main__':
    main()
