from typing import Dict, Any, List

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


def content_list_to_md(content_list: List[Dict[str, Any]]) -> str:
    """
    Convert a list of content items to a Markdown string
    """
    curr_page = 1
    total_pages = content_list[-1]["page_idx"] + 1
    md = f"@@ Page 1/{str(total_pages)} @@\n\n"
    for item in content_list:
        if item["page_idx"] + 1 != curr_page:
            curr_page += 1
            md += f"@@ Page {str(curr_page)}/{str(total_pages)} @@\n\n"
        if item["type"] == "text":
            if "text_level" in item:
                md += "#" * item["text_level"] + " "
            md += item["text"] + "\n"
    return md
