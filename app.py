import streamlit as st
from pathlib import Path
from langchain_classic.agents import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.callbacks import StreamlitCallbackHandler
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="SQL Query Agent", page_icon=":bar_chart:", layout="wide")
st.title("SQL Query Agent with LangChain Classic and Groq")

INJECTION_WARNING = """
**⚠️ Warning: This agent executes SQL queries directly on the database.**
Make sure to only input safe and valid SQL queries to avoid potential security risks or data loss.
"""

LOCALDB = "USE_LOCAL_DB"
MYSQL = "USE_MYSQL_DB"

radio_opt = ["Use Local SQLite Database", "Use MySQL Database"]
selected_opt = st.sidebar.radio("Select Database Type", radio_opt)

if radio_opt.index(selected_opt) == 1:
    db_url = MYSQL
    mysql_host = st.sidebar.text_input("provide MySQL Host")
    mysql_user = st.sidebar.text_input("provide MySQL User")
    mysql_pass = st.sidebar.text_input("provide MySQL Password", type="password")
    mysql_db = st.sidebar.text_input("provide MySQL Database Name")
else:
    db_url = LOCALDB

api_key = st.text_input("Goq API Key")

if not db_url:
    st.info("Please select a database type and provide the necessary connection details.")
if not api_key:
    st.info("Please enter your Groq API Key to proceed.")

## llm model
llm = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        streaming=True,   
    )
## configure db function with cache
@st.cache_resource(ttl="1d2h34m")
def configure_db(db_url, mysql_host=None, mysql_user=None, mysql_pass=None, mysql_db=None):
    if db_url == LOCALDB:
       dbfilepath = (Path(__file__).parent / "student.db").absolute()
       print("file path",dbfilepath)
       creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
       return SQLDatabase(create_engine("sqlite+pysqlite://", creator=creator))
    elif db_url == MYSQL:
        if not (mysql_host and mysql_user and mysql_pass and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        ## connect to mysql database
        return SQLDatabase.from_uri(f"mysql+pymysql://{mysql_user}:{mysql_pass}@{mysql_host}/{mysql_db}")
    
if db_url==MYSQL:
    db = configure_db(db_url, mysql_host, mysql_user, mysql_pass, mysql_db)
else:
    db = configure_db(db_url)

## toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

## create agent
schema = """
You are working with a database that has the following table:

Table: student
Columns:
- id (integer, primary key)
- name (text)
- age (integer)
- grade (text)

Example queries:
- "show all students"
- "list students older than 20"
- "count students"

Use SQL SELECT queries only.
"""

agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type="zero-shot-react-description",
    prefix=schema,
    max_iterations=50,
    max_execution_time=70,
    handle_parsing_errors=True
)

if "messages" not in st.session_state or st.sidebar.button("clear messages history"):
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello, I am a SQL query agent. Ask me anything about the student or mysql database."}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

user_query = st.chat_input("Ask a question about the database...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        callback = StreamlitCallbackHandler(st.container())
        response = agent.invoke( {"input": user_query}, {"callbacks": [callback]})
        response = response["output"]
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)
