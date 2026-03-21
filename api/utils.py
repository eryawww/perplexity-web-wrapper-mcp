import os
import json

logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../logs")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)


def extract_answer(res, file_name):
    """Extract answer from Perplexity API response.

    For deep research, also extracts the report title and research steps from the text field.
    """
    backend_uuid = res.get("backend_uuid", None)
    blocks = res.get("blocks", [])
    if not isinstance(blocks, list):
        print(f"Unexpected blocks format in {file_name}: {blocks}")
        return {"answer": None, "backend_uuid": backend_uuid}

    # Collect all answer blocks and prefer the longest one (deep research report vs summary)
    answer_blocks = []
    for block in blocks:
        intended_usage = block.get("intended_usage", "")
        if not intended_usage.startswith("ask_text"):
            continue
        answer_blocks.append(block)

    answer_blocks.sort(
        key=lambda b: len((b.get("markdown_block") or {}).get("answer", "") or ""),
        reverse=True,
    )

    result = {"answer": None, "backend_uuid": backend_uuid}

    for block in answer_blocks:
        markdown_block = block.get("markdown_block", {})
        if not isinstance(markdown_block, dict):
            continue

        progress = markdown_block.get("progress")
        if progress == "IN_PROGRESS":
            chunks = markdown_block.get("chunks", [])
            if not isinstance(chunks, list):
                continue
            result.update({"progress": progress, "answer": "".join(chunks)})
            break

        if progress == "DONE":
            result.update({"progress": progress, "answer": markdown_block.get("answer")})
            break

    # Extract deep research metadata from text steps
    text = res.get("text", [])
    if isinstance(text, list):
        for step in text:
            step_type = step.get("step_type")
            if step_type == "RESEARCH_ANSWER":
                content = step.get("content", {})
                result["report_title"] = content.get("title")
                result["report_url"] = content.get("url")

    # Extract web sources/references
    for block in blocks:
        if block.get("intended_usage") == "web_results":
            wrb = block.get("web_result_block", {})
            web_results = wrb.get("web_results", [])
            if web_results:
                result["sources"] = [
                    {"index": i + 1, "name": r.get("name", ""), "url": r.get("url", "")}
                    for i, r in enumerate(web_results)
                ]
            break

    return result


def save_resp(res, file_name):
    """Save response to file for logging/debugging."""
    try:
        with open(os.path.join(logs_dir, file_name), "w", encoding="utf-8") as f:
            json.dump(res, f, indent=2, ensure_ascii=False)
    except Exception:
        # Silently fail if we can't save
        pass
