# IEC 62443 Cybersecurity Training Assessment - Streamlit App

This version has been updated from the previous chiller assessment app to an IEC 62443 cybersecurity training assessment.

## Workflow

1. Participant fills in basic details.
2. Participant completes a 10-question IEC 62443 / IACS cybersecurity assessment.
3. Course feedback form appears after assessment submission.
4. Final result is shown after feedback submission.
5. Assessment records and feedback records are saved locally and to GitHub CSV when Streamlit Secrets are configured.
6. Training certificate generation is not included in this version.

## Training content covered

The assessment questions are based on the uploaded IEC 62443 course deck and cover:

- IEC 62443 standard groups: General, Policies & Procedures, System, Component, Profiles and Evaluation
- IT vs IACS cybersecurity priorities
- Cybersecurity awareness
- Security management / patch governance
- SuC, zones and conduits
- System risk assessment and target security levels
- Network security and defense-in-depth
- Component secure development lifecycle
- Security profiles
- Evaluation, evidence and conformance assessment

## Files to upload / replace in GitHub

```text
app.py
requirements.txt
assets/zealcorps_logo.png
results/assessment_results.csv
results/course_feedback.csv
```

## Streamlit Secrets

In Streamlit Community Cloud, open your app > Settings > Secrets and add:

```toml
[app]
admin_password = "admin123"

[github]
token = "YOUR_GITHUB_FINE_GRAINED_TOKEN"
owner = "sarathgoshzc"
repo = "chiller-assessment"
branch = "main"
results_path = "results/assessment_results.csv"
feedback_path = "results/course_feedback.csv"
```

## GitHub token permission

Create a GitHub fine-grained personal access token with:

```text
Repository: chiller-assessment
Contents: Read and Write
```

Do not put the token inside `app.py`.

## Admin download

In the app sidebar:

1. Enter admin password.
2. Download assessment CSV and feedback CSV.

Default password:

```text
admin123
```

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
