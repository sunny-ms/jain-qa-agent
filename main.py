import os
import re
from fastapi import FastAPI, UploadFile, File, Form, Header
from typing import Optional
from dotenv import load_dotenv

# Base Integrations
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Core Tools & Hub (2026 Stable Path)
from langchain_core.tools import tool as tool_decorator
import langchainhub

# Legacy/Classic Agent logic
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.memory import ConversationBufferMemory

load_dotenv()

app = FastAPI()
DB_PATH = "faiss_index_shared"
user_memories = {}

# Helper to initialize models with a specific key
def get_llm_and_embeddings(api_key: str):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=api_key)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    return embeddings, llm

def parse_youtube_transcription(content: str):
    """Parse a YouTube transcription file with --- header and [MM:SS:frames] timestamps."""
    from langchain_core.documents import Document

    # Extract header block
    header_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
    if not header_match:
        return None

    header_text = header_match.group(1)
    body = content[header_match.end():]

    # Parse header fields
    meta = {}
    for line in header_text.strip().splitlines():
        if ':' in line:
            key, val = line.split(':', 1)
            meta[key.strip()] = val.strip()

    if meta.get('source_type') != 'youtube' or 'youtube_url' not in meta:
        return None

    # Extract video ID from URL
    url = meta['youtube_url']
    video_id_match = re.search(r'(?:v=|live/)([A-Za-z0-9_-]+)', url)
    video_id = video_id_match.group(1) if video_id_match else ''
    title = meta.get('title', 'YouTube Video')

    # Split body into segments by [MM:SS:frames] pattern
    segments = re.split(r'\[(\d{2}:\d{2}:\d{2,3})\]', body)
    # segments: ['', 'MM:SS:ff', ' text\n', 'MM:SS:ff', ' text\n', ...]

    docs = []
    for i in range(1, len(segments), 2):
        timestamp_raw = segments[i]
        text = segments[i + 1].strip() if i + 1 < len(segments) else ''
        if not text:
            continue

        # Convert MM:SS:frames to seconds
        parts = timestamp_raw.split(':')
        minutes, seconds = int(parts[0]), int(parts[1])
        total_seconds = minutes * 60 + seconds

        youtube_link = f"https://www.youtube.com/watch?v={video_id}&t={total_seconds}"
        display_ts = f"{minutes:02d}:{seconds:02d}"

        docs.append(Document(
            page_content=text,
            metadata={
                "source": title,
                "source_type": "youtube",
                "youtube_url": url,
                "timestamp": display_ts,
                "youtube_link": youtube_link
            }
        ))

    return docs

from langchain_core.prompts import PromptTemplate

# Define the custom ReAct prompt in Hindi
hindi_react_template = """
आप एक विशेषज्ञ दिगंबर जैन विद्वान और सहायक AI हैं। आपका नाम 'जैन-QA-एजेंट' है।
आपका कार्य उपयोगकर्ताओं को दिगंबर जैन शास्त्रों, तीर्थंकरों और आचरण के बारे में सटीक जानकारी देना है।

हमेशा निम्नलिखित प्रारूप (format) का उपयोग करें:

प्रत्यूत्तर के लिए उपलब्ध उपकरण (Tools): {tools}

निर्देश:
1. 'Thought': आपको हमेशा सोचना चाहिए कि क्या करना है। (जैसे: मुझे शास्त्र में अहिंसा के बारे में खोजना चाहिए)
2. 'Action': वह उपकरण (tool) जिसे आप चुनेंगे, इन में से एक होना चाहिए: [{tool_names}]
3. 'Action Input': उपकरण के लिए खोज शब्द (search query)।
4. 'Observation': उपकरण द्वारा दी गई जानकारी। ध्यान दें कि Observation में metadata भी होती है जैसे source, source_type, timestamp, youtube_link।
... (यह Thought/Action/Action Input/Observation चक्र कई बार दोहराया जा सकता है)
5. 'Thought': अब मुझे अंतिम उत्तर पता चल गया है।
6. 'Final Answer': मूल प्रश्न का विस्तार से और विनम्रतापूर्वक हिंदी में अंतिम उत्तर।

उद्धरण (Citation) नियम:
- जब भी आप Observation से जानकारी का उपयोग करें, तो inline उद्धरण दें।
- YouTube स्रोत के लिए: [स्रोत: <title>, <timestamp> - <youtube_link>]
- अन्य स्रोत के लिए: [स्रोत: <source name>]
- अंतिम उत्तर के अंत में एक "स्रोत (Sources):" अनुभाग जोड़ें जिसमें सभी संदर्भित स्रोतों की सूची हो।

शुरू करें!

चैट का इतिहास (Chat History):
{chat_history}

प्रश्न: {input}
Thought: {agent_scratchpad}
"""

# Create the Prompt object
hindi_prompt = PromptTemplate.from_template(hindi_react_template)

@app.post("/upload")
async def upload(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    x_api_key: str = Header(...) # Key passed in headers
):
    embeddings, _ = get_llm_and_embeddings(x_api_key)
    filename = file.filename if file else None
    content = (await file.read()).decode("utf-8") if file else text

    if not content: return {"error": "No content"}

    # Check if content is a YouTube transcription
    youtube_docs = parse_youtube_transcription(content)
    if youtube_docs:
        docs = youtube_docs
    else:
        source = filename or "Uploaded Text"
        chunks = RecursiveCharacterTextSplitter(chunk_size=1000).create_documents([content])
        for chunk in chunks:
            chunk.metadata["source"] = source
            chunk.metadata["source_type"] = "text"
        docs = chunks

    # Load or create index using the user's key
    if os.path.exists(DB_PATH):
        vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        vectorstore.add_documents(docs)
    else:
        vectorstore = FAISS.from_documents(docs, embeddings)

    vectorstore.save_local(DB_PATH)
    return {"message": f"Knowledge updated. {len(docs)} chunks indexed."}

@app.post("/chat")
async def chat(query: str, session_id: str, x_api_key: str = Header(...)):
    embeddings, llm = get_llm_and_embeddings(x_api_key)
    
    if not os.path.exists(DB_PATH):
        return {"answer": "ज्ञान का आधार (Knowledge base) खाली है। कृपया पहले दस्तावेज अपलोड करें।"}
        
    vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever()

    @tool_decorator
    def jain_scripture_search(query: str) -> str:
        """दिगंबर जैन ग्रंथों और शास्त्रों के अंश खोजने के लिए उपयोगी। परिणाम में source, timestamp, और YouTube लिंक शामिल होते हैं।"""
        docs = retriever.invoke(query)
        results = []
        for doc in docs:
            meta = doc.metadata
            entry = doc.page_content
            if meta.get("source_type") == "youtube":
                entry += f"\n[स्रोत: {meta.get('source', '')}, समय: {meta.get('timestamp', '')}, लिंक: {meta.get('youtube_link', '')}]"
            else:
                entry += f"\n[स्रोत: {meta.get('source', 'Unknown')}]"
            results.append(entry)
        return "\n\n---\n\n".join(results) if results else "कोई जानकारी नहीं मिली।"

    tools = [jain_scripture_search]

    if session_id not in user_memories:
        user_memories[session_id] = ConversationBufferMemory(
            memory_key="chat_history", 
            return_messages=True
        )
    
    # Construct the ReAct Agent with the CUSTOM HINDI PROMPT
    agent = create_react_agent(llm, tools, hindi_prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        memory=user_memories[session_id], 
        verbose=True, 
        handle_parsing_errors=True
    )

    result = agent_executor.invoke({"input": query})
    return {"answer": result["output"]}