import streamlit as st
import pandas as pd
from datetime import date
import os
import google.generativeai as genai
from PIL import Image
import json

# စာမျက်နှာ အကျယ်ချဲ့ခြင်း
st.set_page_config(page_title="ဇွဲထက် ရွှေဆိုင် AI OCR စာရင်းစစ်စနစ် (V6)", layout="wide")

# မြန်မာ့ရွှေချိန် (ရွဲ) ပြောင်းလဲတွက်ချက်မှု ဖန်ရှင်များ
def to_rupe(kyat, pae, yway):
    return (int(kyat) * 128) + (int(pae) * 8) + int(yway)

def from_rupe(total_yway):
    kyat = int(total_yway) // 128
    remainder = int(total_yway) % 128
    pae = remainder // 8
    yway = remainder % 8
    return kyat, pae, yway

def format_weight(kyat, pae, yway):
    return f"{kyat} ကျပ် ၊ {pae} ပဲ ၊ {yway} ရွဲ"

# Session State ဖြင့် မှတ်သားခြင်း
if "sales_list" not in st.session_state:
    st.session_state.sales_list = []

if "inflow_list" not in st.session_state:
    st.session_state.inflow_list = []

# ခေါင်းစဉ်နှင့် ရက်စွဲ
col_title, col_date = st.columns([3, 1])
with col_title:
    st.title("🪙 ဇွဲထက် ရွှေဆိုင် - AI Receipt OCR စာရင်းစစ်စနစ် (V6)")
    st.write("ဘောက်ချာ ဓာတ်ပုံ တင်လိုက်ရုံဖြင့် AI ဖြင့် အလိုအလျောက် အလေးချိန် ဖတ်ယူမည့်စနစ်")
with col_date:
    audit_date = st.date_input("📅 စာရင်းစစ်သည့် ရက်စွဲ", date.today())

st.markdown("---")

# API Key ထည့်ရန် Sidebar
with st.sidebar:
    st.subheader("⚙️ AI ဆက်တင်များ (Settings)")
    api_key_input = st.text_input("Gemini API Key ထည့်ရန်", type="password")
    if api_key_input:
        genai.configure(api_key=api_key_input)
        st.success("API Key ချိတ်ဆက်ပြီးပါပြီ!")
    st.markdown("---")
    st.markdown("💡 **AI OCR အသုံးပြုပုံ:**\nအရောင်းဘောက်ချာ ဓာတ်ပုံ (JPG/PNG) ကို Upload တင်ပြီး 'AI ဖြင့် ဘောက်ချာဖတ်မည်' ကို နှိပ်ပါ။ AI က ကျပ်၊ ပဲ၊ ရွဲ နှင့် အထည်အမျိုးအစားကို အလိုအလျောက် ဖြည့်ပေးပါမည်။")

# --- အပိုင်း (၁) မနက်ခင်း ဖွင့်ပွဲလက်ကျန် ---
st.subheader("☀️ ၁။ မနက်ခင်း ဖွင့်ပွဲလက်ကျန် (Opening Stock)")
op_col1, op_col2, op_col3, op_col4 = st.columns(4)
with op_col1:
    op_k = st.number_input("ကျပ်သား (မနက်)", min_value=0, value=10, key="op_k")
with op_col2:
    op_p = st.number_input("ပဲ (မနက်)", min_value=0, max_value=15, value=5, key="op_p")
with op_col3:
    op_y = st.number_input("ရွဲ (မနက်)", min_value=0, max_value=7, value=4, key="op_y")
with op_col4:
    op_items = st.number_input("အထည် အရေအတွက် (မနက်)", min_value=0, value=25, key="op_items")

st.markdown("---")

# --- အပိုင်း (၂) အဝင် / အရောင်းဘောက်ချာ ---
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("📥 ၂။ ပစ္စည်းအသစ် အဝင်ထည့်ရန် (Inflow)")
    with st.form("inflow_form", clear_on_submit=True):
        in_name = st.text_input("ပစ္စည်း အမျိုးအစား / မှတ်ချက်")
        ic1, ic2 = st.columns(2)
        in_qty = ic1.number_input("အထည် အရေအတွက်", min_value=1, value=1)

        c1, c2, c3 = st.columns(3)
        in_k = c1.number_input("ကျပ်သား", min_value=0, value=0)
        in_p = c2.number_input("ပဲ", min_value=0, max_value=15, value=0)
        in_y = c3.number_input("ရွဲ", min_value=0, max_value=7, value=0)
        submit_in = st.form_submit_button("➕ အဝင်စာရင်း ထည့်မည်")

        if submit_in:
            if in_k == 0 and in_p == 0 and in_y == 0:
                st.warning("အလေးချိန် ထည့်သွင်းပေးပါ!")
            else:
                st.session_state.inflow_list.append({
                    "ရက်စွဲ": str(audit_date),
                    "အမျိုးအစား": "အဝင် (Inflow)",
                    "ဘောက်ချာ/မှတ်ချက်": in_name if in_name else "ပစ္စည်းအသစ်",
                    "အရေအတွက်": in_qty,
                    "ကျပ်သား": in_k, "ပဲ": in_p, "ရွဲ": in_y,
                    "total_r": to_rupe(in_k, in_p, in_y)
                })

    if st.session_state.inflow_list:
        df_in = pd.DataFrame(st.session_state.inflow_list).drop(columns=["total_r"])
        st.dataframe(df_in, use_container_width=True)
        if st.button("🗑️ အဝင်စာရင်း ဖျက်မည်"):
            st.session_state.inflow_list = []
            st.rerun()
    else:
        st.caption("အဝင်စာရင်း မရှိသေးပါ။")

with col_out:
    st.subheader("📤 ၃။ အရောင်းဘောက်ချာ ထည့်ရန် (AI OCR & Manual)")

    st.markdown("📸 **AI ဖြင့် ဘောက်ချာပုံဖတ်ရန် (OCR):**")
    uploaded_file = st.file_uploader("ဘောက်ချာ ဓာတ်ပုံ တင်ပါ (JPG, PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="တင်ထားသော ဘောက်ချာပုံ", width=250)

        if st.button("🤖 AI ဖြင့် ဘောက်ချာဖတ်မည် (Extract Receipt)"):
            if not api_key_input:
                st.error("ကျေးဇူးပြု၍ ဘယ်ဘက် Sidebar တွင် Gemini API Key ထည့်သွင်းပေးပါ!")
            else:
                with st.spinner("AI မှ ဘောက်ချာကို ဖတ်နေပါပြီ..."):
                    try:
                        genai.configure(api_key=api_key_input)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        prompt = """
                        You are an AI receipt reader for a Myanmar gold shop. Extract the following information from the receipt image:
                        - voucher_number (string, e.g. V-001)
                        - item_type (string: လက်စွပ်, ဆွဲကြိုး, လက်ကောက်, နားကပ်, ဆွဲသီး, or အခြား)
                        - quantity (integer, number of items)
                        - kyat (integer, gold kyat weight)
                        - pae (integer, gold pae weight)
                        - yway (integer, gold yway weight)

                        Return ONLY a valid JSON object with these keys: voucher_number, item_type, quantity, kyat, pae, yway. No markdown formatting.
                        """
                        response = model.generate_content([image, prompt])
                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)

                        st.session_state.ai_extracted = data
                        st.success("✅ ဘောက်ချာကို အောင်မြင်စွာ ဖတ်ပြီးပါပြီ!")
                    except Exception as e:
                        st.error(f"AI ဖတ်ရှုရာတွင် အမှားရှိသည်: {e}")

    extracted = st.session_state.get("ai_extracted", {"voucher_number": "V-001", "item_type": "လက်စွပ်", "quantity": 1, "kyat": 0, "pae": 0, "yway": 0})

    with st.form("sales_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        v_no = f1.text_input("ဘောက်ချာ နံပါတ်", value=extracted.get("voucher_number", "V-001"))
        item_type = f2.selectbox("ရွှေထည် အမျိုးအစား", ["လက်စွပ်", "ဆွဲကြိုး", "လက်ကောက်", "နားကပ်", "ဆွဲသီး", "အခြား"],
                                 index=["လက်စွပ်", "ဆွဲကြိုး", "လက်ကောက်", "နားကပ်", "ဆွဲသီး", "အခြား"].index(extracted.get("item_type", "လက်စွပ်")) if extracted.get("item_type") in ["လက်စွပ်", "ဆွဲကြိုး", "လက်ကောက်", "နားကပ်", "ဆွဲသီး", "အခြား"] else 0)

        sc1, sc2, sc3 = st.columns(3)
        sale_qty = sc1.number_input("အထည် အရေအတွက်", min_value=1, value=int(extracted.get("quantity", 1)))
        s_k = sc2.number_input("ကျပ်သား", min_value=0, value=int(extracted.get("kyat", 0)))
        s_p = sc3.number_input("ပဲ", min_value=0, max_value=15, value=int(extracted.get("pae", 0)))
        s_y = sc3.number_input("ရွဲ", min_value=0, max_value=7, value=int(extracted.get("yway", 0)))

        submit_sale = st.form_submit_button("➕ အရောင်းဘောက်ချာ ထည့်မည်")

        if submit_sale:
            if s_k == 0 and s_p == 0 and s_y == 0:
                st.warning("ရောင်းထွက် အလေးချိန် ထည့်သွင်းပေးပါ!")
            else:
                st.session_state.sales_list.append({
                    "ရက်စွဲ": str(audit_date),
                    "အမျိုးအစား": f"အရောင်း ({item_type})",
                    "ဘောက်ချာ/မှတ်ချက်": v_no,
                    "အရေအတွက်": sale_qty,
                    "ကျပ်သား": s_k, "ပဲ": s_p, "ရွဲ": s_y,
                    "total_r": to_rupe(s_k, s_p, s_y)
                })
                if "ai_extracted" in st.session_state:
                    del st.session_state["ai_extracted"]
                st.rerun()

    if st.session_state.sales_list:
        df_sales = pd.DataFrame(st.session_state.sales_list).drop(columns=["total_r"])
        st.dataframe(df_sales, use_container_width=True)
        if st.button("🗑️ အရောင်းစာရင်း ဖျက်မည်"):
            st.session_state.sales_list = []
            st.rerun()
    else:
        st.caption("အရောင်းဘောက်ချာ မရှိသေးပါ။")

# စုစုပေါင်း တွက်ချက်ခြင်း
total_in_r = sum(item["total_r"] for item in st.session_state.inflow_list)
total_sold_r = sum(item["total_r"] for item in st.session_state.sales_list)
total_in_qty = sum(item["အရေအတွက်"] for item in st.session_state.inflow_list)
total_sold_qty = sum(item["အရေအတွက်"] for item in st.session_state.sales_list)

in_tot_k, in_tot_p, in_tot_y = from_rupe(total_in_r)
sold_tot_k, sold_tot_p, sold_tot_y = from_rupe(total_sold_r)

st.info(f"📊 **စုစုပေါင်း အဝင်:** {format_weight(in_tot_k, in_tot_p, in_tot_y)} ({total_in_qty} ထည်)  |  **စုစုပေါင်း ရောင်းထွက်:** {format_weight(sold_tot_k, sold_tot_p, sold_tot_y)} ({total_sold_qty} ထည်)")

st.markdown("---")

# --- အပိုင်း (၄) ညနေ ဆိုင်ပိတ်ချိန် စစ်ဆေးခြင်း ---
st.subheader("🔍 ၄။ ညနေ ဆိုင်ပိတ်ချိန် လက်တွေ့စစ်ဆေးချက် (Actual Count)")
act_col1, act_col2, act_col3, act_col4 = st.columns(4)
with act_col1:
    act_k = st.number_input("ကျပ်သား (လက်တွေ့)", min_value=0, value=10, key="act_k")
with act_col2:
    act_p = st.number_input("ပဲ (လက်တွေ့)", min_value=0, max_value=15, value=0, key="act_p")
with act_col3:
    act_y = st.number_input("ရွဲ (လက်တွေ့)", min_value=0, max_value=7, value=0, key="act_y")
with act_col4:
    act_items = st.number_input("လက်တွေ့ အထည်အရေအတွက်", min_value=0, value=25, key="act_items")

op_r = to_rupe(op_k, op_p, op_y)
act_r = to_rupe(act_k, act_p, act_y)
expected_r = op_r + total_in_r - total_sold_r
diff_r = act_r - expected_r

expected_items = op_items + total_in_qty - total_sold_qty
diff_items = act_items - expected_items

exp_k, exp_p, exp_y = from_rupe(expected_r)
d_k, d_p, d_y = from_rupe(abs(diff_r))

st.markdown("---")
st.subheader("🤖 AI စာရင်းစစ် အမှားရှာဖွေရေး အစီရင်ခံစာ (AI Error Diagnosis Report)")

st.write(f"📌 **ရှိသင့်သော လက်ကျန်:** `{format_weight(exp_k, exp_p, exp_y)}` ({expected_items} ထည်)")
st.write(f"📌 **လက်တွေ့ ရှိသော လက်ကျန်:** `{format_weight(act_k, act_p, act_y)}` ({act_items} ထည်)")

if diff_r == 0 and diff_items == 0:
    st.success("✅ စာရင်းများ အပြည့်အစုံ ကိုက်ညီပါသည်။ မည်သည့် အမှားအယွင်းမှ မရှိပါ။")
else:
    st.error("⚠️ **AI တွေ့ရှိချက် - စာရင်း မကိုက်ညီပါ! အောက်ပါ အကြောင်းရင်းများကို စစ်ဆေးပါ:**")
    if diff_r < 0:
        st.markdown(f"* ❌ **အလေးချိန် လိုနေသည် (Shortage):** `{format_weight(d_k, d_p, d_y)}`")
    elif diff_r > 0:
        st.markdown(f"* ⚠️ **အလေးချိန် ပိုနေသည် (Excess):** `{format_weight(d_k, d_p, d_y)}`")

    if diff_items != 0:
        st.markdown(f"* 📦 **အထည်အရေအတွက် ကွာခြားချက်:** `{abs(diff_items)} ထည်` {'လျော့နည်းနေသည်' if diff_items < 0 else 'ပိုနေသည်'}")

    st.markdown("---")
    st.markdown("#### 💡 AI ၏ တိုက်ရိုက် ညွှန်ပြချက်နှင့် အကြံပြုချက်များ:")

    found_cause = False
    for v in st.session_state.sales_list:
        if v["total_r"] == abs(diff_r):
            found_cause = True
            if diff_r > 0:
                st.warning(f"👉 အရောင်းဘောက်ချာ **{v['ဘောက်ချာ/မှတ်ချက်']} ({v['အမျိုးအစား']})** ၏ အလေးချိန်သည် ပိုနေသော အလေးချိန်နှင့် တိတိကျကျ တူညီနေပါသည်။ နှစ်ခါရိုက်မိခြင်း ရှိမရှိ စစ်ဆေးပါ။")
            else:
                st.warning(f"👉 အရောင်းဘောက်ချာ **{v['ဘောက်ချာ/မှတ်ချက်']} ({v['အမျိုးအစား']})** ကို စာရင်းသွင်းရန် မေ့ကျန်ခဲ့ခြင်း ဖြစ်နိုင်ပါသည်။")

    if not found_cause:
        st.info("ℹ️ သီးသန့် ဘောက်ချာတစ်ခုချင်းစီနှင့် အတိအကျ မကိုက်ညီပါ။ အလေးချိန်နှင့် အထည်ရေ တိုက်ဆိုင်မှုကို ထပ်မံစစ်ဆေးပါ။")

st.markdown("---")

# --- အပိုင်း (၅) Excel ထုတ်ယူခြင်းနှင့် မှတ်တမ်းသိမ်းဆည်းခြင်း ---
st.subheader("💾 ၅။ စာရင်းချုပ် Excel (CSV) ထုတ်ယူရန်နှင့် သိမ်းဆည်းရန်")

summary_data = {
    "ရက်စွဲ": [str(audit_date)],
    "မနက်လက်ကျန်": [format_weight(op_k, op_p, op_y)],
    "မနက်အထည်ရေ": [op_items],
    "စုစုပေါင်းအဝင်": [format_weight(in_tot_k, in_tot_p, in_tot_y)],
    "အဝင်အထည်ရေ": [total_in_qty],
    "စုစုပေါင်းရောင်းထွက်": [format_weight(sold_tot_k, sold_tot_p, sold_tot_y)],
    "ရောင်းထွက်အထည်ရေ": [total_sold_qty],
    "ရှိသင့်သောလက်ကျန်": [format_weight(exp_k, exp_p, exp_y)],
    "ရှိသင့်သောအထည်ရေ": [expected_items],
    "လက်တွေ့လက်ကျန်": [format_weight(act_k, act_p, act_y)],
    "လက်တွေ့အထည်ရေ": [act_items],
    "စစ်ဆေးချက်ရလဒ်": ["MATCHED" if (diff_r == 0 and diff_items == 0) else "MISMATCH"]
}
df_summary = pd.DataFrame(summary_data)
csv_summary = df_summary.to_csv(index=False).encode('utf-8-sig')

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    st.download_button(
        label="📥 နေ့စဉ်စာရင်းချုပ် (Excel/CSV) ဒေါင်းလုဒ်ဆွဲရန်",
        data=csv_summary,
        file_name=f"Zwe_Htet_Summary_V6_{audit_date}.csv",
        mime="text/csv",
    )

with btn_col2:
    history_file = "zwe_htet_audit_history_v6.csv"
    if st.button("💾 မှတ်တမ်းသိမ်းမည် (Save to History)", type="primary"):
        if os.path.exists(history_file):
            df_existing = pd.read_csv(history_file)
            df_combined = pd.concat([df_existing, df_summary], ignore_index=True)
            df_combined.to_csv(history_file, index=False, encoding='utf-8-sig')
        else:
            df_summary.to_csv(history_file, index=False, encoding='utf-8-sig')
        st.success("✅ AI OCR စာရင်းချုပ်ကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!")

if os.path.exists(history_file):
    st.markdown("---")
    st.subheader("📚 သိမ်းဆည်းထားသော AI OCR မှတ်တမ်းများ")
    df_hist = pd.read_csv(history_file)
    st.dataframe(df_hist, use_container_width=True)
