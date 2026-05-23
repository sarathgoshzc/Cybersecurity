import base64
import csv
import io
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st


PASS_MARK = 80
COURSE_TITLE = "IEC 62443 Cybersecurity Training"
COURSE_SUBTITLE = "IACS / OT Cybersecurity Standards and Assessment"
COMPANY_NAME = "Zealcorps Pte Ltd"

BASE_DIR = Path(__file__).resolve().parent
RESULTS_DIR = BASE_DIR / "results"
ASSESSMENT_RESULTS_FILE = RESULTS_DIR / "assessment_results.csv"
FEEDBACK_RESULTS_FILE = RESULTS_DIR / "course_feedback.csv"

# CSV file paths inside your GitHub repository.
GITHUB_RESULTS_PATH = "results/assessment_results.csv"
GITHUB_FEEDBACK_PATH = "results/course_feedback.csv"

ASSETS_DIR = BASE_DIR / "assets"
LOGO_FILE = ASSETS_DIR / "zealcorps_logo.png"


QUESTIONS = [
    {
        "question": "IEC 62443 is best described as which type of document set?",
        "options": [
            "A single standard used only for IT networks",
            "A series of standards covering IACS cybersecurity concepts, processes, systems, components, profiles and evaluation",
            "A product catalogue for firewalls and switches",
            "A checklist used only during FAT testing",
        ],
        "answer": "A series of standards covering IACS cybersecurity concepts, processes, systems, components, profiles and evaluation",
    },
    {
        "question": "What is the correct IEC 62443 group order used in this course?",
        "options": [
            "Component, General, Evaluation, System, Policies, Profiles",
            "General, Policies & Procedures, System, Component, Profiles, Evaluation",
            "Policies, System, General, Profiles, Evaluation, Component",
            "General, Component, System, Evaluation, Policies, Profiles",
        ],
        "answer": "General, Policies & Procedures, System, Component, Profiles, Evaluation",
    },
    {
        "question": "In IACS cybersecurity, what is usually the main priority compared with normal IT systems?",
        "options": [
            "Only confidentiality of business information",
            "Safety, availability, process integrity and operational continuity",
            "Fast patching without shutdown planning",
            "Replacing all legacy PLCs immediately",
        ],
        "answer": "Safety, availability, process integrity and operational continuity",
    },
    {
        "question": "Which statement best describes cybersecurity awareness in an IACS environment?",
        "options": [
            "Awareness is only required for IT administrators",
            "Awareness should be treated like safety and reinforced through targeted, repeated communication",
            "Awareness is only needed after a cybersecurity incident",
            "Awareness can replace technical controls such as firewalls and monitoring",
        ],
        "answer": "Awareness should be treated like safety and reinforced through targeted, repeated communication",
    },
    {
        "question": "Which item is part of IACS patch management governance?",
        "options": [
            "Patch all controllers immediately without vendor review",
            "Inventory, supplier relationship, monitoring, evaluation, testing, scheduling, deployment and reporting",
            "Disable all patching for the full system lifecycle",
            "Allow every user to install updates independently",
        ],
        "answer": "Inventory, supplier relationship, monitoring, evaluation, testing, scheduling, deployment and reporting",
    },
    {
        "question": "In IEC 62443-3-x risk assessment, what does SuC mean?",
        "options": [
            "Security update checklist",
            "System under consideration",
            "Service user credential",
            "Secure unified controller",
        ],
        "answer": "System under consideration",
    },
    {
        "question": "Which sequence best represents the IEC 62443 system risk assessment method covered in the training?",
        "options": [
            "Buy firewall, install antivirus, close project",
            "Define SuC, perform initial risk assessment, partition zones/conduits, perform detailed assessment, set target SL, obtain approval",
            "Write policy, train users, ignore architecture review",
            "Prepare certificate, submit invoice, archive documentation",
        ],
        "answer": "Define SuC, perform initial risk assessment, partition zones/conduits, perform detailed assessment, set target SL, obtain approval",
    },
    {
        "question": "What is the purpose of zones and conduits in IEC 62443 system design?",
        "options": [
            "To group assets and control communication paths based on risk and security requirements",
            "To remove the need for network monitoring",
            "To make all OT assets part of one flat network",
            "To replace operational procedures",
        ],
        "answer": "To group assets and control communication paths based on risk and security requirements",
    },
    {
        "question": "Which IEC 62443 area covers secure product development lifecycle and technical requirements for IACS components?",
        "options": [
            "IEC 62443-1-x General",
            "IEC 62443-2-x Policies & Procedures",
            "IEC 62443-4-x Component",
            "IEC 62443-6-x Evaluation only",
        ],
        "answer": "IEC 62443-4-x Component",
    },
    {
        "question": "What is the correct purpose of security profiles and evaluation in IEC 62443?",
        "options": [
            "Profiles create new IEC 62443 requirements, and evaluation is only a document check",
            "Profiles contextualize existing IEC 62443 requirements, while evaluation links claims, requirements, evidence and test or assessment results",
            "Profiles are used only for marketing brochures, and evaluation is optional for all projects",
            "Profiles replace risk assessment, and evaluation replaces system design",
        ],
        "answer": "Profiles contextualize existing IEC 62443 requirements, while evaluation links claims, requirements, evidence and test or assessment results",
    },
]


ASSESSMENT_FIELDNAMES = [
    "submitted_at",
    "name",
    "position",
    "department",
    "phone",
    "email",
    "score",
    "total",
    "percentage",
    "result",
    "feedback_submitted",
    "overall_rating",
] + [f"q{i + 1}_answer" for i in range(len(QUESTIONS))] + [
    f"q{i + 1}_status" for i in range(len(QUESTIONS))
]


FEEDBACK_FIELDNAMES = [
    "submitted_at",
    "name",
    "position",
    "department",
    "phone",
    "email",
    "score",
    "percentage",
    "result",
    "overall_rating",
    "course_content_rating",
    "trainer_rating",
    "practical_usefulness_rating",
    "confidence_after_course_rating",
    "comments",
    "improvement_suggestions",
]


RATING_OPTIONS = {
    "5 - Excellent": 5,
    "4 - Very Good": 4,
    "3 - Good": 3,
    "2 - Fair": 2,
    "1 - Poor": 1,
}


# -----------------------------
# Page and UI
# -----------------------------

def setup_page():
    st.set_page_config(
        page_title="IEC 62443 Cybersecurity Assessment",
        page_icon="🔐",
        layout="wide",
    )

    st.markdown(
        """
        <style>
            .main { background-color: #ffffff; }
            .title-box {
                padding: 22px 26px;
                border-radius: 16px;
                background: linear-gradient(90deg, #003B73 0%, #0A548A 100%);
                color: white;
                margin-bottom: 18px;
                box-shadow: 0 6px 18px rgba(0, 59, 115, 0.16);
            }
            .subtitle {
                color: #1f7a3a;
                font-size: 19px;
                font-weight: 700;
                margin-bottom: 20px;
            }
            .info-card {
                padding: 18px;
                border: 1px solid #d8e2ee;
                border-radius: 12px;
                background-color: #f8fbff;
                margin-bottom: 16px;
            }
            .pass-box {
                padding: 30px;
                border-radius: 16px;
                background-color: #ecfdf3;
                border: 2px solid #1f7a3a;
                text-align: center;
            }
            .fail-box {
                padding: 30px;
                border-radius: 16px;
                background-color: #fff4f2;
                border: 2px solid #b42318;
                text-align: center;
            }
            .step-card {
                padding: 18px;
                border-radius: 14px;
                border: 1px solid #dce6ef;
                background-color: #fbfdff;
                margin-bottom: 16px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    logo_col, title_col = st.columns([1, 5])
    with logo_col:
        if LOGO_FILE.exists():
            st.image(str(LOGO_FILE), use_container_width=True)
    with title_col:
        st.markdown(
            """
            <div class="title-box">
                <h1 style="margin:0;">🔐 IEC 62443 Cybersecurity Training Assessment</h1>
                <p style="margin:8px 0 0 0;font-size:18px;">IACS / OT Cybersecurity | Standards Series | Assessment</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div class="subtitle">Pass Criteria: Score ≥ {PASS_MARK}% | 10 Questions | Certificate generation disabled</div>',
        unsafe_allow_html=True,
    )


def valid_email(email: str) -> bool:
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
    return bool(re.match(pattern, email))


def rating_value(label: str) -> int:
    return RATING_OPTIONS.get(label, 0)


# -----------------------------
# GitHub storage helpers
# -----------------------------

def get_github_config():
    """Read GitHub settings from Streamlit secrets."""
    github = st.secrets.get("github", {})
    return {
        "token": github.get("token", ""),
        "owner": github.get("owner", ""),
        "repo": github.get("repo", ""),
        "branch": github.get("branch", "main"),
        "results_path": github.get("results_path", GITHUB_RESULTS_PATH),
        "feedback_path": github.get("feedback_path", GITHUB_FEEDBACK_PATH),
    }


def github_is_configured():
    config = get_github_config()
    return all([config["token"], config["owner"], config["repo"], config["branch"]])


def github_headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def get_github_csv_content(repo_path: str, fieldnames: list[str]):
    """Get an existing CSV from GitHub. If it does not exist, return a CSV header."""
    config = get_github_config()
    url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/contents/{repo_path}"

    response = requests.get(
        url,
        headers=github_headers(config["token"]),
        params={"ref": config["branch"]},
        timeout=20,
    )

    if response.status_code == 404:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        return output.getvalue(), None

    response.raise_for_status()
    payload = response.json()
    decoded = base64.b64decode(payload.get("content", "")).decode("utf-8")
    return decoded, payload.get("sha")


def append_row_to_csv_text(csv_text: str, row: dict, fieldnames: list[str]):
    input_buffer = io.StringIO(csv_text)
    reader = csv.DictReader(input_buffer)
    existing_rows = list(reader)

    output_buffer = io.StringIO()
    writer = csv.DictWriter(output_buffer, fieldnames=fieldnames)
    writer.writeheader()

    for existing_row in existing_rows:
        writer.writerow({field: existing_row.get(field, "") for field in fieldnames})

    writer.writerow({field: row.get(field, "") for field in fieldnames})
    return output_buffer.getvalue()


def save_row_to_github(row: dict, repo_path: str, fieldnames: list[str], commit_label: str):
    """Commit an updated CSV row to GitHub."""
    if not github_is_configured():
        return False, "GitHub storage not configured in Streamlit Secrets."

    config = get_github_config()

    try:
        existing_csv, sha = get_github_csv_content(repo_path, fieldnames)
        updated_csv = append_row_to_csv_text(existing_csv, row, fieldnames)
        encoded_updated_csv = base64.b64encode(updated_csv.encode("utf-8")).decode("utf-8")

        url = f"https://api.github.com/repos/{config['owner']}/{config['repo']}/contents/{repo_path}"

        data = {
            "message": f"Add {commit_label} - {row.get('name', 'participant')} - {row.get('submitted_at', '')}",
            "content": encoded_updated_csv,
            "branch": config["branch"],
        }

        if sha:
            data["sha"] = sha

        response = requests.put(
            url,
            headers=github_headers(config["token"]),
            json=data,
            timeout=20,
        )
        response.raise_for_status()
        return True, f"{commit_label.title()} saved to GitHub CSV."

    except requests.HTTPError as e:
        error_text = e.response.text if e.response is not None else str(e)
        return False, f"GitHub save failed: {error_text}"
    except Exception as e:
        return False, f"GitHub save failed: {e}"


# -----------------------------
# CSV local save/read helpers
# -----------------------------

def save_row_locally(row: dict, file_path: Path, fieldnames: list[str]):
    RESULTS_DIR.mkdir(exist_ok=True)

    existing_rows = []
    if file_path.exists() and file_path.stat().st_size > 0:
        try:
            with file_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                existing_rows = list(reader)
        except Exception:
            existing_rows = []

    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for existing_row in existing_rows:
            writer.writerow({field: existing_row.get(field, "") for field in fieldnames})
        writer.writerow({field: row.get(field, "") for field in fieldnames})


def read_local_csv(file_path: Path, fieldnames: list[str]):
    if file_path.exists():
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=fieldnames)


def read_github_csv(repo_path: str, fieldnames: list[str]):
    if not github_is_configured():
        return None, "GitHub storage not configured."

    try:
        csv_text, _sha = get_github_csv_content(repo_path, fieldnames)
        return pd.read_csv(io.StringIO(csv_text)), "Loaded from GitHub CSV."
    except Exception as e:
        return None, f"Could not read GitHub CSV: {e}"


# -----------------------------
# Assessment and feedback
# -----------------------------

def calculate_score(answers: dict):
    score = 0
    review_rows = []

    for i, q in enumerate(QUESTIONS):
        selected = answers.get(i)
        correct = q["answer"]
        is_correct = selected == correct

        if is_correct:
            score += 1

        review_rows.append(
            {
                "No": i + 1,
                "Question": q["question"],
                "Your Answer": selected or "Not answered",
                "Correct Answer": correct,
                "Status": "Correct" if is_correct else "Wrong",
            }
        )

    total = len(QUESTIONS)
    percentage = round((score / total) * 100, 1)
    result = "PASSED" if percentage >= PASS_MARK else "RETAKE"

    return score, total, percentage, result, review_rows


def create_assessment_row(result_data: dict, feedback_data: dict):
    profile = result_data["profile"]
    answers = result_data["answers"]
    row = {
        "submitted_at": result_data["submitted_at"],
        **profile,
        "score": result_data["score"],
        "total": result_data["total"],
        "percentage": result_data["percentage"],
        "result": result_data["result"],
        "feedback_submitted": "Yes",
        "overall_rating": feedback_data.get("overall_rating", ""),
    }

    for i, q in enumerate(QUESTIONS):
        selected = answers.get(i, "")
        row[f"q{i + 1}_answer"] = selected
        row[f"q{i + 1}_status"] = "Correct" if selected == q["answer"] else "Wrong"

    return row


def create_feedback_row(result_data: dict, feedback_data: dict):
    profile = result_data["profile"]
    return {
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **profile,
        "score": result_data["score"],
        "percentage": result_data["percentage"],
        "result": result_data["result"],
        **feedback_data,
    }


def save_final_submission(result_data: dict, feedback_data: dict):
    config = get_github_config()
    assessment_row = create_assessment_row(result_data, feedback_data)
    feedback_row = create_feedback_row(result_data, feedback_data)

    save_row_locally(assessment_row, ASSESSMENT_RESULTS_FILE, ASSESSMENT_FIELDNAMES)
    save_row_locally(feedback_row, FEEDBACK_RESULTS_FILE, FEEDBACK_FIELDNAMES)

    assessment_saved, assessment_message = save_row_to_github(
        assessment_row,
        config["results_path"],
        ASSESSMENT_FIELDNAMES,
        "assessment result",
    )
    feedback_saved, feedback_message = save_row_to_github(
        feedback_row,
        config["feedback_path"],
        FEEDBACK_FIELDNAMES,
        "course feedback",
    )

    return {
        "assessment_saved": assessment_saved,
        "assessment_message": assessment_message,
        "feedback_saved": feedback_saved,
        "feedback_message": feedback_message,
    }


# -----------------------------
# Screen rendering
# -----------------------------

def reset_all():
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def reset_assessment_only():
    keys_to_delete = [
        key for key in st.session_state.keys()
        if key.startswith("q_") or key.startswith("feedback_") or key in [
            "assessment_done",
            "pending_result",
            "final_submitted",
            "final_result",
        ]
    ]
    for key in keys_to_delete:
        del st.session_state[key]


def show_assessment_form():
    st.markdown(
        f"""
        <div class="info-card">
            Please fill in participant details and answer all {len(QUESTIONS)} questions.
            The assessment is based on the IEC 62443 cybersecurity training deck covering General, Policies & Procedures,
            System, Component, Profiles and Evaluation sections. Certificate generation is not included in this version.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("assessment_form", clear_on_submit=False):
        st.subheader("Participant Details")

        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Name *")
            position = st.text_input("Position *")
            department = st.text_input("Department *")
        with col2:
            phone = st.text_input("Phone No. *")
            email = st.text_input("Email *")

        st.divider()
        st.subheader("Assessment Questions")

        answers = {}
        for i, q in enumerate(QUESTIONS):
            st.markdown(f"**{i + 1}. {q['question']}**")
            answers[i] = st.radio(
                label=f"Question {i + 1}",
                options=q["options"],
                index=None,
                key=f"q_{i}",
                label_visibility="collapsed",
            )
            st.write("")

        submitted = st.form_submit_button("Submit Assessment", type="primary")

    if submitted:
        profile = {
            "name": name.strip(),
            "position": position.strip(),
            "department": department.strip(),
            "phone": phone.strip(),
            "email": email.strip(),
        }

        missing_fields = [label for label, value in profile.items() if not value]
        unanswered = [i + 1 for i, value in answers.items() if value is None]

        if missing_fields:
            st.error("Please fill all participant details.")
            return

        if not valid_email(profile["email"]):
            st.error("Please enter a valid email address.")
            return

        if unanswered:
            st.error(f"Please answer all questions. Missing question(s): {unanswered}")
            return

        score, total, percentage, result, review_rows = calculate_score(answers)
        st.session_state["assessment_done"] = True
        st.session_state["pending_result"] = {
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": profile,
            "answers": answers,
            "score": score,
            "total": total,
            "percentage": percentage,
            "result": result,
            "review": review_rows,
        }
        st.rerun()


def show_feedback_form():
    result_data = st.session_state.get("pending_result")
    if not result_data:
        reset_assessment_only()
        st.rerun()

    st.markdown(
        """
        <div class="step-card">
            <h3 style="margin-top:0;">Course Feedback</h3>
            Your assessment answers have been submitted. Please complete the feedback below to view the final result.
        </div>
        """,
        unsafe_allow_html=True,
    )

    rating_labels = list(RATING_OPTIONS.keys())

    with st.form("course_feedback_form", clear_on_submit=False):
        st.subheader("Rating")
        col1, col2 = st.columns(2)
        with col1:
            overall_rating = st.radio("Overall course rating *", rating_labels, index=None, key="feedback_overall")
            course_content_rating = st.radio("Course content quality *", rating_labels, index=None, key="feedback_content")
        with col2:
            trainer_rating = st.radio("Trainer / delivery rating *", rating_labels, index=None, key="feedback_trainer")
            practical_rating = st.radio("Practical usefulness *", rating_labels, index=None, key="feedback_practical")

        confidence_rating = st.radio(
            "Confidence to apply the learning at work *",
            rating_labels,
            index=None,
            key="feedback_confidence",
        )

        comments = st.text_area("What did you like most about the course?", height=90)
        improvement_suggestions = st.text_area("Suggestions for improvement", height=90)

        feedback_submitted = st.form_submit_button("Submit Feedback and View Result", type="primary")

    if feedback_submitted:
        required_ratings = [overall_rating, course_content_rating, trainer_rating, practical_rating, confidence_rating]
        if any(value is None for value in required_ratings):
            st.error("Please complete all rating fields before submitting feedback.")
            return

        feedback_data = {
            "overall_rating": rating_value(overall_rating),
            "course_content_rating": rating_value(course_content_rating),
            "trainer_rating": rating_value(trainer_rating),
            "practical_usefulness_rating": rating_value(practical_rating),
            "confidence_after_course_rating": rating_value(confidence_rating),
            "comments": comments.strip(),
            "improvement_suggestions": improvement_suggestions.strip(),
        }

        save_status = save_final_submission(result_data, feedback_data)

        st.session_state["final_submitted"] = True
        st.session_state["final_result"] = {
            **result_data,
            "feedback": feedback_data,
            **save_status,
        }
        st.rerun()


def show_final_result():
    result_data = st.session_state.get("final_result")
    if not result_data:
        reset_assessment_only()
        st.rerun()

    result = result_data["result"]
    score = result_data["score"]
    total = result_data["total"]
    percentage = result_data["percentage"]

    if result == "PASSED":
        st.markdown(
            f"""
            <div class="pass-box">
                <h1 style="color:#1f7a3a;margin:0;">PASSED</h1>
                <h2 style="color:#003B73;">Score: {score} / {total} | {percentage}%</h2>
                <p>Feedback submitted successfully. Certificate generation is disabled for this training.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="fail-box">
                <h1 style="color:#b42318;margin:0;">RETAKE</h1>
                <h2 style="color:#003B73;">Score: {score} / {total} | {percentage}%</h2>
                <p>Feedback submitted successfully. Your score is below {PASS_MARK}%.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("Retake Assessment", type="primary"):
            reset_assessment_only()
            st.rerun()
    with col2:
        if st.button("New Participant"):
            reset_all()
            st.rerun()

    st.divider()
    if result_data.get("assessment_saved") and result_data.get("feedback_saved"):
        st.success("Assessment result and course feedback saved to GitHub CSV successfully.")
    else:
        st.warning(result_data.get("assessment_message", "Assessment result was not saved to GitHub."))
        st.warning(result_data.get("feedback_message", "Course feedback was not saved to GitHub."))

    st.subheader("Answer Review")
    review_df = pd.DataFrame(result_data["review"])
    st.dataframe(review_df, use_container_width=True, hide_index=True)

    st.subheader("Submitted Course Feedback")
    feedback_df = pd.DataFrame([result_data["feedback"]])
    st.dataframe(feedback_df, use_container_width=True, hide_index=True)


def show_results_download():
    st.sidebar.header("Admin / Records")
    st.sidebar.caption("Submitted assessment records and course feedback are saved to GitHub CSV when configured.")

    admin_password = st.sidebar.text_input("Admin Password", type="password")
    expected_password = st.secrets.get("app", {}).get("admin_password", "admin123")

    if admin_password != expected_password:
        st.sidebar.info("Enter admin password to download records.")
        return

    st.sidebar.success("Admin access granted.")
    config = get_github_config()

    github_assessment_df, github_assessment_message = read_github_csv(config["results_path"], ASSESSMENT_FIELDNAMES)
    if github_assessment_df is not None:
        st.sidebar.download_button(
            label="Download GitHub Assessment CSV",
            data=github_assessment_df.to_csv(index=False).encode("utf-8"),
            file_name="iec62443_assessment_results_github.csv",
            mime="text/csv",
        )
        st.sidebar.success(github_assessment_message)
    else:
        st.sidebar.warning(github_assessment_message)

    github_feedback_df, github_feedback_message = read_github_csv(config["feedback_path"], FEEDBACK_FIELDNAMES)
    if github_feedback_df is not None:
        st.sidebar.download_button(
            label="Download GitHub Feedback CSV",
            data=github_feedback_df.to_csv(index=False).encode("utf-8"),
            file_name="iec62443_course_feedback_github.csv",
            mime="text/csv",
        )
        st.sidebar.success(github_feedback_message)
    else:
        st.sidebar.warning(github_feedback_message)

    local_assessment_df = read_local_csv(ASSESSMENT_RESULTS_FILE, ASSESSMENT_FIELDNAMES)
    st.sidebar.download_button(
        label="Download Local Assessment Backup CSV",
        data=local_assessment_df.to_csv(index=False).encode("utf-8"),
        file_name="iec62443_assessment_results_local_backup.csv",
        mime="text/csv",
    )

    local_feedback_df = read_local_csv(FEEDBACK_RESULTS_FILE, FEEDBACK_FIELDNAMES)
    st.sidebar.download_button(
        label="Download Local Feedback Backup CSV",
        data=local_feedback_df.to_csv(index=False).encode("utf-8"),
        file_name="iec62443_course_feedback_local_backup.csv",
        mime="text/csv",
    )


def main():
    setup_page()
    show_results_download()

    if st.session_state.get("final_submitted") and st.session_state.get("final_result"):
        show_final_result()
        return

    if st.session_state.get("assessment_done") and st.session_state.get("pending_result"):
        show_feedback_form()
        return

    show_assessment_form()


if __name__ == "__main__":
    main()
