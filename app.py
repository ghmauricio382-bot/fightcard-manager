import streamlit as st
import qrcode
from io import BytesIO

# --- 1. SETTINGS & APP CONSTANTS ---
st.set_page_config(page_title="Fight Night Pool Manager", layout="centered")
HOST_CUT_PERCENTAGE = 0.07  # Your 7% host cut

query_params = st.query_params

# Global Persistence for Fighter Names via URL Link parameters
fighter_a_name = query_params.get("a", "Mario")
fighter_b_name = query_params.get("b", "Alejandro")

# --- 2. LIVE DATABASE ARRAYS (In-Memory) ---
if "pools" not in st.session_state:
    st.session_state.pools = {"A": 0.0, "B": 0.0}
if "bettors" not in st.session_state:
    st.session_state.bettors = {"A": 0, "B": 0}
if "locked_bets" not in st.session_state:
    st.session_state.locked_bets = []

# Global Mathematical Calculations
gross_total_pool = st.session_state.pools["A"] + st.session_state.pools["B"]
house_take = gross_total_pool * HOST_CUT_PERCENTAGE
net_distributable_pool = gross_total_pool - house_take

# Helper function to easily construct matching URL parameters
def get_url_suffix():
    return f"&a={fighter_a_name}&b={fighter_b_name}"

# --- 3. THE THREE TERMINAL ROUTING SYSTEMS ---

if "ticket" in query_params:
    # ==========================================
    # 📱 PRIVATE BETTOR TICKET RECEIPT VIEW
    # ==========================================
    ticket_id = query_params["ticket"]
    st.title("🎟️ Your Personal Bet Receipt")
    st.markdown("---")
    
    # Locate this bettor's exact row inside your dashboard
    found_bet = next((bet for bet in st.session_state.locked_bets if bet["ticket_id"] == ticket_id), None)
    
    if found_bet:
        st.subheader(f"Bettor: **{found_bet['name']}**")
        
        # Pull live matchup parameters
        my_fighter = found_bet['fighter']
        my_amount = found_bet['amount']
        choice_key = found_bet['choice_key']
        
        # Real-time calculation sync based on current pool fluctuations
        current_fighter_pool = st.session_state.pools[choice_key]
        
        # Dynamic share inside their fighter's specific backing pool
        share_percentage = my_amount / current_fighter_pool if current_fighter_pool > 0 else 0
        possible_payout = share_percentage * net_distributable_pool
        
        # Clean read-only display cards
        st.metric(label="Your Cash Staked", value=f"${my_amount:,.2f}")
        st.metric(label="Your Selected Fighter", value=str(my_fighter))
        
        col1, col2 = st.columns(2)
        col1.metric(label="Your Current Pool Share", value=f"{share_percentage*100:.1f}%")
        col2.metric(label="Your Projected Payout (7% Cut Inc.)", value=f"${possible_payout:,.2f}")
        
        st.caption("⚠️ Your payout amount is dynamic and can fluctuate as more cash entries are added to the live pools.")
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
        
        # Option A: Manage match names
        st.subheader("📝 Setup Current Matchup")
        new_name_a = st.text_input("Fighter A Name", value=fighter_a_name)
        new_name_b = st.text_input("Fighter B Name", value=fighter_b_name)
        if st.button("Save & Update Match Names"):
            st.query_params.update({"view": "admin", "a": new_name_a, "b": new_name_b})
            st.success("Names synchronized across the pool tracker!")
            st.rerun()
            
        st.markdown("---")
        
        # Option B: Add Cash Bets In Person
        st.subheader("💵 Add In-Person Cash Bet")
        inbound_name = st.text_input("Customer Name / Ticket Alias")
        inbound_cash = st.number_input("Cash Collected ($)", min_value=1.0, value=20.0, step=5.0)
        selected_target = st.radio("Fighter Chosen", (fighter_a_name, fighter_b_name))
        
        if st.button("Lock Bet & Generate Receipt QR"):
            if not inbound_name.strip():
                st.error("Please assign a customer name to compile the bet sheet record.")
            else:
                target_key = "A" if selected_target == fighter_a_name else "B"
                
                # Assign transaction keys
                new_id = f"FIGHT-{len(st.session_state.locked_bets) + 1001}"
                
                # Append transaction to backend array ledger
                st.session_state.pools[target_key] += inbound_cash
                st.session_state.bettors[target_key] += 1
                st.session_state.locked_bets.append({
                    "ticket_id": new_id,
                    "name": inbound_name,
                    "fighter": selected_target,
                    "amount": inbound_cash,
                    "choice_key": target_key
                })
                st.success(f"Bet Authenticated! Ticket ID: {new_id}")
                st.balloons()
                
                # Keep active parameters on refresh re-run
                st.rerun()

        # Display unique QR code for the last placed bet right on your screen
        if st.session_state.locked_bets:
            last_bet = st.session_state.locked_bets[-1]
            st.markdown("---")
            st.subheader(f"📱 QR Code Receipt for {last_bet['name']}")
            st.info("Have the customer scan this code right now with their phone camera to keep their live receipt open.")
            
            receipt_url = f"https://streamlit.app{last_bet['ticket_id']}{get_url_suffix()}"
            qr_img = qrcode.make(receipt_url)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            st.image(buf.getvalue(), use_container_width=True)
            st.caption(f"Target: {receipt_url}")

    else:
        st.warning("Please type your Admin PIN password in the sidebar panel to unlock ledger tools.")


else:
    # ==========================================
    # 🥊 PUBLIC LIVE SCREEN DASHBOARD
    # ==========================================
    st.title("🥊 Fight Night Live Board Tracker")
    st.subheader("Current Card Matchup")
    
    # 1. Clean Display Layout Cards
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"🏆 {fighter_a_name} Pool", 
            value=f"${st.session_state.pools['A']:,.2f}", 
            delta=f"{st.session_state.bettors['A']} Total Backers"
        )
    with col2:
        st.metric(
            label=f"⚡ {fighter_b_name} Pool", 
            value=f"${st.session_state.pools['B']:,.2f}", 
            delta=f"{st.session_state.bettors['B']} Total Backers"
        )
        
    st.markdown(f"### **Total Live Cash in Pot: ${gross_total_pool:,.2f}**")
    st.markdown(f"##### *Net Distributable Pool (After Host Cut): ${net_distributable_pool:,.2f}*")
    st.divider()
    
    # 2. Scrolling Live Ledger of all bets made
    st.subheader("📜 Recent Transactions")
    if st.session_state.locked_bets:
        for bet in reversed(st.session_state.locked_bets):
            st.text(f"🎟️ {bet['name']} placed ${bet['amount']:.2f} on {bet['fighter']}")
    else:
        st.info("Waiting for first cash pool entry...")
