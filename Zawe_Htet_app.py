import streamlit as st
import pandas as pd
from datetime import date
import os
import google.generativeai as genai
from PIL import Image
import json
import io

# စာမျက်နှာ အကျယ်ချဲ့ခြင်းနှင့် Page Config
st.set_page_config(
    page_title="ဇွဲထက် ရွှေဆိုင် - Master Audit Workflow V7.2 (Excel Multi-sheet)",
    layout="wide",
    page_icon="💎"
)

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

# 🗂️ Master Categories & Sub-categories Structure
CATEGORY_STRUCTURE = {
    "စိန်": {
        "-": ["နားကပ်", "လက်စွပ်", "ဆွဲသီး", "လက်ကောက်", "ဟန်ချိန်း", "ဘယက်", "ရတီနားကပ်", "ရတီလက်စွပ်"]
    },
    "ရွှေ": {
        "၁၅ ပဲရည်": ["လက်စွပ်", "လက်ကောက်", "ဆွဲကြိုး", "နားကပ်", "ဆွဲသီး", "ဟန်ချိန်း", "ကလစ်"],
        "၁၆ ပဲရည်": ["လက်ကောက်", "လက်စွပ်", "ဆွဲကြိုး", "နားကပ်", "ဆွဲသီး", "ဟန်ချိန်း", "ဖိချူး", "cut eye", "ရွှေတွဲအပ်", "ချိတ်"]
    },
    "ပလက်တီနမ်": {
        "-": ["ဆွဲကြိုး", "ဟန်ချိန်း", "လက်စွပ်", "ဆွဲသီး", "နားကပ်", "ချိတ်", "cut eye"]
    }
}

def get_all_category_rows():
    rows = []
    for main_cat, sub_dict in CATEGORY_STRUCTURE.items():
        for sub_cat, items in sub_dict.items():
            for item in items:
                rows.append({
                    "အဓိကအမျိုးအစား": main_cat,
                    "ခွဲအမျိုးအစား": sub_cat,
                    "ပစ္စည်းအမည်": item
                })
    return rows

# --- Session State စတင်သတ်မှတ်ခြင်း ---
if "opening_stock_df" not in st.session_state:
    init_rows = get_all_category_rows()
    for r in init_rows:
        r["မနက်လက်ကျန် (အရေအတွက်)"] = 0
        r["ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"] = 0
    st.session_state.opening_stock_df = pd.DataFrame(init_rows)

if "inflow_list" not in st.session_state:
    st.session_state.inflow_list = []

if "sales_list" not in st.session_state:
    st.session_state.sales_list = []

if "admin_password" not in st.session_state:
    st.session_state.admin_password = "zwehtet2026"

if "flash_msg" not in st.session_state:
    st.session_state.flash_msg = None

if st.session_state.flash_msg:
    st.toast(st.session_state.flash_msg)
    st.session_state.flash_msg = None

# --- Header ---
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("💎 ဇွဲထက် ရွှေဆိုင် - စာရင်းစစ်နှင့် လက်ကျန်ထိန်းချုပ်ရေးစနစ် (V7.2)")
    st.caption("✨ စိန် ၊ ရွှေ (၁၅/၁၆ပဲရည်) ၊ ပလက်တီနမ် ၊ ပန်းထိမ်ဆရာ အဝင်နှင့် Excel Multi-sheet Report စနစ်")
with col_date:
    audit_date = st.date_input("📅 စာရင်းစစ်သည့် ရက်စွဲ", date.today(), key="audit_date_main")

st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.subheader("⚙️ ဆက်တင်များ (Settings)")
    shop_owner = st.text_input("တာဝန်ခံဝန်ထမ်း အမည် (Auditor)", value="ကိုအောင်နိုင်ဦး", key="shop_owner_name")
    
    st.markdown("---")
    st.subheader("🤖 Gemini AI API (OCR)")
    gemini_api_key = st.text_input("Gemini API Key ထည့်ပါ", type="password", key="gemini_api_key")
    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)
        
    st.markdown("---")
    st.subheader("🔐 Founder / Admin လုံခြုံရေး")
    
    with st.expander("⚙️ Admin Password ပြောင်းရန်"):
        old_pass_input = st.text_input("Password အဟောင်း ထည့်ပါ", type="password", key="old_pass_input")
        new_pass_input = st.text_input("Password အသစ် ထည့်ပါ", type="password", key="new_pass_input")
        confirm_pass_input = st.text_input("Password အသစ် ထပ်မံရိုက်ပါ", type="password", key="confirm_pass_input")
        
        if st.button("💾 Password အသစ် သတ်မှတ်မည်"):
            if old_pass_input == st.session_state.admin_password:
                if new_pass_input and new_pass_input == confirm_pass_input:
                    st.session_state.admin_password = new_pass_input
                    st.success("✅ Password အသစ်သို့ အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ။")
                else:
                    st.error("❌ Password အသစ်နှစ်ခု မတူညီပါ သို့မဟုတ် ကွက်လပ်ဖြစ်နေပါသည်။")
            else:
                st.error("❌ Password အဟောင်း မှားယွင်းနေပါသည်။")

    st.markdown("---")
    st.subheader("🔑 Admin / Founder ဝင်ရန်")
    input_pass = st.text_input("Admin Password ရိုက်ပါ", type="password", key="login_pass_input")
    
    is_founder = False
    if input_pass:
        if input_pass == st.session_state.admin_password:
            is_founder = True
            st.success("✅ Founder / Admin အဖြစ် ဝင်ရောက်ပြီးပါပြီ။")
        else:
            st.error("❌ စကားဝှက် မှားယွင်းနေပါသည်။")

def render_category_selector(prefix):
    c1, c2, c3 = st.columns(3)
    with c1:
        main_cat = st.selectbox("၁။ အဓိက ခေါင်းစဉ်ကြီး", ["စိန်", "ရွှေ", "ပလက်တီနမ်"], key=f"{prefix}_main_cat")
    with c2:
        if main_cat == "ရွှေ":
            sub_cat = st.selectbox("၂။ ရွှေ အမျိုးအစားခွဲ", ["၁၅ ပဲရည်", "၁၆ ပဲရည်"], key=f"{prefix}_sub_cat")
        else:
            st.selectbox("၂။ အမျိုးအစားခွဲ", ["-"], disabled=True, key=f"{prefix}_sub_cat_disabled")
            sub_cat = "-"
    with c3:
        item_list = CATEGORY_STRUCTURE[main_cat][sub_cat]
        item_name = st.selectbox("၃။ ပစ္စည်း အမျိုးအမည်", item_list, key=f"{prefix}_item_name")
    return main_cat, sub_cat, item_name

op_col_config = {
    "ပစ္စည်းအမည်": st.column_config.TextColumn("ပစ္စည်းအမည်", disabled=True),
    "မနက်လက်ကျန် (အရေအတွက်)": st.column_config.NumberColumn("မနက်လက်ကျန် (အရေအတွက်)", min_value=0, step=1, required=True, default=0)
}
act_col_config = {
    "ပစ္စည်းအမည်": st.column_config.TextColumn("ပစ္စည်းအမည်", disabled=True),
    "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)": st.column_config.NumberColumn("ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)", min_value=0, step=1, required=True, default=0)
}

# ==========================================
# အပိုင်း (၁) မနက်ခင်း ဖွင့်ပွဲလက်ကျန် (Opening Stock)
# ==========================================
st.subheader("☀️ ၁။ မနက်ခင်း ဖွင့်ပွဲလက်ကျန် စာရင်းထည့်သွင်းရန် (Opening Stock)")

tab_op1, tab_op2, tab_op3 = st.tabs(["💎 စိန် (Diamond)", "🪙 ရွှေ (၁၅ ပဲရည် / ၁၆ ပဲရည်)", "⚪ ပလက်တီနမ် (Platinum)"])

with tab_op1:
    sein_mask = st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "စိန်"
    edited_sein_op = st.data_editor(
        st.session_state.opening_stock_df[sein_mask][["ပစ္စည်းအမည်", "မနက်လက်ကျန် (အရေအတွက်)"]],
        column_config=op_col_config, hide_index=True, use_container_width=True, key="editor_op_sein"
    )
    st.session_state.opening_stock_df.loc[sein_mask, "မနက်လက်ကျန် (အရေအတွက်)"] = edited_sein_op["မနက်လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values

with tab_op2:
    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**🔸 ၁၅ ပဲရည် မနက်လက်ကျန်**")
        g15_mask = (st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "ရွှေ") & (st.session_state.opening_stock_df["ခွဲအမျိုးအစား"] == "၁၅ ပဲရည်")
        edited_g15_op = st.data_editor(
            st.session_state.opening_stock_df[g15_mask][["ပစ္စည်းအမည်", "မနက်လက်ကျန် (အရေအတွက်)"]],
            column_config=op_col_config, hide_index=True, use_container_width=True, key="editor_op_g15"
        )
        st.session_state.opening_stock_df.loc[g15_mask, "မနက်လက်ကျန် (အရေအတွက်)"] = edited_g15_op["မနက်လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values
    with g2:
        st.markdown("**🔸 ၁၆ ပဲရည် မနက်လက်ကျန်**")
        g16_mask = (st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "ရွှေ") & (st.session_state.opening_stock_df["ခွဲအမျိုးအစား"] == "၁၆ ပဲရည်")
        edited_g16_op = st.data_editor(
            st.session_state.opening_stock_df[g16_mask][["ပစ္စည်းအမည်", "မနက်လက်ကျန် (အရေအတွက်)"]],
            column_config=op_col_config, hide_index=True, use_container_width=True, key="editor_op_g16"
        )
        st.session_state.opening_stock_df.loc[g16_mask, "မနက်လက်ကျန် (အရေအတွက်)"] = edited_g16_op["မနက်လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values

with tab_op3:
    plat_mask = st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "ပလက်တီနမ်"
    edited_plat_op = st.data_editor(
        st.session_state.opening_stock_df[plat_mask][["ပစ္စည်းအမည်", "မနက်လက်ကျန် (အရေအတွက်)"]],
        column_config=op_col_config, hide_index=True, use_container_width=True, key="editor_op_plat"
    )
    st.session_state.opening_stock_df.loc[plat_mask, "မနက်လက်ကျန် (အရေအတွက်)"] = edited_plat_op["မနက်လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values

st.markdown("---")

# ==========================================
# အပိုင်း (၂) ပန်းထိမ်ဆရာ အဝင် & အရောင်းစာရင်း (Inflow & Sales)
# ==========================================
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("📥 ၂။ ပန်းထိမ်ဆရာ ပစ္စည်းအဝင်စာရင်း (Artisan Inflow)")
    in_main_cat, in_sub_cat, in_item_name = render_category_selector("inflow")
    
    with st.form("inflow_form", clear_on_submit=True):
        f_in1, f_in2 = st.columns(2)
        artisan_name = f_in1.text_input("👨‍🎨 ပန်းထိမ်ဆရာ နာမည် *", placeholder="ဥပမာ - ဆရာဦးကျော်")
        in_code = f_in2.text_input("🏷️ ပစ္စည်း Code နံပါတ်", placeholder="ဥပမာ - D-001")
        
        f_in3, f_in4 = st.columns(2)
        in_qty = f_in3.number_input("အဝင် အရေအတွက် *", min_value=1, value=1, step=1)
        in_note = f_in4.text_input("မှတ်ချက်", placeholder="မှတ်ချက်")
        
        submit_in = st.form_submit_button("➕ ပန်းထိမ်ဆရာ အဝင်စာရင်း ထည့်မည်")
        if submit_in:
            if not artisan_name.strip():
                st.warning("⚠️ ပန်းထိမ်ဆရာ နာမည်ကို ထည့်သွင်းပေးပါ!")
            else:
                st.session_state.inflow_list.append({
                    "id": len(st.session_state.inflow_list) + 1,
                    "ရက်စွဲ": str(audit_date),
                    "ပရိန်ဆရာအမည်": artisan_name.strip(),
                    "Code နံပါတ်": in_code.strip() if in_code.strip() else "-",
                    "အဓိကအမျိုးအစား": in_main_cat,
                    "ခွဲအမျိုးအစား": in_sub_cat,
                    "ပစ္စည်းအမည်": in_item_name,
                    "အရေအတွက်": int(in_qty),
                    "မှတ်ချက်": in_note.strip() if in_note.strip() else "-",
                    "status": "ACTIVE"
                })
                st.session_state.flash_msg = f"✅ ပန်းထိမ်ဆရာ '{artisan_name.strip()}' ၏ အဝင်စာရင်း သိမ်းဆည်းပြီးပါပြီ။"
                st.rerun()

    if st.session_state.inflow_list:
        st.markdown("**📋 ယနေ့ ပန်းထိမ်ဆရာ အဝင် မှတ်တမ်းများ**")
        st.dataframe(pd.DataFrame(st.session_state.inflow_list), use_container_width=True, hide_index=True)
        active_in_ids = [i["id"] for i in st.session_state.inflow_list if i["status"] == "ACTIVE"]
        if active_in_ids:
            v_in_col1, v_in_col2 = st.columns([2, 1])
            void_in_id = v_in_col1.selectbox("ပယ်ဖျက်မည့် အဝင် ID", active_in_ids, key="void_in_select")
            if v_in_col2.button("⚠️ အဝင် Void", key="void_in_btn"):
                for item in st.session_state.inflow_list:
                    if item["id"] == void_in_id:
                        item["status"] = "VOIDED"
                        item["အရေအတွက်"] = 0
                st.session_state.flash_msg = f"✅ အဝင် ID #{void_in_id} ကို Void လုပ်ပြီးပါပြီ။"
                st.rerun()

with col_out:
    st.subheader("📤 ၃။ အရောင်းစာရင်းသွင်းရန် & Void (Sales)")
    
    with st.expander("📸 Gemini AI ဖြင့် အရောင်းဘောက်ချာ ဖတ်ရန် (OCR)"):
        uploaded_voucher = st.file_uploader("ဘောက်ချာပုံ တင်ပါ", type=["jpg", "png", "jpeg"], key="ocr_uploader")
        if uploaded_voucher and gemini_api_key:
            if st.button("🔍 AI ဖြင့် ဘောက်ချာဖတ်မည်"):
                try:
                    img = Image.open(uploaded_voucher)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    prompt = """
                    Extract sales voucher info in valid JSON: voucher_no, item_code, main_category (စိန်, ရွှေ, ပလက်တီနမ်), sub_category (-, ၁၅ ပဲရည်, ၁၆ ပဲရည်), item_name, quantity
                    """
                    response = model.generate_content([prompt, img])
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(clean_json)
                    
                    m_c = data.get("main_category", "ရွှေ")
                    s_c = data.get("sub_category", "၁၆ ပဲရည်" if m_c == "ရွှေ" else "-")
                    i_n = data.get("item_name", "လက်စွပ်")
                    
                    st.session_state.sales_list.append({
                        "id": len(st.session_state.sales_list) + 1,
                        "ရက်စွဲ": str(audit_date),
                        "ဘောက်ချာနံပါတ်": data.get("voucher_no", "AI-VOUCHER"),
                        "Code နံပါတ်": data.get("item_code", "AI-CODE"),
                        "အဓိကအမျိုးအစား": m_c,
                        "ခွဲအမျိုးအစား": s_c,
                        "ပစ္စည်းအမည်": i_n,
                        "အရေအတွက်": int(data.get("quantity", 1)),
                        "မှတ်ချက်": "AI OCR Scan",
                        "status": "ACTIVE"
                    })
                    st.session_state.flash_msg = "✅ AI ဖြင့် ဘောက်ချာဖတ်ပြီးပါပြီ။"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ အမှားဖြစ်ပေါ်ပါသည်: {e}")

    sale_main_cat, sale_sub_cat, sale_item_name = render_category_selector("sales")
    
    with st.form("sales_form", clear_on_submit=True):
        f_s1, f_s2 = st.columns(2)
        sale_code = f_s1.text_input("🏷️ ရောင်းထွက် Code *", placeholder="ဥပမာ - G16-R025")
        voucher_no = f_s2.text_input("🧾 ဘောက်ချာ နံပါတ်", placeholder="ဥပမာ - V-001")
        
        f_s3, f_s4 = st.columns(2)
        sale_qty = f_s3.number_input("အရေအတွက် *", min_value=1, value=1, step=1)
        sale_note = f_s4.text_input("မှတ်ချက်", placeholder="မှတ်ချက်")
        
        submit_sale = st.form_submit_button("➕ အရောင်းစာရင်း ထည့်မည်")
        if submit_sale:
            clean_code = sale_code.strip()
            existing_active_codes = [s["Code နံပါတ်"] for s in st.session_state.sales_list if s["status"] == "ACTIVE"]
            if not clean_code:
                st.warning("⚠️ Code နံပါတ် ထည့်သွင်းပေးပါ!")
            elif clean_code in existing_active_codes:
                st.error(f"❌ Code နံပါတ် '{clean_code}' သည် ထည့်သွင်းပြီးသား ဖြစ်နေပါသည်!")
            else:
                st.session_state.sales_list.append({
                    "id": len(st.session_state.sales_list) + 1,
                    "ရက်စွဲ": str(audit_date),
                    "ဘောက်ချာနံပါတ်": voucher_no.strip() if voucher_no.strip() else "V-001",
                    "Code နံပါတ်": clean_code,
                    "အဓိကအမျိုးအစား": sale_main_cat,
                    "ခွဲအမျိုးအစား": sale_sub_cat,
                    "ပစ္စည်းအမည်": sale_item_name,
                    "အရေအတွက်": int(sale_qty),
                    "မှတ်ချက်": sale_note.strip() if sale_note.strip() else "-",
                    "status": "ACTIVE"
                })
                st.session_state.flash_msg = f"✅ Code '{clean_code}' အရောင်းစာရင်း သိမ်းဆည်းပြီးပါပြီ။"
                st.rerun()

    if st.session_state.sales_list:
        st.markdown("**📋 ယနေ့ ရောင်းထွက် Code စာရင်းများ**")
        st.dataframe(pd.DataFrame(st.session_state.sales_list), use_container_width=True, hide_index=True)
        active_sale_ids = [s["id"] for s in st.session_state.sales_list if s["status"] == "ACTIVE"]
        if active_sale_ids:
            v_s_col1, v_s_col2 = st.columns([2, 1])
            void_sale_id = v_s_col1.selectbox("ပယ်ဖျက်မည့် အရောင်း ID", active_sale_ids, key="void_sale_select")
            if v_s_col2.button("⚠️ အရောင်း Void", key="void_sale_btn"):
                for s in st.session_state.sales_list:
                    if s["id"] == void_sale_id:
                        s["status"] = "VOIDED"
                        s["အရေအတွက်"] = 0
                st.session_state.flash_msg = f"✅ အရောင်း ID #{void_sale_id} ကို Void လုပ်ပြီးပါပြီ။"
                st.rerun()

st.markdown("---")

# ==========================================
# အပိုင်း (၄) ညနေ ဆိုင်ပိတ်ချိန် လက်တွေ့လက်ကျန် စစ်ဆေးခြင်း
# ==========================================
st.subheader("🔍 ၄။ ညနေ ဆိုင်ပိတ်ချိန် လက်တွေ့လက်ကျန် စစ်ဆေးရန် (Closing Count)")

tab_act1, tab_act2, tab_act3 = st.tabs(["💎 စိန် (လက်တွေ့လက်ကျန်)", "🪙 ရွှေ ၁၅/၁၆ ပဲရည် (လက်တွေ့လက်ကျန်)", "⚪ ပလက်တီနမ် (လက်တွေ့လက်ကျန်)"])

with tab_act1:
    sein_mask = st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "စိန်"
    edited_sein_act = st.data_editor(
        st.session_state.opening_stock_df[sein_mask][["ပစ္စည်းအမည်", "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"]],
        column_config=act_col_config, hide_index=True, use_container_width=True, key="editor_act_sein"
    )
    st.session_state.opening_stock_df.loc[sein_mask, "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"] = edited_sein_act["ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values

with tab_act2:
    ga1, ga2 = st.columns(2)
    with ga1:
        st.markdown("**🔸 ၁၅ ပဲရည် လက်တွေ့လက်ကျန်**")
        g15_mask = (st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "ရွှေ") & (st.session_state.opening_stock_df["ခွဲအမျိုးအစား"] == "၁၅ ပဲရည်")
        edited_g15_act = st.data_editor(
            st.session_state.opening_stock_df[g15_mask][["ပစ္စည်းအမည်", "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"]],
            column_config=act_col_config, hide_index=True, use_container_width=True, key="editor_act_g15"
        )
        st.session_state.opening_stock_df.loc[g15_mask, "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"] = edited_g15_act["ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values
    with ga2:
        st.markdown("**🔸 ၁၆ ပဲရည် လက်တွေ့လက်ကျန်**")
        g16_mask = (st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "ရွှေ") & (st.session_state.opening_stock_df["ခွဲအမျိုးအစား"] == "၁၆ ပဲရည်")
        edited_g16_act = st.data_editor(
            st.session_state.opening_stock_df[g16_mask][["ပစ္စည်းအမည်", "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"]],
            column_config=act_col_config, hide_index=True, use_container_width=True, key="editor_act_g16"
        )
        st.session_state.opening_stock_df.loc[g16_mask, "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"] = edited_g16_act["ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values

with tab_act3:
    plat_mask = st.session_state.opening_stock_df["အဓိကအမျိုးအစား"] == "ပလက်တီနမ်"
    edited_plat_act = st.data_editor(
        st.session_state.opening_stock_df[plat_mask][["ပစ္စည်းအမည်", "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"]],
        column_config=act_col_config, hide_index=True, use_container_width=True, key="editor_act_plat"
    )
    st.session_state.opening_stock_df.loc[plat_mask, "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"] = edited_plat_act["ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"].fillna(0).astype(int).values

st.markdown("---")

# ==========================================
# အပိုင်း (၅) Data Processing & Audit Calculation
# ==========================================
st.subheader("📊 ၅။ Data Processing နှင့် လက်ကျန်စာရင်းပေါင်းချုပ်")

audit_df = st.session_state.opening_stock_df.copy()

inflow_totals = []
sales_totals = []
expected_totals = []
diff_totals = []
status_labels = []

for idx, row in audit_df.iterrows():
    m_cat = row["အဓိကအမျိုးအစား"]
    s_cat = row["ခွဲအမျိုးအစား"]
    i_name = row["ပစ္စည်းအမည်"]
    op_q = int(row["မနက်လက်ကျန် (အရေအတွက်)"])
    act_q = int(row["ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)"])
    
    in_q = sum(
        item["အရေအတွက်"] for item in st.session_state.inflow_list
        if item["status"] == "ACTIVE" and item["အဓိကအမျိုးအစား"] == m_cat and item["ခွဲအမျိုးအစား"] == s_cat and item["ပစ္စည်းအမည်"] == i_name
    )
    out_q = sum(
        s["အရေအတွက်"] for s in st.session_state.sales_list
        if s["status"] == "ACTIVE" and s["အဓိကအမျိုးအစား"] == m_cat and s["ခွဲအမျိုးအစား"] == s_cat and s["ပစ္စည်းအမည်"] == i_name
    )
    
    exp_q = op_q + in_q - out_q
    diff_q = act_q - exp_q
    
    if diff_q == 0:
        st_label = "✅ ကိုက်ညီသည် (MATCHED)"
    elif diff_q < 0:
        st_label = f"❌ လိုနေသည် ({diff_q})"
    else:
        st_label = f"⚠️ ပိုနေသည် (+{diff_q})"
        
    inflow_totals.append(in_q)
    sales_totals.append(out_q)
    expected_totals.append(exp_q)
    diff_totals.append(diff_q)
    status_labels.append(st_label)

audit_df["ယနေ့အဝင် (ပန်းထိမ်ဆရာ)"] = inflow_totals
audit_df["ယနေ့ရောင်းထွက်"] = sales_totals
audit_df["ရှိသင့်သောလက်ကျန်"] = expected_totals
audit_df["ကွာဟချက်"] = diff_totals
audit_df["စစ်ဆေးချက်ရလဒ်"] = status_labels

audit_df = audit_df[[
    "အဓိကအမျိုးအစား", "ခွဲအမျိုးအစား", "ပစ္စည်းအမည်",
    "မနက်လက်ကျန် (အရေအတွက်)", "ယနေ့အဝင် (ပန်းထိမ်ဆရာ)", "ယနေ့ရောင်းထွက်",
    "ရှိသင့်သောလက်ကျန်", "ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)", "ကွာဟချက်", "စစ်ဆေးချက်ရလဒ်"
]]

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("☀️ မနက်လက်ကျန်", f"{audit_df['မနက်လက်ကျန် (အရေအတွက်)'].sum()} ခု")
m2.metric("📥 ပန်းထိမ်ဆရာအဝင်", f"{audit_df['ယနေ့အဝင် (ပန်းထိမ်ဆရာ)'].sum()} ခု")
m3.metric("📤 ရောင်းထွက်အား", f"{audit_df['ယနေ့ရောင်းထွက်'].sum()} ခု")
m4.metric("📌 ရှိသင့်လက်ကျန်", f"{audit_df['ရှိသင့်သောလက်ကျန်'].sum()} ခု")
m5.metric("🔍 လက်တွေ့လက်ကျန်", f"{audit_df['ညနေလက်တွေ့လက်ကျန် (အရေအတွက်)'].sum()} ခု")

st.markdown("### 📋 အမျိုးအစားအလိုက် လက်ကျန်စာရင်းပေါင်းချုပ် ဇယား")
st.dataframe(audit_df, use_container_width=True, hide_index=True)

mismatched_df = audit_df[audit_df["ကွာဟချက်"] != 0]
if mismatched_df.empty:
    st.success("✅ **Data Processing Diagnosis:** စာရင်းများအားလုံး ၁၀၀% ကိုက်ညီပါသည်။")
else:
    st.error(f"⚠️ **Data Processing Diagnosis:** စာရင်းမကိုက်ညီသော ပစ္စည်း ({len(mismatched_df)}) ခု တွေ့ရှိရပါသည်။")

st.markdown("---")

# ==========================================
# အပိုင်း (၆) Excel Multi-sheet ဒေါင်းလုဒ်စနစ် & System Log
# ==========================================
st.subheader("💾 ၆။ Excel Multi-sheet အစီရင်ခံစာ ထုတ်ယူရန်")

history_stock_file = "zwe_htet_stock_audit_history.csv"
history_sales_file = "zwe_htet_sales_code_history.csv"
history_artisan_file = "zwe_htet_artisan_inflow_history.csv"

# Excel Multi-sheet ဖိုင်ထုတ်ပေးသည့် Function
def create_excel_report():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Stock Summary
        export_stock = audit_df.copy()
        export_stock.insert(0, "ရက်စွဲ", str(audit_date))
        export_stock.insert(1, "တာဝန်ခံ", shop_owner)
        export_stock.to_excel(writer, sheet_name='Stock_Summary', index=False)
        
        # Sheet 2: Sales Code Report
        if st.session_state.sales_list:
            df_sales_exp = pd.DataFrame(st.session_state.sales_list)
        else:
            df_sales_exp = pd.DataFrame(columns=["id", "ရက်စွဲ", "ဘောက်ချာနံပါတ်", "Code နံပါတ်", "အဓိကအမျိုးအစား", "ခွဲအမျိုးအစား", "ပစ္စည်းအမည်", "အရေအတွက်", "မှတ်ချက်", "status"])
        df_sales_exp.to_excel(writer, sheet_name='Sales_Code_Report', index=False)
        
        # Sheet 3: Artisan Inflow Report
        if st.session_state.inflow_list:
            df_art_exp = pd.DataFrame(st.session_state.inflow_list)
        else:
            df_art_exp = pd.DataFrame(columns=["id", "ရက်စွဲ", "ပရိန်ဆရာအမည်", "Code နံပါတ်", "အဓိကအမျိုးအစား", "ခွဲအမျိုးအစား", "ပစ္စည်းအမည်", "အရေအတွက်", "မှတ်ချက်", "status"])
        df_art_exp.to_excel(writer, sheet_name='Artisan_Inflow', index=False)
        
    processed_data = output.getvalue()
    return processed_data

excel_data = create_excel_report()

col_dl, col_log = st.columns(2)
with col_dl:
    st.download_button(
        label="📥 📊 နေ့စဉ်စာရင်းချုပ် (Excel Multi-sheet) ဒေါင်းလုဒ်ဆွဲရန်",
        data=excel_data,
        file_name=f"Zwe_Htet_Master_Report_{audit_date}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_log:
    if st.button("🚀 ယနေ့စာရင်းများကို Founder System Log သို့ သိမ်းဆည်းမည်", type="primary", use_container_width=True):
        audit_export_df = audit_df.copy()
        audit_export_df.insert(0, "ရက်စွဲ", str(audit_date))
        audit_export_df.insert(1, "တာဝန်ခံဝန်ထမ်း", shop_owner)
        
        if os.path.exists(history_stock_file):
            existing_stock = pd.read_csv(history_stock_file)
            existing_stock = existing_stock[existing_stock["ရက်စွဲ"].astype(str) != str(audit_date)]
            pd.concat([existing_stock, audit_export_df], ignore_index=True).to_csv(history_stock_file, index=False, encoding="utf-8-sig")
        else:
            audit_export_df.to_csv(history_stock_file, index=False, encoding="utf-8-sig")
            
        if st.session_state.sales_list:
            df_s_log = pd.DataFrame(st.session_state.sales_list)
            df_s_log["တာဝန်ခံဝန်ထမ်း"] = shop_owner
            if os.path.exists(history_sales_file):
                existing_sales = pd.read_csv(history_sales_file)
                existing_sales = existing_sales[existing_sales["ရက်စွဲ"].astype(str) != str(audit_date)]
                pd.concat([existing_sales, df_s_log], ignore_index=True).to_csv(history_sales_file, index=False, encoding="utf-8-sig")
            else:
                df_s_log.to_csv(history_sales_file, index=False, encoding="utf-8-sig")
                
        if st.session_state.inflow_list:
            df_a_log = pd.DataFrame(st.session_state.inflow_list)
            df_a_log["တာဝန်ခံဝန်ထမ်း"] = shop_owner
            if os.path.exists(history_artisan_file):
                existing_artisan = pd.read_csv(history_artisan_file)
                existing_artisan = existing_artisan[existing_artisan["ရက်စွဲ"].astype(str) != str(audit_date)]
                pd.concat([existing_artisan, df_a_log], ignore_index=True).to_csv(history_artisan_file, index=False, encoding="utf-8-sig")
            else:
                df_a_log.to_csv(history_artisan_file, index=False, encoding="utf-8-sig")
                
        st.success("✅ System Log သို့ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!")

# ==========================================
# 🔐 FOUNDER / ADMIN SECURED AUDIT TRAIL
# ==========================================
st.markdown("---")
if is_founder:
    st.subheader("🔐 Founder သီးသန့် ဝင်ရောက်စစ်ဆေးသော မှတ်တမ်းချုပ်များ")
    f_tab1, f_tab2, f_tab3 = st.tabs([
        "📊 နေ့စဉ် လက်ကျန်စာရင်းပေါင်းချုပ် မှတ်တမ်း",
        "🏷️ ရောင်းထွက် Code နံပါတ် မှတ်တမ်းချုပ်",
        "👨‍🎨 ပန်းထိမ်ဆရာ ပစ္စည်းအဝင် မှတ်တမ်းချုပ်"
    ])
    
    with f_tab1:
        if os.path.exists(history_stock_file):
            st.dataframe(pd.read_csv(history_stock_file), use_container_width=True, hide_index=True)
        else:
            st.info("မှတ်တမ်း မရှိသေးပါ။")
    with f_tab2:
        if os.path.exists(history_sales_file):
            st.dataframe(pd.read_csv(history_sales_file), use_container_width=True, hide_index=True)
        else:
            st.info("မှတ်တမ်း မရှိသေးပါ။")
    with f_tab3:
        if os.path.exists(history_artisan_file):
            st.dataframe(pd.read_csv(history_artisan_file), use_container_width=True, hide_index=True)
        else:
            st.info("မှတ်တမ်း မရှိသေးပါ။")
            
    if st.button("🗑️ [Founder သီးသန့်] မှတ်တမ်းဟောင်းအားလုံး ရှင်းလင်းမည်"):
        for f_path in [history_stock_file, history_sales_file, history_artisan_file]:
            if os.path.exists(f_path):
                os.remove(f_path)
        st.session_state.flash_msg = "✅ မှတ်တမ်းများ ရှင်းလင်းပြီးပါပြီ။"
        st.rerun()
else:
    st.info("🔒 **Founder မှတ်တမ်းများ ကြည့်ရှုရန် ဘယ်ဘက် Sidebar တွင် Admin Password ရိုက်ထည့်ပါ။**")