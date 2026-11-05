
import json
import logging

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    AIMessage,
)

from chat.prompts.system_prompt import SYSTEM_PROMPT
from chat.services.context_service import get_user_skin_context


load_dotenv()

logger = logging.getLogger(__name__)


def debug_messages(messages):

    print("\n========== TOKEN DEBUG ==========")

    for index, message in enumerate(messages):

        content = str(message.content)

        print({
            "index": index,
            "role": message.type,
            "characters": len(content),
            "preview": content[:100],
        })

    total_chars = sum(
        len(str(message.content))
        for message in messages
    )



model = ChatGroq(
    model="qwen/qwen3.8-27b",
    temperature=0,
    streaming=True,
)



def build_chat_messages(
    user,
    chat,
    current_message_id,
):

    context = get_user_skin_context(user)

    skin_context = json.dumps(
        context.get("skin_profile"),
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    products_context = json.dumps(
        context.get("products"),
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    routine_context = json.dumps(
        context.get("routine"),
        indent=2,
        ensure_ascii=False,
        default=str,
    )

    system_prompt = SYSTEM_PROMPT.format(
        skin_context=skin_context,
        products_context=products_context,
    )

    system_prompt += (
        "\n\nUSER'S LATEST SKINCARE ROUTINE:\n"
        + routine_context
    )

    messages = [
        SystemMessage(content=system_prompt)
    ]

    # Retrieve previous messages
    previous_messages = (
        chat.messages
        .exclude(id=current_message_id)
        .order_by("-created_at")[:6]
    )

    previous_messages = list(reversed(previous_messages))

    for message in previous_messages:

        if message.role == "user":
            messages.append(
                HumanMessage(content=message.content)
            )

        elif message.role == "assistant":
            messages.append(
                AIMessage(content=message.content)
            )

    current_message = chat.messages.get(
        id=current_message_id,
        role="user",
    )

    messages.append(
        HumanMessage(content=current_message.content)
    )

    return messages


def stream_ai_response(user, chat, current_message_id):

    messages = build_chat_messages(
        user=user,
        chat=chat,
        current_message_id=current_message_id,
    )
    debug_messages(messages)

    for chunk in model.stream(messages):

        content = chunk.content

        if isinstance(content, str) and content:
            yield content

