# E4 grading guideline (one page)

You are grading answers to questions, the same way the LLM judges in this study were asked to. Your grades
are the human reference the judges are compared against, so grade independently and honestly.

## Your sheet

`data/e4/reduced40/sheet_<your id>.csv`, 160 assigned rows (40 questions in four forms), amended 9 November 2026. Original row IDs are retained and have gaps. Use the shorter XLSX files in `outputs/e4_reduced40/` if grading in Excel. Each row has:

- **question**: the question, in English (multiple-choice questions show their options).
- **reference_answer**: a correct reference answer, for factual questions only. Blank for open-ended ones.
- **answer**: the answer to grade.

Fill in four whole numbers from 1 to 5 per row, and optionally a short **notes** entry. Do not change any
other cell, and do not sort, insert or delete rows.

## The four criteria (exactly the judges' rubric)

| Criterion | 1 | 5 |
|---|---|---|
| **correctness** | wrong | fully correct |
| **completeness** | misses the main points | covers them fully |
| **clarity** | confusing | clear and well organised |
| **language_quality** | hard to read in its own language | fluent and natural |

Use 2, 3 and 4 for everything in between.

- With a reference answer, judge correctness and completeness against it. Without one, use your own
  knowledge of the topic.
- Grade every row on its own, on the same scale.

## Rules

1. **Some answers will look familiar.** The same question comes back later in the sheet, in a different
   version. Grade each row by itself. Don't scroll back to compare, and don't change a row you have already
   graded.
2. **Work alone.** Don't discuss questions, answers or grades with the other grader until you have both
   finished and imported your sheets.
3. **Don't use AI tools or translators** to grade or to read the answers.
4. **Take breaks.** Each consecutive block of 40 assigned answers contains every selected question once.
   Original row IDs are not sequential in the shorter sheet. Keep existing grades; transfer by row ID, never by spreadsheet row number.
5. If you can't grade a row (for example, a broken answer), leave all four grades blank and say why in notes.

## Saving

Google Sheets (recommended): **File > Import** the CSV, grade, then **File > Download > Comma-separated
values (.csv)**. Excel: **Save As > CSV UTF-8 (Comma delimited)**. A plain "CSV" save in Excel loses the
Hindi text, and the import will refuse the file. Send the CSV back without renaming it.
