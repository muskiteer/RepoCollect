import logging
import cognee

logger = logging.getLogger(__name__)

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