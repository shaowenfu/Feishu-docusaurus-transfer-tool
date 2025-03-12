# feishu_api.py
import requests
import json
import time
from config import APP_ID, APP_SECRET, AUTH_URL, DOC_URL, DOC_TOKEN
import lark_oapi as lark
from lark_oapi.api.docx.v1 import *

def get_tenant_access_token():
    """
    获取飞书API的tenant_access_token
    
    Returns:
        str: 获取到的tenant_access_token
    
    Raises:
        Exception: 如果获取失败，抛出异常
    """
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    
    print(f"正在获取tenant_access_token，使用APP_ID: {APP_ID}")
    
    try:
        response = requests.post(AUTH_URL, headers=headers, json=payload)
        response_json = response.json()
        
        print(f"飞书API认证响应: {json.dumps(response_json, ensure_ascii=False)}")
        
        if response_json.get("code") == 0:
            token = response_json.get("tenant_access_token")
            print(f"成功获取tenant_access_token: {token[:10]}...")
            return token
        else:
            error_msg = f"获取tenant_access_token失败: {response_json.get('msg')}"
            print(f"错误详情: {json.dumps(response_json, ensure_ascii=False)}")
            raise Exception(error_msg)
    except Exception as e:
        print(f"获取tenant_access_token时发生错误: {str(e)}")
        raise

# 存储token及其过期时间
_token_cache = {
    "token": None,
    "expire_time": 0
}

def get_token():
    """
    获取有效的token，如果缓存的token已过期则重新获取
    
    Returns:
        str: 有效的tenant_access_token
    """
    current_time = time.time()
    
    # 如果token不存在或已过期（预留10分钟缓冲）
    if (_token_cache["token"] is None or 
        current_time > _token_cache["expire_time"] - 600):
        
        token = get_tenant_access_token()
        # 设置过期时间（2小时后）
        _token_cache["token"] = token
        _token_cache["expire_time"] = current_time + 7200
        
    return _token_cache["token"]

def get_document_content():
    """
    获取《命理Tips》文档的内容
    
    Returns:
        dict: 文档内容的JSON对象，格式为：
        {
            "code": 0,
            "data": {
                "content": "markdown格式的文档内容"
            },
            "msg": "success"
        }
    
    Raises:
        Exception: 如果获取失败，抛出异常
    """
    token = get_token()
    
    # 创建 lark client
    client = lark.Client.builder() \
        .enable_set_token(True) \
        .log_level(lark.LogLevel.DEBUG) \
        .build()

    # 构造请求对象
    request = RawContentDocumentRequest.builder() \
        .document_id(DOC_TOKEN) \
        .lang(0) \
        .build()

    print(f"正在获取文档内容，DOC_TOKEN: {DOC_TOKEN}")
    
    try:
        # 发起请求
        option = lark.RequestOption.builder().tenant_access_token(token).build()
        response = client.docx.v1.document.raw_content(request, option)
        
        print(f"飞书文档API响应状态码: {response.code}")
        
        # 处理失败返回
        if not response.success():
            error_msg = f"获取文档内容失败: {response.msg}"
            print(f"错误详情: {response.raw.content}")
            raise Exception(error_msg)
            
        # 处理业务结果
        # 将SDK响应对象转换为字典格式
        response_dict = {
            "code": 0,
            "data": {
                "content": response.data.content
            },
            "msg": "success"
        }
        
        # 保存原始响应内容到文件，用于调试
        with open("raw_response.json", "w", encoding="utf-8") as f:
            if hasattr(response.data, 'to_dict'):
                json.dump(response.data.to_dict(), f, ensure_ascii=False, indent=2)
            else:
                json.dump({"content": response.data.content}, f, ensure_ascii=False, indent=2)
        
        print(f"已将原始响应内容保存到raw_response.json文件")
        
        return response_dict
        
    except Exception as e:
        print(f"获取文档内容时发生错误: {str(e)}")
        raise

def debug_api_response(doc_content):
    """
    调试输出API返回的JSON结构
    """
    try:
        # 如果是 SDK 的响应对象，转换为字典
        if hasattr(doc_content, 'to_dict'):
            content_dict = doc_content.to_dict()
        else:
            content_dict = doc_content
            
        # 如果内容太长，只打印前1000个字符
        content_str = json.dumps(content_dict, ensure_ascii=False, indent=2)
        if len(content_str) > 1000:
            print(f"{content_str[:1000]}...(内容过长，已截断)")
        else:
            print(content_str)
            
        # 保存完整内容到文件
        with open("api_response.json", "w", encoding="utf-8") as f:
            json.dump(content_dict, f, ensure_ascii=False, indent=2)
        
        print(f"已将完整响应内容保存到api_response.json文件")
    except Exception as e:
        print(f"无法序列化响应内容: {str(e)}")
        print(f"响应内容类型: {type(doc_content)}")
        print(f"响应内容: {str(doc_content)}")
