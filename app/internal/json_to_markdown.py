import json

def json_to_markdown(data, level=1):
    """
    Convert a Python dictionary/list (parsed JSON) into Markdown.

    Args:
        data: dict, list, or primitive value
        level: Heading level (used internally)

    Returns:
        Markdown string.
    """
    md = []

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                md.append(f'{"#" * level} {key}')
                md.append("")
                md.append(json_to_markdown(value, level + 1))
            else:
                md.append(f"- **{key}:** {value}")

    elif isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, (dict, list)):
                md.append(f'{"#" * level} Item {i}')
                md.append("")
                md.append(json_to_markdown(item, level + 1))
            else:
                md.append(f"- {item}")

    else:
        md.append(str(data))

    return "\n".join(md)


# Example usage
if __name__ == "__main__":
    json_data = {
        "title": "Example",
        "author": "John Doe",
        "tags": ["python", "markdown", "json"],
        "metadata": {
            "created": "2026-06-28",
            "version": 1.0
        },
        "sections": [
            {
                "name": "Introduction",
                "pages": 2
            },
            {
                "name": "Conclusion",
                "pages": 1
            }
        ]
    }

    markdown = json_to_markdown(json_data)
    print(markdown)