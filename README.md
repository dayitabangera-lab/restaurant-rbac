Restaurant Owner RBAC Web Application

Description
This project is a simple Role-Based Access Control (RBAC) web application developed using Flask and SQLite.

The application authenticates a Restaurant Owner and displays only the activities assigned to that role.

-Sample Login
Login ID:owner1
Password:owner123

-How to Run
1. Install Flask

```bash
pip install flask
```

2. Run the application

```bash
python app.py
```

3. Open your browser and visit

```
http://127.0.0.1:5000
```

Technologies Used
- Python 3
- Flask
- SQLite
- HTML
- CSS

Database Schema

Role
- RoleId
- RoleName

User
- UserId
- UserName
- LoginId
- Pwd
- RoleId

Activity
- ActivityId
- ActivityName
- ParentActivityId
- AccessDetail

Responsibility
- RoleId
- ActivityId




