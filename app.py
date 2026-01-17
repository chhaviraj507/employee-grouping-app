import streamlit as st
import pandas as pd

st.set_page_config(page_title="Employee Grouping", layout="wide")

LIMIT_DEFAULT = 48500
LEADERS_DEFAULT = 15


# ---------- Grouping function ----------
def group_employees(employees, leaders, LIMIT):
    emp_dict = {name: salary for name, salary in employees}

    # Validation
    for leader in leaders:
        if leader not in emp_dict:
            return None, [f"Leader '{leader}' not found in employees list."]

    if len(set(leaders)) != len(leaders):
        return None, ["Duplicate leader names found."]

    # Groups: leader is included
    groups = {leader: [(leader, emp_dict[leader])] for leader in leaders}
    group_sum = {leader: emp_dict[leader] for leader in leaders}

    # Remaining employees
    remaining_employees = [(n, s) for n, s in employees if n not in leaders]
    remaining_employees.sort(key=lambda x: x[1], reverse=True)

    unassigned = []

    # Assign employees to least loaded group
    for emp_name, emp_salary in remaining_employees:
        assigned = False
        leaders_sorted = sorted(leaders, key=lambda l: group_sum[l])

        for leader in leaders_sorted:
            if group_sum[leader] + emp_salary <= LIMIT:
                groups[leader].append((emp_name, emp_salary))
                group_sum[leader] += emp_salary
                assigned = True
                break

        if not assigned:
            unassigned.append((emp_name, emp_salary))

    return (groups, group_sum, unassigned), []


# ---------- UI ----------
st.title("✅ Employee Grouping System (Free Student Project)")
st.write(
    "Make groups under a salary limit. Leaders are employees (their salary is included in group total)."
)

col1, col2 = st.columns(2)

with col1:
    LIMIT = st.number_input("Salary LIMIT per group", value=LIMIT_DEFAULT, step=500)

with col2:
    LEADERS = st.number_input("Number of Leaders (Groups)", value=LEADERS_DEFAULT, step=1)

st.divider()

input_method = st.radio("Choose input method:", ["Manual Input", "Excel Upload"])

employees = []
leaders = []

# ---------- Manual Input ----------
if input_method == "Manual Input":
    st.subheader("✍️ Manual Employee Input")
    n = st.number_input("Total Employees", min_value=1, value=10, step=1)

    emp_data = []
    for i in range(int(n)):
        c1, c2 = st.columns([2, 1])

        with c1:
            name = st.text_input(f"Employee {i+1} Name", key=f"emp_name_{i}")

        with c2:
            salary = st.number_input(
                f"Salary", min_value=0, value=0, step=500, key=f"emp_salary_{i}"
            )

        if name.strip():
            emp_data.append((name.strip(), int(salary)))

    employees = emp_data

    st.subheader("👑 Leaders (must be from employees list)")
    leader_input = st.text_area(
        f"Enter exactly {int(LEADERS)} leader names (one name per line):",
        height=160,
    )
    leaders = [x.strip() for x in leader_input.split("\n") if x.strip()]

# ---------- Excel Input ----------
else:
    st.subheader("📂 Upload Excel File")
    st.info(
        "Excel format:\n\n"
        "Sheet 1: Employees  (columns: Name, Salary)\n"
        "Sheet 2: Leaders   (column: LeaderName)"
    )

    uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

    if uploaded_file:
        try:
            emp_df = pd.read_excel(uploaded_file, sheet_name="Employees")
            lead_df = pd.read_excel(uploaded_file, sheet_name="Leaders")

            employees = list(zip(emp_df["Name"].astype(str), emp_df["Salary"].astype(int)))
            leaders = lead_df["LeaderName"].astype(str).tolist()

            st.success("Excel loaded successfully ✅")

            st.write("Employees Preview:")
            st.dataframe(emp_df, use_container_width=True)

            st.write("Leaders Preview:")
            st.dataframe(lead_df, use_container_width=True)

        except Exception as e:
            st.error(f"Excel reading error: {e}")

# ---------- Process ----------
st.divider()

if st.button("✅ Make Groups"):
    if not employees:
        st.error("Please enter employees first.")

    elif len(leaders) != int(LEADERS):
        st.error(f"You must enter exactly {int(LEADERS)} leaders.")

    else:
        result, errors = group_employees(employees, leaders, LIMIT)

        if errors:
            for er in errors:
                st.error(er)

        else:
            groups, group_sum, unassigned = result

            st.subheader("📌 Groups Output")

            for i, leader in enumerate(leaders, start=1):
                st.markdown(
                    f"### Group {i} — Leader: **{leader}** | Total Salary: **{group_sum[leader]}**"
                )
                df = pd.DataFrame(groups[leader], columns=["Name", "Salary"])
                st.dataframe(df, use_container_width=True)

            if unassigned:
                st.subheader("❌ Unassigned Employees")
                st.warning("These employees could not be assigned because all groups exceed LIMIT.")
                un_df = pd.DataFrame(unassigned, columns=["Name", "Salary"])
                st.dataframe(un_df, use_container_width=True)
            else:
                st.success("✅ All employees successfully assigned into groups.")

            # Download CSV output
            all_rows = []
            for leader in leaders:
                for name, sal in groups[leader]:
                    all_rows.append({"Leader": leader, "Employee": name, "Salary": sal})

            output_df = pd.DataFrame(all_rows)

            st.download_button(
                label="⬇️ Download Grouping Result (CSV)",
                data=output_df.to_csv(index=False).encode("utf-8"),
                file_name="grouping_result.csv",
                mime="text/csv",
            )
