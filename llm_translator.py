# llm_translator.py
import os
import json
import time
import urllib.request
import ssl
from typing import Optional, Dict, List, Any

# Azure OpenAI API configuration
AZURE_OPENAI_ENDPOINT = ""
AZURE_OPENAI_API_KEY = ""
AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4o"

def set_azure_openai_config(endpoint: str, api_key: str, deployment_name: str = "gpt-4o"):
    """Set Azure OpenAI API configuration"""
    global AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT_NAME
    AZURE_OPENAI_ENDPOINT = endpoint
    AZURE_OPENAI_API_KEY = api_key
    AZURE_OPENAI_DEPLOYMENT_NAME = deployment_name

def allow_self_signed_https(allowed: bool):
    """Bypass the server certificate verification on client side"""
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

def generate_translation_prompt(content: str, file_path: str, target_language: str) -> str:
    """
    Generate a prompt for the LLM to translate the content
    
    Args:
        content (str): The markdown content to translate
        file_path (str): The path of the file being translated
        target_language (str): The target language code
    
    Returns:
        str: The prompt for the LLM
    """
    language_names = {
        "en": "English",
        "ja": "Japanese",
        "ko": "Korean",
        "zh-Hant": "Traditional Chinese"
    }
    
    language_name = language_names.get(target_language, target_language)
    
    # Extract directory and filename from the path
    parts = file_path.split('/')
    directory = parts[-2] if len(parts) >= 2 else ""
    filename = parts[-1].replace('.md', '')
    
    prompt = f"""You are a professional translator specializing in Chinese metaphysics and traditional Chinese divination systems. 
Translate the following Markdown content from Chinese to {language_name}.

IMPORTANT TRANSLATION GUIDELINES:
1. Maintain all Markdown formatting in your translation.
2. For specialized Chinese metaphysics terms (like 天干, 地支, 甲, 乙, etc.) that don't have precise translations, use the Chinese pinyin with the original term in parentheses. For example: "Jia (甲)".
3. Ensure your translation sounds natural to native {language_name} speakers while preserving the technical accuracy.
4. Your translation should be high quality and not easily identifiable as machine translation.
5. Preserve all YAML frontmatter (content between --- markers at the beginning of the document).
6. If the frontmatter contains a 'sidebar_position' field, ensure it's set correctly based on the content's position in Chinese metaphysics. For example, in 天干 (Heavenly Stems), 甲 (Jia) should be position 1, 丙 (Bing) should be position 3, etc.
7. If the frontmatter is missing, add the following YAML frontmatter at the beginning of your translation:
```
---
sidebar_position: [appropriate position]
hide_table_of_contents: true
hide_title: true
pagination_next: null
pagination_prev: null
---
```

CONTEXT INFORMATION:
- Directory: {directory}
- Filename: {filename}

ORIGINAL MARKDOWN CONTENT:
{content}

Provide ONLY the translated Markdown content with proper frontmatter. Do not include any explanations or notes outside the translation.
"""
    return prompt

def translate_with_llm(content: str, file_path: str, target_language: str, max_retries: int = 4) -> Optional[str]:
    """
    Translate content using Azure OpenAI API
    
    Args:
        content (str): The markdown content to translate
        file_path (str): The path of the file being translated
        target_language (str): The target language code
        max_retries (int): Maximum number of retries on failure
    
    Returns:
        Optional[str]: The translated content or None if translation failed
    """
    if not AZURE_OPENAI_ENDPOINT or not AZURE_OPENAI_API_KEY:
        raise ValueError("Azure OpenAI API configuration not set. Please set endpoint and API key.")
    
    # Allow self-signed HTTPS certificates
    allow_self_signed_https(True)
    
    # Generate the prompt for translation
    prompt = generate_translation_prompt(content, file_path, target_language)
    
    # Use the provided endpoint directly
    url = AZURE_OPENAI_ENDPOINT
    
    # print(f"Using API endpoint: {url}")  # Debug log
    
    # Prepare the request data
    data = {
        "messages": [
            {"role": "system", "content": "You are a professional translator specializing in Chinese metaphysics."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 4000,
        "top_p": 0.95,
        "frequency_penalty": 0,
        "presence_penalty": 0
    }
    
    body = json.dumps(data).encode('utf-8')
    
    # Set up the request headers
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'api-key': AZURE_OPENAI_API_KEY
    }
    
    # print(f"Request headers: {headers}")  # Debug log (注意隐藏 API key)
    
    # Disable proxy for this request
    proxy_handler = urllib.request.ProxyHandler({})
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)
    
    for retry in range(max_retries):
        try:
            # Create the request
            req = urllib.request.Request(url, body, headers)
            
            # print(f"\nAttempt {retry + 1}/{max_retries}")  # Debug log
            # print(f"Sending request to: {url}")  # Debug log
            
            # Send the request
            try:
                response = urllib.request.urlopen(req, timeout=60)
                # print(f"Response status: {response.status}")  # Debug log
                # print(f"Response headers: {response.headers}")  # Debug log
            except urllib.error.HTTPError as e:
                print(f"HTTP Error {e.code}: {e.reason}")
                print(f"Error response body: {e.read().decode('utf-8')}")
                raise
            except urllib.error.URLError as e:
                print(f"URL Error: {e.reason}")
                raise
            
            # Parse the response
            response_body = response.read().decode('utf-8')
            # print(f"Response body: {response_body[:200]}...")  # Debug log (truncated)
            
            result = json.loads(response_body)
            
            # Extract the translated content
            if 'choices' in result and len(result['choices']) > 0:
                translated_content = result['choices'][0]['message']['content']
                
                # Clean up the response to extract just the markdown
                translated_content = extract_markdown_from_response(translated_content)
                
                return translated_content
            else:
                print(f"Unexpected response format: {result}")
                
                if retry < max_retries - 1:
                    print(f"Retrying ({retry + 1}/{max_retries})...")
                    time.sleep(2 ** retry)  # Exponential backoff
                    continue
                return None
                
        except Exception as e:
            print(f"Error during LLM translation: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            print(f"Error details: {getattr(e, '__dict__', {})}")
            
            if retry < max_retries - 1:
                print(f"Retrying ({retry + 1}/{max_retries}) after error...")
                time.sleep(2 ** retry)  # Exponential backoff
                continue
            return None
    
    return None

def extract_markdown_from_response(response: str) -> str:
    """
    Extract the markdown content from the LLM response
    
    Args:
        response (str): The raw response from the LLM
    
    Returns:
        str: The extracted markdown content
    """
    # If the response is already clean markdown, return it as is
    if response.startswith('---'):
        return response
    
    # Check if the response contains markdown code blocks
    if '```markdown' in response or '```md' in response:
        # Extract content between markdown code blocks
        import re
        markdown_blocks = re.findall(r'```(?:markdown|md)\n([\s\S]*?)\n```', response)
        if markdown_blocks:
            return markdown_blocks[0]
    
    # If no code blocks but has frontmatter, try to extract from the beginning of frontmatter
    if '---' in response:
        start_idx = response.find('---')
        # Find the second occurrence of '---'
        second_idx = response.find('---', start_idx + 3)
        if second_idx != -1:
            # Find content after the second '---'
            return response[start_idx:]
    
    # If all else fails, return the original response
    return response

def translate_document_with_llm(document_structure: Dict[str, Dict[str, str]], 
                               target_languages: List[str], 
                               force_translate: bool = False,
                               docusaurus_path: str = None,
                               language_paths: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Translate document structure using LLM
    
    Args:
        document_structure (Dict): The document structure to translate
        target_languages (List[str]): List of target language codes
        force_translate (bool): Whether to force retranslation of existing files
        docusaurus_path (str): Path to the Docusaurus project
        language_paths (Dict[str, str]): Mapping of language codes to i18n directory paths
    
    Returns:
        Dict[str, Any]: Statistics about the translation process
    """
    from translator import DOCUSAURUS_LANGUAGE_PATHS
    from file_generator import sanitize_filename
    from config import DOCS_PATH
    
    if docusaurus_path is None:
        from config import DOCUSAURUS_PATH
        docusaurus_path = DOCUSAURUS_PATH
    
    if language_paths is None:
        language_paths = DOCUSAURUS_LANGUAGE_PATHS
    
    print(f"Starting LLM translation for languages: {', '.join(target_languages)}")
    
    # Translation statistics
    stats = {
        'total_files': 0,
        'skipped_files': 0,
        'translated_files': 0,
        'failed_files': 0
    }
    
    for lang in target_languages:
        # Skip Chinese (source language)
        if lang == "zh-Hans":
            continue
        
        # Get the language directory path
        lang_path = language_paths.get(lang)
        if not lang_path:
            print(f"Warning: No directory mapping found for language {lang}, skipping")
            continue
        
        i18n_docs_path = os.path.join(docusaurus_path, "i18n", lang_path, "docusaurus-plugin-content-docs", "current")
        
        print(f"\nTranslating content to {lang} using LLM")
        
        # Iterate through the document structure
        for level1_title, content_dict in document_structure.items():
            # Use the original Chinese directory name
            category_name = level1_title
            category_path = os.path.join(i18n_docs_path, sanitize_filename(category_name))
            
            # If English translation, also prepare the path in docs directory
            docs_category_path = None
            if lang == "en":
                docs_category_path = os.path.join(DOCS_PATH, sanitize_filename(category_name))
                os.makedirs(docs_category_path, exist_ok=True)
                print(f"  Preparing docs directory for English translation: {docs_category_path}")
            
            # Ensure the i18n directory exists
            os.makedirs(category_path, exist_ok=True)
            
            print(f"  Processing directory: {category_name}")
            
            # Create translated files for each content item
            for title, content in content_dict.items():
                stats['total_files'] += 1
                
                # Use the original Chinese filename
                file_name = sanitize_filename(title) + ".md"
                file_path = os.path.join(category_path, file_name)
                
                # If English translation, also prepare the file path in docs directory
                docs_file_path = None
                if lang == "en":
                    docs_file_path = os.path.join(docs_category_path, file_name)
                
                # Check if the file already exists
                skip_translation = False
                if os.path.exists(file_path) and not force_translate:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_content = f.read().strip()
                        if existing_content:
                            print(f"    - Skipping existing file: {file_name}")
                            stats['skipped_files'] += 1
                            skip_translation = True
                    except Exception as e:
                        print(f"    - Failed to read existing file {file_name}, will retranslate: {str(e)}")
                
                if not skip_translation:
                    try:
                        # Translate the content using LLM
                        relative_path = f"{category_name}/{file_name}"
                        translated_content = translate_with_llm(content, relative_path, lang)
                        
                        if translated_content:
                            # Write to i18n file
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(translated_content)
                            
                            # If English translation, also write to docs directory
                            if lang == "en" and docs_file_path:
                                with open(docs_file_path, 'w', encoding='utf-8') as f:
                                    f.write(translated_content)
                                print(f"    - Translated file and wrote to both i18n and docs: {file_name}")
                            else:
                                print(f"    - Translated file: {file_name}")
                            
                            stats['translated_files'] += 1
                        else:
                            print(f"    - Failed to translate file: {file_name}")
                            stats['failed_files'] += 1
                            
                    except Exception as e:
                        print(f"    - Error translating file {file_name}: {str(e)}")
                        stats['failed_files'] += 1
                elif lang == "en" and docs_file_path:
                    # If skipping translation but it's English, still need to copy to docs directory
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_content = f.read()
                        with open(docs_file_path, 'w', encoding='utf-8') as f:
                            f.write(existing_content)
                        print(f"    - Copied existing translation to docs directory: {file_name}")
                    except Exception as e:
                        print(f"    - Failed to copy file {file_name} to docs directory: {str(e)}")
            
            print(f"  Directory {category_name} translation completed")
    
    # Print statistics
    print("\nLLM Translation Statistics:")
    print(f"Total files: {stats['total_files']}")
    print(f"Skipped files: {stats['skipped_files']}")
    print(f"Successfully translated: {stats['translated_files']}")
    print(f"Failed translations: {stats['failed_files']}")
    
    return stats
