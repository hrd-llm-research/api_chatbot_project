from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from .database import Base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public'}  # Specify schema
      
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    profile_img = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=False)
    
    session = relationship("Session", back_populates="user", cascade="all, delete")
    opt = relationship("Opt", back_populates="user", cascade="all, delete")
    project = relationship("Project", back_populates="user", cascade="all, delete")
    model_customization = relationship("ModelCustomization", back_populates="user", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "profile_img": self.profile_img,
            "created_at": self.created_at.isoformat() if self.created_at else None,  # Convert datetime to string
            "is_active": self.is_active
        }
    
    
class Opt(Base):
    __tablename__ = "opt"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("public.users.id"))
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    expired_at = Column(DateTime, default=lambda: datetime.now() + timedelta(minutes=1))
    
    user = relationship("User", back_populates="opt", cascade="all, delete")
    
class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("public.users.id"))
    session = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="session", cascade="all, delete")
    message_history = relationship("MessageHistory", back_populates="session", cascade="all, delete")
    file_metadata = relationship("FileMetadata", back_populates="session", cascade="all, delete")
    
    def to_dict(self):
        # history_info = {
        #     "message_id": self.message_history.id,
        #     "provider_name": self.provider.provider_name,
        # } if self.provider else {}
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session": str(self.session),
            "created_at": self.created_at.isoformat(),
        }
    # def to_dict(self):
        # provider_info = {
        #     "provider_id": self.provider.id,
        #     "provider_name": self.provider.provider_name,
        # } if self.provider else {}
        
        # return {
        #     "id": self.id,
        #     "provider_id": self.provider_id,
        #     "model_name": self.model_name,
        #     "provider_info": provider_info
        # }
        
class MessageHistory(Base):
    __tablename__ = "message_histories"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("public.sessions.id"))
    history_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    session = relationship("Session", back_populates="message_history", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "history_name": self.history_name,
            "created_at": self.created_at.isoformat(),
        }
    
class FileMetadata(Base):
    __tablename__ = "file_metadata"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("public.sessions.id"))
    collection_name = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    session = relationship("Session", back_populates="file_metadata", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "collection_name": self.collection_name,
            "file_name": self.file_name,
            "created_at": self.created_at.isoformat(),
        }
    
class ModelProvider(Base):
    __tablename__ = "model_providers"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    provider_name = Column(String, nullable=False)
    
    model = relationship("Model", back_populates="provider", cascade="all, delete")
    
class Model(Base):
    __tablename__ = "models"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    provider_id = Column(Integer, ForeignKey("public.model_providers.id"))
    model_name = Column(String, nullable=False)
    
    provider = relationship("ModelProvider", back_populates="model", cascade="all, delete")
    model_customization = relationship("ModelCustomization", back_populates="model", cascade="all, delete")
    
    def to_dict(self):
        provider_info = {
            "provider_id": self.provider.id,
            "provider_name": self.provider.provider_name,
        } if self.provider else {}
        
        return {
            "id": self.id,
            "provider_id": self.provider_id,
            "model_name": self.model_name,
            "provider_info": provider_info
        }
    
class ModelCustomization(Base):
    __tablename__ = "model_customizations"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("public.users.id"))
    model_id = Column(Integer, ForeignKey("public.models.id"))
    provider_api_key = Column(String)
    temperature = Column(Integer)
    max_token = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="model_customization", cascade="all, delete")
    model = relationship("Model", back_populates="model_customization", cascade="all, delete")
    
    def to_dict(self):
        provider_info = {
            "model_id": self.model.id,
            "model_name": self.model.model_name,  # Adjust based on actual fields in `ModelProvider`
            "provider_id": self.model.provider_id,  # Adjust based on actual fields in `ModelProvider`
        } if self.model else {}

        return {
            "id": self.id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "provider_api_key": self.provider_api_key,
            "temperature": self.temperature,
            "max_token": self.max_token,
            "created_at": self.created_at.isoformat(),
            "provider_info": provider_info,
        }
    
class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("public.users.id"))
    api_key = Column(String, nullable=False)
    project_name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    chroma_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="project", cascade="all, delete")
    external_session = relationship("ExternalSession", back_populates="project", cascade="all, delete")   
    external_file = relationship("ExternalFile", back_populates="project", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "api_key": self.api_key,
            "project_name": self.project_name,
            "description": self.description,
            "chroma": self.chroma_name,
            "created_at": self.created_at.isoformat(),
        }
    
    
class ExternalSession(Base):
    __tablename__ = "external_sessions"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("public.projects.id"))
    session = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.now)
    
    project = relationship("Project", back_populates="external_session", cascade="all, delete")
    external_history = relationship("ExternalHistory", back_populates="session", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "session": str(self.session),
            "created_at": self.created_at.isoformat(),
        }
    
class ExternalFile(Base):
    __tablename__ = "external_files"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("public.projects.id"))
    file_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    project = relationship("Project", back_populates="external_file", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "file_name": self.file_name,
            "created_at": self.created_at.isoformat(),
        }
    
class ExternalHistory(Base):
    __tablename__ = "external_histories"
    __table_args__ = {'schema': 'public'}  # Specify schema
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("public.external_sessions.id"))
    history_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    session = relationship("ExternalSession", back_populates="external_history", cascade="all, delete")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "history_name": self.history_name,
            "created_at": self.created_at.isoformat(),
        }