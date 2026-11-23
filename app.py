import random
import time
import pandas as pd
import streamlit as st

st.set_page_config(page_title="색깔 트릭 퀴즈", page_icon="🎨", layout="wide")

ALL_COLORS = [
    {"name": "빨강", "hex": "#E53935", "emoji": "🔴"},
    {"name": "파랑", "hex": "#1E88E5", "emoji": "🔵"},
    {"name": "초록", "hex": "#43A047", "emoji": "🟢"},
    {"name": "노랑", "hex": "#FDD835", "emoji": "🟡"},
    {"name": "보라", "hex": "#8E24AA", "emoji": "🟣"},
    {"name": "주황", "hex": "#FB8C00", "emoji": "🟠"},
]

DIFFICULTIES = {
    "쉬움 (60초 · 4색)": {"time": 60.0, "color_count": 4},
    "보통 (45초 · 5색)": {"time": 45.0, "color_count": 5},
    "어려움 (30초 · 6색)": {"time": 30.0, "color_count": 6},
}


def get_palette(difficulty_label: str):
    cfg = DIFFICULTIES.get(difficulty_label, DIFFICULTIES["보통 (45초 · 5색)"])
    return cfg["time"], ALL_COLORS[: cfg["color_count"]]


def make_question(palette, prev_sig=None):
    while True:
        word_color = random.choice(palette)     # 글자 '뜻'
        ink_color = random.choice(palette)      # 실제 '글자 색'
        mode = random.choice(["ink", "meaning"])
        sig = (word_color["name"], ink_color["name"], mode)

        same_as_prev_combo = (
            prev_sig is not None
            and (word_color["name"] == prev_sig[0] or ink_color["name"] == prev_sig[1])
        )
        if word_color["name"] != ink_color["name"] and sig != prev_sig and not same_as_prev_combo:
            break

    correct_color = ink_color if mode == "ink" else word_color
    others = [c for c in palette if c["name"] != correct_color["name"]]
    options = random.sample(others, min(3, len(others))) + [correct_color]
    random.shuffle(options)

    return {
        "sig": sig,
        "word_name": word_color["name"],
        "ink_hex": ink_color["hex"],
        "mode": mode,
        "correct_name": correct_color["name"],
        "options": options,
    }


def init_game(difficulty_label=None):
    if difficulty_label is not None:
        st.session_state.difficulty = difficulty_label
    elif "difficulty" not in st.session_state:
        st.session_state.difficulty = "보통 (45초 · 5색)"

    time_limit, palette = get_palette(st.session_state.difficulty)

    st.session_state.time_limit = time_limit
    st.session_state.start_time = time.time()
    st.session_state.score = 0
    st.session_state.combo = 0
    st.session_state.best_combo = 0
    st.session_state.solved = 0
    st.session_state.wrong = 0
    st.session_state.game_over = False
    st.session_state.end_msg = ""
    st.session_state.last_sig = None
    st.session_state.q = make_question(palette)
    st.session_state.feedback = "글자 뜻과 글자 색의 함정에 주의하세요! 빠르게 선택해 보세요."
    st.session_state.history = [{"문제": 0, "누적점수": 0, "콤보": 0}]


if "best_score" not in st.session_state:
    st.session_state.best_score = 0
if "difficulty" not in st.session_state:
    st.session_state.difficulty = "보통 (45초 · 5색)"
if "q" not in st.session_state:
    init_game(st.session_state.difficulty)


def remaining_sec():
    if st.session_state.game_over:
        return 0.0
    return max(0.0, st.session_state.time_limit - (time.time() - st.session_state.start_time))


def finish_game(reason_prefix="⏰ 시간 종료!"):
    st.session_state.game_over = True
    st.session_state.best_score = max(st.session_state.best_score, st.session_state.score)
    st.session_state.end_msg = (
        f"{reason_prefix} 최종 점수 **{st.session_state.score}점** "
        f"(정답 {st.session_state.solved}개 / 오답 {st.session_state.wrong}개)"
    )


# --- 상단 헤더 & 난이도 선택 ---
top_left, top_right = st.columns([2.2, 1])
with top_left:
    st.title("🎨 색깔 트릭 퀴즈 (스트룹 순발력 테스트)")
    st.caption("미션 조건('글자 색' vs '글자 뜻')을 먼저 확인하고, 제한 시간 안에 최고 기록에 도전하세요!")

with top_right:
    selected_diff = st.selectbox(
        "난이도 선택",
        options=list(DIFFICULTIES.keys()),
        index=list(DIFFICULTIES.keys()).index(st.session_state.difficulty),
        key="diff_selector",
    )
    if selected_diff != st.session_state.difficulty:
        init_game(selected_diff)
        st.rerun()


# --- 실시간 타이머 및 상태판 (버튼 씹힘 방지를 위해 fragment 적용) ---
@st.fragment(run_every=0.2)
def render_timer_and_metrics():
    rem = remaining_sec()
    if not st.session_state.game_over and rem <= 0.0:
        finish_game(f"⏰ {int(st.session_state.time_limit)}초 종료!")
        st.rerun()

    progress_ratio = rem / st.session_state.time_limit if st.session_state.time_limit > 0 else 0.0
    st.progress(max(0.0, min(1.0, progress_ratio)))

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("남은 시간", f"{rem:.1f} 초")
    m2.metric("현재 점수", f"{st.session_state.score} 점")
    m3.metric("최고 점수", f"{st.session_state.best_score} 점")
    m4.metric("현재 콤보", f"{st.session_state.combo} 연속")
    m5.metric("정답 수", f"{st.session_state.solved} 개")


render_timer_and_metrics()

st.info(st.session_state.end_msg if st.session_state.game_over else st.session_state.feedback)

# --- 메인 화면 ---
left, right = st.columns([1.2, 1])

with left:
    if not st.session_state.game_over:
        _, palette = get_palette(st.session_state.difficulty)
        q = st.session_state.q
        mission_label = (
            "🎨 실제 '글자 색'을 고르세요!"
            if q["mode"] == "ink"
            else "📖 적혀 있는 '글자 뜻'을 고르세요!"
        )

        st.markdown(f"### 🎯 미션: {mission_label}")
        st.markdown(
            f"""
            <div style="
                text-align: center;
                padding: 28px 16px;
                margin: 12px 0 20px 0;
                border-radius: 14px;
                background-color: #161A22;
                border: 1px solid #2E3545;
            ">
                <span style="
                    font-size: 64px;
                    font-weight: 900;
                    color: {q['ink_hex']};
                    letter-spacing: 6px;
                ">{q['word_name']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        row1 = st.columns(2)
        row2 = st.columns(2)
        grid = [row1[0], row1[1], row2[0], row2[1]]

        for idx, opt in enumerate(q["options"]):
            with grid[idx]:
                btn_label = f"{opt['emoji']} {opt['name']}" if q["mode"] == "ink" else opt["name"]
                if st.button(
                    btn_label,
                    key=f"ans_{st.session_state.solved}_{st.session_state.wrong}_{idx}",
                    use_container_width=True,
                ):
                    now_rem = remaining_sec()
                    if now_rem <= 0.0:
                        finish_game("⏰ 시간 초과!")
                        st.rerun()
                    else:
                        if opt["name"] == q["correct_name"]:
                            st.session_state.combo += 1
                            st.session_state.best_combo = max(
                                st.session_state.best_combo, st.session_state.combo
                            )
                            st.session_state.solved += 1
                            speed_bonus = int(now_rem * 2)
                            combo_bonus = (st.session_state.combo - 1) * 20
                            gained = 100 + speed_bonus + combo_bonus
                            st.session_state.score += gained
                            st.session_state.best_score = max(
                                st.session_state.best_score, st.session_state.score
                            )
                            st.session_state.feedback = (
                                f"✅ 정답! +{gained}점 "
                                f"(기본 100 + 속도 {speed_bonus} + 콤보 {combo_bonus})"
                            )
                        else:
                            st.session_state.combo = 0
                            st.session_state.wrong += 1
                            st.session_state.score = max(0, st.session_state.score - 30)
                            st.session_state.feedback = (
                                f"❌ 트릭에 걸렸어요! 정답은 **'{q['correct_name']}'** "
                                f"(-30점, 콤보 초기화)"
                            )

                        st.session_state.history.append({
                            "문제": len(st.session_state.history),
                            "누적점수": st.session_state.score,
                            "콤보": st.session_state.combo,
                        })
                        st.session_state.last_sig = q["sig"]
                        st.session_state.q = make_question(palette, prev_sig=st.session_state.last_sig)
                        st.rerun()

        if st.button("🔄 다시 시작", use_container_width=True):
            init_game(st.session_state.difficulty)
            st.rerun()
    else:
        st.success(
            f"최고 연속 콤보: **{st.session_state.best_combo}회** | "
            f"세션 최고 기록: **{st.session_state.best_score}점**"
        )
        if st.button("🚀 새 게임 도전하기", type="primary", use_container_width=True):
            init_game(st.session_state.difficulty)
            st.rerun()

with right:
    st.subheader("📈 점수 & 콤보 기록")
    df = pd.DataFrame(st.session_state.history).set_index("문제")
    st.line_chart(df[["누적점수"]])
    st.line_chart(df[["콤보"]])
