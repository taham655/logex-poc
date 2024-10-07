from typing import Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
from datetime import datetime
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AnyMessage
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph, START
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]
    contact_id: Optional[str]

class ProductionAgent:
    def __init__(self, tools: List[BaseTool], model_name: str = "gpt-4o"):
        self.tools = tools
        # Use Streamlit secrets for the OpenAI API key
        openai_api_key = st.secrets["OPENAI_API_KEY"]
        self.llm = ChatOpenAI(model=model_name, temperature=0, api_key=openai_api_key)
        self.graph = self._build_graph()

    def _build_graph(self) -> Runnable:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                                """You are an Bob a Customer Service Representative for Logex, a leading logistics company. Your primary function is to assist customers with their shipping and delivery inquiries. Always provide concise, accurate information and use the available tools to retrieve real-time data when necessary.
                Key responsibilities:

                - Order tracking: Use the track_order tool to provide up-to-date information on package locations and estimated delivery times.
                - Shipping cost estimation: Utilize the calculate_shipping_cost tool to give customers accurate price quotes based on package dimensions and weight.
                - Delivery time estimation: Employ the estimate_delivery_time tool to provide customers with expected delivery dates for their orders.
                - Address validation: Use the validate_address tool to ensure customer-provided addresses are correct and suggest corrections if needed.

                Important guidelines:

                - Always use the appropriate tool to retrieve accurate, real-time information for customers.
                - Provide clear, step-by-step instructions when guiding customers through processes like scheduling a pickup or filing a claim.
                - If unable to find information using the available tools, politely inform the customer and offer to escalate the query to a human representative.
                - Maintain a professional and friendly tone in all interactions.
                - Do not make promises or guarantees about delivery times or costs without using the relevant tools.
                - Protect customer privacy by never sharing personal or order information with unauthorized parties.

                Remember to greet customers warmly and focus on efficiently resolving their logistics-related queries using the tools at your disposal. Good luck!"""   
                "\nCurrent time: {time}."
                "\nContact ID: {contact_id}"
            ),
            ("placeholder", "{messages}"),
        ]).partial(time=lambda: datetime.now().isoformat())

        assistant_runnable = prompt | self.llm.bind_tools(self.tools)

        builder = StateGraph(State)
        builder.add_node("assistant", self._create_assistant_node(assistant_runnable))
        builder.add_node("tools", self._create_tool_node())
        
        builder.set_entry_point("assistant")
        builder.add_conditional_edges(
            "assistant",
            tools_condition,
        )
        builder.add_edge("tools", "assistant")

        return builder.compile()

    def _create_assistant_node(self, runnable: Runnable):
        async def assistant(state: State) -> Dict[str, Any]:
            while True:
                result = await runnable.ainvoke({**state, "contact_id": state.get("contact_id", "Unknown")})
                if not result.tool_calls and (not result.content or (isinstance(result.content, list) and not result.content[0].get("text"))):
                    state["messages"].append(HumanMessage(content="Respond with a real output."))
                else:
                    break
            return {"messages": state["messages"] + [result], "contact_id": state.get("contact_id")}
        return assistant

    def _create_tool_node(self):
        return ToolNode(tools=self.tools)

    async def process_query(self, past_messages: List[AnyMessage], query: str, contact_id: Optional[str] = None) -> str:
        initial_state = {"messages": past_messages + [HumanMessage(content=query)], "contact_id": contact_id}
        result = await self.graph.ainvoke(initial_state)
        return result['messages'][-1].content