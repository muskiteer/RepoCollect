import logging
import cognee

logger = logging.getLogger(__name__)

async def recall_data(query_text: str, datasets: list[str], top_k: int = 5):
    """
    Recall insights from cognee based on a natural language query.
    """
    logger.info(
        "[recall_data] Querying cognee for %r in datasets=%r (top_k=%d)", 
        query_text, datasets, top_k
    )
    try:
        results = await cognee.search(
            query_text=query_text,
            datasets=datasets,
            top_k=top_k
        )
        
        if isinstance(results, dict):
            return results.get("search_result", [])
        
        if isinstance(results, list):
            final_results = []
            for item in results:
                if isinstance(item, dict) and "search_result" in item:
                    final_results.extend(item["search_result"])
                else:
                    final_results.append(item)
            return final_results
            
        return results
    except Exception as exc:
        logger.error("[recall_data] cognee.search() failed - %s: %s", type(exc).__name__, exc)
        raise