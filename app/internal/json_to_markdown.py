import json

SKIP_KEYS = {
    # Truly internal / meaningless IDs
    "node_id", "database_id",

    # Avatar / gravatar (never useful in text output)
    "avatar_url", "gravatar_id",

    # Redundant API URL templates (contain placeholders like {/sha}, not real links)
    # Note: html_url is intentionally kept — it's the human-facing browser link.
    # Note: clone_url is skipped for now (only useful on repo objects, noise elsewhere).
    "archive_url", "assignees_url", "blobs_url", "branches_url", "clone_url", "collaborators_url",
    "comments_url", "commits_url", "compare_url", "contents_url", "contributors_url",
    "deployments_url", "downloads_url", "events_url", "forks_url", "git_commits_url",
    "git_refs_url", "git_tags_url", "hooks_url", "issue_comment_url", "issue_events_url",
    "issues_url", "keys_url", "labels_url", "languages_url", "merges_url", "milestones_url",
    "notifications_url", "pulls_url", "releases_url", "statuses_url", "subscribers_url",
    "subscription_url", "tags_url", "teams_url", "trees_url",

    # User profile API URLs (not useful in output)
    "followers_url", "following_url", "gists_url", "organizations_url",
    "received_events_url", "repos_url", "starred_url", "subscriptions_url",

    # GitHub App noise
    "performed_via_github_app",
}

MAX_DEPTH = 5
MAX_ITEMS = 50
MAX_STRING = 20000

def _get_item_name(list_name):
    if not list_name:
        return "Item"
    name = str(list_name).capitalize()
    if name.endswith("s") and not name.endswith("ss"):
        name = name[:-1]
    return name

def json_to_markdown(data, level=1, list_name="Item"):
    """
    Convert a Python dictionary/list (parsed JSON) into Markdown.
    """
    if level > MAX_DEPTH:
        return "*Nested object omitted (depth limit reached)*"

    md = []

    if isinstance(data, dict):
        for key, value in data.items():
            # Skip empty values
            if value in (None, "", [], {}):
                continue

            # Skip noisy fields
            if key in SKIP_KEYS:
                continue

            # Truncate large strings
            if isinstance(value, str) and len(value) > MAX_STRING:
                value = value[:MAX_STRING] + "\n\n... (truncated)"

            if isinstance(value, (dict, list)):
                nested_md = json_to_markdown(value, level + 1, list_name=key)
                if nested_md.strip():
                    md.append(f'{"#" * level} {key}')
                    md.append("")
                    md.append(nested_md)
            else:
                md.append(f"- **{key}:** {value}")

    elif isinstance(data, list):
        item_name = _get_item_name(list_name)
        total_items = len(data)
        for i, item in enumerate(data[:MAX_ITEMS], 1):
            # Skip empty values
            if item in (None, "", [], {}):
                continue

            # Truncate large strings
            if isinstance(item, str) and len(item) > MAX_STRING:
                item = item[:MAX_STRING] + "\n\n... (truncated)"

            if isinstance(item, (dict, list)):
                nested_md = json_to_markdown(item, level + 1, list_name=item_name)
                if nested_md.strip():
                    md.append(f'{"#" * level} {item_name} {i}/{total_items}')
                    md.append("")
                    md.append(nested_md)
            else:
                md.append(f"- {item}")

        if total_items > MAX_ITEMS:
            md.append(f"- *... {total_items - MAX_ITEMS} more items omitted ...*")

    else:
        if data in (None, "", [], {}):
            return ""
        if isinstance(data, str) and len(data) > MAX_STRING:
            data = data[:MAX_STRING] + "\n\n... (truncated)"
        md.append(str(data))

    return "\n".join(md)