from typing import List, Dict, Any, Callable
from functools import wraps
import collections

def lru_cache_with_list_support(maxsize: int = 128):
    """
    Decorator that implements an LRU cache for functions that take a list of IDs.
    Only uncached IDs will trigger API requests.

    The decorated function must return items in the same order as the IDs.
    
    :param maxsize: Maximum size of the cache
    :return: Decorated function
    """
    def decorator(func: Callable):
        cache: Dict[str, str] = collections.OrderedDict()
        
        @wraps(func)
        def wrapper(ids: List[str]) -> List[str]:
            uncached_ids = [id for id in ids if id not in cache]
            
            if uncached_ids:
                new_results = func(uncached_ids)
                
                for id, name in zip(uncached_ids, new_results):
                    if len(cache) >= maxsize:
                        cache.popitem(last=False)
                    
                    cache[id] = name
                    if id in cache:
                        cache.move_to_end(id)
            
            return [cache[id] for id in ids]
            
        wrapper.clear_cache = lambda: cache.clear()
        
        wrapper.get_cache = lambda: dict(cache)

        return wrapper
    
    return decorator