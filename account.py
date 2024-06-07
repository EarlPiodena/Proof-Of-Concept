import streamlit as st
import calendar
from datetime import datetime
import firebase_admin
import plotly.graph_objects as go

from streamlit_option_menu import option_menu

from firebase_admin import credentials, firestore
from firebase_admin import auth

@st.cache_resource
def initialize(creds):
    cred = credentials.Certificate(creds)
    firebase_admin.initialize_app(cred)
    return firestore.client()

def authentication():
    choice = st.selectbox('Login/Signup', ['Login', 'Sign Up'])

    def f(email):
        try:
            user = auth.get_user_by_email(email)
            st.success('Login Successful.')
            st.session_state['user'] = user.uid

            st.rerun()

        except Exception as e:
            st.warning('Login Failed')

    
    if choice == 'Login':

        email = st.text_input('Email Address')
        password = st.text_input('Password', type = 'password')

        login = st.button('Login')
        if login:
            f(email=email)
    
    else:

        email = st.text_input('Email Address')
        password = st.text_input('Password', type = 'password')

        if  st.button('Create Account'):
            user = auth.create_user(email = email, password = password)

            st.success('Account created Successfully.')
            st.markdown('Login using your Email and Password.')
            st.balloons()

def app():

    expenses_ref = db.collection('expenses')
    incomes_ref = db.collection('incomes')

    incomes = ["Salary", "Business", "Other Income"]
    expenses = ["Rent", "Utilities", "Groceries", "Car", "Savings", "Other Expenses"]
    currency = "AED"

    def period_data(period, collection):
        integer_pairs = {}  # Initialize an empty list to store filtered data
        documents = collection.get()
        for doc in documents:
            data = doc.to_dict()
            print("Document ID:", doc.id)  # Print document ID for debugging
            print("Document Data:", data)   # Print document data for debugging
            if data['period'] == period:
                for key, value in data.items():
                    if isinstance(value, int):
                        integer_pairs[key] = value
        return integer_pairs  

    years = [datetime.today().year, datetime.today().year - 1]
    months = list(calendar.month_name[1:])

    def get_all_periods():
        return [doc.id for doc in incomes_ref.stream()]

    hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_st_style, unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["Data Entry", "Data Visualization"],
        icons=["pencil-square","bar-chart-line-fill"],
        orientation="horizontal",
    )


    if selected == "Data Entry":
        st.header(f"Data Entry in {currency}")
        
        with st.form("entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            col1.selectbox("Select Month:", months, key="month")
            col2.selectbox("Select Year: ", years, key="year")

            "---"
            with st.expander("Income"):
                for income in incomes:
                    st.number_input(f"{income}:", min_value=0, format="%i", step=10, key=income)
            with st.expander("Expenses"):
                for expense in expenses:
                    st.number_input(f"{expense}:", min_value=0, format="%i", step=10, key=expense)
        
            "---"
            submitted = st.form_submit_button("Save Data")
            if submitted:
                period = str(st.session_state["year"]) + "_" + str(st.session_state["month"])
                incomes = {income: st.session_state[income] for income in incomes}
                expenses = {expense: st.session_state[expense] for expense in expenses}
                
                incomes['user'] = st.session_state['user']
                incomes['period'] = period

                expenses['user'] = st.session_state['user'] 
                expenses['period'] = period

                incomes_doc_ref = incomes_ref.document(incomes['period'])
                expenses_doc_ref = expenses_ref.document(expenses['period'])

                incomes_doc_ref.set(incomes)
                expenses_doc_ref.set(expenses)    

                st.success("Data Saved.")


    if selected == "Data Visualization":
        st.header("Data Visualization")
        with st.form("saved_periods"):
            period = st.selectbox("Select Date:", get_all_periods())
            submitted = st.form_submit_button("Plot Date")
            if submitted:

                incomes = period_data(period, incomes_ref)
                expenses = period_data(period, expenses_ref)

                total_income = sum(incomes.values())
                total_expense = sum(expenses.values())
                remaining_budget = total_income - total_expense
                col1, col2, col3, = st.columns(3)
                col1.metric("Total Income", f"{total_income} {currency}")
                col2.metric("Total Expense", f"{total_expense} {currency}")
                col3.metric("Remaining Budget", f"{remaining_budget} {currency}")

                label = list(incomes.keys()) + ["Total Income"] + list(expenses.keys())
                source = list(range(len(incomes))) + [len(incomes)] * len(expenses)
                target = [len(incomes)] * len(incomes) + [label.index(expense) for expense in expenses.keys()]
                value = list(incomes.values()) + list(expenses.values())

                link = dict(source=source, target=target, value=value)
                node = dict(label=label, pad=20, thickness=30, color="#006400")
                data = go.Sankey(link=link, node=node)

                fig = go.Figure(data)
                fig.update_layout(margin=dict(l=0, r=0, t=5, b=5))
                st.plotly_chart(fig, use_container_width=True)


        logout = st.button('Logout')
        if logout:
            st.session_state['user'] = None
            st.rerun()

if __name__ == '__main__':
    page_title = "Track:green[ME]"
    page_icon = ":bank:"
    layout = "centered"

    st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
    st.title(page_title + " " + page_icon)

    if 'user' not in st.session_state:
        st.session_state['user'] = None

    initialize(creds=dict(st.secrets['FIREBASE_CREDS']))
    db = firestore.client()

    if st.session_state['user']:
        app()
    else:
        authentication()
