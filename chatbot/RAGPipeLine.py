# RAGPipeLine.py
from fastapi import FastAPI, HTTPException, Request
import logging
from chatbot.utils.update import split_document, convert_file_to_documents
from chatbot.utils.prompt import contextualize_q_prompt, qa_prompt
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import HumanMessage, SystemMessage, Document
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables import Runnable
from dotenv import load_dotenv
from pydantic import BaseModel
from chatbot.utils.redis_utils import save_message_to_redis, get_messages_from_redis
from core.redis_config import redis_conn  # Redis 설정 임포트

load_dotenv()

config = {
    "llm_predictor": {
        "model_name": "gpt-3.5-turbo",
        "temperature": 0
    },
    "embed_model": {
        "model_name": "text-embedding-ada-002",
        "cache_directory": "",
    },
    "chroma": {
        "persist_dir": "./database",
    },
    "path": {
        "input_directory": "./documents",
    },
    "search_type": "similarity",
    "ensemble_search_type": "mmr",
    "similarity_k": 0.25,
    "retriever_k": 5,
}


class Ragpipeline(Runnable):
    def __init__(self):
        self.SIMILARITY_THRESHOLD = config["similarity_k"]
        self.llm = ChatOpenAI(
            model=config['llm_predictor']['model_name'],
            temperature=config['llm_predictor']['temperature']
        )
        self.vector_store = self.init_vectorDB()
        self.retriever = self.init_retriever()
        self.chain = self.init_chat_chain()
        self.session_histories = {}
        self.current_user_email = None
        self.current_session_id = None

    def init_vectorDB(self):
        embeddings = OpenAIEmbeddings(
            model=config['embed_model']['model_name'])
        vector_store = Chroma(
            persist_directory=config["chroma"]["persist_dir"],
            embedding_function=embeddings
        )
        print(f"[초기화] vector_store 초기화 완료")
        return vector_store

    def init_retriever(self):
        retriever = self.vector_store.as_retriever(
            search_kwargs={"k": config["retriever_k"]},
            search_type="similarity"
        )
        print(f"[초기화] retriever 초기화 완료")
        return retriever

    def init_chat_chain(self):
        history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )
        question_answer_chain = create_stuff_documents_chain(
            self.llm, qa_prompt)
        rag_chat_chain = create_retrieval_chain(
            history_aware_retriever, question_answer_chain)
        print("[초기화] RAG chain 초기화 완료")
        return rag_chat_chain

    def invoke(self, input, config=None, **kwargs):
        self.current_user_email = input["user_email"]
        self.current_session_id = input.get("session_id", "default_session")
        question = input["input"]
        try:
            answer = self.chat_generation(question)
            response = {
                "output": answer,
                "metadata": {"source": "RAGPipeline"}
            }
            print(f"Server response: {response}")
            return response
        except Exception as e:
            print(f"Error in invoke method: {e}")
            raise

    def chat_generation(self, question: str) -> dict:
        def get_session_history(session_id=None, user_email=None):
            session_id = session_id if session_id else self.current_session_id
            user_email = user_email if user_email else self.current_user_email
            if session_id not in self.session_histories:
                self.session_histories[session_id] = ChatMessageHistory()
                # Redis에서 세션 히스토리 불러오기
                history_messages = get_messages_from_redis(
                    user_email, session_id)
                for message in history_messages:
                    self.session_histories[session_id].add_message(
                        HumanMessage(content=message)
                    )
                print(
                    f"[히스토리 생성] 새로운 히스토리를 생성합니다. 세션 ID: {session_id}, 유저: {user_email}")
            return self.session_histories[session_id]

        conversational_rag_chain = RunnableWithMessageHistory(
            self.chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer"
        )

        response = conversational_rag_chain.invoke(
            {"input": question},
            config={"configurable": {"session_id": self.current_session_id}}
        )

        # Redis에 세션 히스토리 저장
        save_message_to_redis(self.current_user_email,
                              self.current_session_id, question)
        save_message_to_redis(self.current_user_email,
                              self.current_session_id, response["answer"])

        print(f'[응답 생성] 실제 모델 응답: response => \n{response}\n')
        return response["answer"]

    def update_vector_db(self, file, filename) -> bool:
        upload_documents = convert_file_to_documents(file)
        new_documents = []
        for doc in upload_documents:
            results = self.vector_store.similarity_search_with_score(
                doc.page_content, k=1)
            print(f'유사도 검사 중...results : {results}')
            if results and results[0][1] <= self.SIMILARITY_THRESHOLD:
                print(f"유사한 청크로 판단되어 추가되지 않음 - {results[0][1]}")
                continue
            chunks = split_document(doc)
            new_documents.extend(chunks)
        if new_documents:
            self.vector_store.add_documents(new_documents)
            print(
                f"Added {len(new_documents)} new documents to the vector store")
            return True
        else:
            print('모두 유사한 청크로 판단되어 해당 문서가 저장되지 않음')
            return False

    def delete_vector_db_by_doc_id(self, doc_id):
        all_documents = self.vector_store._collection.get(
            include=["metadatas"])
        documents_to_delete = [doc_id for i, metadata in enumerate(
            all_documents["metadatas"]) if metadata.get("doc_id") == doc_id]
        if documents_to_delete:
            self.vector_store._collection.delete(ids=documents_to_delete)
            print(f"[벡터 DB 삭제] 문서 ID [{doc_id}]의 임베딩을 벡터 DB에서 삭제했습니다.")
        else:
            print(f"[벡터 DB 삭제 실패] 문서 ID [{doc_id}]에 대한 임베딩을 찾을 수 없습니다.")
