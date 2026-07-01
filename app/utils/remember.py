import logging
import cognee

logger = logging.getLogger(__name__)


async def add_to_cognee(content: str, *, dataset: str | None = None) -> None:
    """
    Stage one piece of content into cognee's buffer.

    This is a lightweight call — it does NOT trigger any Ollama / LLM work.
    Call cognify() once after all items are staged to do the actual processing.

    Args:
        content: Text to stage.
        dataset: Optional dataset/collection name.
    """
    preview = content[:120].replace("\n", " ")
    logger.debug(
        "[add_to_cognee] Staging %d chars into dataset=%r | preview: %s…",
        len(content), dataset, preview,
    )

    kwargs: dict = {}
    if dataset is not None:
        kwargs["dataset_name"] = dataset

    try:
        await cognee.add(content, **kwargs)
    except Exception as exc:
        logger.error(
            "[add_to_cognee] cognee.add() failed for dataset=%r — %s: %s",
            dataset, type(exc).__name__, exc,
        )
        raise


async def run_cognify(dataset: str | None = None) -> None:
    """
    Trigger the single Ollama/LLM processing pass over everything staged so far.

    Call this ONCE after all cognee.add() calls are done — this is what
    actually hits Ollama and builds the knowledge graph.

    Args:
        dataset: Optional dataset scope.
    """
    logger.info("[run_cognify] Starting cognee.cognify() for dataset=%r …", dataset)

    kwargs: dict = {}
    if dataset is not None:
        kwargs["datasets"] = [dataset]

    kwargs.setdefault("data_per_batch", 1)
    kwargs.setdefault("chunks_per_batch", 1)

    try:
        result = await cognee.cognify(**kwargs)

        logger.info(
            "[run_cognify] cognee.cognify() finished for dataset=%r",
            dataset,
        )

        return result

    except Exception as exc:
        logger.error(
            "[run_cognify] cognee.cognify() failed for dataset=%r — %s: %s",
            dataset,
            type(exc).__name__,
            exc,
        )
        raise


async def recall_data(query_text: str, datasets: list[str], top_k: int = 5):
    """
    Recall insights from cognee based on a natural language query.
    """
    logger.info(
        "[recall_data] Querying cognee for %r in datasets=%r (top_k=%d)", 
        query_text, datasets, top_k
    )
    try:
        # Assuming we can pass top_k or slice the results later
        results = await cognee.search(
            query_type="INSIGHTS", 
            query_text=query_text, 
            datasets=datasets
        )
        return results[:top_k] if isinstance(results, list) else results
    except Exception as exc:
        logger.error("[recall_data] cognee.search() failed - %s: %s", type(exc).__name__, exc)
        raise


async def delete_dataset(dataset: str) -> None:
    """
    Delete an entire dataset from cognee.
    """
    logger.info("[delete_dataset] Forgetting dataset=%r", dataset)
    try:
        await cognee.forget(dataset=dataset)
        logger.info("[delete_dataset] Successfully deleted dataset=%r", dataset)
    except Exception as exc:
        logger.error("[delete_dataset] cognee.forget() failed for dataset=%r - %s: %s", dataset, type(exc).__name__, exc)
        raise