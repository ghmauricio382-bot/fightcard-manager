import streamlit as st
import qrcode
from io import BytesIO

# --- CONFIGURATION ---
HOST_CUT_PERCENTAGE = 0.07  # 7% cut goes to you as the organizer

st.set_page_config(page_title="Fight Club Pool Dashboard", layout="centered")

# --- INITIALIZE SECURE SIMULATED DATABASE ---
if "bets" not in st.session_state:
    st.session_state.bets = {
        "Fighter A": {"total_cash": 400.0, "bettors_count": 8},
        "Fighter B": {"total_cash": 460.0, "bettors_count": 10}
    }
if "receipts" not in st.session_state:
    st.session_state.receipts = {}

# --- LIVE POOL MATHEMATICS ---
pool_a = st.session_state.bets["Fighter A"]["total_cash"]
pool_b = st.session_state.bets["Fighter B"]["total_cash"]
gross_total_pool = pool_a + pool_b

# Calculate the house cut and the net pool that actually gets distributed
house_take = gross_total_pool * HOST_CUT_PERCENTAGE
net_distributable_pool = gross_total_pool - house_take

# --- FRONTEND INTERFACE ---
st.title("🥊 Private Fight Club Pool Tracker")
st.subheader("Upcoming Event Card")
st.write("**Date:** Saturday Night | Doors close at 9:00 PM")

# Live Feed of the Pools
col1, col2 = st.columns(2)
with col1:
    st.metric(label="🏆 Fighter A Total Pool", value=f"\${pool_a:.2f}", delta=f"{st.session_state.bets['Fighter A']['bettors_count']} Bettors")
with col2:
    st.metric(label="⚡ Fighter B Total Pool", value=f"\${pool_b:.2f}", delta=f"{st.session_state.bets['Fighter B']['bettors_count']} Bettors")

st.markdown(f"### **Total Cash in Pot: \${gross_total_pool:.2f}**")
st.divider()

# --- ADMIN DOOR (FOR YOUR EYES ONLY) ---
with st.sidebar:
    st.header("🔑 Organizer Control Panel")
    admin_pass = st.text_input("Enter Admin PIN", type="password")
    
    if admin_pass == "1234": # Change this to your private code
        st.success("Access Granted")
        
        # Financial Overview for the Host
        st.subheader("📈 House Finances")
        st.write(f"**Your 7% Cut Accumulated:** `${house_take:.2f}`")
        st.write(f"**Net Payout Pool Remaining:** `${net_distributable_pool:.2f}`")
        st.divider()
        
        st.subheader("Issue Cash Receipt")
        bettor_name = st.text_input("Bettor Name / Alias")
        cash_received = st.number_input("Exact Cash Handed to You (\$)", min_value=1.0, step=1.0)
        
        if st.button("Generate Secure Ticket Link"):
            ticket_id = "".join(bettor_name.split()).lower()
            st.session_state.receipts[ticket_id] = {
                "name": bettor_name,
                "value": cash_received
            }
            secure_url = f"https://streamlit.app{ticket_id}"
            st.write(f"**Private Link for {bettor_name}:**")
            st.code(secure_url)
            
            # Make a QR code to display on your phone/laptop screen
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(secure_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            buf = BytesIO()
            img.save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Scan to open private wager room")

# --- USER TICKET SCREEN (SCANNED QR VIEW) ---
query_params = st.query_params

if "ticket" in query_params:
    user_ticket = query_params["ticket"]
    
    if user_ticket in st.session_state.receipts:
        client_data = st.session_state.receipts[user_ticket]
        st.success(f"🎟️ Secure Ticket Verified: Welcome, **{client_data['name']}**")
        
        locked_wager = client_data["value"]
        st.info(f"Your Verified Cash Wager Balance: **\${locked_wager:.2f}**")
        
        fighter_pick = st.selectbox("Simulate your wager outcome:", ["Select a Fighter", "Fighter A", "Fighter B"])
        
        if fighter_pick != "Select a Fighter":
            if fighter_pick == "Fighter A":
                sim_winning_pool = pool_a + locked_wager
                sim_gross_pool = gross_total_pool + locked_wager
            else:
                sim_winning_pool = pool_b + locked_wager
                sim_gross_pool = gross_total_pool + locked_wager
            
            # MATH RULE: Take out your 7% before calculating individual slices
            sim_house_take = sim_gross_pool * HOST_CUT_PERCENTAGE
            sim_net_pool = sim_gross_pool - sim_house_take
            
            # User's share of the winning side
            share = locked_wager / sim_winning_pool
            possible_payout = share * sim_net_pool
            profit = possible_payout - locked_wager
            payout_percentage = (possible_payout / locked_wager) * 100
            
            # Display metrics to the bettor
            st.markdown("### 📊 Your Payout Scenarios (After 7% Host Fee)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Est. Total Payout", f"\${possible_payout:.2f}")
            c2.metric("Net Profit", f"\${profit:.2f}")
            c3.metric("Return Rate", f"{payout_percentage:.1f}%")
            
            if st.button("Confirm and Lock This Bet Permanently"):
                st.balloons()
                st.success(f"Bet Locked! \${locked_wager} placed on {fighter_pick}.")
    else:
        st.error("Invalid or expired digital ticket QR code.")
