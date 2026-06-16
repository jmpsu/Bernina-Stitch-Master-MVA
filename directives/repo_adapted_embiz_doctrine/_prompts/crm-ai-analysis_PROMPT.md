Read this local source bundle and create complete EMBIZ-specific operational doctrine.

Repository: crm-ai-analysis
Local source: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis
Bundle: /root/embroidery_business_agent_system/directives/repo_adapted_embiz_doctrine/_prompts/crm-ai-analysis_SOURCE_BUNDLE.md

EMBIZ context:
- Root: /root/embroidery_business_agent_system
- Local corpus: /root/web-archive/ai_agents_skills_library
- OpenClaw: /root/.openclaw/workspace
- Agent bus: /usr/local/bin/agent-msg
- Slack mirror outbound-only; no secrets.
- Human approval required before customer contact.
- Human approval required before digitizing.
- Never claim SVG/PES/DST/EXP/INF/BMP exists unless file exists on disk.
- Named agents: Maya, Madeline, Morgan, Mila, Melanie, Mackenzie, Marina, Monica, Meredith, Mckenna, Margaret, Miranda, Michaela, Maeve, Matilda, Melody, Miriam, Mallory

You must adapt this repo into EMBIZ doctrine, not summarize it.

Write these sections:
# crm-ai-analysis EMBIZ ADAPTED DOCTRINE
## Source Material Read
## What This Repo Contributes To EMBIZ
## EMBIZ-Specific Adaptation
## Assigned Agent Ownership
## Local Skill / Knowledge Library Integration
## Runtime Rules
## Required Files / Configs
## Commands / Checks
## Security Restrictions
## Verification Checklist
## Build Tasks
## What Not To Use
## Integration Status

Now use this source bundle:


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/chat/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/chat/messages.py =====

from enum import Enum, auto
from pydantic import BaseModel

class RoleNotRecognized(Exception):
    """
    Exception raised when a provided role is not recognized.

    Args:
        role_provided (str):
            The role that was provided but not recognized.
        roles_availables (list[list[str]]):
            The available role equivalents categorized.

    Attributes:
        role_provided (str):
            Stores the unrecognized role.
        roles_availables (list[list[str]]):
            Stores the available role mappings.

    Methods:
        __str__():
            Returns a descriptive error message.
    """
    def __init__(self, role_provided: str, roles_availables: list[list[str]]):
        self.role_provided = role_provided
        self.roles_availables = roles_availables

    def __str__(self) -> str:
        return (f"Role provided ({self.role_provided}) not in available roles "
                f"({self.roles_availables}), provide an entity mapper")


class Role(Enum):
    """
    Enum representing different roles in a chat system.

    Roles:
        assistant: Represents an AI assistant.
        human: Represents a human user.
        system: Represents a system-generated message.

    Methods:
        get(role: str) -> Role:
            Returns the corresponding Role enum based on the provided role string.
    """
    assistant = auto()
    human = auto()
    system = auto()

    @staticmethod
    def get(role: str) -> 'Role':
        """
        Maps a string representation of a role to the corresponding Role enum.

        Args:
            role (str):
                The string representation of the role.

        Returns:
            Role:
                The corresponding Role enum.

        Raises:
            RoleNotRecognized:
                If the provided role does not match any known equivalents.
        """
        role = role.lower()
        human_equivalents = ['human', 'user']
        system_equivalents = ['system', 'sys']
        assistant_equivalents = ['assistant', 'ai']

        if role in human_equivalents:
            return Role.human
        if role in assistant_equivalents:
            return Role.assistant
        if role in system_equivalents:
            return Role.system

        raise RoleNotRecognized(
                role_provided=role,
                roles_availables=[human_equivalents,
                                  system_equivalents,
                                  assistant_equivalents])

class Message(BaseModel):
    """
    Represents a message in the chat system.

    Args:
        role (Role):
            The role of the sender (assistant, human, or system).
        content (str):
            The message content.

    Attributes:
        role (Role):
            The sender's role.
        content (str):
            The message content.
    """
    role: Role
    content: str

class MessageHistory:
    """
    Maintains a history of messages in a chat.

    Attributes:
        message_history (list[Message]):
            A list storing all messages in the chat history.

    Methods:
        add_message(message: Message) -> None:
            Adds a message to the history.
        add_human_message(content: str) -> None:
            Adds a message from a human user.
        add_system_message(content: str) -> None:
            Adds a system-generated message.
        add_assistant_message(content: str) -> None:
            Adds a message from the assistant.
    """
    def __init__(self):
        """
        Initializes an empty message history.
        """
        self.message_history: list[Message] = []

    def add_message(self, message: Message) -> None:
        """
        Adds a message to the history.

        Args:
            message (Message):
                The message to be added.
        """
        self.message_history.append(message)

    def add_human_message(self, content: str) -> None:
        """
        Adds a message from a human user.

        Args:
            content (str):
                The message content.
        """
        message = Message(role=Role.human, content=content)
        self.message_history.append(message)

    def add_system_message(self, content: str) -> None:
        """
        Adds a system-generated message.

        Args:
            content (str):
                The message content.
        """
        message = Message(role=Role.system, content=content)
        self.message_history.append(message)

    def add_assistant_message(self, content: str) -> None:
        """
        Adds a message from the assistant.

        Args:
            content (str):
                The message content.
        """
        message = Message(role=Role.assistant, content=content)
        self.message_history.append(message)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/chat/services.py =====

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from .messages import Role
from models.historic_messages_model import MessageDB, MessageHistoryDB

def chat_history_from_id(message_history_id: str, session) -> MessageHistoryDB:
    """
    Retrieves a chat history from the database based on the given ID.

    Args:
        message_history_id (str):
            The unique identifier of the chat history.
        session (Session):
            The database session used to execute the query.

    Returns:
        MessageHistoryDB:
            The retrieved chat history object. If not found, a new instance is created.

    Raises:
        NoResultFound:
            If no chat history is found, a new one is instantiated instead.
    """
    stmt = select(MessageHistoryDB).where(
        MessageHistoryDB.id == message_history_id
    )

    try:
        chat = session.scalars(stmt).one()
    except NoResultFound:
        chat = MessageHistoryDB(id=message_history_id)

    return chat


def save_user_message_in_chat(content: str, chat: MessageHistoryDB) -> None:
    """
    Saves a user message in the chat history.

    Args:
        content (str):
            The message content from the user.
        chat (MessageHistoryDB):
            The chat history object where the message should be stored.
    """
    chat.messages.append(MessageDB(role=Role.human.name, content=content))


def save_assistant_message_in_chat(content: str, chat: MessageHistoryDB) -> None:
    """
    Saves an assistant message in the chat history.

    Args:
        content (str):
            The message content from the assistant.
        chat (MessageHistoryDB):
            The chat history object where the message should be stored.
    """
    chat.messages.append(MessageDB(role=Role.assistant.name, content=content))


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/core/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/core/configs.py =====

from typing import ClassVar
import os

from pydantic_settings import BaseSettings
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

class Settings(BaseSettings):

    """
    General configs used for the the aplication
    """

    DBBaseModel: ClassVar = declarative_base()

    load_dotenv()
    DB_URL: ClassVar = os.getenv("DB_URL")
    PROJECT_PATH: ClassVar = os.getenv("PROJECT_PATH")
    DB_SCHEMA: ClassVar = os.getenv("DB_SCHEMA")
    DBT_PATH: ClassVar = os.getenv("DBT_PATH")

    class Config:
        case_sensitive = True


settings: Settings = Settings()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/core/database.py =====

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from core.configs import settings
from models.historic_messages_model import Base

engine = create_engine(settings.DB_URL, echo=False, future=True)

Session = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine
)

Base.metadata.create_all(engine)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/core/deps.py =====

from core.database import Session
from typing import Generator

def get_session() -> Generator[Session, None, None]:
    """
    Provides a database session, ensuring proper resource management.

    Yields:
        Session:
            A SQLAlchemy session for executing database queries.
    """
    session = Session()
    try:
        yield session
    finally:
        session.close()


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/main.py =====

import uvicorn
from fastapi import FastAPI

from src.database_operations import router as database_router
from src.rag_operations import router as rag_router
from src.historic_messages import router as historic_router
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifespan of the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.

     Returns:
        None
    """
    pass


app = FastAPI(
    title='CRM Analysis API',
    docs_url="/docs",
    redoc_url=None,  
    openapi_url="/docs/openapi.json"
)

prefix = '/api'
app.include_router(database_router, prefix=prefix)
app.include_router(rag_router, prefix=prefix)
app.include_router(historic_router, prefix=prefix)


if __name__ == "__main__":
    print("Initializing API server...")
    uvicorn.run(
        "main:app",
        port=8200,
        host='0.0.0.0',
        reload=True,
        log_level="info"
    )


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/models/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/models/accounts_model.py =====

from core.configs import settings
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid

class AccountsSourceModel(settings.DBBaseModel):
    """
    Represents account-related data stored in the database.

    Attributes:
        __tablename__ (str): 
            The name of the database table ("accounts_source").
        id (UUID): 
            The unique identifier for the account.
        account (str): 
            The name of the account.
        sector (str): 
            The business sector of the account.
        year_established (str): 
            The year the account was established.
        revenue (str): 
            The revenue of the account.
        employees (str): 
            The number of employees in the company.
        office_location (str): 
            The primary office location of the account.
        subsidiary_of (str, optional): 
            Indicates if the account is a subsidiary of another company.
    """
    __tablename__ = 'accounts_source'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account = Column(String, nullable=False)
    sector = Column(String, nullable=False)
    year_established = Column(String, nullable=False)
    revenue = Column(String, nullable=False)
    employees = Column(String, nullable=False)
    office_location = Column(String, nullable=False)
    subsidiary_of = Column(String, nullable=True)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/models/historic_messages_model.py =====

from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from chat.messages import Message, MessageHistory, Role


class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models, defining default table configurations.

    Attributes:
        __table_args__ (dict):
            Specifies the default schema ('public') for all tables.
    """
    __table_args__ = {'schema': 'public'}
    pass


class MessageHistoryDB(Base):
    """
    Represents a chat history stored in the database.

    Attributes:
        __tablename__ (str): 
            The name of the database table ("message_history").
        id (int): 
            The primary key identifier for the chat history.
        messages (List[MessageDB]): 
            A list of messages related to this chat history.

    Methods:
        to_message_history() -> MessageHistory:
            Converts the database object into a `MessageHistory` instance.
        to_list() -> list:
            Converts the stored messages into a list of dictionaries.
    """

    __tablename__ = "message_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    messages: Mapped[List["MessageDB"]] = relationship(
        back_populates="message_history",
        cascade="all, delete-orphan"
    )

    def to_message_history(self) -> MessageHistory:
        """
        Converts the stored messages into a `MessageHistory` object.

        Returns:
            MessageHistory:
                A `MessageHistory` instance containing all messages.
        """
        message_history = MessageHistory()
        for msg in self.messages:
            message_history.add_message(
                Message(
                    role=Role.get(msg.role),
                    content=msg.content
                )
            )
        return message_history

    def to_list(self) -> list:
        """
        Converts the stored messages into a list of dictionaries.

        Returns:
            list:
                A list containing message dictionaries with `role` and `content`.
        """
        msg_list = []
        for msg in self.messages:
            msg_list.append(msg.to_dict())

        return msg_list


class MessageDB(Base):
    """
    Represents an individual chat message stored in the database.

    Attributes:
        __tablename__ (str): 
            The name of the database table ("message").
        id (int): 
            The primary key identifier for the message.
        role (str): 
            The role of the sender (e.g., "human", "assistant", "system").
        content (str): 
            The actual message content.
        message_history_id (int): 
            The foreign key linking this message to a chat history.
        message_history (MessageHistoryDB): 
            The associated chat history.

    Methods:
        to_dict() -> dict:
            Converts the message into a dictionary format.
    """

    __tablename__ = "message"

    id: Mapped[int] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(String(2000))
    message_history_id: Mapped[int] = mapped_column(
        ForeignKey("public.message_history.id"))
    message_history: Mapped["MessageHistoryDB"] = relationship(
        back_populates="messages")

    def to_dict(self) -> dict:
        """
        Converts the message into a dictionary format.

        Returns:
            dict:
                A dictionary containing the `role` and `content` of the message.
        """
        return {'role': self.role, 'content': self.content}


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/models/products_model.py =====

from core.configs import settings
from sqlalchemy import Column, String, ForeignKey
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ProductsSourceModel(settings.DBBaseModel):
    """
    Represents product-related data stored in the database.

    Attributes:
        __tablename__ (str): 
            The name of the database table ("products_source").
        id (UUID): 
            The unique identifier for the product.
        product (str): 
            The name of the product.
        series (str): 
            The series to which the product belongs.
        sales_price (str): 
            The sales price of the product.
    """
    __tablename__ = 'products_source'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product = Column(String, nullable=False)
    series = Column(String, nullable=False)
    sales_price = Column(String, nullable=False)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/models/sales_pipeline_model.py =====

from core.configs import settings
from sqlalchemy import Column, String, Date, Float
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid

class SalesPipelineSourceModel(settings.DBBaseModel):
    """
    Represents sales pipeline data stored in the database.

    Attributes:
        __tablename__ (str): 
            The name of the database table ("sales_pipeline_source").
        opportunity_id (str): 
            The unique identifier for the sales opportunity.
        sales_agent (str): 
            The sales agent handling the opportunity.
        product (str): 
            The product associated with the opportunity.
        account (str, optional): 
            The account linked to the opportunity.
        deal_stage (str): 
            The current stage of the sales deal.
        engage_date (str, optional): 
            The date the opportunity was first engaged.
        close_date (str, optional): 
            The date the opportunity was closed.
        close_value (str, optional): 
            The closing value of the deal.
    """
    __tablename__ = 'sales_pipeline_source'
    
    opportunity_id = Column(String, nullable=False, primary_key=True)
    sales_agent = Column(String, nullable=False)
    product = Column(String, nullable=False)
    account = Column(String, nullable=True)
    deal_stage = Column(String, nullable=False)
    engage_date = Column(String, nullable=True)
    close_date = Column(String, nullable=True)
    close_value = Column(String, nullable=True)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/models/sales_teams_model.py =====

from core.configs import settings
from sqlalchemy import Column, String
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
import uuid

class SalesTeamsSourceModel(settings.DBBaseModel):
    """
    Represents sales team data stored in the database.

    Attributes:
        __tablename__ (str): 
            The name of the database table ("sales_teams_source").
        id (UUID): 
            The unique identifier for the sales team record.
        sales_agent (str): 
            The name of the sales agent.
        manager (str): 
            The name of the sales agent's manager.
        regional_office (str): 
            The regional office the agent is associated with.
    """
    __tablename__ = 'sales_teams_source'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sales_agent = Column(String, nullable=False)
    manager = Column(String, nullable=False)
    regional_office = Column(String, nullable=False)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/schemas/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/schemas/historic_messages_schema.py =====

from pydantic import BaseModel, NonNegativeInt

class ExampleSchema(BaseModel):
    """
    Represents an example data schema.

    Attributes:
        name (str): 
            The name of the example entity.
        description (str | None): 
            A brief description of the entity (can be None).
        date (str | None): 
            The associated date in string format (can be None).
    """
    name: str
    description: str | None
    date: str | None

class Message(BaseModel):
    """
    Represents a user message containing a query and a reference to message history.

    Attributes:
        message_history_id (NonNegativeInt): 
            A non-negative integer representing the message history ID.
        query (str): 
            The content of the query sent by the user.
    """
    message_history_id: NonNegativeInt
    query: str


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/schemas/sales_pipeline_schema.py =====

from pydantic import BaseModel, NonNegativeFloat
from datetime import date

class SalesPipelineSourceSchema(BaseModel):
    """
    Represents a sales pipeline entry.

    Attributes:
        opportunity_id (str): 
            The unique identifier for the sales opportunity.
        sales_agent (str): 
            The sales agent associated with the opportunity.
        product (str): 
            The product being sold.
        account (str): 
            The account linked to the sales opportunity.
        deal_stage (str): 
            The current stage of the sales deal.
        engage_date (date): 
            The date when the engagement started.
        close_date (date): 
            The expected or actual closing date of the deal.
        close_value (NonNegativeFloat): 
            The monetary value of the closed deal.
    """
    opportunity_id: str
    sales_agent: str
    product: str
    account: str
    deal_stage: str
    engage_date: date
    close_date: date
    close_value: NonNegativeFloat


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/schemas/sql_agentic_rag_schema.py =====

from pydantic import BaseModel
from typing import Literal

class SQLInjectionStatus(BaseModel):
    """
    Represents the security status of an SQL query regarding SQL injection threats.

    Attributes:
        status (Literal["Insecure", "Secure"]): 
            A status indicating whether the SQL query is "Secure" or "Insecure".
    """
    status: Literal["Insecure", "Secure"]

class SerializableChatSchema(BaseModel):
    """
    Represents a serializable chat message.

    Attributes:
        role (Literal["human", "assistant"]): 
            The role of the sender, either "human" or "assistant".
        content (str): 
            The content of the message.
    """
    role: Literal["human", "assistant"]
    content: str


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/src/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/src/database_operations.py =====

from typing import List, ClassVar
import subprocess
import os
import uuid

import fireducks.pandas as pd
from fastapi import APIRouter, Depends, Response
from sqlalchemy import MetaData, Table, Column, String, inspect, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.exc import ProgrammingError
from dotenv import load_dotenv

from core.database import engine
from core.deps import get_session
from core.configs import settings
from shared.contracts.user_input_contract import UserInput
from utils.full_dataset_preparation import full_dataset_preparation
from schemas.sales_pipeline_schema import SalesPipelineSourceSchema
from models.sales_pipeline_model import SalesPipelineSourceModel


load_dotenv()

router = APIRouter(tags=['Database Operations'])


@router.get(
    '/serve-dbt-docs/',
    status_code=200,
    description='Generate and serve DBT docs'
)
def docs_dbt() -> Response:
    """
    Generates and serves DBT documentation using the configured DBT path.

    Returns:
        Response:
            A FastAPI response indicating the success or failure of the operation.
    """
    original_dir = os.getcwd()
    try:
        dbt_path = settings.DBT_PATH
        if not dbt_path:
            raise ValueError("DBT_PATH environment variable is not set.")

    except ValueError as e:
        print(f"Configuration Error: {e}")

    os.chdir(dbt_path)

    try:
        _ = subprocess.run(
            ["dbt", "docs", "generate"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        _ = subprocess.run(
            "dbt docs serve --host 0.0.0.0 --port 8080 > /dev/null 2>&1 &",
            shell=True,
            check=True
        )

    except subprocess.CalledProcessError as e:
        print("Error occurred while running dbt:")
        print(e.stderr)
    except Exception as e:
        print(f"Unexpected error occured generating or serving docs: {e}")
    finally:
        os.chdir(original_dir)
        return Response(status_code=200)


@router.post(
    '/run-dbt/',
    status_code=200,
    description='Run DBT models for data transformation and agregation'
)
def run_dbt() -> Response:
    """
    Executes DBT models to transform and aggregate data.

    Returns:
        Response:
            A FastAPI response indicating the success or failure of the operation.
    """
    original_dir = os.getcwd()
    try:
        dbt_path = settings.DBT_PATH
        if not dbt_path:
            raise ValueError("DBT_PATH environment variable is not set.")

        os.chdir(dbt_path)

        result = subprocess.run(
            ["dbt", "run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )

        print("DBT Run Output:")
        print(result.stdout)

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except subprocess.CalledProcessError as e:
        print("Error occurred while running dbt:")
        print(e.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        os.chdir(original_dir)
        return Response(status_code=200)


@router.post(
    '/create-run-won-stage-data/',
    status_code=200,
    description='Insert data to Postgres database given a user input.'
)
def create_run_won_stage_data(
    schema:str, 
    session=Depends(get_session)
) -> Response:
    """
    Prepares and inserts processed data into the PostgreSQL database.

    Args:
        schema (str):
            The database schema where the data will be stored.
        session (Session):
            The database session dependency.

    Returns:
        Response:
            A FastAPI response indicating the success or failure of the operation.
    """
    try:
        model_predictions_summary, customers_rfm_features, general_enriched_dataset = full_dataset_preparation(session)
        all_dataframes = [model_predictions_summary, customers_rfm_features, general_enriched_dataset]
        dataframe_names = ['model_predictions_summary', 'customers_rfm_features', 'general_enriched_dataset'] 

        for df, name in zip(all_dataframes, dataframe_names):
            table_name = f"{name}_source"

            with engine.connect() as conn:
                try:
                    conn.execution_options(isolation_level="AUTOCOMMIT").execute(
                        text(f"DROP TABLE IF EXISTS {table_name} CASCADE;")
                    )
                    print(f"Table {table_name} successfully removed.")
                except ProgrammingError as e:
                    print(f"Error trying to remove the table {table_name}: {e}")

            result = df.to_sql(
                table_name,
                con=engine,
                schema=schema,
                index=False,
                if_exists="replace"
            )
            
            if result:
                print(result)
                print('Tables added successfully')
            else:
                print("Didn't add tables")

        # Creating or updating the database views of medallion architecture
        run_dbt()

    except Exception as e:
        session.rollback()
        raise e

    return Response(status_code=200)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/src/historic_messages.py =====

from fastapi import APIRouter, Depends

from models.historic_messages_model import Message
from core.database import engine
from core.deps import get_session
from core.configs import settings
from chat.services import chat_history_from_id


router = APIRouter(tags=['Chat'])


@router.post(
    "/historic-message/",
    status_code=200,
    description="Return historic messages from the chat"
)
async def historic_message(
    message: Message,
    session=Depends(get_session)
):
    """
    Retrieves historical messages from a chat session.

    Args:
        message (Message):
            The message object containing the chat history ID.
        session (Session):
            The database session dependency.

    Returns:
        chat (list):
            A list of messages from the chat history.
    """
    with session:
        chat = chat_history_from_id(
            message_history_id=message.message_history_id,
            session=session
        ).to_list()
        
        session.commit()

    return chat


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/src/rag_operations.py =====

from datetime import datetime
from typing import Literal
import copy
from typing import List

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, Response
from langchain_openai import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate

from core.database import engine
from core.deps import get_session
from core.configs import settings
from utils.tables_metadata_prompt import TABLES_METADATA, generate_tables_metadata_prompt
from chat.services import (chat_history_from_id,
                           save_user_message_in_chat,
                           save_assistant_message_in_chat)
from schemas.historic_messages_schema import Message
from schemas.sql_agentic_rag_schema import SQLInjectionStatus, SerializableChatSchema

load_dotenv()

router = APIRouter(tags=['RAG Operations'])

@router.get(
    '/verify-sql-injection/{query}',
    status_code=200,
    response_model=SQLInjectionStatus,
    description="Specialized Agent that verifies SQL injection based on the user's query"
)
def verify_sql_injection(query: str) -> SQLInjectionStatus:
    """
    Identifies whether a given SQL query is a potential SQL injection attempt.

    Args:
    query (str):
        The SQL query input from the user.

    Returns:
        SQLInjectionStatus:
            A status indicating whether the query is "Secure" or "Insecure".
    """
    examples = [
        {
            "input": "1; DROP TABLE users; --",
            "result": "Insecure, attempt of SQL Injection",
        },
        {
            "input": "SELECT * FROM users WHERE id = 1",
            "result": "Secure",
        },
        {
            "input": "' OR '1' = '1",
            "result": "Insecure, attempt of SQL Injection",
        },
    ]
    example_prompt = ChatPromptTemplate.from_messages(
        [
            ("human", "{input}"),
            ("ai", "{result}"),
        ]
    )
    few_shot_prompt = FewShotChatMessagePromptTemplate(
        example_prompt=example_prompt,
        examples=examples,
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                You are an expert in cybersecurity. 
                Your task is to identify whether a user input query is an attempt of SQL Injection in our database.
                Follow these examples to assist in identifying potential SQL Injection attempts:
                """,
            ),
            few_shot_prompt,
            ("user", "{input}"),
        ]
    )

    class ChooseQueryStatus(BaseModel):
        status: Literal["Insecure", "Secure"] = Field(
            ...,
            description="Given a user input, determine if the query is Secure or Insecure.",
        )

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    structured_llm = llm.with_structured_output(ChooseQueryStatus)
    chain = prompt | structured_llm

    result = chain.invoke({"input": query})
    return {'status': result.status}


@router.post(
    '/text-to-sql/',
    status_code=200,
    response_model=List[SerializableChatSchema],
    description="Text-to-SQL agent to generate SQL queries based on user input"
)
def text_to_sql(
    message: Message, session=Depends(get_session)
) -> List[SerializableChatSchema]:
    """
    Converts natural language input into SQL queries using an AI agent.

    Args:
        message (Message):
            The user's input query in natural language.
        session (Session):
            The database session dependency, by default retrieved from `get_session`.

    Returns:
        serializable_chat (List[SerializableChatSchema]):
            A list of chat messages containing the generated SQL query and responses.
    """
    chat = chat_history_from_id(message.message_history_id, session)
    save_user_message_in_chat(message.query, chat)

    db = SQLDatabase(
        engine=engine,
        schema=settings.DB_SCHEMA,
        view_support=True,
    )

    views_to_query = [
        table
        for table in db.get_usable_table_names()
        if not table.endswith('_source')
        and not table.startswith('raw-')
        and not table.startswith('stg-')
    ]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    toolkit = SQLDatabaseToolkit(
        db=db,
        llm=llm
    )

    prompt_template = """
        You are an agent designed to interact with a SQL database.
        Below is the description of the tables and their columns that you can query:
        
        {tables_metadata_prompt}
        
        Given the input question, create a syntactically correct {dialect} query to run, 
        then look at the results of the query and return the answer.
        
        Unless the user specifies a specific number of examples they wish to obtain, 
        always limit your query to at most {top_k} results.
        
        You must first try to make a simple query on these tables: {views_to_query}. 
        If you are not sure that the user's query can be answered by the content present 
        in this list of tables, you must perform a more complex query on the centralized 
        table named 'stg-won_deal_stage'.
        
        You can order the results by a relevant column to return the most interesting examples 
        in the database.
        
        Never query for all the columns from a specific table; only ask for the relevant columns 
        given the question.
        
        You have access to tools for interacting with the database. If the user's input question 
        is related to a date, consider today's date as {today_date}.
        
        Only use the below tools. Only use the information returned by the below tools 
        to construct your final answer.
        
        You MUST double-check your query before executing it. If you get an error while executing 
        a query, rewrite the query and try again.
        
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP, etc.) to the database.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/utils/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/utils/export_models.py =====

import cloudpickle
import os
from lifetimes import BetaGeoFitter, GammaGammaFitter
from dotenv import load_dotenv

load_dotenv()
PROJECT_PATH = os.getenv("PROJECT_PATH")


def export_beta_geo_fitter(bgf: BetaGeoFitter) -> None:
    """
    Exports the BetaGeoFitter object to a pickle file.

    Args:
        bgf (BetaGeoFitter): The BetaGeoFitter object to be exported

    Returns:
        None
    """
    with open(f"{PROJECT_PATH}/models/beta_geo_fitter.pkl", "wb") as file:
        cloudpickle.dump(bgf, file)


def export_gamma_gamma_fitter(ggf: GammaGammaFitter) -> None:
    """
    Exports the GammaGammaFitter object to a pickle file.

    Args:
        ggf (GammaGammaFitter): The GammaGammaFitter object to be exported.

    Returns:
        None
    """
    with open(f"{PROJECT_PATH}/models/gamma_gamma_fitter.pkl", "wb") as file:
        cloudpickle.dump(ggf, file)


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/utils/full_dataset_preparation.py =====

import os
import random
from datetime import date, datetime

import fireducks.pandas as pd
from sqlalchemy import select
from lifetimes import BetaGeoFitter, GammaGammaFitter
from lifetimes.utils import summary_data_from_transaction_data
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sqlalchemy.orm import Session

from models.accounts_model import AccountsSourceModel
from models.products_model import ProductsSourceModel
from models.sales_pipeline_model import SalesPipelineSourceModel
from models.sales_teams_model import SalesTeamsSourceModel
from utils.export_models import export_beta_geo_fitter, export_gamma_gamma_fitter



def full_dataset_preparation(
    session: Session, deal_stage: str = 'Won', today_date: date = datetime(2018, 1, 1)
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Prepares a consolidated dataset for analysis.

    Args:
        session (Session): Database session for loading data.
        deal_stage (str): The deal stage to filter by. Default is 'Won'.
        today_date (date): Reference date for temporal calculations. Default is 2018-01-01.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: 
            - Summary data for merging.
            - RFM data for merging.
            - Consolidated dataset.
    """

    accounts_df = load_accounts_data(session)
    products_df = load_products_data(session)
    sales_pipeline_df = load_sales_pipeline_data(session)
    sales_teams_df = load_sales_teams_data(session)
    
    dataframes = [accounts_df, products_df, sales_pipeline_df, sales_teams_df]
    
    filtered_dataframes = []
    for i, raw_df in enumerate(dataframes):
        if 'id' in raw_df.columns:
            raw_df = filtered_dataframes.append(raw_df.drop(columns=['id']))
        else:
            filtered_dataframes.append(raw_df)

    accounts_df, products_df, sales_pipeline_df, sales_teams_df = filtered_dataframes
    
    sales_pipeline_df.loc[sales_pipeline_df['product'] == 'GTXPro', 'product'] = 'GTX Pro'
    
    df = (pd.merge(
            pd.merge(
                pd.merge(
                    sales_pipeline_df, accounts_df, on='account', how='inner'
                    ),
                products_df, on='product', how='inner'
                ),
            sales_teams_df, on='sales_agent', how='inner'
            )
        )

    df = make_preprocessing(df)
    
    if deal_stage == 'Won':
        df = make_won_pre_feature_engineering(df)
    else:
        raise NotImplementedError('Only "Won" deal stage analysis are implemented by now.')
    
    df = make_filter_by_deal_stage(df, deal_stage)
    rfm = make_rfm_enrichment(df, today_date)
    rfm = expand_rfm_features(rfm)

    summary, bgf = fit_predict_bg_nbd_model(df, today_date)
    summary, ggf = fit_predict_gamma_gamma_model(summary)
    summary = make_cltv_predictions(summary, bgf, ggf)
    
    summary_to_merge, rfm_to_merge = drop_duplicate_columns_for_merge(summary, rfm)

    return summary_to_merge, rfm_to_merge, df


def drop_duplicate_columns_for_merge(
    summary: pd.DataFrame, rfm: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Removes duplicate columns from DataFrames before merging.

    Args:
        summary (pd.DataFrame): Summary DataFrame.
        rfm (pd.DataFrame): RFM DataFrame.

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: 
            - Summary DataFrame without duplicates.
            - RFM DataFrame without duplicates.
    """
   
    summary = summary.drop(columns=['frequency', 'recency', 'monetary_value'])
    summary.reset_index(inplace=True)

    rfm = rfm.drop(columns=['product', 'revenue', 'Months_Since_Start', 'office_location'])

    return summary, rfm


def make_cltv_predictions(
    summary: pd.DataFrame, bgf: BetaGeoFitter, ggf: GammaGammaFitter
) -> pd.DataFrame:
    """
    Calculates and adds CLTV predictions to the DataFrame.

    Args:
        summary (pd.DataFrame): Summary DataFrame.
        bgf (BetaGeoFitter): Beta-Geometric/NBD model.
        ggf (GammaGammaFitter): Gamma-Gamma model.

    Returns:
        pd.DataFrame: DataFrame with added CLTV predictions.
    """

    summary['Predicted_Year_CLTV'] = ggf.customer_lifetime_value(
        bgf,
        summary['frequency'],
        summary['recency'],
        summary['T'],
        summary['monetary_value'],
        time=12,  # Monthly
        discount_rate=0.01,  # Monthly discount
    )

    summary['Predicted_Year_CLTV'].sort_values(ascending = False)
    summary['Predicted_CLTV_Segment'] = pd.qcut(summary['Predicted_Year_CLTV'], q=3, labels=['Low', 'Medium', 'High'])

    return summary


def fit_predict_gamma_gamma_model(summary: pd.DataFrame) -> tuple[pd.DataFrame, GammaGammaFitter]:
    """
    Fits and makes predictions using the Gamma-Gamma model.

    Args:
        summary (pd.DataFrame): Summary DataFrame.

    Returns:
        tuple[pd.DataFrame, GammaGammaFitter]: 
            - Updated DataFrame with predictions.
            - Fitted GammaGammaFitter instance.
    """

    ggf = GammaGammaFitter(penalizer_coef=0.05)
    ggf.fit(summary['frequency'], summary['monetary_value'])

    summary['expected_average_profit'] = ggf.conditional_expected_average_profit(
        summary['frequency'], summary['monetary_value']
    )
    
    export_gamma_gamma_fitter(ggf)
    
    return summary, ggf
    

def fit_predict_bg_nbd_model(
    df: pd.DataFrame, today_date: date = datetime(2018, 1, 1)
) -> tuple[pd.DataFrame, BetaGeoFitter]:
    """
    Fits and makes predictions using the Beta-Geometric/NBD model.

    Args:
        df (pd.DataFrame): DataFrame with transaction data.
        today_date (date): Reference date for calculations. Default is 2018-01-01.

    Returns:
        tuple[pd.DataFrame, BetaGeoFitter]: 
            - DataFrame with predictions.


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/api/utils/tables_metadata_prompt.py =====

from typing import List
from pydantic import BaseModel


class ColumnMetadata(BaseModel):
    name: str
    description: str

class TableMetadata(BaseModel):
    name: str
    description: str
    columns: List[ColumnMetadata]


TABLES_METADATA = [
    TableMetadata(
        name="stg-won_deal_stage",
        description="Centralized table containing enriched data for sales opportunities, customer features, and predictive model outputs.",
        columns=[
            ColumnMetadata(name="opportunity_id", description="Unique identifier for each sales opportunity."),
            ColumnMetadata(name="sales_agent", description="Sales agent responsible for managing the opportunity."),
            ColumnMetadata(name="product", description="Product associated with the sales opportunity."),
            ColumnMetadata(name="customer", description="Customer account involved in the sales opportunity."),
            ColumnMetadata(name="business_deal_stage", description="Current stage of the sales opportunity in the deal pipeline."),
            ColumnMetadata(name="business_engage_date", description="Date when the engagement with the customer began."),
            ColumnMetadata(name="business_close_date", description="Date when the sales opportunity was closed."),
            ColumnMetadata(name="business_close_value", description="Monetary value of the closed deal."),
            ColumnMetadata(name="customer_sector", description="Industry sector of the customer."),
            ColumnMetadata(name="customer_partnership_year_established", description="Year when the partnership with the customer was established."),
            ColumnMetadata(name="customer_revenue", description="Annual revenue of the customer."),
            ColumnMetadata(name="customer_number_of_employees", description="Number of employees in the customer's organization."),
            ColumnMetadata(name="customer_office_location", description="Office location of the customer."),
            ColumnMetadata(name="customer_is_subsidiary_of", description="Parent organization of the customer, if any."),
            ColumnMetadata(name="product_series", description="Series or category of the product."),
            ColumnMetadata(name="product_retail_sales_price", description="Retail sales price of the product."),
            ColumnMetadata(name="sales_agent_manager", description="Manager responsible for supervising the sales agent."),
            ColumnMetadata(name="sales_agent_regional_office", description="Regional office associated with the sales agent."),
            ColumnMetadata(name="business_sales_cycle_duration", description="Duration of the sales cycle for the opportunity."),
            ColumnMetadata(name="agent_won_deal_effectiveness", description="Effectiveness rate of the sales agent in closing deals."),
            ColumnMetadata(name="business_opportunities_per_customer", description="Number of sales opportunities associated with the customer."),
            ColumnMetadata(name="business_opportunities_per_sales_agent", description="Number of opportunities handled by the sales agent."),
            ColumnMetadata(name="customer_first_purchase", description="Date of the customer's first purchase."),
            ColumnMetadata(name="customer_last_purchase", description="Date of the customer's most recent purchase."),
            ColumnMetadata(name="absolute_customer_recency_value", description="Recency of the customer's activity."),
            ColumnMetadata(name="absolute_customer_frequency_value", description="Frequency of the customer's activity."),
            ColumnMetadata(name="absolute_customer_monetary_value", description="Monetary value associated with the customer."),
            ColumnMetadata(name="customer_recency_score", description="Score representing the recency of the customer's activity."),
            ColumnMetadata(name="customer_frequency_score", description="Score representing the frequency of the customer's activity."),
            ColumnMetadata(name="customer_monetary_score", description="Score representing the monetary value of the customer."),
            ColumnMetadata(name="customer_recency_frequency_monetary_score", description="Combined RFM score for the customer."),
            ColumnMetadata(name="customer_recency_frequency_monetary_segment", description="Segment classification based on the customer's RFM score."),
            ColumnMetadata(name="customer_engagement_score", description="Score representing the customer's overall engagement."),
            ColumnMetadata(name="actual_customer_lifetime_value", description="Actual/Present lifetime value of the customer."),
            ColumnMetadata(name="recency_frequency_ratio", description="Ratio of recency to frequency for the customer."),
            ColumnMetadata(name="customer_average_transaction_value", description="Average transaction value for the customer."),
            ColumnMetadata(name="customer_days_since_first_purchase", description="Number of days since the customer's first purchase."),
            ColumnMetadata(name="prob_alive_customer", description="Probability that the customer is still active."),
            ColumnMetadata(name="customer_expected_purchases_day", description="Expected number of purchases by the customer per day."),
            ColumnMetadata(name="customer_expected_purchases_week", description="Expected number of purchases by the customer per week."),
            ColumnMetadata(name="customer_expected_purchases_monthly", description="Expected number of purchases by the customer per month."),
            ColumnMetadata(name="customer_expected_purchases_bimonthly", description="Expected number of purchases by the customer every two months."),
            ColumnMetadata(name="customer_expected_purchases_trimester", description="Expected number of purchases by the customer per trimester."),
            ColumnMetadata(name="customer_expected_purchases_half_year", description="Expected number of purchases by the customer every six months."),
            ColumnMetadata(name="customer_expected_purchases_year", description="Expected number of purchases by the customer per year."),
            ColumnMetadata(name="customer_expected_average_profit", description="Expected average profit per customer."),
            ColumnMetadata(name="predicted_year_customer_lifetime_value", description="Predicted/Expected customer lifetime value for the upcoming year."),
            ColumnMetadata(name="predicted_customer_lifetime_value_segment", description="Segment classification based on predicted CLTV."),
        ]
    ),
    TableMetadata(
        name="sector_wise_revenue_analysis",
        description="Analysis of revenue and sales cycle duration across different customer sectors.",
        columns=[
            ColumnMetadata(name="customer_sector", description="Industry sector of the customer."),
            ColumnMetadata(name="total_revenue", description="Total revenue generated from the customer sector."),
            ColumnMetadata(name="average_sales_cycle_duration", description="Average duration of the sales cycle for the sector."),
        ]
    ),
    TableMetadata(
        name="sales_performance_analysis",
        description="Analysis of sales agent performance, focusing on opportunities, revenue, and efficiency metrics.",
        columns=[
            ColumnMetadata(name="sales_agent", description="Sales agent responsible for the opportunities."),
            ColumnMetadata(name="total_opportunities", description="Total number of distinct sales opportunities handled by the agent."),
            ColumnMetadata(name="total_revenue", description="Total revenue generated by the sales agent."),
            ColumnMetadata(name="avg_close_rate", description="Average effectiveness rate of the sales agent in closing deals."),
            ColumnMetadata(name="avg_sales_cycle_duration", description="Average duration of the sales cycle for opportunities handled by the agent."),
        ]
    ),
    TableMetadata(
        name="sales_agent_performance",
        description="Detailed performance metrics for individual sales agents.",
        columns=[
            ColumnMetadata(name="sales_agent", description="Sales agent responsible for the sales."),
            ColumnMetadata(name="total_sales_value", description="Total value of sales closed by the agent."),
            ColumnMetadata(name="average_sales_cycle_duration", description="Average duration of the sales cycle for deals handled by the agent."),
            ColumnMetadata(name="average_won_deal_effectiveness", description="Average effectiveness rate of the sales agent in winning deals."),
        ]
    ),
    TableMetadata(
        name="regional_sales_performance",
        description="Performance metrics for sales across different regional offices.",
        columns=[
            ColumnMetadata(name="sales_agent_regional_office", description="Regional office responsible for sales."),
            ColumnMetadata(name="total_sales_value", description="Total value of sales closed in the regional office."),
            ColumnMetadata(name="average_won_deal_effectiveness", description="Average effectiveness rate of agents in the regional office in closing deals."),
        ]
    ),
    TableMetadata(
        name="products_sales_analysis",
        description="Analysis of product sales, including total sales value and ranking by revenue.",
        columns=[
            ColumnMetadata(name="product", description="The name or type of the product."),
            ColumnMetadata(name="product_series", description="The series or category of the product."),
            ColumnMetadata(name="total_sales_value", description="Total value of sales for the product."),
            ColumnMetadata(name="total_opportunities", description="Total number of sales opportunities associated with the product."),
            ColumnMetadata(name="sales_rank", description="Rank of the product based on total sales value."),
        ]
    ),
    TableMetadata(
        name="customer_segmentation_analysis",
        description="Analysis of customer segmentation based on RFM scores and other metrics.",
        columns=[
            ColumnMetadata(name="customer", description="The account or identifier for the customer."),
            ColumnMetadata(name="customer_revenue", description="Total revenue generated by the customer."),
            ColumnMetadata(name="customer_office_location", description="Location of the customer's office."),
            ColumnMetadata(name="customer_recency_frequency_monetary_segment", description="RFM segment classification of the customer."),
            ColumnMetadata(name="customer_average_transaction_value", description="Average transaction value for the customer."),
            ColumnMetadata(name="customer_engagement_score", description="Engagement score for the customer."),
            ColumnMetadata(name="actual_customer_lifetime_value", description="Actual lifetime value of the customer."),
            ColumnMetadata(name="customer_expected_purchases_week", description="Expected number of purchases per week by the customer."),
            ColumnMetadata(name="customer_expected_purchases_half_year", description="Expected number of purchases over six months by the customer."),
            ColumnMetadata(name="customer_expected_purchases_year", description="Expected number of purchases over a year by the customer."),
            ColumnMetadata(name="customer_expected_average_profit", description="Expected average profit from the customer."),
            ColumnMetadata(name="prob_alive_customer", description="Probability that the customer is still active."),
            ColumnMetadata(name="predicted_year_customer_lifetime_value", description="Predicted customer lifetime value for the year."),
            ColumnMetadata(name="predicted_customer_lifetime_value_segment", description="Segment classification based on predicted customer lifetime value."),
        ]
    ),
    TableMetadata(
        name="customer_retention_analysis",
        description="Analysis of customer retention metrics focusing on active customers.",
        columns=[
            ColumnMetadata(name="customer", description="The account or identifier for the customer."),
            ColumnMetadata(name="customer_recency_frequency_monetary_segment", description="RFM segment classification of the customer."),
            ColumnMetadata(name="prob_alive_customer", description="Probability that the customer is still active."),
            ColumnMetadata(name="customer_engagement_score", description="Engagement score for the customer."),
        ]
    ),
    TableMetadata(
        name="customer_profitability_analysis",
        description="Analysis of customer profitability, including ranking within RFM segments.",
        columns=[
            ColumnMetadata(name="customer", description="The account or identifier for the customer."),
            ColumnMetadata(name="customer_revenue", description="Total revenue generated by the customer."),
            ColumnMetadata(name="customer_recency_frequency_monetary_segment", description="RFM segment classification of the customer."),
            ColumnMetadata(name="customer_average_transaction_value", description="Average transaction value for the customer."),
            ColumnMetadata(name="actual_customer_lifetime_value", description="Actual lifetime value of the customer."),
            ColumnMetadata(name="customer_expected_average_profit", description="Expected average profit from the customer."),
            ColumnMetadata(name="profitability_rank", description="Ranking of the customer within their RFM segment based on expected profit."),
        ]
    )
]

def generate_tables_metadata_prompt(metadata: List[TableMetadata]) -> str:
    """
    Generates a descriptive string for table metadata.

    Args:
        metadata: List[TableMetadata]: A list of TableMetadata objects containing table information.

    Returns:
        str: A formatted string describing the tables and their columns.
    """
    table_descriptions = []
    for table in metadata:
        column_descriptions = "\n".join(
            [f"- {col.name}: {col.description}" for col in table.columns]
        )
        table_descriptions.append(


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/home.py =====

import streamlit as st


st.set_page_config(page_title="Home", page_icon="🏠")

st.header("Welcome to the platform for querying data related to CRM!")

st.write("On your left, choose the type of query information you want!")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/pages/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/pages/add_new_data.py =====

import streamlit as st
import plotly.express as px

from utils.api_calls import api_request
from shared.contracts.user_input_contract import UserInput

st.title("CRM System for Advanced Data Analysis with a ChatBot")

sales_agent = st.selectbox('Sales agent name', [
    'Moses Frase', 'Darcel Schlecht', 'Zane Levy', 'Anna Snelling',
    'Vicki Laflamme', 'Markita Hansen', 'Niesha Huffines',
    'Gladys Colclough', 'James Ascencio', 'Maureen Marcano',
    'Hayden Neloms', 'Rosalina Dieter', 'Versie Hillebrand',
    'Daniell Hammack', 'Elease Gluck', 'Violet Mclelland',
    'Kami Bicknell', 'Rosie Papadopoulos', 'Kary Hendrixson',
    'Reed Clapper', 'Wilburn Farren', 'Garret Kinder',
    'Marty Freudenburg', 'Lajuana Vencill', 'Boris Faz',
    'Donn Cantrell', 'Corliss Cosme', 'Cassey Cress',
    'Cecily Lampkin', 'Jonathan Berthelot'])
product = st.selectbox('Select the product that was engaged', [
    'GTX Plus Basic', 'GTX Pro', 'MG Special', 'GTX Basic',
    'GTX Plus Pro', 'MG Advanced', 'GTK 500'])
account = st.selectbox('Select the customer (if known)', [
    'Cancity', 'Isdom', 'Codehow', 'Hatfan', 'Ron-tech',
    'J-Texon', 'Cheers', 'Zumgoity', 'Bioholding',
    'Genco Pura Olive Oil Company', 'Sunnamplex', 'Sonron',
    'Finjob', 'Scotfind', 'Treequote', 'Xx-zobam', 'Rantouch',
    'Fasehatice', 'Vehement Capital Partners', 'Warephase',
    'Zoomit', 'Labdrill', 'Zotware', 'dambase', 'Xx-holding',
    'Acme Corporation', 'Green-Plus', 'The New York Inquirer',
    'Mathtouch', 'Gogozoom', 'Stanredtax', 'Konmatfix',
    'Conecom', 'Golddex', 'Plexzap', 'Rundofase', 'Finhigh',
    'Funholding', 'Opentech', 'Silis', 'Goodsilron', 'Rangreen',
    'Kan-code', 'Nam-zim', 'Y-corporation', 'Bioplex',
    'Plusstrip', 'Toughzap', 'Dalttechnology', 'Ontomedia',
    'Kinnamplus', 'Statholdings', 'Umbrella Corporation',
    'Faxquote', 'Dontechi', 'Konex', 'Betasoloin', 'Domzoom',
    'Donquadtech', 'Globex Corporation', 'Plussunin', 'Condax',
    'Massive Dynamic', 'Doncon', 'Scottech', 'Gekko & Co',
    'Initech', 'Singletechno', 'Yearin', 'Lexiqvolax',
    'Zathunicon', 'Betatech', 'Bubba Gump', 'Blackzim',
    'Hottechi', 'Inity', 'Sumace', 'Zencorporation',
    'Groovestreet', 'Donware', 'Ganjaflex', 'Streethex',
    'Iselectrics', 'Newex', 'Bluth Company', 'Other'])


if account == 'Other':
    unknow_customer = st.text_input('Put the name of the new customer (if the above customers options are not available)')
else:
    unknow_customer = None

deal_stage = st.selectbox('Put the actual deal stage', ['Won', 'Engaging', 'Lost', 'Prospecting'])

engage_date = None
close_date = None
if deal_stage in ['Won', 'Lost', 'Engaging']:
    engage_date = st.date_input('Put the engage date')
    
    if not deal_stage == 'Engaging':
        close_date = st.date_input('Put the close date')

close_value = None
if deal_stage == 'Won':
    close_value = st.number_input('Put the closed value')
elif deal_stage == 'Lost':
    close_value = 0.0


if st.button('Save'):
    try:
        data = {'sales_agent':sales_agent,
                'product':product,
                'account':account,
                'unknow_customer':unknow_customer,
                'deal_stage':deal_stage,
                'engage_date':engage_date,
                'close_date':close_date,
                'close_value':close_value
        }

        deal_data = UserInput(**data)

        st.success("Data successfully saved")
        st.json(deal_data.model_dump(mode="json"))

        # Just won endpoint for now:
        api_request(
            api_url="http://localhost:8200/api/insert-won-stage-data/",
            json=deal_data.model_dump(mode="json")
        )

    except Exception as e:
        st.error(f"Error saving data: {e}")


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/pages/query_database.py =====

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
import random

from utils.api_calls import api_request
from urllib.parse import quote


def verify_sql_injection(query: str) -> str:
    """
    Checks if a given SQL query is vulnerable to SQL injection.

    Args:
        query (str): 
            The SQL query to be checked.

    Returns:
        str:
            The security status of the query ("Secure" or "Insecure").
    """
    encoded_query = quote(query)
    response = api_request(
        api_url=f"http://0.0.0.0:8200/api/verify-sql-injection/{encoded_query}",
        json=None
    )['status']

    return response


def call_rag(query: str, message_history_id: int) -> dict:
    """
    Sends a query to a RAG (Retrieval-Augmented Generation) system.

    Args:
        query (str): 
            The user's input query.
        message_history_id (int): 
            The ID of the message history session.

    Returns:
        dict:
            The response from the RAG system.
    """
    response = api_request(
        api_url=f"http://0.0.0.0:8200/api/text-to-sql/",
        json={
             "message_history_id": message_history_id,
             "query": query
        }
    )
    return response


def get_historic_message(message_history_id: int) -> list:
    """
    Retrieves the historic messages associated with a given message history ID.

    Args:
        message_history_id (int): 
            The ID of the message history session.

    Returns:
        list:
            A list of previous messages in the conversation.
    """
    response = api_request(
        api_url=f"http://0.0.0.0:8200/api/historic-message/",
        json={
                "message_history_id": message_history_id,
                "question": ""
            })
    
    return response


def write_user_and_assistant_messages(q_and_a: list[dict]) -> None:
    """
    Displays chat messages for both the user and assistant in a Streamlit app.

    Args:
        q_and_a (list[dict]): 
            A list of messages with 'role' and 'content' keys.

    Returns:
        None
    """
    for msg in q_and_a:
        owner = "assistant" if msg["role"] == "assistant" else "user"
        with st.chat_message(name=owner):
            st.write(msg["content"])


def update_historic(q_and_a: list[dict]) -> None:
    """
    Updates the chat history stored in Streamlit's session state.

    Args:
        q_and_a (list[dict]): 
            A list of messages to be added to the session history.

    Returns:
        None
    """
    if "historic" not in st.session_state:
        st.session_state.historic = q_and_a
    else:
        for msg in q_and_a:
            st.session_state.historic.append(msg)


def get_new_message_history_id() -> int:
    """
    Generates a new random message history ID.

    Returns:
        int:
            A randomly generated integer ID.
    """
    return random.randint(0, 2**16 - 1)


def return_historic() -> list:
    """
    Retrieves the chat history from Streamlit's session state.

    Returns:
        list:
            The stored message history, or an empty list if no history is found.
    """
    if "historic" not in st.session_state:
        if "message_history_id_site" not in st.session_state:
            st.session_state.message_history_id_site = get_new_message_history_id()
            return []
        else:
            response = get_historic_message(
                st.session_state.message_history_id_site)
            return response
    return st.session_state.historic


def update_last_message(msg: dict) -> None:
    """
    Updates the last message stored in Streamlit's session state.

    Args:
        msg (dict): 
            The message to be stored.

    Returns:
        None
    """
    st.session_state.last_message = msg


def return_last_message() -> list | dict:
    """
    Retrieves the last message stored in Streamlit's session state.

    Returns:
        list | dict:
            The last message, or an empty list if no message is stored.
    """
    return st.session_state.get("last_message", [])


with st.chat_message(name="assistant"):
    st.markdown("Hi! How can i help you?")

write_user_and_assistant_messages(return_historic())

if user_input := st.chat_input("Type Here"):
    status = verify_sql_injection(user_input)

    if status:
        if status == 'Secure':
            # st.success("Hi")
            response = call_rag(
                query=user_input,
                message_history_id= st.session_state.message_history_id_site
            )


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/utils/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/app/ui/utils/api_calls.py =====

import requests

def api_request(api_url: str, json=None):
    """
    Sends an HTTP GET or POST request to the specified API URL.

    Args:
        api_url (str): 
            The URL of the API endpoint.
        json (dict | None, optional): 
            The JSON payload for a POST request (None for GET requests).

    Returns:
        response (list | dict): 
            The JSON response from the API, or an empty list if an error occurs.
    """
    try:
        if json:
            response = requests.post(api_url, json=json)
        else:
            response = requests.get(api_url)
            
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as err:
        print(f"HTTP Error occurred: {err}")
        return []
    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        return []


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/shared/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/shared/contracts/__init__.py =====




===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/shared/contracts/user_input_contract.py =====

from pydantic import (
    BaseModel,
    NonNegativeFloat, 
    field_validator,
    model_validator
)
from typing import Optional
from datetime import date

class UserInput(BaseModel):
    """
    A model representing the input data from the user, with validation for various fields.

    Attributes:
        sales_agent (str): The sales agent handling the deal.
        product (str): The product being dealt with.
        account (str): The account associated with the deal.
        unknow_customer (Optional[str]): An optional field for unknown customer details.
        deal_stage (str): The current stage of the deal.
        engage_date (Optional[date]): The date when the deal was engaged.
        close_date (Optional[date]): The date when the deal was closed.
        close_value (Optional[NonNegativeFloat]): The value of the closed deal, if applicable.
    """

    sales_agent: str
    product: str
    account: str
    unknow_customer: Optional[str] = None
    deal_stage: str
    engage_date: Optional[date] = None
    close_date: Optional[date] = None
    close_value: Optional[NonNegativeFloat] = None

    @field_validator("unknow_customer", mode="before")
    def validate_unknown_customer(cls, value: Optional[str], info) -> Optional[str]:
        """
        Validates the 'unknow_customer' field to ensure it's filled if the account is 'Other'.

        Args:
            value (Optional[str]): The value of the 'unknow_customer' field.
            info: Additional information about the validation context.

        Returns:
            Optional[str]: The validated value of 'unknow_customer'.
        
        Raises:
            ValueError: If 'unknow_customer' is required but not provided.
        """
        if info.data.get("account") == "Other" and not value:
            raise ValueError("If 'Other' was selected, the field 'unknow_customer' must be filled.")
        return value

    @field_validator("close_date", mode="before")
    def validate_close_date(cls, value: Optional[date], info) -> Optional[date]:
        """
        Validates the 'close_date' field to ensure it's provided for 'Won' or 'Lost' deal stages.

        Args:
            value (Optional[date]): The value of the 'close_date' field.
            info: Additional information about the validation context.

        Returns:
            Optional[date]: The validated value of 'close_date'.
        
        Raises:
            ValueError: If 'close_date' is required but not provided for certain deal stages.
        """
        if (info.data.get("deal_stage") not in ["Engaging", "Prospecting"]) and not value:
            raise ValueError("The closing date must be entered for stages 'Won' or 'Lost'.")
        return value

    @model_validator(mode="after")
    def validate_date_difference(cls, data: "UserInput") -> "UserInput":
        """
        Validates that the 'close_date' is later than or equal to the 'engage_date'.

        Args:
            data (UserInput): The instance of the class being validated.

        Returns:
            UserInput: The validated instance of the class.

        Raises:
            ValueError: If 'close_date' is earlier than 'engage_date'.
        """
        engage_date = data.engage_date
        close_date = data.close_date
        if close_date and close_date < engage_date:
            raise ValueError("The close date must be later than or equal to the engage date.")
        return data

    @field_validator("close_value")
    def validate_close_value(cls, value: Optional[NonNegativeFloat], info) -> Optional[NonNegativeFloat]:
        """
        Validates the 'close_value' field to ensure it's greater than 0 if the deal is 'Won'.

        Args:
            value (Optional[NonNegativeFloat]): The value of the 'close_value' field.
            info: Additional information about the validation context.

        Returns:
            Optional[NonNegativeFloat]: The validated value of 'close_value'.
        
        Raises:
            ValueError: If 'close_value' is less than or equal to 0 for a 'Won' deal stage.
        """
        if info.data.get("deal_stage") == "Won" and value is not None and value <= 0:
            raise ValueError("The closing value must be greater than 0 for 'Won' stages.")
        return value


===== FILE: /root/web-archive/ai_agents_skills_library/0-platform-precursor-systems/imported/crm-ai-analysis/data/won_stage_enriched_data.json =====

{"opportunity_id":{"0":"1C1I7A6R","1":"Z063OYW0","2":"EC4QE1BX","3":"MV1LWRNH","4":"PE84CX4O","5":"ZNBS69V1","6":"9ME3374G","7":"7GN8Q4LL","8":"OLK9LKZB","9":"NL3JZH1Z","10":"S8DX3XOU","11":"ENB2XD8G","12":"09YE9QOV","13":"M6WEJXC0","14":"6PTR7VBR","15":"5J9CMGDV","16":"WF4HA5NW","17":"C5K2JP1H","18":"ADRB8OMB","19":"SBCR987L","20":"JSD4APT2","21":"5M58DTJK","22":"KNY1OSAB","23":"2STUSOFE","24":"JYKM0B00","25":"KU28360J","26":"N4SD17JR","27":"E67P9Y3Q","28":"AT3MMVIS","29":"REJ11LRY","30":"ERV0CAZ7","31":"CZVN09WN","32":"30UQWUKB","33":"97UN20YY","34":"JXLERZ9O","35":"XKMZVSN4","36":"IU8V0BZK","37":"XY42936P","38":"XRN54MBM","39":"2V848WZD","40":"HIOHX80Y","41":"LPKT07PV","42":"WPB2SLIG","43":"XUSUEAV7","44":"3TYPII47","45":"MYDUMR3R","46":"37JFKD4I","47":"25YKPHX8","48":"GIUUTBXM","49":"MFX2LR1Q","50":"DUHE9FLY","51":"7FQMSWIX","52":"C20AVXN7","53":"GS1QVWCR","54":"ZWH8FXY3","55":"AAR79NOO","56":"B6B0PNR2","57":"LXZA2OSZ","58":"513DPFX5","59":"RU023K5W","60":"BZCBQ514","61":"HEE6P0QH","62":"L8CHRJ2B","63":"V2X2KMUR","64":"NYVA2G6U","65":"FF45BXTL","66":"TTA9LYBS","67":"PAGZQH8L","68":"J7YF6DS7","69":"S5IXY4Z9","70":"JQBJMETQ","71":"0LVWSWEW","72":"D40N5I9Y","73":"051QTX8Z","74":"5D2XH04S","75":"V9E582SK","76":"UK0LEZRJ","77":"IT10CFQH","78":"8VKD2CCH","79":"2XQAKBXH","80":"7G7YLGJO","81":"GCA97W27","82":"K8FUZHOG","83":"5WJZMULK","84":"ZPYD4T9W","85":"KE9ZEDS8","86":"FP7014Z0","87":"N4HFHDMW","88":"2HFLKREC","89":"7JVTTVCO","90":"7LE19SYE","91":"J5V2M7Y1","92":"41MURAI5","93":"QHI8WRIA","94":"VPDXX5PJ","95":"PZB9NUK8","96":"A0ANOYPF","97":"0P4AAPYX","98":"O6T5WC3W","99":"0NO04P6C","100":"22OFSXBT","101":"MRXZTMM6","102":"LGI8QEC2","103":"6KZ0NCFX","104":"3SF8O9S6","105":"BADC6A9H","106":"B8E0UUZR","107":"MWWB44CC","108":"DZ3KHZSX","109":"45A57X68","110":"9SLYC4TR","111":"JLWKWQYC","112":"7QC6FOKW","113":"XA184CMW","114":"S0N7BYU3","115":"6WOMHAJM","116":"G1QGATKV","117":"6XFVQI32","118":"OGD4MDJ9","119":"4NGBUZWJ","120":"EFG5DGV5","121":"82MM4H33","122":"14PM641K","123":"1YSOZLHF","124":"E8RP9FRW","125":"787IRG9Q","126":"0TUS4NAC","127":"FAJTQMUM","128":"TWF0J0DF","129":"UQ14O415","130":"BOJSLNDG","131":"DASMR0EK","132":"A76M0OOH","133":"E1VKE2PH","134":"V5OK4V5I","135":"GJ4L5HHN","136":"9R8JWY3J","137":"0EOFVU05","138":"HNHOPL7M","139":"Y0NYI17R","140":"R4F4RGAL","141":"0ZHLQFGU","142":"40DPY158","143":"DP9E525R","144":"DBDUMQQK","145":"CNBN12RL","146":"OXL0YWEE","147":"5CSSZJF4","148":"IIS0O91J","149":"PYZZ3IS6","150":"RV3LPOYP","151":"1HVNTEPV","152":"LC85AQ1I","153":"EJMX0EIJ","154":"VR9NYBOV","155":"3U25FK08","156":"CRLK4Z1P","157":"OGENAT0L","158":"F57JWIDF","159":"LF8JZ3Q5","160":"MRGBSMQ5","161":"CBAV8ZJL","162":"6JXHEZYK","163":"WDHNR2EI","164":"4K750D6F","165":"94GI0ZJ7","166":"TODG6DEK","167":"G0ECB8FS","168":"96MZYUY0","169":"JZOKHHWN","170":"EH6I67I0","171":"JUUXF02Z","172":"OT87JDWO","173":"YHKT6YJ7","174":"H78I3TAY","175":"1ROC43JK","176":"LPZLQL48","177":"3KR50X38","178":"Q3WLHRE9","179":"NQU62K1H","180":"NAQKOU0T","181":"I3V3GUAI","182":"PN4VJDXY","183":"K9D4DQ3R","184":"9X6V79KE","185":"W1KLFNE4","186":"GD2OCW12","187":"6XO4RYXK","188":"18Y7GRPW","189":"NLB4D5BQ","190":"FCFDJIEZ","191":"YZGDW4G1","192":"LXXW3TRW","193":"8KJ3H262","194":"UYP3NNU6","195":"MOPWEMB5","196":"3EL8D4WO","197":"VOAN1NXG","198":"FKAFO8O9","199":"1XBC7M9F","200":"8IXBS90G","201":"2X45BEOS","202":"EQ8X0QTL","203":"5QD53WHF","204":"79EABK3X","205":"QZ3VV4C1","206":"62AK8UWX","207":"5QM4ORNT","208":"N5AZLQZR","209":"4T295XQL","210":"YFS5KLJJ","211":"S8GLKDB9","212":"01QKN578","213":"M0JKP0HT","214":"ZC3KKSUK","215":"3X8VLQ5G","216":"EZLXL6GL","217":"R8PEL8V8","218":"L1R32S8H","219":"J7N8J8NM","220":"A051G1B4","221":"NMDMM5YJ","222":"I93ZFHEM","223":"B2VJCVBB","224":"PC78RLUX","225":"X6GL64T5","226":"OWM3BPGW","227":"RP5PS9A5","228":"F2PW7WP2","229":"U4LRR9E9","230":"9N55D1AH","231":"WI4PODA2","232":"MZAN11FT","233":"8S6TNXYB","234":"MOLGOSGE","235":"FA1VHZSV","236":"PXQEX039","237":"RX56S6G3","238":"G4F8W039","239":"4T31MWVO","240":"83XN082U","241":"J21W3WIW","242":"52UPJFYI","243":"QOL51JIB","244":"93AGN8A6","245":"J7UNJFJL","246":"A4H5ESTU","247":"4501T63I","248":"FPNGEJRC","249":"S33WRL0Y","250":"Q7IRUJK7","251":"DTZPYISJ","252":"Y9HWSG8Z","253":"JOQCXC9Z","254":"AP7PCLAZ","255":"BIE471SO","256":"UA8AWDG4","257":"FZDRB789","258":"PC1NUL8Q","259":"F1X5ZJ7V","260":"IF7MJ88P","261":"06B7XWPC","262":"12MQ3WM8","263":"91M6FY8S","264":"0LNZRNEU","265":"NKOKUS7D","266":"I4UCA7CU","267":"1LI7ETNZ","268":"N36DEZBR","269":"IRB461Y7","270":"NM2Q3CGW","271":"5E14LG51","272":"CRX91A45","273":"ZOQ8RC86","274":"SV4SOO2K","275":"ITHR5WLF","276":"HG07LMHI","277":"2U54WYQ1","278":"1G866GH4","279":"Q5CABPMO","280":"HHBA93J5","281":"BBC3JB3H","282":"OX4P78HP","283":"72LNJRY9","284":"L0345WKB","285":"S24L8LVR","286":"JXWXEJXE","287":"W2JCRPLX","288":"1M2I2NXQ","289":"54EGR0AD","290":"VT5Y73GX","291":"8O9V7UOZ","292":"GIIC5H9X","293":"9WMU7YHD","294":"8BQMFR86","295":"DDCC6ZPK","296":"YMGWLEHY","297":"FKS9MVF6","298":"HF8ABDF6","299":"SIRC44NM","300":"7S6SHJJG","301":"ZE84UHHB","302":"2R3ZA84D","303":"LTTYTAXA","304":"ZWFPD71J","305":"T5C527Z9","306":"AEBF9M5T","307":"EV46ES18","308":"ID3IJHUS","309":"5DEO8EDS","310":"A4BBDK82","311":"4XCJP60W","312":"CDKX2A19","313":"344I60EI","314":"0IYQX303","315":"6IMUQYMN","316":"N9GAZ6B6","317":"8O3IYWSM","318":"R3OR0J5C","319":"RXV4UXRE","320":"5AKGNKX1","321":"KNLMLTJH","322":"G9GH5KV5","323":"K1RXVUG9","324":"1QT3STIA","325":"070M5M6X","326":"DFTR2O9K","327":"EJSFO67U","328":"SKTD4GGU","329":"561707V4","330":"J28ZRO9G","331":"AOOFHH6F","332":"5U9Y1P87","333":"J0Y91LUA","334":"YBRZQFEO","335":"PHR8KB1Y","336":"TBZMXKH4","337":"6389JY2H","338":"SZ81H1PM","339":"N9C0OCYY","340":"R7XZAIWS","341":"FFO5WOHT","342":"XHHJ48MJ","343":"YAR5GGA4","344":"NOVPMLOV","345":"UPHN2I1Q","346":"NN9R2Y4W","347":"A6Y1V5Z0","348":"NU8LWEWU","349":"904203D6","350":"Z0TSV030","351":"8C4QM1X6","352":"NOPI41RP","353":"AC5YXLIR","354":"HSGJKH6U","355":"4TZF9N1D","356":"IMTPZV7J","357":"6NXY7144","358":"KBKHKULU","359":"INMJIFTF","360":"FUVQ5UKB","361":"O462ARMZ","362":"6DCKCXDC","363":"QVF0JRM5","364":"Y6HNPIIT","365":"IBKRO1AN","366":"JN1ZFD18","367":"ZE7ILYKB","368":"WPGTHV8V","369":"GWAT8UWK","370":"IZD69C5Q","371":"QFU565JJ","372":"Z5BCBTAO","373":"2KKRRM1G","374":"RLUGVSNV","375":"ZKSJ1DOK","376":"RSZC6BMW","377":"O7YNBRX0","378":"VAH6Y3F6","379":"5HKAT5GS","380":"TBIW957T","381":"MSEIIH95","382":"CF1CSNPX","383":"NOXNFJ2L","384":"NN6CSUWT","385":"X69POZIN","386":"CPGCT81C","387":"P13DDOTM","388":"9ZKORPL2","389":"1ZCOKNNI","390":"BVYMJ6TD","391":"VXX8GJGY","392":"ES9L0DXE","393":"36PTGLTW","394":"6WTNSL1T","395":"PV1DISEC","396":"S6BG03TB","397":"2YOW2BI0","398":"IQ9KYZCG","399":"C4AFMVFM","400":"WK6ERCGR","401":"64DJ954O","402":"84V18DBW","403":"WFY0S4WW","404":"HA1KXAIS","405":"SNFW1FD7","406":"2EOF1QCY","407":"QY6HCHDH","408":"CZ3XOD03","409":"WVJBVA61","410":"MV9AO6WU","411":"VS2G74XQ","412":"Q37IWCG1","413":"CUR03RXO","414":"81APSLDP","415":"G2GU9DYX","416":"ZW58VIDI","417":"Q7IIF1IP","418":"AALARPLH","419":"01X8H9SO","420":"N9VYMV3W","421":"2FTB6A7I","422":"7V9A9TXZ","423":"HWDRCUYU","424":"GFV4W89I","425":"7A4AC5BC","426":"A3BK99P6","427":"NY21X16G","428":"4DW2FDX4","429":"A66X4Q2J","430":"IT9YW5RP","431":"7IZ2GMYK","432":"TTY0X4TG","433":"L8D22SSW","434":"4563ENEB","435":"4WP0VJAS","436":"60UOBOEM","437":"QPFNQYMV","438":"031BBF1I","439":"O11S2R63","440":"G13DD850","441":"WZU2OHYU","442":"RGCH6CUF","443":"JX7WZ9UP","444":"FDCEBWRI","445":"0AJ6LTZ0","446":"SVMB8M7E","447":"4Q4NBPD6","448":"K8VSDOP8","449":"YNP9PI1X","450":"3XVY4LEU","451":"8K1OGB0R","452":"QQDO45YR","453":"88KUDE6J","454":"RZ2PUH86","455":"GLVSDQQT","456":"OCLEO3CD","457":"GQCRMEIL","458":"UK2JIE61","459":"OV5X3O5I","460":"LSVMMUJ0","461":"97KFQSX1","462":"08APB75Q","463":"TPVFA5B8","464":"4E01ALB0","465":"K4HVGBVH","466":"L33YUX9V","467":"QT7LRWTN","468":"5831YZMT","469":"FOWAY95L","470":"SRZMNS79","471":"0XMB83YO","472":"4TEO0LE1","473":"5P82H5AA","474":"V751HK8R","475":"QWL218JV","476":"12M4HB7G","477":"5IES0B4B","478":"GMI6XZ4O","479":"YOQCQ4UO","480":"KOZTDBJ5","481":"8NMPO9K3","482":"RCQDGE4W","483":"I995O4XJ","484":"EOXZGSX9","485":"NJCSG7MX","486":"5Q8BQ64R","487":"L47EPGVT","488":"9GENDMWA","489":"GKLE0CDI","490":"XT9YNOV2","491":"BAOSO1I2","492":"IZDF2RTL","493":"F61DLVRS","494":"S9W53L4L","495":"12OQKSVK","496":"VC94R5H8","497":"XTKIX6I4","498":"MSE1UXKU","499":"HM334UL2","500":"L4124UJG","501":"FD8YL177","502":"UU21EYFN","503":"QSQ42Q6M","504":"PCBA3KAV","505":"ZBBMGEV4","506":"ULVXOPG3","507":"ZDZGCWX7","508":"PQJZ5Z3R","509":"7KXTF2Q6","510":"M6UEZLOQ","511":"D6T5MM04","512":"5QBQMEY5","513":"14PBBHSE","514":"P1KS5YFX","515":"7R4VL3Q8","516":"3MNZF5ZK","517":"52SANIGE","518":"73SY9EU8","519":"HVM656P3","520":"U2SW8DT1","521":"XMH4CH4Q","522":"UNLIS3RY","523":"GVFQXZLL","524":"NRYC7T45","525":"ZVR3I3F0","526":"2TKQ8B78","527":"OZ5O64KJ","528":"UCXCUP1U","529":"CKLYIFLY","530":"I3MC9XZC","531":"6CEEGQ8I","532":"P2LY9NFN","533":"94GCWI08","534":"GUMQTC3J","535":"U64RT0UF","536":"RWGSCFHR","537":"GEBVQH17","538":"3OVJXUSB","539":"DC7COE9W","540":"GQ125FX0","541":"JO52QXJ0","542":"E2NXQUWO","543":"M1QKPX6R","544":"X6LO8WPD","545":"CVKLHZEO","546":"8KJZJFJ1","547":"W560QFJL","548":"2DVE0XCM","549":"VOTOT8MK","550":"Y3ULGUD8","551":"7350YGG4","552":"BRQRF65L","553":"LB6XW39X","554":"WS9CXY7E","555":"CK0MDHHM","556":"RNUH1SI8","557":"JOQQZ5RH","558":"LIIBOUUQ","559":"UDYSM42B","560":"F835LA4P","561":"2U6QQHCC","562":"MMKMJ0WC","563":"KIHC1QJQ","564":"LTZCN1RA","565":"K4VP5HK4","566":"10R46CSK","567":"VBA34LWX","568":"FJCCTOPN","569":"LR6USOHL","570":"5VAV2TUY","571":"HTD2ME9C","572":"GHUCMUPL","573":"1LKY3B4X","574":"7Y5E0RDL","575":"BEQIZZ7W","576":"YJIH415V","577":"G9565UWZ","578":"2BWZLXZ8","579":"2QHRL8CW","580":"LCW83256","581":"QCY951QA","582":"09BVA55J","583":"JLK8KCNN","584":"SZQUBIMH","585":"8ZYVKQ27","586":"4B4XCPHT","587":"5JFOA4XC","588":"QTNPGKJ7","589":"4PKHDQOQ","590":"3Y9SB2QK","591":"5MZ0O77T","592":"2EILEDKF","593":"J4NX9TK5","594":"5ITSLO0E","595":"WJC5J533","596":"XGLMCTLG","597":"IVT0S1N1","598":"NHDTSMX2","599":"PNL17RE9","600":"5EKN0BFN","601":"R4LH95QS","602":"REDGEUCP","603":"6KT5HAR6","604":"48AJ0X9E","605":"RA1UBXY9","606":"W4BNO6UL","607":"3H80RIHV","608":"L5U7OT6O","609":"FNY6F0KF","610":"1W23LEWK","611":"JHJEQ1U3","612":"CPJAA632","613":"9OLYBVNE","614":"R8N49PHN","615":"P5EVJUKQ","616":"24UTFDPK","617":"ERYLM04D","618":"IQ9W1X36","619":"GSR9PIF0","620":"8477482V","621":"VFZOL6CB","622":"75ZOJ3O7","623":"DR6MQSWL","624":"KAV5TU8X","625":"A82DG6R5","626":"37FKT2ZP","627":"M2TZSYTN","628":"KGJL5GHX","629":"IF7DSONM","630":"RR4FWSVB","631":"C5IWM5VJ","632":"9WZ3I1TF","633":"IO4GTLAB","634":"U185INDA","635":"2AGLONC4","636":"TBDUMBLA","637":"0AXGVKN8","638":"TAPNNL1W","639":"R9ZAKBFE","640":"Y40ADYX7","641":"RSEDY99J","642":"Z0BGG6IJ","643":"ZCA1IRGD","644":"HJIO57TA","645":"U6N053E1","646":"MTKCJVFO","647":"KIP060D0","648":"QU4FNKZL","649":"GZUKDP7F","650":"S519S1EK","651":"AL554AUI","652":"MCWDHOBT","653":"P3VM7655","654":"G17JEA75","655":"BGU0JJ9X","656":"U02OIJGK","657":"3N7ZXGMF","658":"0QHI3KG5","659":"0WWDVOM3","660":"QPPUCKFM","661":"56XQOTXV","662":"AK2LRFXF","663":"UCK7JRXG","664":"WM30CUBE","665":"BGNB966A","666":"YQ24IWRQ","667":"4A189ZAB","668":"GBMHNLRO","669":"NAVG0P26","670":"GK0A4IQW","671":"UXJSIAVS","672":"KR4K652E","673":"VTT447YT","674":"STTAXKIU","675":"87MEZS8G","676":"SLIWHUIM","677":"XBVFZ1IR","678":"7B3J333S","679":"3N9I1WH7","680":"ZI1MPYF3","681":"L6KOBEBZ","682":"Z2S4KUPO","683":"GIW1PN4L","684":"E57F5Z2K","685":"38KKSE72","686":"4V0S4BA3","687":"1LTD5TKV","688":"VBM56CIF","689":"PDH2NPE1","690":"2OAIXF3A","691":"FBSEA94D","692":"EOB01PRO","693":"5QC9H4C2","694":"3HGQ3BOY","695":"CO6ZPH1W","696":"M3WTE943","697":"X914SMX7","698":"1MCE2AOV","699":"8061HKKB","700":"T1HIH384","701":"FM2NX2GB","702":"SJ45HNHM","703":"NYGZJYCJ","704":"6MMFIIGE","705":"NKL5SWX3","706":"WVG1CIHX","707":"7GRNFO6D","708":"G0QKNVIJ","709":"6HRIX06M","710":"AM5YTMH3","711":"6B6Q8C5S","712":"DF4KYH5H","713":"O8JF46GT","714":"RK5Y67V6","715":"V28NVD6A","716":"4MC584U5","717":"MCYLHUCZ","718":"1VUBYV53","719":"W03CXYET","720":"LZVFFQLN","721":"MFV0C5RN","722":"A1WZEK7U","723":"516FJUNB","724":"PE8DK02A","725":"10NTPQUY","726":"X2EXSMPR","727":"JCFQVIEG","728":"XIWKGJOW","729":"DHGLWIDZ","730":"74VGCEEW","731":"MXTAIS4Q","732":"G20IQSA3","733":"Q16BQCEL","734":"9924I5ZF","735":"SLLJT3T1","736":"AAEUN73V","737":"32LY2D1K","738":"S2UWELRW","739":"5VQRLIEZ","740":"6U0CT07B","741":"DFN1V29L","742":"VBZ862OS","743":"VFKKSJT2","744":"FJMFXCTD","745":"JREGYB42","746":"EMUA57Q2","747":"DB3N4CHN","748":"OF7GY5F4","749":"L5807I4N","750":"Q1ZKBGV5","751":"9JKODCAU","752":"LELWKXDX","753":"JE245P8R","754":"U85VV1BU","755":"V6HB68BL","756":"H9JPB7GW","757":"SWPTTVQZ","758":"GKJLM1UR","759":"8L1ZHTPL","760":"4XX690SP","761":"JSDGELLK","762":"LV1754PS","763":"JIYYV11P","764":"6TB7XA83","765":"4T8KR12S","766":"JA0D4V57","767":"HKBAON9X","768":"7S1N6QHI","769":"CHI2T3IH","770":"X7HK448T","771":"R4L36Y0P","772":"YNKWBEEN","773":"SARVIBLS","774":"M4ZNQTEQ","775":"ITCY8YV0","776":"SAUAOZVO","777":"OJVA8ZEK","778":"UAX3F7D4","779":"7PDUWDGT","780":"3AU5SZ3V","781":"BVOO33UA","782":"M92Y63Q3","783":"PSGTTYUT","784":"JRC2PMKX","785":"FPTH6URQ","786":"S3XE14XP","787":"U6Q0T9KV","788":"HRWHRCH8","789":"8B29CRQL","790":"3KM8WN7L","791":"S0XILDHQ","792":"AZH0INTS","793":"9AMJKJX6","794":"3NQBMKOK","795":"VBG91TQH","796":"QZE24X2H","797":"WSPBQ5YR","798":"YJJ1BLPQ","799":"XUGTSB00","800":"I0TSIELX","801":"UMZ986GC","802":"RZI9HX5X","803":"WFJPWN9O","804":"S93L97VV","805":"HRU8FNE1","806":"JDFN8AZI","807":"11EK1VP7","808":"50HQRWGJ","809":"N90VSHI2","810":"21PRD9FN","811":"ITIQJARB","812":"EAUV9J9L","813":"XWEZ1WNK","814":"CJ5U6GX3","815":"HDUV7VJN","816":"5OCY2XME","817":"1YB00UYY","818":"Y23HQJRG","819":"9HXSC391","820":"ENOMNCOJ","821":"CG4TWLUR","822":"0FIG6ZP2","823":"IA62KQBO","824":"C54ZXDLT","825":"X96MMTCI","826":"P4RDU8QM","827":"7C9Q2ZA3","828":"YZ1EYM3Y","829":"M7J5BV9Q","830":"MDRX39D8","831":"7GRFWF1U","832":"CDA8Y12G","833":"RYLLRATF","834":"Y38ULZPM","835":"YFP8IZ98","836":"E5UW8AGQ","837":"EWA9JFBA","838":"MK57PHV1","839":"D01U0UR8","840":"9LFX3HBC","841":"JP3IMU5X","842":"5I8WOI8P","843":"GMVW87C4","844":"NY9ARKRE","845":"XO3XXR9X","846":"ZWAJWK40","847":"WQ0C723A","848":"396WP6JS","849":"57689GK9","850":"S2WDGIHL","851":"8VG88HMH","852":"TF7HCU69","853":"X7M4GO0J","854":"0YN6EALP","855":"A4LUP6W6","856":"KUK2H5MD","857":"UI1UION3","858":"ZPX96Q40","859":"I0CYLPNE","860":"FGH181PC","861":"8OBC9CQE","862":"2Y84YR3K","863":"97QHOOWD","864":"YL7XWUYO","865":"Q949MQ5W","866":"HZU0L5GS","867":"8RF8XVYF","868":"ZILYYA1V","869":"WBJX6O2D","870":"T14K7M5G","871":"HG07756D","872":"E7YSM99K","873":"4D1FP59D","874":"TK29F68V","875":"N3H82NHO","876":"GTANESSU","877":"LA0O6BHX","878":"RRKQ0P07","879":"J4V3VKQ5","880":"17U8549G","881":"Y34MVXP3","882":"N8G3G1UF","883":"SDXZB8MC","884":"PFUE2JYB","885":"4A8SFEJ2","886":"HEG8WPQF","887":"0FST40LV","888":"I7WERQ6B","889":"V0EIMVES","890":"DL4SZAGH","891":"RVIU1YQ8","892":"ZNSWDHTJ","893":"A2G8VYZY","894":"Y9B94N72","895":"34MBPHRL","896":"K73K8IQ3","897":"8L5WBK75","898":"Z1RN8D42","899":"JV1NCDKP","900":"ECCVMNUZ","901":"A3GVFKYP","902":"COTHR6F7","903":"3OAEEV0S","904":"RTH5O6ZW","905":"GH6U8WWN","906":"GVNI96XB","907":"KC324LPK","908":"2Y2R082L","909":"HALGOQ5D","910":"1R38Y0C1","911":"3QQW8VJ2","912":"8JS4BWQ7","913":"78TOITP2","914":"YHNBSXPN","915":"TW6D3KT4","916":"Z8RI8RLU","917":"FT0L8HZZ","918":"E96ZTKHC","919":"RZ08GKZY","920":"9U6RAS0M","921":"3S31RHE5","922":"GOM8T4Y4","923":"7Z5AVSH6","924":"E7OPE1O8","925":"647E6ED0","926":"M9OTPNII","927":"086279IX","928":"6EEC9HQQ","929":"MHN0SWM2","930":"IGELOJ42","931":"0LMA8GMJ","932":"E40RN3MN","933":"093R7PK9","934":"I8A9OXP2","935":"7IFEKEMG","936":"K2KK9SW2","937":"8SIG4C8X","938":"K4ETVW4H","939":"YA2NDY1H","940":"G6DYTQQE","941":"RZZ9K7UN","942":"YZ9ZKK3P","943":"E1921PBZ","944":"0E761F02","945":"HDBNC8W1","946":"KP6NOWM7","947":"HPYLUU5P","948":"RSFYKC1F","949":"CG65AS6X","950":"9XV6GX8D","951":"IDIMBX0N","952":"W75XU368","953":"WIY2Q0Q5","954":"4PXSBQU8","955":"QRKHWNRB","956":"1YGNHE69","957":"TAEUD0HP","958":"FCW4SAAP","959":"DEH0MYSO","960":"PEVJ6O6R","961":"T02CX0BY","962":"FHLNW3WH","963":"IAVMELUO","964":"PRMMZX9O","965":"ZZFES7ID","966":"VS0TWECS","967":"XN7EV14M","968":"P5BRH80Z","969":"CQVDJR45","970":"RW13VT8T","971":"87XTACKH","972":"0Z2CQ0MQ","973":"4SK6YLB0","974":"EVVX3PQ5","975":"9Y3JDP1B","976":"COWC9H9T","977":"ZTHMJWYZ","978":"MMGWAWBA","979":"8LPO6YCO","980":"CDUIUYY2","981":"9328IHHL","982":"ZFB7CBR6","983":"6RJE18RW","984":"GK86H0SK","985":"QXU90OP8","986":"NXXSU27K","987":"06YL7WVJ","988":"K4Y8R0FX","989":"F8O0IY28","990":"T0SEVT4K","991":"36VPT9RZ","992":"7Q7SA3EK","993":"B5CBSTM5","994":"SNBYNW8H","995":"IEN6RBZI","996":"9P026O47","997":"AJLNEUVY","998":"LJIAOC0Q","999":"HP6DSCMH","1000":"GGPSSI5Q","1001":"4D95LU0H","1002":"KA79LTFF","1003":"SGV1FR3O","1004":"TJ6U9HZ3","1005":"JYE2QFGE","1006":"QSBKLWSW","1007":"0GTJE2VQ","1008":"H91G4MYP","1009":"DDBH2FPP","1010":"N8F2PFQP","1011":"WELHHO3U","1012":"M1L0IWB6","1013":"I2U6MKUT","1014":"ECOU1XXZ","1015":"IJ4GXGCU","1016":"U0G8KIPB","1017":"TGW7OYMD","1018":"XJ9RQU4K","1019":"TJXY9DQG","1020":"J712QVSG","1021":"LCBVIPRA","1022":"WNMF0OHM","1023":"7LNGJB3S","1024":"CRW2CCMB","1025":"7FER10E1","1026":"SE609QTE","1027":"CT9XECID","1028":"SUO8VZQ8","1029":"9LX9MAPU","1030":"7XEB6TFB","1031":"KV9LW061","1032":"8RZ1A49O","1033":"V4EKF9RF","1034":"VJ1EK4A3","1035":"65B8HSTW","1036":"8PHJ7N4E","1037":"EDAJ0YEW","1038":"54JFGNXN","1039":"WLXPA3LB","1040":"3WQMBMSN","1041":"XIKWT7HM","1042":"I51MJ7PP","1043":"V690FQG4","1044":"JWRSTAU8","1045":"YYAZ4JBY","1046":"4L36DJTM","1047":"J2B3UZXA","1048":"KZKMLY96","1049":"H6NJKV4F","1050":"L69Q015M","1051":"JQ3HJFNA","1052":"XCC1C1GG","1053":"WI1HQSIS","1054":"LCTI4CFV","1055":"8GMDSXYY","1056":"QLTDWAEM","1057":"UB8M6I5R","1058":"EBTJPEEY","1059":"HRV9DSYF","1060":"MNC7Q3JJ","1061":"E3WWC6FJ","1062":"QKKZQJ46","1063":"Z72Y3C3C","1064":"FQPPZ9NQ","1065":"DUHS8KVY","1066":"M72CT8RN","1067":"XBFTCRLN","1068":"72HZ4LDT","1069":"4X3LNCWH","1070":"F481S8G3","1071":"677XNEFB","1072":"A3D8MRDX","1073":"YE6R6I1K","1074":"JXUXBANJ","1075":"GOIVV4OG","1076":"CJOU1RYX","1077":"2QQD7411","1078":"XR57MBVC","1079":"8BY9YRL9","1080":"CVPH0J04","1081":"H8CLNRM2","1082":"B85LVFR1","1083":"U8XA7JCO","1084":"AV4ZPXE3","1085":"RO6QLRCX","1086":"SKTAI2GS","1087":"3O7PIS8O","1088":"FAV4HHP4","1089":"C334XDK8","1090":"R707GGNA","1091":"EP81D4IN","1092":"UWZ7DFKY","1093":"7SH51ME1","1094":"C2WEF4XH","1095":"5G645WYV","1096":"5M3Z5DS4","1097":"CR20TBUT","1098":"M5E8U8HP","1099":"9S7VQ79A","1100":"1MQFYGEE","1101":"DLZYL69K","1102":"FRIVBOOA","1103":"7ASDRLM5","1104":"CCVCBR83","1105":"ASL3FJZP","1106":"8IJOC37Z","1107":"28BIO7F9","1108":"9ZDFLOKA","1109":"8FXUNDUS","1110":"181X64EU","1111":"5RUF6451","1112":"DF19VWL4","1113":"ZIZXHX09","1114":"JPJ3A9T8","1115":"1A86ZD0B","1116":"OFQCCQ6I","1117":"HMKFBTYR","1118":"OUR875IK","1119":"1OUHMFJV","1120":"GMNQUFQZ","1121":"YWF7W7H8","1122":"N55VF08D","1123":"265SZR01","1124":"NKO2JRRS","1125":"WW3NDCO2","1126":"DGPI60HG","1127":"06DUY829","1128":"PLM5WEY4","1129":"EWQVZB85","1130":"99AAJPQN","1131":"JW2FHT1G","1132":"08KE6ZQN","1133":"OZDJFUHH","1134":"BUPUP2TV","1135":"HTQO5XIW","1136":"W7F056RK","1137":"YAKIMBKC","1138":"FHU2WQ2K","1139":"0XIPT9AX","1140":"UURLD9W8","1141":"6YEF304L","1142":"6AALZVSE","1143":"JF9CTPPZ","1144":"LAH7932Y","1145":"ZT6XPQR0","1146":"MUHI7FIM","1147":"1WSLRC69","1148":"ZZJ4I52J","1149":"T4NRIY5R","1150":"5PA21ZHE","1151":"MCR8YCCY","1152":"8INCUUGJ","1153":"JFB4WY8C","1154":"BP7JRV1O","1155":"OREPAY0O","1156":"XBSZ29VJ","1157":"VZS17M7X","1158":"26XU4887","1159":"LGTIXQ46","1160":"KJBYGG1S","1161":"B6UWHOD4","1162":"RH805ELL","1163":"7RI58VF7","1164":"H00Y9555","1165":"RJYMI03Q","1166":"5PJJCTJ9","1167":"J60KKQ4B","1168":"X2QRD0DC","1169":"6RQCLF28","1170":"HO6M5P37","1171":"OV08QE7X","1172":"WJLJIWYS","1173":"GJQXUDI3","1174":"OOGOZGGV","1175":"C9XJ9KHD","1176":"AKT5EF0X","1177":"V7YVW4U0","1178":"QWLH0WD8","1179":"JZTX4MXK","1180":"4AHNCJ2Y","1181":"JK75NQBD","1182":"U1BDEL90","1183":"A9C9YCSN","1184":"524GC3WL","1185":"FH4VP5CL","1186":"K9MMOXUC","1187":"LV5SEMZQ","1188":"JXS3KFKM","1189":"QODSAVWU","1190":"YTL8VNGT","1191":"5UE0TE1R","1192":"RFNRVNXJ","1193":"VNCFE4LQ","1194":"VIV0OXU6","1195":"KVF0HK8S","1196":"JLT2LLR3","1197":"Z50GQV8I","1198":"O2CPAAF0","1199":"Y9XOOWHS","1200":"EFO8XWXE","1201":"HYCELUAD","1202":"LUT9KYJA","1203":"ILYP3YGW","1204":"0XC4DR3F","1205":"3ZM8BJQO","1206":"AM5J5QPK","1207":"4YH4JR1Q","1208":"NUA0OE6Z","1209":"GDOHDB6U","1210":"I58DG1XE","1211":"YA3O04NX","1212":"C2X9D7JO","1213":"SBLP2LJB","1214":"64KS4KGN","1215":"637HKAFD","1216":"FB1AO8SL","1217":"79LGX9EX","1218":"E6WG7J0I","1219":"37FL55S0","1220":"5QSU8PQU","1221":"N58V2ML8","1222":"0000I7AO","1223":"P9SDPJJO","1224":"NW6OPA4M","1225":"ZZQB2NPD","1226":"4XGA0K6N","1227":"UIFIWKNI","1228":"MBGVOGCY","1229":"2WQ5FUPR","1230":"DA6LGJ66","1231":"OJSYLHMZ","1232":"QO6CI3P4","1233":"HJP5X1MT","1234":"THMEDL51","1235":"94B4785B","1236":"E6GVZ30Q","1237":"74P8ZFDD","1238":"MB3376Q1","1239":"3N6VGWVS","1240":"KG61YJ92","1241":"Z4A1R9CJ","1242":"I6ZWBDU6","1243":"CBTC7BHL","1244":"93JCG10L","1245":"X9BUD48V","1246":"TQLJOZBP","1247":"BG2656VA","1248":"7TJEHAED","1249":"PYY9M6Q4","1250":"WAF692K8","1251":"XBLA9VO6","1252":"QL7H3WQZ","1253":"DXBLA2BS","1254":"EYW0QD8A","1255":"3M03SX77","1256":"C7Y0UUIN","1257":"DI6H5ERU","1258":"SQZ293C0","1259":"EBBIJKLT","1260":"8RIKWACO","1261":"KK7L97V7","1262":"GNKFTK7J","1263":"2FEA30KT","1264":"P2VXL7MO","1265":"YT7QY06V","1266":"L66MAMK5","1267":"RGYBSSEK","1268":"5KC9ZGBX","1269":"Q1MP64HG","1270":"XGD6BFD6","1271":"BK85705L","1272":"77MKNCO3","1273":"1B4CL153","1274":"93X2W24Q","1275":"I7KV29LC","1276":"NNM6GN1J","1277":"UFGI9P05","1278":"RDQZ245F","1279":"JA2CDNVM","1280":"R0XAJA2I","1281":"BU1B6PHK","1282":"Z29AX2KB","1283":"E733YMVH","1284":"QDRYCR05","1285":"TYWS7KJR","1286":"X22G55Y5","1287":"72WE0PUH","1288":"RU3OP2BA","1289":"LIZMTGH2","1290":"04LU4OPA","1291":"T1I8GE75","1292":"2HU581DM","1293":"6AC2ATXU","1294":"F4J6AVPQ","1295":"NFTSU7RW","1296":"NCUXZU3S","1297":"5OJ4IRW4","1298":"ZLY8SZXO","1299":"DCC85LZO","1300":"7AL9GWK6","1301":"RHXY2M2W","1302":"X501NN9P","1303":"AUDYTWRK","1304":"KPUHKYWU","1305":"B0KF3NFK","1306":"OC66D0JA","1307":"KE7SZLG7","1308":"O4LNS6IC","1309":"DIAR4IM7","1310":"SZ1H1L8I","1311":"T23MHC9C","1312":"D30QC4EE","1313":"BPUE8GTU","1314":"0PSKGNYE","1315":"J75N0QYA","1316":"SDS8SAZC","1317":"W1GERPB9","1318":"L36WU4AH","1319":"XNHGOHPW","1320":"BHT7UEDJ","1321":"7PAVX9CP","1322":"IVW8MQGN","1323":"OHVPXBSR","1324":"JBBJL4C2","1325":"HMI6RBK9","1326":"2EKGLB0Q","1327":"NBYPJR21","1328":"HYPZOTY8","1329":"31I0SB7T","1330":"TGQN6HTN","1331":"TRR34NSR","1332":"F2KINGVU","1333":"1QWG9VM6","1334":"QBCK25DV","1335":"8IEVY30X","1336":"2ZU519Y6","1337":"ZESI2PFU","1338":"X8T4XLTY","1339":"OS2CD01K","1340":"7MGVL7FC","1341":"HEDUIEUN","1342":"D3OST43E","1343":"6PMHI9G4","1344":"JQ8V4I1K","1345":"VN6JB8HU","1346":"QKQ5N9Z1","1347":"HBIQF55L","1348":"V5XB0UPL","1349":"QW9JMUTD","1350":"7ODLTF4W","1351":"RUCPPMPY","1352":"2B0QVPBT","1353":"FMNSL9TP","1354":"8ZU8D508","1355":"NVDVFYGE","1356":"QQH0YV1W","1357":"6WODV6KD","1358":"KYFONJP5","1359":"ANXSK3QV","1360":"BEP06EN5","1361":"8H95X3AP","1362":"P7LVKDC9","1363":"QRVHBQSF","1364":"8KH8XJRE","1365":"5FWBETTO","1366":"35IRGXY3","1367":"YHRVQVPV","1368":"0PGJNCD7","1369":"7X7YIWJO","1370":"2IO3IJPO","1371":"FCNYDFK3","1372":"3Y26MZHI","1373":"P0BMLVSL","1374":"QK5BW61U","1375":"D7F2AWWW","1376":"FUL5V96O","1377":"GYBIACTC","1378":"VD6BP6T2","1379":"8ZYPSX66","1380":"0AN86YDG","1381":"YGL1F8K1","1382":"EXICVP8C","1383":"DLXFY70W","1384":"F5ITRBMX","1385":"UPZRAO84","1386":"BPCWRG9P","1387":"JE5085VJ","1388":"P5MLWDXX","1389":"84T104O7","1390":"0GXXCA37","1391":"OJ0C7S3T","1392":"L3AYCTGW","1393":"IZ02GW0R","1394":"30FHAEJZ","1395":"3PPB3Q04","1396":"610UUEAG","1397":"FIYSM4E1","1398":"BCUR8B2A","1399":"8PGDRAH2","1400":"G4B4Z525","1401":"JORFI81C","1402":"GET2JILL","1403":"FCGE8U5M","1404":"ROQBT7TM","1405":"WLFLY0BD","1406":"JR7SC0S2","1407":"Y9Y4TXD9","1408":"J5DF2ZO1","1409":"9B8SPYAF","1410":"VTLI5HIE","1411":"N60UJ28O","1412":"R102IPTH","1413":"C9O4E52T","1414":"CJP7LWRK","1415":"1O1GVZEU","1416":"JHLG51ZI","1417":"TS4CB9TH","1418":"PGRIPWHY","1419":"0VXUZU7P","1420":"7B21SGQ8","1421":"PHAFVDFO","1422":"I6O855AE","1423":"OUIK8VX3","1424":"99QIJAAP","1425":"4K7PRO1B","1426":"AYB7DWUH","1427":"6CKXLPAR","1428":"FQ2F717F","1429":"LPGOTIM2","1430":"LW8485Y2","1431":"UKLAKXP2","1432":"4LLWRSBJ","1433":"5QD09R7U","1434":"K0T5LJ3E","1435":"T7MVQ9SX","1436":"D7MYDHMF","1437":"XAE858UJ","1438":"WTCU9X9M","1439":"0IF5FH68","1440":"QUGPSHY8","1441":"QNFO4GX8","1442":"H1NFMTJ4","1443":"XIXNILOP","1444":"M645P7NW","1445":"UPAGB68Z","1446":"7TCCYDR3","1447":"07BT6PBZ","1448":"JOLRMB6X","1449":"K8DHOJWM","1450":"HRLYABOS","1451":"BTLXFPUB","1452":"HBXLK0B6","1453":"ETADSAC3","1454":"8W206MO5","1455":"Z9SY11HK","1456":"TBPGQYF8","1457":"7CC38V2J","1458":"PC2V729V","1459":"7AOZ2F9R","1460":"79DYTU8Y","1461":"V4HYSJS2","1462":"1L6M83Q5","1463":"POFA8BWL","1464":"AKXBF6IQ","1465":"EBUJQ571","1466":"Z2M1XXEK","1467":"OI6UHCTN","1468":"LTOKXFP1","1469":"VPSJHIAA","1470":"MJF4D19K","1471":"JR4WED6G","1472":"GC4YH9D0","1473":"8CUN8O4Z","1474":"AMX2BM39","1475":"FK3NS3EW","1476":"3AB31BUU","1477":"ZQ7TYNUV","1478":"E223LSRZ","1479":"SW75F1Q1","1480":"0Z6MNUF2","1481":"HWD8ELR9","1482":"XJI41C0L","1483":"9FWCMMM3","1484":"XPDLW6F0","1485":"I18DIO6O","1486":"8W464DG6","1487":"FI5OA7O6","1488":"YDBPPU6J","1489":"L6PCVRJS","1490":"7EBT21IA","1491":"M7W3E298","1492":"MCRDLBIE","1493":"FX54MQFC","1494":"A2C5O4EN","1495":"79G6725X","1496":"6VET70WX","1497":"UQO59R6N","1498":"8V4PEF5D","1499":"7RJMI3GC","1500":"2ZEFCKS3","1501":"APWT2PFU","1502":"64WCPKZ1","1503":"D3G7ER0D","1504":"7FKONHLX","1505":"S439SXI1","1506":"SLP4PTFK","1507":"X3S5O9LJ","1508":"ZA6AJ0N1","1509":"GWRN1R49","1510":"Q0KYIEKA","1511":"2K7R3QHZ","1512":"WUWOHRX2","1513":"EO481IOJ","1514":"UOXKC4UG","1515":"EYZ1MNSS","1516":"KFVI73X6","1517":"88R4UBAN","1518":"08EX3XKE","1519":"4DK84UMX","1520":"735GFCU0","1521":"S87Y1DOY","1522":"EUE812O3","1523":"OBE9NAIO","1524":"XE84LNAS","1525":"RD0L0NJG","1526":"JHVY8I1M","1527":"N5QER189","1528":"AEMTQ0GH","1529":"XPJQBSLV","1530":"ZBAMKTFX","1531":"SICU0A7Z","1532":"H7GBGRSO","1533":"RLAGB32O","1534":"NYLCZ28K","1535":"3LO8XJBY","1536":"YMMQA65I","1537":"I8A539VV","1538":"DJF1XMC4","1539":"UXNB9OIB","1540":"MZILPLUE","1541":"7QIU2BCK","1542":"5ICV1IBY","1543":"H1O491SG","1544":"IRBQH4FY","1545":"ZKVVWZ8T","1546":"SAGXC5PF","1547":"J5QLUH5O","1548":"WX8KQPCM","1549":"0CSJCW8I","1550":"0WRMY7IX","1551":"N6185PK0","1552":"066V2ZGP","1553":"731TOWDY","1554":"UNSJJUY4","1555":"XNO6DQPU","1556":"IE6TPFU9","1557":"WWTJ5PNC","1558":"S2ZN5NLA","1559":"NEM0GXXH","1560":"EQZGV36H","1561":"DG6RIZ6R","1562":"9SBO74M5","1563":"WHHVN372","1564":"FWTNRN0L","1565":"TTNORNQI","1566":"BGQ2F0HA","1567":"JGXLR3H3","1568":"ZNFFFJ1T","1569":"T5JO33V3","1570":"V7Y78MPU","1571":"CNO8JPLA","1572":"Y5OTY9O5","1573":"I81SUA2R","1574":"2UHH7PD3","1575":"443ATESI","1576":"4UN65HWV","1577":"E5NRH4BP","1578":"RCNTHN0E","1579":"ZIFDD41D","1580":"FI0I7E73","1581":"523458T9","1582":"GAIFPSU2","1583":"GBSK2HX8","1584":"GYKFAK7W","1585":"GXBV5VYA","1586":"DNUTJO70","1587":"I631R5DT","1588":"OJPTGB57","1589":"QYTGB5LA","1590":"UCNEMT8P","1591":"KOFE244J","1592":"D3JR6WFQ","1593":"OJMME9V9","1594":"NLKPA1KP","1595":"38EYB40T","1596":"3FZVCDW0","1597":"2NTWE1G4","1598":"AETY0W6G","1599":"A7F5O29R","1600":"IEZCZAKT","1601":"PDMWTS8O","1602":"OPEICJES","1603":"10UN7LA8","1604":"Z032GGRE","1605":"I8WTUMTA","1606":"KTX7ETCE","1607":"JEPAVEO7","1608":"SUYF0EN7","1609":"S2D060YF","1610":"70TRVHOM","1611":"SOE904XE","1612":"C64JTLGO","1613":"F9XJYM9F","1614":"XWN6WWOD","1615":"FV6PHMQW","1616":"NX2K0HQ9","1617":"H2PEIFZH","1618":"V8M89S4W","1619":"WB974HS4","1620":"B0MOQZVN","1621":"09C4GR2W","1622":"6YN4FZHL","1623":"45CION64","1624":"BSQRXW4X","1625":"PYEQPW42","1626":"5NW73ZRY","1627":"0AR9HD16","1628":"OH7VVUY0","1629":"INI33ALF","1630":"8G9Q7NXD","1631":"559PYA0L","1632":"237L2CSV","1633":"INAEAAI9","1634":"1XNXJUQM","1635":"Z64MQTF2","1636":"VDOUNMRC","1637":"TEKCKT3V","1638":"96A1GDXO","1639":"AAU2IQFW","1640":"PRHL94PK","1641":"SHG8Y43V","1642":"1O2ZN81M","1643":"J6T6BTJI","1644":"JTTLDM4E","1645":"8KQH5XI1","1646":"A3PNPLTG","1647":"03CWYGC9","1648":"FSEF5ZR9","1649":"S9K81CWS","1650":"4NAHJMYM","1651":"HI2E8TBI","1652":"XSB7IN6X","1653":"G17H7YXA","1654":"WEB7LYK0","1655":"N4Z3QYK7","1656":"JECCHO49","1657":"QUOU67L5","1658":"WUE92JFJ","1659":"EYNZMBI0","1660":"3C5KXGO6","1661":"95532CI0","1662":"Q0MRZHN7","1663":"ZC3UEHXG","1664":"O22S564Y","1665":"UO62J3M0","1666":"ROBBKT4T","1667":"FPTY1B79","1668":"AP3405RD","1669":"FXLA39YR","1670":"WQ5WIP35","1671":"U48PDN1F","1672":"53ZXALR1","1673":"SLCWM9BH","1674":"974QGNBZ","1675":"T8E8EDZS","1676":"R034IT17","1677":"H6CG7TPM","1678":"P4GX3HZH","1679":"GACP1E2I","1680":"ASW97JK3","1681":"XBYJ3NUR","1682":"4Q2GV039","1683":"ZA1YVJQC","1684":"ZQVUQ5CJ","1685":"ZFVG8LP2","1686":"P2ST849C","1687":"6ID18IJX","1688":"7SF3PMMY","1689":"CZF82O5B","1690":"6VLA3FDQ","1691":"Z3FOWY9N","1692":"S4OLFL40","1693":"QQ96SPTU","1694":"5YLCW6L5","1695":"GO4G2L4X","1696":"9HKP3RBS","1697":"YQFF7GFK","1698":"5BAGWGAG","1699":"V1ROZMCX","1700":"CEQ3J96G","1701":"P96S0ATV","1702":"GXKR6EG9","1703":"INBSL1I4","1704":"4N2KE2ER","1705":"UJSFG18F","1706":"0MZIJDPM","1707":"FNQYVW3T","1708":"D6XIVDQF","1709":"TWXUDY78","1710":"5VKRCTJE","1711":"7DDD3NZ2","1712":"QL97HH1Y","1713":"4V3TLIGG","1714":"S9WJ9NAS","1715":"F914VHA3","1716":"1CZU97OX","1717":"4BPA17HF","1718":"LAOGNZOU","1719":"V3KGPHH9","1720":"RNH95U0V","1721":"ZJ1BOSNL","1722":"0X1AY1FM","1723":"UOUG01WG","1724":"3X2HOUYU","1725":"V135X5B7","1726":"ENE1HNL3","1727":"C8SWZNON","1728":"EXMA7FRC","1729":"8H1VRXAK","1730":"10QXTLQX","1731":"BHV4K3VV","1732":"BOHWQ1B3","1733":"KS9B13NQ","1734":"K0ZYCW3U","1735":"SFCT64YG","1736":"AVNVFAIR","1737":"TEJBT5CP","1738":"UFALPP82","1739":"NHA6MNJF","1740":"K44WX2BT","1741":"XD6R8R5B","1742":"KJP1JFKX","1743":"1F950BGI","1744":"FN080GSV","1745":"XR3BL1JL","1746":"4AS1VXQM","1747":"GYC77KNM","1748":"5BGYQS4R","1749":"YMS8IG4L","1750":"NISR8D1V","1751":"T4MF2SMF","1752":"483NKH0E","1753":"UQY5TEE8","1754":"AXHNVQPQ","1755":"N2KXGJO3","1756":"852ZZB90","1757":"V2GGEAOC","1758":"0Y8HO91H","1759":"PNUBACZM","1760":"DPT11UGS","1761":"GQFRHJF6","1762":"S8ALJKKH","1763":"HU6IS6Q2","1764":"UXFEJC9Q","1765":"D4Z6IL8W","1766":"NJCI3Y9S","1767":"OATOYNX2","1768":"0XHTFQE8","1769":"6I76NXTK","1770":"0FLFT1R4","1771":"QX4VN0WB","1772":"2G82J8WD","1773":"00KY25OA","1774":"6TN4T6HN","1775":"MQY3YOQS","1776":"3YWITFR5","1777":"BEKQZ411","1778":"PK0T5N02","1779":"E1OBRLYZ","1780":"913RPKAD","1781":"NJC209SC","1782":"MMUC1AXI","1783":"X66G66ZA","1784":"WXRWSVTT","1785":"81NOKKSW","1786":"CP3JY4PE","1787":"K2683261","1788":"0DDBDPJU","1789":"RXIQFV8D","1790":"5RGYU88R","1791":"F3P73EG4","1792":"CRLWCEMY","1793":"IQ5ASHI1","1794":"G378ZBNC","1795":"6ZVC87CV","1796":"4Y1DYANE","1797":"PGYBGBU3","1798":"GQPQ6XBD","1799":"G4KL8QWY","1800":"GIVVPRQQ","1801":"JF178AXO","1802":"43NBMRFY","1803":"UQ67214Z","1804":"HDITQL1S","1805":"1WPONGOS","1806":"ZG1DFNPW","1807":"SS9FXCS2","1808":"ZHKJIJA1","1809":"SDL8MJ4R","1810":"R8CMI00I","1811":"T7HHH8HK","1812":"407NLHJH","1813":"KD63LC6D","1814":"TB27K4GC","1815":"NFFS1KSK","1816":"V1T47SKL","1817":"M6IGBW79","1818":"2QGI573A","1819":"QW4QPPSY","1820":"99L2TNR5","1821":"7SJD7M9K","1822":"5FX5TX9L","1823":"RA77E84P","1824":"7U225819","1825":"PA55AGYL","1826":"V93ZA48C","1827":"TR3TXXHF","1828":"SURL8H49","1829":"KMGXUADZ","1830":"X58FLJ8K","1831":"7U81B9AQ","1832":"WC8KQJV9","1833":"FENOSL5C","1834":"PQ3CLZ2N","1835":"N4ZJ2PJT","1836":"HZCF65PU","1837":"TCTLOMKP","1838":"O0NCMYX9","1839":"HELQUZNO","1840":"A3OROHUS","1841":"DLQTM07N","1842":"ZT2NKCV5","1843":"I4YPNNTU","1844":"KOYW9WIV","1845":"JRAAPD3L","1846":"21JDZDNJ","1847":"EP0H3SJO","1848":"GIP11NY3","1849":"PDXFONE0","1850":"DJDVV89L","1851":"GRRY4DQR","1852":"S3JAC8GQ","1853":"E3JP7HCX","1854":"FF5G00YD","1855":"5975TDTI","1856":"GZU4ZSFE","1857":"E4KL4NGF","1858":"QCH2R1VO","1859":"DMUQAWQH","1860":"09RN3MHV","1861":"YW14K7PE","1862":"N1H9ILZ9","1863":"V8RYC18P","1864":"AR2T4LAR","1865":"GPC8PLM7","1866":"JBCQ1ODR","1867":"PLYYX5CD","1868":"JP2EY6QU","1869":"48INT6OA","1870":"9FH4OP4U","1871":"N128I4H8","1872":"8NKLCSES","1873":"1ZMWMU21","1874":"R617R51D","1875":"W8E2YLNY","1876":"TX9VFL4J","1877":"9DEDEQ5O","1878":"Z8JLMCOM","1879":"52Q1PYGW","1880":"56ZJUSNG","1881":"Y92RU9V8","1882":"SXV6VZVC","1883":"BGY307FC","1884":"BAN0BVHW","1885":"Z75R686C","1886":"12GLKKV4","1887":"VDD7H92Q","1888":"83JP1K4E","1889":"ME3H0RUJ","1890":"W8E76HJG","1891":"IMB2N710","1892":"OJBBZHM4","1893":"2PQORQGO","1894":"I3RW4OMF","1895":"LG8ZAMCB","1896":"XJ8UTM6B","1897":"CVGTFBZE","1898":"RW02HG5P","1899":"7W8CQJ2Z","1900":"M03IHS3P","1901":"GX3SHSEA","1902":"Q808L4HZ","1903":"3GOXMQPF","1904":"1WZ5N86Q","1905":"C3QK8M7F","1906":"9BXXDYH9","1907":"4X3H9YD5","1908":"K83L4L0I","1909":"E9C7WXQL","1910":"AAVJHH3M","1911":"POLWB0UX","1912":"ZSHK2ZXD","1913":"PF7GFMLQ","1914":"3R8PJCCW","1915":"CPWTJ2WC","1916":"NDVZAHYA","1917":"1R8VKE8O","1918":"LNX7ULEG","1919":"42N0IWF8","1920":"S1AU0IZX","1921":"JSNPH01N","1922":"CQDULMXS","1923":"VKM187MX","1924":"ZE7PM90V","1925":"CAAYFKK8","1926":"NQZNAEYQ","1927":"37B8ES7X","1928":"KYABDCKE","1929":"3CP9VXC1","1930":"9XGT3451","1931":"AG0H8IAZ","1932":"28FTXKAB","1933":"ROUOR5L0","1934":"QPMZ5RG0","1935":"2PMIYAFN","1936":"CRWE8FRT","1937":"6FI9HAX7","1938":"JL86Q0B4","1939":"C2MKJA8V","1940":"IJ4Y77D9","1941":"CGCPVYNI","1942":"ST8ZOXKI","1943":"P07OGZ3F","1944":"0DLEXLEV","1945":"27UN3UX8","1946":"NR5D7201","1947":"C4FEG98K","1948":"EKH5O1HH","1949":"ZT6D57ED","1950":"Q67320CY","1951":"K5NFTQRI","1952":"9WISPXZW","1953":"4ZGA57SX","1954":"JVIIWJDL","1955":"W8M8XI8Y","1956":"MELHF0ZP","1957":"6SV2WYK4","1958":"IKQSEYPT","1959":"ZN0FWO0L","1960":"CPL37MZC","1961":"GM68OLDH","1962":"GIJ14130","1963":"CUA83384","1964":"ZGQI86AQ","1965":"L8NLCWFS","1966":"JDFQYP5L","1967":"06AIY3IS","1968":"4LQAN2JX","1969":"84QGC91P","1970":"98MASV7P","1971":"QFBBRJL5","1972":"XCGW5K0N","1973":"UUF8Z53N","1974":"J6MIKNYJ","1975":"VBN5T6F8","1976":"W1J3L0EU","1977":"LDAXEBR0","1978":"NGTMVX1C","1979":"SFBHZLHK","1980":"6GY8Q8F0","1981":"5JIXFMFY","1982":"69XL3JMB","1983":"DYWMK8OF","1984":"URT8A7OQ","1985":"LGO0XF4X","1986":"Y46OEBEH","1987":"E884CL8B","1988":"KVTBYOVD","1989":"ZA6CBQAL","1990":"Y6YZXVTF","1991":"SHETLR3T","1992":"3KZUBSRU","1993":"FA6JQ4V2","1994":"9KJ89VHI","1995":"N3CN7GCZ","1996":"KAHKF9H1","1997":"IHF5GR01","1998":"81DUFIPO","1999":"EEBOSTAA","2000":"9DDHZUZB","2001":"IWLEND3K","2002":"VICY80KW","2003":"H35AXY3M","2004":"VF7DWQIH","2005":"C7NW3JB2","2006":"SUABQAC0","2007":"6JWA8DFJ","2008":"OEBJXZN6","2009":"W5P1OLUL","2010":"MASS6JEE","2011":"XNC9UMYH","2012":"AUEAKRQV","2013":"08Q8A6M9","2014":"NTHLG5DT","2015":"Y5OZ7VOF","2016":"QMJHLT1V","2017":"Q5JU0LZJ","2018":"IRODLEGG","2019":"HTA6XLY3","2020":"1BV5JLZV","2021":"NXFAXN16","2022":"FXXEZ5U2","2023":"3F81XLI7","2024":"ID4LC9V5","2025":"IPQFYK0E","2026":"UU0F81HS","2027":"7SBDZJF4","2028":"7UI7YX03","2029":"BNYWSG6W","2030":"RC1YCAEP","2031":"MU6NOSH1","2032":"OFIORN0G","2033":"PMHOZRJN","2034":"YT9PLSVL","2035":"BLFMYCVF","2036":"379SDV6Y","2037":"2756CEOQ","2038":"Z4CFFZAW","2039":"I967JINR","2040":"IE18U4NO","2041":"JNIMHE7Y","2042":"QCIG6H19","2043":"R7IIOFBH","2044":"6MTURF7Q","2045":"MWT1ZV0Y","2046":"B7Q6Q7S2","2047":"3DYZN86H","2048":"2O1IK8VR","2049":"V93EX6XU","2050":"5QNUZYIL","2051":"WX63AIMZ","2052":"09P7O0LQ","2053":"GYS3APR7","2054":"9VF00HWL","2055":"MD0SRXG4","2056":"PGK5K24U","2057":"4QP55BTO","2058":"G6X1B2K5","2059":"0YCAS0B9","2060":"6UZVABQR","2061":"9NTDQ8ZC","2062":"ALQRAPZR","2063":"7SPRU76Q","2064":"JEMEGXUG","2065":"GVHIFUN1","2066":"RBB3C85Q","2067":"8I4915WD","2068":"839DCVT2","2069":"EJ0EF8S1","2070":"0ORRC53X","2071":"3QTN3F5T","2072":"JW5SYMNS","2073":"2F0RUQ0B","2074":"XUP62FUM","2075":"MUIT1E0M","2076":"ORG6MXKF","2077":"VS4UFFLH","2078":"VUYQCXTY","2079":"YFJKP42F","2080":"V9FD3EYK","2081":"3C9CWV6J","2082":"NDGQ0H91","2083":"OU9O62Y7","2084":"3ZG0719M","2085":"EMIAKHPF","2086":"MKEVYIDI","2087":"WEGC0W05","2088":"3J1W4LM0","2089":"1RIY3IBH","2090":"DJ2GWNGZ","2091":"S02S3TVE","2092":"34YT99YN","2093":"C7NBDKVV","2094":"VUF34IPC","2095":"A50JWKFS","2096":"JP72AC6I","2097":"9SZTURAF","2098":"LB8UE159","2099":"QYWZZ16B","2100":"IJNOVBGU","2101":"QFBITAKR","2102":"VSZ4UVVN","2103":"31C5DVJT","2104":"EG3KHGPL","2105":"LSJ2A8ZX","2106":"9D06AK8T","2107":"PPXIWYMT","2108":"YWKJW726","2109":"ZVT9J7V1","2110":"NOBIC0PD","2111":"UKECBJV5","2112":"FU00L2Y2","2113":"AOZKTGZG","2114":"TKN1L8EX","2115":"9GQ6HQLK","2116":"0RL4RHQJ","2117":"ZE9WX1Q9","2118":"RUYLZD4O","2119":"3X5BD9NU","2120":"YT8YYRTU","2121":"6V7OMXY5","2122":"0TR3RU8A","2123":"GTOKTXRA","2124":"PBJ01MRE","2125":"0XWCTQL2","2126":"SY72RAK2","2127":"K7FBRQCA","2128":"F4V2FXK0","2129":"S34T8KPW","2130":"5F40OSXS","2131":"AILF7GOP","2132":"AIAX4W1O","2133":"DFSRHCXU","2134":"1VFUCUWA","2135":"3VLKZISJ","2136":"ULES5Z21","2137":"IITSDWWL","2138":"8X890G2T","2139":"HH4I6PAY","2140":"TAGD6XU9","2141":"IIREXAQX","2142":"6M89XBL0","2143":"YT2QLCVS","2144":"4ICL09BD","2145":"8TTFFCIK","2146":"OG13XT4P","2147":"KRSNQKC6","2148":"YY39ZQNV","2149":"YHVY1LHH","2150":"QQCIN1M4","2151":"KIMW6PXN","2152":"AKFNIQR0","2153":"D5LEL3HF","2154":"6X4EEUGA","2155":"KTSB1KYT","2156":"RB7IA4JX","2157":"M4HY664H","2158":"I2V3EPW7","2159":"RB8LSFVK","2160":"7SYJDW4L","2161":"O7E0302B","2162":"U11XXNCF","2163":"73FYEJQV","2164":"C4CQ8FZL","2165":"OJ1WKIVY","2166":"N9ZXCBTU","2167":"RLHNJZBW","2168":"GKHTT70P","2169":"GL8PN4LQ","2170":"NOHEK8PU","2171":"WB44DF28","2172":"DJ60T39C","2173":"52H2CE10","2174":"F57Z7KJF","2175":"ZGSQMEQ9","2176":"3NM7A8SX","2177":"1XWQZ1F8","2178":"LXGNXNX1","2179":"YQK2K6U5","2180":"FROU0UKW","2181":"SD8JJSKT","2182":"LCWP23CI","2183":"9BTSKY01","2184":"81LMZHD1","2185":"1J5Y9X1H","2186":"6LC0XB2D","2187":"PAQTBHVA","2188":"JRWBU9BS","2189":"K6ZDH79M","2190":"GKL9QV5B","2191":"BH7EXL5M","2192":"BTNSR87A","2193":"L58MN75X","2194":"SWV0JUQJ","2195":"910IXBKP","2196":"NTNYA5PE","2197":"ESH4HX52","2198":"VWSFZUNS","2199":"F3UB81V7","2200":"FLANUQCV","2201":"8MKXIQQK","2202":"E4H6CBPJ","2203":"1FAMR9UR","2204":"SYJKN818","2205":"VMTPCY5G","2206":"CV0BDYMP","2207":"7DI7A7G7","2208":"4DLOXD13","2209":"XN63KZRZ","2210":"WSG25BZ9","2211":"6GL2LRUH","2212":"K0G1IB3Q","2213":"UYJDOT4Q","2214":"VOSSIXSY","2215":"ILUMUKG8","2216":"NUNQGOUW","2217":"FUHP1IXR","2218":"TJEEFJG8","2219":"ABRQIWS9","2220":"IVCON5CU","2221":"RQXFD7FW","2222":"VE4LZ8F5","2223":"5AOWZ6AG","2224":"3AIA6RL3","2225":"9TRVSW35","2226":"GTH3VIDW","2227":"WFNKJ2LT","2228":"P7GCDFU8","2229":"ACOJBA02","2230":"FQB53DQH","2231":"1C2V9RAO","2232":"7FN6LV2E","2233":"V8I2CE9V","2234":"NYI5VMXK","2235":"Z9W748SJ","2236":"LWX9V7HI","2237":"PAQOPSR0","2238":"6BV9IARK","2239":"NTGU3NYS","2240":"3F5AAJZB","2241":"EK0KWGQX","2242":"K33NPCAY","2243":"1LLRNE8G","2244":"EFWND7VS","2245":"IR2D4ZG5","2246":"BO8DSRV7","2247":"LD1HNIUL","2248":"RX39Z0P1","2249":"ASC1OWNE","2250":"WCEPUBH5","2251":"VMIMPP6H","2252":"B0XO4WY7","2253":"VYPIKMKO","2254":"VCD47XNB","2255":"8QH99OEZ","2256":"1DMERFNB","2257":"FR8FT0ZX","2258":"DG7LABPD","2259":"ZMYUFTS9","2260":"P60EK5NN","2261":"YRYMSUE3","2262":"UZOTC90C","2263":"JFHKBG40","2264":"RJD0D0GD","2265":"L9IXFTIL","2266":"48FB5MD2","2267":"BLY5FD3N","2268":"A60QAIT3","2269":"RQ3BV2I5","2270":"0W6S0ODT","2271":"557JX4BM","2272":"VRSTX620","2273":"Y6IIUECA","2274":"LXWQDEU3","2275":"P1E4KWF7","2276":"R8MZ10BW","2277":"PI8RROK0","2278":"KDRIBXNQ","2279":"TCK6V290","2280":"UKSS5YPE","2281":"Z3QJESWJ","2282":"PYIQ65W0","2283":"RGRUF328","2284":"EFA9E6WV","2285":"YTSX7IW3","2286":"CMD0758L","2287":"CM5MFWCO","2288":"0MNAGD91","2289":"LBZY9VUG","2290":"6UUTR15S","2291":"9SRU5CI6","2292":"CM2GVLV6","2293":"NZB45UZX","2294":"T2J83GFD","2295":"28S2Z15A","2296":"EUOA0E47","2297":"NMN9DVEV","2298":"95V8BLR2","2299":"81DXTTI5","2300":"95B6AKI1","2301":"N1G2CFCB","2302":"40VSPND6","2303":"7RPM84Y4","2304":"LFN6XPK7","2305":"18LZY55R","2306":"UQALCAIV","2307":"6E2Y3HKI","2308":"ZRZI054E","2309":"CN69EYQ1","2310":"NX4ODZY2","2311":"L2QMWU4H","2312":"XVYL67FL","2313":"G1303HIC","2314":"HVDQ4EEA","2315":"2RB900SL","2316":"AUS25SFH","2317":"Q3HYAWDW","2318":"94TA0AWF","2319":"G1XX0IB4","2320":"VIMY08JH","2321":"WPTNE0QN","2322":"DLGW8Y7B","2323":"HM4TKVET","2324":"Q81Q0PJK","2325":"Y5HR9J3G","2326":"STYLQ47K","2327":"6CFONO4W","2328":"RKT3WVBC","2329":"07WKR17A","2330":"7GM1XD9W","2331":"QM6GJ78P","2332":"DQ0DSK7P","2333":"MIX6JTSN","2334":"9KYX5G9K","2335":"KWYKKVJC","2336":"T7TDUK3T","2337":"42YPT5L7","2338":"ACZQMAR4","2339":"TP9IE6PV","2340":"8H19L55Y","2341":"TPNU79C1","2342":"TFQR150O","2343":"6FUPOO3I","2344":"K1OBT27J","2345":"5CFCTZ5K","2346":"EG5M02ZV","2347":"5UKQ16DK","2348":"C9M5B1N6","2349":"ZS4PKX65","2350":"Y5CP83V4","2351":"9Y2HDGST","2352":"7R0G2LC1","2353":"8FX574BJ","2354":"AU5Q1XCW","2355":"CUMYWQYP","2356":"29ZDUK49","2357":"CMCVD0N8","2358":"NNKWGFDH","2359":"YC6QEUJN","2360":"794XWMYE","2361":"FHK0BBGK","2362":"461LIUS7","2363":"Y9SCLUH8","2364":"J75Y9C75","2365":"PUP6JDT9","2366":"G087QT6R","2367":"PUTILZZG","2368":"QU7MSL36","2369":"FEGSJ8QI","2370":"1SKIPYI7","2371":"66Q03Q2P","2372":"ZZCKQ2JV","2373":"F3G00C56","2374":"9824T94P","2375":"B8TD9HCN","2376":"PEFTXK4Q","2377":"LUIEQRMQ","2378":"8QOUXQEV","2379":"6SC26SGG","2380":"2Y9R7T2W","2381":"8U5GBXK1","2382":"G2EECJNG","2383":"UZN5JBF3","2384":"2CZVRGQ4","2385":"K5D2IP27","2386":"4HP16LRH","2387":"MNTHSHH6","2388":"5J1C46RJ","2389":"0BSYDRMT","2390":"NKERC6IA","2391":"H6AN87LE","2392":"0XK80WX8","2393":"X4ARE2PT","2394":"7T9J42UX","2395":"2J649YC5","2396":"9N66Q1VO","2397":"ZWXKCHOO","2398":"4QTD5X53","2399":"2IQ0ZY9W","2400":"N3TUSU37","2401":"O6LVMQ5R","2402":"LYAFXO9B","2403":"SNY2UWJ2","2404":"UFIAFP10","2405":"MG7CZFIG","2406":"H4U50AEW","2407":"8PU9FIQS","2408":"MJ12SZ89","2409":"B6F9PSRN","2410":"TKKSOBRC","2411":"AX63HIS9","2412":"YY3ACGA2","2413":"019I751P","2414":"PI0FYKXU","2415":"I7QSO0VZ","2416":"5AU1SJA7","2417":"A9Q7ERA4","2418":"0D95JSVW","2419":"CMLYDJFN","2420":"6TBAKLMX","2421":"OHJGW03I","2422":"AJQC76NI","2423":"PH5GSB37","2424":"9OLZU3WB","2425":"JDXET5H9","2426":"AHIDE6VS","2427":"YZJLPVJG","2428":"M3MJY0CK","2429":"H2HNTSIP","2430":"RABLXW5E","2431":"TJTOVN5K","2432":"1IG94UUQ","2433":"MN8UHP5B","2434":"D7JDQB12","2435":"GWI45VGH","2436":"G3TZD0CB","2437":"WXCEZ7JY","2438":"WR45SVGN","2439":"WAFSPTW6","2440":"3AX6QBR3","2441":"24OSGLGF","2442":"AUPXRV8O","2443":"CI00UV0Y","2444":"TS2JEK3E","2445":"4R0TB2CL","2446":"XGMMHWZC","2447":"7MK55ULJ","2448":"0VZIDVCC","2449":"YTQH4YM9","2450":"IG734VZK","2451":"W3C2KLXD","2452":"IZJR1WDM","2453":"5MRPZ44K","2454":"KDDN1E4O","2455":"S8JALB62","2456":"J3N73B00","2457":"09W047QT","2458":"VXOZC2CN","2459":"JAMW5SWB","2460":"GVCWDG9Y","2461":"UEXJN3Y6","2462":"MCQGU5EA","2463":"M0IN22XH","2464":"IEB855X8","2465":"R9V8QAPK","2466":"BXOIQHTS","2467":"K8VBNOW9","2468":"3GEDSDVN","2469":"R0ZYAJFM","2470":"CDGA1SD7","2471":"SBILEY2W","2472":"JMTKEPXF","2473":"937CNF5D","2474":"EQ399D3M","2475":"E7TDBIDS","2476":"LXDCC260","2477":"1Z72JRDI","2478":"MON3JWUF","2479":"PMVKMS6A","2480":"611J0LEK","2481":"ZWA2ES4F","2482":"CPQ348W9","2483":"UZ0MRAFU","2484":"GE5SORJX","2485":"03O9FNTZ","2486":"FIQIRK37","2487":"M6J6VNVQ","2488":"ZPKCSV3R","2489":"PMQCN4PR","2490":"CBIFB5BB","2491":"BSVZWUXR","2492":"PU2UJDTV","2493":"LN9NU0A8","2494":"FN50OJHN","2495":"90K2ZTKB","2496":"Y1GEH2EG","2497":"4MTCQ31T","2498":"COGZW25D","2499":"BOG3D6D7","2500":"J03H7OQF","2501":"DJXM9LIW","2502":"6XH71PH8","2503":"AW1U6QKR","2504":"MAVEITJH","2505":"GUJNYTXN","2506":"ELLLRB7A","2507":"F4EHCQIC","2508":"00XBYXIB","2509":"SHS9HQX4","2510":"S9DVJGUO","2511":"UIA0FO51","2512":"48J7F1A2","2513":"045D5MZO","2514":"K1UREXI5","2515":"M7Y1LHHA","2516":"SGI5I4X1","2517":"U07VUUGP","2518":"SEC6K7X2","2519":"MXVBWIE5","2520":"794F5VJB","2521":"TNEB1XNK","2522":"P60PIE95","2523":"NC7V5K1T","2524":"XTAPYDDI","2525":"0CTHPQGT","2526":"02SSRMSA","2527":"HBJPBF3P","2528":"OUMM04QV","2529":"66KFPHBT","2530":"6178B4JM","2531":"WC7KCJ2N","2532":"9GOWJ93R","2533":"9B9VDAFU","2534":"L9F6QP4P","2535":"1D5AYQO6","2536":"6WR7JQ3C","2537":"MN34I4DD","2538":"9CQ6TMET","2539":"0FGWN6O0","2540":"8IGYTN3H","2541":"OTNZ5ZCN","2542":"DKUVKTIT","2543":"X2EH33CU","2544":"U3ZMURXR","2545":"KHWG1W75","2546":"MWAW08I7","2547":"0QV1LRME","2548":"VBRZZAP8","2549":"JR76K5YA","2550":"RGUC0V54","2551":"M93A8LTF","2552":"6XLFG3VK","2553":"856VG3CS","2554":"J80ZEYYM","2555":"HUNM56HY","2556":"SIONXEMH","2557":"BUJ1TX7Y","2558":"6C70OX62","2559":"3N6BHLN6","2560":"32K5LEDV","2561":"XW1ONOVO","2562":"YYRYSVOO","2563":"GC1TSADL","2564":"QF1I965E","2565":"YKBRF0NG","2566":"OP2DIRC2","2567":"IC4J0BIZ","2568":"BNMJAOF4","2569":"VSWHUBD0","2570":"7ZWN0JO9","2571":"U3M8XTMY","2572":"P89VI9EN","2573":"185PGG0J","2574":"8EF4D82U","2575":"2X86737Q","2576":"HSZOPWWT","2577":"1KVGSF08","2578":"516C0X9F","2579":"DDD515FB","2580":"8M6TB2ZX","2581":"9CE6F4NZ","2582":"Z9KNL9A1","2583":"7JBR36G8","2584":"EYTBRK2B","2585":"SJ62BMK5","2586":"GHDAXC7T","2587":"FQQ2JJZ1","2588":"8SGMUWET","2589":"3KVS08NL","2590":"CLIIR1T0","2591":"6K7LDRKR","2592":"J6UOUH6Y","2593":"2EYTB3PX","2594":"568NS3GO","2595":"TQLO6QP6","2596":"C75RV9DY","2597":"EUQCW0ZA","2598":"TT5QRQTF","2599":"5NXD4U83","2600":"OQYDQCTM","2601":"M1VNX1D7","2602":"TWO2Q99P","2603":"72UVDOKU","2604":"DMSQ0TSG","2605":"FEWIDJGH","2606":"AUZM3MLU","2607":"GS2CLR52","2608":"HYP3SXPV","2609":"9G93P7SV","2610":"7XSAHM67","2611":"UB2UAI38","2612":"B00OD1IF","2613":"I6ZC5V1K","2614":"1N3G9WG2","2615":"JHNXPUNX","2616":"NPHD3ZTC","2617":"YCA44Q4U","2618":"FR4GTSEQ","2619":"P6BJ24ZP","2620":"ZFRPQV2M","2621":"BMQEY089","2622":"CYOJ4G39","2623":"5IOG6X00","2624":"CAXTE48L","2625":"OO3BM7A9","2626":"VE334W2U","2627":"AX7WS66G","2628":"OB8UCQ17","2629":"3L965RUK","2630":"YVGDC8L2","2631":"ZEWNPF3K","2632":"6T64JWH9","2633":"E7RTG575","2634":"I9U5PCM3","2635":"H1Y2W48V","2636":"YFNRXR7X","2637":"VBN56JMP","2638":"7ITUU2YO","2639":"6ALH2N0I","2640":"QABD6SAS","2641":"GUJCRHYU","2642":"SHKTBB71","2643":"G0L0B1QC","2644":"O3K5RKMI","2645":"75P6HFA0","2646":"W01768VM","2647":"GOGIZWW6","2648":"DOPOI0R5","2649":"69V1WQLK","2650":"FEDXQCKJ","2651":"CKDPWHTZ","2652":"944H7LRC","2653":"F0OWRRLN","2654":"P4RLJHR3","2655":"M10S36W3","2656":"GR
