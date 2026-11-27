import streamlit as st
import requests

def get_live_rate():
    try:
        r1 = requests.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=10).json()
        gold_usd_oz = r1['items'][0]['curr']
        r2 = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10).json()
        usd_inr = r2['rates']['INR']
        rate_10g_24k = (gold_usd_oz * usd_inr / 31.1035) * 10 * 1.17
        return round(rate_10g_24k), round(rate_10g_24k * 0.9167)
    except:
        return None, None

# --- LOGIN WALA TAALA ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔒 Hari Jewellers - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == st.secrets["USERNAME"] and password == st.secrets["PASSWORD"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Galat Username ya Password hai")
    st.stop()

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()
import pandas as pd
import os
from datetime import date, datetime
import base64
try:
    import requests
except:
    requests = None

st.set_page_config(page_title="Hari Jewellers", page_icon="💎", layout="wide")
CUSTOMER_FILE = "customers.xlsx"
GIRVI_FILE = "girvi.xlsx"
SALE_FILE = "sales.xlsx"
WHOLESALE_FILE = "wholesale.xlsx"
ARTICLE_FILE = "articles.xlsx"

DEFAULT_GOLD = ["Chain","Ring","Mangalsutra","Kada","Bangles","Jhumka","Tops","Nose Pin","Tagdi","Addha Tagdi","Tabeez","Chanda","Suraj","Ramnami","Gulshan Patti","Coin","Pendant"]
DEFAULT_SILVER = ["Payal","Pajeb","Bichhiya","Kardhani","Coin","Glass","Katori","Murti","Chain","Tabeez","Chaku","Tagdi"]
CUSTOMER_COLS = ["CustomerID","CustomerName","Mobile","Address","Aadhaar","CreatedDate"]
GIRVI_COLS = ["GirviID","CustomerID","CustomerName","Mobile","Metal","Item","Weight","LoanAmount","InterestRate","EntryDate","ReleaseDate","Remarks","Status","InterestAmount","TotalReturn"]
SALE_COLS = ["SaleID","BillNo","BillType","CustomerID","CustomerName","Mobile","Metal","Item","Weight","Rate","Making","SubTotal","GSTPercent","GSTAmount","TotalAmount","PaymentMode","SaleDate","Remarks"]
WHOLESALE_COLS = ["WholesaleID","ParchaNo","CustomerID","CustomerName","Mobile","Metal","Item","Weight","KacchaWeight","NetWeight","PakkaWeight","Rate","AayiPercent","DiyaPercent","CostAmount","SaleAmount","Profit","EntryTime","Date","Status","Remarks"]
ARTICLE_COLS = ["Metal","Item"]

st.markdown("""
<style>
.stApp { background: #FFF8E7; }
.main-header { background: linear-gradient(90deg, #1a1a1a 0%, #3d2b00 50%, #B8860B 100%); padding: 20px 25px; border-radius: 15px; color: white; }
.main-header h1 { margin:0; font-size: 34px; }
.main-header p { margin:5px 0 0 0; color:#FFD700; font-size:15px; }
.metric-card { background: white; padding: 18px; border-radius: 15px; border-left: 5px solid #B8860B; box-shadow: 0 4px 15px rgba(0,0,0,0.08); text-align: center; }
.metric-card h3 { margin:0; color:#888; font-size:14px; }
.metric-card h2 { margin:5px 0 0 0; color:#1a1a1a; font-size:28px; }
.stButton>button { background: linear-gradient(90deg, #B8860B, #FFD700); color: black !important; font-weight: 700; border-radius: 10px; border: none; padding: 10px 20px; }
div[data-testid="stSidebar"] { background: #1a1a1a; }
div[data-testid="stSidebar"] * { color: white !important; }
.success-box { background:#e8f5e9; padding:12px; border-radius:10px; border-left:5px solid green; }
.pending-box { background:#fff3cd; padding:12px; border-radius:10px; border-left:5px solid #ff9800; }
.profit-box { background:#e3f2fd; padding:12px; border-radius:10px; border-left:5px solid #1976d2; }
.kaccha-box { background:#fff3e0; padding:12px; border-radius:10px; border-left:5px solid #ff9800; }
.pakka-box { background:#e8f5e9; padding:12px; border-radius:10px; border-left:5px solid #2e7d32; }
.rate-box { background:white; padding:18px; border-radius:15px; border:2px solid #B8860B; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
</style>
""", unsafe_allow_html=True)

def fetch_24k_live():
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r1 = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/GC=F", headers=headers, timeout=15).json()
        gold_usd_oz = r1['chart']['result'][0]['meta']['regularMarketPrice']
        r2 = requests.get("https://open.er-api.com/v6/latest/USD", timeout=15).json()
        usd_inr = r2['rates']['INR']
        rate_10g = (gold_usd_oz * usd_inr / 31.1035) * 10 * 1.152
        return round(rate_10g)
    except:
        pass
    try:
        r = requests.get("https://api.metals.live/v1/spot?currency=INR", timeout=15).json()
        return round(float(r[0]['gold']) * 10)
    except:
        return None

def get_default_rate(metal):
    if metal == "Gold": return float(st.session_state.get("gold_rate", 72000.0)) / 10.0
    else: return float(st.session_state.get("silver_rate", 1530.0)) / 10.0
def get_default_rate_10g(metal):
    if metal == "Gold": return float(st.session_state.get("gold_rate", 72000.0))
    else: return float(st.session_state.get("silver_rate", 1530.0))

if "gold_rate" not in st.session_state:
    st.session_state.gold_rate = 72000.0
    st.session_state.gold_24k = 78500.0
    st.session_state.silver_rate = 1530.0

def load_file(fname, cols):
    if not os.path.exists(fname):
        df = pd.DataFrame(columns=cols); df.to_excel(fname, index=False); return df
    try:
        df = pd.read_excel(fname, dtype=str).fillna("")
        for c in cols:
            if c not in df.columns: df[c] = ""
        return df
    except: return pd.DataFrame(columns=cols)
def save_file(df, fname): df.to_excel(fname, index=False)
def gen_id(df, prefix, col):
    if df.empty: return f"{prefix}0001"
    try:
        nums = [int(str(x).replace(prefix,"")) for x in df[col] if str(x).startswith(prefix) and str(x).replace(prefix,"").isdigit()]
        return f"{prefix}{max(nums)+1:04d}" if nums else f"{prefix}0001"
    except: return f"{prefix}{len(df)+1:04d}"
def to_num(x):
    try: return float(str(x).replace(",",""))
    except: return 0.0
def get_pakka(row):
    if to_num(row.get("PakkaWeight", ""))>0: return to_num(row.get("PakkaWeight"))
    return to_num(row.get("Weight", "")) * to_num(row.get("DiyaPercent", 74)) / 100
def get_kaccha(row):
    if to_num(row.get("KacchaWeight", ""))>0: return to_num(row.get("KacchaWeight"))
    return to_num(row.get("Weight", ""))
def get_net(row):
    if to_num(row.get("NetWeight", ""))>0: return to_num(row.get("NetWeight"))
    return get_kaccha(row)

def load_articles():
    if not os.path.exists(ARTICLE_FILE):
        rows = [{"Metal":"Gold","Item":x} for x in DEFAULT_GOLD] + [{"Metal":"Silver","Item":x} for x in DEFAULT_SILVER]
        df = pd.DataFrame(rows)
        df.to_excel(ARTICLE_FILE, index=False)
        return df
    try:
        df = pd.read_excel(ARTICLE_FILE, dtype=str).fillna("")
        return df
    except:
        rows = [{"Metal":"Gold","Item":x} for x in DEFAULT_GOLD] + [{"Metal":"Silver","Item":x} for x in DEFAULT_SILVER]
        return pd.DataFrame(rows)

def get_article_list(metal):
    df = load_articles()
    lst = df[df["Metal"]==metal]["Item"].astype(str).tolist()
    lst = sorted(list(dict.fromkeys([x.strip() for x in lst if x.strip()!=""])))
    return lst

def save_new_article(metal, item):
    item = item.strip()
    if not item: return False
    df = load_articles()
    exists = ((df["Metal"]==metal) & (df["Item"].str.lower()==item.lower())).any()
    if exists: return False
    new = pd.DataFrame([{"Metal":metal,"Item":item}])
    save_file(pd.concat([df, new], ignore_index=True), ARTICLE_FILE)
    return True

def article_select(metal, key):
    lst = get_article_list(metal)
    search = st.text_input(f"🔍 Article Search Karo ({metal})...", key=f"art_search_{key}", placeholder="Payal, Chain, Tagdi... sirf naam likho, PC / Piece Remarks me likhna")
    if search.strip() != "":
        filtered = [x for x in lst if search.strip().lower() in x.lower()]
    else:
        filtered = lst
    options = filtered.copy()
    if search.strip() != "" and search.strip().lower() not in [x.lower() for x in lst]:
        options = [f"➕ Naya Add Karo: {search.strip()}"] + options
    if not options:
        options = [f"➕ Naya Add Karo: {search.strip()}" if search.strip() else "Koi Article Nahi"]
    sel = st.selectbox(f"Article Select Karo ({len(lst)} Articles)", options, key=f"art_select_{key}")
    if sel and sel.startswith("➕ Naya Add Karo:"):
        new_name = sel.replace("➕ Naya Add Karo:", "").strip()
        if st.button(f"✅ '{new_name}' Ko List Me Save Karo", key=f"art_save_{key}"):
            if save_new_article(metal, new_name):
                st.success(f"✅ '{new_name}' save ho gaya! Ab har baar list me aayega.")
                st.rerun()
            else: st.info("Ye pehle se hai.")
        return new_name
    if search.strip() != "" and sel not in lst and not sel.startswith("➕"):
        return sel
    return sel

def searchable_select(label, options_list, key):
    if not options_list:
        st.info("List khali hai."); return None
    search = st.text_input(f"🔍 {label} me Search Karo...", key=f"search_{key}", placeholder="Naam / No. / Mobile likho...")
    if search.strip() != "":
        filtered = [o for o in options_list if search.strip().lower() in str(o).lower()]
        if not filtered:
            st.warning(f"'{search}' se kuch nahi mila."); filtered = options_list
    else: filtered = options_list
    st.caption(f"Total: {len(options_list)} | Dikh raha hai: {len(filtered)}")
    return st.selectbox(label, filtered, key=f"select_{key}")

def make_print_html(title, body_html, doc_no, is_pakka=False, header_note=None):
    if header_note is None:
        if "WHOLESALE" in title.upper(): gst_line = "<p class='center'>Wholesale Parcha - Dene-Lene Ka Hisab</p>"
        elif is_pakka: gst_line = "<p class='center'>GSTIN: APNE GST NO YAHAN LIKHO | Tax Invoice</p>"
        else: gst_line = "<p class='center'>Estimate Only - Kaccha Bill</p>"
    else: gst_line = f"<p class='center'>{header_note}</p>"
    return f"""
    <html><head><title>{title} - {doc_no}</title>
    <style>body{{font-family:Arial;padding:20px;}}.receipt{{max-width:800px;margin:auto;border:2px solid #000;padding:25px;}}h1{{text-align:center;margin:0;}}.center{{text-align:center;color:#555;}}table{{width:100%;border-collapse:collapse;margin-top:15px;}}th,td{{padding:8px;border:1px solid #000;text-align:left;font-size:13px;}}th{{background:#f2f2f2;}}.total{{font-size:20px;font-weight:bold;text-align:right;margin-top:15px;}}.footer{{text-align:center;font-size:12px;margin-top:20px;}}.sign{{display:flex;justify-content:space-between;margin-top:40px;}}@media print{{.no-print{{display:none;}}}}</style></head>
    <body><div class="receipt"><h1>💎 HARI JEWELLERS</h1><p class="center">Wholesale • Retail • Girvi | Main Market</p>{gst_line}<p class="center"><b>{title}</b> | No: {doc_no} | Date: {date.today().strftime("%d-%m-%Y")}</p><hr>{body_html}<div class="sign"><span>Customer Sign</span><span>Shop Sign</span></div><p class="footer">Thank You! • Kripya ye bill sambhal kar rakhein</p></div>
    <div class="no-print" style="text-align:center;margin-top:20px;"><button onclick="window.print()" style="padding:12px 30px;font-size:16px;background:#B8860B;color:white;border:none;border-radius:8px;cursor:pointer;">🖨️ PRINT KARO</button></div><script>window.onload=function(){{window.print();}}</script></body></html>"""

def download_print_button(label, html_content, filename):
    b64 = base64.b64encode(html_content.encode()).decode()
    href = f'<a href="data:text/html;base64,{b64}" download="{filename}" target="_blank" style="display:inline-block;background:linear-gradient(90deg,#B8860B,#FFD700);color:black;font-weight:700;padding:12px 25px;border-radius:10px;text-decoration:none;">{label}</a>'
    st.markdown(href, unsafe_allow_html=True); st.caption("👆 Click karo -> Bill khulega -> PRINT dabao")

def customer_search_select(customers_df, key_prefix):
    search_text = st.text_input("🔍 Customer Ka Naam / Mobile Likho...", key=f"{key_prefix}_search", placeholder="Ram, Sharma, 98...")
    if search_text.strip() != "":
        fdf = customers_df[customers_df["CustomerName"].astype(str).str.contains(search_text.strip(), case=False, na=False) | customers_df["Mobile"].astype(str).str.contains(search_text.strip(), case=False, na=False)]
    else: fdf = customers_df.copy()
    opts = ["➕ Naya Customer Add Karo"]; mp = {}
    for _, r in fdf.iterrows():
        lab = f"{r['CustomerName']} - {r['Mobile']} | {r['CustomerID']}"
        opts.append(lab); mp[lab] = r
    if search_text.strip() != "" and fdf.empty: st.warning(f"'{search_text}' nahi mila. Naya Add karo.")
    st.caption(f"Total Customers: {len(customers_df)} | Filtered: {len(fdf)}")
    sel = st.selectbox("Customer Select Karein 👇", opts, key=f"{key_prefix}_select")
    return sel, mp, search_text

st.markdown('<div class="main-header"><h1>💎 HARI JEWELLERS</h1><p>✨ Retail • Wholesale • Girvi Management ✨</p></div>', unsafe_allow_html=True); st.write("")
customers_df = load_file(CUSTOMER_FILE, CUSTOMER_COLS)
girvi_df = load_file(GIRVI_FILE, GIRVI_COLS)
sales_df = load_file(SALE_FILE, SALE_COLS)
wholesale_df = load_file(WHOLESALE_FILE, WHOLESALE_COLS)
articles_df = load_articles()
if "kaccha_cart" not in st.session_state: st.session_state["kaccha_cart"] = []
st.sidebar.markdown("## 💎 HARI JEWELLERS")
menu = st.sidebar.radio("📂 MENU", ["🏠 Dashboard","👤 New Customer","💰 New Girvi","🛍️ New Sale / Billing","🏭 Wholesale Entry","🧾 Wholesale Parcha (Shaam)","🔍 Search & Release","🧾 Receipt / Print","✏️ Entry Edit / Delete","📦 Article List","📄 Reports"], index=0)
st.sidebar.markdown("---")
st.sidebar.markdown(f"📈 **Gold:** ₹ {st.session_state.gold_rate:,.0f} / 10 gm")
st.sidebar.markdown(f"📈 **24K:** ₹ {st.session_state.gold_24k:,.0f} / 10 gm")
st.sidebar.markdown(f"📈 **Silver:** ₹ {st.session_state.silver_rate:,.0f} / 10 gm")
st.sidebar.markdown("📞 **Shop:** Hari Jewellers")

# ========== DASHBOARD ==========
if menu == "🏠 Dashboard":
    st.subheader("📊 Aaj Ka Hisab")
    st.markdown('<div class="rate-box">', unsafe_allow_html=True)
    st.markdown("### 📈 Aaj Ka Rate - 10 Gram Me Dalo")
    c1, c2, c3 = st.columns([2,2,1])
    with c1:
        st.session_state.gold_rate = st.number_input("Gold Rate ₹ / 10 gram * (Manual)", value=float(st.session_state.gold_rate), step=100.0, key="dash_gold")
        st.caption(f"= ₹ {st.session_state.gold_rate/10:,.0f} / gram")
    with c2:
        st.session_state.gold_24k = st.number_input("Gold 24K ₹ / 10 gram (Auto / Manual)", value=float(st.session_state.gold_24k), step=100.0, key="dash_24k")
    with c3:
        st.write("")
        if st.button("🔄 24K Live Lao", key="fetch_24k"):
            live = fetch_24k_live()
            if live:
                st.session_state.gold_24k = float(live); st.success(f"24K Live: ₹ {live:,.0f} / 10gm"); st.rerun()
            else: st.warning("Net nahi hai. Haath se daal do.")
    st.session_state.silver_rate = st.number_input("Silver Rate ₹ / 10 gram (Manual)", value=float(st.session_state.silver_rate), step=10.0, key="dash_silver")
    st.caption(f"Silver = ₹ {st.session_state.silver_rate/10:,.0f} / gram")
    if st.button("✅ Rate Save Karo - Sab Parchon Me Lagu Karo"):
        st.success(f"Rate save ho gaya! Gold ₹ {st.session_state.gold_rate:,.0f} / 10gm | 24K ₹ {st.session_state.gold_24k:,.0f} / 10gm | Silver ₹ {st.session_state.silver_rate:,.0f} / 10gm")
    st.markdown('</div>', unsafe_allow_html=True); st.write("")
    active = girvi_df[girvi_df["Status"]=="Active"] if not girvi_df.empty else girvi_df
    pending_wholesale = wholesale_df[wholesale_df["Status"]=="Pending"] if not wholesale_df.empty else wholesale_df
    kaccha_sale = sum(to_num(x) for x in sales_df[sales_df["BillType"]=="Kaccha"]["TotalAmount"]) if not sales_df.empty else 0
    pakka_sale = sum(to_num(x) for x in sales_df[sales_df["BillType"]=="Pakka"]["TotalAmount"]) if not sales_df.empty else 0
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card"><h3>👥 Customers</h3><h2>{len(customers_df)}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><h3>💰 Active Girvi</h3><h2>{len(active)}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><h3>🧾 Kaccha Sale</h3><h2>₹ {kaccha_sale:,.0f}</h2></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card"><h3>🧾 Pakka Sale</h3><h2>₹ {pakka_sale:,.0f}</h2></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("### 🏭 Wholesale Pending")
    if not pending_wholesale.empty:
        disp = pending_wholesale.copy()
        disp["Kaccha"] = disp.apply(lambda r: get_kaccha(r), axis=1)
        disp["Pakka"] = disp.apply(lambda r: get_pakka(r), axis=1)
        st.dataframe(disp[["EntryTime","CustomerName","Metal","Item","Kaccha","DiyaPercent","Pakka","SaleAmount","Remarks"]], use_container_width=True)
    else: st.info("Koi Wholesale Pending nahi hai.")
    st.markdown("### 🔥 Latest Girvi")
    if not active.empty: st.dataframe(active.sort_values("GirviID", ascending=False).head(5), use_container_width=True)

# ========== NEW CUSTOMER ==========
elif menu == "👤 New Customer":
    st.subheader("👤 New Customer")
    check = st.text_input("🔍 Pehle Check Karo - Mobile / Naam Likho, Duplicate na ho...", placeholder="98...")
    if check.strip() != "":
        chk = customers_df[customers_df["CustomerName"].astype(str).str.contains(check.strip(), case=False, na=False) | customers_df["Mobile"].astype(str).str.contains(check.strip(), case=False, na=False)]
        if not chk.empty:
            st.warning("⚠️ Ye naam / mobile pehle se hai:"); st.dataframe(chk, use_container_width=True)
        else: st.success("✅ Naya hai, add kar sakte ho.")
    c1,c2 = st.columns(2)
    with c1: name = st.text_input("Customer Name *"); mobile = st.text_input("Mobile Number *", max_chars=10)
    with c2: aadhaar = st.text_input("Aadhaar Number", max_chars=12); address = st.text_area("Full Address")
    if st.button("✅ Save Customer"):
        if not name.strip(): st.error("Name required hai.")
        elif not mobile.strip() or len(mobile.strip())!=10 or not mobile.isdigit(): st.error("Sahi 10 digit mobile dalo.")
        elif mobile.strip() in customers_df["Mobile"].astype(str).values: st.error("Duplicate Mobile!")
        else:
            nid = gen_id(customers_df, "CUS", "CustomerID")
            new = {"CustomerID":nid,"CustomerName":name.strip(),"Mobile":mobile.strip(),"Address":address.strip(),"Aadhaar":aadhaar.strip(),"CreatedDate":datetime.now().strftime("%d-%m-%Y")}
            save_file(pd.concat([customers_df, pd.DataFrame([new])], ignore_index=True), CUSTOMER_FILE); st.success(f"✅ Saved! ID: {nid}"); st.balloons()
    st.markdown("### 👥 All Customers - Search Karo")
    cust_search = st.text_input("🔍 Customers me Search...", key="cust_list_search", placeholder="Naam / Mobile...")
    if cust_search.strip() != "":
        show_cust = customers_df[customers_df["CustomerName"].astype(str).str.contains(cust_search.strip(), case=False, na=False) | customers_df["Mobile"].astype(str).str.contains(cust_search.strip(), case=False, na=False)]
    else: show_cust = customers_df
    st.dataframe(show_cust, use_container_width=True)

# ========== NEW GIRVI ==========
elif menu == "💰 New Girvi":
    st.subheader("💰 New Girvi Entry")
    sel_opt, mp, search_text = customer_search_select(customers_df, "girvi")
    selected_row = None; is_new_customer = False; new_name=""; new_mobile=""; new_address=""; new_aadhaar=""
    if sel_opt == "➕ Naya Customer Add Karo":
        is_new_customer = True
        c1,c2 = st.columns(2)
        with c1: new_name = st.text_input("Customer Name *", value=search_text if search_text and not search_text.isdigit() else ""); new_mobile = st.text_input("Mobile Number *", max_chars=10, value=search_text if search_text.isdigit() else "")
        with c2: new_aadhaar = st.text_input("Aadhaar Number", max_chars=12); new_address = st.text_input("Address")
    else:
        selected_row = mp[sel_opt]; st.success(f"✅ {selected_row['CustomerName']} | {selected_row['Mobile']} | {selected_row['CustomerID']}")
        if not girvi_df.empty:
            hist = girvi_df[girvi_df["CustomerID"]==selected_row["CustomerID"]]
            if not hist.empty:
                st.markdown("#### 📜 Purani Girvi History"); st.dataframe(hist, use_container_width=True)
    c1,c2,c3 = st.columns(3)
    with c1: metal = st.selectbox("Metal Type", ["Gold","Silver"]); item = article_select(metal, "girvi_item")
    with c2: weight = st.number_input("Weight (grams)", min_value=0.0, step=0.1); loan = st.number_input("Loan Amount ₹", min_value=0.0, step=500.0)
    with c3: interest_rate = st.number_input("Interest Rate % / Month", min_value=0.0, value=2.0, step=0.5); entry_date = st.date_input("Entry Date", value=date.today())
    girvi_rate_10g = st.number_input(f"Rate ₹ / 10 gram (Dashboard se auto)", value=float(get_default_rate_10g(metal)), step=100.0, key=f"girvi_rate_{metal}")
    girvi_rate = girvi_rate_10g / 10.0
    if weight>0 and girvi_rate>0:
        st.info(f"💡 Market Value: {weight} gm x ₹ {girvi_rate:,.0f}/gm (₹ {girvi_rate_10g:,.0f}/10gm) = ₹ {weight*girvi_rate:,.0f}  |  Loan ₹ {loan:,.0f}")
    remarks = st.text_input("Remarks")
    if loan>0: st.markdown(f'<div class="success-box">💡 Loan ₹ {loan:,.0f} | 1 Month Interest = ₹ {loan*interest_rate/100:,.0f}</div>', unsafe_allow_html=True)
    if st.button("💾 Save Girvi"):
        if is_new_customer:
            if not new_name.strip(): st.error("Naam zaroori hai."); st.stop()
            if not new_mobile.strip() or len(new_mobile.strip())!=10: st.error("Sahi Mobile dalo."); st.stop()
            if new_mobile.strip() in customers_df["Mobile"].astype(str).values: st.error("Ye Mobile pehle se hai."); st.stop()
            new_cid = gen_id(customers_df, "CUS", "CustomerID"); new_cust = {"CustomerID":new_cid,"CustomerName":new_name.strip(),"Mobile":new_mobile.strip(),"Address":new_address.strip(),"Aadhaar":new_aadhaar.strip(),"CreatedDate":datetime.now().strftime("%d-%m-%Y")}
            save_file(pd.concat([customers_df, pd.DataFrame([new_cust])], ignore_index=True), CUSTOMER_FILE); selected_row = pd.Series(new_cust)
        if selected_row is None: st.error("Customer select karo.")
        elif weight<=0 or loan<=0: st.error("Weight / Loan dalo.")
        elif not item or item.startswith("➕"): st.error("Article select karo / naya add karo.")
        else:
            save_new_article(metal, item)
            girvi_df = load_file(GIRVI_FILE, GIRVI_COLS); gid = gen_id(girvi_df, "GV", "GirviID")
            new_girvi = {"GirviID":gid,"CustomerID":selected_row["CustomerID"],"CustomerName":selected_row["CustomerName"],"Mobile":str(selected_row["Mobile"]),"Metal":metal,"Item":item,"Weight":str(weight),"LoanAmount":str(int(loan)),"InterestRate":str(interest_rate),"EntryDate":entry_date.strftime("%d-%m-%Y"),"ReleaseDate":"","Remarks":f"{remarks} | Rate ₹ {girvi_rate_10g:,.0f}/10gm","Status":"Active","InterestAmount":"0","TotalReturn":"0"}
            save_file(pd.concat([girvi_df, pd.DataFrame([new_girvi])], ignore_index=True), GIRVI_FILE); st.success(f"✅ Girvi Saved! ID: {gid}")
            body = f"<table><tr><td>Girvi ID</td><td>{gid}</td></tr><tr><td>Customer</td><td>{selected_row['CustomerName']} ({selected_row['Mobile']})</td></tr><tr><td>Item</td><td>{metal} - {item} ({weight} gm)</td></tr><tr><td>Rate</td><td>₹ {girvi_rate_10g:,.0f} / 10 gm</td></tr><tr><td>Loan</td><td>₹ {loan:,.0f}</td></tr></table><div class='total'>Loan: ₹ {loan:,.0f}</div>"
            html = make_print_html("GIRVI SLIP", body, gid); download_print_button("🖨️ GIRVI SLIP PRINT KARO", html, f"Girvi_{gid}.html"); st.balloons()

# ========== NEW SALE / BILLING - DUKANDAR HATA DIYA ==========
elif menu == "🛍️ New Sale / Billing":
    st.subheader("🛍️ New Sale / Billing - Sirf Customer Ke Liye")
    st.caption("Dukandar ka hisab yahan nahi hoga. Dukandar ke liye Wholesale Entry / Wholesale Parcha alag se hai.")
    bill_type = st.radio("Bill Type *", ["🧾 Kaccha Bill (Customer - No GST, 100% Me)", "🧾 Pakka Bill (GST Tax Invoice)"], horizontal=False)
    is_pakka = "Pakka" in bill_type
    if is_pakka: st.markdown('<div class="pakka-box">✅ <b>PAKKA BILL:</b> GST ke saath, Single Item, Proper Bill No. Customer ke liye.</div>', unsafe_allow_html=True)
    else: st.markdown('<div class="kaccha-box">📝 <b>KACCHA BILL:</b> NO GST. Sirf Customer ke liye - Hamesha 100% me.</div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("### 👤 Customer")
    sel_opt, mp, search_text = customer_search_select(customers_df, "sale")
    selected_row=None; is_new=False; s_name=""; s_mobile=""; s_addr=""
    if sel_opt == "➕ Naya Customer Add Karo":
        is_new=True
        c1,c2=st.columns(2)
        with c1: s_name=st.text_input("Customer Name", value=search_text if search_text and not search_text.isdigit() else "Cash Customer")
        with c2: s_mobile=st.text_input("Mobile", max_chars=10, value=search_text if search_text.isdigit() else "")
        s_addr=st.text_input("Address")
    else:
        selected_row=mp[sel_opt]; st.success(f"✅ {selected_row['CustomerName']} | {selected_row['Mobile']}"); s_addr = selected_row["Address"]
    sale_date = st.date_input("Bill Date", value=date.today())
    payment=st.selectbox("Payment", ["Cash","UPI","Card","Udhar"], key="sale_payment")
    if not is_pakka:
        st.markdown("### 💎 Kaccha Article Add Karo - Customer 100% Me")
        c1,c2,c3,c4 = st.columns(4)
        with c1:
            k_metal=st.selectbox("Metal", ["Gold","Silver"], key="k_metal")
            k_item=article_select(k_metal, "kaccha_item")
        with c2:
            k_weight=st.number_input("Weight (gram) *", min_value=0.0, step=0.1, key="k_weight")
            # Customer ke liye Percent hamesha 100 - Dukandar wala option hata diya
            k_percent=100.0
            k_making = st.number_input("Making Charge (₹) - Manually Bharo", min_value=0.0, value=0.0, step=10.0, key="k_making")        
            with c3:
            k_rate_10g=st.number_input("Rate ₹ / 10 gram *", min_value=0.0, step=100.0, value=float(get_default_rate_10g(k_metal)), key=f"k_rate_{k_metal}")
            k_rate_per_gm = k_rate_10g / 10.0
            k_remarks=st.text_input("Remarks - Jaise PC 70, Piece etc.", key="k_remarks")
        with c4:
            st.write(""); st.write("")
            k_total_value = k_weight * k_rate_per_gm
            k_amount = k_total_value * k_percent / 100
            st.markdown(f"**Full Value:** ₹ {k_total_value:,.0f}")
            st.markdown(f"**Lena Hai:** ₹ {k_amount:,.0f}")
        if k_weight>0 and k_rate_per_gm>0:
            st.markdown(f'<div class="success-box">💡 <b>Customer Hisab (100%):</b> {k_weight} gm x ₹ {k_rate_per_gm:,.0f}/gm (₹ {k_rate_10g:,.0f}/10gm) = <b>₹ {k_amount:,.0f} Lena Hai</b></div>', unsafe_allow_html=True)
        col_add, col_clear = st.columns([3,1])
        with col_add:
            if st.button("➕ Article Add Karo"):
                if k_weight<=0: st.error("Weight dalo."); st.stop()
                if k_rate_per_gm<=0: st.error("Rate dalo."); st.stop()
                if not k_item or k_item.startswith("➕"): st.error("Article select karo."); st.stop()
                save_new_article(k_metal, k_item)
                st.session_state["kaccha_cart"].append({"Metal":k_metal,"Item":k_item,"Weight":k_weight,"Percent":k_percent,"Rate":k_total_value,"RatePerGm":k_rate_per_gm,"Rate10g":k_rate_10g,"Amount":k_amount,"Remarks":k_remarks,"BillFor":"Customer"})
                st.success(f"✅ {k_item} Add Ho Gaya! Amount ₹ {k_amount:,.0f}"); st.rerun()
        with col_clear:
            if st.button("🗑️ Cart Clear"):
                st.session_state["kaccha_cart"]=[]; st.rerun()
        if st.session_state["kaccha_cart"]:
            st.markdown("### 📋 Kaccha Bill - Ab Tak Ke Article")
            cart_df = pd.DataFrame(st.session_state["kaccha_cart"])
            st.dataframe(cart_df[["Metal","Item","Weight","Rate10g","Percent","Rate","Amount","Remarks"]], use_container_width=True)
            total_kaccha = sum(x["Amount"] for x in st.session_state["kaccha_cart"])
            total_wt = sum(x["Weight"] for x in st.session_state["kaccha_cart"])
            st.markdown(f"**Total Articles:** {len(cart_df)} | **Total Weight:** {total_wt:.2f} gm")
            st.markdown(f"### 🧾 KACCHA BILL TOTAL (NO GST): ₹ {total_kaccha:,.0f}")
            if st.button("↩️ Last Article Hatayo"):
                st.session_state["kaccha_cart"].pop(); st.rerun()
            st.divider()
            if st.button("💾 Kaccha Bill Save + Print"):
                cust_id="CASH"; cust_name=s_name if is_new else selected_row["CustomerName"]; cust_mobile=s_mobile if is_new else str(selected_row["Mobile"])
                if not is_new: cust_id=selected_row["CustomerID"]
                if is_new and s_name.strip() and s_name.strip().lower() not in ["cash","cash customer"] and s_mobile.strip() and len(s_mobile.strip())==10 and s_mobile.strip() not in customers_df["Mobile"].astype(str).values:
                    cust_id=gen_id(customers_df, "CUS", "CustomerID")
                    new_cust={"CustomerID":cust_id,"CustomerName":s_name.strip(),"Mobile":s_mobile.strip(),"Address":s_addr.strip(),"Aadhaar":"","CreatedDate":datetime.now().strftime("%d-%m-%Y")}
                    save_file(pd.concat([customers_df, pd.DataFrame([new_cust])], ignore_index=True), CUSTOMER_FILE)
                sales_all = load_file(SALE_FILE, SALE_COLS)
                kaccha_count = len(sales_all[sales_all["BillType"]=="Kaccha"]["BillNo"].unique()) + 1 if not sales_all.empty else 1
                bill_no = f"K-{kaccha_count:04d}"
                rows_to_save=[]; base_num = 1
                if not sales_all.empty:
                    try: base_num = max([int(str(x).replace("SL","")) for x in sales_all["SaleID"] if str(x).replace("SL","").isdigit()]) + 1
                    except: base_num = len(sales_all)+1
                for idx, it in enumerate(st.session_state["kaccha_cart"]):
                    sid = f"SL{base_num+idx:04d}"
                    rows_to_save.append({"SaleID":sid,"BillNo":bill_no,"BillType":"Kaccha","CustomerID":cust_id,"CustomerName":cust_name,"Mobile":cust_mobile,"Metal":it["Metal"],"Item":it["Item"],"Weight":str(it["Weight"]),"Rate":str(int(it["Rate"])),"Percent":str(it["Percent"]),"SubTotal":str(int(it["Amount"])),"GSTPercent":"0","GSTAmount":"0","TotalAmount":str(int(it["Amount"])),"PaymentMode":payment,"SaleDate":sale_date.strftime("%d-%m-%Y"),"Remarks":f"{it['Remarks']} | Customer | Rate ₹ {it.get('Rate10g',0):,.0f}/10gm"})
                save_file(pd.concat([sales_all, pd.DataFrame(rows_to_save)], ignore_index=True), SALE_FILE)
                st.success(f"✅ Kaccha Bill Saved! Bill No: {bill_no} | Total ₹ {total_kaccha:,.0f}")
                rows_html="".join([f"<tr><td>{i+1}</td><td>{it['Metal']} - {it['Item']}</td><td>{it['Weight']} gm</td><td>₹ {it.get('Rate10g',0):,.0f} /10gm</td><td>{it['Percent']}%</td><td>₹ {it['Rate']:,.0f}</td><td>₹ {it['Amount']:,.0f}</td></tr>" for i,it in enumerate(st.session_state["kaccha_cart"])])
                body=f"<p><b>Bill No:</b> {bill_no} | <b>Customer:</b> {cust_name} ({cust_mobile}) | <b>Payment:</b> {payment}</p><table><tr><th>S.No</th><th>Article</th><th>Weight</th><th>Rate /10gm</th><th>Percent</th><th>Full Value</th><th>Amount</th></tr>{rows_html}</table><p><b>Total Weight:</b> {total_wt:.2f} gm</p><div class='total'>Grand Total (No GST): ₹ {total_kaccha:,.0f}</div>"
                html=make_print_html("KACCHA BILL - DENE-LENE", body, bill_no, is_pakka=False)
                download_print_button("🖨️ KACCHA BILL PRINT KARO", html, f"Kaccha_{bill_no}.html")
                st.session_state["kaccha_cart"]=[]; st.balloons()
        else: st.info("👆 Pehle upar se Article Add karo, fir Bill banega.")
    else:
        st.markdown("### 💎 Pakka Saman Details")
        c1,c2,c3=st.columns(3)
        with c1: metal=st.selectbox("Metal", ["Gold","Silver"]); item=article_select(metal, "pakka_item")
        with c2: weight=st.number_input("Weight (grams)", min_value=0.0, step=0.1); rate_10g=st.number_input("Rate ₹ / 10 gram (Dashboard se auto)", min_value=0.0, step=100.0, value=float(get_default_rate_10g(metal)), key=f"pakka_rate_{metal}"); rate=rate_10g/10.0
        with c3: making=st.number_input("Making Charge ₹", min_value=0.0, step=100.0); remarks=st.text_input("Remarks")
        subtotal = weight*rate + making
        gst_percent = st.number_input("GST %", min_value=0.0, value=3.0, step=0.5)
        gst_amt = subtotal * gst_percent / 100; total = subtotal + gst_amt
        if subtotal>0: st.markdown(f'<div class="success-box">💡 {weight} gm x ₹ {rate:,.0f}/gm + Making ₹ {making:,.0f} = Subtotal ₹ {subtotal:,.0f} + GST = <b>Total ₹ {total:,.0f}</b></div>', unsafe_allow_html=True)
        if st.button("💾 Pakka Bill Save + Print"):
            if weight<=0 or rate<=0: st.error("Weight / Rate dalo."); st.stop()
            if not item or item.startswith("➕"): st.error("Article select karo."); st.stop()
            save_new_article(metal, item)
            cust_id="CASH"; cust_name=s_name if is_new else selected_row["CustomerName"]; cust_mobile=s_mobile if is_new else str(selected_row["Mobile"])
            if not is_new: cust_id=selected_row["CustomerID"]
            sales_all = load_file(SALE_FILE, SALE_COLS)
            pakka_count = len(sales_all[sales_all["BillType"]=="Pakka"]["BillNo"].unique()) + 1 if not sales_all.empty else 1
            bill_no = f"P-{pakka_count:04d}"; sid = gen_id(sales_all, "SL", "SaleID")
            new_sale={"SaleID":sid,"BillNo":bill_no,"BillType":"Pakka","CustomerID":cust_id,"CustomerName":cust_name,"Mobile":cust_mobile,"Metal":metal,"Item":item,"Weight":str(weight),"Rate":str(int(rate)),"Percent":"0","SubTotal":str(int(subtotal)),"GSTPercent":str(gst_percent),"GSTAmount":str(int(gst_amt)),"TotalAmount":str(int(total)),"PaymentMode":payment,"SaleDate":sale_date.strftime("%d-%m-%Y"),"Remarks":f"{remarks} | Rate ₹ {rate_10g:,.0f}/10gm"}
            save_file(pd.concat([sales_all, pd.DataFrame([new_sale])], ignore_index=True), SALE_FILE)
            st.success(f"✅ Pakka Bill Saved! Bill No: {bill_no} | Total ₹ {total:,.0f}")
            body=f"<p><b>Bill No:</b> {bill_no} | <b>Customer:</b> {cust_name} ({cust_mobile})</p><table><tr><th>Item</th><th>Weight</th><th>Rate</th><th>Making</th><th>Subtotal</th></tr><tr><td>{metal} - {item}</td><td>{weight} gm</td><td>₹ {rate_10g:,.0f} / 10 gm</td><td>₹ {making:,.0f}</td><td>₹ {subtotal:,.0f}</td></tr></table><table><tr><td>Subtotal</td><td>₹ {subtotal:,.0f}</td></tr><tr><td>CGST ({gst_percent/2}%)</td><td>₹ {gst_amt/2:,.0f}</td></tr><tr><td>SGST ({gst_percent/2}%)</td><td>₹ {gst_amt/2:,.0f}</td></tr></table><div class='total'>Grand Total: ₹ {total:,.0f}</div>"
            html=make_print_html("TAX INVOICE - PAKKA BILL", body, bill_no, is_pakka=True)
            download_print_button("🖨️ PAKKA BILL PRINT KARO", html, f"Pakka_{bill_no}.html"); st.balloons()

# ========== WHOLESALE ENTRY - DUKANDAR KE LIYE ==========
elif menu == "🏭 Wholesale Entry":
    st.subheader("🏭 Wholesale Entry - Dukandar Ke Liye - Kaccha / Pakka Wala Hisab")
    st.markdown('<div class="pending-box">💡 <b>Example:</b> Payal Kaccha 155 gm x 74% = <b>Pakka 114.7 gm</b> | Tagdi Kaccha 250 gm, Net 180 gm x 74% = <b>Pakka 133.2 gm</b> | Normal me Net bharna nahi hai, Kaccha hi Net hai.</div>', unsafe_allow_html=True); st.write("")
    sel_opt, mp, search_text = customer_search_select(customers_df, "wholesale")
    selected_row=None; is_new=False; w_name=""; w_mobile=""; w_addr=""
    if sel_opt == "➕ Naya Customer Add Karo":
        is_new=True
        c1,c2=st.columns(2)
        with c1: w_name=st.text_input("Shop / Dukandar Name *", value=search_text if search_text and not search_text.isdigit() else "")
        with c2: w_mobile=st.text_input("Mobile *", max_chars=10, value=search_text if search_text.isdigit() else "")
        w_addr=st.text_input("Shop Address / Area")
    else:
        selected_row=mp[sel_opt]; st.success(f"✅ Wholesale Dukandar: **{selected_row['CustomerName']}** | 📱 {selected_row['Mobile']}")
        today_str=date.today().strftime("%d-%m-%Y")
        if not wholesale_df.empty:
            today_pending = wholesale_df[(wholesale_df["CustomerID"]==selected_row["CustomerID"]) & (wholesale_df["Date"]==today_str) & (wholesale_df["Status"]=="Pending")]
            if not today_pending.empty:
                st.markdown(f"### 📋 Aaj Ka Pending Parcha - {today_pending.iloc[0]['ParchaNo']}")
                disp = today_pending.copy()
                disp["KacchaW"] = disp.apply(lambda r: get_kaccha(r), axis=1)
                disp["NetW"] = disp.apply(lambda r: get_net(r), axis=1)
                disp["PakkaW"] = disp.apply(lambda r: get_pakka(r), axis=1)
                st.dataframe(disp[["EntryTime","Metal","Item","KacchaW","NetW","DiyaPercent","PakkaW","SaleAmount","Remarks"]], use_container_width=True)
                for m in ["Gold","Silver"]:
                    m_df = today_pending[today_pending["Metal"]==m]
                    if not m_df.empty:
                        m_kaccha = sum(get_kaccha(r) for _, r in m_df.iterrows())
                        m_pakka = sum(get_pakka(r) for _, r in m_df.iterrows())
                        m_amt = sum(to_num(x) for x in m_df["SaleAmount"])
                        st.markdown(f"**{m}:** Kaccha {m_kaccha:.2f} gm | **Pakka {m_pakka:.2f} gm** | **Lena Hai ₹ {m_amt:,.0f}**")
    st.markdown("### 💎 Wholesale Saman Entry")
    c1,c2,c3=st.columns(3)
    with c1:
        metal=st.selectbox("Metal", ["Gold","Silver"], key="ws_metal")
        item=article_select(metal, "ws_item")
    with c2:
        kaccha_wt=st.number_input("Kaccha Weight (grams) * - Jo Tol Me Aaya", min_value=0.0, step=0.1, key="ws_kaccha")
        is_net_alag = st.checkbox("✅ Net Weight alag hai? (Sirf Tagdi jaisi cheez me tick lagao)", value=False, key="ws_net_alag")
        if is_net_alag:
            net_wt=st.number_input("Net Weight (grams) - Tagdi jaisa alag ho to yahan dalo", min_value=0.0, step=0.1, value=float(kaccha_wt), key="ws_net_manual")
        else:
            net_wt = kaccha_wt
            if kaccha_wt>0:
                st.info(f"Net Weight = Kaccha Weight = {net_wt:.2f} gm (Auto)")
            else:
                st.caption("Net Weight Kaccha dalte hi khud aa jayega")
    with c3:
        aayi_percent=st.number_input("Hamari Aayi % * (Sirf Aapko Dikhega)", min_value=0.0, max_value=100.0, value=70.0, step=1.0)
        diya_percent=st.number_input("Dukandaar ko Diya % *", min_value=0.0, max_value=100.0, value=74.0, step=1.0)
    rate_10g=st.number_input("Rate ₹ / 10 gram * (Dashboard se auto)", min_value=0.0, step=100.0, value=float(get_default_rate_10g(metal)), key=f"ws_rate_{metal}")
    rate = rate_10g / 10.0
    remarks=st.text_input("Remarks - Jaise PC 70, Piece, Kari etc. Yahan likho", key="ws_remarks")
    pakka_wt = net_wt * diya_percent / 100
    full_value = pakka_wt * rate
    sale_amt = full_value
    cost_amt = sale_amt * aayi_percent / diya_percent if diya_percent>0 else 0
    profit_amt = sale_amt - cost_amt
    if kaccha_wt>0:
        st.markdown(f'<div class="success-box">💡 <b>Hisab:</b> Kaccha {kaccha_wt} gm | Net {net_wt} gm x {diya_percent}% = <b>Pakka {pakka_wt:.2f} gm</b> | Pakka {pakka_wt:.2f} gm x ₹ {rate:,.0f}/gm (₹ {rate_10g:,.0f}/10gm) = <b>₹ {sale_amt:,.0f} Lena Hai</b></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="profit-box">📈 <b>Hamara Profit (Sirf Aapko):</b> ₹ {profit_amt:,.0f} | Lagat: ₹ {cost_amt:,.0f}</div>', unsafe_allow_html=True)
    if st.button("➕ Wholesale Entry Add Karo (Parcha Me Jodo)"):
        if is_new:
            if not w_name.strip(): st.error("Shop / Naam likho."); st.stop()
            if not w_mobile.strip() or len(w_mobile.strip())!=10: st.error("Sahi 10 digit Mobile dalo."); st.stop()
            if w_mobile.strip() in customers_df["Mobile"].astype(str).values: selected_row=customers_df[customers_df["Mobile"]==w_mobile.strip()].iloc[0]
            else:
                new_cid=gen_id(customers_df, "CUS", "CustomerID"); new_cust={"CustomerID":new_cid,"CustomerName":w_name.strip(),"Mobile":w_mobile.strip(),"Address":w_addr.strip(),"Aadhaar":"","CreatedDate":datetime.now().strftime("%d-%m-%Y")}
                save_file(pd.concat([customers_df, pd.DataFrame([new_cust])], ignore_index=True), CUSTOMER_FILE); selected_row=pd.Series(new_cust)
        if selected_row is None: st.error("Customer select karo."); st.stop()
        if kaccha_wt<=0 or rate<=0: st.error("Kaccha Weight aur Rate dalo."); st.stop()
        if not item or item.startswith("➕"): st.error("Article select karo."); st.stop()
        save_new_article(metal, item)
        ws_df = load_file(WHOLESALE_FILE, WHOLESALE_COLS); today_str=date.today().strftime("%d-%m-%Y")
        existing = ws_df[(ws_df["CustomerID"]==selected_row["CustomerID"]) & (ws_df["Date"]==today_str) & (ws_df["Status"]=="Pending")]
        parcha_no = existing.iloc[0]["ParchaNo"] if not existing.empty else f"WH-{date.today().strftime('%d%m%Y')}-{gen_id(ws_df, 'WS', 'WholesaleID')}"
        wid = gen_id(ws_df, "WS", "WholesaleID")
        new_row = {"WholesaleID":wid,"ParchaNo":parcha_no,"CustomerID":selected_row["CustomerID"],"CustomerName":selected_row["CustomerName"],"Mobile":str(selected_row["Mobile"]),"Metal":metal,"Item":item,"Weight":str(net_wt),"KacchaWeight":str(kaccha_wt),"NetWeight":str(net_wt),"PakkaWeight":str(round(pakka_wt,2)),"Rate":str(int(rate)),"AayiPercent":str(aayi_percent),"DiyaPercent":str(diya_percent),"CostAmount":str(int(cost_amt)),"SaleAmount":str(int(sale_amt)),"Profit":str(int(profit_amt)),"EntryTime":datetime.now().strftime("%I:%M %p"),"Date":today_str,"Status":"Pending","Remarks":f"{remarks} | Rate ₹ {rate_10g:,.0f}/10gm"}
        save_file(pd.concat([ws_df, pd.DataFrame([new_row])], ignore_index=True), WHOLESALE_FILE); st.success(f"✅ Entry Add! Parcha: {parcha_no} | Pakka {pakka_wt:.2f} gm | Lena Hai: ₹ {sale_amt:,.0f}"); st.rerun()
    st.divider(); st.markdown("### 🏭 Aaj Ki Sabhi Wholesale Entry (Pending)")
    if not wholesale_df.empty:
        pend = wholesale_df[wholesale_df["Status"]=="Pending"]
        if not pend.empty:
            disp2 = pend.copy()
            disp2["KacchaW"] = disp2.apply(lambda r: get_kaccha(r), axis=1)
            disp2["PakkaW"] = disp2.apply(lambda r: get_pakka(r), axis=1)
            st.dataframe(disp2[["EntryTime","CustomerName","Metal","Item","KacchaW","DiyaPercent","PakkaW","SaleAmount","Remarks"]], use_container_width=True)

# ========== WHOLESALE PARCHA ==========
elif menu == "🧾 Wholesale Parcha (Shaam)":
    st.subheader("🧾 Wholesale Parcha - Shaam Ko Print Karo")
    if wholesale_df.empty: st.info("Koi Wholesale Entry nahi hai.")
    else:
        all_dates = sorted(wholesale_df["Date"].unique().tolist(), reverse=True)
        sel_date = searchable_select("Date Select Karein", all_dates, "ws_date")
        if sel_date is None: st.stop()
        date_df = wholesale_df[(wholesale_df["Date"]==sel_date) & (wholesale_df["Status"]=="Pending")]
        if date_df.empty:
            st.info(f"{sel_date} ko koi Pending Parcha nahi hai.")
            billed = wholesale_df[(wholesale_df["Date"]==sel_date) & (wholesale_df["Status"]=="Billed")]
            if not billed.empty: st.dataframe(billed, use_container_width=True)
        else:
            parcha_list = date_df["ParchaNo"].unique().tolist(); parcha_options=[]; parcha_map={}
            for pn in parcha_list:
                crow = date_df[date_df["ParchaNo"]==pn].iloc[0]
                label = f"{crow['CustomerName']} - {crow['Mobile']} | Parcha: {pn} | Items: {len(date_df[date_df['ParchaNo']==pn])} | Lena Hai: ₹ {sum(to_num(x) for x in date_df[date_df['ParchaNo']==pn]['SaleAmount']):,.0f}"
                parcha_options.append(label); parcha_map[label]=pn
            sel_parcha_label = searchable_select("Kiska Parcha Print Karna Hai? 👇", parcha_options, "ws_parcha")
            if sel_parcha_label is None: st.stop()
            sel_parcha = parcha_map[sel_parcha_label]
            parch_df = date_df[date_df["ParchaNo"]==sel_parcha]; cust = parch_df.iloc[0]
            st.markdown(f"### 📋 Parcha Preview - {cust['CustomerName']}")
            disp = parch_df.copy()
            disp["KacchaW"] = disp.apply(lambda r: get_kaccha(r), axis=1)
            disp["NetW"] = disp.apply(lambda r: get_net(r), axis=1)
            disp["PakkaW"] = disp.apply(lambda r: get_pakka(r), axis=1)
            st.dataframe(disp[["EntryTime","Metal","Item","KacchaW","NetW","DiyaPercent","PakkaW","SaleAmount","Remarks"]], use_container_width=True)
            gold_pakka = sum(get_pakka(r) for _, r in parch_df[parch_df["Metal"]=="Gold"].iterrows())
            silver_pakka = sum(get_pakka(r) for _, r in parch_df[parch_df["Metal"]=="Silver"].iterrows())
            gold_rate_10 = st.session_state.gold_rate
            silver_rate_10 = st.session_state.silver_rate
            gold_amt = gold_pakka * (gold_rate_10/10) if gold_pakka>0 else 0
            silver_amt = silver_pakka * (silver_rate_10/10) if silver_pakka>0 else 0
            total_sale = sum(to_num(x) for x in parch_df["SaleAmount"])
            total_profit = sum(to_num(x) for x in parch_df["Profit"])
            st.markdown("### 🧾 Shaam Wala Hisab - Neeche Parcha Me Aise Aayega")
            if gold_pakka>0: st.markdown(f"**Gold:** Pakka {gold_pakka:.2f} gm x Rate ₹ {gold_rate_10:,.0f} / 10gm = **₹ {gold_amt:,.0f}**")
            if silver_pakka>0: st.markdown(f"**Silver:** Pakka {silver_pakka:.2f} gm x Rate ₹ {silver_rate_10:,.0f} / 10gm = **₹ {silver_amt:,.0f}**")
            st.markdown(f"**Total Pakka Metal:** Gold {gold_pakka:.2f} gm + Silver {silver_pakka:.2f} gm")
            st.markdown(f"### 🧾 GRAND TOTAL (Entries ka Total): ₹ {total_sale:,.0f} | 📈 Hamara Profit (Sirf Aapko): ₹ {total_profit:,.0f}")
            rows_html = "".join([f"<tr><td>{r['EntryTime']}</td><td>{r['Metal']} - {r['Item']}</td><td>{get_kaccha(r):.2f} gm</td><td>{get_net(r):.2f} gm</td><td>{r['DiyaPercent']}%</td><td>{get_pakka(r):.2f} gm</td><td>{r['Remarks']}</td></tr>" for _, r in parch_df.iterrows()])
            bottom_html = ""
            if gold_pakka>0: bottom_html += f"<tr><td colspan='5'><b>Gold - Pakka {gold_pakka:.2f} gm x Rate ₹ {gold_rate_10:,.0f} / 10gm</b></td><td colspan='2'><b>₹ {gold_amt:,.0f}</b></td></tr>"
            if silver_pakka>0: bottom_html += f"<tr><td colspan='5'><b>Silver - Pakka {silver_pakka:.2f} gm x Rate ₹ {silver_rate_10:,.0f} / 10gm</b></td><td colspan='2'><b>₹ {silver_amt:,.0f}</b></td></tr>"
            body = f"<p><b>Customer:</b> {cust['CustomerName']} | <b>Mobile:</b> {cust['Mobile']} | <b>Date:</b> {sel_date}</p><p><b>Gold Rate:</b> ₹ {gold_rate_10:,.0f} / 10gm | <b>Silver Rate:</b> ₹ {silver_rate_10:,.0f} / 10gm</p><table><tr><th>Time</th><th>Item</th><th>Kaccha Wt</th><th>Net Wt</th><th>Percent</th><th>Pakka Wt</th><th>Remarks</th></tr>{rows_html}</table><table>{bottom_html}</table><p><b>Total Pakka:</b> Gold {gold_pakka:.2f} gm + Silver {silver_pakka:.2f} gm</p><div class='total'>Grand Total: ₹ {total_sale:,.0f}</div>"
            html = make_print_html("WHOLESALE PARCHA", body, sel_parcha)
            col1, col2 = st.columns(2)
            with col1: download_print_button("🖨️ PARCHA PRINT KARO", html, f"Wholesale_{sel_parcha}.html")
            with col2:
                if st.button("✅ Parcha De Diya - Billed Karo"):
                    wholesale_df.loc[wholesale_df["ParchaNo"]==sel_parcha, "Status"] = "Billed"; save_file(wholesale_df, WHOLESALE_FILE); st.success("✅ Billed ho gaya."); st.rerun()

# ========== SEARCH & RELEASE ==========
elif menu == "🔍 Search & Release":
    st.subheader("🔍 Search & Release Girvi")
    search_type = st.radio("Search By", ["Mobile Number","Customer Name","Girvi ID"], horizontal=True); q = st.text_input(f"Enter {search_type} - Yaha Search Karo")
    if st.button("🔍 Search"):
        if girvi_df.empty: st.info("No records.")
        else:
            if search_type=="Mobile Number": res = girvi_df[girvi_df["Mobile"].astype(str).str.contains(q, case=False, na=False)]
            elif search_type=="Customer Name": res = girvi_df[girvi_df["CustomerName"].astype(str).str.contains(q, case=False, na=False)]
            else: res = girvi_df[girvi_df["GirviID"].astype(str).str.contains(q, case=False, na=False)]
            st.session_state["search_res"] = res
    if "search_res" in st.session_state and not st.session_state["search_res"].empty:
        res = st.session_state["search_res"]; st.dataframe(res, use_container_width=True)
        active_list = res[res["Status"]=="Active"]["GirviID"].tolist()
        if active_list:
            gid_sel = searchable_select("Girvi ID Select Karein", active_list, "release_girvi")
            if gid_sel is None: st.stop()
            grow = girvi_df[girvi_df["GirviID"]==gid_sel].iloc[0]
            try: ed = datetime.strptime(grow["EntryDate"], "%d-%m-%Y").date()
            except: ed = date.today()
            months = max(1, (date.today().year-ed.year)*12 + (date.today().month-ed.month) + 1); months = st.number_input("Total Months", min_value=1, value=months)
            loan_amt = to_num(grow["LoanAmount"]); rate = to_num(grow["InterestRate"]) if to_num(grow["InterestRate"])>0 else 2.0
            interest = loan_amt * rate / 100 * months; total = loan_amt + interest
            st.markdown(f"**Loan:** ₹ {loan_amt:,.0f} | **Interest:** ₹ {interest:,.0f} | **Total:** ₹ {total:,.0f}")
            if st.button("✅ Release Karo"):
                girvi_df.loc[girvi_df["GirviID"]==gid_sel, ["Status","ReleaseDate","InterestAmount","TotalReturn"]] = ["Released", date.today().strftime("%d-%m-%Y"), str(int(interest)), str(int(total))]
                save_file(girvi_df, GIRVI_FILE); st.success("Released!"); st.rerun()
    st.divider()
    st.markdown("### 📋 All Girvi - Search Karo")
    girvi_search = st.text_input("🔍 All Girvi me Search...", key="all_girvi_search", placeholder="Naam / Mobile / Girvi ID...")
    if girvi_search.strip() != "":
        show_g = girvi_df[girvi_df["CustomerName"].astype(str).str.contains(girvi_search.strip(), case=False, na=False) | girvi_df["Mobile"].astype(str).str.contains(girvi_search.strip(), case=False, na=False) | girvi_df["GirviID"].astype(str).str.contains(girvi_search.strip(), case=False, na=False)]
    else: show_g = girvi_df
    st.dataframe(show_g, use_container_width=True)

# ========== RECEIPT / PRINT ==========
elif menu == "🧾 Receipt / Print":
    st.subheader("🧾 Receipt / Print - Purane Bill Dobara Print Karo")
    tab1, tab2, tab3 = st.tabs(["💰 Girvi Slip", "🛍️ Retail Bill (Kaccha / Pakka)", "🏭 Wholesale Parcha"])
    with tab1:
        if not girvi_df.empty:
            gid = searchable_select("Girvi ID Select Karein", girvi_df["GirviID"].tolist(), "receipt_girvi")
            if gid:
                r = girvi_df[girvi_df["GirviID"]==gid].iloc[0]
                st.write(f"{r['CustomerName']} | {r['Metal']} - {r['Item']} | ₹ {to_num(r['LoanAmount']):,.0f} | {r['Status']}")
                body = f"<table><tr><td>Girvi ID</td><td>{gid}</td></tr><tr><td>Customer</td><td>{r['CustomerName']}</td></tr><tr><td>Item</td><td>{r['Metal']} - {r['Item']}</td></tr></table>"
                html = make_print_html("GIRVI SLIP", body, gid); download_print_button("🖨️ PRINT", html, f"Girvi_{gid}.html")
        else: st.info("Koi Girvi nahi hai.")
    with tab2:
        if not sales_df.empty:
            sales_df["Label"] = sales_df["BillNo"].astype(str) + " | " + sales_df["BillType"].astype(str) + " | " + sales_df["CustomerName"].astype(str) + " | " + sales_df["Mobile"].astype(str)
            sel_label = searchable_select("Bill Select Karein", sales_df["Label"].unique().tolist(), "receipt_bill")
            if sel_label:
                bill_no_sel = sel_label.split(" | ")[0]
                s_df = sales_df[sales_df["BillNo"]==bill_no_sel]
                s0 = s_df.iloc[0]
                st.write(f"**{s0['BillType']} Bill** - {bill_no_sel} | {s0['CustomerName']} | Total ₹ {sum(to_num(x) for x in s_df['TotalAmount']):,.0f}")
                st.dataframe(s_df, use_container_width=True)
                if s0["BillType"]=="Pakka":
                    body=f"<p><b>Bill No:</b> {bill_no_sel} | <b>Customer:</b> {s0['CustomerName']}</p><table><tr><th>Item</th><th>Weight</th><th>Rate</th><th>Total</th></tr><tr><td>{s0['Metal']} - {s0['Item']}</td><td>{s0['Weight']} gm</td><td>₹ {to_num(s0['Rate'])*10:,.0f} /10gm</td><td>₹ {to_num(s0['TotalAmount']):,.0f}</td></tr></table><div class='total'>Total: ₹ {to_num(s0['TotalAmount']):,.0f}</div>"
                    html=make_print_html("TAX INVOICE - PAKKA BILL", body, bill_no_sel, is_pakka=True); download_print_button("🖨️ PAKKA BILL PRINT KARO", html, f"Pakka_{bill_no_sel}.html")
                else:
                    rows = "".join([f"<tr><td>{i+1}</td><td>{r['Metal']} - {r['Item']}</td><td>{r['Weight']} gm</td><td>{r['Percent']}%</td><td>₹ {to_num(r['Rate']):,.0f}</td><td>₹ {to_num(r['TotalAmount']):,.0f}</td></tr>" for i,(_,r) in enumerate(s_df.iterrows())])
                    total_k = sum(to_num(x) for x in s_df['TotalAmount'])
                    body=f"<p><b>Bill No:</b> {bill_no_sel} | <b>Customer:</b> {s0['CustomerName']}</p><table><tr><th>S.No</th><th>Article</th><th>Weight</th><th>Percent</th><th>Rate</th><th>Amount</th></tr>{rows}</table><div class='total'>Total (No GST): ₹ {total_k:,.0f}</div>"
                    html=make_print_html("KACCHA BILL", body, bill_no_sel, is_pakka=False); download_print_button("🖨️ KACCHA BILL PRINT KARO", html, f"Kaccha_{bill_no_sel}.html")
        else: st.info("Koi Sale nahi hai.")
    with tab3:
        if not wholesale_df.empty:
            pn = searchable_select("Parcha No Select Karein", wholesale_df["ParchaNo"].unique().tolist(), "receipt_wholesale")
            if pn:
                pdf = wholesale_df[wholesale_df["ParchaNo"]==pn]
                disp = pdf.copy()
                disp["KacchaW"] = disp.apply(lambda r: get_kaccha(r), axis=1)
                disp["PakkaW"] = disp.apply(lambda r: get_pakka(r), axis=1)
                st.dataframe(disp[["EntryTime","Metal","Item","KacchaW","DiyaPercent","PakkaW","SaleAmount"]], use_container_width=True)
                rows = "".join([f"<tr><td>{r['Metal']} - {r['Item']}</td><td>{get_kaccha(r):.2f} gm</td><td>{get_net(r):.2f} gm</td><td>{r['DiyaPercent']}%</td><td>{get_pakka(r):.2f} gm</td><td>₹ {to_num(r['SaleAmount']):,.0f}</td></tr>" for _, r in pdf.iterrows()])
                total_pakka_gold = sum(get_pakka(r) for _, r in pdf[pdf["Metal"]=="Gold"].iterrows())
                total_pakka_silver = sum(get_pakka(r) for _, r in pdf[pdf["Metal"]=="Silver"].iterrows())
                total_amt = sum(to_num(x) for x in pdf["SaleAmount"])
                body = f"<p><b>Customer:</b> {pdf.iloc[0]['CustomerName']} | <b>Mobile:</b> {pdf.iloc[0]['Mobile']}</p><p><b>Gold Rate:</b> ₹ {st.session_state.gold_rate:,.0f} / 10gm | <b>Silver Rate:</b> ₹ {st.session_state.silver_rate:,.0f} / 10gm</p><table><tr><th>Item</th><th>Kaccha</th><th>Net</th><th>Percent</th><th>Pakka</th><th>Amount</th></tr>{rows}</table><p><b>Total Pakka:</b> Gold {total_pakka_gold:.2f} gm + Silver {total_pakka_silver:.2f} gm</p><div class='total'>Total: ₹ {total_amt:,.0f}</div>"
                html = make_print_html("WHOLESALE PARCHA", body, pn); download_print_button("🖨️ WHOLESALE PARCHA PRINT KARO", html, f"Wholesale_{pn}.html")
        else: st.info("Koi Wholesale nahi hai.")

# ========== ENTRY EDIT / DELETE ==========
elif menu == "✏️ Entry Edit / Delete":
    st.subheader("✏️ Entry Edit / Delete - Galti Sudharo")
    edit_type = st.radio("Kya Edit Karna Hai?", ["🏭 Wholesale Entry", "💰 Girvi Entry", "🛍️ Sale / Bill Entry", "👤 Customer"], horizontal=True)
    if edit_type == "🏭 Wholesale Entry":
        if wholesale_df.empty: st.info("Koi Wholesale Entry nahi hai.")
        else:
            wholesale_df["Label"] = wholesale_df["WholesaleID"].astype(str) + " | " + wholesale_df["CustomerName"].astype(str) + " | " + wholesale_df["Metal"].astype(str) + " - " + wholesale_df["Item"].astype(str) + " | Kaccha: " + wholesale_df.apply(lambda r: str(get_kaccha(r)), axis=1) + " | " + wholesale_df["Date"].astype(str)
            sel = searchable_select("Kaunsi Entry Edit Karni Hai?", wholesale_df["Label"].tolist(), "edit_ws")
            if sel:
                wid = sel.split(" | ")[0]; row = wholesale_df[wholesale_df["WholesaleID"]==wid].iloc[0]
                st.markdown(f"### Edit Kar Rahe Ho: {wid} - {row['CustomerName']} - Parcha: {row['ParchaNo']}")
                c1,c2,c3 = st.columns(3)
                with c1:
                    e_metal = st.selectbox("Metal", ["Gold","Silver"], index=0 if row["Metal"]=="Gold" else 1, key="e_ws_metal")
                    e_item = article_select(e_metal, "edit_ws_item")
                with c2:
                    e_kaccha = st.number_input("Kaccha Weight (grams)", value=float(get_kaccha(row)), key="e_ws_kaccha")
                    e_net_alag = st.checkbox("Net Weight alag hai?", value=False, key="e_ws_net_alag")
                    if e_net_alag:
                        e_net = st.number_input("Net Weight (grams)", value=float(get_net(row)), key="e_ws_net_manual")
                    else:
                        e_net = e_kaccha
                        st.info(f"Net = Kaccha = {e_net:.2f} gm (Auto)")
                with c3:
                    e_aayi = st.number_input("Hamari Aayi %", value=float(to_num(row["AayiPercent"])), key="e_ws_aayi")
                    e_diya = st.number_input("Diya %", value=float(to_num(row["DiyaPercent"])), key="e_ws_diya")
                e_rate_10g = st.number_input("Rate ₹ / 10 gram", value=float(to_num(row["Rate"])*10), key="e_ws_rate")
                e_rate = e_rate_10g / 10.0
                e_remarks = st.text_input("Remarks", value=str(row["Remarks"]), key="e_ws_rem")
                e_status = st.selectbox("Status", ["Pending","Billed"], index=0 if row["Status"]=="Pending" else 1, key="e_ws_status")
                e_pakka = e_net * e_diya / 100
                e_sale = e_pakka * e_rate
                e_cost = e_sale * e_aayi / e_diya if e_diya>0 else 0
                e_profit = e_sale - e_cost
                st.markdown(f"**Naya Hisab:** Kaccha {e_kaccha} gm | Net {e_net} gm x {e_diya}% = **Pakka {e_pakka:.2f} gm** x ₹ {e_rate:,.0f}/gm = **₹ {e_sale:,.0f}**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Changes - Wholesale Update Karo", key="save_ws"):
                        if not e_item or e_item.startswith("➕"): st.error("Article select karo.")
                        else:
                            save_new_article(e_metal, e_item)
                            idx = wholesale_df[wholesale_df["WholesaleID"]==wid].index[0]
                            wholesale_df.at[idx, "Metal"] = e_metal; wholesale_df.at[idx, "Item"] = e_item; wholesale_df.at[idx, "Weight"] = str(e_net); wholesale_df.at[idx, "KacchaWeight"] = str(e_kaccha); wholesale_df.at[idx, "NetWeight"] = str(e_net); wholesale_df.at[idx, "PakkaWeight"] = str(round(e_pakka,2)); wholesale_df.at[idx, "Rate"] = str(int(e_rate)); wholesale_df.at[idx, "AayiPercent"] = str(e_aayi); wholesale_df.at[idx, "DiyaPercent"] = str(e_diya); wholesale_df.at[idx, "CostAmount"] = str(int(e_cost)); wholesale_df.at[idx, "SaleAmount"] = str(int(e_sale)); wholesale_df.at[idx, "Profit"] = str(int(e_profit)); wholesale_df.at[idx, "Remarks"] = e_remarks; wholesale_df.at[idx, "Status"] = e_status
                            save_file(wholesale_df, WHOLESALE_FILE); st.success("✅ Wholesale Entry Update Ho Gayi!"); st.rerun()
                with col2:
                    if st.button("🗑️ Ye Entry Delete Karo", key="del_ws"):
                        wholesale_df = wholesale_df[wholesale_df["WholesaleID"]!=wid]; save_file(wholesale_df, WHOLESALE_FILE); st.success("🗑️ Delete Ho Gayi!"); st.rerun()
    elif edit_type == "💰 Girvi Entry":
        if girvi_df.empty: st.info("Koi Girvi nahi hai.")
        else:
            girvi_df["Label"] = girvi_df["GirviID"].astype(str) + " | " + girvi_df["CustomerName"].astype(str) + " | " + girvi_df["Metal"].astype(str) + " - " + girvi_df["Item"].astype(str) + " | Loan: " + girvi_df["LoanAmount"].astype(str) + " | " + girvi_df["Status"].astype(str)
            sel = searchable_select("Kaunsi Girvi Edit Karni Hai?", girvi_df["Label"].tolist(), "edit_gv")
            if sel:
                gid = sel.split(" | ")[0]; row = girvi_df[girvi_df["GirviID"]==gid].iloc[0]
                st.markdown(f"### Edit: {gid} - {row['CustomerName']}")
                c1,c2,c3 = st.columns(3)
                with c1:
                    e_metal = st.selectbox("Metal", ["Gold","Silver"], index=0 if row["Metal"]=="Gold" else 1, key="e_gv_metal")
                    e_item = article_select(e_metal, "edit_gv_item")
                with c2:
                    e_weight = st.number_input("Weight (grams)", value=float(to_num(row["Weight"])), key="e_gv_wt")
                    e_loan = st.number_input("Loan Amount ₹", value=float(to_num(row["LoanAmount"])), key="e_gv_loan")
                with c3:
                    e_int = st.number_input("Interest % / Month", value=float(to_num(row["InterestRate"]) if to_num(row["InterestRate"])>0 else 2.0), key="e_gv_int")
                    e_status = st.selectbox("Status", ["Active","Released"], index=0 if row["Status"]=="Active" else 1, key="e_gv_status")
                e_remarks = st.text_input("Remarks", value=str(row["Remarks"]), key="e_gv_rem")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Changes - Girvi Update Karo", key="save_gv"):
                        save_new_article(e_metal, e_item)
                        idx = girvi_df[girvi_df["GirviID"]==gid].index[0]
                        girvi_df.at[idx, "Metal"] = e_metal; girvi_df.at[idx, "Item"] = e_item; girvi_df.at[idx, "Weight"] = str(e_weight); girvi_df.at[idx, "LoanAmount"] = str(int(e_loan)); girvi_df.at[idx, "InterestRate"] = str(e_int); girvi_df.at[idx, "Status"] = e_status; girvi_df.at[idx, "Remarks"] = e_remarks
                        save_file(girvi_df, GIRVI_FILE); st.success("✅ Girvi Update Ho Gayi!"); st.rerun()
                with col2:
                    if st.button("🗑️ Ye Girvi Delete Karo", key="del_gv"):
                        girvi_df = girvi_df[girvi_df["GirviID"]!=gid]; save_file(girvi_df, GIRVI_FILE); st.success("🗑️ Delete Ho Gayi!"); st.rerun()
    elif edit_type == "🛍️ Sale / Bill Entry":
        if sales_df.empty: st.info("Koi Sale nahi hai.")
        else:
            sales_df["Label"] = sales_df["SaleID"].astype(str) + " | " + sales_df["BillNo"].astype(str) + " | " + sales_df["CustomerName"].astype(str) + " | " + sales_df["Item"].astype(str) + " | ₹ " + sales_df["TotalAmount"].astype(str)
            sel = searchable_select("Kaunsi Sale Entry Edit Karni Hai?", sales_df["Label"].tolist(), "edit_sale")
            if sel:
                sid = sel.split(" | ")[0]; row = sales_df[sales_df["SaleID"]==sid].iloc[0]
                st.markdown(f"### Edit: {sid} - Bill: {row['BillNo']} - {row['CustomerName']}")
                c1,c2,c3 = st.columns(3)
                with c1:
                    e_metal = st.selectbox("Metal", ["Gold","Silver"], index=0 if row["Metal"]=="Gold" else 1, key="e_sl_metal")
                    e_item = article_select(e_metal, "edit_sl_item")
                with c2:
                    e_weight = st.number_input("Weight (grams)", value=float(to_num(row["Weight"])), key="e_sl_wt")
                    e_rate = st.number_input("Rate ₹ (Kaccha=Full Value, Pakka=Per Gram)", value=float(to_num(row["Rate"])), key="e_sl_rate")
                with c3:
                    e_percent = st.number_input("Percent % (Kaccha ke liye - Customer hamesha 100%)", value=float(to_num(row["Percent"])), key="e_sl_per")
                    e_gst = st.number_input("GST % (Pakka ke liye)", value=float(to_num(row["GSTPercent"])), key="e_sl_gst")
                e_remarks = st.text_input("Remarks", value=str(row["Remarks"]), key="e_sl_rem")
                if row["BillType"]=="Kaccha":
                    new_sub = e_rate * e_percent / 100; new_total = new_sub; new_gst_amt = 0
                else:
                    new_sub = e_weight * e_rate; new_gst_amt = new_sub * e_gst / 100; new_total = new_sub + new_gst_amt
                st.markdown(f"**Naya Total:** ₹ {new_total:,.0f}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Changes - Sale Update Karo", key="save_sl"):
                        save_new_article(e_metal, e_item)
                        idx = sales_df[sales_df["SaleID"]==sid].index[0]
                        sales_df.at[idx, "Metal"] = e_metal; sales_df.at[idx, "Item"] = e_item; sales_df.at[idx, "Weight"] = str(e_weight); sales_df.at[idx, "Rate"] = str(int(e_rate)); sales_df.at[idx, "Percent"] = str(e_percent); sales_df.at[idx, "SubTotal"] = str(int(new_sub)); sales_df.at[idx, "GSTPercent"] = str(e_gst); sales_df.at[idx, "GSTAmount"] = str(int(new_gst_amt)); sales_df.at[idx, "TotalAmount"] = str(int(new_total)); sales_df.at[idx, "Remarks"] = e_remarks
                        save_file(sales_df, SALE_FILE); st.success("✅ Sale Update Ho Gayi!"); st.rerun()
                with col2:
                    if st.button("🗑️ Ye Entry Delete Karo", key="del_sl"):
                        sales_df = sales_df[sales_df["SaleID"]!=sid]; save_file(sales_df, SALE_FILE); st.success("🗑️ Delete Ho Gayi!"); st.rerun()
    else:
        if customers_df.empty: st.info("Koi Customer nahi hai.")
        else:
            customers_df["Label"] = customers_df["CustomerID"].astype(str) + " | " + customers_df["CustomerName"].astype(str) + " | " + customers_df["Mobile"].astype(str)
            sel = searchable_select("Kaunsa Customer Edit Karna Hai?", customers_df["Label"].tolist(), "edit_cus")
            if sel:
                cid = sel.split(" | ")[0]; row = customers_df[customers_df["CustomerID"]==cid].iloc[0]
                c1,c2 = st.columns(2)
                with c1:
                    e_name = st.text_input("Customer Name", value=str(row["CustomerName"]), key="e_cus_name")
                    e_mobile = st.text_input("Mobile", value=str(row["Mobile"]), key="e_cus_mob", max_chars=10)
                with c2:
                    e_aadhaar = st.text_input("Aadhaar", value=str(row["Aadhaar"]), key="e_cus_aad")
                    e_addr = st.text_input("Address", value=str(row["Address"]), key="e_cus_addr")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save Changes - Customer Update Karo", key="save_cus"):
                        idx = customers_df[customers_df["CustomerID"]==cid].index[0]
                        customers_df.at[idx, "CustomerName"] = e_name; customers_df.at[idx, "Mobile"] = e_mobile; customers_df.at[idx, "Aadhaar"] = e_aadhaar; customers_df.at[idx, "Address"] = e_addr
                        save_file(customers_df, CUSTOMER_FILE); st.success("✅ Customer Update Ho Gaya!"); st.rerun()
                with col2:
                    if st.button("🗑️ Customer Delete Karo", key="del_cus"):
                        customers_df = customers_df[customers_df["CustomerID"]!=cid]; save_file(customers_df, CUSTOMER_FILE); st.success("🗑️ Delete Ho Gaya!"); st.rerun()

# ========== ARTICLE LIST ==========
elif menu == "📦 Article List":
    st.subheader("📦 Article List - Sab Article Yahan Se Manage Karo")
    st.info("Jo article yahan add karoge wo Girvi / Kaccha / Wholesale sab jagah Dropdown me aa jayega.")
    tab1, tab2 = st.tabs(["➕ Naya Article Add Karo", "📋 Sari List Dekho / Delete Karo"])
    with tab1:
        c1,c2 = st.columns(2)
        with c1: new_metal = st.selectbox("Metal", ["Gold","Silver"], key="new_art_metal")
        with c2: new_item = st.text_input("Naya Article Ka Naam - Jaise: Jhalar, Choker, Hathphool", key="new_art_name")
        if st.button("✅ Article Save Karo"):
            if not new_item.strip(): st.error("Naam likho.")
            elif save_new_article(new_metal, new_item):
                st.success(f"✅ '{new_item}' save ho gaya! Ab har jagah list me aayega."); st.balloons()
            else: st.warning("Ye article pehle se hai.")
        st.markdown("### Quick Add - Ek Saath Kai Article")
        st.caption("Ek line me ek naam likho, sab save ho jayenge.")
        bulk = st.text_area("Bulk Add Karo - Har Line Me Ek Article", key="bulk_art")
        bulk_metal = st.selectbox("In Sab Ka Metal", ["Gold","Silver"], key="bulk_metal")
        if st.button("✅ Sab Save Karo"):
            cnt = 0
            for line in bulk.split("\n"):
                if line.strip() and save_new_article(bulk_metal, line.strip()): cnt += 1
            st.success(f"✅ {cnt} naye article save ho gaye!"); st.rerun()
    with tab2:
        for m in ["Gold","Silver"]:
            st.markdown(f"### {m} Articles - {len(get_article_list(m))} hai")
            lst = get_article_list(m)
            search_a = st.text_input(f"🔍 {m} me Search...", key=f"art_list_search_{m}", placeholder="Naam likho...")
            if search_a.strip(): lst = [x for x in lst if search_a.strip().lower() in x.lower()]
            cols = st.columns(3)
            for idx, it in enumerate(lst):
                with cols[idx % 3]:
                    c1, c2 = st.columns([3,1])
                    with c1: st.write(f"• {it}")
                    with c2:
                        if st.button("🗑️", key=f"del_art_{m}_{idx}"):
                            df = load_articles()
                            df = df[~((df["Metal"]==m) & (df["Item"]==it))]
                            save_file(df, ARTICLE_FILE); st.success(f"'{it}' delete ho gaya."); st.rerun()
        st.divider()
        st.markdown("### 📦 Sari List Ek Saath")
        st.dataframe(articles_df, use_container_width=True)

# ========== REPORTS ==========
elif menu == "📄 Reports":
    st.subheader("📄 Reports - Search Ke Saath")
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Customers", "💰 Girvi", "🛍️ Retail (Kaccha/Pakka)", "🏭 Wholesale"])
    with tab1:
        s = st.text_input("🔍 Customers Search...", key="rep_cust")
        df = customers_df[customers_df["CustomerName"].astype(str).str.contains(s, case=False, na=False) | customers_df["Mobile"].astype(str).str.contains(s, case=False, na=False)] if s.strip() else customers_df
        st.dataframe(df, use_container_width=True)
    with tab2:
        s = st.text_input("🔍 Girvi Search...", key="rep_girvi")
        df = girvi_df[girvi_df["CustomerName"].astype(str).str.contains(s, case=False, na=False) | girvi_df["Mobile"].astype(str).str.contains(s, case=False, na=False) | girvi_df["GirviID"].astype(str).str.contains(s, case=False, na=False)] if s.strip() else girvi_df
        st.dataframe(df, use_container_width=True)
    with tab3:
        s = st.text_input("🔍 Retail Bill Search...", key="rep_sale")
        df = sales_df[sales_df["CustomerName"].astype(str).str.contains(s, case=False, na=False) | sales_df["BillNo"].astype(str).str.contains(s, case=False, na=False) | sales_df["Mobile"].astype(str).str.contains(s, case=False, na=False)] if s.strip() else sales_df
        st.dataframe(df, use_container_width=True)
    with tab4:
        s = st.text_input("🔍 Wholesale Search...", key="rep_ws")
        df = wholesale_df[wholesale_df["CustomerName"].astype(str).str.contains(s, case=False, na=False) | wholesale_df["ParchaNo"].astype(str).str.contains(s, case=False, na=False) | wholesale_df["Mobile"].astype(str).str.contains(s, case=False, na=False)] if s.strip() else wholesale_df
        st.dataframe(df, use_container_width=True)
