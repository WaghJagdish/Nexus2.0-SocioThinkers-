import asyncio, json
from core.config import get_settings
from services.cache_service import CacheService, MemoryCache
from services.llm_service import LLMService
from services.scheme_service import SchemeService
async def test():
    settings = get_settings()
    cache = CacheService(MemoryCache())
    llm = LLMService(settings)
    ss = SchemeService(llm, cache)
    res = await ss.search_schemes('maize farming', 'Maharashtra')
    print(json.dumps(res, indent=2))
asyncio.run(test())
