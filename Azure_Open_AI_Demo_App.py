import streamlit as st
import openai
import os
import json
import requests
import openai
from azure.search.documents import SearchClient
import logging

logging.debug("This is a debug message")


openai.api_type = "azure"
openai.api_base = "https://dhopenai.openai.azure.com/"
openai.api_version = "2023-03-15-preview"

openai.api_key = os.environ.get("OpenAI_Key")
search_api_key = os.environ.get("Search_Admin_Key") #Cog search admin key

#Cognitive Search Connection
search_endpoint = "https://dhcogsearch.search.windows.net"
search_endpoint_for_creating_index = "https://dhcogsearch.search.windows.net/indexes/purview-index-no-embeddings/docs/search?api-version=2023-07-01-Preview"

def createSearchRequest(user_question):
#Create an embedding for the user question - skipped for now
    #response = openai.Embedding.create(
    #    input=user_question,
    #    engine="dh-embeddings-ada-002"
    #)
    #embeddings = response['data'][0]['embedding']

    #This is the search that will be sent to Azure Cog search in JSOn format
    search_json = {
        #"vector": {
        #    "value": embeddings,
        #    "fields": "contentVector, titleVector",
        #    "k": 2
        #},
        "search": f"{user_question}",
        "select": "title, content, path",
        "queryType": "semantic",
        "semanticConfiguration": "my-semantic-config",
        "queryLanguage": "en-us",
        "captions": "extractive",
        "answers": "extractive",
        "top": "2"
    }

  
    url = f'{search_endpoint_for_creating_index }'
    print("")
    print("URL is " + url)
    headers = {'Content-Type': 'application/json', 'api-key': search_api_key}

    #print("Search JSON is " + json.dumps(search_json))
    print("About to make the rest call")
    #print("data is" + str(search_json))
    response = requests.post(url , headers=headers, data=json.dumps(search_json))
    st.write('url is ', url)
    st.write('request is ', json.dumps(search_json))
    
    if response.status_code == 200:
        data = response.json()
        st.write("Azure Search call Succeeded") 
        #print(data)
    else:
        print('Error:', response.status_code)
        st.write("Azure Search call failed") 
        st.write(response.status_code)


    print("rest call completed") 

    array_length = len(data['value'])
    print("array length is " +str(array_length))
  

    azure_search_response = data['value'][0]['content']
    response_message = data['value'][0]['content']
    response_link = data['value'][0]['path']
    response_title = data['value'][0]['title']

    azure_search_response += data['value'][1]['content']
    print(azure_search_response)
    #response_message += data['value'][1]['content']
    #response_link += data['value'][1]['path']
    #response_title += data['value'][1]['title']

    addon_command = " Don't answer the question if you can't answer it using the text in the system message, just say 'I'm sorry, I don't have the answer to that question, can you please rephrase it?\" Don't say anything more after that."
    response = openai.ChatCompletion.create(
    engine="gpt-35-turbo-16k",
    messages = [{
            "role": "system",
            "content": f"You are an IT helpdesk bot. Try to answer the question based on the text that is given to you. Include all relevant information from the text. Text to look for an answer: {azure_search_response} "
        },
        {
            "role": "user",
            "content": user_question + addon_command
    }],
    temperature=0.2,
    max_tokens=8000,
    top_p=0.95,
    frequency_penalty=0,
    presence_penalty=0,
    stream=False,
    stop=None)


    #print(messages2)
    
    return response, response_message, response_title, response_link

st.title("🔎 Newmont Compliance Search")
st.write("<p style='text-align:center'>This app allows you to search the Newmont Mining compliance documenation", unsafe_allow_html=True)

with st.form("my_form"):
    input_message = st.text_input('Question')
    submitted = st.form_submit_button("Submit")
    if submitted:
        response, response_message, response_title, response_link = createSearchRequest(input_message)
        st.write(response['choices'][0]['message']['content'])
        response_content = response['choices'][0]['message']['content']
        #st.write(response_message)
        substring = "I'm sorry"
        if substring not in str(response_content):
            st.write("Source: <a href=" + response_link+ "> " +response_title +" </a>", unsafe_allow_html=True)

        #st.write(response_link)
