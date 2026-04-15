# services/rag_chain.py
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from services.llm_service import get_llm


def get_standard_rag_chain(retriever):
    llm = get_llm()

    # Prompt yêu cầu trả lời bằng tiếng Việt
    template = """Sử dụng ngữ cảnh sau đây để trả lời câu hỏi. 
Nếu bạn không biết, chỉ cần nói là bạn không biết. Trả lời ngắn gọn (3-4 câu) bằng tiếng Việt.

Ngữ cảnh: {context}

Câu hỏi: {question}

Trả lời:"""

    prompt = PromptTemplate.from_template(template)

    # Hàm phụ để nối các văn bản tìm được lại với nhau thành 1 chuỗi dài
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Xây dựng chuỗi LangChain Expression Language (LCEL)
    rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    return rag_chain