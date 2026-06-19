# CampaignSim — Paper Review
**Document:** CampaignSim: An AI-Powered Multi-Agent Marketing Simulation and Recommendation Platform
**Institution:** The Hashemite University, Faculty of Engineering, Computer Engineering Department
**Reviewed:** 2026-05-29

---

## Overall Assessment

The paper presents a technically credible and well-scoped graduation project. The architecture is thoughtfully designed and the technology stack choices are defensible. However, the submission has significant issues that should be addressed before final submission: missing citations for core statistics, weak experimental validation, low-quality sources for the regional market claims, and strong indicators of AI-assisted writing throughout.

---

## 1. Technical Accuracy

### ✅ Accurate Claims

- **Argyle et al. "algorithmic fidelity"** — Correctly attributed. The concept maps to the cited paper "Out of One, Many: Using Language Models to Simulate Human Samples" (Reference 5). ✓
- **Park et al. "Generative Agents"** — Correctly attributed and described. ✓
- **Horton's "Homo silicus"** — Correctly attributed to "Large Language Models as Simulated Economic Agents" (Reference 10). ✓
- **GraphRAG pioneered by Microsoft Research** — Accurate. Supported by References 1 and 15. ✓
- **OASIS "up to one million users"** — Matches the paper title (Reference 27/28). ✓
- **Technology stack versions** (Flask 3.0+, Python 3.11–3.12, Vue 3, Pydantic 2.0+, D3.js 7.x) — All plausible and consistent with the 2025–2026 timeframe. ✓
- **concurrent.futures.ThreadPoolExecutor** — Correct Python standard library module. ✓
- **PyMuPDF for PDF extraction with 500-token chunks / 50-token overlap** — Standard and reasonable RAG chunking configuration. ✓

### ❌ Inaccurate or Unsupported Claims

**1. Missing citation: "60% to 80% of new product marketing campaigns fail to meet their KPIs" (Section 1.2)**
This statistic is presented as established fact but has no citation. It is a widely repeated industry claim with unclear origins. It must be sourced or removed.

**2. Missing citations: Global ad market figures (Section 1.2)**
- "$600 billion in 2024" — no citation
- "projected to exceed $870 billion by 2028" — no citation
Both require reputable sources (e.g., Statista, eMarketer, GroupM Global Ad Forecast).

**3. "ReACT (Reasoning + Acting)" — Minor inaccuracy**
The ReAct paper by Yao et al. (2022) defines the framework as "Reasoning and Acting," not "Reasoning + Acting." More critically, the original ReAct paper is never cited anywhere in the bibliography despite being used as a core methodology throughout the system design. This is a significant omission. The citation should be: Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," ICLR 2023.

**4. Jordan/MENA economic statistics sourced from marketing agency websites (Section 5.1)**
Several specific economic claims are cited from low-quality, non-authoritative sources:
- "Jordan's tech sector contributes over $2.2 billion to the national economy annually" — cited from thehovi.com (a local AI marketing agency). This should use the World Bank, Jordanian Ministry of Digital Economy, or UNCTAD data.
- "tertiary education enrollment rate at over 33%" — same source. UNESCO Institute for Statistics is the authoritative source.
- "digital ad spend exceeded $120 million in 2025" and "18%–22% year-on-year growth" — cited from thiqagency.com (a local advertising agency). These figures require an authoritative report (e.g., WARC, eMarketer, or IAB MENA).

Using marketing agency websites as sources for national economic statistics is academically inappropriate and will likely be flagged by supervisors.

**5. "Zep Cloud operates natively with sub-200ms latency" — Unverified**
This specific latency figure is stated twice (Sections 3.2 and 3.1) as a hard requirement and system property but is not cited or empirically verified in the paper. Either cite official Zep Cloud documentation or reframe as a tested observation with measured data.

**6. Engagement formula not accessible (Section 4.1)**
The text states "The system mathematically defines the core engagement score as:" but the formula appears to be embedded as an image, making it inaccessible in text-based review and potentially non-machine-readable. Formulas should be in LaTeX or plain text in the document body.

---

## 2. Content Quality and Structure

### Strengths

- The problem statement is well-framed with concrete, quantifiable pain points.
- The design alternatives analysis (Section 3.3) is one of the strongest sections — it clearly justifies architectural decisions with technical reasoning.
- ABET and standards alignment (ISO 25010, IEEE 7000-2021, ISO/IEC/IEEE 29148) shows appropriate academic rigor.
- The technology stack is modern and internally consistent.
- The use of GraphRAG + OASIS + ReAct as a combined architecture is genuinely novel enough to be interesting.

### Issues

**1. Experimental validation is the paper's most serious academic weakness (Section 4.2–4.3)**
The entire evaluation consists of one synthetic scenario ("FreshBrew Cold Brew Coffee") run on 30–40 generated agents. The paper reports engagement rates (35.2%, 28.9%, 19.4%) as though they are meaningful results, but there is no ground truth to compare against. Critically missing:
- How do you know the simulation is accurate? Were any results compared to real marketing outcomes?
- Was the same scenario run multiple times? Are the engagement figures reproducible?
- Were any statistical significance tests performed?
- A single hypothetical brand is insufficient validation for a system claiming to replace expensive real-world A/B testing. Even a comparison against a public marketing dataset would strengthen this significantly.

**2. Conclusion is largely a restatement of the Abstract (Section 6.1)**
Nearly every sentence in the conclusion paraphrases the abstract or introduction without adding new synthesis. A conclusion should reflect on what was *learned* — what surprised you, what limitations became apparent during implementation, what would you do differently. As written, it adds almost no value.

**3. Chapter 5 reads as a marketing pitch, not academic analysis**
Section 5.1 in particular uses language more appropriate for a business plan than a technical paper ("immense commercial viability," "unprecedented expansion," "highly educated, bilingual workforce"). The environmental argument in Section 5.3 — that preventing failed A/B tests saves "vast amounts of global network bandwidth" — is a significant stretch that is not supported by any data or citation.

**4. Appendices describe documentation that may not exist**
Appendix B states that "comprehensive agile tracking logs, Kanban board progression charts, sprint retrospective minutes, and continuous integration pipeline diagnostics are maintained on the development team's shared directory." If these documents were not actually produced, this is a misrepresentation. Either include them or remove the claim.

**5. Table and Figure content not integrated into the text**
Tables 1–5 and Figures 1–4 are referenced throughout but their content is not discussed in sufficient depth in the surrounding text. For example, Table 5 (Agent Action Engagement Weights) shows headers but the actual weights and their justification deserve a paragraph of analysis explaining *why* those specific values were chosen.

**6. No validation of persona quality**
The paper claims generated personas achieve "high algorithmic fidelity" (citing Argyle et al.) but does not test this claim. A basic check — such as asking the same personas follow-up questions and seeing if responses are consistent with their defined profiles — is not reported.

---

## 3. Writing Style — AI-Generation Indicators

**Disclaimer:** No tool can reliably detect AI-generated text with certainty. The following are stylistic patterns commonly associated with AI-assisted writing. Some may reflect the writing style of the authors, so treat these as observations, not accusations.

**Strong stylistic indicators present throughout the paper:**

1. **Excessive use of intensifiers and superlatives** — Words like "immense," "massive," "severe," "profound," "highly," "drastically," "unprecedented," "rigorous," and "rapidly" appear in nearly every paragraph. AI text generators frequently overuse these words to add emphasis. Human academic writing typically uses them sparingly.

2. **Uniformly formal, polished register with no variation** — The acknowledgments, abstract, technical sections, and ethical analysis all read at the exact same level of complexity and formality. Human-authored papers almost always show stylistic variation between sections written at different times or by different contributors.

3. **Generic acknowledgment section** — The acknowledgment contains no personal details: no names of supervisors, family members, or specific colleagues. It uses phrases like "Extensive appreciation is extended to the Hashemite University Faculty of Engineering for providing the rigorous academic foundation." This is characteristic AI boilerplate.

4. **Characteristic AI sentence openers** appearing multiple times:
   - "The successful completion of..."
   - "By [gerund], [system] dramatically..."
   - "[X] possesses immense [positive quality]..."
   - "The explosive growth of..."

5. **Weak first-person attribution** — The paper makes extensive claims about what "the team did" or "the system achieves" without any grounded personal perspective. A graduation project paper should include the students' perspective on challenges encountered, decisions debated, and lessons learned.

6. **Section 5.3 (Environmental Analysis) reads as padding** — The argument that CampaignSim reduces "global network bandwidth" by preventing failed ad campaigns is not supported by any data. This section appears designed to fill a required section without substantive content.

**Recommendation:** Your supervisor may or may not run this through AI detection tools, but the writing style will likely raise questions during the oral defense. It is strongly recommended that the authors revise the paper in their own voice, particularly Chapters 5 and 6 and the Acknowledgment section.

---

## 4. Citation and Reference Issues

| Issue | Section | Severity |
|---|---|---|
| No citation for "60–80% campaign failure rate" | 1.2 | High |
| No citation for "$600B in 2024" and "$870B by 2028" | 1.2 | High |
| ReAct (Yao et al. 2023) paper not cited | 3.3, 4.1 | High |
| Economic stats cited from marketing agency websites | 5.1 | High |
| Citation [4] used in context of "algorithmic fidelity" but [5] is the Argyle paper | 2.1, 5.2 | Medium |
| Zep Cloud sub-200ms latency claim uncited | 3.1, 3.2 | Medium |
| No citation for the engagement score formula weights | 4.1 | Medium |

---

## 5. Summary Recommendations

**Before submission, the team should address:**

1. Add citations for the 60–80% failure rate, global ad market size projections, and ReAct (Yao et al.).
2. Replace marketing agency website sources in Section 5.1 with World Bank, UNESCO, WARC, or eMarketer data.
3. Strengthen Section 4.2–4.3 with at minimum a second test scenario, reproducibility data, and a discussion of the simulation's limitations and potential inaccuracies.
4. Rewrite the Conclusion to add genuine reflection rather than restating the abstract.
5. Revise the Acknowledgment to include specific names (supervisor, teammates, etc.).
6. Tone down the hyperbolic language in Chapter 5 to match academic register.
7. Make the engagement score formula accessible as text (LaTeX or plain math notation).
8. Either provide or remove the Appendix B claims about Kanban boards and CI diagnostics.

**Lower priority but recommended:**
- Add a paragraph justifying the specific engagement weight values in Table 5.
- Clarify the ReACT acronym as "Reasoning and Acting" and add the original paper citation.
- Note the Zep Cloud latency figure as a tested measurement or cite official documentation.
