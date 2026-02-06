import os
from fastapi import FastAPI, UploadFile, File, Form, Header
from typing import Optional
from dotenv import load_dotenv

# Base Integrations
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Core Tools & Hub (2026 Stable Path)
from langchain_core.tools.retriever import create_retriever_tool
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
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-001", google_api_key=api_key)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    return embeddings, llm

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
4. 'Observation': उपकरण द्वारा दी गई जानकारी।
... (यह Thought/Action/Action Input/Observation चक्र कई बार दोहराया जा सकता है)
5. 'Thought': अब मुझे अंतिम उत्तर पता चल गया है।
6. 'Final Answer': मूल प्रश्न का विस्तार से और विनम्रतापूर्वक हिंदी में अंतिम उत्तर।

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
    content = (await file.read()).decode("utf-8") if file else text
    
    if not content: return {"error": "No content"}

    docs = RecursiveCharacterTextSplitter(chunk_size=1000).create_documents([content])
    
    # Load or create index using the user's key
    if os.path.exists(DB_PATH):
        vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)
        vectorstore.add_documents(docs)
    else:
        vectorstore = FAISS.from_documents(docs, embeddings)
    
    vectorstore.save_local(DB_PATH)
    return {"message": "Knowledge updated."}

@app.post("/chat")
async def chat(query: str, session_id: str, x_api_key: str = Header(...)):
    embeddings, llm = get_llm_and_embeddings(x_api_key)
    
    if not os.path.exists(DB_PATH):
        return {"answer": "ज्ञान का आधार (Knowledge base) खाली है। कृपया पहले दस्तावेज अपलोड करें।"}
        
    vectorstore = FAISS.load_local(DB_PATH, embeddings, allow_dangerous_deserialization=True)

    tool = create_retriever_tool(
        vectorstore.as_retriever(),
        "jain_scripture_search",
        "दिगंबर जैन ग्रंथों और शास्त्रों के अंश खोजने के लिए उपयोगी।"
    )
    tools = [tool]

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