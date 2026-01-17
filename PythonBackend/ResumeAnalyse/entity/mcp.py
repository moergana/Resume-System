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
