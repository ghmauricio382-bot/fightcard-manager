import streamlit as st
import qrcode
from io import BytesIO

# --- 1. CONFIGURATION & CONSTANTS ---
st.set_page_config(page_title="Fight Night Pool Manager", layout="centered")
HOST_CUT_PERCENTAGE = 0.07  # 7% host cut

query_params = st.query_params

# --- 2. INITIALIZE LIVE DATABASE IN MEMORY ---
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

# Global Math Calculations
gross_total_pool = st.session_state.pools["A"] + st.session_state.pools["B"]
house_take = gross_total_pool * HOST_CUT_PERCENTAGE
net_distributable_pool = gross_total_pool - house_take

# --- 3. ROUTING LOGIC BASED ON URL PARAMETERS ---
if "ticket" in query_params:
    # INDIVIDUAL TICKET SCAN SCREEN
    ticket_id = query_params["ticket"]
    st.title("🎟️ Ticket Details")
    st.write(f"Ticket ID: {ticket_id}")
    
    # Try to find ticket info from internal data
    found_bet = next((bet for bet in st.session_state.locked_bets if bet["ticket_id"] == ticket_id), None)
    if found_bet:
        st.write(f"**Bettor:** {found_bet['name']}")
        st.write(f"**Selected Fighter:** {found_bet['fighter']}")
        st.write(f"**Amount Staked:** ${found_bet['amount']:,.2f}")
    else:
        st.info("Ticket active. Waiting for final payout assessment.")

elif query_params.get("view") == "admin":
    # ==========================================
    # ORGANIZER / ADMIN CONTROL PANEL (?view=admin)
    # ==========================================
    st.title("Admin Panel")
    
    with st.sidebar:
        st.header("🔑 Organizer Control Panel")
        admin_pass = st.text_input("Enter Admin PIN", type="password")
        
    if admin_pass == "110509":  # Your PIN
        st.success("Access Granted")
        
        st.subheader("📝 Edit Fighter Names")
        new_name_a = st.text_input("Edit Fighter A Name", value=st.session_state.fighters["A"])
        new_name_b = st.text_input("Edit Fighter B Name", value=st.session_state.fighters["B"])
        
        if st.button("Update Names"):
            st.session_state.fighters["A"] = new_name_a
            st.session_state.fighters["B"] = new_name_b
            st.success("Fighter names updated successfully!")
            st.rerun()
            
        st.markdown("---")
        st.subheader("📱 Live View Dynamic QR Generator")
        st.write("Scan this code with a bettor's phone camera to direct them to the betting terminal:")
        
        # Base app URL generation
        base_url = "https://streamlit.app"
        qr_img = qrcode.make(base_url)
        buf = BytesIO()
        qr_img.save(buf, format="PNG")
        st.image(buf.getvalue(), use_container_width=True)
    else:
        st.warning("Please enter your Admin PIN in the sidebar to access management utilities.")

else:
    # ==========================================
    # PUBLIC BETTOR INTERFACE (Default Screen)
    # ==========================================
    st.title("🥊 Live Fight Club Pool Tracker")
    st.subheader("Current Card Matchup")
    
    fighter_a = st.session_state.fighters["A"]
    fighter_b = st.session_state.fighters["B"]
    pool_a = st.session_state.pools["A"]
    pool_b = st.session_state.pools["B"]
    
    # Display tracker metric boxes
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label=f"🏆 {fighter_a} Total Pool", 
            value=f"${pool_a:,.2f}", 
            delta=f"{st.session_state.bettors['A']} Locked Bets"
        )
    with col2:
        st.metric(
            label=f"⚡ {fighter_b} Total Pool", 
            value=f"${pool_b:,.2f}", 
            delta=f"{st.session_state.bettors['B']} Locked Bets"
        )
        
    st.markdown(f"### **Total Cash in Pot: ${gross_total_pool:,.2f}**")
    st.divider()
    
    # Interactive Betting Layout Block
    st.subheader("Place Your Bet")
    bettor_name = st.text_input("Bettor Name / Alias", placeholder="Enter your name")
    bet_amount = st.number_input("Bet Amount ($)", min_value=1.0, value=10.0, step=5.0)
    
    selected_fighter = st.radio("Choose your fighter:", (fighter_a, fighter_b))
    
    # Calculations Panel
    if bet_amount > 0:
        st.write("### 📊 Your Projected Payout Preview")
        
        if selected_fighter == fighter_a:
            simulated_pool = pool_a + bet_amount
            simulated_total = gross_total_pool + bet_amount
            share_percentage = bet_amount / simulated_pool if simulated_pool > 0 else 0
        else:
            simulated_pool = pool_b + bet_amount
            simulated_total = gross_total_pool + bet_amount
            share_percentage = bet_amount / simulated_pool if simulated_pool > 0 else 0

        take_home_pot = simulated_total * (1.0 - HOST_CUT_PERCENTAGE)
        possible_payout = share_percentage * take_home_pot
        
        st.info(f"If **{selected_fighter}** wins, your pool share is **{share_percentage*100:.1f}%**.")
        st.success(f"💰 Estimated Payout (after 7% cut): **${possible_payout:,.2f}**")
        
    if st.button("Confirm & Lock Bet"):
        if not bettor_name.strip():
            st.error("Please enter a Bettor Name or Alias before locking.")
        else:
            choice_key = "A" if selected_fighter == fighter_a else "B"
            st.session_state.pools[choice_key] += bet_amount
            st.session_state.bettors[choice_key] += 1
            
            new_ticket_id = f"TICK-{len(st.session_state.locked_bets) + 1001}"
            st.session_state.locked_bets.append({
                "ticket_id": new_ticket_id,
                "name": bettor_name,
                "fighter": selected_fighter,
                "amount": bet_amount
            })
            
            st.balloons()
            st.success(f"Bet successfully locked in! Ticket ID: {new_ticket_id}")
            st.rerun()
