import streamlit as st
import google.generativeai as genai

# ==============================================================================
# 1. 網頁基本配置
# ==============================================================================
st.set_page_config(
    page_title="國中生物 AI 智慧教學系統",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 國中生物 AI 智慧教學系統")

# ==============================================================================
# 2. 側邊欄設定：API 金鑰與功能導覽
# ==============================================================================
st.sidebar.title("控制面板")
api_key = st.sidebar.text_input("輸入 Gemini API Key:", type="password")
mode = st.sidebar.radio("功能選擇", ["知識重點整理", "針對重點出題", "錯題盲點分析"])

# API 金鑰驗證與模型初始化
ai_active = False
if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        ai_active = True
        st.sidebar.success("API 連線成功")
    except Exception as e:
        st.sidebar.error(f"API 連線失敗: {str(e)}")
else:
    st.sidebar.warning("請先輸入 API Key 以啟用 AI 分析功能。")

# ==============================================================================
# 3. 功能實作：知識重點整理
# ==============================================================================
if mode == "知識重點整理":
    st.header("📝 知識重點整理系統")
    user_knowledge = st.text_area("請輸入欲整理之生物知識/課文內容：", height=250)
    
    if st.button("執行重點提煉"):
        if not ai_active:
            st.error("系統未啟用：請先提供有效的 API Key。")
        elif not user_knowledge.strip():
            st.warning("輸入欄位不可為空。")
        else:
            with st.spinner("AI 正在提煉重點..."):
                prompt = f"""
                角色：專業國中生物教師
                任務：閱讀下方生物知識內容，並針對臺灣國中會考等級提煉結構化筆記。
                
                輸出規範：
                1. 採用 Markdown 格式排版。
                2. 包含【核心定義】。
                3. 包含【必考核心步驟/觀念對比】。
                4. 包含【會考常見陷阱與常見錯誤觀念釐清】。
                
                輸入內容：
                {user_knowledge}
                """
                try:
                    response = model.generate_content(prompt)
                    st.success("重點提煉完成")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"生成失敗: {str(e)}")

# ==============================================================================
# 4. 功能實作：針對重點出題
# ==============================================================================
elif mode == "針對重點出題":
    st.header("🎯 核心觀念測驗出題系統")
    quiz_topic = st.text_input("請輸入欲測試之生物單元/主題名稱：")
    
    if st.button("生成模擬試題"):
        if not ai_active:
            st.error("系統未啟用：請先提供有效的 API Key。")
        elif not quiz_topic.strip():
            st.warning("輸入欄位不可為空。")
        else:
            with st.spinner("AI 正在生成題目..."):
                prompt = f"""
                角色：專業國中生物教師
                任務：針對「{quiz_topic}」主題，設計符合臺灣國中會考難度與題型趨勢的單選題。
                
                輸出規範：
                1. 總計生成 3 題單選題。
                2. 每題需包含：題目、(A)(B)(C)(D)四個選項、正確答案。
                3. 每題下方需附帶【核心觀念與盲點解析】。
                """
                try:
                    response = model.generate_content(prompt)
                    st.success("試題生成完成")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"生成失敗: {str(e)}")

# ==============================================================================
# 5. 功能實作：錯題盲點分析
# ==============================================================================
elif mode == "錯題盲點分析":
    st.header("📕 錯題診斷與變形題訓練系統")
    
    col1, col2 = st.columns(2)
    with col1:
        wrong_q = st.text_area("請輸入寫錯的題目內容：", height=150)
    with col2:
        user_ans = st.text_input("請輸入你當時選擇的錯誤答案（選填）：")
        correct_ans = st.text_input("請輸入正確官方答案（選填）：")
        
    if st.button("啟動錯題診斷"):
        if not ai_active:
            st.error("系統未啟用：請先提供有效的 API Key。")
        elif not wrong_q.strip():
            st.warning("錯題內容欄位不可為空。")
        else:
            with st.spinner("AI 正在進行錯題診斷..."):
                prompt = f"""
                角色：專業國中生物教師
                任務：分析學生遺漏之核心觀念，並給出修正指導。
                
                輸入資料：
                - 錯題題目：{wrong_q}
                - 學生錯誤答案：{user_ans}
                - 正確答案：{correct_ans}
                
                輸出規範：
                1. 【正確答案與核心邏輯】：解說正確答案之生物學理論。
                2. 【思考盲點分析】：指出此題型之邏輯陷阱，分析學生容易混淆之處。
                3. 【舉一反三變形題】：針對該知識點，即時生成 1 題相似結構之新題，並於下方附上答案與解析。
                """
                try:
                    response = model.generate_content(prompt)
                    st.success("錯題診斷書生成完成")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"生成失敗: {str(e)}")
