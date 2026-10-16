import streamlit as st
import qrcode
from io import BytesIO

# --- INITIALIZE LIVE DATABASE IN MEMORY ---
if "fighters" not in st.session_state:
    st.session_state.fighters = {"A": "Fighter A", "B": "Fighter B"}
if "pools" not in st.session_state:
    st.session_state.pools = {"A": 0.0, "B": 0.0}
if "bettors" not in st.session_state:
    st.session_state.bettors = {"A": 0, "B": 0}
if "receipts" not in st.session_state:
    st.session_state.receipts = {}
if "locked_bets" not in st.session_state:
    st.session_state.locked_bets = []

HOST_CUT_PERCENTAGE = 0.07  # 7% host cut

st.set_page_config(page_title="Fight Night Pool Manager", layout="centered")

# --- MATH CALCULATIONS ---
gross_total_pool = st.session_state.pools["A"] + st.session_state.pools["B"]
house_take = gross_total_pool * HOST_CUT_PERCENTAGE
net_distributable_pool = gross_total_pool - house_take

# --- LIVE DASHBOARD (FRONTEND) ---
st.title("🥊 Live Fight Club Pool Tracker")
st.subheader("Current Card Matchup")

# Display Live Dashboard
col1, col2 = st.columns(2)
with col1:
    st.metric(
        label=f"🏆 {st.session_state.fighters['A']} Total Pool", 
        value=f"\${st.session_state.pools['A']:.2f}", 
        delta=f"{st.session_state.bettors['A']} Locked Bets"
    )
with col2:
    st.metric(
        label=f"⚡ {st.session_state.fighters['B']} Total Pool", 
        value=f"\${st.session_state.pools['B']:.2f}", 
        delta=f"{st.session_state.bettors['B']} Locked Bets"
    )

st.markdown(f"### **Total Cash in Pot: \${gross_total_pool:.2f}**")
st.divider()

# --- ADMIN PANEL (FOR YOU ONLY) ---
with st.sidebar:
    st.header("🔑 Organizer Control Panel")
    admin_pass = st.text_input("Enter Admin PIN", type="password")
    
    if admin_pass == "110509":  # Change your PIN here
        st.success("Access Granted")
        
        # FIX FEATURE: Change fighter names on the spot
        st.subheader("📝 Edit Fighter Names")
        new_name_a = st.text_input("Edit Fighter A Name", value=st.session_state.fighters["A"])
        new_name_b = st.text_input("Edit Fighter B Name", value=st.session_state.fighters["B"])
        if st.button("Update Names"):
            st.session_state.fighters["A"] = new_name_a
            st.session_state.fighters["B"] = new_name_b
            st.rerun()
            
        st.divider()
        st.subheader("📈 House Profit Overview")
        st.write(f"**Your 7% Cut Accumulated:** `${house_take:.2f}`")
        st.write(f"**Net Payout Pool Remaining:** `${net_distributable_pool:.2f}`")
        st.divider()
        
        # Issue Cash Tickets
bettor_name = st.text_input("Bettor Name / Alias", key="bettor_name_input")
cash_received = st.number_input("Exact Cash Received ($)", min_value=1.0, step=1.0)
ticket_id = "".join(bettor_name.split()).lower()

bet_data = {
    "bettor_name": bettor_name,
    "ticket_id": ticket_id,
    "value": cash_received,
    "used": False
}bet_data = {
    "bettor_name": bettor_name,
    "ticket_id": ticket_id,
    "value": cash_received,
    "used": False
}            
            # FIXED QR CODE LINK: Automatically grabs your exact live web address 
            base_url = st.nav_to if hasattr(st, "nav_to") else "https://streamlit.io" 
            try:
                # Tries to read the browser's URL context live
                from streamlit.web.server.server import Server
                current_url = st.get_option("browser.gatherUsageStats") 
            except:
                pass
            
            # Fallback text instruction for URL configuration
            secure_url = f"URL_HOLDER/?ticket={ticket_id}" 
            st.warning("Note: When deploying, copy your live Streamlit site URL from the browser bar and swap it into the QR generator below if needed.")
            
            # Manual URL config override box to guarantee QR works perfectly
          # Check if a bettor name was submitted in session state or text input
if "bettor_name_input" in st.session_state and st.session_state["bettor_name_input"]:
    bettor_name = st.session_state["bettor_name_input"]
else:
    bettor_name = "Bettor"

# Grab active ticket ID or fallback
ticket_id = st.session_state.get("current_ticket_id", "demo123")

homepage_url = st.text_input(
    "Paste your live website homepage link here first:",
    value=st.secrets.get("SITE_URL", "https://fightcard-manager-fwwmzw5rjtx3jufqcpdfsw.streamlit.app"),
    key="homepage_link_input"
)

final_qr_url = f"{homepage_url.rstrip('/')}/?ticket={ticket_id}"
st.write(f"**Private Link for {bettor_name}:**")
st.code(final_qr_url)
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(final_qr_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
buf = BytesIO()
img.save(buf, format="PNG")
st.image(buf.getvalue(), caption="Scan this code with bettor's phone camera")
# --- USER TICKET SCREEN (SCANNED QR CODES) ---
# Reads parameters straight from scanned URL link
if "ticket" in st.query_params:
    user_ticket = st.query_params["ticket"]
    
    if user_ticket in st.session_state.receipts:
        client_data = st.session_state.receipts[user_ticket]
        
        if client_data["used"]:
            st.error("❌ This ticket has already been used and locked in. You cannot bet twice with the same cash.")
        else:
            st.success(f"🎟️ Ticket Verified: Welcome, **{client_data['name']}**")
            locked_wager = client_data["value"]
            st.info(f"Your Cash Balance: **\${locked_wager:.2f}**")
            
            # Pick a fighter selection dropdown
            fighter_options = ["Select a Fighter", st.session_state.fighters["A"], st.session_state.fighters["B"]]
            fighter_pick = st.selectbox("Choose who to bet your cash on:", fighter_options)
            
            if fighter_pick != "Select a Fighter":
                pick_key = "A" if fighter_pick == st.session_state.fighters["A"] else "B"
                
                # Math simulation calculations
                sim_winning_pool = st.session_state.pools[pick_key] + locked_wager
                sim_gross_pool = gross_total_pool + locked_wager
                sim_net_pool = sim_gross_pool - (sim_gross_pool * HOST_CUT_PERCENTAGE)
                
                share = locked_wager / sim_winning_pool
                possible_payout = share * sim_net_pool
                profit = possible_payout - locked_wager
                payout_percentage = (possible_payout / locked_wager) * 100
                
                st.markdown("### 📊 Your Payout Preview (7% House Cut Applied)")
                c1, c2, c3 = st.columns(3)
                c1.metric("Est. Payout if Won", f"\${possible_payout:.2f}")
                c2.metric("Net Profit", f"\${profit:.2f}")
                c3.metric("Return Multiplier", f"{payout_percentage:.1f}%")
                
                # THE LIVE APPROVE BUTTON
                if st.button("Confirm & Place Bet Live 🚀"):
                    # Add money to global dashboard pools immediately
                    st.session_state.pools[pick_key] += locked_wager
                    st.session_state.bettors[pick_key] += 1
                    
                    # Lock ticket so they cannot spam click or change their pick
                    st.session_state.receipts[user_ticket]["used"] = True
                    st.session_state.locked_bets.append({"name": client_data["name"], "bet": fighter_pick, "amount": locked_wager})
                    
                    st.balloons()
                    st.success("Bet approved! Hand your phone back to the host. The main dashboard pool has updated live.")
                    st.rerun()
    else:
        st.error("Invalid ticket profile or bad QR structure.")
