"""userlist script

Displays users in the database.
"""
import reflex as rx
from AIPlanner.classes.database import *
from AIPlanner.pages.login import LoginState
from AIPlanner.classes.ai import AIState

def display_usernames(state=UserManagementState):
    """Function to display usernames
    
    Returns:
    A reflex vertical stack component with all of the usernames, IDs, and tasks for all users in the database
    """
    return rx.vstack(
    rx.text(state.message),  # Display number of users retrieved
    rx.foreach(  # Use rx.foreach for list rendering
        state.users,
        # Create a text component for each username
            lambda user: rx.text(user.username, " ", user.id, user.tasks)
        )
    )

def display_user_tasks(state=UserManagementState):
    """Function to display tasks for the specified user
    
    Returns:
    A reflex vertical stack component with the task names, due dates, descriptions, priority levels, IDs, and deletion status of tasks
    """
    return rx.vstack(
        rx.foreach(
            state.tasks,
            lambda task: rx.text(
                f"Task Name: {task.task_name}, Due Date: {task.due_date}, "
                f"Description: {task.description}, Priority: {task.priority_level}, "
                f"Task ID: {task.task_id}, is_deleted: {task.is_deleted}, id: {task.id}"
                f"Recur_Frequency: {task.recur_frequency}"
            )
        )
    )

def userlist(state=UserManagementState) -> rx.Component:
    """
    Calls display_usernames to display all users in database, 
    with buttons for quick addition of test users to the database
    and repeated retrieval of users from the database

    Returns:
    Reflex container component with a heading, several buttons, and the result of display_usernames and display_user_tasks
    """
    state.fetch_all_users()
    state.get_user_tasks()

    # User list debugging page
    return rx.container(
        rx.heading("User List", size="5"),
        rx.button("Fetch All Users From Database", on_click=[state.fetch_all_users]),
        rx.button("Add Test User",
                     # Button to add test user
                     on_click=lambda: state.add_test_user()),
        rx.button("Add task to test user with ID 1", on_click=lambda: state.add_test_task(1)),
        rx.button("Show tasks assigned to currently logged in user",
                  on_click=lambda: state.get_user_tasks(LoginState.user_id)),
        rx.button("Generate AI schedule for current user", on_click=lambda: AIState.send_request(state.tasks)),
        rx.text(AIState.processed_output),
        display_usernames(),
        display_user_tasks(),
        rx.logo(),
    )


#Eof
