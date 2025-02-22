import streamlit as st
import json
import datetime
import plotly.express as px



def create_is_not_exists():
    try:
        with open("data.json", "r") as f:
            pass
    except FileNotFoundError:
        with open("data.json", "w") as f:
            data = {
                "name": "",
                "saldo": {
                    "USD": 0,
                    "EUR": 0,
                    "CUP": 0,
                },
                "expenses": {
                },
                "income": {
                },
                "Loans":{

                },
            }
            json.dump(data, f, indent=4)

def possible_expense_reasons():
    return [
        "Food",
        "Transport",
        "Rent",
        "Health",
        "Education",
        "Entertainment",
        "Home",
        "Clothing",
        "Gift",
        "Other",
    ]

def possible_income_reasons():
    return [
        "Salary",
        "Freelance",
        "Investment",
        "Gift",
        "Selling",
        "Rent",
        "Other",
    ]

def possible_currencies():
    return ["USD", "EUR", "CUP", "CUP card"]

def create_money_log(amount, currency, reason):
    return {
        "amount": amount,
        "currency": currency,
        "reason": reason,
        "date": datetime.datetime.now().strftime("%d-%m-%Y"),
    }
def load_data():
    create_is_not_exists()
    with open("data.json", "r") as f:
        data = json.load(f)
    return data

def save_name(name, data):
    data["name"] = name
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    return data

def save_income(amount, currency,reason, data):
    # get the current month
    record = create_money_log(amount, currency, reason)
    key = record["date"][3:]
    if key not in data["income"]:
        data["income"][key] = []
    if currency not in data["saldo"]:
        data["saldo"][currency] = 0

    data["income"][key].append(record)
    data["saldo"][currency] += amount
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    return data

def save_expense(amount, currency, reason, data):
    record = create_money_log(amount, currency, reason)
    key = record["date"][3:]
    if key not in data["expenses"]:
        data["expenses"][key] = []
    if currency not in data["saldo"]:
        data["saldo"][currency] = 0

    if data["saldo"][currency] < amount:
        st.error("You don't have enough money")
        return None

    data["expenses"][key].append(record)
    data["saldo"][currency] -= amount

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    return data


def show_saldo(data):
    st.write("### Current Saldo")

    # Create a pie chart for saldo using plotly
    labels = list(data["saldo"].keys())
    values = list(data["saldo"].values())
    labels = [f"{label} ({value})" for label, value in zip(labels, values)]

    fig = px.pie(names=labels, values=values, title="Saldo Distribution")
    st.plotly_chart(fig)

def show_loans(data):
    st.write("### Loans")
    if not data['Loans']:
        st.write("No loans found")
        return
    for person, info in data['Loans'].items():
        st.write(f"#### {person}")
        for currency, amount in info['owe'].items():
            st.write(f"{currency}: {amount}")

def _add_income(data):
    amount = st.number_input("Amount", key="income_amount")
    currency = st.selectbox("Currency", possible_currencies(), key="income_currency")
    reason = st.selectbox("Reason", possible_income_reasons(), key="income_reason")
    if st.button("Accept Income"):
        data = save_income(amount, currency, reason, data)
        st.session_state.data = data
        st.success("Income added successfully!")
    return data

def _add_expense(data):
    amount = st.number_input("Amount", key="expense_amount")
    currency = st.selectbox("Currency", possible_currencies(), key="expense_currency")
    reason = st.selectbox("Reason", possible_expense_reasons(), key="expense_reason")
    if st.button("Accept Expense"):
        data_ = save_expense(amount, currency, reason, data)
        if data_ is not None:
            st.session_state.data = data_
            st.success("Expense added successfully!")
            data = data_
        else:
            st.error("Expense not added")
    return data

def exchange_(data, from_currency, to_currency, amount, exchange_rate):
    if from_currency not in data["saldo"]:
        st.error("You don't have enough money")
        return None
    if data["saldo"][from_currency] < amount:
        st.error("You don't have enough money")
        return None

    # exchange rate will always be according to CUP
    if to_currency not in ["CUP", "CUP card"]:
        exchange_rate = 1 / exchange_rate

    data["saldo"][from_currency] -= amount
    data["saldo"][to_currency] += amount * exchange_rate

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    return data

def loan_(data, from_user, to_user, amount, currency, other_person):
    if not data['Loans']:
        data['Loans'] = {}
    if data['Loans'] is None:
        data['Loans'] = {}
    if other_person not in data['Loans']:
        data['Loans'][other_person] = {}
    if 'owe' not in data['Loans'][other_person]:
        data['Loans'][other_person]['owe'] = {}
    if currency not in data['Loans'][other_person]['owe']:
        data['Loans'][other_person]['owe'][currency] = 0

    if from_user == 'Me':
        if to_user == 'Me':
            st.error("You can't loan money to yourself")
            return None
        else:
            data['Loans'][other_person]['owe'][currency] += amount
    else:
        if to_user == 'Me':
            data['Loans'][other_person]['owe'][currency] -= amount
            if data['Loans'][other_person]['owe'][currency] == 0:
                del data['Loans'][other_person]['owe'][currency]
        else:
            st.error("You have to be involved in the loan")
            return None

    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)
    return data



def _change_name(data):
    name = st.text_input("Name", key="name_input")
    if st.button("Accept Name"):
        data = save_name(name, data)
        st.session_state.data = data
        st.success("Name updated successfully!")
    return data


def show_breakdown(income=False, expense=False, key=None):
    if income:
        st.write("### Income Breakdown")
        _data = st.session_state.data["income"]
    elif expense:
        st.write("### Expense Breakdown")
        _data = st.session_state.data["expenses"]
    else:
        return

    if key is None:
        key = create_money_log(0, "", "").get("date")[3:]

    if key not in _data:
        st.write("No records found for this month")
        return

    records = _data[key]
    reasons = {}
    for record in records:
        reason = record["reason"]
        if reason not in reasons:
            reasons[reason] = {}
        currency = record["currency"]
        if currency not in reasons[reason]:
            reasons[reason][currency] = 0
        reasons[reason][currency] += record["amount"]

    labels = []
    values = []
    for reason, currencies in reasons.items():
        for currency, amount in currencies.items():
            labels.append(f"{reason} ({currency})")
            values.append(amount)

#     bar graph
    fig = px.bar(x=labels, y=values, title=f"Breakdown for {key}")
    st.plotly_chart(fig)


def _exchange_money(data):
    from_currency = st.selectbox("From Currency", possible_currencies(), key="from_currency")
    to_currency = st.selectbox("To Currency", possible_currencies(), key="to_currency")
    amount = st.number_input("Amount", key="exchange_amount")
    exchange_rate = st.number_input("Exchange Rate", key="exchange_rate")
    if st.button("Exchange Money"):
        data_ = exchange_(data, from_currency, to_currency, amount, exchange_rate)
        if data_ is not None:
            data = data_
            st.success("Money exchanged successfully!")
            st.session_state.data = data
    return data

def _loan_money(data):
    from_user = st.selectbox("From", ['Me', 'Other'], key="from_user")
    to_user = st.selectbox("To", ['Me', 'Other'], key="to_user")
    amount = st.number_input("Amount", key="loan_amount")
    currency = st.selectbox("Currency", possible_currencies(), key="loan_currency")
    other_person = st.text_input("Other Person", key="loan_person")
    if st.button("Save Loan"):
        data_ = loan_(data, from_user, to_user, amount, currency, other_person)
        if data_ is not None:
            data = data_
            st.success("Money loaned successfully!")
            st.session_state.data = data
    return data



def main():
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

    data = st.session_state.data

    st.title(f"Spending")

    # Use st.expander to hide sections
    with st.expander("Show Saldo"):
        show_saldo(data)

    with st.expander("Show Loans"):
        show_loans(data)

    with st.expander("Income Breakdown"):
        show_breakdown(income=True)

    with st.expander("Expense Breakdown"):
        show_breakdown(expense=True)

    # Use st.expander to hide sections
    with st.expander("Change Name"):
        data = _change_name(data)

    with st.expander("Add Income"):
        data = _add_income(data)
        st.session_state.data = data

    with st.expander("Add Expense"):
        data = _add_expense(data)
        st.session_state.data = data

    with st.expander("Exchange Money"):
        data = _exchange_money(data)
        st.session_state.data = data

    with st.expander("Loan Money"):
        data = _loan_money(data)
        st.session_state.data = data


if __name__ == "__main__":
    main()