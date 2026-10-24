import streamlit as st
import pandas as pd
from datetime import date
import os
import google.generativeai as genai
from PIL import Image
import json

# စာမျက်နှာ အကျယ်ချဲ့ခြင်းနှင့် Page Config
st.set_page_config(page_title="ဇွဲထက် ရွှေဆိုင် စာရင်းစစ်စနစ်", layout="wide", page_icon="🪙")

# --- 🎨 Custom CSS Styling ---
st.markdown("""
<style>
    .main {
        background-color: #f4eee1;
    }
    h1, h2, h3 {
        color: #2d2424;
        font-family: 'Georgia', serif;
    }
    h1 {
        border-bottom: 3px solid #b8860b;
        padding-bottom: 10px;
    }
    div.stTextInput input, div.stNumberInput input, div.stSelectbox select {
        background-color: #fffaf0 !important;
        border: 2px solid #d4af37 !important;
        color: #2d2424 !important;
        border-radius: 6px !important;
        font-weight: 500;
    }
    div[data-testid="stMetric"] {
        background-color: #fffaf0;
        border: 1px solid #d4af37;
        padding: 15px;
        border-radius: 6px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    div[data-testid="stMetric"] label {
        color: #5c4033 !important;
        font-weight: 600;
    }
    .stButton>button {
        background: linear-gradient(135deg, #d4af37 0%, #8b6508 100%);
        color: #ffffff;
        border: 1px solid #5c4033;
        border-radius: 4px;
        font-weight: 600;
        padding: 0.5rem 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #ffd700 0%, #b8860b 100%);
        color: #2d2424;
    }
    section[data-testid="stSidebar"] {
        background-color: #2d2424;
        color: #f4eee1;
    }
    section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
        color: #f4eee1 !important;
    }
    div.stAlert {
        border-radius: 6px;
        border-left: 5px solid #b8860b;
        background-color: #fff8dc;
        color: #2d2424;
    }
</style>
""", unsafe_allow_html=True)

# ရွှေချိန်တွက်ချက်မှု ဖန်ရှင်များ
def to_rupe(kyat, pae, yway):
    return (int(kyat) * 128) + (int(pae) * 8) + int(yway)

def from_rupe(total_yway):
    total_yway = int(total_yway)
    kyat = total_yway // 128
    remainder = total_yway % 128
    pae = remainder // 8
    yway = remainder % 8
    return kyat, pae, yway

def format_weight(kyat, pae, yway):
    return f"{kyat} ကျပ် ၊ {pae} ပဲ ၊ {yway} ရွဲ"

# Session State စတင်သတ်မှတ်ခြင်း
if "sales_list" not in st.session_state:
    st.session_state.sales_list = []
if "inflow_list" not in st.session_state:
    st.session_state.inflow_list = []
if "admin_password" not in st.session_state:
    st.session_state.admin_password = "zwehtet2026"

# Header
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("🪙 ဇွဲထက် ရွှေဆိုင် - စာရင်းစစ်စနစ် (Enterprise V6 Pro)")
    st.caption("✨ AI စနစ်သုံး ဘောက်ချာဖတ်ခြင်း၊ လုံခြုံသော စာရင်းစစ်စနစ်နှင့် အမှားရှာဖွေရေး")
with col_date:
    audit_date = st.date_input("📅 စာရင်းစစ်သည့် ရက်စွဲ", date.today(), key="audit_date_main")

st.markdown("---")

# --- Sidebar (Settings, API Key & Secure Founder Login Mode) ---
with st.sidebar:
    st.subheader("⚙️ ဆက်တင်များ (Settings)")
    shop_owner = st.text_input("တာဝန်ခံ အမည် (Auditor)", value="ကိုအောင်နိုင်ဦး", key="shop_owner_name")
    
    st.markdown("---")
    st.subheader("🤖 Gemini AI API")
    gemini_api_key = st.text_input("Gemini API Key ထည့်ပါ", type="password", key="gemini_api_key")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        
    st.markdown("---")
    st.subheader("🔐 Founder / Admin လုံခြုံရေး")
    
    # 🔒 Password ပြောင်းလဲသည့် အပိုင်း (Old Password စစ်ဆေးခြင်း)
    with st.expander("⚙️ Admin Password ပြောင်းရန်"):
        old_pass_input = st.text_input("Password အဟောင်း ထည့်ပါ", type="password", key="old_pass_input")
        new_pass_input = st.text_input("Password အသစ် ထည့်ပါ", type="password", key="new_pass_input")
        confirm_pass_input = st.text_input("Password အသစ် ထပ်မံရိုက်ပါ", type="password", key="confirm_pass_input")
        
        if st.button("💾 Password အသစ် သတ်မှတ်မည်"):
            if old_pass_input == st.session_state.admin_password:
                if new_pass_input and new_pass_input == confirm_pass_input:
                    st.session_state.admin_password = new_pass_input
                    st.success("✅ Password အဟောင်းကို ပယ်ဖျက်ပြီး Password အသစ်သို့ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။")
                else:
                    st.error("❌ Password အသစ်နှစ်ခု မတူညီပါ သို့မဟုတ် ကွက်လပ်ဖြစ်နေပါသည်။")
            else:
                st.error("❌ Password အဟောင်း မှားယွင်းနေပါသည်။")

    st.markdown("---")
    st.subheader("🔑 Admin ဝင်ရန်")
    input_pass = st.text_input("Admin Password ရိုက်ပါ", type="password", key="login_pass_input")
    
    is_founder = False
    if input_pass:
        if input_pass == st.session_state.admin_password:
            is_founder = True
            st.success("✅ Admin အဖြစ် ဝင်ရောက်ပြီးပါပြီ။")
        else:
            st.error("❌ Incorrect Password! စကားဝှက် မှားယွင်းနေပါသည်။")

# --- အပိုင်း (၁) မနက်ခင်း ဖွင့်ပွဲလက်ကျန် ---
st.subheader("☀️ ၁။ မနက်ခင်း ဖွင့်ပွဲလက်ကျန် (Opening Stock)")
op_col1, op_col2, op_col3, op_col4 = st.columns(4)
with op_col1:
    op_k = st.number_input("ကျပ်သား (မနက်)", min_value=0, value=0, key="op_k")
with op_col2:
    op_p = st.number_input("ပဲ (မနက်)", min_value=0, max_value=15, value=0, key="op_p")
with op_col3:
    op_y = st.number_input("ရွဲ (မနက်)", min_value=0, max_value=7, value=0, key="op_y")
with op_col4:
    op_items = st.number_input("အထည် အရေအတွက် (မနက်)", min_value=0, value=0, key="op_items")

st.markdown("---")

# --- အပိုင်း (၂) အဝင် / အရောင်းဘောက်ချာ (Manual & AI OCR) ---
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("📥 ၂။ ပစ္စည်းအသစ် အဝင်ထည့်ရန် (Inflow)")
    with st.form("inflow_form", clear_on_submit=True):
        in_name = st.text_input("ပစ္စည်း အမျိုးအစား / မှတ်ချက်", key="in_name_input")
        ic1, ic2 = st.columns(2)
        in_qty = ic1.number_input("အထည် အရေအတွက်", min_value=0, value=0, key="in_qty_input")
        c1, c2, c3 = st.columns(3)
        in_k = c1.number_input("ကျပ်သား", min_value=0, value=0, key="in_k_input")
        in_p = c2.number_input("ပဲ", min_value=0, max_value=15, value=0, key="in_p_input")
        in_y = c3.number_input("ရွဲ", min_value=0, max_value=7, value=0, key="in_y_input")
        submit_in = st.form_submit_button("➕ အဝင်စာရင်း ထည့်မည်")
        
        if submit_in:
            if in_k == 0 and in_p == 0 and in_y == 0 and in_qty == 0:
                st.warning("အချက်အလက် ထည့်သွင်းပေးပါ!")
            else:
                st.session_state.inflow_list.append({
                    "ရက်စွဲ": str(audit_date),
                    "အမျိုးအစား": "အဝင် (Inflow)",
                    "ဘောက်ချာ/မှတ်ချက်": in_name if in_name else "ပစ္စည်းအသစ်",
                    "အရေအတွက်": in_qty,
                    "ကျပ်သား": in_k, "ပဲ": in_p, "ရွဲ": in_y,
                    "total_r": to_rupe(in_k, in_p, in_y),
                    "status": "ACTIVE"
                })

    if st.session_state.inflow_list:
        display_in = [i for i in st.session_state.inflow_list if i["status"] == "ACTIVE"]
        if display_in:
            st.dataframe(pd.DataFrame(display_in).drop(columns=["total_r", "status"], errors="ignore"), use_container_width=True)

with col_out:
    st.subheader("📤 ၃။ အရောင်းဘောက်ချာ ထည့်ရန် & ပယ်ဖျက်ခြင်း (Void)")
    
    # 📸 AI OCR Voucher Scanner
    with st.expander("📸 Gemini AI ဖြင့် ဘောက်ချာဓာတ်ပုံဖတ်ရန် (OCR)"):
        uploaded_voucher = st.file_uploader("ဘောက်ချာဓာတ်ပုံ တင်ပါ", type=["jpg", "png", "jpeg"], key="voucher_file")
        ocr_v_no = ""
        ocr_type = "လက်စွပ်"
        ocr_qty = 0
        ocr_k = 0
        ocr_p = 0
        ocr_y = 0
        
        if uploaded_voucher and gemini_api_key:
            if st.button("🔍 AI ဖြင့် ဘောက်ချာဖတ်မည်"):
                try:
                    img = Image.open(uploaded_voucher)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = """
                    You are an assistant for a Myanmar gold shop. Extract details from this voucher image:
                    - voucher_no (string)
                    - item_type (one of: လက်စွပ်, ဆွဲကြိုး, လက်ကောက်, နားကပ်, ဆွဲသီး, အခြား)
                    - quantity (integer)
                    - kyat (integer)
                    - pae (integer)
                    - yway (integer)
                    Output strictly valid JSON with keys: voucher_no, item_type, quantity, kyat, pae, yway.
                    """
                    response = model.generate_content([prompt, img])
                    res_text = response.text.replace("```json", "").replace("```", "").strip()
                    extracted_data = json.loads(res_text)
                    
                    st.session_state.sales_list.append({
                        "id": len(st.session_state.sales_list) + 1,
                        "ရက်စွဲ": str(audit_date),
                        "အမျိုးအစား": f"အရောင်း ({extracted_data.get('item_type', 'လက်စွပ်')})",
                        "ဘောက်ချာ/မှတ်ချက်": extracted_data.get('voucher_no', 'AI-SCAN'),
                        "အရေအတွက်": int(extracted_data.get('quantity', 1)),
                        "ကျပ်သား": int(extracted_data.get('kyat', 0)),
                        "ပဲ": int(extracted_data.get('pae', 0)),
                        "ရွဲ": int(extracted_data.get('yway', 0)),
                        "total_r": to_rupe(int(extracted_data.get('kyat', 0)), int(extracted_data.get('pae', 0)), int(extracted_data.get('yway', 0))),
                        "status": "ACTIVE"
                    })
                    st.success("✅ AI က ဘောက်ချာဖတ်ပြီး စာရင်းထဲသို့ တိုက်ရိုက် ထည့်သွင်းပေးလိုက်ပါပြီ။")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ AI ဖတ်ရာတွင် အမှားဖြစ်ပေါ်ပါသည် - {str(e)}")

    # Manual Form
    with st.form("sales_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        v_no = f1.text_input("ဘောက်ချာ နံပါတ်", value="", key="sales_v_no")
        item_type = f2.selectbox("ရွှေထည် အမျိုးအစား", ["လက်စွပ်", "ဆွဲကြိုး", "လက်ကောက်", "နားကပ်", "ဆွဲသီး", "အခြား"], key="sales_item_type")
        sc1, sc2, sc3 = st.columns(3)
        sale_qty = sc1.number_input("အထည် အရေအတွက်", min_value=0, value=0, key="sale_qty_input")
        s_k = sc2.number_input("ကျပ်သား", min_value=0, value=0, key="sale_k_input")
        s_p = sc3.number_input("ပဲ", min_value=0, max_value=15, value=0, key="sale_p_input")
        s_y = sc3.number_input("ရွဲ", min_value=0, max_value=7, value=0, key="sale_y_input")
        submit_sale = st.form_submit_button("➕ အရောင်းဘောက်ချာ ထည့်မည်")
        
        if submit_sale:
            if s_k == 0 and s_p == 0 and s_y == 0 and sale_qty == 0:
                st.warning("အချက်အလက် ထည့်သွင်းပေးပါ!")
            else:
                st.session_state.sales_list.append({
                    "id": len(st.session_state.sales_list) + 1,
                    "ရက်စွဲ": str(audit_date),
                    "အမျိုးအစား": f"အရောင်း ({item_type})",
                    "ဘောက်ချာ/မှတ်ချက်": v_no if v_no else "V-001",
                    "အရေအတွက်": sale_qty,
                    "ကျပ်သား": s_k, "ပဲ": s_p, "ရွဲ": s_y,
                    "total_r": to_rupe(s_k, s_p, s_y),
                    "status": "ACTIVE"
                })
                st.rerun()

    if st.session_state.sales_list:
        display_sales = [{
            "ID": s["id"],
            "ရက်စွဲ": s["ရက်စွဲ"],
            "အမျိုးအစား": s["အမျိုးအစား"],
            "ဘောက်ချာ/မှတ်ချက်": s["ဘောက်ချာ/မှတ်ချက်"],
            "အရေအတွက်": s["အရေအတွက်"],
            "ကျပ်သား": s["ကျပ်သား"], "ပဲ": s["ပဲ"], "ရွဲ": s["ရွဲ"],
            "အခြေအနေ": s["status"]
        } for s in st.session_state.sales_list]
        st.dataframe(pd.DataFrame(display_sales), use_container_width=True)
        
        # ❌ Void Feature
        v_ids = [s["id"] for s in st.session_state.sales_list if s["status"] == "ACTIVE"]
        if v_ids:
            selected_void_id = st.selectbox("ပယ်ဖျက်မည့် ဘောက်ချာ ID ကို ရွေးပါ", v_ids, key="void_select")
            if st.button("⚠️ ရွေးချယ်ထားသော ဘောက်ချာကို ပယ်ဖျက်မည် (Void)", key="void_btn"):
                for s in st.session_state.sales_list:
                    if s["id"] == selected_void_id:
                        s["status"] = "VOIDED"
                        s["ကျပ်သား"] = 0; s["ပဲ"] = 0; s["ရွဲ"] = 0; s["အရေအတွက်"] = 0; s["total_r"] = 0
                st.success(f"✅ ဘောက်ချာ ID #{selected_void_id} ကို ပယ်ဖျက်ပြီးပါပြီ။")
                st.rerun()

# စုစုပေါင်း တွက်ချက်ခြင်း
total_in_r = sum(item["total_r"] for item in st.session_state.inflow_list if item.get("status") == "ACTIVE")
total_sold_r = sum(item["total_r"] for item in st.session_state.sales_list if item.get("status") == "ACTIVE")
total_in_qty = sum(item["အရေအတွက်"] for item in st.session_state.inflow_list if item.get("status") == "ACTIVE")
total_sold_qty = sum(item["အရေအတွက်"] for item in st.session_state.sales_list if item.get("status") == "ACTIVE")

in_tot_k, in_tot_p, in_tot_y = from_rupe(total_in_r)
sold_tot_k, sold_tot_p, sold_tot_y = from_rupe(total_sold_r)

st.info(f"📊 **စုစုပေါင်း အဝင်:** {format_weight(in_tot_k, in_tot_p, in_tot_y)} ({total_in_qty} ထည်)  |  **စုစုပေါင်း ရောင်းထွက်:** {format_weight(sold_tot_k, sold_tot_p, sold_tot_y)} ({total_sold_qty} ထည်)")
st.markdown("---")

# --- အပိုင်း (၄) ညနေ ဆိုင်ပိတ်ချိန် စစ်ဆေးခြင်း ---
st.subheader("🔍 ၄။ ညနေ ဆိုင်ပိတ်ချိန် လက်တွေ့စစ်ဆေးချက် (Actual Count)")
act_col1, act_col2, act_col3, act_col4 = st.columns(4)
with act_col1:
    act_k = st.number_input("ကျပ်သား (လက်တွေ့)", min_value=0, value=0, key="act_k_input")
with act_col2:
    act_p = st.number_input("ပဲ (လက်တွေ့)", min_value=0, max_value=15, value=0, key="act_p_input")
with act_col3:
    act_y = st.number_input("ရွဲ (လက်တွေ့)", min_value=0, max_value=7, value=0, key="act_y_input")
with act_col4:
    act_items = st.number_input("လက်တွေ့ အထည်အရေအတွက်", min_value=0, value=0, key="act_items_input")

op_r = to_rupe(op_k, op_p, op_y)
act_r = to_rupe(act_k, act_p, act_y)
expected_r = op_r + total_in_r - total_sold_r
diff_r = act_r - expected_r

expected_items = op_items + total_in_qty - total_sold_qty
diff_items = act_items - expected_items

exp_k, exp_p, exp_y = from_rupe(abs(expected_r))
d_k, d_p, d_y = from_rupe(abs(diff_r))

st.markdown("---")
st.subheader("🤖 စာရင်းစစ် အမှားရှာဖွေရေး အစီရင်ခံစာ & AI အကြံပြုချက်များ (Error Diagnosis & AI Recommendations)")

st.write(f"📌 **ရှိသင့်သော လက်ကျန်:** `{' - ' if expected_r < 0 else ''}{format_weight(exp_k, exp_p, exp_y)}` ({expected_items} ထည်)")
st.write(f"📌 **လက်တွေ့ ရှိသော လက်ကျန်:** `{format_weight(act_k, act_p, act_y)}` ({act_items} ထည်)")

# 🧠 Smart AI Diagnosis & Recommendations Logic
if diff_r == 0 and diff_items == 0:
    st.success("✅ စာရင်းများ အပြည့်အစုံ ကိုက်ညီပါသည်။ မည်သည့် အမှားအယွင်းမှ မရှိပါ။")
    result_status = "MATCHED (စာရင်းကိုက်ညီသည်)"
    diff_text = "0"
else:
    st.error("⚠️ **တွေ့ရှိချက် - စာရင်း မကိုက်ညီပါ!**")
    
    if expected_r < 0:
        st.warning("💡 **AI အကြံပြုချက် (Root-cause Warning):** ရှိသင့်သောလက်ကျန်တွင် အနှုတ်လက္ခဏာ (`-`) ထွက်နေပါသည်။ မနက်ခင်း ဖွင့်ပွဲလက်ကျန် (Opening Stock) ထည့်သွင်းမှု နည်းနေခြင်း (သို့မဟုတ်) ရောင်းထွက်စာရင်း အလွန်အကျွံ မှားယွင်းရိုက်ထည့်မိခြင်း ရှိမရှိ စစ်ဆေးပါ။")

    if diff_r < 0:
        st.markdown(f"* ❌ **အလေးချိန် လိုနေသည် (Shortage):** `{format_weight(d_k, d_p, d_y)}`")
        st.info("💡 **AI ၏ အကြံပြုချက် (Recommendations):**\n1. အရောင်းဘောက်ချာ တစ်ခုခု ရိုက်ထည့်ရန် ကျန်နေနိုင်ပါသည် (သို့မဟုတ်) ပမာဏပိုမှားရိုက်မိထားနိုင်ပါသည်။\n2. ဖောက်သည်ထံမှ ပစ္စည်းအာမခံ/ပေါင်နှံထားသည်များကို ပြန်လည်စစ်ဆေးပါ။")
        result_status = "SHORTAGE (အလေးချိန် လိုနေသည်)"
        diff_text = f"- {format_weight(d_k, d_p, d_y)}"
    elif diff_r > 0:
        st.markdown(f"* ⚠️ **အလေးချိန် ပိုနေသည် (Excess):** `{format_weight(d_k, d_p, d_y)}`")
        st.info("💡 **AI ၏ အကြံပြုချက် (Recommendations):**\n1. ပစ္စည်းအသစ်အဝင် (Inflow) စာရင်းသွင်းစဉ် အလေးချိန် သို့မဟုတ် အရေအတွက် ပိုမိုရိုက်ထည့်မိခြင်း ရှိမရှိ စစ်ဆေးပါ။\n2. မနက်ခင်း ဖွင့်ပွဲလက်ကျန် (Opening Stock) ကို အတိုးအလျှော့ မှားယွင်းရိုက်မိခြင်း ရှိမရှိ ပြန်လည်စစ်ဆေးပါ။")
        result_status = "EXCESS (အလေးချိန် ပိုနေသည်)"
        diff_text = f"+ {format_weight(d_k, d_p, d_y)}"
    else:
        diff_text = "0"
    
    if diff_items != 0:
        st.markdown(f"* 📦 **အထည်အရေအတွက် ကွာခြားချက်:** `{abs(diff_items)} ထည်` {'လျော့နည်းနေသည်' if diff_items < 0 else 'ပိုနေသည်'}")

st.markdown("---")

# --- အပိုင်း (၅) စာရင်းသိမ်းဆည်းခြင်းနှင့် Admin မှတ်တမ်း ---
st.subheader("💾 ၅။ စာရင်းသိမ်းဆည်းရန်နှင့် အချက်အလက်များ")

summary_data = {
    "ရက်စွဲ": [str(audit_date)],
    "တာဝန်ခံဝန်ထမ်း": [shop_owner],
    "မနက်လက်ကျန်": [format_weight(op_k, op_p, op_y)],
    "စုစုပေါင်းအဝင်": [format_weight(in_tot_k, in_tot_p, in_tot_y)],
    "စုစုပေါင်းရောင်းထွက်": [format_weight(sold_tot_k, sold_tot_p, sold_tot_y)],
    "ရှိသင့်သောလက်ကျန်": [f"- {format_weight(exp_k, exp_p, exp_y)}" if expected_r < 0 else format_weight(exp_k, exp_p, exp_y)],
    "လက်တွေ့လက်ကျန်": [format_weight(act_k, act_p, act_y)],
    "ကွာဟချက်": [diff_text],
    "စစ်ဆေးချက်ရလဒ်": [result_status]
}
df_summary = pd.DataFrame(summary_data)
csv_summary = df_summary.to_csv(index=False).encode('utf-8-sig')

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    st.download_button(label="📥 နေ့စဉ်စာရင်းချုပ် (Excel/CSV) ဒေါင်းလုဒ်ဆွဲရန်", data=csv_summary, file_name=f"Zwe_Htet_Summary_{audit_date}.csv", mime="text/csv", key="download_csv_btn")

with btn_col2:
    history_file = "zwe_htet_audit_history.csv"
    if st.button("💾 ဆိုင်မှတ်တမ်းသို့ သိမ်းမည် (Save to System Log)", type="primary", key="save_history_btn"):
        if os.path.exists(history_file):
            df_existing = pd.read_csv(history_file)
            df_combined = pd.concat([df_existing, df_summary], ignore_index=True)
            df_combined.to_csv(history_file, index=False, encoding='utf-8-sig')
        else:
            df_summary.to_csv(history_file, index=False, encoding='utf-8-sig')
        st.success("✅ စာရင်းချုပ် အချက်အလက်အပြည့်အစုံကို လုံခြုံစွာ သိမ်းဆည်းပြီးပါပြီ!")

# --- 🔐 FOUNDER / ADMIN SECURED SECTION ---
st.markdown("---")
if is_founder:
    st.markdown("### 🔐 Founder သီးသန့် ဝင်ရောက်စစ်ဆေးသော မှတ်တမ်း (Secure Audit Trail)")
    st.info("💡 သင်သည် Admin Password ဖြင့် အောင်မြင်စွာ ဝင်ထားသောကြောင့် နေ့စဉ်စာရင်းချုပ်များကို ကြည့်ရှုနိုင်ပါသည်။")
    
    if os.path.exists(history_file):
        df_hist = pd.read_csv(history_file)
        st.dataframe(df_hist, use_container_width=True)
        
        if st.button("🗑️ [Founder သီးသန့်] မှတ်တမ်းအားလုံးကို ရှင်းလင်းရန် (Reset Log)", key="founder_reset_btn"):
            if os.path.exists(history_file):
                os.remove(history_file)
                st.success("✅ မှတ်တမ်းဟောင်းအားလုံးကို ရှင်းလင်းပြီးပါပြီ။")
                st.rerun()
    else:
        st.warning("⚠️ သိမ်းဆည်းထားသော ဆိုင်မှတ်တမ်း ဖိုင် မရှိသေးပါ။")
else:
    st.info("🔒 **Admin / Founder မှတ်တမ်းများကို ကြည့်ရှုလိုပါက ဘယ်ဘက် Sidebar ရှိ Password များကို မှန်ကန်စွာ ထည့်သွင်းပါ။**")