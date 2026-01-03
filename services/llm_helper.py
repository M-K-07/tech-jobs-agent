from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
import json
load_dotenv()

def get_llm():
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        model="google/gemma-3n-e2b-it:free",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    return llm


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
    1. Prefer links that start with "Link:"
    2. If no "Link:" exists, use the company name from the TITLE to match a relevant URL.
    3. Ignore unrelated links (Topmate, WhatsApp, Educative, Google Docs, Reddit, GFG, etc.)

    EXAMPLES:

    Title:
    Mhtechin Hiring Interns🔥Apply Now | Open to All

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
    llm=get_llm() 
    response = llm.invoke(PROMPT)
    return response.content.strip()

def get_job_details(title,transcript):
    PROMPT = f"""
    You are a helpful assistant that extracts job details from YouTube video transcripts.
    TASK:
    - Extract the following details:
    1. Company Name (It is clearly mentioned in the video title for example: "Mhtechin Hiring Interns🔥Apply Now | Open to All" -> Company Name is "Mhtechin")
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
    llm=get_llm()
    response = llm.invoke(PROMPT)
    content = response.content.strip()

    # Clean up markdown code blocks if present
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    try:
        return json.loads(content.strip())
    except json.JSONDecodeError:
        return {
            "company_name": "Not specified",
            "role": "Not specified",
            "location": "Not specified",
            "job_requirements": "Not specified",
            "package_range": "Not specified"
        }

if __name__ == "__main__":
    # ---------- TESTING LLM ---------- 
    llm = get_llm()
    title=" Mhtechin Hiring Interns🔥Apply Now | Open to All"
    transcript="""
    Hi everyone. So I'm back with a great off-c campus opportunity and this one is with MTeken. So if you don't know by now, Mtechen is hiring for internship right now. So this is a great opportunity for all of you people out there that are looking for an internship. So in this video, we'll be having a look at the details of the internship. We're going to be talking about the eligibility and we're going to discuss everything in detail. So make sure that you watch the complete video and then apply right away. And it has been posted just a day back but people have already started getting reverts back for online assessment. So this is an opening that you can definitely get a revert back from. Okay. So watch the video and then apply right away. The details for everything is going to be in the description box. All right. Right? And if you're someone who's having difficulty in off-c campus placements, if you keep on applying everywhere, but your resume keeps on getting rejected, you keep on seeing rejected mail everywhere and you don't know what to change in your resume, what to change in your portfolio to be able to get shortlisted or you're stuck in preparation, you don't know how to master DSA, you don't know how to master development or any other sort of issues you're facing in your placement journey or in your career, then you can connect one to one with me and I'll personally sit with you, guide you, mentor you and tell you the exact road map that you need to follow, what you need to do exactly. so that you're able to land your dream job. So you can connect 21 with me. The link for that is going to be in the description box. All right, coming back to this opportunity. Like I said, Mken is hiring for internship and we'll talk about eligibility first. Then we'll go deeper into what the internship is going to be, you know, all about and the details of it. So let's get into the eligibility. So one thing I really like is that here all branches are welcome basically. So if you're from BCA, BTech, ME, Mtech, MCA, basically if you're from any branch and you're from a degree, a bachelor's degree and you're in any branch, you know, any branch in your uh college, it doesn't matter. That is basically what they've written, right? They've clearly mentioned all branches are welcome, which is something we don't see often. You know, a lot of times people from Mtech branch comments on my channel, people from civil comment on my channel and they say that, you know, we're not getting any opportunities, bring some opportunities for us. So here you go. This is an opportunity that is open to all and people are getting rewards back from this opportunity. So it's a very very very important opportunity and one that you should apply for right away if you're eligible. Now if you talk about year- wise then they haven't mentioned exactly which year can apply. They have just clearly mentioned that freshers can apply and students can apply. So you can take that for what it is. If you're a student you can apply from any branch from bachelor's degree and of course if you're a fresher you can apply as well. Right? So that is exactly what they've mentioned. they have not gone into the specifics of it. Okay. So that is pretty much the eligibility. Now if we talk more about the internship, this is going to be a 6 months internship. The location is going to be in Pune and it is going to be hybrid. So of course that is one thing that you need to have the commitment for a 6 months internship. Even if you're a college student, it is fine but you need to have the commitment for a six months internship. Okay. And of course they've not exactly mentioned what texts they're looking for. So probably a lot of people are getting their resume shortlisted and getting the OA based on what I have heard most of the people have gotten the OA for that. So of course most of it is going to be dependent on the online assessment. So first you're going to have your resume shortlisting. Second you're going to have your online assessment then you're going to have your technical interview, HR interview and then your background verification and then you'll get the offer letter. Okay. So everything seems very legit. This has been posted by the company itself. Now for how to apply it's not a link. There's not a link for this. They're not using a link for this basically or a form for this. What you need to do, you need to send your resume to the mail id. So they have mentioned a mail in the post basically. I'll also give the mail ID in the description box. You can basically mail to it with your resume and you know a few details about yourself and based on that you will be able to get a online assessment. Okay. So that's pretty much it. This is the exact way on how to apply. It has been posted one day back. So do not delay for any longer. Just try to apply as soon as possible. We don't know when it's going to close. So yeah, that's pretty much it. Let's not delay any further and let's not make the video any longer. The way to apply every detail is in the description.
    """
    description="""
        Connect 1:1 with me for placement help and resume review: https://topmate.io/ashishcode

        Link:https://eoje.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/5029

        https://docs.google.com/document/d/1S1Sjxj9R9D4hJptOmpm5Zekb0VzkJ2WPNyrLkO555FU/edit?usp=sharing   """ 
    # res = get_job_details(title, transcript)
    res = get_job_link(title, description)
    print("----- JOB DETAILS -----")
    print(res)
    print(type(res))
