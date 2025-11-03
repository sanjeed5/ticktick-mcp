import asyncio
import json
import os
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Dict, List, Any, Optional

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

from .ticktick_client import TickTickClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server
mcp = FastMCP("ticktick")

# Create TickTick client
ticktick = None

def initialize_client():
    global ticktick
    try:
        # Check if .env file exists with access token
        load_dotenv()
        
        # Check if we have valid credentials
        if os.getenv("TICKTICK_ACCESS_TOKEN") is None:
            logger.error("No access token found in .env file. Please run 'uv run -m ticktick_mcp.cli auth' to authenticate.")
            return False
        
        # Initialize the client
        ticktick = TickTickClient()
        logger.info("TickTick client initialized successfully")
        
        # Test API connectivity
        projects = ticktick.get_projects()
        if 'error' in projects:
            logger.error(f"Failed to access TickTick API: {projects['error']}")
            logger.error("Your access token may have expired. Please run 'uv run -m ticktick_mcp.cli auth' to refresh it.")
            return False
            
        logger.info(f"Successfully connected to TickTick API with {len(projects)} projects")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize TickTick client: {e}")
        return False

# Format a task object from TickTick for better display
def format_task(task: Dict) -> str:
    """Format a task into a human-readable string."""
    formatted = f"ID: {task.get('id', 'No ID')}\n"
    formatted += f"Title: {task.get('title', 'No title')}\n"
    
    # Add project ID
    formatted += f"Project ID: {task.get('projectId', 'None')}\n"
    
    # Add dates if available
    if task.get('startDate'):
        formatted += f"Start Date: {task.get('startDate')}\n"
    if task.get('dueDate'):
        formatted += f"Due Date: {task.get('dueDate')}\n"
    
    # Add priority if available
    priority_map = {0: "None", 1: "Low", 3: "Medium", 5: "High"}
    priority = task.get('priority', 0)
    formatted += f"Priority: {priority_map.get(priority, str(priority))}\n"
    
    # Add status if available
    status = "Completed" if task.get('status') == 2 else "Active"
    formatted += f"Status: {status}\n"
    
    # Add content if available
    if task.get('content'):
        formatted += f"\nContent:\n{task.get('content')}\n"
    
    # Add subtasks if available
    items = task.get('items', [])
    if items:
        formatted += f"\nSubtasks ({len(items)}):\n"
        for i, item in enumerate(items, 1):
            status = "✓" if item.get('status') == 1 else "□"
            formatted += f"{i}. [{status}] {item.get('title', 'No title')}\n"
    
    return formatted

# Format a project object from TickTick for better display
def format_project(project: Dict) -> str:
    """Format a project into a human-readable string."""
    formatted = f"Name: {project.get('name', 'No name')}\n"
    formatted += f"ID: {project.get('id', 'No ID')}\n"
    
    # Add color if available
    if project.get('color'):
        formatted += f"Color: {project.get('color')}\n"
    
    # Add view mode if available
    if project.get('viewMode'):
        formatted += f"View Mode: {project.get('viewMode')}\n"
    
    # Add closed status if available
    if 'closed' in project:
        formatted += f"Closed: {'Yes' if project.get('closed') else 'No'}\n"
    
    # Add kind if available
    if project.get('kind'):
        formatted += f"Kind: {project.get('kind')}\n"
    
    return formatted

# MCP Tools

@mcp.tool()
async def get_projects() -> str:
    """
    Get all projects from TickTick.
    
    Returns:
        Formatted list of all projects with their details (ID, name, color, view mode, etc.).
    
    Example:
        Use this to see all available projects before creating tasks or filtering by project.
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        projects = ticktick.get_projects()
        if 'error' in projects:
            return f"Error fetching projects: {projects['error']}"
        
        if not projects:
            return "No projects found."
        
        result = f"Found {len(projects)} projects:\n\n"
        for i, project in enumerate(projects, 1):
            result += f"Project {i}:\n" + format_project(project) + "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_projects: {e}")
        return f"Error retrieving projects: {str(e)}"

@mcp.tool()
async def get_project(project_id: str) -> str:
    """
    Get details about a specific project.
    
    Args:
        project_id: ID of the project. Use "inbox" for the inbox project.
    
    Returns:
        Formatted project details including name, ID, color, view mode, and status.
    
    Example:
        get_project("6226ff9877acee87727f6bca") - Get details for a specific project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        project = ticktick.get_project(project_id)
        if 'error' in project:
            return f"Error fetching project: {project['error']}"
        
        return format_project(project)
    except Exception as e:
        logger.error(f"Error in get_project: {e}")
        return f"Error retrieving project: {str(e)}"

@mcp.tool()
async def get_project_tasks(project_id: str) -> str:
    """
    Get all tasks in a specific project.
    
    Args:
        project_id: ID of the project. Use "inbox" to access your TickTick inbox tasks.
    
    Returns:
        Formatted list of all tasks in the project with their details (title, priority, due dates, status, etc.).
    
    Example:
        get_project_tasks("inbox") - Get all tasks in your inbox
        get_project_tasks("6226ff9877acee87727f6bca") - Get all tasks in a specific project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        project_data = ticktick.get_project_with_data(project_id)
        if 'error' in project_data:
            return f"Error fetching project data: {project_data['error']}"
        
        tasks = project_data.get('tasks', [])
        if not tasks:
            return f"No tasks found in project '{project_data.get('project', {}).get('name', project_id)}'."
        
        result = f"Found {len(tasks)} tasks in project '{project_data.get('project', {}).get('name', project_id)}':\n\n"
        for i, task in enumerate(tasks, 1):
            result += f"Task {i}:\n" + format_task(task) + "\n"
        
        return result
    except Exception as e:
        logger.error(f"Error in get_project_tasks: {e}")
        return f"Error retrieving project tasks: {str(e)}"

@mcp.tool()
async def get_task(project_id: str, task_id: str) -> str:
    """
    Get details about a specific task.
    
    Args:
        project_id: ID of the project. Use "inbox" for inbox tasks.
        task_id: ID of the task
    
    Returns:
        Formatted task details including title, content, priority, dates, status, and subtasks.
    
    Example:
        get_task("inbox", "63b7bebb91c0a5474805fcd4") - Get details for a specific task
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        task = ticktick.get_task(project_id, task_id)
        if 'error' in task:
            return f"Error fetching task: {task['error']}"
        
        return format_task(task)
    except Exception as e:
        logger.error(f"Error in get_task: {e}")
        return f"Error retrieving task: {str(e)}"

@mcp.tool()
async def create_task(
    title: str, 
    project_id: str, 
    content: str = None, 
    start_date: str = None, 
    due_date: str = None, 
    priority: int = 0
) -> str:
    """
    Create a new task in TickTick.
    
    Args:
        title: Task title (required)
            Example: "Review Q4 report"
        project_id: ID of the project to add the task to (required)
            Use "inbox" to create tasks in your TickTick inbox.
            Example: "inbox" or "6226ff9877acee87727f6bca"
        content: Task description/content (optional)
            Example: "Review all sections and provide feedback"
        start_date: Start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            Example: "2025-11-05T09:00:00+0000"
        due_date: Due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            Example: "2025-11-05T18:00:00+0000"
        priority: Priority level (optional, default 0)
            0 = None, 1 = Low, 3 = Medium, 5 = High
    
    Returns:
        Formatted task details including ID for future updates.
    
    Example:
        create_task("Buy groceries", "inbox", priority=3, due_date="2025-11-05T18:00:00+0000")
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate priority
    if priority not in [0, 1, 3, 5]:
        return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
    
    try:
        # Validate dates if provided
        for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
            if date_str:
                try:
                    # Try to parse the date to validate it
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
        
        task = ticktick.create_task(
            title=title,
            project_id=project_id,
            content=content,
            start_date=start_date,
            due_date=due_date,
            priority=priority
        )
        
        if 'error' in task:
            return f"Error creating task: {task['error']}"
        
        return f"Task created successfully:\n\n" + format_task(task)
    except Exception as e:
        logger.error(f"Error in create_task: {e}")
        return f"Error creating task: {str(e)}"

@mcp.tool()
async def update_task(
    task_id: str,
    project_id: str,
    title: str = None,
    content: str = None,
    start_date: str = None,
    due_date: str = None,
    priority: int = None
) -> str:
    """
    Update an existing task in TickTick.
    
    Args:
        task_id: ID of the task to update (required)
        project_id: ID of the project the task belongs to (required). Use "inbox" for inbox tasks.
        title: New task title (optional)
            Example: "Review Q4 report - Updated"
        content: New task description/content (optional)
        start_date: New start date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            Example: "2025-11-05T09:00:00+0000"
        due_date: New due date in ISO format YYYY-MM-DDThh:mm:ss+0000 (optional)
            Example: "2025-11-06T18:00:00+0000"
        priority: New priority level (optional)
            0 = None, 1 = Low, 3 = Medium, 5 = High
    
    Returns:
        Formatted updated task details.
    
    Example:
        update_task("63b7bebb91c0a5474805fcd4", "inbox", priority=5) - Update task priority to high
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate priority if provided
    if priority is not None and priority not in [0, 1, 3, 5]:
        return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
    
    try:
        # Validate dates if provided
        for date_str, date_name in [(start_date, "start_date"), (due_date, "due_date")]:
            if date_str:
                try:
                    # Try to parse the date to validate it
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    return f"Invalid {date_name} format. Use ISO format: YYYY-MM-DDThh:mm:ss+0000"
        
        task = ticktick.update_task(
            task_id=task_id,
            project_id=project_id,
            title=title,
            content=content,
            start_date=start_date,
            due_date=due_date,
            priority=priority
        )
        
        if 'error' in task:
            return f"Error updating task: {task['error']}"
        
        return f"Task updated successfully:\n\n" + format_task(task)
    except Exception as e:
        logger.error(f"Error in update_task: {e}")
        return f"Error updating task: {str(e)}"

@mcp.tool()
async def complete_task(project_id: str, task_id: str) -> str:
    """
    Mark a task as complete.
    
    Args:
        project_id: ID of the project (required). Use "inbox" for inbox tasks.
        task_id: ID of the task to complete (required)
    
    Returns:
        Confirmation message indicating the task was marked as complete.
    
    Example:
        complete_task("inbox", "63b7bebb91c0a5474805fcd4") - Mark a task as done
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.complete_task(project_id, task_id)
        if 'error' in result:
            return f"Error completing task: {result['error']}"
        
        return f"Task {task_id} marked as complete."
    except Exception as e:
        logger.error(f"Error in complete_task: {e}")
        return f"Error completing task: {str(e)}"

@mcp.tool()
async def delete_task(project_id: str, task_id: str) -> str:
    """
    Delete a task permanently.
    
    Args:
        project_id: ID of the project (required). Use "inbox" for inbox tasks.
        task_id: ID of the task to delete (required)
    
    Returns:
        Confirmation message indicating the task was deleted.
    
    Warning:
        This action cannot be undone. Use complete_task if you want to mark a task as done instead.
    
    Example:
        delete_task("inbox", "63b7bebb91c0a5474805fcd4") - Delete a task permanently
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.delete_task(project_id, task_id)
        if 'error' in result:
            return f"Error deleting task: {result['error']}"
        
        return f"Task {task_id} deleted successfully."
    except Exception as e:
        logger.error(f"Error in delete_task: {e}")
        return f"Error deleting task: {str(e)}"

@mcp.tool()
async def create_project(
    name: str,
    color: str = "#F18181",
    view_mode: str = "list"
) -> str:
    """
    Create a new project in TickTick.
    
    Args:
        name: Project name (required)
            Example: "Vacation Planning"
        color: Color code in hex format (optional, default "#F18181")
            Example: "#F18181" (red), "#5AC8FA" (blue), "#34C759" (green)
        view_mode: View mode (optional, default "list")
            Options: "list", "kanban", "timeline"
    
    Returns:
        Formatted project details including the new project ID.
    
    Example:
        create_project("Work Tasks", color="#5AC8FA", view_mode="kanban")
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate view_mode
    if view_mode not in ["list", "kanban", "timeline"]:
        return "Invalid view_mode. Must be one of: list, kanban, timeline."
    
    try:
        project = ticktick.create_project(
            name=name,
            color=color,
            view_mode=view_mode
        )
        
        if 'error' in project:
            return f"Error creating project: {project['error']}"
        
        return f"Project created successfully:\n\n" + format_project(project)
    except Exception as e:
        logger.error(f"Error in create_project: {e}")
        return f"Error creating project: {str(e)}"

@mcp.tool()
async def delete_project(project_id: str) -> str:
    """
    Delete a project permanently.
    
    Args:
        project_id: ID of the project to delete (required)
    
    Returns:
        Confirmation message indicating the project was deleted.
    
    Warning:
        This action cannot be undone. All tasks in the project will also be deleted.
    
    Example:
        delete_project("6226ff9877acee87727f6bca") - Delete a project
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    try:
        result = ticktick.delete_project(project_id)
        if 'error' in result:
            return f"Error deleting project: {result['error']}"
        
        return f"Project {project_id} deleted successfully."
    except Exception as e:
        logger.error(f"Error in delete_project: {e}")
        return f"Error deleting project: {str(e)}"
    

### Improved Task MCP Tools

# Helper Functions

PRIORITY_MAP = {0: "None", 1: "Low", 3: "Medium", 5: "High"}

def _parse_ticktick_date(date_str: str) -> Optional[datetime]:
    """
    Parse a TickTick date string to a datetime object.
    
    TickTick API returns dates in format: "2019-11-14T03:00:00+0000"
    (without microseconds, timezone as +0000 instead of +00:00)
    
    Args:
        date_str: Date string from TickTick API
        
    Returns:
        datetime object with timezone, or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        # Try parsing with microseconds first (in case API changes)
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            pass
        
        # Normalize timezone format: +0000 -> +00:00 for Python's strptime
        # Python's %z expects +00:00 format, not +0000
        normalized_date = date_str
        if len(date_str) > 5 and date_str[-5] in ['+', '-']:
            # Format: YYYY-MM-DDTHH:MM:SS+0000 -> YYYY-MM-DDTHH:MM:SS+00:00
            timezone_part = date_str[-5:]
            if len(timezone_part) == 5 and timezone_part[-4:].isdigit():
                sign = timezone_part[0]
                hours = timezone_part[1:3]
                minutes = timezone_part[3:5]
                normalized_date = date_str[:-5] + f"{sign}{hours}:{minutes}"
        
        # Try parsing without microseconds
        try:
            return datetime.strptime(normalized_date, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            # Fallback: try with fromisoformat which handles both formats
            try:
                # Convert +0000 to +00:00 for fromisoformat
                if normalized_date.endswith(('+0000', '-0000')):
                    sign = normalized_date[-5]
                    normalized_date = normalized_date[:-5] + f"{sign}00:00"
                return datetime.fromisoformat(normalized_date.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return None
    except (ValueError, TypeError, AttributeError):
        return None

def _is_task_due_today(task: Dict[str, Any]) -> bool:
    """Check if a task is due today."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    task_dt = _parse_ticktick_date(due_date)
    if not task_dt:
        return False
    
    task_due_date = task_dt.date()
    today_date = datetime.now(timezone.utc).date()
    return task_due_date == today_date

def _is_task_overdue(task: Dict[str, Any]) -> bool:
    """Check if a task is overdue."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    task_dt = _parse_ticktick_date(due_date)
    if not task_dt:
        return False
    
    return task_dt < datetime.now(timezone.utc)

def _is_task_due_in_days(task: Dict[str, Any], days: int) -> bool:
    """Check if a task is due in exactly X days."""
    due_date = task.get('dueDate')
    if not due_date:
        return False
    
    task_dt = _parse_ticktick_date(due_date)
    if not task_dt:
        return False
    
    task_due_date = task_dt.date()
    target_date = (datetime.now(timezone.utc) + timedelta(days=days)).date()
    return task_due_date == target_date

def _task_matches_search(task: Dict[str, Any], search_term: str) -> bool:
    """Check if a task matches the search term (case-insensitive)."""
    search_term = search_term.lower()
    
    # Search in title
    title = task.get('title', '').lower()
    if search_term in title:
        return True
    
    # Search in content
    content = task.get('content', '').lower()
    if search_term in content:
        return True
    
    # Search in subtasks
    items = task.get('items', [])
    for item in items:
        item_title = item.get('title', '').lower()
        if search_term in item_title:
            return True
    
    return False

def _validate_task_data(task_data: Dict[str, Any], task_index: int) -> Optional[str]:
    """
    Validate a single task's data for batch creation.
    
    Returns:
        None if valid, error message string if invalid
    """
    # Check required fields
    if 'title' not in task_data or not task_data['title']:
        return f"Task {task_index + 1}: 'title' is required and cannot be empty"
    
    if 'project_id' not in task_data or not task_data['project_id']:
        return f"Task {task_index + 1}: 'project_id' is required and cannot be empty"
    
    # Validate priority if provided
    priority = task_data.get('priority')
    if priority is not None and priority not in [0, 1, 3, 5]:
        return f"Task {task_index + 1}: Invalid priority {priority}. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)"
    
    # Validate dates if provided
    for date_field in ['start_date', 'due_date']:
        date_str = task_data.get(date_field)
        if date_str:
            try:
                # Try to parse the date to validate it
                # Handle both with and without timezone info
                if date_str.endswith('Z'):
                    datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                elif '+' in date_str or date_str.endswith(('00', '30')):
                    datetime.fromisoformat(date_str)
                else:
                    # Assume local timezone if no timezone specified
                    datetime.fromisoformat(date_str)
            except ValueError:
                return f"Task {task_index + 1}: Invalid {date_field} format '{date_str}'. Use ISO format: YYYY-MM-DDTHH:mm:ss or with timezone"
    
    return None

def _get_project_tasks_by_filter(projects: List[Dict], filter_func, filter_name: str) -> str:
    """
    Helper function to filter tasks across all projects.
    
    Args:
        projects: List of project dictionaries
        filter_func: Function that takes a task and returns True if it matches the filter
        filter_name: Name of the filter for output formatting
    
    Returns:
        Formatted string of filtered tasks
    """
    if not projects:
        return "No projects found."
    
    result = f"Found {len(projects)} projects:\n\n"
    
    for i, project in enumerate(projects, 1):
        if project.get('closed'):
            continue
            
        project_id = project.get('id', 'No ID')
        project_data = ticktick.get_project_with_data(project_id)
        tasks = project_data.get('tasks', [])
        
        if not tasks:
            result += f"Project {i}:\n{format_project(project)}"
            result += f"With 0 tasks that are to be '{filter_name}' in this project :\n\n\n"
            continue
        
        # Filter tasks using the provided function
        filtered_tasks = [(t, task) for t, task in enumerate(tasks, 1) if filter_func(task)]
        
        result += f"Project {i}:\n{format_project(project)}"
        result += f"With {len(filtered_tasks)} tasks that are to be '{filter_name}' in this project :\n"
        
        for t, task in filtered_tasks:
            result += f"Task {t}:\n{format_task(task)}\n"
        
        result += "\n\n"
    
    return result

# Task Filtering Tool

@mcp.tool()
async def filter_tasks(
    date_filter: str = "all",
    priority: int = None,
    search_term: str = None,
    project_id: str = None
) -> str:
    """
    Filter tasks across all projects with flexible criteria. Combine multiple filters to find exactly what you need.
    
    Args:
        date_filter: Filter by date range. Options:
            - "all" (default): All tasks regardless of date
            - "today": Tasks due today
            - "tomorrow": Tasks due tomorrow
            - "overdue": Tasks that are past their due date
            - "this_week": Tasks due within the next 7 days
            - "next_7_days": Same as "this_week"
        priority: Filter by priority level. Options:
            - None (default): Any priority
            - 0: None priority
            - 1: Low priority
            - 3: Medium priority
            - 5: High priority
        search_term: Search for text in task title, content, or subtask titles (case-insensitive).
            Example: "client meeting" will find tasks containing "client meeting"
        project_id: Filter to a specific project. Use "inbox" for inbox tasks, or a project ID.
            If None, searches across all projects.
    
    Returns:
        Formatted list of matching tasks grouped by project.
    
    Examples:
        filter_tasks(date_filter="overdue") - All overdue tasks
        filter_tasks(priority=5) - All high priority tasks
        filter_tasks(date_filter="today", priority=5) - High priority tasks due today
        filter_tasks(search_term="client meeting") - Search for tasks about client meetings
        filter_tasks(project_id="inbox", date_filter="this_week") - Inbox tasks due this week
        filter_tasks(priority=3, search_term="review") - Medium priority tasks containing "review"
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate date_filter
    valid_date_filters = ["all", "today", "tomorrow", "overdue", "this_week", "next_7_days"]
    if date_filter not in valid_date_filters:
        return f"Invalid date_filter. Valid values: {', '.join(valid_date_filters)}"
    
    # Validate priority if provided
    if priority is not None and priority not in PRIORITY_MAP:
        return f"Invalid priority. Valid values: {list(PRIORITY_MAP.keys())}"
    
    # Validate search_term if provided
    if search_term is not None and not search_term.strip():
        return "Search term cannot be empty."
    
    try:
        # Get projects to filter
        if project_id:
            # Single project filter
            projects_data = ticktick.get_projects()
            if 'error' in projects_data:
                return f"Error fetching projects: {projects_data['error']}"
            
            # Find the specific project
            project = None
            for p in projects_data:
                if p.get('id') == project_id or (project_id == "inbox" and p.get('name', '').lower() == "inbox"):
                    project = p
                    break
            
            if not project:
                return f"Project '{project_id}' not found."
            
            projects = [project]
        else:
            # All projects
            projects = ticktick.get_projects()
            if 'error' in projects:
                return f"Error fetching projects: {projects['error']}"
        
        # Build filter function
        def task_filter(task: Dict[str, Any]) -> bool:
            # Date filter
            if date_filter == "all":
                date_match = True
            elif date_filter == "today":
                date_match = _is_task_due_today(task)
            elif date_filter == "tomorrow":
                date_match = _is_task_due_in_days(task, 1)
            elif date_filter == "overdue":
                date_match = _is_task_overdue(task)
            elif date_filter in ["this_week", "next_7_days"]:
                due_date = task.get('dueDate')
                if not due_date:
                    date_match = False
                else:
                    task_dt = _parse_ticktick_date(due_date)
                    if not task_dt:
                        date_match = False
                    else:
                        task_due_date = task_dt.date()
                        today = datetime.now(timezone.utc).date()
                        week_from_today = today + timedelta(days=7)
                        date_match = today <= task_due_date <= week_from_today
            else:
                date_match = True
            
            # Priority filter
            if priority is None:
                priority_match = True
            else:
                priority_match = task.get('priority', 0) == priority
            
            # Search filter
            if search_term is None:
                search_match = True
            else:
                search_match = _task_matches_search(task, search_term)
            
            return date_match and priority_match and search_match
        
        # Build filter description
        filter_parts = []
        if date_filter != "all":
            filter_parts.append(date_filter)
        if priority is not None:
            filter_parts.append(f"priority {PRIORITY_MAP[priority]}")
        if search_term:
            filter_parts.append(f"matching '{search_term}'")
        if project_id:
            filter_parts.append(f"in project '{project_id}'")
        
        filter_name = " and ".join(filter_parts) if filter_parts else "all tasks"
        
        return _get_project_tasks_by_filter(projects, task_filter, filter_name)
        
    except Exception as e:
        logger.error(f"Error in filter_tasks: {e}")
        return f"Error filtering tasks: {str(e)}"

# GTD Workflow Prompts

@mcp.prompt()
async def engaged() -> list:
    """
    Show me tasks that need immediate attention (GTD "Engaged" workflow).
    
    This prompt helps you focus on tasks that require immediate action:
    - High priority tasks (priority 5)
    - Overdue tasks
    - Tasks due today
    
    Use this when you need to see what demands your attention right now.
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": "Use the filter_tasks tool to show me all engaged tasks. Engaged tasks are: (1) tasks with priority=5 OR (2) tasks with date_filter='overdue' OR (3) tasks with date_filter='today'. Format the results as a clear, actionable list with project groupings."
            }
        }
    ]

@mcp.prompt()
async def next_actions() -> list:
    """
    Show me tasks for next actions (GTD "Next" workflow).
    
    This prompt helps you identify tasks ready for action:
    - Medium priority tasks (priority 3)
    - Tasks due tomorrow
    
    Use this when planning what to work on next.
    """
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": "Use the filter_tasks tool to show me my next actions. Next actions are: (1) tasks with priority=3 OR (2) tasks with date_filter='tomorrow'. Format the results as an organized, prioritized list."
            }
        }
    ]

@mcp.tool()
async def create_subtask(
    subtask_title: str,
    parent_task_id: str,
    project_id: str,
    content: str = None,
    priority: int = 0
) -> str:
    """
    Create a subtask for a parent task within the same project.
    
    Args:
        subtask_title: Title of the subtask (required)
            Example: "Buy milk"
        parent_task_id: ID of the parent task (required)
            Example: "63b7bebb91c0a5474805fcd4"
        project_id: ID of the project (required). Must match the parent task's project.
            Use "inbox" if the parent task is in the inbox.
        content: Optional content/description for the subtask
        priority: Priority level (optional, default 0)
            0 = None, 1 = Low, 3 = Medium, 5 = High
    
    Returns:
        Formatted subtask details including ID.
    
    Example:
        create_subtask("Buy milk", "63b7bebb91c0a5474805fcd4", "inbox", priority=1)
    """
    if not ticktick:
        if not initialize_client():
            return "Failed to initialize TickTick client. Please check your API credentials."
    
    # Validate priority
    if priority not in [0, 1, 3, 5]:
        return "Invalid priority. Must be 0 (None), 1 (Low), 3 (Medium), or 5 (High)."
    
    try:
        subtask = ticktick.create_subtask(
            subtask_title=subtask_title,
            parent_task_id=parent_task_id,
            project_id=project_id,
            content=content,
            priority=priority
        )
        
        if 'error' in subtask:
            return f"Error creating subtask: {subtask['error']}"
        
        return f"Subtask created successfully:\n\n" + format_task(subtask)
    except Exception as e:
        logger.error(f"Error in create_subtask: {e}")
        return f"Error creating subtask: {str(e)}"

def main():
    """Main entry point for the MCP server."""
    # Initialize the TickTick client
    if not initialize_client():
        logger.error("Failed to initialize TickTick client. Please check your API credentials.")
        return
    
    # Run the server
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main()