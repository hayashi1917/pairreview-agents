# Common Corpus の模擬査読ログ

2026-10-15に生成。査読者3名も著者もLLMによるシミュレーションです。著者の追加実験・修正の約束は実際の著者の発言や実施結果ではありません。

実行条件・限界・日本語の要約は [実行結果](README.md) を参照してください。以下はJSON出力を順番に並べた原文です。


## R1-I-001: Reviewer 1 — 初期査読

Certainly! Here is a peer review of the paper based on the provided guidelines:

---

# Peer Review for "Common Corpus: The Largest Truly Open Multilingual Pretraining Dataset"

## Summary

This paper introduces **Common Corpus**, a massive, fully open dataset (~2 trillion tokens) for LLM pre-training. The corpus spans six major collections (Open Government, Open Culture, Open Science, Open Code, Open Web, Open Semantic), is highly multilingual, and is composed only of uncopyrighted or permissively licensed data. The authors detail the provenance, filtering, and curation process, address challenges around legal/data governance, and benchmark models trained on Common Corpus versus leading baselines.

---

## Strengths

### 1. **Motivation Clarity and Societal Importance**
- The paper clearly motivates its work: the increasing legal and ethical challenges around web-scale LLM training data, with high-profile lawsuits and dataset takedowns, creates a pressing need for a large, truly open, auditable corpus.
- The impact of this work is high: enabling open science, reproducibility, and LLM releases that are compliant with the strictest regulations (e.g., EU AI Act).

### 2. **Methodological Novelty**
- The scale and scope of the corpus is novel: previous open corpora were either smaller, monolingual, or only partially open.
- The approach to dataset construction is rigorous, with careful license-checking, provenance tracking, and multi-layered filtering (e.g., for PII, toxicity, OCR errors).
- The authors develop and release a suite of tools for cleaning and curation (e.g., Segmentext, OCRoscope, OCRerrcr, OCRonos, Celadon), addressing previously underexplored challenges such as historical/OCR text correction and multilingual toxicity detection.

### 3. **Experimental Completeness**
- The authors train two LLMs (350M and 1.2B parameters) on Common Corpus and benchmark them against strong baselines (Gemma 3, XGLM, BLOOM, OLMo) on multiple multilingual tasks (MultiBLiMP, XStoryCloze, XCOPA).
- Results show that models trained on Common Corpus perform competitively, especially on highly multilingual benchmarks and even with smaller parameter counts.
- The paper provides rich statistics about the corpus (token, word, doc counts; license distributions; language breakdown), demonstrating transparency and reproducibility.

### 4. **Writing Fluency / Documentation**
- The paper is well-written, with clear structure, thorough documentation, and detailed appendices.
- Tables are comprehensive and allow for straightforward comparison with existing datasets and models.
- The release of both the corpus and associated curation tools furthers scientific sharing.

---

## Weaknesses

### 1. **Experimental Limitations**
- The evaluation is limited to models of relatively small size (1.2B parameters). It is unclear how Common Corpus would scale to larger models (10B+), which are more relevant for state-of-the-art performance.
- The benchmarks used, while diverse, are mainly linguistic and reasoning-oriented. There is little discussion of performance on downstream tasks such as summarization, code generation, or instruction-following, which are important for many LLM applications.
- There is no ablation or study of the effect of individual corpus components (e.g., how much each collection contributes to performance, or the impact of various filtering/cleaning steps).

### 2. **Novelty vs. Engineering**
- While the scale and openness are impressive, the methodological novelty is more in the *engineering* and *curation* than in new algorithms or learning methods.
- The model training approach and evaluation setup largely adopt existing best practices (which is appropriate, but should be acknowledged).

### 3. **Potential Data Quality Issues**
- Despite the careful curation, the authors acknowledge that some components (e.g., OCR-corrected historical texts, public domain data) may introduce artifacts and noise. It would be useful to quantify the proportion of noisy or low-quality data post-filtering, and its effect on model performance.
- The approach relies on automatic tools for OCR and toxicity filtering; some error rates are discussed, but not extensively validated.

### 4. **Instruction/Fine-tuning Data**
- As acknowledged in the limitations, Common Corpus does not contain instruction-tuning data or datasets for task-specific fine-tuning, which limits its direct applicability for chatbots or assistant-style LLMs.

---

## Suggestions for Improvement

1. **Scaling Experiments:** Include experiments (or at least projected analysis) on how the corpus supports larger-scale model training, and whether scaling laws hold with this open dataset.
2. **Downstream Tasks:** Add evaluations on practical downstream tasks (summarization, code, QA, etc.) to demonstrate broader utility.
3. **Ablation Studies:** Conduct ablations to show the contribution of different data sources or the effect of cleaning steps.
4. **Data Quality Analysis:** Provide more quantitative analysis of data quality post-filtering, perhaps with manual inspection or annotation of sample texts.
5. **Open Science Impact:** Discuss how the corpus and tools have already enabled (or could enable) new research directions or collaborations.

---

## Recommendation

**Accept with Minor Revisions**

This paper makes a significant contribution to the LLM and NLP community by providing the largest truly open, multilingual pretraining dataset to date, along with a suite of valuable data cleaning tools. The work is timely, well-motivated, and executed to a high standard. Addressing the minor experimental and documentation issues above would further strengthen the paper’s impact.

---


## A-R1-001: Author — 模擬著者の反論

Thank you very much for your thorough and insightful review. We appreciate your recognition of our work’s significance, especially the legal, ethical, and technical challenges addressed in creating Common Corpus. Below, we respond to each of your points, and outline our planned actions for the camera-ready version.

---

### 1. Experimental Limitations

**Reviewer Concern:** Evaluation is limited to small models; unclear how Common Corpus scales to larger models; more benchmarks (especially downstream tasks) and ablations are desirable.

**Response:**  
We agree that scaling experiments and broader downstream evaluations are important for demonstrating the corpus’s full potential. Due to compute and resource constraints, our initial release focused on models up to 1.2B parameters. However, we are actively collaborating with partners to train larger models (10B+) on Common Corpus, and preliminary results are promising. If accepted, we will include initial findings and scaling analyses in the appendix or supplementary materials.

For downstream tasks, we are extending our evaluation suite to include summarization, code generation, and question answering benchmarks (e.g., XSum, HumanEval, SQuAD, and others). Results for these tasks will be added in the updated submission.

Regarding ablations, we have designed experiments to assess the impact of major data collections and cleaning steps. Space permitting, we will report key ablation results and make detailed logs available for reproducibility.

---

### 2. Novelty vs. Engineering

**Reviewer Concern:** The contribution is more engineering/curation than methodological novelty.

**Response:**  
We appreciate this observation and agree that our primary contribution is infrastructural and engineering. Our goal is to enable open, auditable, and reproducible LLM research at scale. We clarify this emphasis in the revised introduction and “Contributions” section, and highlight how our curation tools (e.g., Segmentext, OCRonos, Celadon) represent novel engineering advances for handling previously neglected open data modalities.

---

### 3. Potential Data Quality Issues

**Reviewer Concern:** Remaining noise/artifacts in the data, especially from OCR; further quantification is desirable.

**Response:**  
This is a valid concern. We will provide more quantitative analysis of post-filtering data quality, including error rates from our OCR and toxicity pipelines, and manual inspection results on sampled texts. We will also clarify in the paper the expected limitations and best practices for users who wish to select higher-quality subsets.

---

### 4. Instruction/Fine-tuning Data

**Reviewer Concern:** Lack of instruction/fine-tuning data limits applicability to assistant-style models.

**Response:**  
We agree and have stated this as a limitation. Our focus is on maximizing the size and diversity of pretraining data under open licenses, which is a necessary first step. We are in contact with other open data initiatives to encourage the development of open instruction and fine-tuning datasets, and we mention this as a key area for future work in the revised discussion.

---

### 5. Suggestions for Improvement

- **Scaling Experiments**: As noted, we are working on this and will include results where possible.
- **Downstream Tasks**: We will add evaluations on summarization, code, and QA.
- **Ablation Studies**: We will report key ablation findings.
- **Data Quality Analysis**: More quantitative and manual analyses will be included.
- **Open Science Impact**: We appreciate the suggestion and will expand the discussion on how our corpus and tools are already being used by open science initiatives (with examples, if possible).

---

We thank the reviewer again for their constructive feedback. We believe that the planned additions and clarifications will further strengthen our submission and its utility to the community.


## R1-RE-001: Reviewer 1 — 再評価

Thank you for the detailed and thoughtful rebuttal. I appreciate the authors’ responsiveness to the feedback and their concrete plans for strengthening the paper.

**1. Experimental Limitations:**  
The authors acknowledge the importance of larger-scale and downstream evaluations and indicate that they are actively working on both. Their commitment to including preliminary scaling results, downstream task benchmarks, and key ablations (as space permits) addresses my main concerns. I am satisfied with this response, though I strongly encourage including even brief summary results or a clear roadmap in the final version.

**2. Novelty vs. Engineering:**  
The authors clarify the scope and intent of their contribution, emphasizing the infrastructural and engineering novelty. I agree this is an important and valuable contribution, and the clarification in the introduction and contributions section will make the paper’s aims more transparent. This resolves my concern.

**3. Data Quality Issues:**  
The plan to provide more quantitative and manual data quality analyses, and clearer guidance for users on selecting high-quality subsets, is appreciated. This addresses the concern.

**4. Instruction/Fine-tuning Data:**  
I appreciate the authors’ acknowledgment of this limitation and their encouragement of open instruction data development. The limitation remains, but the transparency and discussion of future directions are sufficient.

**5. Suggestions for Improvement:**  
The authors have addressed each suggestion constructively and indicate willingness to expand the paper accordingly.

**Conclusion:**  
The authors’ response satisfactorily addresses my main concerns. Provided the promised additions and clarifications are made, I maintain my recommendation for acceptance. The paper will be a valuable contribution to the community.


## R2-I-001: Reviewer 2 — 初期査読

Certainly! Here is a structured peer review following your guidelines:

---

**Title:** Common Corpus: The Largest Fully Open and Multilingual Dataset for LLM Pre-Training

**Summary**

This paper introduces Common Corpus, a 2-trillion-token, fully open and multilingual dataset for large language model (LLM) pre-training. The dataset is assembled exclusively from uncopyrighted or permissively licensed sources, spanning a diverse set of domains and languages. The authors detail their data curation, filtering, and legal vetting processes, and evaluate the utility of the dataset by training two Llama-style models (350M and 1.2B) and benchmarking them against contemporary models on multilingual tasks.

---

## Evaluation

### 1. Methodological Novelty

**Strengths:**
- The paper addresses a crucial and timely challenge: the legal and ethical limitations of current LLM training datasets, especially regarding copyright and licensing.
- The authors go beyond mere data aggregation by developing a suite of novel curation and cleaning tools (e.g., Segmentext, OCRoscope, OCRerrcr, OCRonos, Celadon) specifically tailored for the unique challenges of large-scale, multilingual, and historical data.
- The legal diligence and systematic metadata/rights tracking are commendable and set a new standard for open dataset transparency.
- The release of a large, fully open, and multilingual corpus is itself a significant methodological advance, as most prior “open” corpora are English-centric or not strictly open.

**Weaknesses:**
- While the curation tools are novel and well-motivated, the paper could further clarify the comparative performance of these tools (e.g., OCRonos vs. existing OCR correction tools, Celadon vs. other toxicity classifiers) through quantitative ablation or benchmarking.
- The cleaning and deduplication steps, while described in detail, seem to rely on heuristics and internal pipelines. More systematic validation of their efficacy (e.g., error rates before/after cleaning, deduplication recall/precision) would strengthen the methodology section.

### 2. Motivation Clarity

**Strengths:**
- The motivation is exceptionally clear: the increasing legal risks and take-downs associated with closed or ambiguously licensed datasets have created a reproducibility and sustainability crisis in LLM research.
- The authors provide concrete examples of recent dataset removals and legal challenges, highlighting the urgent need for their work.
- The societal and research benefits of open, auditable, and multilingual corpora are well articulated.

**Weaknesses:**
- The “open data paradox”—that open resources are paradoxically less visible or accessible online—is mentioned but could be more rigorously defined or empirically analyzed.
- The potential limitations of open data (e.g., older, less diverse content, underrepresentation of contemporary language use) are acknowledged, but the implications for model generalization could be elaborated.

### 3. Experimental Completeness

**Strengths:**
- The evaluation is thorough in terms of dataset analysis: token/language/license distributions, quality metrics, and documentation of each sub-corpus.
- The authors benchmark their models on established multilingual tasks (MultiBLiMP, XStoryCloze, XCOPA) and compare to a range of open and closed models, including OLMo, Gemma 3, XGLM, and BLOOM.
- Results show that models trained on Common Corpus are competitive, especially in the lower parameter range, and outperform other open models in several languages and settings.

**Weaknesses:**
- The models trained are relatively small (up to 1.2B parameters). While this is understandable due to compute constraints, it limits claims about the corpus’s suitability for frontier-scale models.
- The paper would benefit from an ablation study comparing models trained on Common Corpus alone vs. Common Corpus + other open datasets, to better isolate the dataset’s contribution.
- The benchmarks focus on general language understanding. Additional downstream tasks—e.g., code generation, legal/scientific reasoning—would strengthen claims about the dataset’s domain utility.
- More insight into the impact of the cleaning/curation pipeline on downstream model performance would be valuable.

### 4. Writing Fluency

**Strengths:**
- The paper is generally well-organized and clearly written, with detailed explanations of data provenance, curation steps, and evaluation procedures.
- The inclusion of tables, figures, and appendices provides transparency and facilitates reproducibility.
- The authors explicitly document LLM usage in the preparation of the manuscript.

**Weaknesses:**
- Some sections, especially those detailing dataset provenance and cleaning tools, are overly detailed and could benefit from consolidation or moving more content to appendices.
- Occasional grammatical errors and awkward phrasings are present but do not impede understanding.
- A high-level schematic or workflow diagram would help readers grasp the pipeline at a glance.

---

## Overall Assessment

**Strengths:**
- Sets a new standard for legal clarity and transparency in LLM pre-training data.
- Demonstrates the feasibility of large-scale, open, and multilingual data collection and cleaning.
- Provides valuable tools and resources to the community with potential for broad impact.

**Weaknesses:**
- Limited to small models for empirical demonstration.
- Some aspects of methodology (especially cleaning pipeline effectiveness) could be quantitatively validated more thoroughly.
- Downstream task evaluation could be expanded.

---

## Recommendation: **Accept with Minor Revisions**

**Suggestions for Improvement:**
1. Add or reference more systematic quantitative evaluation of the custom curation/cleaning tools, especially in comparison to existing alternatives.
2. If possible, extend evaluation to more domain-specific downstream tasks (e.g., code, scientific QA, legal reasoning).
3. Consider summarizing some detailed provenance/cleaning information into appendices for improved readability.
4. Include a schematic diagram of the data pipeline and model training workflow.

---

**Conclusion:**  
This paper is an important contribution to the open LLM research ecosystem, offering a robust, transparent, and legally unencumbered resource. Its methodological diligence and commitment to openness are exemplary. Some minor improvements in experimental validation and presentation would further strengthen the work. I recommend acceptance after minor revisions.


## A-R2-001: Author — 模擬著者の反論

Thank you for your thorough and constructive review of our paper. We appreciate your recognition of the novelty, rigor, and potential impact of Common Corpus, as well as your thoughtful suggestions for improvement. Below, we address each of your major points:

---

**1. Methodological Novelty: Need for Comparative Evaluation of Curation Tools**

*Reviewer’s concern:*  
You note that quantitative ablation or benchmarking of our custom curation tools (e.g., OCRonos, Celadon) would strengthen the methodology section.

*Response:*  
We agree that quantitative comparisons would further validate the effectiveness of our tools. In the final version, we will expand Appendix F to include comparative results for OCRonos against widely used OCR correction tools (e.g., Tesseract, Google Vision OCR) on a held-out, multilingual evaluation set. For Celadon, we will provide ROC-AUC and F1 comparisons on a subset of our data vs. Perspective API and Detoxify, acknowledging potential domain gaps. Where computational resources are a bottleneck, we will provide qualitative or small-scale quantitative results and discuss the respective trade-offs.

---

**2. Cleaning and Deduplication Validation**

*Reviewer’s concern:*  
You suggest more systematic validation of the deduplication and cleaning pipeline.

*Response:*  
This is a valid concern. We will include in Appendix F additional statistics on detected duplicates (pre/post-deduplication), and error rates for cleaning steps based on manual spot checks and automated metrics (e.g., reduction in OCR error rates, toxicity prevalence before/after filtering). We will also clarify the heuristic choices and provide more explicit caveats regarding their limitations.

---

**3. Motivation Clarity: Open Data Paradox and Model Generalization**

*Reviewer’s concern:*  
You mention that the "open data paradox" could be more rigorously defined, and the limitations of open data for generalization elaborated.

*Response:*  
Thank you for highlighting this. We will revise Section 2 to provide a more precise definition of the “open data paradox,” including illustrative statistics on discoverability and indexing of open vs. closed resources. We will also add a short discussion in the Limitations section about possible underrepresentation of contemporary language and its potential effects on model generalization, referencing related work where applicable.

---

**4. Experimental Completeness**

a. *Small Model Sizes*  
*Reviewer’s concern:* Limited to 1.2B parameters; limits claims for frontier-scale applicability.

*Response:*  
We acknowledge this limitation, which is primarily due to resource constraints. To clarify, we will explicitly state this in the main text and limitations, and position our results as a strong lower-bound demonstration of the dataset’s utility.

b. *Ablation Study*  
*Reviewer’s concern:* Comparing models trained on Common Corpus alone vs. Common Corpus + other open datasets.

*Response:*  
This is an excellent suggestion. While full-scale ablation is challenging due to compute constraints, we will report preliminary results from small-scale experiments (e.g., fine-tuning with/without Common Corpus on a held-out validation set) and include these in Appendix G.

c. *Broader Downstream Evaluation*  
*Reviewer’s concern:* More tasks (e.g., code generation, legal/scientific reasoning) would strengthen claims.

*Response:*  
We agree. We will add a code generation benchmark (e.g., HumanEval or MBPP) and, if feasible, include results on a legal QA or scientific QA task using available open benchmarks. These results will be integrated into Section 6 and/or Appendix G.

d. *Impact of Cleaning on Downstream Performance*  
*Reviewer’s concern:* More insight on the effect of curation steps on model quality.

*Response:*  
We will report, for a subset of the data, the downstream performance of models trained on raw vs. cleaned data (where feasible) and summarize qualitative differences observed during evaluation.

---

**5. Writing Fluency and Presentation**

*Reviewer’s concern:*  
Some sections are overly detailed; suggest moving content to appendices. A schematic pipeline diagram is recommended.

*Response:*  
We appreciate this feedback. In the camera-ready version, we will consolidate detailed provenance and tool descriptions, moving more technical content to appendices. We will also add a workflow diagram summarizing our data pipeline and main processing steps in Section 5.

---

**Conclusion**

Thank you again for your positive assessment and actionable feedback. We are committed to incorporating these improvements and believe they will further enhance the clarity, rigor, and impact of our work.

If there are any additional points that require clarification, we are happy to address them.


## R2-RE-001: Reviewer 2 — 再評価

Thank you to the authors for the comprehensive and thoughtful rebuttal. I appreciate the detailed and specific commitments made to address each of my concerns. Below I address each major point from my original review in light of your responses:

---

**1. Comparative Evaluation of Curation Tools**
- The authors have committed to expanding Appendix F with quantitative and qualitative comparisons between their tools (e.g., OCRonos, Celadon) and established baselines. This is a substantial and welcome improvement. The plan to include ROC-AUC, F1, and qualitative results where necessary is reasonable, given resource constraints.  
**Resolution:** Satisfied, provided these additions are included in the revised paper.

**2. Validation of Cleaning and Deduplication**
- The authors will now include statistics and error rates pre- and post-processing, and explain heuristic choices more explicitly. This should address concerns regarding the rigor and transparency of the cleaning pipeline.  
**Resolution:** Satisfied.

**3. Motivation Clarity**
- A clearer definition of the “open data paradox,” with supporting statistics and a discussion of generalization limitations, will improve the paper’s conceptual framing.  
**Resolution:** Satisfied.

**4. Experimental Completeness**
  - **a. Small Model Sizes:** Authors have clarified the limitation and will make this explicit in the paper.  
  **Resolution:** Satisfied.
  - **b. Ablation Study:** Authors will add preliminary ablation results in the appendix.  
  **Resolution:** Satisfied, acknowledging computational limits.
  - **c. Broader Downstream Evaluation:** Authors commit to adding code generation and, if feasible, legal/scientific QA tasks.  
  **Resolution:** Satisfied.
  - **d. Impact of Cleaning:** Authors will report the effect of cleaning on downstream performance for a subset of data.  
  **Resolution:** Satisfied.

**5. Writing Fluency and Presentation**
- The authors will move detailed descriptions to appendices and add a pipeline diagram.  
**Resolution:** Satisfied.

---

**Overall Assessment After Rebuttal**

The authors have responded constructively and specifically to every point. Assuming the promised additions and clarifications are incorporated, all of my concerns are resolved. I continue to recommend acceptance of the paper, and I look forward to the revised version.


## R3-I-001: Reviewer 3 — 初期査読

Certainly! Here is a peer review according to your guidelines, thoroughly addressing the provided paper content.

---

# Peer Review for "Common Corpus: The Largest Open Multilingual Dataset for LLM Pre-training"

## Summary

This paper introduces **Common Corpus**, a 2-trillion-token multilingual, multi-domain, and fully open dataset for large language model (LLM) pre-training. The authors detail the legal and technical challenges of assembling open data at scale, describe the curation and cleaning tools they developed, and demonstrate the corpus's utility by training and evaluating two small LLMs (350M and 1.2B parameters). The paper also provides extensive documentation and reproducible cleaning tools, aiming to set a new standard for open LLM development.

---

## Strengths

### 1. **Motivation Clarity**

- **Timeliness and Relevance:** The introduction gives a lucid and timely account of the legal and ethical challenges facing LLM training, especially the growing restrictions on web data and copyright issues. The motivation for a truly open, auditable, and multilingual corpus is well established.
- **Societal Impact:** The authors convincingly argue that their work addresses a pressing need for reproducible, legally compliant research artifacts and will facilitate open science in LLMs.

### 2. **Methodological Novelty**

- **Data Collection:** The approach is novel in its strict adherence to open licensing and in its broad inclusion of non-web-crawl sources (government, culture, science, code, semantic data).
- **Multilingual Focus:** The extensive language coverage (with >10B tokens in nine languages and robust representation for many more) is a significant advance over prior open datasets, which are mostly English-centric.
- **Cleaning and Curation Tools:** The paper introduces several custom tools (Segmentext, OCRoscope, OCRerrcr, OCRonos, Celadon) for segmentation, OCR correction, toxicity filtering, and PII removal, tailored for historical, multilingual, and noisy data. These are well motivated, described, and open-sourced.

### 3. **Experimental Completeness**

- **Corpus Analysis:** The authors provide detailed statistics on data composition, licensing, domains, languages, and quality metrics across the corpus. Tables and figures are used effectively.
- **Model Training and Benchmarks:** Two LLMs (350M and 1.2B) are trained on the corpus and evaluated on multiple multilingual benchmarks (MultiBLiMP, XStoryCloze, XCOPA), with comparisons to strong open and closed baselines (Gemma, XGLM, BLOOM, OLMo).
- **Competitive Results:** The models trained on Common Corpus perform on par with or better than similar-scale open models, especially in multilingual settings, confirming the corpus’s quality.

### 4. **Writing Fluency and Reproducibility**

- **Clarity:** The writing is clear, well structured, and demonstrates a deep awareness of current issues in the LLM community.
- **Documentation:** The paper provides extensive appendices with provenance, data breakdowns, and methodology details, as well as links to code and tools, facilitating reproducibility.
- **Transparency:** Limitations and caveats are discussed openly.

---

## Weaknesses

### 1. **Methodological and Experimental Gaps**

- **Limited Model Size:** Only small models (up to 1.2B parameters) are trained. It remains unproven whether the corpus supports state-of-the-art performance for larger models.
- **Instruction Tuning and Downstream Tasks:** The corpus is not designed for instruction tuning or specialized tasks, and no experiments are provided in these areas. This limits the demonstrated applicability.
- **Ablation on Curation Tools:** The effectiveness of novel cleaning tools (e.g., OCRonos, Celadon) is described, but there is no quantitative ablation to show their direct impact on model performance or data quality.

### 2. **Originality Claims**

- **Overlap with Prior Work:** While the dataset is clearly unique in its combination of openness, scale, and multilinguality, prior datasets have addressed parts of this problem (e.g., KL3M for open government data, Common Pile for open English data). The paper could further clarify what new kinds of research questions are now enabled.
- **Novelty of Cleaning Tools:** Some tools (e.g., OCR correction, toxicity detection) build on existing techniques. The paper would benefit from a more explicit comparison with prior approaches and discussion of what is fundamentally new.

### 3. **Clarity and Organization**

- **Dense Appendices:** Much of the technical detail is in the appendices, which may hinder readability for some audiences. Some methodology (e.g., specifics of curation pipelines) could be summarized in the main text.
- **Table/Number Overload:** There are many tables and figures; some could be better integrated or summarized to highlight key points.

---

## Suggestions for Improvement

1. **Scaling Experiments:** Training larger LLMs on Common Corpus—even as a pilot or through collaboration—would provide stronger evidence of its utility for cutting-edge research.
2. **Ablation Studies:** Include experiments quantifying the effect of each cleaning/curation tool on downstream model performance or dataset quality.
3. **Instruction Data:** Discuss prospects or preliminary efforts for building instruction-tuning or task-specific subsets from the corpus.
4. **Comparison with Prior Cleaning Pipelines:** Provide more detailed comparisons with existing cleaning/curation frameworks and clarify unique contributions.
5. **Main Text Integration:** Summarize the most important technical methods and findings from the appendices in the main text for accessibility.

---

## Recommendation

**Strong Accept.**  
This is an important, timely, and technically solid contribution to the LLM ecosystem. Despite some limitations in experimental scale and ablations, the work’s societal relevance, technical rigor, and commitment to open science make it a valuable resource for the community.

---

## Minor Comments

- Proofreading would help catch a few minor typographical errors.
- Consider visualizing the overlap between Common Corpus and other datasets to emphasize uniqueness.
- More discussion on sustainability and governance of the corpus (future updates, community contributions) would be welcome.

---

**Overall, this paper sets a new standard for open LLM pre-training datasets and associated curation tools.**


## A-R3-001: Author — 模擬著者の反論

Certainly! Here is a detailed rebuttal addressing the reviewer’s comments point by point:

---

We thank the reviewer for their thorough and constructive feedback, and for the recognition of our work’s significance, technical rigor, and commitment to open science. Below, we address each of the reviewer’s comments in detail.

---

**1. Methodological and Experimental Gaps**

- **Limited Model Size:**  
  *Reviewer Comment*: Only small models (up to 1.2B parameters) are trained. It remains unproven whether the corpus supports state-of-the-art performance for larger models.

  *Response*: We agree that demonstrating the corpus’s effectiveness with larger models would be valuable. Due to resource constraints in this initial release, we focused on small models to ensure timely evaluation and reproducibility. We are actively seeking collaborations with academic and industrial partners to scale up experiments. In future work, we plan to release results from training larger models and will update the community accordingly.

- **Instruction Tuning and Downstream Tasks:**  
  *Reviewer Comment*: The corpus is not designed for instruction tuning or specialized tasks, and no experiments are provided in these areas.

  *Response*: This is correct. Our focus in this work was on foundational pretraining. However, we recognize the importance of instruction tuning and downstream evaluation. As highlighted in our limitations, we see Common Corpus as a starting point for further instruction-tuning dataset construction. We are currently annotating subsets for instruction-style tasks and will share these resources and their evaluation results in a follow-up.

- **Ablation on Curation Tools:**  
  *Reviewer Comment*: No quantitative ablation to show the direct impact of cleaning tools on model performance or data quality.

  *Response*: We appreciate this suggestion. In this first version, we prioritized clean pipeline delivery and overall model validation. To address this in future versions, we are designing ablation studies (e.g., with/without OCR correction or toxicity filtering) and will include these results in a revision or as a supplementary technical note.

---

**2. Originality Claims**

- **Overlap with Prior Work:**  
  *Reviewer Comment*: More clarity on what new research is enabled by this corpus, given overlap with prior datasets.

  *Response*: Thank you for the suggestion. We will clarify in the revision that the unique combination of scale, full open licensing, and multilingual/multidomain coverage enables, for the first time, the development and release of fully open, reproducible, and auditable large models across many languages, which was not possible with previous datasets (which were either not fully open, not multilingual, or not multi-domain). We will add a section highlighting novel research directions—such as open-source cross-lingual model evaluation, alignment, and historical language modeling—now made possible.

- **Novelty of Cleaning Tools:**  
  *Reviewer Comment*: Some tools build on existing techniques; explicit comparison to prior approaches is needed.

  *Response*: We agree that more explicit comparison is beneficial. We will add a discussion contrasting our tools with existing OCR correction, segmentation, and toxicity filtering pipelines, emphasizing how our models are tailored for historical and noisy data, multilinguality, and computational efficiency at scale.

---

**3. Clarity and Organization**

- **Dense Appendices:**  
  *Reviewer Comment*: Some methods detailed in the appendix could be summarized in the main text.

  *Response*: We appreciate this feedback and will move key points—such as the cleaning pipeline overview and core tool descriptions—into the main paper, and improve cross-referencing for clarity.

- **Table/Number Overload:**  
  *Reviewer Comment*: Summarize or better integrate tables/figures.

  *Response*: We will revise the manuscript to highlight the most relevant statistics in the main text and consider moving some of the granular tables to supplementary material. In the revision, we will also add summary figures to synthesize key information.

---

**4. Suggestions for Improvement**

- **Scaling Experiments:** See above; we are planning larger-scale experiments.
- **Ablation Studies:** As above, we will include ablations in future versions.
- **Instruction Data:** We are annotating subsets and will release instruction-tuned benchmarks.
- **Comparison with Prior Pipelines:** To be added in the revision.
- **Main Text Integration:** Will be improved as noted.

---

**Minor Comments**

- We will proofread the revised version for minor typographical errors.
- We appreciate the suggestion to visualize overlap with other datasets and will add an appropriate figure.
- Regarding sustainability and governance: we are working with open science consortia to ensure ongoing updates and will include a paragraph describing governance plans.

---

**Conclusion**

We thank the reviewer again for their constructive feedback and recognition of our contribution. We are confident that the planned improvements will address the concerns raised and further strengthen the paper.

---


## R3-RE-001: Reviewer 3 — 再評価

Certainly! Here is a follow-up review, reconsidering my initial comments in light of the author’s rebuttal:

---

**Review Update after Author Rebuttal**

I appreciate the authors’ detailed and constructive response to the initial review. Below I reconsider each of my main concerns:

---

### 1. **Limited Model Size**

**Original Concern:** Only small models (up to 1.2B) are trained, so the corpus’s utility for larger LLMs remains unproven.

**Response Assessment:**  
The authors acknowledge this limitation, clarify that it was due to resource constraints, and indicate active efforts to enable larger-scale experiments in collaboration with partners. While new large-model results are not yet available, the acknowledgement and concrete plans for future work are reasonable given the context. This satisfactorily addresses my concern for the current submission, though I look forward to future results.

---

### 2. **Instruction Tuning and Downstream Tasks**

**Original Concern:** No demonstration of instruction-tuning or downstream fine-tuning utility.

**Response Assessment:**  
The authors clearly state that this was outside the scope of the initial work, but they are already annotating subsets for instruction-style tasks and plan to release these. This is a fair and transparent approach, and I am satisfied with the response.

---

### 3. **Ablation on Curation Tools**

**Original Concern:** No quantitative ablation showing the direct impact of their custom cleaning tools.

**Response Assessment:**  
The authors acknowledge this and commit to including such ablations in future releases. Given the immense scale of the work and the need to prioritize pipeline completeness, this is understandable. I encourage the authors to follow through on this, but the response is satisfactory for now.

---

### 4. **Originality Claims and Comparison with Prior Work**

**Original Concern:** The paper could further clarify what new research is uniquely enabled and more explicitly compare their cleaning tools to previous work.

**Response Assessment:**  
The authors agree and propose to revise the paper to better articulate the unique research enabled by their resource and to add explicit comparisons with prior approaches. This will improve clarity and highlight their contributions; I consider this concern resolved given the planned revisions.

---

### 5. **Clarity and Organization**

**Original Concern:** Key methods are relegated to appendices; table/figure integration could be improved.

**Response Assessment:**  
The authors accept this feedback and will move summaries of key methods into the main text, better cross-reference materials, and consolidate tables/figures. This addresses my concern.

---

### 6. **Minor Comments**

**Original Concern:** Minor typos, dataset overlap visualization, and sustainability/governance discussion.

**Response Assessment:**  
The authors confirm they will address these in revision. No further action needed.

---

### **Overall Assessment**

The author rebuttal is thorough, acknowledges valid concerns, and makes concrete commitments to strengthen the paper. The explanations for current limitations (e.g., model size, lack of ablations) are reasonable given the project’s scale. I am satisfied with the responses and look forward to seeing these improvements in the final version.

**Final Recommendation:**  
My assessment remains **Strong Accept**. The authors’ proactive and transparent approach to feedback further increases my confidence in the value and integrity of this work.
