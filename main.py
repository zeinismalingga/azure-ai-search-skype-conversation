import os
import streamlit as st
from openai import AzureOpenAI   
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

search_endpoint = st.secrets["AZURE_AI_SEARCH_ENDPOINT"]
search_api_key = st.secrets["AZURE_AI_SEARCH_API_KEY"]
index_name = st.secrets["AZURE_AI_SEARCH_INDEX"]

AZURE_COGNITIVE_SEARCH_CREDENTIAL = AzureKeyCredential(search_api_key)
search_client = SearchClient(endpoint=search_endpoint, index_name=index_name, credential=AZURE_COGNITIVE_SEARCH_CREDENTIAL)

# Runs a semantic query 
# results = search_client.search(
#     query_type="semantic",
#     search_text="Show messages where I sent or received invoices.",
#     query_language="en-us",
#     semantic_configuration_name="semantic-content",
#     top=5,
#     query_caption="extractive",
#     include_total_count=True,
# )

# combined_results = "\n".join([
#     f"Conversation Name: {result['conversation_name']}\nFrom: {result['from']}\nContent: {result['content']}\nTime: {result['time']}\n--------------------------------"
#     for result in results
# ])

# print(combined_results)

# Create a chat interface
st.title("Chat with your data")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history on app re-run
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Show messages where I sent or received invoices."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)                

    # Query Azure AI Search
    results = search_client.search(
        query_type="semantic",
        search_text=prompt,
        query_language="en-us",
        semantic_configuration_name="semantic-content",
        top=5,
        query_caption="extractive",
        include_total_count=True,
    )

    combined_results = "\n".join([
        f"Conversation Name: {result['conversation_name']}\nFrom: {result['from']}\nContent: {result['content']}\nTime: {result['time']}\n--------------------------------"
        for result in results
    ])

    # Call AzureOpenAI
    system_prompt = f"""
    You are a helpful assistant that can answer questions about the following Skype Conversation data:
    {combined_results}

    Return format:
    Conversation Name:
    From:
    Content:
    Time:
    """

    client = AzureOpenAI(
        azure_endpoint=st.secrets["AZURE_OPENAI_ENDPOINT"],
        api_version="2024-05-01-preview",
        api_key=st.secrets["AZURE_OPENAI_API_KEY"],
    )

    response = client.chat.completions.create(
        model=st.secrets["AZURE_OPENAI_DEPLOYMENT"],
        messages=[{"role": "user", "content": system_prompt}],
        temperature=0.7,
        max_tokens=1000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )
    

    # Add assistant response to chat history    
    st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
    st.chat_message("assistant").markdown(response.choices[0].message.content)