import streamlit as st
import urllib.parse

# --- 1. SETTINGS & APP CONSTANTS ---
st.set_page_config(page_title="Fight Night Pool Manager", layout="centered")
HOST_CUT_PERCENTAGE = 0.07  # Your 7% host cut

query_params = st.query_params

# --- 2. 🌐 GLOBAL SHARED DATABASE CLASS ---
@st.cache_resource
class SharedFightNightDatabase:
    def __init__(self):
        self.fighters = {"A": "Mario", "B": "Alejandro"}
        self.pools = {"A": 0.0, "B": 0.0}
        self.bettors = {"A": 0, "B": 0}
        self.locked_bets = []

db = SharedFightNightDatabase()

# Global Mathematical Calculations
gross_total_pool = db.pools["A"] + db.pools["B"]
house_take = gross_total_pool * HOST_CUT_PERCENTAGE
net_distributable_pool = gross_total_pool - house_take

# --- 3. THE THREE TERMINAL ROUTING SYSTEMS ---

if "ticket" in query_params:
    # ==========================================
    # 📱 PRIVATE BETTOR TICKET RECEIPT VIEW
    # ==========================================
    ticket_id = query_params["ticket"]
    st.title("🎟️ Your Personal Bet Receipt")
    st.markdown("---")
    
    found_bet = next((bet for bet in db.locked_bets if bet["ticket_id"] == ticket_id), None)
    
    if found_bet:
        st.subheader(f"Bettor: **{found_bet['name']}**")
        
        my_fighter = found_bet['fighter']
        my_amount = found_bet['amount']
        choice_key = found_bet['choice_key']
        
        current_fighter_pool = db.pools[choice_key]
        share_percentage = my_amount / current_fighter_pool if current_fighter_pool > 0 else 0
        possible_payout = share_percentage * net_distributable_pool
        
        st.metric(label="Your Cash Staked", value=f"${my_amount:,.2f}")
        st.metric(label="Your Selected Fighter", value=str(my_fighter))
        
        col1, col2 = st.columns(2)
        col1.metric(label="Your Current Pool Share", value=f"{share_percentage*100:.1f}%")
        col2.metric(label="Your Projected Payout", value=f"${possible_payout:,.2f}")
        
        st.caption("⚠️ Your payout amount updates automatically as more cash entries are added to the live pools.")
    else:
        st.error("Ticket transaction lookup error. Please verify with organizer.")


elif query_params.get("view") == "admin":
    # ==========================================
    # 🛡️ ORGANIZER CENTRAL CONTROL PANEL
    # ==========================================
    st.title("Admin Master Control Panel")
    
    with st.sidebar:
        st.header("🔒 Authorization")
        admin_pass = st.text_input("Enter Admin PIN", type="password")
        
    if admin_pass == "110509":
        st.success("Access Granted")
        
        st.subheader("📝 Setup Current Matchup")
        new_name_a = st.text_input("Fighter A Name", value=db.fighters["A"])
        new_name_b = st.text_input("Fighter B Name", value=db.fighters["B"])
        if st.button("Save & Update Match Names"):
            db.fighters["A"] = new_name_a
            db.fighters["B"] = new_name_b
            st.success("Names synchronized across all screens globally!")
            st.rerun()
            
        st.markdown("---")
        
        st.subheader("💵 Add In-Person Cash Bet")
        inbound_name = st.text_input("Customer Name / Ticket Alias")
        inbound_cash = st.number_input("Cash Collected ($)", min_value=1.0, value=20.0, step=5.0)
        selected_target = st.radio("Fighter Chosen", (db.fighters["A"], db.fighters["B"]))
        
        if st.button("Lock Bet & Generate Receipt QR"):
            if not inbound_name.strip():
                st.error("Please assign a customer name to compile the bet sheet record.")
            else:
                target_key = "A" if selected_target == db.fighters["A"] else "B"
                new_id = f"FIGHT-{len(db.locked_bets) + 1001}"
                
                db.pools[target_key] += inbound_cash
                db.bettors[target_key] += 1
                db.locked_bets.append({
                    "ticket_id": new_id,
                    "name": inbound_name,
                    "fighter": selected_target,
                    "amount": inbound_cash,
                    "choice_key": target_key
                })
                st.success(f"Bet Authenticated! Ticket ID: {new_id}")
                st.balloons()
                st.rerun()

        # FOOLPROOF GOOGLE API QR GENERATOR
        if db.locked_bets:
            last_bet = db.locked_bets[-1]
            st.markdown("---")
            st.subheader(f"📱 QR Code Receipt for {last_bet['name']}")
            st.info("Scan this code right now to open the live personal ticket screen:")
            
            # Form clean direct web url address string 
            receipt_url = f"https://streamlit.app{last_bet['ticket_id']}"
            
            # Encode URL parameters securely for safe transit over the internet
            encoded_url = urllib.parse.quote_plus(receipt_url)
            google_qr_api = f"https://googleapis.com{encoded_url}&choe=UTF-8"
            
            # Stream the dynamic cloud image securely onto the view area
            st.image(google_qr_api, caption="Scan this clean receipt link")
            st.code(receipt_url, language="text")

    else:
        st.warning("Please type your Admin PIN password in the sidebar panel to unlock ledger tools.")


else:
    # ==========================================
    # 🥊 PUBLIC LIVE SCREEN DASHBOARD
    # ==========================================
    st.title("🥊 Fight Night Live Board Tracker")
    st.subheader("Current Card Matchup")
    
    if st.button("🔄 Refresh Live Board Data"):
        st.rerun()
        
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"🏆 {db.fighters['A']} Pool", 
            value=f"${db.pools['A']:,.2f}", 
            delta=f"{db.bettors['A']} Total Backers"
        )
    with col2:
        st.metric(
            label=f"⚡ {db.fighters['B']} Pool", 
            value=f"${db.pools['B']:,.2f}", 
            delta=f"{db.bettors['B']} Total Backers"
        )
        
    st.markdown(f"### **Total Live Cash in Pot: ${gross_total_pool:,.2f}**")
    st.markdown(f"##### *Net Distributable Pool (After Host Cut): ${net_distributable_pool:,.2f}*")
    st.divider()
    
    st.subheader("📜 Recent Transactions")
    if db.locked_bets:
        for bet in reversed(db.locked_bets):
            st.text(f"🎟️ {bet['name']} placed ${bet['amount']:.2f} on {bet['fighter']}")
    else:
        st.info("Waiting for first cash pool entry...")
