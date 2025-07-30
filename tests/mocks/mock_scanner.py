"""
Mock scanner using the new modular architecture.
Demonstrates clean separation of concerns and SOLID principles.
"""
import logging
import sys
from pathlib import Path
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import print as rprint

# Add src to Python path for imports when running as script
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent.parent / "src"
    sys.path.insert(0, str(src_path))

# Import using relative paths when run as module, absolute when run as script
try:
    from src.core.scanner_service import ScannerService
    from src.utils.config import config
except ImportError:
    from core.scanner_service import ScannerService
    from utils.config import config

# Initialize rich console
console = Console()


def show_welcome():
    """Display welcome message with rich formatting"""
    welcome_text = Text("Scanner Proxy", style="bold blue")
    subtitle = Text("Modular Network Scanner with SOLID Architecture", style="italic")
    
    panel = Panel.fit(
        f"{welcome_text}\n{subtitle}",
        title="Welcome",
        border_style="blue"
    )
    console.print(panel)


def interactive_menu():
    """Interactive CLI menu using inquirer library"""
    questions = [
        inquirer.List(
            'operation',
            message="Select an operation",
            choices=[
                ('Dummy Operation', 'dummy'),
                ('Discover Agents', 'discover'),
                ('Exit', 'exit')
            ]
        )
    ]
    
    answers = inquirer.prompt(questions)
    return answers['operation'] if answers else 'exit'
        

def dummy_operation():
    """Dummy operation for testing with rich formatting"""
    console.print("\n")
    panel = Panel(
        "This is a placeholder operation for testing purposes.\nNo actual scanner operations are performed.",
        title="[bold yellow]Dummy Operation[/bold yellow]",
        border_style="yellow"
    )
    console.print(panel)
    console.input("\n[dim]Press Enter to return to main menu...[/dim]")


def discover_agents_operation():
    """Perform agent discovery operation with rich formatting"""
    console.print("\n")
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    with console.status("[bold green]Initializing scanner service...", spinner="dots"):
        try:
            # Create and initialize scanner service
            scanner_service = ScannerService()
            scanner_service.initialize()
            
            # Display network status
            network_status = scanner_service.get_network_status()
        except Exception as e:
            logger.error(f"Scanner initialization failed: {e}")
            console.print(f"[bold red]Error:[/bold red] {e}")
            return
    
    # Create network info table
    table = Table(title="Network Information")
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")
    
    table.add_row("Local IP", network_status['local_ip'])
    table.add_row("Broadcast IP", network_status['broadcast_ip'])
    table.add_row("Interface", network_status['interface_name'])
    
    console.print(table)
    
    with console.status("[bold green]Discovering agents on network...", spinner="dots"):
        try:
            # Discover agents on the network
            discovered_agents = scanner_service.discover_agents()
            
            # Print summary with rich formatting
            agents_found = print_discovery_summary(discovered_agents)
            
            # If agents were found, allow user to select one
            if agents_found:
                console.print("\n")
                selected_agent = select_agent(discovered_agents)
                
                if selected_agent:
                    # Here you can add further operations with the selected agent
                    # For now, just confirm the selection
                    console.print("\n[dim]Note: Further operations with the selected agent can be implemented here.[/dim]")
            
        except Exception as e:
            logger.error(f"Scanner operation failed: {e}")
            console.print(f"[bold red]Error:[/bold red] {e}")
    
    console.input("\n[dim]Press Enter to return to main menu...[/dim]")

    
def setup_logging():
    """Setup logging configuration"""
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format
    )


def print_discovery_summary(discovered_agents):
    """Print a summary of discovered agents with rich formatting"""
    console.print("\n")
    
    if discovered_agents:
        # Create agents table
        agents_table = Table(title=f"Discovery Results - Found {len(discovered_agents)} Agent(s)")
        agents_table.add_column("#", style="cyan", no_wrap=True)
        agents_table.add_column("Address", style="yellow")
        agents_table.add_column("Source Name", style="green")
        agents_table.add_column("Destination Name", style="blue")
        agents_table.add_column("IP", style="magenta")
        
        for i, (message, address) in enumerate(discovered_agents, 1):
            agents_table.add_row(
                str(i),
                address,
                message.src_name.decode('ascii', errors='ignore'),
                message.dst_name.decode('ascii', errors='ignore'),
                str(message.initiator_ip)
            )
        
        console.print(agents_table)
        return True
    else:
        panel = Panel(
            "No agents discovered on the network listening for scanned documents.",
            title="[bold yellow]Discovery Results[/bold yellow]",
            border_style="yellow"
        )
        console.print(panel)
        return False


def select_agent(discovered_agents):
    """Allow user to select one of the discovered agents"""
    if not discovered_agents:
        return None
    
    # Create choices for inquirer
    choices = []
    for i, (message, address) in enumerate(discovered_agents):
        src_name = message.src_name.decode('ascii', errors='ignore')
        dst_name = message.dst_name.decode('ascii', errors='ignore')
        choice_text = f"{src_name} at {address} (→ {dst_name})"
        choices.append((choice_text, i))
    
    # Add option to go back
    choices.append(("← Back to main menu", -1))
    
    questions = [
        inquirer.List(
            'selected_agent',
            message="Select an agent to connect to",
            choices=choices
        )
    ]
    
    answers = inquirer.prompt(questions)
    if answers and answers['selected_agent'] != -1:
        selected_index = answers['selected_agent']
        selected_agent = discovered_agents[selected_index]
        
        # Display selected agent details
        message, address = selected_agent
        src_name = message.src_name.decode('ascii', errors='ignore')
        dst_name = message.dst_name.decode('ascii', errors='ignore')
        
        # Create detailed info panel
        info_text = f"""[bold]Selected Agent Details:[/bold]
        
Address: {address}
Source Name: {src_name}
Destination Name: {dst_name}
IP: {message.initiator_ip}
        
[green]✓ Agent selected successfully![/green]"""
        
        panel = Panel(
            info_text,
            title="[bold green]Agent Selection[/bold green]",
            border_style="green"
        )
        console.print(panel)
        
        return selected_agent
    
    return None


def main():
    """Main function with interactive CLI menu using rich and inquirer"""
    try:
        # Show welcome message
        show_welcome()
        
        while True:
            selected_option = interactive_menu()
            
            if selected_option == 'exit':
                console.print("\n[bold green]Thank you for using Scanner Proxy![/bold green]")
                break
            elif selected_option == 'dummy':
                dummy_operation()
            elif selected_option == 'discover':
                discover_agents_operation()
        
        return 0
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        return 1
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
