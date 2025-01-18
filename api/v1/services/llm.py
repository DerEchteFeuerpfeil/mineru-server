import os
import logging
import base64
import json
from typing import Dict, List, Optional, Union, Tuple, Any

from openai import OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

SYSTEM_PROMPT = """I need you to help me in correcting mistakes made from my OCR system. I will provide you with an image of a document and the output of my OCR system as a JSON and you should correct this output according to your expertise. The OCR system outputs the detected text and the text level, which is another term for header level. The absence of the key "text_level" in the JSON objects indicates that this is regular text. A text level of 1 means that this is a top level headline, so it basically refers to the number of hashtags in a markdown file.

Here are some extra data cleaning rules the client wishes:
@@CUSTOM_INSTRUCTION@@

Please correct the text and the text level where necessary, potentially also adding or removing the key altogether. Output only the new list of JSON objects, no further explanation. Output them in JSON mode.
"""
USER_PROMPT = """Here is the current OCR result:

```
@@CONTENT_JSON@@
```
"""

# Content list json example
# [
#     {
#         "type": "text",
#         "text": "Wahlprogramm X zur Bundestagswahl 2025 ",
#         "text_level": 1,
#         "page_idx": 0
#     },
#     {
#         "type": "text",
#         "text": "Dieser Entwurf wurde am 2. Januar 2025 vom Parteivorstand beschlossen und wird in finaler Fassung am 12. Januar auf dem Bundesparteitag in X verabschiedet. ",
#         "page_idx": 0
#     },
#     {
#         "type": "text",
#         "text": "Präambel ",
#         "text_level": 1,
#         "page_idx": 0
#     }
# ]

GEMINI_JSON_ADDON = """Use this JSON schema:
Content = {'type' : str, 'text' : str, 'text_level' : int, 'page_idx' : int}
Return: list[Content]
"""

logger = logging.getLogger("__main__." + __name__)


def handle_openai_response(response: ChatCompletion) -> Dict[str, Any]:
    # Check if the conversation was too long for the context window, resulting in incomplete JSON
    if response.choices[0].message.finish_reason == "length":
        raise ValueError(
            "The conversation was too long for the context window, resulting in incomplete JSON"
        )

    # Check if the OpenAI safety system refused the request and generated a refusal instead
    if response.choices[0].message[0].get("refusal"):
        # your code should handle this error case
        raise ValueError(
            "OpenAI request resulted in safety refusal: "
            + response.choices[0].message[0]["refusal"]
        )

    # Check if the model's output included restricted content, so the generation of JSON was halted and may be partial
    if response.choices[0].message.finish_reason == "content_filter":
        raise ValueError("OpenAI content filter halted JSON generation")

    if response.choices[0].message.finish_reason == "stop":
        # In this case the model has either successfully finished generating the JSON object according to your schema, or the model generated one of the tokens you provided as a "stop token"
        result = response.choices[0].message[0].content
        try:
            return json.loads(result)
        except json.JSONDecodeError as e:
            logger.error(f"OpenAI generated invalid JSON {type(result)}: " + str(e))
            raise ValueError("OpenAI generated invalid JSON: " + str(e))


def post_process_with_llm(
    content_list_json: Dict[str, Any],
    b64_page_screenshot: str,
    vendor: str,
    detail: str = "low",
    custom_instruction: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Uses Gemini or OpenAI to post-process the MinerU detected output as there might be OCR errors or incorrect headings.
    Also allows for customizations in the prompt, e.g. if you want to remove leading line numbers from the text or if you want to inject prior knowledge about the layout into the process.

    Models are currently hard-coded to be "gpt-4o" for OpenAI and "gemini-1.5-flash" for Google.

    Args:
        content_list_json: The JSON object containing the OCR output
        b64_page_screenshot: The base64 encoded JPEG image of the page, must be utf-8 decoded base64 string
        vendor: The vendor to use, either "openai" or "google"
        detail: The detail level of the image, either "low" or "high"
        custom_instruction: Custom instruction to be added to the prompt, e.g. for removing heading numbers
    """

    user_prompt = USER_PROMPT.replace("@@CONTENT_JSON@@", content_list_json)
    system_prompt = SYSTEM_PROMPT.replace("@@CUSTOM_INSTRUCTION@@", custom_instruction)

    if vendor == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            logger.error("OpenAI API key not found")
            raise ValueError("OpenAI API key not found")

        client = OpenAI(api_key=api_key, timeout=20.0, max_retries=3)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_page_screenshot}",
                                "detail": detail,
                            },
                        },
                    ],
                },
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )

        return handle_openai_response(response)
    elif vendor == "google":
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key is None:
            logger.error("Google API key not found")
            raise ValueError("Google API key not found")

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        gemini_prompt = system_prompt + "\n" + GEMINI_JSON_ADDON + "\n" + user_prompt
        response = model.generate_content(
            [
                {
                    "mime_type": "image/jpeg",
                    "data": b64_page_screenshot,
                },
                gemini_prompt,
            ]
        )
        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Google generated invalid JSON {response.text}: " + str(e))
            raise ValueError("Google generated invalid JSON: " + str(e))
    else:
        logger.error(f"Tried to post process with unsupported vendor {vendor}")
        raise ValueError(f"Vendor {vendor} not supported")
