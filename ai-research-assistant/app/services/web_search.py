"""
Web Search Integration Module
Enables web search capability for research enhancement
Supports multiple search providers
"""
import os
import logging
from typing import List, Dict, Any, Optional
import requests
from urllib.parse import quote

logger = logging.getLogger(__name__)

class WebSearchProvider:
    """Base class for web search providers"""
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search and return results"""
        raise NotImplementedError

class GoogleSearchProvider(WebSearchProvider):
    """Google Custom Search API Provider"""
    
    def __init__(self, api_key: Optional[str] = None, search_engine_id: Optional[str] = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.search_engine_id = search_engine_id or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API"""
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Search API credentials not configured")
            return []
        
        try:
            params = {
                "q": query,
                "key": self.api_key,
                "cx": self.search_engine_id,
                "num": min(num_results, 10)
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json().get("items", [])
                return [
                    {
                        "title": result.get("title"),
                        "url": result.get("link"),
                        "snippet": result.get("snippet"),
                        "domain": result.get("displayLink")
                    }
                    for result in results
                ]
        except Exception as e:
            logger.error(f"Google Search error: {str(e)}")
        
        return []

class BingSearchProvider(WebSearchProvider):
    """Bing Search API Provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("BING_SEARCH_API_KEY")
        self.base_url = "https://api.bing.microsoft.com/v7.0/search"
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Bing Search API"""
        if not self.api_key:
            logger.warning("Bing Search API key not configured")
            return []
        
        try:
            headers = {
                "Ocp-Apim-Subscription-Key": self.api_key
            }
            params = {
                "q": query,
                "count": min(num_results, 50),
                "mkt": "en-US"
            }
            
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                results = response.json().get("webPages", {}).get("value", [])
                return [
                    {
                        "title": result.get("name"),
                        "url": result.get("url"),
                        "snippet": result.get("snippet"),
                        "domain": result.get("displayUrl")
                    }
                    for result in results
                ]
        except Exception as e:
            logger.error(f"Bing Search error: {str(e)}")
        
        return []

class DuckDuckGoSearchProvider(WebSearchProvider):
    """DuckDuckGo Search Provider (Free, No API Key Required)"""
    
    def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo (instant answers API)"""
        try:
            params = {
                "q": query,
                "format": "json"
            }
            
            response = requests.get(
                "https://api.duckduckgo.com/",
                params=params,
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0"}
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Get results from RelatedTopics
                for result in data.get("RelatedTopics", [])[:num_results]:
                    if "Text" in result and "FirstURL" in result:
                        results.append({
                            "title": result.get("Text", "").split('\n')[0][:100],
                            "url": result.get("FirstURL"),
                            "snippet": result.get("Text"),
                            "domain": result.get("FirstURL", "").split('/')[2]
                        })
                
                return results
        except Exception as e:
            logger.error(f"DuckDuckGo Search error: {str(e)}")
        
        return []

class WebSearchEngine:
    """
    Unified Web Search Engine
    Supports multiple providers with fallback
    """
    
    def __init__(self, provider: str = "duckduckgo"):
        self.provider = provider
        self.set_provider(provider)
    
    def set_provider(self, provider: str):
        """Set the search provider"""
        if provider.lower() == "google":
            self.search_provider = GoogleSearchProvider()
        elif provider.lower() == "bing":
            self.search_provider = BingSearchProvider()
        else:
            self.search_provider = DuckDuckGoSearchProvider()
    
    def search(self, query: str, num_results: int = 5) -> Dict[str, Any]:
        """
        Search the web
        Returns structured results
        """
        try:
            results = self.search_provider.search(query, num_results)
            
            return {
                "success": len(results) > 0,
                "query": query,
                "provider": self.provider,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def search_and_summarize(self, query: str, num_results: int = 3) -> Dict[str, Any]:
        """
        Search the web and combine results
        Returns a consolidated knowledge summary
        """
        search_results = self.search(query, num_results)
        
        if not search_results["success"]:
            return {
                "success": False,
                "error": "No search results found"
            }
        
        # Combine snippets
        combined_info = "\n".join([
            f"• {result['title']}\n  {result['snippet']}\n  Source: {result['url']}"
            for result in search_results['results']
        ])
        
        return {
            "success": True,
            "query": query,
            "summary": combined_info,
            "sources": search_results['results'],
            "source_count": len(search_results['results'])
        }

# Convenience function
def web_search(query: str, provider: str = "duckduckgo", num_results: int = 5) -> Dict[str, Any]:
    """Quick web search function"""
    engine = WebSearchEngine(provider)
    return engine.search(query, num_results)

def web_search_and_summarize(query: str, provider: str = "duckduckgo") -> Dict[str, Any]:
    """Quick web search with summary"""
    engine = WebSearchEngine(provider)
    return engine.search_and_summarize(query)
