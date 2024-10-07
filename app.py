import streamlit as st
import asyncio
from typing import List
from langchain_core.messages import AIMessage, HumanMessage, AnyMessage
from tools import retrieve_company_information, track_order, estimate_delivery_time, calculate_shipping_cost, validate_address
from agent import ProductionAgent

# Initialize the agent
tools = [
    retrieve_company_information,
    track_order,
    estimate_delivery_time,
    calculate_shipping_cost,
    validate_address,
]
agent = ProductionAgent(tools)

st.title("Logex Customer Service Agent")

# Initialize an empty list to store chat messages
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Create buttons for quick order tracking above the query box
st.write("Quick Actions:")
col1, col2, col3 = st.columns(3)
if col1.button("Track Order ORD123456"):
    st.session_state.temp_query = "I would like to track my order: ORD123456"
if col2.button("Track Order ORD789012"):
    st.session_state.temp_query = "I would like to track my order: ORD789012"
if col3.button("Track Order ORD345678"):
    st.session_state.temp_query = "I would like to track my order: ORD345678"

# User input
prompt = st.chat_input("What is your question?")

# Use the temporary query if set, otherwise use the chat input
if 'temp_query' in st.session_state and st.session_state.temp_query:
    prompt = st.session_state.temp_query
    st.session_state.temp_query = None  # Clear the temporary query

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare past messages for the agent
    past_messages: List[AnyMessage] = [
        HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"])
        for msg in st.session_state.messages[:-1]  # Exclude the last message as it's the current prompt
    ]

    # Get AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            with st.spinner("Thinking..."):
                # Use asyncio.run to properly await the asynchronous process_query method
                response = asyncio.run(agent.process_query(past_messages, prompt, contact_id=1))
            message_placeholder.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            message_placeholder.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})

