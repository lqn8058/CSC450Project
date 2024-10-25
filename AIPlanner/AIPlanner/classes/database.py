"""Module containing classes and methods pertaining to the SQLite database built into Reflex"""
from datetime import date, time, timedelta
from typing import List, Optional
import random

import reflex as rx
import sqlmodel
from rxconfig import config

class User(rx.Model, table=True):
    """Class that defines the User table in the SQLite database
    
    Attributes:
        username: A unique string identifier, allows users 
                  to sign in without a canvas_hash_id specified
        canvas_hash_id: A unique integer identifier, allows tasks to be imported from Canvas
        password: A string used to authenticate user login
    """
    username: str
    canvas_hash_id: int
    password: str
    tasks: List["Task"] = sqlmodel.Relationship(back_populates="user")

class Task(rx.Model, table=True):
    """Class that defines the Task table in the SQLite database"""
    recur_frequency: int
    due_date: date
    is_deleted: bool
    task_name: str
    description: str
    task_id: int
    priority_level: int
    assigned_block_date: date
    assigned_block_start_time: time
    assigned_block_duration: timedelta
    user_id: int = sqlmodel.Field(foreign_key="user.canvas_hash_id")
    user: Optional[User] = sqlmodel.Relationship(back_populates="tasks")

class UserManagementState(rx.State):
    """Class that defines the state in which variables are held relating to user management"""
    users: list[User] = []  # To hold the list of users
    message: str = ""        # To display success or error messages
    tasks: list[Task]

    def get_user_tasks(self, user_id: int):
        """Method to retrieve all tasks for a given user"""
        with rx.session() as session:
            self.tasks = session.exec(
                Task.select().where(Task.user_id == user_id)
            ).all()

    def fetch_all_users(self):
        """Method to retrieve all usernames in the database"""
        with rx.session() as session:
            # Retrieve all users from the database
            self.users = session.exec(User.select()).all()
            self.message = f"Retrieved {len(self.users)} users."
            print(self.users)

    def add_test_user(self):
        """Method to insert test users into the database"""
        create_user("Test", random.randint(850000000,850999999), "test11")


class AddUser(rx.State):
    """Class that enables adding users to the database"""
    username: str
    canvas_hash_id: int
    password: str

    def set_username(self, value: str):
        """Initializing username"""
        self.username = value

    def set_canvas_hash_id(self, value: int):
        """Initializing user canvas ID"""
        self.canvas_hash_id = value

    def set_password(self, value: str):
        """Initializing user's password"""
        self.password = value

    # def add_user(self, new_user:User):
    #     """Function to add users"""
    #     with rx.session() as session:
    #         session.add(
    #             User(
    #                 username=self.username,
    #                 canvas_hash_id=self.canvas_hash_id,
    #                 password=self.password
    #             )
    #         )
    #         session.commit()


def create_user(username:str, canvas_hash_id:int, password:str):
    """
    Function that creates a User function and calls add_user function with that User object.
    """
    new_user = User(username=username, canvas_hash_id=canvas_hash_id, password=password)
    add_user(new_user=new_user)
    

def add_user(new_user:User):
    """
    Starts a database session and adds the new_user User object into the database.
    """
    with rx.session() as session:
        session.add(new_user)
        session.commit()

def get_user_tasks(session: rx.session, user_id: int) -> List[Task]:
    """
    Retrieve all tasks associated with a specific user ID.
    """
    statement = User.select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()
    return tasks
