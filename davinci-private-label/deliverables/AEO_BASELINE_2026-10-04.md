# Praxera AEO baseline — 50 buyer questions x 4 engines (4 Oct 2026)

Tool: ClientCommand run_aeo_check (Perplexity sonar, Gemini 3.8 flash + Google Search, OpenAI web_search, Anthropic web search). Raw rows: reference/aeo_praxera_2026-10-04_raw_rows.json. Single runs are noisy; re-run monthly and read the trend.

| Engine | Asked | Answered | Praxera cited | davincilabs.com cited |
|---|---|---|---|---|
| Perplexity | 50 | 50 | 2 | 26 |
| Gemini | 50 | 50 | 0 | 13 |
| OpenAI | 50 | 30 (20 timed out) | 3 | 1 |
| Anthropic | 50 | 37 (13 timed out) | 0 | 8 |
| **Total** | 200 | 167 | **5 (3%)** | **48 (29%)** |

By group (Praxera cited): vendor discovery 0, audience (practitioners/gyms/coaches) 0 of 13, product categories 3 (weight-management, sleep, men's health), channels 0, compliance 0, local/comparison 2 (the "190+ catalog" question).
Praxera and davincilabs.com were cited together once.
Most cited domains: davincilabs.com 48, wonnda 38, supliful 37, makersnutrition 35, vitaplusinter 21, smpnutra 20, matsunnutrition 19, hdnutra 18, newtropin 18, thomasnet 16.
Source types engines cite: directories/listicles (wonnda, thomasnet, usetorg, alibaba, newtropin), supplier guides (inventoryready, atriumsci, build-your-own-brand), manufacturer sites; LinkedIn (Perplexity only), Wikipedia (Anthropic only), YouTube/Reddit (Gemini only); compliance questions cite fda.gov/nsf.org.
Caveats: OpenAI/Anthropic timeouts (33 cells), Gemini returned citations on only 19 of 50, citation lists capped at 12 domains per cell.
