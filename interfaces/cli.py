import sys
import asyncio
from termcolor import colored
from mockdeu.interfaces.base import InterviewInterface

class CLIInterface(InterviewInterface):
    """Command-line interface implementation"""
    
    async def initialize(self) -> bool:
        print(colored("\n=== MockDeu CLI Initialized ===\n", "cyan", attrs=["bold"]))
        return True
        
    async def set_case_details(self, details: dict):
        print(colored(f"\n[CASE FILE]: {details.get('name', 'Unknown')} - {details.get('visa_type', 'N/A')}", "cyan"))

    async def display_officer(self, text: str):
        print(f"\n{colored('OFFICER:', 'blue', attrs=['bold'])} {colored(text, 'yellow')}")
        
    async def display_applicant(self, text: str):
        print(f"{colored('APPLICANT:', 'green', attrs=['bold'])} {colored(text, 'white')}")
        
    async def update_status(self, text: str):
        # Use the same logic as OptimizedSTTClient._print_status
        max_len = 90
        if len(text) > max_len:
            text = "..." + text[-(max_len-3):]
        sys.stdout.write("\033[2K\r" + text)
        sys.stdout.flush()
        
    async def get_input(self, prompt: str = "", options: list = None) -> str:
        if options:
            print(f"\n{prompt}")
            for i, opt in enumerate(options, 1):
                print(f"{i}. {opt}")
            while True:
                try:
                    choice = await asyncio.to_thread(input, f"Choice (1-{len(options)}): ")
                    idx = int(choice.strip()) - 1
                    if 0 <= idx < len(options):
                        return str(idx + 1) # Return 1-based index as string for compatibility
                except ValueError:
                    pass
                print("Invalid choice, try again.")
        else:
            return await asyncio.to_thread(input, f"{prompt} ")

    async def show_feedback(self, markdown_text: str):
        print(colored("\n--- FEEDBACK SNEAK PEEK ---", "yellow"))
        lines = markdown_text.split('\n')
        for line in lines[:20]:
            print(line)
        print(colored("...", "yellow"))
        
    def close(self):
        pass
