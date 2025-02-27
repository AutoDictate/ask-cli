import os
import time
from dotenv import load_dotenv, set_key, find_dotenv
import google.generativeai as genai
import typer
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.markdown import Markdown
from InquirerPy import inquirer

# Suppress gRPC warnings
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

# Load environment variables
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    dotenv_path = ".env"  # Ensure a default path for saving later

app = typer.Typer()
console = Console()

# Ensure API key is set
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    console.print("[red]Error:[/red] Set your Gemini API key using 'export GEMINI_API_KEY=your_api_key'")
    exit(1)

# Configure API key
genai.configure(api_key=GEMINI_API_KEY)

# Load saved model from .env
CURRENT_MODEL = os.getenv("CURRENT_MODEL")

def save_current_model(model_name):
    """Save the selected model to the .env file."""
    global CURRENT_MODEL
    CURRENT_MODEL = model_name
    set_key(dotenv_path, "CURRENT_MODEL", model_name)  # Save to .env

@app.command()
def models():
    """Fetch available Gemini models and allow selection."""
    global CURRENT_MODEL
    try:
        models = genai.list_models()  # Get available models
    except Exception as e:
        console.print(Panel(f"[bold red]Error fetching models: {e}[/bold red]", title="Error", border_style="red"))
        return

    model_choices = [model.name.replace("models/", "") for model in models]

    if not model_choices:
        console.print("[red]No models found![/red]")
        return

    # Interactive selection
    selected_model = inquirer.select(
        message="Select a Gemini model:",
        choices=model_choices,
        default=CURRENT_MODEL if CURRENT_MODEL in model_choices else model_choices[0],
    ).execute()

    # Save the selection
    save_current_model(selected_model)

    console.print(f"\n✅ Selected model: [green]{CURRENT_MODEL}[/green] (Saved to .env)")

@app.command("q")
def ask(question: str):
    """Ask AI a question using Google Gemini AI"""
    if not CURRENT_MODEL:
        console.print(Panel("[bold red]Select a model using 'models' command first![/bold red]", title="🚨 Error", border_style="red"))
        return
    
    try:
        model = genai.GenerativeModel(CURRENT_MODEL)

        console.print(Panel(f"[cyan bold]{question}[/cyan bold]", title="🧐 You Asked", border_style="cyan"))

        response = model.generate_content(question, stream=True)
        ai_response = ""

        with Live(Panel("", title="🤖 AI Response", border_style="blue"), console=console, refresh_per_second=10) as live:
            for chunk in response:
                if hasattr(chunk, "text") and chunk.text:
                    ai_response += chunk.text
                    formatted_response = Markdown(ai_response)
                    live.update(Panel(formatted_response, title="🤖 AI Response", border_style="blue"))
                    time.sleep(0.05)

    except Exception as e:
        console.print(Panel(f"[bold red]{e}[/bold red]", title="🚨 Error", border_style="red"))

if __name__ == "__main__":
    app()
