import streamlit as st
import os, json
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════
# PUT YOUR GROQ KEY HERE
GROQ_KEY= st.secrets["GROQ_API_KEY"]

# ═══════════════════════════════════════

client = Groq(api_key=GROQ_KEY)
MODEL  = "llama-3.3-70b-versatile"

os.makedirs("data", exist_ok=True)
PERF_FILE   = "data/performance.json"
MEMORY_FILE = "data/memory.json"

st.set_page_config(
    page_title="🐱 CAT Study Agent",
    page_icon="🐱",
    layout="wide"
)

st.markdown("""
<style>
body { background:#0a0a0f; color:#e2e8f0; }
.stApp { background:#0a0a0f; }
[data-testid="stSidebar"] { background:#0d1117; }
.stButton>button {
    background:linear-gradient(90deg,#00d4ff,#7b2ff7);
    color:white; border:none; border-radius:8px;
    font-weight:bold; width:100%;
}
.stTextInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div {
    background:#21262d;
    color:#e2e8f0;
    border:1px solid #30363d;
}
#MainMenu {visibility:hidden;}
footer    {visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {
        "name":"", "exam":"CAT",
        "weak_topics":[], "strong_topics":[],
        "study_hours":4, "months_left":6,
        "total_sessions":0, "target_college":""
    }

def save_memory(d):
    with open(MEMORY_FILE,"w") as f:
        json.dump(d, f, indent=2)

def load_perf():
    if os.path.exists(PERF_FILE):
        with open(PERF_FILE) as f:
            return json.load(f)
    return {"quizzes":[], "mock_tests":[], "sessions":[]}

def save_perf(d):
    with open(PERF_FILE,"w") as f:
        json.dump(d, f, indent=2)

def ask_ai(prompt, system="You are CatBot, expert MBA coach for Indian students. Be concise and helpful."):
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role":"system","content":system},
                {"role":"user",  "content":prompt}
            ],
            max_tokens=2048,
            temperature=0.7
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ── Load data ──────────────────────────────────────────────
mem  = load_memory()
perf = load_perf()

# ── Sidebar ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🐱 CAT Study Agent")
    st.markdown("---")

    if mem["name"]:
        st.success(f"👋 {mem['name']} | {mem['exam']}")
    else:
        name = st.text_input("Your name:")
        exam = st.selectbox("Target exam:", ["CAT","XAT","GMAT","SNAP"])
        if st.button("Save Profile"):
            mem["name"] = name
            mem["exam"] = exam
            mem["total_sessions"] += 1
            save_memory(mem)
            st.rerun()

    st.markdown("---")

    page = st.radio("", [
        "🏠 Home",
        "📅 Study Schedule",
        "📄 Summarize",
        "🧠 Quiz Me",
        "📚 Notes Q&A",
        "💡 Explain Topic",
        "🔍 Web Search",
        "💬 Chat",
        "📊 Dashboard",
        "📝 Mock Test",
        "🏫 College Shortlist"
    ], label_visibility="collapsed")

    st.markdown("---")
    quizzes = perf.get("quizzes",[])
    st.markdown(f"**Sessions:** {mem.get('total_sessions',0)}")
    st.markdown(f"**Quizzes:** {len(quizzes)}")
    if mem.get("weak_topics"):
        st.markdown("**⚠️ Weak:**")
        for t in mem["weak_topics"][:3]:
            st.markdown(f"• {t}")

# ═══════════════════════════════════════════════════════════
# PAGES
# ═══════════════════════════════════════════════════════════

# ── HOME ───────────────────────────────────────────────────
if page == "🏠 Home":
    st.markdown("# 🐱 CAT Study Agent")
    st.markdown("### Your Personal MBA AI Coach — 100% Free")
    st.markdown("---")

    quizzes = perf.get("quizzes",[])
    mocks   = perf.get("mock_tests",[])
    avg     = round(sum(q["pct"] for q in quizzes)/len(quizzes),1) if quizzes else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("📅 Sessions",   mem.get("total_sessions",0))
    c2.metric("🧠 Quizzes",    len(quizzes))
    c3.metric("📝 Mock Tests", len(mocks))
    c4.metric("⭐ Avg Score",  f"{avg}%")

    st.markdown("---")
    st.progress(min(avg/100, 1.0))
    if avg < 40:   st.warning("🔴 Keep studying!")
    elif avg < 70: st.info("🟡 Good progress!")
    else:          st.success("🟢 Excellent work!")

    if mem.get("weak_topics"):
        st.markdown("### ⚠️ Focus on these weak topics:")
        for t in mem["weak_topics"]:
            st.error(f"🔴 {t}")

    if mem.get("strong_topics"):
        st.markdown("### ✅ Strong topics:")
        for t in mem["strong_topics"]:
            st.success(f"🟢 {t}")

# ── STUDY SCHEDULE ─────────────────────────────────────────
elif page == "📅 Study Schedule":
    st.markdown("# 📅 Study Schedule")
    c1,c2,c3 = st.columns(3)
    with c1: exam   = st.selectbox("Exam:",["CAT","XAT","GMAT","SNAP"])
    with c2: months = st.slider("Months left:",1,24,int(mem.get("months_left",6)))
    with c3: hours  = st.slider("Hours/day:",1,12,int(mem.get("study_hours",4)))

    weak   = st.text_input("Weak areas:", value=", ".join(mem.get("weak_topics",[])))
    target = st.text_input("Target:", placeholder="e.g. 99 percentile")

    if st.button("📅 Generate Plan"):
        with st.spinner("🐱 Creating your plan..."):
            r = ask_ai(f"""Make a {months}-month study plan for {exam}.
Daily: {hours} hrs. Weak: {weak}. Target: {target}.
Include: month-wise topics, daily split, mock schedule, revision strategy.""")
        st.markdown("---")
        st.markdown(r)

# ── SUMMARIZE ──────────────────────────────────────────────
elif page == "📄 Summarize":
    st.markdown("# 📄 Summarize Material")
    tab1, tab2 = st.tabs(["📝 Paste Text","📄 Upload PDF"])

    with tab1:
        text   = st.text_area("Paste text:", height=200)
        length = st.select_slider("Length:",["Short","Medium","Detailed"],"Medium")
        if st.button("✨ Summarize"):
            if text.strip():
                with st.spinner("🐱 Summarizing..."):
                    r = ask_ai(f"Summarize ({length}). Key concepts, formulas, tips:\n\n{text[:4000]}")
                st.markdown("---")
                st.markdown(r)
            else:
                st.warning("Please paste some text!")

    with tab2:
        pdf = st.file_uploader("Upload PDF:", type=["pdf"])
        if pdf:
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(pdf.read()))
            text   = "".join(p.extract_text() or "" for p in reader.pages)
            st.success(f"✅ {len(reader.pages)} pages loaded!")
            q = st.text_input("Ask question (optional):")
            if st.button("✨ Summarize PDF"):
                prompt = f"Answer: {q}\n\n{text[:4000]}" if q else f"Summarize key points:\n\n{text[:4000]}"
                with st.spinner("🐱 Reading PDF..."):
                    r = ask_ai(prompt)
                st.markdown("---")
                st.markdown(r)

# ── QUIZ ───────────────────────────────────────────────────
elif page == "🧠 Quiz Me":
    st.markdown("# 🧠 Quiz Me")

    weak = mem.get("weak_topics",[])
    if weak:
        st.markdown("**⚠️ Practice weak topics:**")
        cols = st.columns(min(len(weak),4))
        for i,t in enumerate(weak[:4]):
            with cols[i]:
                if st.button(t):
                    st.session_state["quiz_topic"] = t

    c1,c2,c3 = st.columns(3)
    with c1:
        topic = st.text_input("Topic:",
            value=st.session_state.get("quiz_topic",""))
    with c2:
        diff = st.selectbox("Difficulty:",["Easy","Medium","Hard"])
    with c3:
        num = st.selectbox("Questions:",[3,5,10])

    if st.button("🚀 Generate Quiz") and topic:
        with st.spinner("🐱 Generating..."):
            r = ask_ai(f"""Generate {num} {diff} MCQ questions on '{topic}' for CAT exam.
Format each:
Q. [question]
A) B) C) D)
✅ Answer: [letter]
💡 Explanation: [one line]
---""")
        st.markdown("---")
        st.markdown(r)
        st.markdown("---")

        score = st.number_input(f"How many correct? (out of {num})",0,num,0)
        if st.button("💾 Save Score"):
            pct = round(score/num*100,1)
            p   = load_perf()
            p["quizzes"].append({"topic":topic,"score":score,"total":num,"pct":pct,"date":now()})
            save_perf(p)
            m2 = load_memory()
            if pct >= 70:
                if topic not in m2["strong_topics"]: m2["strong_topics"].append(topic)
                if topic in m2["weak_topics"]:       m2["weak_topics"].remove(topic)
                st.success(f"🎉 {score}/{num} = {pct}% — Added to Strong!")
            else:
                if topic not in m2["weak_topics"]:   m2["weak_topics"].append(topic)
                st.warning(f"📚 {score}/{num} = {pct}% — Added to Weak. Practice more!")
            save_memory(m2)

# ── NOTES Q&A ──────────────────────────────────────────────
elif page == "📚 Notes Q&A":
    st.markdown("# 📚 Notes Q&A")
    tab1,tab2 = st.tabs(["📄 Upload PDF","📝 Paste Notes"])

    with tab1:
        pdf = st.file_uploader("Upload notes PDF:", type=["pdf"])
        if pdf:
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(pdf.read()))
            st.session_state["notes"] = "".join(p.extract_text() or "" for p in reader.pages)
            st.success(f"✅ {len(reader.pages)} pages loaded!")

    with tab2:
        pasted = st.text_area("Paste notes:", height=150)
        if st.button("Use These Notes"):
            st.session_state["notes"] = pasted
            st.success("✅ Notes saved!")

    if "notes" in st.session_state:
        q = st.text_input("Ask question from notes:")
        if st.button("🔍 Get Answer") and q:
            with st.spinner("🐱 Reading notes..."):
                r = ask_ai(f"Based ONLY on these notes answer:\n\nNOTES:\n{st.session_state['notes'][:3000]}\n\nQUESTION: {q}")
            st.markdown("---")
            st.markdown(r)

# ── EXPLAIN ────────────────────────────────────────────────
elif page == "💡 Explain Topic":
    st.markdown("# 💡 Explain a Topic")
    c1,c2 = st.columns(2)
    with c1:
        topic = st.text_input("Topic:", placeholder="e.g. Percentages, Syllogisms")
    with c2:
        level = st.selectbox("Level:",["Beginner","Intermediate","Advanced"])

    st.markdown("**Quick select:**")
    quick = ["Percentages","Time & Work","Probability","Syllogisms","RC Strategy","Data Interpretation"]
    cols  = st.columns(3)
    for i,t in enumerate(quick):
        with cols[i%3]:
            if st.button(t, key=f"q{i}"):
                st.session_state["exp_topic"] = t

    if "exp_topic" in st.session_state:
        topic = st.session_state["exp_topic"]

    if st.button("💡 Explain Now") and topic:
        with st.spinner("🐱 Preparing..."):
            r = ask_ai(f"Explain '{topic}' at {level} level for MBA exam. Include concept, formulas, shortcuts, examples, common mistakes.")
        st.markdown("---")
        st.markdown(r)

# ── WEB SEARCH ─────────────────────────────────────────────
elif page == "🔍 Web Search":
    st.markdown("# 🔍 Web Search + AI Summary")
    query = st.text_input("Search:", placeholder="e.g. IIM cutoffs 2024")

    if st.button("🔍 Search") and query:
        with st.spinner("🌐 Searching..."):
            try:
                from duckduckgo_search import DDGS
                results = []
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=5):
                        results.append(f"{r['title']}: {r['body'][:200]}")
                context = "\n".join(results)
                response = ask_ai(f"Summarize for MBA student:\n{context}")
                st.markdown("### 🐱 AI Summary")
                st.markdown(response)
                with st.expander("📰 Raw Results"):
                    for r in results:
                        st.markdown(f"• {r}")
            except Exception as e:
                st.error(f"Search error: {e}")

# ── CHAT ───────────────────────────────────────────────────
elif page == "💬 Chat":
    st.markdown("# 💬 Chat with CatBot")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("Ask anything about MBA prep...")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            with st.spinner("🐱 Thinking..."):
                context = f"Student: {mem.get('name','')}, Exam: {mem.get('exam','CAT')}, Weak: {', '.join(mem.get('weak_topics',[]))}"
                history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:]])
                r = ask_ai(f"Context: {context}\nHistory:\n{history}\nRespond helpfully.")
            st.markdown(r)
            st.session_state.messages.append({"role":"assistant","content":r})

# ── DASHBOARD ──────────────────────────────────────────────
elif page == "📊 Dashboard":
    st.markdown("# 📊 Performance Dashboard")
    perf    = load_perf()
    quizzes = perf.get("quizzes",[])
    mocks   = perf.get("mock_tests",[])
    avg_q   = round(sum(q["pct"] for q in quizzes)/len(quizzes),1) if quizzes else 0
    avg_m   = round(sum(m["pct"] for m in mocks)/len(mocks),1)     if mocks   else 0

    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🧠 Quizzes",    len(quizzes))
    c2.metric("⭐ Quiz Avg",   f"{avg_q}%")
    c3.metric("📝 Mock Tests", len(mocks))
    c4.metric("🎯 Mock Avg",   f"{avg_m}%")

    st.markdown("---")

    if quizzes:
        st.markdown("### 📈 Quiz Score Trend")
        import pandas as pd
        df = pd.DataFrame({"Quiz": range(1,len(quizzes)+1), "Score": [q["pct"] for q in quizzes]})
        st.line_chart(df.set_index("Quiz"))

        st.markdown("### 📊 Recent Quizzes")
        for q in reversed(quizzes[-8:]):
            c1,c2,c3 = st.columns([3,1,1])
            with c1: st.progress(q["pct"]/100)
            with c2: st.write(q["topic"])
            with c3:
                if q["pct"]>=70: st.success(f"{q['pct']}%")
                else:            st.error(f"{q['pct']}%")
    else:
        st.info("📭 No quizzes yet! Take one first.")

    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### ⚠️ Weak Topics")
        mem2 = load_memory()
        for t in mem2.get("weak_topics",[]):
            st.error(f"🔴 {t}")
        if not mem2.get("weak_topics"):
            st.success("No weak topics! 🎉")
    with c2:
        st.markdown("### ✅ Strong Topics")
        for t in mem2.get("strong_topics",[]):
            st.success(f"🟢 {t}")
        if not mem2.get("strong_topics"):
            st.info("Complete quizzes to see strength!")

# ── MOCK TEST ──────────────────────────────────────────────
elif page == "📝 Mock Test":
    st.markdown("# 📝 Mock Test")
    c1,c2,c3 = st.columns(3)
    with c1: exam = st.selectbox("Exam:",["CAT","XAT","GMAT"])
    with c2: num  = st.selectbox("Questions/section:",[5,10,15])
    with c3: mins = st.selectbox("Time (mins):",[15,30,45,60])

    if st.button("🚀 Start Test"):
        with st.spinner("🐱 Generating test..."):
            r = ask_ai(f"""Create {exam} mock test with {num} questions each for:
VARC, DILR, Quantitative Aptitude.
MCQ format with answer and explanation for each.""")
        st.markdown("---")
        st.markdown(r)
        st.markdown("---")

        total = num * 3
        score = st.number_input(f"Your score (out of {total}):",0,total,0)
        if st.button("💾 Submit Score"):
            pct = round(score/total*100,1)
            p   = load_perf()
            p["mock_tests"].append({"score":score,"total":total,"pct":pct,"exam":exam,"date":now()})
            save_perf(p)
            if pct>=70: st.success(f"🎉 {score}/{total} = {pct}%")
            else:       st.warning(f"📚 {score}/{total} = {pct}% — Keep practicing!")

# ── COLLEGE ────────────────────────────────────────────────
elif page == "🏫 College Shortlist":
    st.markdown("# 🏫 College Shortlisting")
    c1,c2 = st.columns(2)
    with c1:
        pct    = st.slider("CAT Percentile:",50,100,85)
        budget = st.slider("Budget (₹ Lakhs):",5,50,20)
    with c2:
        loc  = st.selectbox("Location:",["Any","Mumbai","Delhi","Bangalore","Ahmedabad","Kolkata"])
        spec = st.selectbox("Specialization:",["Any","Finance","Marketing","HR","Operations"])

    workex = st.slider("Work Experience (months):",0,60,0)

    if st.button("🏫 Shortlist Colleges"):
        with st.spinner("🐱 Finding colleges..."):
            r = ask_ai(f"""Shortlist MBA colleges for:
Percentile: {pct}, Budget: ₹{budget} lakhs,
Location: {loc}, Specialization: {spec}, Work ex: {workex} months.
Give Dream, Target, Safe colleges with cutoffs, fees, placements.""")
        st.markdown("---")
        st.markdown(r)