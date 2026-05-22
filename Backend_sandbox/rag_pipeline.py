from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
import json
import re

from Backend_sandbox.config import Config
from Backend_sandbox.tools import capture_lead_tool, qualify_project_tool, generate_strategy_tool, get_company_portfolio_summary


# 🔥 SMART QUERY ENHANCER
def enhance_query(user_input):
    text = user_input.lower()

    if re.search(r'\b(mobile|app|application)\b', text):
        return f"Focus: Mobile Development. User says: {user_input}"

    elif re.search(r'\bweb\b', text):
        return f"Focus: Web Development. User says: {user_input}"

    elif re.search(r'\b(ai|artificial intelligence)\b', text):
        return f"Focus: AI Solutions. User says: {user_input}"

    return user_input


# 🔥 FORMAT RESPONSE
def format_ai_response(text):
    text = text.replace("•", "-")
    text = text.replace("\n\n\n", "\n\n")
    return text.strip()


# 🔥 EXTRACT OPTIONS FOR FRONTEND
def extract_options(text):
    if "[OPTIONS:" in text:
        start = text.find("[OPTIONS:")
        end = text.find("]", start)
        options_text = text[start+9:end].strip()
        
        # Handle both \n, raw newlines, and comma-separated options
        options_text = options_text.replace("\\n", "\n")
        if "\n" in options_text:
            raw_lines = options_text.split("\n")
        else:
            raw_lines = options_text.split(",")
            
        options = [opt.strip() for opt in raw_lines if opt.strip()]
        
        clean_text = text[:start] + text[end+1:]
        return clean_text.strip(), options

    return text, []


# Global cache for vectorstore
_VECTORSTORE_CACHE = None

# 🔥 LOAD VECTOR DB
def load_vectorstore():
    global _VECTORSTORE_CACHE
    
    if _VECTORSTORE_CACHE is not None:
        return _VECTORSTORE_CACHE

    embeddings = GoogleGenerativeAIEmbeddings(model=Config.EMBEDDING_MODEL)

    if os.path.exists(Config.VECTORSTORE_PATH):
        try:
            _VECTORSTORE_CACHE = FAISS.load_local(
                Config.VECTORSTORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
            return _VECTORSTORE_CACHE
        except Exception as e:
            print(f"Vector load error: {e}")

    return None


# 🔥 MAIN CHAT FUNCTION
def get_chat_response(user_input, history_messages=[]):
    db = load_vectorstore()

    context = "Appic Software provides AI, Mobile and Web development services."

    if db:
        try:
            docs = db.similarity_search(user_input, k=3)
            if docs:
                context = "\n".join([doc.page_content for doc in docs])
        except Exception as e:
            print(f"Search error: {e}")

    models = [Config.PRIMARY_MODEL, Config.FALLBACK_MODEL, Config.LITE_MODEL]
    current_history = history_messages[-6:]

    for i, model_name in enumerate(models):
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_name,
                temperature=Config.TEMPERATURE,
                google_api_key=Config.GOOGLE_API_KEY
            )

            # ... (rest of the logic remains same)
            # (I'll just replace the whole block for clarity)
            tools = [
                capture_lead_tool,
                qualify_project_tool,
                generate_strategy_tool,
                get_company_portfolio_summary
            ]

            llm_with_tools = llm.bind_tools(tools)

            prompt = ChatPromptTemplate.from_messages([
                ("system", f"""
You are a premium AI Sales Consultant for Appic Software. Your style is helpful, professional, and conversational like ChatGPT.

SALES FUNNEL:
1. IDENTIFY & ENGAGE: Once the user chooses a service (Mobile, Web, or AI), talk about it with expertise.
2. VALUE ADD: Provide insights like ChatGPT.
3. LEAD CAPTURE: Ask for Name & Email once the user is engaged.
4. QUALIFY (STEP-BY-STEP): Ask for Budget, then ask for Developer Level separately.
5. DEEP DIVE: After qualification, discuss 1-2 more specific project aspects (like user experience, scalability, or key features) to make it feel natural and detailed.
6. STRATEGY: Finally, provide a comprehensive strategy using the `generate_strategy_tool`. This MUST include:
   - Detailed Functions/Features.
   - Specific Tech Stack (Frontend, Backend, Database).
   - Estimated Timeline (e.g., 4-6 weeks).
   - How we will build it (Our methodology).
7. CALL REQUEST: After the strategy, address the user by Name and offer a discovery call. 
   - If they agree to a call: Ask for their Phone Number. Once provided, tell them: "Got it! We will arrange a call for you, and you'll be notified via email. Now we will discuss it in depth on the call." Then ask if they have any other queries or info to share. 
     - If they say YES: Ask: "What specifically would you like to know more about?" and respond accordingly.
     - If they say NO: End with a premium, warm greeting and a big "Thank You" for choosing Appic Software.
   - If they refuse the call and want to discuss here: Respect their choice and continue the technical discussion right here in the chat.

Context:
{context}

CRITICAL RULES:
1. END OF CONVERSATION: Whenever the user indicates they have no more questions, are satisfied, or want to end the chat (e.g., "no", "that is all", "thanks"), provide a premium, warm farewell greeting and a big "Thank You" for choosing Appic Software.
2. PERSONALIZATION: Address the user by name frequently after the strategy.
3. CALL BRANCHING: strictly follow the "Yes/No" call logic. If they want to stay on chat, continue.
4. ONE AT A TIME: Ask questions separately.
5. CHATGPT STYLE: Advisor-like tone.
6. ENGAGEMENT: End every response with 2-3 strategic questions until the call request is finalized.
7. OPTIONS: Always provide 2-3 options in [OPTIONS: ...].

🔥 TOOL RULES:
- Name + Email -> `capture_lead_tool`.
- Project + Budget + Level -> `qualify_project_tool`.
- Ready for full roadmap -> `generate_strategy_tool`.
"""),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])

            chain = prompt | llm_with_tools
            enhanced_input = enhance_query(user_input)

            response = chain.invoke({
                "input": enhanced_input,
                "history": current_history
            })

            if response.tool_calls:
                tool_results = []
                for tool_call in response.tool_calls:
                    name = tool_call["name"]
                    args = tool_call["args"]

                    if name == "capture_lead_tool":
                        res = capture_lead_tool.invoke(args)
                    elif name == "qualify_project_tool":
                        res = qualify_project_tool.invoke(args)
                    elif name == "generate_strategy_tool":
                        res = generate_strategy_tool.invoke(args)
                    elif name == "get_company_portfolio_summary":
                        res = get_company_portfolio_summary.invoke(args)
                    else:
                        res = "Tool executed"

                    tool_results.append(
                        ToolMessage(content=str(res), tool_call_id=tool_call["id"])
                    )

                second_response = llm.invoke(
                    prompt.format_messages(
                        input=enhanced_input,
                        history=current_history + [response] + tool_results
                    )
                )

                content = second_response.content
                if isinstance(content, list):
                    content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content if not isinstance(c, dict) or "text" in c])
                
                final_text = format_ai_response(str(content))
                clean_text, options = extract_options(final_text)

                return {"message": clean_text, "options": options}

            content = response.content
            if isinstance(content, list):
                content = "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content if not isinstance(c, dict) or "text" in c])
            
            final_text = format_ai_response(str(content))
            clean_text, options = extract_options(final_text)

            return {"message": clean_text, "options": options}

        except Exception as e:
            error_str = str(e)
            print(f"Model {model_name} error: {e}")
            
            # If it's a rate limit and we have more models, try next one
            if any(x in error_str for x in ["429", "RESOURCE_EXHAUSTED", "quota"]):
                import time
                time.sleep(2) # Wait to clear limit
                print(f"Rate limit hit for {model_name}, switching...")
                if i < len(models) - 1:
                    continue
                
            if i == len(models) - 1:
                if "404" in error_str or "NOT_FOUND" in error_str:
                    msg = "⚠️ AI Models not found for this API Key. Please check your Google AI Studio settings."
                else:
                    msg = "⚠️ API Rate Limit reached or Service unavailable. Please try again in 15 seconds."
                
                return {
                    "message": msg,
                    "options": ["Try Again", "Services"]
                }
            continue

    return {
        "message": "I'm having a little trouble connecting. Please try again in a moment.",
        "options": ["Services", "Contact"]
    }


# 🔥 AGENT
class SimpleAgent:
    def __init__(self, session_id="default"):
        self.session_id = session_id
        self.history_file = f"data/history_{session_id}.json"
        self.history = self._load_history()

    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r") as f:
                    data = json.load(f)
                    messages = []
                    for msg in data:
                        if msg["type"] == "human":
                            messages.append(HumanMessage(content=msg["content"]))
                        else:
                            messages.append(AIMessage(content=msg["content"]))
                    return messages
            except:
                return []
        return []

    def _save_history(self):
        os.makedirs("data", exist_ok=True)
        data = []
        for msg in self.history:
            m_type = "human" if isinstance(msg, HumanMessage) else "ai"
            data.append({"type": m_type, "content": msg.content})
        with open(self.history_file, "w") as f:
            json.dump(data, f)

    def invoke(self, data):
        user_input = data["input"]
        result = get_chat_response(user_input, self.history)

        self.history.append(HumanMessage(content=user_input))
        self.history.append(AIMessage(content=result["message"]))
        self._save_history()

        return result


def get_agent_executor(session_id="default"):
    return SimpleAgent(session_id)


# 🔥 DOC SPLITTER
def split_docs(documents):
    return RecursiveCharacterTextSplitter(
        chunk_size=Config.CHUNK_SIZE,
        chunk_overlap=Config.CHUNK_OVERLAP
    ).split_documents(documents)


# 🔥 ADD TO VECTOR DB
def add_to_vectorstore(docs):
    embeddings = GoogleGenerativeAIEmbeddings(model=Config.EMBEDDING_MODEL)

    if os.path.exists(Config.VECTORSTORE_PATH):
        db = FAISS.load_local(
            Config.VECTORSTORE_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        db.add_documents(docs)
    else:
        db = FAISS.from_documents(docs, embeddings)

    db.save_local(Config.VECTORSTORE_PATH)
    return True
