from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os

from Backend.config import Config
from Backend.tools import capture_lead_tool, qualify_project_tool, generate_strategy_tool, get_company_portfolio_summary


# 🔥 SMART QUERY ENHANCER
def enhance_query(user_input):
    text = user_input.lower()

    if "mobile" in text:
        return "Explain mobile app development and list top technologies like Flutter and React Native"

    elif "web" in text:
        return "Explain web development and list frontend/backend technologies"

    elif "ai" in text:
        return "Explain AI/ML services and tools used by the company"

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


# 🔥 LOAD VECTOR DB
def load_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(model=Config.EMBEDDING_MODEL)

    if os.path.exists(Config.VECTORSTORE_PATH):
        try:
            return FAISS.load_local(
                Config.VECTORSTORE_PATH,
                embeddings,
                allow_dangerous_deserialization=True
            )
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
You are a premium AI Sales Consultant for Appic Software.

SALES FUNNEL:
1. GREET & IDENTIFY: Welcome the user and ask about their project (Mobile, Web, or AI).
2. LEAD CAPTURE: Once they describe a project, ask for their Name & Email.
3. QUALIFY: Ask for Budget & Developer Level.
4. STRATEGY: Propose the roadmap.

Context:
{context}

CRITICAL RULES:
1. DO NOT ask for Name/Email in the very first greeting. First, understand what they want to build.
2. ALWAYS provide 2-3 clear options in [OPTIONS: ...].
3. For the first message, suggest services: [OPTIONS: Mobile Apps, Web Development, AI Solutions].
4. Keep answers very short (2 lines max).

🔥 TOOL RULES:
- Name + Email -> `capture_lead_tool`.
- Project + Budget + Level -> `qualify_project_tool`.
- Ready for roadmap -> `generate_strategy_tool`.
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
            if ("429" in error_str or "RESOURCE_EXHAUSTED" in error_str) and i < len(models) - 1:
                continue
                
            if i == len(models) - 1:
                return {
                    "message": "⚠️ API Rate Limit reached or Service unavailable. Please try again in 15 seconds.",
                    "options": ["Try Again", "Services"]
                }
            continue

    return {
        "message": "I'm having a little trouble connecting. Please try again in a moment.",
        "options": ["Services", "Contact"]
    }


# 🔥 AGENT
class SimpleAgent:
    def __init__(self):
        self.history = []

    def invoke(self, data):
        user_input = data["input"]

        result = get_chat_response(user_input, self.history)

        self.history.append(HumanMessage(content=user_input))
        self.history.append(AIMessage(content=result["message"]))

        return result


def get_agent_executor():
    return SimpleAgent()


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