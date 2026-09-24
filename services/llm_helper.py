from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os
import sys
import json
import logging

# Ensure UTF-8 standard output encoding on Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

load_dotenv()

# Prioritized list of 100% Free-Tier text-based Gemini models (Google AI Studio Free Tier):
# Flash and Flash-Lite models offer generous free rate limits (up to 15 RPM / 1,500 RPD) with no billing required.
FREE_TEXT_MODELS = [
    "gemini-3.8-flash",            # Primary: Fast, intelligent Flash model (Free Tier)
    "gemini-3.7-flash",            # Fallback 1: Multi-step Flash model (Free Tier)
    "gemini-3.6-flash",            # Fallback 2: Balanced Flash model (Free Tier)
    "gemini-3.5-flash-lite",       # Fallback 3: Fastest & high-throughput Flash-Lite (Free Tier)
    "gemini-3.5-flash",            # Fallback 4: Foundational Flash (Free Tier)
    "gemini-3.1-flash-lite",       # Fallback 5: Frontier Flash-Lite (Free Tier)
    "gemini-3-flash-preview",      # Fallback 6: Flash Preview (Free Tier)
    "gemini-2.5-flash",            # Fallback 7: 2.5 Flash (Free Tier)
    "gemini-2.5-flash-lite",       # Fallback 8: 2.5 Flash-Lite (Free Tier)
]

def create_model_instance(model_name: str, temperature: float = 0):
    """Creates a ChatGoogleGenerativeAI instance for a specific model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is missing.")
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=temperature
    )

def get_llm(primary_model: str = None, fallback_models: list = None):
    """
    Returns an LLM runnable with LangChain automatic fallbacks configured
    strictly across 100% Free-Tier Gemini Flash/Lite models.
    """
    if primary_model is None:
        primary_model = os.getenv("GEMINI_MODEL", FREE_TEXT_MODELS[0])

    if fallback_models is None:
        fallback_models = [m for m in FREE_TEXT_MODELS if m != primary_model]

    primary_llm = create_model_instance(primary_model)
    fallbacks = []

    for model_name in fallback_models:
        try:
            fallbacks.append(create_model_instance(model_name))
        except Exception as e:
            print(f"[Warning] Failed to initialize free fallback model {model_name}: {e}")

    if fallbacks:
        return primary_llm.with_fallbacks(fallbacks=fallbacks)
    return primary_llm


def invoke_llm_with_resilience(prompt: str) -> str:
    """
    Invokes the LLM with multi-tier fallback handling across free-tier Gemini models
    to ensure 100% free high availability even when rate limits or spikes occur.
    """
    primary_model = os.getenv("GEMINI_MODEL", FREE_TEXT_MODELS[0])
    candidate_models = [primary_model] + [m for m in FREE_TEXT_MODELS if m != primary_model]
    
    last_exception = None

    # Try LangChain fallback chain first
    try:
        llm = get_llm(primary_model=primary_model)
        response = llm.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part) for part in content
            )
        return content.strip()
    except Exception as e:
        print(f"[LLM Fallback Warning] Primary fallback chain encountered error: {e}. Trying iterative fallback across free models...")
        last_exception = e

    # Explicit iterative fallback across free-tier models
    for model_name in candidate_models:
        try:
            print(f"[LLM Fallback] Attempting execution with free model: {model_name}")
            instance = create_model_instance(model_name)
            response = instance.invoke(prompt)
            content = response.content
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part) for part in content
                )
            print(f"[LLM Fallback] Succeeded with model: {model_name}")
            return content.strip()
        except Exception as err:
            print(f"[LLM Spiked/Failed] Model '{model_name}' failed: {err}")
            last_exception = err

    raise RuntimeError(f"All free Gemini models failed. Last error: {last_exception}")


def get_job_link(title, description):
    PROMPT = f"""
    You are a helpful assistant that extracts job application links from YouTube video descriptions.

    TASK:
    - Return the FIRST valid job application link.
    - Output format MUST be exactly:
    Link: <URL>
    - If no job application link is found, return:
    No link found

    RULES:
    1. Prefer links that start with "Link: or Links:" in the description. These are more likely to be the correct application links. Like google forms, jobs portal, etc.
    2. If no "Link:" exists, use the company name from the TITLE to match a relevant URL.
    3. Ignore unrelated links (Topmate, WhatsApp, Educative, GFG, etc.) 

    EXAMPLES:

    Title:
    Mhtechin Hiring Interns Apply Now | Open to All

    Description:
    https://www.linkedin.com/posts/mhtechin-india_hiring-internship-freshers-activity-7406640651783688192-APkn

    Output:
    https://www.linkedin.com/posts/mhtechin-india_hiring-internship-freshers-activity-7406640651783688192-APkn

    just extract the link.

    ------------------
    ACTUAL INPUT:

    Title:
    {title}

    Description:
    {description}
    """
    print(f"Invoking LLM to extract job link for: {title}")
    content = invoke_llm_with_resilience(PROMPT)
    print("LLM successfully returned job link extraction response.")
    return content


def get_job_details(title, transcript):
    PROMPT = f"""
    You are a helpful assistant that extracts job details from YouTube video transcripts.
    TASK:
    - Extract the following details:
    1. Company Name (It is clearly mentioned in the video title for example: "Mhtechin Hiring Interns Apply Now | Open to All" -> Company Name is "Mhtechin")
    2. Role (if internship mention "Internship" in brackets. for example: Software Engineer (Internship))
    3. Location
    4. Job Requirements (brief summary which includes skills/qualifications and experience required. Format as a plain text list using "•" as the bullet. Do NOT use HTML tags like <ul> or <li>. Use newlines to separate items. If the role is internship then include the duration of internship)
    5. Package Range (if mentioned, if not, mention "Not specified")
    - Output format MUST be exactly in JSON as shown below:
    {{
        "company_name": "<Company Name>",
        "role": "<Role>",
        "location": "<Location>",
        "job_requirements": "<Job Requirements>",
        "package_range": "<Package Range>"
    }}
    - If any detail is not mentioned, use "Not specified" for that field.
    Here's the title and transcript:
    Title:
    {title}

    Transcript:
    {transcript}
    """
    print(f"Invoking LLM to extract job details for: {title}")
    content = invoke_llm_with_resilience(PROMPT)
    print("LLM successfully returned job details extraction response.")

    # Clean up markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    try:
        parsed = json.loads(content.strip())
        
        if isinstance(parsed, list) and len(parsed) > 0:
            parsed = parsed[0]
            
        if not isinstance(parsed, dict):
            raise ValueError("Parsed JSON is not a dictionary")
            
        return parsed
    except (json.JSONDecodeError, ValueError):
        return {
            "company_name": "Not specified",
            "role": "Not specified",
            "location": "Not specified",
            "job_requirements": "Not specified",
            "package_range": "Not specified"
        }


if __name__ == "__main__":
    # ---------- TESTING LLM ---------- 
    title = "Mhtechin Hiring Interns Apply Now | Open to All"
    transcript = """
    Hi everyone. So I'm back with a great off-campus opportunity and this one is with MTeken. So if you don't know by now, Mtechen is hiring for internship right now.
    """
    description = """
        Connect 1:1 with me for placement help: https://topmate.io/example
        Link: https://eoje.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/5029
    """
    print("Testing get_job_link...")
    res_link = get_job_link(title, description)
    print("Link Result:", res_link)

    print("\nTesting get_job_details...")
    res_details = get_job_details(title, transcript)
    print("Details Result:", json.dumps(res_details, indent=2))
