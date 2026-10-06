# Founding context — raw brief (2026-09-16)

> Verbatim capture of the requirements brain-dump given in chat on 2026-09-16, before any structuring. Kept because the PRD paraphrases it and paraphrase loses detail — if something in the PRD looks off, check it against this first. Lightly reformatted into paragraphs for readability; no content added or removed.

---

## The system, as described

PowerApp for data entry — database organized by year — database uploaded to a backend system. Every time a student goes on internship, the student fills in the details. Previously entered data auto-fills (populated data), but the student can also change it. On submit, data goes to SharePoint.

The system identifies whether the company is already in the database (new vs. existing) and, for a company name that's in the database but with additional/different detail, flags it separately. Example: how many new companies, how many partial matches (new detail) — instead of checking all records, staff only need to check the new or partial ones (for manual checking). Staff can reconfirm and re-upload; the database gets updated. This produces a clean database for that semester. The backend (Excel/Office Script) also gets updated/reset for the next semester so it can be refilled easily.

For current semester data — after data cleaning, there is a button to send an automated, personalized email to the host company supervisor (PDF, personalized).

Current student data gets cleaned for the next year/semester, and using the semester template, new batch student details are entered to allow only that batch's students to access the system for report duty — repeating the same process as the previous semester.

There is a button to send an email to all students for the report duty process (normally the first-time notification).

There is a reminder button for students who haven't filled in the report duty form.

All processes, while running, should show notifications in Teams: running / processing / success.

## What's currently broken

- Issue with the student share folder.
- Process ID reading Excel doesn't work.
- Email has to be sent manually (automation not working / not trusted).
- The system currently only works for students to fill in (implying other parts are degraded/manual).
- Old database (issue unspecified beyond "also").
- Possibly an issue with a script, or with OneDrive storage.
- There's also an admin guideline that should exist/be produced.

## Ownership

The flows currently live on another person's account — Encik Kamal (`kamalazreel.k@utp.edu.my`). Need to figure out what to move / how to migrate.

## The ask

Help set up this as a proper project, and generate ideas on how to tackle the issues above.

---

## Follow-up answers (same session, after initial flow-export analysis)

Asked before scaffolding the project, to avoid guessing on load-bearing calls:

- **Access level:** "No, I can only test and analyse in my personal [account]. Use the admin laptop in the office (can come whenever needed to)." → Live/admin changes require physical presence at the office admin laptop; the personal account is read/analyze-only.
- **Deadline:** "Yes, tied to next semester rollover." → Exact date not yet given; tracked as an open question.
- **Test safety net:** "The zip folders are a copy of the flows we have." → No separate Power Platform dev/test environment exists. The exported zips are the only existing backup/rollback mechanism for the live flows.
- **Scope boundary:** "Open to small custom code if it helps." → Not required to stay 100% low-code; a small script (e.g. one Azure Function) is acceptable where it clearly outperforms the Power Platform-native option, balanced against CDO staff being able to maintain it after handover.
