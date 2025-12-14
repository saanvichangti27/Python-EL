import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, datetime, timedelta, time
from fpdf import FPDF
import os

# 1. Session State Initialization
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'points' not in st.session_state:
    st.session_state.points = 0
if 'last_active' not in st.session_state:
    st.session_state.last_active = str(date.today() - timedelta(days=1))
if 'badge' not in st.session_state:
    st.session_state.badge = "Star ★"

def update_activity():
    if st.session_state.points <20:
        st.session_state.badge = "Star ★"
    elif st.session_state.points > 20 and st.session_state.points < 40:
        st.session_state.badge = "Gem 💎"
    elif st.session_state.points > 40:
        st.session_state.badge = "Master 👑"

def add_task():
    task_name = st.session_state["new_task_name"]
    task_deadline = st.session_state["new_task_deadline"]

    if task_name:
        st.session_state.tasks.append({
            "name": task_name, 
            "deadline": str(task_deadline), 
            "subtasks": [],
            "completed": False
        })
        st.session_state.points += 5
        st.session_state["new_task_name"] = ""
        update_activity()

# Callback to Add Subtask
def add_subtask(task_index):
    name_key = f"n{task_index}"
    type_key = f"t{task_index}"
    deadline_key = f"d{task_index}_deadline"
    
    sub_name = st.session_state[name_key]
    sub_type = st.session_state[type_key]
    sub_deadline = st.session_state[deadline_key]
    
    if sub_name:
        st.session_state.tasks[task_index]['subtasks'].append({
            "name": sub_name, 
            "deadline": str(sub_deadline), 
            "status": "In-progress",
            "start_date": str(date.today()), 
            "submitted_date": None, 
            "type": sub_type
        })
        st.session_state.points += 2
        st.session_state[name_key] = ""
        update_activity()

# 3. UI: Sidebar
st.sidebar.title("🎮 Scores")
st.sidebar.metric("Current Coins 🪙", st.session_state.points)
st.sidebar.metric(" Currect Badge", st.session_state.badge)

# 4. UI: Task Creation 
st.title("Task Completion Report Generator")
st.caption("Manage your Tasks and Gain Coins!")

with st.container():
    st.subheader("📝 Add Task")
    c_new1, c_new2 = st.columns([3, 1])
    
    with c_new1: 
        st.text_input("Task Name", key="new_task_name")
    with c_new2: 
        st.datetime_input("Due Date and Time", key="new_task_deadline")
    
    st.button("Create Task", on_click=add_task, type="primary")

st.divider()

# 5. UI: Task Management
st.subheader("📌 Your Tasks")

if not st.session_state.tasks:
    st.info("No tasks yet. Add to get started!")

for i, task in enumerate(st.session_state.tasks):
    # Visual Header for Task
    st.subheader(f" :blue[{task['name']}]")
    st.caption(f"📅 Due: {task['deadline']}")
    
    # Subtask Input Area
    with st.expander("Add Sub-tasks", expanded=True):
        c1, c2, c3, c4 = st.columns([2, 1.5, 1.5, 1])
        
        with c1: st.text_input("Subtask Name", key=f"n{i}")
        with c2: st.selectbox("Type", ["Must-do", "Optional"], key=f"t{i}")
        with c3: st.datetime_input("Due Date and Time", key=f"d{i}_deadline")
        with c4: 
            st.write("") # Spacer
            st.button("Add ➕", key=f"b{i}", on_click=add_subtask, args=(i,))

    # List Subtasks
    all_subs_done = True
    
    if task['subtasks']:
        st.markdown("**Progress:**")
        
    for j, sub in enumerate(task['subtasks']):
        col_mark, col_desc = st.columns([0.05, 0.95])
        status_text = f":blue[In Progress]"
        
        # Check if completed
        if sub['status'] == "Completed":
            status_text = f":green[Completed]"
        elif sub['status'] == "Over-due" or (sub['status'] == "In-progress" and str(datetime.now()) > sub['deadline']):
            sub["status"] = "Over-due"
            status_text = f":red[Over-due ⚠️]"
            
        with col_mark:
            is_checked = sub['status'] == "Completed"
            if st.checkbox("", value=is_checked, key=f"chk_{i}_{j}"):
                if sub['status'] != "Completed":
                    sub['status'] = "Completed"
                    sub['submitted_date'] = str(date.today())
                    st.session_state.points += 5
                    update_activity()
                    st.rerun()
            else:
                if sub['status'] == "Completed":
                    sub['status'] = "In-progress"
                    sub['submitted_date'] = None

        with col_desc:
            st.markdown(f"**{sub['name']}** | {status_text} | Due: {sub['deadline']}")
            
            if sub['status'] != "Completed":
                all_subs_done = False

    # Check Task Completion Bonus
    if all_subs_done and len(task['subtasks']) > 0 and not task['completed']:
        task['completed'] = True
        st.session_state.points += 10
        st.success(f"🎉 Task '{task['name']}' Completed! +10 Points Added!")
    update_activity()
    st.divider()

# 6. Graph Data Preparation
data = []
overdue_count = 0
completed_count = 0
in_progress_count = 0

for task in st.session_state.tasks:
    for sub in task['subtasks']:
        status = sub['status']
        if status == "Over-due": overdue_count += 1
        elif status == "Completed": completed_count += 1
        else: in_progress_count += 1

        data.append([task['name'], sub['name'], sub['deadline'], sub['submitted_date'] if sub['submitted_date'] else "N/A", sub['start_date'], status])

df = pd.DataFrame(data, columns=["Task", "Sub-task", "Deadline", "Submitted", "Start-date", "Status"])

# Only generate graph if there is data
if not df.empty:
    st.subheader("📊 Analytics")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    # Bar Chart
    status_counts = df['Status'].value_counts()
    color_map = {'Completed': 'green', 'In-progress': 'blue', 'Over-due': 'red'}
    bar_colors = [color_map.get(x, 'gray') for x in status_counts.index]
    
    status_counts.plot(kind='bar', ax=ax1, color=bar_colors)
    ax1.set_title("Task Status Distribution")
    
    # Pie Chart
    labels = ['Completed', 'In-Progress', 'Overdue']
    sizes = [completed_count, in_progress_count, overdue_count]
    if sum(sizes) > 0:
        ax2.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#90EE90', '#ADD8E6', '#FFCCCB'])
    ax2.set_title("Completion Rate")
    
    plt.tight_layout()
    plt.savefig("report_graph.png")
    st.image("report_graph.png")

# 7. Report Generation
if st.button("📄 Generate PDF Report", type="primary"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Task Completion Report", ln=True, align='C')
    
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {date.today()}", ln=True, align='C')
    pdf.ln(10)
    
    # Safe Badge
    safe_badge = st.session_state.badge.encode('ascii', 'ignore').decode('ascii')
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Current Points: {st.session_state.points} | Badge: {safe_badge}", ln=True)
    pdf.ln(5)

    if os.path.exists("report_graph.png"):
        pdf.image("report_graph.png", x=10, y=50, w=190)
    pdf.ln(100)

    # Table
    pdf.set_font("Arial", 'B', 10)
    # Headers
    headers = ["Task", "Sub-task", "Deadline", "Submitted", "Start-date", "Status"]
    widths = [30, 30, 40, 30, 30, 30]
    
    for i, col in enumerate(headers):
        pdf.cell(widths[i], 10, col, border=1)
    pdf.ln()
    
    pdf.set_font("Arial", size=9) # Slightly smaller font for timestamp
    for index, row in df.iterrows():
        # Iterate manually to match widths
        data_row = [str(item).encode('latin-1', 'ignore').decode('latin-1') for item in row]
        for i, text in enumerate(data_row):
            pdf.cell(widths[i], 10, text, border=1)
        pdf.ln()

    # Output
    pdf_output = pdf.output(dest='S').encode('latin-1', 'ignore')
    st.download_button("📥 Download PDF", data=pdf_output, file_name="task_report.pdf", mime="application/pdf")
    st.success("Report Ready! Click 'Download PDF' above.")