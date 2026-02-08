from ResumeAnalyse import utils

amap_maps_mcp_config = {
    "transport": "sse",
    "url": "https://dashscope.aliyuncs.com/api/v1/mcps/amap-maps/sse",
    "headers": {
        "Authorization": f"Bearer {utils.dashscope_api_key}"
    }
}

tongyi_web_search_mcp_config = {
    "transport": "sse",
    "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/sse",
    "headers": {
        "Authorization": f"Bearer {utils.dashscope_api_key}",
        "Content-Type": "application/json"
    }
}

tongyi_web_parser = {
    "transport": "sse",
    "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebParser/sse",
    "headers": {
      "Authorization": f"Bearer {utils.dashscope_api_key}"
    }
}

jina_web_search_mcp_config = {
    "transport": "sse",
    "url": "https://dashscope.aliyuncs.com/api/v1/mcps/jina-ai/sse",
    "headers": {
        "Authorization": f"Bearer {utils.dashscope_api_key}"
    }
}

tavily_mcp_config = {
    "transport": "sse",
    "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={utils.tavily_api_key}",
}

mcp_list: dict[str, dict[str, str]] = {
    "amap_maps": amap_maps_mcp_config,
    # "tongyi_web_search": tongyi_web_search_mcp_config,
    # "tongyi_web_parser": tongyi_web_parser,
    # "jina_web_search": jina_web_search_mcp_config,
    "tavily": tavily_mcp_config,
}
