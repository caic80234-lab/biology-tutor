import streamlit as st
import google.generativeai as genai
import json
import re

# ==============================================================================
# 1. 網頁基本配置與全域樣式優化
# ==============================================================================
st.set_page_config(
    page_title="AI 全方位一體化智慧教學系統",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI 全方位一體化智慧教學系統")
st.caption("智慧辨識系統：直接輸入「單元名稱」或貼上「考題/錯題」，系統將自動識別並啟動一體化學習或錯題診斷。")

# ==============================================================================
# 2. 雲端金鑰安全讀取（使用者端不可見）
# ==============================================================================
ai_active = False

if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
        ai_active = True
    except Exception as e:
        st.error(f"系統核心連線異常: {str(e)}")
else:
    st.error("系統未配置核心金鑰，請管理員於 Streamlit 後台設定 Secrets。")

# ==============================================================================
# 3. 教學環境動態設定
# ==============================================================================
st.markdown("### ⚙️ 教學環境設定")
col_subject, col_level = st.columns(2)

with col_subject:
    subject = st.selectbox(
        "選擇學習科目：",
        ["生物", "理化/自然", "數學", "英文", "歷史", "地理", "公民", "地科", "其他（請於下方說明）"]
    )

with col_level:
    level = st.selectbox(
        "選擇學生年級/程度：",
        ["國小高年級", "國中七年級", "國中八年級", "國中九年級（會考衝刺）", "高中職", "大學/成人教育"]
    )

st.write("---")

# ==============================================================================
# 4. 核心智慧辨識與自動串聯邏輯
# ==============================================================================
st.header("🚀 輸入學習內容（單元或錯題皆可）")
user_input = st.text_area(
    "請在此輸入你想學的單元（例：優養化），或直接貼上你想解析的錯題（例：下列何者為非...）：", 
    height=150, 
    placeholder="直接打字或貼上內容即可，系統會自動判斷..."
)

# 初始化 session state 記憶體
if "workflow_type" not in st.session_state:
    st.session_state.workflow_type = None  # 'topic' 或 'wrong_question'
if "data_note" not in st.session_state:
    st.session_state.data_note = None
if "data_quiz" not in st.session_state:
    st.session_state.data_quiz = None
if "data_analysis" not in st.session_state:
    st.session_state.data_analysis = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if st.button("✨ 啟動 AI 智慧教學"):
    if not ai_active:
        st.error("系統未啟用：雲端金鑰配置失效。")
    elif not user_input.strip():
        st.warning("請先輸入內容！")
    else:
        # 重置作答狀態
        st.session_state.quiz_submitted = False
        
        with st.spinner("AI 智慧家教正在分析輸入內容..."):
            # 任務 0：讓 AI 判斷使用者輸入的是「單元名稱」還是「一題特定的題目」
            intent_prompt = f"""
            你是一位專業的【{subject}】老師。請分析以下使用者的輸入內容，並判斷它是：
            1. 一個宏觀的【單元名稱/主題/觀念】(例如: 優養化、一元二次方程式、現在完成式)
            2. 一題具體的【考題/錯題/練習題】(例如題目包含選擇題選項、問答題問句、特定考題描述)
            
            請嚴格只回應 "TOPIC" 或 "QUESTION" 這兩個英文單字之一，不要有任何其他字。
            使用者輸入內容：
            {user_input}
            """
            try:
                intent_res = model.generate_content(intent_prompt).text.strip()
                
                # ------ 情況 A：使用者輸入的是一個想學的【單元名稱】 ------
                if "TOPIC" in intent_res:
                    st.session_state.workflow_type = "topic"
                    
                    # 同時生成重點筆記與連動考題
                    p_note = f"針對【{level}】學生的認知，為「{user_input}」這個【{subject}】單元提煉結構化筆記。包含核心定義、對比表格與常錯陷阱。內容限於學術範疇。"
                    p_quiz = f"""針對「{user_input}」這個【{subject}】單元，為【{level}】學生設計1題高質量單選題。內容限於學術範疇。必須嚴格以 JSON 格式輸出：
                    {{"question": "題目？", "options": ["A. xx", "B. xx", "C. xx", "D. xx"], "correct": "A", "analysis": "盲點解析"}}"""
                    
                    st.session_state.data_note = model.generate_content(p_note).text
                    clean_text = re.sub(r"```json\s*|```", "", model.generate_content(p_quiz).text).strip()
                    st.session_state.data_quiz = json.loads(clean_text)
                
                # ------ 情況 B：使用者直接貼上了一題【寫錯的題目】 ------
                else:
                    st.session_state.workflow_type = "wrong_question"
                    
                    # 進行錯題診斷與現場出一題概念相似的全新變形題
                    p_analysis = f"""
                    學生在學校寫錯了這道【{subject}】題目，程度為【{level}】。
                    題目內容：{user_input}
                    請直接進行以下診斷與教學，限制在學術範疇：
                    1. 【正確答案與核心邏輯】：用該年級學生聽得懂的話，解說正確答案的理論與推導邏輯。
                    2. 【思考盲點分析】：指出此題型設計的邏輯陷阱，分析為什麼學生容易在這邊卡住或選錯。
                    """
                    p_quiz_variant = f"""針對使用者貼上的題目（{user_input}）背後的核心觀念，為【{level}】學生設計1題全新的「舉一反三延伸變形題」。必須嚴格以 JSON 格式輸出：
                    {{"question": "新題目？", "options": ["A. xx", "B. xx", "C. xx", "D. xx"], "correct": "A", "analysis": "新題盲點解析"}}"""
                    
                    st.session_state.data_analysis = model.generate_content(p_analysis).text
                    clean_text = re.sub(r"```json\s*|```", "", model.generate_content(p_quiz_variant).text).strip()
                    st.session_state.data_quiz = json.loads(clean_text)
                    
            except Exception as e:
                st.error("系統辨識或生成失敗，請確保輸入的是明確的學習內容並重試。")
                st.session_state.workflow_type = None

# ==============================================================================
# 5. 動態渲染對應的一體化學習畫面
# ==============================================================================
# --- 流程 A 畫面：單元一條龍（筆記 -> 隨堂考 -> 作答診斷） ---
if st.session_state.workflow_type == "topic":
    st.success("📝 AI 自動識別：啟動【單元一體化學習】")
    st.markdown("### 📌 核心觀念精華筆記")
    st.markdown(st.session_state.data_note)
    st.write("---")
    
    st.info("🎯 隨堂即時互動測驗")
    quiz = st.session_state.data_quiz
    st.markdown(f"##### ❓ 題目：{quiz['question']}")
    user_choice = st.radio("請點選選項進行作答：", quiz['options'], index=None, key="topic_radio")
    
    if st.button("確認提交答案並分析盲點"):
        if user_choice is None:
            st.warning("請先點選一個選項再提交！")
        else:
            st.session_state.quiz_submitted = True
            
    if st.session_state.quiz_submitted and user_choice:
        st.write("---")
        selected_letter = user_choice.split(".")[0].strip()
        if selected_letter == quiz['correct']:
            st.balloons()
            st.success(f"🎉 答對了！正確答案是 ({quiz['correct']})")
        else:
            st.error(f"❌ 答錯囉！你選擇了 {selected_letter}，正確答案是 ({quiz['correct']})")
        st.markdown(f"💡 **思考盲點深度解析：**\n{quiz['analysis']}")

# --- 流程 B 畫面：錯題一條龍（錯題診斷 -> 概念強化變形題 -> 線上點選重新挑戰） ---
elif st.session_state.workflow_type == "wrong_question":
    st.warning("📕 AI 自動識別：啟動【學校錯題診斷與延伸訓練】")
    st.markdown(st.session_state.data_analysis)
    st.write("---")
    
    st.info("🔄 舉一反三：概念強化挑戰題（請重新挑戰相似題）")
    quiz = st.session_state.data_quiz
    st.markdown(f"##### ❓ 題目：{quiz['question']}")
    user_choice = st.radio("請點選選項進行作答：", quiz['options'], index=None, key="wrong_radio")
    
    if st.button("確認提交新答案"):
        if user_choice is None:
            st.warning("請先點選一個選項再提交！")
        else:
            st.session_state.quiz_submitted = True
            
    if st.session_state.quiz_submitted and user_choice:
        st.write("---")
        selected_letter = user_choice.split(".")[0].strip()
        if selected_letter == quiz['correct']:
            st.balloons()
            st.success(f"🎉 成功克服弱點！這次答對了！正確答案是 ({quiz['correct']})")
        else:
            st.error(f"❌ 還是答錯囉，代表觀念尚未完全釐清。正確答案是 ({quiz['correct']})")
        st.markdown(f"💡 **新題深度解析：**\n{quiz['analysis']}")      
