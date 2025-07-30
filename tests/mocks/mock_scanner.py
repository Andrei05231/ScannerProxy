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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn, TimeElapsedColumn, TransferSpeedColumn
from rich import print as rprint

# Add src to Python path for imports when running as script
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent.parent / "src"
    sys.path.insert(0, str(src_path))

# Import using relative paths when run as module, absolute when run as script
try:
    from src.core.scanner_service import ScannerService
    from src.utils.config import config
    from src.utils.logging_setup import setup_logging
except ImportError:
    from core.scanner_service import ScannerService
    from utils.config import config
    from utils.logging_setup import setup_logging

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
    
    # Discover agents (outside of status context to avoid spinner during selection)
    try:
        with console.status("[bold green]Discovering agents on network...", spinner="dots"):
            discovered_agents = scanner_service.discover_agents()
        
        # Print summary with rich formatting (after spinner stops)
        agents_found = print_discovery_summary(discovered_agents)
        
        # If agents were found, allow user to select one
        if agents_found:
            console.print("\n")
            selected_agent = select_agent(discovered_agents)
            
            if selected_agent:
                # Ask user what to do with the selected agent
                next_action = agent_action_menu(selected_agent)
                
                if next_action == 'send_file':
                    send_file_to_agent(scanner_service, selected_agent)
                elif next_action == 'view_details':
                    view_agent_details(selected_agent)
                # 'back' option just continues to the end
        
    except Exception as e:
        logger.error(f"Scanner operation failed: {e}")
        console.print(f"[bold red]Error:[/bold red] {e}")
    
    console.input("\n[dim]Press Enter to return to main menu...[/dim]")


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
    
    console.print("\n")  # Add spacing before the selection menu
    
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


def agent_action_menu(selected_agent):
    """Menu for actions to perform with the selected agent"""
    message, address = selected_agent
    src_name = message.src_name.decode('ascii', errors='ignore')
    
    questions = [
        inquirer.List(
            'action',
            message=f"What would you like to do with {src_name}?",
            choices=[
                ('Send File Transfer Request', 'send_file'),
                ('View Agent Details', 'view_details'),
                ('← Back to main menu', 'back')
            ]
        )
    ]
    
    answers = inquirer.prompt(questions)
    return answers['action'] if answers else 'back'


def select_file_to_send():
    """Let user select a file to send from the files directory"""
    import os
    
    files_dir = config.get('scanner.files_directory', 'files')
    
    # Check if files directory exists
    if not os.path.exists(files_dir):
        console.print(f"[red]Files directory '{files_dir}' does not exist![/red]")
        return None
    
    # Get list of files in the directory
    try:
        all_files = os.listdir(files_dir)
        # Filter for common file types (you can extend this list)
        valid_extensions = ['.raw', '.pdf', '.jpg', '.jpeg', '.png', '.txt', '.doc', '.docx']
        files = [f for f in all_files if os.path.isfile(os.path.join(files_dir, f)) and 
                any(f.lower().endswith(ext) for ext in valid_extensions)]
        
        if not files:
            console.print(f"[yellow]No files found in '{files_dir}' directory![/yellow]")
            console.print(f"[dim]Supported file types: {', '.join(valid_extensions)}[/dim]")
            return None
        
        # Create file selection table
        files_table = Table(title=f"Available Files in '{files_dir}'")
        files_table.add_column("#", style="cyan", no_wrap=True)
        files_table.add_column("File Name", style="white")
        files_table.add_column("Size", style="yellow")
        
        for i, filename in enumerate(files, 1):
            file_path = os.path.join(files_dir, filename)
            file_size = os.path.getsize(file_path)
            size_str = format_file_size(file_size)
            files_table.add_row(str(i), filename, size_str)
        
        console.print(files_table)
        
        # Create choices for inquirer
        choices = []
        for i, filename in enumerate(files):
            file_path = os.path.join(files_dir, filename)
            file_size = os.path.getsize(file_path)
            size_str = format_file_size(file_size)
            choice_text = f"{filename} ({size_str})"
            choices.append((choice_text, os.path.join(files_dir, filename)))
        
        # Add option to cancel
        choices.append(("← Cancel", None))
        
        console.print("\n")  # Add spacing before the selection menu
        
        questions = [
            inquirer.List(
                'selected_file',
                message="Select a file to send",
                choices=choices
            )
        ]
        
        answers = inquirer.prompt(questions)
        if answers and answers['selected_file']:
            selected_path = answers['selected_file']
            console.print(f"[green]✓ Selected file: {selected_path}[/green]")
            return selected_path
        
        return None
        
    except Exception as e:
        console.print(f"[red]Error reading files directory: {e}[/red]")
        return None


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    return f"{size_bytes:.1f} {size_names[i]}"


def send_file_to_agent(scanner_service, selected_agent):
    """Send file transfer request to the selected agent"""
    message, address = selected_agent
    src_name = message.src_name.decode('ascii', errors='ignore')
    dst_name = message.dst_name.decode('ascii', errors='ignore')
    
    # Extract IP from address (format is usually "ip:port")
    target_ip = address.split(':')[0] if ':' in address else address
    
    # Let user select which file to send
    selected_file = select_file_to_send()
    if not selected_file:
        return  # User cancelled or no files available
    
    console.print(f"\n[bold cyan]Sending file transfer request to {src_name}...[/bold cyan]")
    console.print(f"[dim]File to send: {selected_file}[/dim]")
    
    # Get file size for progress bar
    import os
    if os.path.exists(selected_file):
        file_size = os.path.getsize(selected_file)
        file_size_str = format_file_size(file_size)
        console.print(f"[dim]File size: {file_size_str}[/dim]")
    else:
        file_size = 0
    
    # Progress tracking variables
    progress_data = {'bytes_sent': 0, 'file_size': file_size, 'task_id': None}
    
    def progress_callback(bytes_sent, total_bytes):
        """Update progress bar"""
        progress_data['bytes_sent'] = bytes_sent
        if progress_data['task_id'] is not None and progress_data.get('progress'):
            progress_data['progress'].update(progress_data['task_id'], completed=bytes_sent)
    
    # Create progress bar configuration
    progress_columns = [
        SpinnerColumn(),
        TextColumn("[bold blue]Transferring", justify="right"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        "•",
        TransferSpeedColumn(),
        "•",
        TimeElapsedColumn(),
        "•",
        TimeRemainingColumn(),
    ]
    
    with Progress(*progress_columns, console=console, transient=False) as progress:
        # Add progress tracking to the callback
        progress_data['progress'] = progress
        
        # Start with UDP discovery phase
        discovery_task = progress.add_task("Sending UDP request...", total=None)
        
        try:
            success, response = scanner_service.send_file_transfer_request(
                target_ip=target_ip,
                dst_name=dst_name,
                file_path=selected_file,
                progress_callback=progress_callback
            )
            
            # Remove discovery task
            progress.remove_task(discovery_task)
            
            if success and response:
                # UDP response received, now show file transfer progress
                progress_data['task_id'] = progress.add_task(
                    f"Sending {os.path.basename(selected_file)}", 
                    total=file_size
                )
                
                # The progress callback will update the progress bar during file transfer
                # Wait a moment for the transfer to complete
                import time
                while progress_data['bytes_sent'] < file_size and progress_data['bytes_sent'] > 0:
                    time.sleep(0.1)
                
            elif success and not response:
                # UDP sent but no response
                progress.add_task("No UDP response received", total=1, completed=1)
            else:
                # Failed to send UDP
                progress.add_task("UDP request failed", total=1, completed=1)
                
        except Exception as e:
            progress.remove_task(discovery_task)
            console.print(f"[red]Error during file transfer: {e}[/red]")
            return
    
    if success:
        if response:
            # Got a response from the agent
            response_src = response.src_name.decode('ascii', errors='ignore')
            response_dst = response.dst_name.decode('ascii', errors='ignore')
            panel = Panel(
                f"[green]✓ File transfer request sent successfully![/green]\n\n"
                f"Target: {src_name} ({target_ip})\n"
                f"Network Address: {address}\n"
                f"File: {selected_file}\n"
                f"Request Type: File Transfer (0x5A5400)\n"
                f"Status: Message delivered via UDP\n\n"
                f"[bold cyan]UDP Response Received:[/bold cyan]\n"
                f"From: {response_src}\n"
                f"To: {response_dst}\n"
                f"Response Type: {response.type_of_request.hex()}\n\n"
                f"[bold yellow]TCP File Transfer:[/bold yellow]\n"
                f"Initiated TCP connection on port {config.get('network.tcp_port', 708)}\n"
                f"File transfer protocol: direct file data transfer",
                title="[bold green]File Transfer Completed[/bold green]",
                border_style="green"
            )
        else:
            # Request sent but no response received
            panel = Panel(
                f"[green]✓ File transfer request sent successfully![/green]\n\n"
                f"Target: {src_name} ({target_ip})\n"
                f"Network Address: {address}\n"
                f"File: {selected_file}\n"
                f"Request Type: File Transfer (0x5A5400)\n"
                f"Status: Message delivered via UDP\n\n"
                f"[yellow]⚠ No UDP response received from agent[/yellow]\n"
                f"TCP connection not initiated (requires UDP response first)",
                title="[bold green]Transfer Request Sent[/bold green]",
                border_style="green"
            )
    else:
        panel = Panel(
            f"[red]✗ Failed to send file transfer request[/red]\n\n"
            f"Target: {src_name} ({target_ip})\n"
            f"Network Address: {address}\n"
            f"File: {selected_file}\n"
            f"Please check network connection and try again.",
            title="[bold red]Transfer Request Failed[/bold red]",
            border_style="red"
        )
    
    console.print(panel)
    console.input("\n[dim]Press Enter to continue...[/dim]")


def view_agent_details(selected_agent):
    """Display detailed information about the selected agent"""
    message, address = selected_agent
    src_name = message.src_name.decode('ascii', errors='ignore')
    dst_name = message.dst_name.decode('ascii', errors='ignore')
    
    # Create a detailed table
    details_table = Table(title=f"Agent Details: {src_name}")
    details_table.add_column("Property", style="cyan", no_wrap=True)
    details_table.add_column("Value", style="white")
    
    details_table.add_row("Source Name", src_name)
    details_table.add_row("Destination Name", dst_name)
    details_table.add_row("IP Address", str(message.initiator_ip))
    details_table.add_row("Network Address", address)
    details_table.add_row("Signature", message.signature.hex())
    details_table.add_row("Type of Request", message.type_of_request.hex())
    details_table.add_row("Message Size", f"{len(message.to_bytes())} bytes")
    
    console.print(details_table)
    console.input("\n[dim]Press Enter to continue...[/dim]")


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
