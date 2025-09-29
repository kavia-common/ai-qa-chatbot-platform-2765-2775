import os
import re
import random
from typing import Dict, Tuple

# LangChain and OpenAI integrations
try:
    from langchain_openai import ChatOpenAI  # modern LangChain OpenAI chat model
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
except Exception:  # pragma: no cover - avoid failing if not installed yet in CI discovery
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None


class MCPWeatherClient:
    """
    Simulated MCP server client for weather Q&A.
    No external calls are made; it returns consistent pseudo forecasts based on input.
    """

    # PUBLIC_INTERFACE
    def get_forecast(self, location: str, when: str) -> Dict[str, str]:
        """
        Simulate forecast retrieval.
        - location: city or region name string
        - when: a simple time reference like 'today', 'tomorrow', 'on Friday', '2025-09-01'
        Returns a dict with summary and temp range strings.
        """
        # Deterministic seed for repeatability by location+when
        seed = hash((location.lower().strip(), when.lower().strip())) % (2**32)
        rng = random.Random(seed)

        conditions = [
            "sunny", "partly cloudy", "overcast", "light rain",
            "scattered showers", "thunderstorms", "breezy", "humid", "dry", "drizzle"
        ]
        highs = rng.randint(15, 35)
        lows = max(5, highs - rng.randint(5, 12))
        condition = rng.choice(conditions)

        return {
            "location": location.title(),
            "when": when,
            "summary": f"{condition}",
            "temperature": f"High {highs}°C / Low {lows}°C",
            "advice": rng.choice([
                "Carry a light jacket.",
                "Sunscreen recommended.",
                "Pack an umbrella just in case.",
                "Hydrate well.",
                "Good day for a walk.",
            ]),
        }


def extract_location_and_when(text: str) -> Tuple[str, str]:
    """
    Very light heuristic extraction to find a city-like token and time reference.
    This is only to support the simulation; not robust NLP.
    """
    # naive "in <word>" pattern
    loc_match = re.search(r"(?:in|at)\s+([A-Za-z][A-Za-z\s\-]{1,40})", text, re.IGNORECASE)
    location = loc_match.group(1).strip() if loc_match else "your area"

    # time references
    time_keywords = ["today", "tomorrow", "tonight", "this weekend", "this week", "next week"]
    when = "today"
    for kw in time_keywords:
        if re.search(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE):
            when = kw
            break
    # ISO-like date detection
    date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    if date_match:
        when = date_match.group(1)

    return location, when


class WeatherQnAEngine:
    """
    Orchestrates LangChain + OpenAI and simulated MCP weather retrieval.
    """

    def __init__(self):
        self.mcp = MCPWeatherClient()
        # Configure OpenAI model if available and key present
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.use_llm = bool(self.openai_api_key and ChatOpenAI is not None)

        if self.use_llm:
            # Initialize chat model
            self.llm = ChatOpenAI(model=self.model_name, temperature=0.2, api_key=self.openai_api_key)
        else:
            self.llm = None

    # PUBLIC_INTERFACE
    def answer(self, user_question: str) -> str:
        """
        Generate an answer for a weather question using:
        1) Simple heuristic extraction to call the MCP weather client
        2) Optionally use LLM to compose a natural answer around simulated data
        Returns final assistant message text.
        """
        location, when = extract_location_and_when(user_question)
        forecast = self.mcp.get_forecast(location, when)

        # Compose a base answer
        base = (
            f"Weather forecast for {forecast['location']} ({forecast['when']}): "
            f"{forecast['summary']}. Temperatures around {forecast['temperature']}. "
            f"{forecast['advice']}"
        )

        if not self.use_llm:
            # No OpenAI available; return deterministic text.
            return base

        # If LLM is configured, enhance the response for more natural style
        system_prompt = (
            "You are a helpful weather assistant. You have access to a trusted internal "
            "weather tool (MCP) that returns simulated but consistent forecasts. "
            "Use the provided tool output to craft a concise, clear answer."
        )
        user_content = (
            f"User question: {user_question}\n"
            f"Tool data (simulated MCP): {forecast}\n"
            f"Write a friendly, 2-3 sentence answer. Keep it factual and avoid mentioning that it's simulated."
        )
        try:
            messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]
            resp = self.llm.invoke(messages)
            text = getattr(resp, "content", None)
            if isinstance(text, str) and text.strip():
                return text.strip()
        except Exception:
            # Fallback to base on any LLM failure
            pass

        return base
