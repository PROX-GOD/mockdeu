from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class InterviewInterface(ABC):
    """Abstract base class for interview interfaces (CLI, GUI, etc.)"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the interface"""
        pass
        
    @abstractmethod
    async def set_case_details(self, details: Dict):
        """Set case details for display (e.g. sidebar)"""
        pass

    @abstractmethod
    async def display_officer(self, text: str):
        """Display text from the officer"""
        pass
        
    @abstractmethod
    async def display_applicant(self, text: str):
        """Display text from the applicant"""
        pass
        
    @abstractmethod
    async def update_status(self, text: str):
        """Update status display (e.g. listening state)"""
        pass
        
    @abstractmethod
    async def get_input(self, prompt: str = "", options: List[str] = None) -> str:
        """Get input from the user (text selection or typed)"""
        pass
        
    @abstractmethod
    async def show_feedback(self, markdown_text: str):
        """Display the final feedback"""
        pass
        
    @abstractmethod
    def close(self):
        """Clean up resources"""
        pass
