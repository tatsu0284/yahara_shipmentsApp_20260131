import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 設定 & データ準備 ---
DB_FILE = "shipments.csv"
VEGETABLES = ["トマト", "キュウリ", "ナス", "ピーマン", "レタス", "キャベツ"]
STAFF_MEMBERS = [f"担当者 {i}" for i in range(1, 16)]

# データファイルが存在しない場合に初期化
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["日付", "担当者", "野菜名", "数量(kg)", "更新日時"])
    df.to_csv(DB_FILE, index=False)

def load_data():
    return pd.read_csv(DB_FILE)

def save_data(date, staff, veg, qty):
    df = load_data()
    new_data = {
        "日付": date,
        "担当者": staff,
        "野菜名": veg,
        "数量(kg)": qty,
        "更新日時": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)

# --- UI 構成 ---
st.set_page_config(page_title="野菜出荷見込み管理", layout="wide")
st.title("🥬 野菜出荷見込み管理システム")

# サイドバーでモード切り替え
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
            qty = st.number_input("出荷見込み数量 (kg)", min_value=0.0, step=0.1)
        
        submitted = st.form_submit_button("データを送信")
        
        if submitted:
            if qty > 0:
                save_data(date, staff, veg, qty)
                st.success(f"{staff}さん、{veg}のデータを保存しました！")
            else:
                st.error("数量を入力してください。")

# --- 責任者集計画面 ---
else:
    st.header("📊 出荷見込み集計 dashboard")
    df = load_data()
    
    if df.empty:
        st.info("まだデータが登録されていません。")
    else:
        # フィルタリング
        st.subheader("フィルタ")
        target_date = st.date_input("表示する出荷予定日", datetime.now())
        
        # フィルタ後のデータ
        filtered_df = df[df["日付"] == str(target_date)]
        
        if filtered_df.empty:
            st.warning("選択された日付のデータはありません。")
        else:
            # 合計値の算出
            summary = filtered_df.groupby("野菜名")["数量(kg)"].sum().reset_index()
            
            # メトリクス表示
            cols = st.columns(len(summary))
            for i, row in summary.iterrows():
                cols[i].metric(label=row["野菜名"], value=f"{row['数量(kg)']} kg")
            
            # グラフと表
            st.divider()
            c1, c2 = st.columns([1, 1])
            with c1:
                st.subheader("野菜別合計グラフ")
                st.bar_chart(data=summary, x="野菜名", y="数量(kg)", color="#2ecc71")
            with c2:
                st.subheader("入力詳細一覧")
                st.dataframe(filtered_df.sort_values("更新日時", ascending=False), use_container_width=True)

        