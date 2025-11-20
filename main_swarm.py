"""
Career Concierge - Main Swarm Entry Point
Run this file to interact with the Orchestrator Agent.
"""

import os
import sys
import logging
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator_agent import orchestrator_agent

# Configure logging
logging.basicConfig(level=logging.WARNING)

console = Console()

def print_welcome():
    console.print("\n[bold blue]==========================================[/bold blue]")
    console.print("[bold blue]   Career Concierge - AI Agent Swarm      [/bold blue]")
    console.print("[bold blue]==========================================[/bold blue]")
    console.print("Welcome! I am your personal Career Manager.")
    console.print("I can help you find jobs, rewrite your CV, write cover letters,")
    console.print("and prepare for interviews. Just tell me what you need.\n")
    console.print("[italic]Type 'exit' or 'quit' to stop.[/italic]\n")

def main():
    print_welcome()

    while True:
        try:
            user_input = console.input("[bold green]You:[/bold green] ")
            
            if user_input.lower() in ['exit', 'quit']:
                console.print("\n[bold blue]Goodbye! Good luck with your career journey.[/bold blue]")
                break
            
            if not user_input.strip():
                continue

            console.print("\n[bold yellow]Concierge is thinking...[/bold yellow]")
            
            # Run the Orchestrator Agent
            response = orchestrator_agent.run(user_input)
            
            console.print("\n[bold blue]Concierge:[/bold blue]")
            console.print(Markdown(response.content))
            console.print("\n" + "-"*50 + "\n")

        except KeyboardInterrupt:
            console.print("\n[bold blue]Goodbye![/bold blue]")
            break
        except Exception as e:
            console.print(f"\n[bold red]An error occurred: {e}[/bold red]")

if __name__ == "__main__":
    main()
