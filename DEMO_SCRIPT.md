# 2-minute demo script and judging checklist

## Say this (about 2 minutes)
1. **Problem (20s):** "Evidence arrives as scattered documents, and people make claims the documents do not actually prove. Explaining a case clearly takes hours."
2. **Demo (60s):** Open the live site. Click *Use the sample water-complaint file*, then *Analyze evidence*. Point at the live progress ("Gemma 4 is analysing... characters written").
   Show the result: green/amber/red claims, the highlighted quotes, and the line "N of M quotes found word for word in your files".
   Point out the claim "The water is safe to drink" is marked **not supported**, because the inspection report contradicts it. Press *Play storyboard*.
3. **Why it is trustworthy (20s):** "The server re-checks every quote against your files. If the model invents a quote, it is flagged and the claim is downgraded."
4. **Stack and categories (20s):** Gemma 4 (open weights) does the analysis. Open-source, MIT licensed. Graphify maps the codebase (`graphify-out/`). Deployed on Cloudways.

## Before you submit (tick every box)
- [ ] Live URL works and is pasted at the top of README.md
- [ ] `GEMINI_API_KEY` set on the server, `ENVIRONMENT=production`
- [ ] `cd backend && python -m pytest` shows all tests passing
- [ ] Repo is public, `.env` is NOT in it, LICENSE is present
- [ ] README top paragraph matches the official problem statement wording
- [ ] Graphify screenshot added (`graphify-out/` committed)
- [ ] 1-2 minute screen recording uploaded
- [ ] All 4 categories ticked on the submission form
