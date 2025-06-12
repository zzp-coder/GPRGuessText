# === 完整修复后的 app.py（确保正确标记为 1） ===
import streamlit as st
import streamlit.components.v1 as components
import json
import sqlite3
import uuid
import os
import spacy
from datetime import datetime

# 加载 spaCy 英文模型
nlp = spacy.load("en_core_web_sm")

# 用户名 + 密码配置
with open("users.json") as f:
    USER_CONFIG = json.load(f)

USER_DATA_FILES = {
    "user1": "data/test_1.json",
    "user2": "data/test_2.json",
    "user3": "data/test_3.json",
    "user4": "data/test_4.json"
}

# 初始化数据库
def init_db(user):
    db_path = f"db/{user}.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS labels (
        id TEXT PRIMARY KEY,
        paragraph_id INTEGER,
        sentence_index INTEGER,
        sentence TEXT,
        label INTEGER,
        timestamp TEXT
    )''')
    conn.commit()
    return conn, cur

# 加载数据
def load_paragraphs(user):
    with open(USER_DATA_FILES[user], "r") as f:
        return json.load(f)

# 分句
def split_sentences(text):
    return [s.text.strip() for s in nlp(text).sents]

# 页面初始化
st.set_page_config(page_title="Annotation Platform", layout="centered")
st.title("🧠 GeoGuessText Annotation")

# 登录管理
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username in USER_CONFIG and USER_CONFIG[username] == password:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.current_index = 0
            st.rerun()
        else:
            st.error("❌ Invalid credentials")
    st.stop()

# 登录后内容
username = st.session_state.username
st.success(f"👤 Logged in as: {username}")
paragraphs = load_paragraphs(username)
conn, cursor = init_db(username)

# 进度信息
cursor.execute("SELECT COUNT(DISTINCT paragraph_id) FROM labels WHERE label IN (0,1)")
completed = cursor.fetchone()[0] or 0

st.progress(completed / len(paragraphs))
st.markdown(f"**Progress:** {completed} / {len(paragraphs)} paragraphs")

if completed >= len(paragraphs):
    st.success("🎉 All paragraphs labeled. Thank you!")
    st.stop()

# 当前段落与句子
para = paragraphs[completed]
sentences = split_sentences(para["text"])

st.markdown("## Paragraph:")

# JS + HTML 渲染器（并写入隐藏输入框）
st.text_input("selected_indexes_raw", key="selected_indexes_raw", label_visibility="collapsed")

components.html(
    """
    <script>
      const selected = new Set();
      function toggle(i) {
        const el = document.getElementById('sent_' + i);
        if (selected.has(i)) {
          selected.delete(i);
          el.style.backgroundColor = '';
        } else {
          selected.add(i);
          el.style.backgroundColor = '#ffe599';
        }
        const input = window.parent.document.querySelector('input[data-streamlit-key=\"selected_indexes_raw\"]');
        if (input) {
          input.value = Array.from(selected).join(',');
          input.dispatchEvent(new Event('input', { bubbles: true }));
        }
      }
    </script>
    <div style='line-height:2;'>
    """ +
    "".join([
        f"<span id='sent_{i}' onclick='toggle({i})' style='cursor:pointer; padding:2px;'>{s} </span>"
        for i, s in enumerate(sentences)
    ]) +
    """
    </div>
    """,
    height=min(200 + len(sentences) * 20, 600),
    scrolling=True
)

# 提交按钮
if st.button("✅ Confirm"):
    ts = datetime.now().isoformat()
    raw = st.session_state.get("selected_indexes_raw", "")
    try:
        selected = set(int(i) for i in raw.split(",") if i.strip().isdigit())
    except:
        selected = set()
    for i, sent in enumerate(sentences):
        label = 1 if i in selected else 0
        cursor.execute("INSERT INTO labels (id, paragraph_id, sentence_index, sentence, label, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), para["id"], i, sent, label, ts))
    conn.commit()
    st.rerun()