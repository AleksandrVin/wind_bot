"""
LLM integration for the wind sports Telegram bot using LangChain.
"""
import logging
import os
from typing import List

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI

from config import settings, Language
from infrastructure.llm.tools import WindSpeedToKnotsTool, WindSpeedToMSTool, GetCurrentWeatherTool
from infrastructure.weather.openweather_service import OpenWeatherService

logger = logging.getLogger(__name__)


class LangChainService:
    """Service for LLM integration using LangChain"""
    
    def __init__(self):
        """Initialize the LLM service"""
        # Set up LangSmith tracing if enabled
        if settings.LANGSMITH_TRACING:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGSMITH_ENDPOINT
            os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
            os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        
        # Initialize OpenAI client
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=0.1
        )
        
        # Initialize tools
        weather_service = OpenWeatherService()
        self.tools = [
            WindSpeedToKnotsTool(),
            WindSpeedToMSTool(),
            GetCurrentWeatherTool(weather_service=weather_service)
        ]
        
        # Set up agent with memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content="{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent"""
        return """
        You are a helpful assistant for kitesurfing and windsurfing enthusiasts.
        
        You help users with information about current weather conditions, wind speed, and other relevant data for water sports.
        
        Important instructions:
        1. Wind speed is the most critical factor for kitesurfing and windsurfing.
        2. For kitesurfing, good wind speeds are usually between 12-25 knots.
        3. For windsurfing, good wind speeds are usually between 15-30 knots.
        4. Always provide both knots and m/s when talking about wind speed.
        5. Include location name and country in your responses when available.
        6. Be extremely concise and informative. Avoid asking follow-up questions in your responses.
        7. Respond directly with the information requested without preamble.
        8. Format your response in clear sections with bullet points to enhance readability.
        9. Present the core information first (wind speed, conditions) before any recommendations.
        
        You have tools available to get weather data and convert between wind speed units.
        Always use these tools when answering questions about weather or wind conditions.
        
        Do not make up information. If you don't know something, say so without apology or asking additional questions.
        """
    
    async def process_message(self, message: str, language: str = Language.ENGLISH) -> str:
        """Process a user message and return a response"""
        try:
            # If message is in Russian, translate to English for processing
            input_message = message
            needs_translation = language != Language.ENGLISH
            
            # Process the message
            response = await self.agent_executor.ainvoke({"input": input_message})
            output = response.get("output", "I'm sorry, I couldn't process your request.")
            
            # If language is not English, translate the response
            if needs_translation and language == Language.RUSSIAN:
                translation_prompt = f"Translate the following text to Russian, preserving formatting: {output}"
                translation_response = await self.llm.ainvoke([HumanMessage(content=translation_prompt)])
                return translation_response.content
            
            return output
        
        except Exception as e:
            logger.error(f"Error processing message with LLM: {e}")
            
            # Return a generic error message in the requested language
            if language == Language.RUSSIAN:
                return "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
            else:
                return "Sorry, there was an error processing your request. Please try again later."