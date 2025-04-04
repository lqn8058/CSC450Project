"""Testing file and page for OpenAI integration. Must have OpenAI API key set as an environment variable OPENAI_API_KEY to use."""
import os
import re
from datetime import datetime, timedelta
import time
import reflex as rx
from openai import OpenAI
from AIPlanner.classes.database import UserManagementState
from AIPlanner.classes.database import Task
from AIPlanner.pages.login import LoginState

class AIState(UserManagementState):
    """State that holds variables related to AI generation and functions that use those variables
    
    Attributes:
    processed_output: String state variable to hold final output of processing
    message: String state variable to hold success or failure messages
    """

    processed_output = ""
    messageText = ""

    def send_request(self, tasks):
        '''Function to send an OpenAI API request to generate task date/time/duration assignments, currently prints to console
        
        Returns:
        task_string: String that contains the result of processing the completion of the API request
        '''

        inputMessage = ""
        self.messageText = ""
        for task in tasks:
            print(task)
            if task['is_deleted'] is False:
                if task['recur_frequency'] == 0:
                    inputMessage = inputMessage + f"task_id = {task['id']}\ntask_name = '{task['task_name']}\npriority_level = {task['priority_level']}\ndue_date = {task['due_date']}\n\n"
                    print(task['id'])

        if not tasks:
            self.messageText = "No tasks available to generate a schedule. Please add some and try again."
            return "No tasks available to generate a schedule. Please add some and try again."
        else:
            self.messageText = "Tasks retrieved successfully."

        currentTime = time.ctime()
        print("Tasks retrieved successfully.")
        OpenAI.api_key = os.environ["OPENAI_API_KEY"]

        client = OpenAI()

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""
                You are a bot that takes user tasks and assigns them to slots on a calendar. Tasks can have a priority level with (1) being the highest and (3) being the lowest. 
                Higher priority tasks should be assigned to blocks before lower priority tasks. Do not make any changes or return anything other than the following format for each task. 
                Do not include anything like "Here's the output" or "Let me know if you'd like any adjustments". The current date is {currentTime}, only schedule tasks after this time.
                Do not include the word hours in the response. Give output in the format as follows:  
                task_id = Integer from prompt
                task_name = String from prompt
                assigned_block_date = Generated date before task due date
                assigned_block_start_time = Choose a time between 09:00:00 and 17:00:00 to start the task
                assigned_block_duration = How long the task should be worked on"""},
                {
                    "role": "user",
                    "content": f"""
                {inputMessage}
                """
                }
            ]
        )

        print(completion.choices[0].message.content)
        self.processed_output = self.process_output(completion.choices[0].message.content)

    def process_output(self, content):
        '''Processes the output of an OpenAI API call using regular expressions 
        and prints the string result to the console
        
        Parameters:
        completion: String that contains the raw completion returned by the OpenAI API

        Returns:
        task_string: String that contains the processed completion resuts
        '''
        # Regular expression to extract task details
        regex = re.compile(
            r"task_id\s*=\s*(\d+).*?"
            r"assigned_block_date\s*=\s*(\d{4}-\d{2}-\d{2}).*?"
            r"assigned_block_start_time\s*=\s*(\d{2}:\d{2}).*?"
            r"assigned_block_duration\s*=\s*(\d+)",
            re.DOTALL
        )

        # Extract matches and build dictionaries
        matches = regex.findall(content)
        print(f"Matches: {matches}")
        if matches:
            self.messageText = "Matching successful."
        tasks = [
            {
                "task_id": int(match[0]),
                "assigned_block_date": match[1],
                "assigned_block_start_time": match[2],
                "assigned_block_duration": int(match[3]),
            }
            for match in matches
            ]
        print(f"Tasks: {tasks}")
        task_string = ""
        for task in tasks:
            for key, value in task.items():
                task_string = task_string + f'{key}: {value}\n'
        print("Task string constructed")
        for task in tasks:
            print("in task loop")
            task_id = None
            task_date = None
            task_start = None
            task_duration = None
            for key, value in task.items():
                print(key,value)
                if key == "task_id":
                    task_id = int(value)
                elif key == "assigned_block_date":
                    try:
                        task_date = datetime.strptime(value, "%Y-%m-%d").date()
                    except ValueError:
                        print(f"Invalid date format for task_id {task_id}: {value}")
                elif key == "assigned_block_start_time":
                    try:
                        value = value + ":00"
                        task_start = datetime.strptime(value, "%H:%M:%S").time()
                    except ValueError:
                        print(f"Invalid time format for task_id {task_id}: {value}")
                elif key == "assigned_block_duration":
                    try:
                        task_duration = timedelta(hours=int(value))
                    except ValueError:
                        print(f"Invalid duration format for task_id {task_id}: {value}")
            self.assign_block(task_id=task_id, task_date=task_date, task_start=task_start, task_duration=task_duration)
            self.messageText = "Schedule generated successfully."
        return task_string

    def assign_block(self, task_id: int, task_date: datetime, task_start: datetime, task_duration: timedelta):
        """Edits tasks to match AI-assigned date, time, and duration values"""
        print(task_id, task_date, task_start, task_duration)
        with rx.session() as session:
            # Try to get the task with the specified ID
            task = session.exec(
                Task.select().where(Task.id == task_id)
            ).first()
            if task:
                # Set block assignment values and commit to database
                task.assigned_block_date = task_date
                task.assigned_block_start_time = task_start
                task.assigned_block_duration = task_duration
                session.commit()
                print(f"Task {task_id} block attributes edited successfully.")
            else:
                print(f"No task found with ID: {task_id}")
        UserManagementState.get_user_tasks(LoginState.user_id)
