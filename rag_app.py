import os
import dotenv
from langchain_community.vectorstores import Neo4jVector
# CAMBIAMENTO 1: Importiamo le classi per Ollama
from langchain_ollama import OllamaEmbeddings, ChatOllama
from langchain_classic.chains.retrieval_qa.base import RetrievalQA
from langchain_classic.prompts import PromptTemplate


# Carica env
dotenv.load_dotenv()

# Configurazione Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password_segreta")

# 1. SETUP DEL RETRIEVER IBRIDO (GraphRAG)
# La query Cypher rimane IDENTICA. È la logica del DB, non dipende dall'LLM.
graph_retrieval_query = """
RETURN
    "Function: " + node.name + "\\n" +
    "File: " + node.filename + "\\n" +
    "Docstring: " + node.docstring + "\\n" +
    "Code snippet: " + substring(node.code, 0, 200) + "...\\n" +
    "IMPACT ANALYSIS (Graph Traversal):\\n" +
    " - Is called by: " + 
    reduce(s = "", caller IN [(node)<-[:CALLS]-(c) | c.name] | s + caller + ", ") + "\\n" +
    " - Calls: " + 
    reduce(s = "", callee IN [(node)-[:CALLS]->(c) | c.name] | s + callee + ", ") 
    AS text,
    score,
    {source: node.filename} AS metadata
"""

# CAMBIAMENTO 2: Inizializzazione Embedding Locale
# DEVE essere lo stesso modello usato in ingest.py (nomic-embed-text)
embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
)

print("Connessione a Neo4j e inizializzazione Vector Store...")

try:
    vector_store = Neo4jVector.from_existing_graph(
        embedding=embeddings,
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        index_name="code_index",
        node_label="Function",
        text_node_properties=["name", "docstring", "code"],
        embedding_node_property="embedding",
        retrieval_query=graph_retrieval_query
    )
    
    # Creiamo il retriever
    retriever = vector_store.as_retriever(search_kwargs={'k': 2}) 

    # CAMBIAMENTO 3: Setup dell'LLM Locale (ChatOllama)
    # Usiamo llama3.1 che è molto solido per compiti di ragionamento
    print("Inizializzazione LLM Locale (Llama 3.1)...")
    llm = ChatOllama(
        model="mistral", # Assicurati di aver fatto `ollama pull llama3.1`
        temperature=0,    # 0 per risposte deterministiche e tecniche
        base_url="http://localhost:11434"
    )

    template = """
    Sei un Senior Software Architect esperto in modernizzazione di codice legacy.
    Usa il contesto fornito (che include codice e analisi delle dipendenze dal grafo) per rispondere alla domanda.
    
    Se il contesto indica delle dipendenze (IMPACT ANALYSIS), enfatizzale nella risposta.

    CONTESTO RECUPERATO:
    {context}

    DOMANDA UTENTE:
    {question}

    RISPOSTA (Analisi tecnica dettagliata in Italiano):
    """

    prompt = PromptTemplate(
        template=template, 
        input_variables=["context", "question"]
    )

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt}
    )

    # 3. ESECUZIONE
    if __name__ == "__main__":
        print("\n--- Agente Legacy Code Navigator (LOCAL VERSION) avviato ---\n")
        
        # Domanda test
        query = "La funzione 'send' è critica. Chi la chiama? Se modifico i suoi parametri, quali parti della libreria smettono di funzionare?"
        
        print(f"Domanda: {query}")
        print("Sto ragionando (può richiedere qualche secondo su CPU)...")
        
        response = qa_chain.invoke(query)
        
        print("\n=== Risposta Agente ===")
        print(response["result"])

except Exception as e:
    print(f"\nERRORE: {e}")
    print("Suggerimento: Controlla che Neo4j sia attivo e che Ollama sia in esecuzione (ollama serve).")