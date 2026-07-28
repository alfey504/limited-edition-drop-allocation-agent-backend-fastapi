import json

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

from app.db.models.message import Message, MessageRole


def to_langchain_messages(messages: list[Message]) -> list[BaseMessage]:
    """
    Converts stored conversation history into what the agent takes as input.
    Only USER/ASSISTANT are handled: we only ever persist one row per turn (the
    final response), never the intermediate tool-calling steps within a turn —
    so there's nothing stored under MessageRole.TOOL to convert (yet).
    """
    result: list[BaseMessage] = []
    for message in messages:
        if message.role == MessageRole.USER:
            result.append(HumanMessage(content=message.content))
        elif message.role == MessageRole.ASSISTANT:
            result.append(AIMessage(content=message.content))
        else:
            raise NotImplementedError(
                f"No conversion defined for stored message role {message.role!r}"
            )
    return result


def extract_final_response(state_messages: list[BaseMessage]) -> str:
    final = state_messages[-1]
    if not isinstance(final, AIMessage):
        raise ValueError(f"Expected the graph's final message to be an AIMessage, got {type(final)}")
    return final.content


def extract_report_filename(state_messages: list[BaseMessage]) -> str | None:
    """Finds the most recent generate_allocation_report_pdf result, if the agent called it."""
    for message in reversed(state_messages):
        if isinstance(message, ToolMessage) and message.name == "generate_allocation_report_pdf":
            try:
                return json.loads(message.content).get("filename")
            except (json.JSONDecodeError, AttributeError):
                return None
    return None
