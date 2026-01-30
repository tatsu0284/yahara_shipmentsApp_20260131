import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 設定 ---
VEGETABLES = ["トマト", "キュウリ", "ナス", "ピーマン", "レタス", "キャベツ"]
STAFF_MEMBERS = [f"担当者 {i}" for i in range(1, 20)]
WORKSHEET_NAME = "shipments_20260131"
st.set_page_config(page_title="野菜出荷管理", layout="wide")
st.title("🥬 野菜出荷見込み管理")

# --- Google Sheets 接続設定 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# データ読み込み関数
def load_data():
    # ttl=0にすることで、読み込みのたびに最新データを取得（キャッシュしない）
    return conn.read(worksheet=WORKSHEET_NAME, ttl=0)

# サイドバーメニュー
app_mode = st.sidebar.selectbox("メニューを選択", ["【担当者】出荷見込み入力", "【責任者】集計確認"])

# --- 担当者入力画面 ---
if app_mode == "【担当者】出荷見込み入力":
    st.header("📝 出荷見込みの入力")
    
    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            date = st.date_input("出荷予定日", datetime.now())
            staff = st.selectbox("あなたの名前", STAFF_MEMBERS)
        with col2:
            veg = st.selectbox("野菜の種類", VEGETABLES)
            qty = st.number_input("出荷見込み数量", min_value=1, step=1)
        
        submitted = st.form_submit_button("データを送信")
        
        if submitted:
            if qty > 0:
                # 既存データ取得
                existing_data = load_data()
                # 新規データ作成
                new_row = pd.DataFrame([{
                    "日付": str(date),
                    "担当者": staff,
                    "野菜名": veg,
                    "数量": qty,
                    "更新日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }])
                # 結合
                updated_df = pd.concat([existing_data, new_row], ignore_index=True)
                # 書き込み
                conn.update(worksheet=WORKSHEET_NAME, data=updated_df)
                st.success(f"スプレッドシートへ保存完了！")
            else:
                st.error("数量を入力してください。")

# --- 責任者集計画面 ---
else:
    st.header("📊 出荷見込み集計 dashboard")
    df = load_data()
    
    if df.empty or len(df) == 0:
        st.info("データがありません。")
    else:
        target_date = st.date_input("表示する出荷予定日", datetime.now())
        filtered_df = df[df["日付"] == str(target_date)]
        
        if filtered_df.empty:
            st.warning(f"{target_date} のデータはありません。")
        else:
            # 集計
            summary = filtered_df.groupby("野菜名")["数量"].sum().reset_index()
            
            # メトリクス表示
            cols = st.columns(len(summary))
            for i, row in summary.iterrows():
                cols[i].metric(label=row["野菜名"], value=row["数量"])
            
            st.divider()
            c1, c2 = st.columns([1, 1])
            with c1:
                st.bar_chart(data=summary, x="野菜名", y="数量", color="#2ecc71")
            with c2:
                st.dataframe(filtered_df.sort_values("更新日時", ascending=False), use_container_width=True)

# データを手動でリロードするボタン
if st.sidebar.button("データを更新(再読込)"):
    st.rerun()
