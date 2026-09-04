# DIG4EL — Digital Inferential Grammar for Endangered Languages

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

DIG4EL is a research application for creating reviewable grammar-learning material about under-documented and endangered languages. It brings together three kinds of evidence:

- human-entered Conversational Questionnaire (CQ) translations and concept annotations;
- existing sentence pairs and reference documents;
- typological evidence derived from WALS and Grambank.

It then makes its reasoning visible enough for a linguist, teacher, or language caretaker to inspect, correct, and approve before producing a grammar lesson or a technical grammar sketch. The current runtime version is **1.1.2**.

> **Important:** DIG4EL assists documentation; it does not establish grammatical facts automatically. Its inferences, retrieval results, and generated lessons can be wrong or incomplete and must be reviewed by a qualified person with appropriate authority over the language data.

## What this project is — and is not

DIG4EL is useful when a team wants to turn structured elicitation, corpus examples, and existing descriptions into editable teaching or descriptive material.

It is **not**:

- an automatic speech-recognition or audio-analysis system. In this project, “transcription” means a human-entered translation plus word-to-concept annotation; the included audio file is home-page media only.
- a conventional REST API or packaged Python library. The Streamlit application and its local modules are run from this repository.
- a production-hardened multi-tenant service. It is a stabilized research prototype with a file-backed runtime volume and operator-managed access controls.
- a replacement for consent, community governance, linguistic analysis, or expert editorial review.

## Contents

- [Quick start](#quick-start)
- [Main workflow](#main-workflow)
- [Architecture](#architecture)
- [Installation and configuration](#installation-and-configuration)
- [Language workspaces and data formats](#language-workspaces-and-data-formats)
- [How the inference works](#how-the-inference-works)
- [Code and library guide](#code-and-library-guide)
- [Advanced pages, operations, and evaluation](#advanced-pages-operations-and-evaluation)
- [Data governance, license, and citation](#data-governance-license-and-citation)

## Quick start

The landing page can be opened locally with Python 3.10 and a writable runtime folder. Run all commands from the repository root: several modules use repository-relative paths.

~~~bash
git clone https://github.com/alterfero/dig4el.git
cd dig4el

python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# A fresh clone has no runtime data volume. This is enough for the landing page.
mkdir -p ld/storage
cp grammar_seeds/grammar_seeds.json ld/storage/grammar_seeds.json

streamlit run home.py
~~~

Open the local address printed by Streamlit, normally http://localhost:8501. The full source dashboard, CQ editor, inference page, and generation page require the additional runtime configuration described below.

The requirements are pinned and include a spaCy model downloaded directly from GitHub, so installation needs internet access. The optional local retrieval features download the SentenceTransformer model on first use. On Windows, create and activate the virtual environment with the equivalent PowerShell commands.

## Main workflow

The supported v1 route through the interface is:

1. Open [home.py](home.py), then select **Source dashboard**.
2. In [pages/dashboard.py](pages/dashboard.py), choose a language workspace and add or review sources.
3. Create, import, or edit a human-annotated Digital Conversational Questionnaire (DCQ) in [pages/record_cq_transcriptions.py](pages/record_cq_transcriptions.py).
4. Run [pages/infer_from_knowledge_and_cqs.py](pages/infer_from_knowledge_and_cqs.py), inspect the evidence and inferred grammar priors, then approve the result.
5. Optionally add sentence-pair corpora and public reference documents in the dashboard. Sentence-pair augmentation is a separate, asynchronous OpenAI/Redis workflow.
6. In [pages/generate_grammar.py](pages/generate_grammar.py), choose the available evidence sources and create either a learner-oriented lesson or a linguist-oriented grammar sketch. Save the JSON and optionally download a DOCX version. The current generator requires a restored runtime volume; see the bootstrap limitation below.

The progression matters: generation is much more useful after the CQ inference has produced inspected grammar priors and pseudo-glossed examples.

### A plain-language view

Think of DIG4EL as a careful research notebook with a drafting assistant:

- A fieldworker or language expert supplies examples and says which target-language words realize which meanings.
- Deterministic code looks for patterns that can actually be observed in those annotations.
- WALS and Grambank supply population-level expectations when local evidence is sparse.
- The system presents an uncertain, inspectable hypothesis rather than a definitive answer.
- Optional language-model tools help organize, retrieve, and draft from the approved material.

## Architecture

DIG4EL is a filesystem-backed Streamlit application. There is no separate application database or HTTP API service; per-language source material and outputs live in a writable runtime volume.

~~~mermaid
flowchart LR
    UI[Streamlit interface]
    CQ[Human CQ translation and<br/>concept annotation]
    PAIRS[Sentence pairs]
    DOCS[Reference documents]
    KG[Concept-linked<br/>knowledge graph]
    OBS[Deterministic CQ observers]
    TYPO[WALS and Grambank<br/>priors and CPTs]
    INF[Approximate Bayesian<br/>inference]
    QUEUE[Redis and RQ worker]
    LLM[OpenAI agents and<br/>File Search]
    GEN[Lesson or grammar-sketch<br/>generation]
    OUT[JSON, DOCX, traces]

    UI --> CQ
    UI --> PAIRS
    UI --> DOCS
    CQ --> KG --> OBS --> INF
    TYPO --> INF
    PAIRS --> QUEUE --> LLM
    DOCS --> LLM
    INF --> GEN
    LLM --> GEN
    PAIRS --> GEN
    GEN --> OUT
~~~

The three evidence streams remain distinct:

| Evidence stream | What it contributes | Main destination |
| --- | --- | --- |
| DCQ translations | Annotated examples, direct grammatical observations, and inferred typological priors | **cq/cq_knowledge/cq_knowledge.json** |
| Sentence pairs | Corpus-like examples, optional semantic descriptions, keywords, and manually corrected word/concept links | **sentence_pairs/augmented_pairs/** |
| Reference documents | Retrieved descriptive evidence from explicitly uploaded documents | OpenAI File Search plus **descriptions/sources/** |

### Key terms

| Term | Meaning in DIG4EL |
| --- | --- |
| **CQ / DCQ** | A structured, contextualized conversational questionnaire. A DCQ is the DIG4EL-adapted form used to elicit comparable grammatical translations. |
| **Concept annotation** | A human link from a target-language word or sequence to an expected semantic concept in the questionnaire. |
| **Knowledge graph** | The merged representation of canonical CQ semantics and a language’s annotated translations. |
| **Observer** | Deterministic code that converts annotated examples into evidence for a specific grammatical parameter. |
| **Grammar prior** | A known, observed, or inferred WALS/Grambank-compatible grammatical value with a model confidence. |
| **Alterlingua** | DIG4EL’s partial pseudo-gloss: target forms annotated with language-independent concepts and internal/relational particularization. |
| **Language workspace** | The persistent folder containing one language’s source files, metadata, intermediate products, and outputs. |

## Installation and configuration

### Prerequisites

| Requirement | Why it is needed |
| --- | --- |
| Python **3.10+** | The included **.python-version** is 3.10, and source code uses modern Python typing syntax that requires Python 3.10 or later. |
| A writable persistent volume | The application writes all language workspaces under a **storage** directory. A clone alone does not contain these records. |
| Internet access during installation | Pip downloads pinned dependencies and the spaCy wheel referenced in **requirements.txt**. |
| OpenAI API credential | Required for practical use of the current source dashboard, document vector stores/File Search, LLM sentence augmentation, generation, and lesson judging. |
| Redis plus an RQ worker | Required only to run asynchronous sentence-pair augmentation. |
| Graphviz system executable, optional | Needed only for DOCX exports that render a word–concept graph. The Python package alone may not provide the **dot** executable. |

The application explicitly reads **OPEN_AI_KEY**. If that value is absent, the installed OpenAI SDK can fall back to **OPENAI_API_KEY**; configure **OPEN_AI_KEY** for predictable DIG4EL behavior.

### Why a fresh clone is not a complete deployment

The **ld/** directory is intentionally ignored by Git because it contains language data, credentials, generated outputs, and remote-service identifiers. The code expects the parent path held by **RAILWAY_VOLUME_MOUNT_PATH** to contain a **storage/** subdirectory. When the variable is not set, that parent path is **./ld**.

For an existing installation, restore an authorized backup of the whole runtime volume rather than attempting to recreate individual language folders. This preserves language data, authentication configuration, outputs, and document-vector-store metadata.

For a new local development volume, create the minimal shared files below.

~~~text
ld/storage/
  languages.json
  auth_config.yaml
  grammar_seeds.json
  feedback.json
  <language workspace created by the dashboard or create_ld()>
~~~

First copy the seed guidance:

~~~bash
mkdir -p ld/storage
cp grammar_seeds/grammar_seeds.json ld/storage/grammar_seeds.json
printf '[]\n' > ld/storage/feedback.json
~~~

Then create **ld/storage/languages.json**. A glottocode is preferred; a trailing plus sign marks a provisional identifier.

~~~json
{
  "Example language": "example+"
}
~~~

Finally create **ld/storage/auth_config.yaml**. Protected pages load this file before they offer the guest path, so it is required even if the first user will choose “Use without logging in”.

~~~yaml
cookie:
  name: dig4el_auth
  key: replace-with-a-long-random-secret
  expiry_days: 30

credentials:
  usernames:
    admin:
      email: admin@example.org
      name: Local administrator
      password: replace-with-a-bcrypt-hash
      role: admin
      caretaker: []
      failed_login_attempts: 0
~~~

The application enables automatic hashing, but storing a bcrypt hash is safer than storing a plain password. After installing dependencies, generate one without echoing the password:

~~~bash
python -c 'from getpass import getpass; from streamlit_authenticator.utilities.hasher import Hasher; print(Hasher.hash(getpass("New password: ")))'
~~~

Paste the resulting hash into the YAML file. Keep this configuration and the runtime volume out of version control.

> **Generator bootstrap limitation:** a brand-new volume is enough to open the landing page and begin configuring the dashboard, but it cannot currently load [pages/generate_grammar.py](pages/generate_grammar.py). [libs/grammar_generation_utils.py](libs/grammar_generation_utils.py) has an import-time development call that reads Tahitian CQ knowledge, and the generation page initially opens the Tahitian workspace before its language selector. For generation, restore an authorized, existing runtime-volume snapshot that includes the Tahitian workspace and CQ knowledge, or remove that development dependency in code first.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| **RAILWAY_VOLUME_MOUNT_PATH** | **./ld** | Parent directory of the persistent **storage/** folder. Set it to a shared mounted-volume path in hosted deployments. |
| **AUTH_CONFIG_PATH** | **$RAILWAY_VOLUME_MOUNT_PATH/storage/auth_config.yaml** | Overrides the path to the authentication YAML. Useful for keeping credentials outside the project directory. |
| **AUTH_COOKIE_KEY** | Value from the YAML | Overrides the cookie encryption/signing key. Use a deployment secret. |
| **OPEN_AI_KEY** | none | DIG4EL’s explicit API-key setting for OpenAI agents, vector stores, File Search, generation, and judging. |
| **OPENAI_API_KEY** | none | OpenAI SDK fallback when **OPEN_AI_KEY** is not set; use the explicit variable above for predictable application configuration. |
| **REDIS_URL** | **redis://localhost:6379** | Redis connection for background sentence augmentation. |
| **QUEUE_NAME** | **sentence** | Queue selected by enqueueing code. See the queue caveat below. |
| **CODE_LOCATION** | **non-mac** | Chooses the worker class: **mac** uses RQ SpawnWorker; **railway** uses Worker. |

Use real environment variables or your host’s secret manager. The application reads operating-system environment variables and does not call python-dotenv, so a local **.env** file is not loaded automatically. If a host or Streamlit secrets facility is used, ensure it exposes **OPEN_AI_KEY** and the other required values to the running process; the application does not call **st.secrets** directly.

### Full local stack

Run the following three processes when you want LLM-based sentence-pair augmentation. They must share the same runtime-volume location and relevant secrets.

Terminal 1 starts Redis. Use an existing Redis installation, or, if Docker is already available:

~~~bash
docker run --rm --name dig4el-redis -p 6379:6379 redis
~~~

Verify that it responds:

~~~bash
redis-cli ping
~~~

Terminal 2 starts the worker:

~~~bash
source .venv/bin/activate
export RAILWAY_VOLUME_MOUNT_PATH="$PWD/ld"
export REDIS_URL="redis://localhost:6379"
export OPEN_AI_KEY="replace-with-your-key"
export CODE_LOCATION="mac"
python rq_worker.py
~~~

Terminal 3 starts the web interface:

~~~bash
source .venv/bin/activate
export RAILWAY_VOLUME_MOUNT_PATH="$PWD/ld"
export OPEN_AI_KEY="replace-with-your-key"
streamlit run home.py
~~~

On non-macOS local systems, the current worker falls back to SpawnWorker after printing a warning. In a Railway-oriented deployment, set **CODE_LOCATION=railway**.

> **Queue caveat:** **rq_worker.py** currently listens to the literal **sentence** queue even though it defines **QUEUE_NAME**. Keep **QUEUE_NAME=sentence** unless the worker is changed to use that environment variable too.

## Language workspaces and data formats

### Persistent layout

[libs/file_manager_utils.py](libs/file_manager_utils.py) defines the workspace contract in **create_ld()**. Each language is stored independently:

~~~text
ld/storage/
  languages.json
  auth_config.yaml                  # secret, not tracked
  grammar_seeds.json
  feedback.json                   # initialize as an empty JSON array for a new volume
  traces/
  conveqs/
  <language>/
    info.json                       # source/output metadata and remote vector-store ID
    delimiters.json
    batch_id_store.json
    cq/
      cq_translations/
      cq_knowledge/
        cq_knowledge.json
    descriptions/
      sources/
      embeddings/
    sentence_pairs/
      pairs/
      augmented_pairs/
      vector_ready_pairs/
      vectors/
    conveqs/
    monolingual/
    outputs/
~~~

Treat this directory as research data, not a cache. Back it up before using the administrator file explorer or reset controls. A local copy of a language workspace does not automatically recreate its remote OpenAI vector store; its ID is recorded in **info.json**.

### Input and output contracts

| Material | Minimal format or location | Notes |
| --- | --- | --- |
| Sentence pairs | CSV with **source** and **target** columns, or a JSON list containing those keys | Templates are in [templates/](templates/). |
| FLEx / Pangloss data | XML imported through [libs/file_format_utils.py](libs/file_format_utils.py) | Helpers convert FLEx gloss XML and Pangloss XML to sentence-pair JSON. |
| DCQ translations | JSON under **cq/cq_translations/**, usually created through the editor or XLSX workflow | A sentence holds the source prompt, human target translation, concept-word links, and comments. |
| CQ knowledge | **cq/cq_knowledge/cq_knowledge.json** | Created after inference is reviewed and approved. It contains **sentences** and **grammar_priors**. |
| Reference documents | **descriptions/sources/** | Upload only material that can lawfully and appropriately be processed. |
| Augmented sentence pairs | **sentence_pairs/augmented_pairs/** | Add semantic descriptions, keywords, translation concepts, and optional human word connections. |
| Outputs | **outputs/** as JSON and, for supported output types, DOCX | The names intentionally mark lessons as unverified. |

An augmented pair commonly evolves from:

~~~json
{
  "source": "A sentence in the lingua franca",
  "target": "A sentence in the target language"
}
~~~

to a record with fields such as **description**, **keywords**, **key_translation_concepts**, and **word connections**. The dashboard accepts and normalizes the simple source/target form; a caretaker should review any LLM-created fields and annotations before treating them as evidence.

### Data bundled with the repository

| Location | Role |
| --- | --- |
| [data/](data/) | Shared concept ontology, delimiters, legacy knowledge-graph fixtures, and supporting data. |
| [questionnaires/](questionnaires/) | Canonical questionnaire dialogs used by the older/current CQ workflows. |
| [conveqs/canonical_cqs.json](conveqs/canonical_cqs.json) | ConveQs-compatible canonical CQ catalog. |
| [templates/](templates/) | Sentence-pair and CQ spreadsheet templates. |
| [grammar_seeds/grammar_seeds.json](grammar_seeds/grammar_seeds.json) | Guidance supplied to the lesson/sketch generation workflow. |
| [external_data/wals-master/](external_data/wals-master/) and [external_data/grambank-1.0.3/](external_data/grambank-1.0.3/) | Vendored source datasets. |
| **external_data/wals_derived/**, **external_data/grambank_derived/**, and cross-dataset CPT JSON files | Precomputed lookup tables and conditional-probability artifacts used at runtime. |
| [external_data/glottolog_derived/](external_data/glottolog_derived/) | Local language metadata and lookup support. |

Do not remove the derived typological JSON files if you intend to use inference: they are runtime data, not disposable build output.

## How the inference works

### 1. Human annotation creates inspectable local evidence

A canonical CQ supplies source sentences, concepts, and a semantic graph. The DCQ editor asks a human to provide target-language translations and to associate forms with concepts. [libs/knowledge_graph_utils.py](libs/knowledge_graph_utils.py) merges the canonical CQ and those annotations into a knowledge graph.

The shared tokenizer in [libs/stats.py](libs/stats.py) uses configurable delimiters and assigns repeated tokens positional suffixes such as **word_2**. This lets an annotation distinguish repeated forms in the same sentence.

### 2. Observers make deterministic grammatical claims

[libs/cq_observers.py](libs/cq_observers.py) contains functions that inspect annotated positions and return both human-readable evidence and an agent-ready count vector indexed by WALS or Grambank value ID. The current inference page activates observers for, among other topics:

- order of subject, object, and verb;
- order of subject and verb;
- adjective/noun, demonstrative/noun, and relative-clause/noun order;
- inclusive/exclusive pronouns;
- person/gender distinctions in independent pronouns;
- semantic-role marking on pronominal core arguments.

To add a new directly observable construction, add an observer with the same evidence/count interface and register it in the **observed_params** mapping in [pages/infer_from_knowledge_and_cqs.py](pages/infer_from_knowledge_and_cqs.py). That preserves the reviewable path from annotated example to inference input.

### 3. WALS and Grambank supply prior distributions and associations

[libs/wals_utils.py](libs/wals_utils.py), [libs/grambank_utils.py](libs/grambank_utils.py), and [libs/grambank_wals_utils.py](libs/grambank_wals_utils.py) load local language/parameter/value lookup tables and estimate conditional associations between feature values.

For a selected parameter, a **LanguageParameter** begins with an empirical distribution over comparable WALS or Grambank languages. The WALS pipeline uses regularization and minimum-support checks; the Grambank pipeline uses smoothing and minimum-attestation checks. Cross-dataset tables allow a WALS value to inform a Grambank value, and conversely.

These are priors derived from documented languages. They are useful when data are missing, but they are not evidence that a particular target language has a feature.

### 4. Approximate belief propagation combines evidence

[libs/general_agents.py](libs/general_agents.py) implements the principal inference engine:

1. A direct CQ observation updates the categorical prior with a symmetric multinomial observation model, computed in log space for numerical stability.
2. Strong or manually known evidence can lock a parameter.
3. Selected parameters form a graph whose edges are conditional-probability matrices.
4. A **GeneralAgent** repeatedly sends and receives damped messages around that graph. Because the graph contains loops, this is loopy belief propagation: an approximation, not an exact posterior calculation.
5. The page records belief histories and surfaces low-entropy results for human review.

The stored confidence is derived from the model’s normalized entropy. It should be read as an internal uncertainty signal, **not** as a calibrated probability that a grammatical claim is true.

### 5. Parameter selection limits the frontier

[libs/ga_param_selection_utils.py](libs/ga_param_selection_utils.py) turns WALS, Grambank, and cross-dataset conditional-probability tables into a directed NetworkX graph. It takes strong values as seeds, follows sufficiently probable conditional edges, and ranks candidates by:

~~~text
score(candidate) =
  max over predecessor of
  P(candidate | predecessor) × belief(predecessor)
~~~

The reusable helper defaults are deliberately permissive; the current inference page supplies stricter settings, including a high conditional-probability threshold and a deeper search frontier. Experts changing this behavior should inspect both the helper defaults and the constants in the page, not just one of them.

### 6. The approved CQ product is reusable evidence

After the reviewer approves the inference, DIG4EL writes:

~~~text
ld/storage/<language>/cq/cq_knowledge/cq_knowledge.json
~~~

Its shape is conceptually:

~~~json
{
  "sentences": [
    {
      "source_english": "...",
      "target_raw": "...",
      "alterlingua": "target<concept(IP:... | RP:...)>",
      "comment": ""
    }
  ],
  "grammar_priors": [
    {
      "Parameter": "...",
      "Origin": "Known | Observed | Inferred",
      "Winner": "...",
      "Confidence": 0
    }
  ]
}
~~~

The generator can then use the approved priors and the pseudo-glossed examples without having to re-run the full CQ workflow.

## LLM, retrieval, and generation

The LLM-enabled components are complementary to the local CQ inference engine; they do not replace it.

### Sentence-pair augmentation

[libs/semantic_description_agents.py](libs/semantic_description_agents.py) defines structured OpenAI-agent outputs for describing source sentences and identifying grammar-relevant keywords/concepts. [libs/semantic_description_utils.py](libs/semantic_description_utils.py) turns those outputs into the augmented pair format.

[libs/sentence_queue_utils.py](libs/sentence_queue_utils.py) queues this work in Redis, while [rq_worker.py](rq_worker.py) executes it asynchronously. The dashboard persists completed results into the language workspace, after which a caretaker can correct the analysis and add precise word–concept connections.

### Document retrieval

[libs/openai_vector_store_utils.py](libs/openai_vector_store_utils.py) manages OpenAI Files and vector stores. Uploaded documents are copied into the language workspace and then associated with a remote vector-store ID in **info.json**. During generation, OpenAI File Search contributes document-grounded material for the selected query.

### Local retrieval utilities

[libs/retrieval_augmented_generation_utils.py](libs/retrieval_augmented_generation_utils.py) also offers reusable local retrieval components:

- SentenceTransformer embeddings using **all-MiniLM-L6-v2**;
- normalized vector similarity through FAISS;
- keyword indexing and hard retrieval;
- persistence helpers for local indexes and metadata.

These are useful for experiments and integrations. In the current generation-page path, local FAISS and keyword retrieval calls are not the default selector; an LLM selector chooses useful examples from the augmented-pair pool.

### Lesson and sketch generation

[libs/grammar_generation_agents.py](libs/grammar_generation_agents.py) contains Pydantic schemas and OpenAI agents for:

- choosing relevant CQ parameters;
- contributing from pseudo-glossed CQ evidence;
- retrieving from document vector stores;
- creating a lesson for learners or a grammar sketch for linguists;
- optionally reviewing and simplifying a lesson.

[pages/generate_grammar.py](pages/generate_grammar.py) lets the user independently include CQ evidence, documents, and sentence pairs. [libs/output_generation_utils.py](libs/output_generation_utils.py) writes JSON, XLSX templates, DOCX lessons, and supported graph/table exports.

Generated text must be treated as an editable draft. Preserve its trace and source context, review every example, and do not assume that a model’s source-restricted prompt prevents all hallucination or misinterpretation.

## Code and library guide

### Repository map

~~~text
home.py                         Streamlit landing page and top-level navigation
pages/                          Streamlit workflows, exploration, administration, evaluation
libs/                           Reusable application and research modules
rq_worker.py                    Redis/RQ worker entry point
data/                           Concept/legacy support data
questionnaires/                 Canonical questionnaire dialogs
conveqs/                        ConveQs-compatible questionnaire catalog
templates/                      Import/export templates
grammar_seeds/                  Generation guidance
external_data/                  WALS, Grambank, Glottolog, and derived tables
ld/                             Local runtime volume; ignored by Git
script/ and feature_tests/      Research, preprocessing, and exploratory utilities
~~~

### Module map for experts

| Area | Main modules | Use or extension point |
| --- | --- | --- |
| Runtime storage and helpers | [utils.py](libs/utils.py), [file_manager_utils.py](libs/file_manager_utils.py), [glottolog_utils.py](libs/glottolog_utils.py), [display_utils.py](libs/display_utils.py) | Unicode normalization, language-workspace creation, metadata, file handling, and shared displays. Start with **create_ld()** when creating a workspace programmatically. |
| CQ semantics | [graphs_utils.py](libs/graphs_utils.py), [knowledge_graph_utils.py](libs/knowledge_graph_utils.py), [cq_observers.py](libs/cq_observers.py), [stats.py](libs/stats.py) | Concept graph traversal, CQ consolidation, pseudo-glossing, deterministic observation, and token/statistical helpers. |
| Typological data | [wals_utils.py](libs/wals_utils.py), [grambank_utils.py](libs/grambank_utils.py), [grambank_wals_utils.py](libs/grambank_wals_utils.py) | Lookup tables, priors, conditional probabilities, and WALS–Grambank bridge matrices. |
| Probabilistic inference | [general_agents.py](libs/general_agents.py), [ga_param_selection_utils.py](libs/ga_param_selection_utils.py), [prob_utils.py](libs/prob_utils.py) | Categorical beliefs, message passing, candidate selection, mutual information, and probability-graph experiments. |
| Sentence augmentation | [semantic_description_agents.py](libs/semantic_description_agents.py), [semantic_description_utils.py](libs/semantic_description_utils.py), [sentence_queue_utils.py](libs/sentence_queue_utils.py) | Structured LLM analysis, augmented-pair construction, queue submission, progress, and persistence. |
| Retrieval | [openai_vector_store_utils.py](libs/openai_vector_store_utils.py), [openai_file_search_utils.py](libs/openai_file_search_utils.py), [retrieval_augmented_generation_utils.py](libs/retrieval_augmented_generation_utils.py) | Remote OpenAI File Search plus reusable local SentenceTransformer/FAISS retrieval. |
| Generation and export | [grammar_generation_agents.py](libs/grammar_generation_agents.py), [grammar_generation_utils.py](libs/grammar_generation_utils.py), [output_generation_utils.py](libs/output_generation_utils.py) | Source selection, schema-constrained lesson/sketch creation, pseudo-gloss parsing, and XLSX/DOCX output. |
| Import and interoperability | [file_format_utils.py](libs/file_format_utils.py), [flex_import_multi_dialect.py](libs/flex_import_multi_dialect.py), [conveqs_utils.py](libs/conveqs_utils.py) | FLEx, Pangloss, generic gloss JSON, multi-dialect, and ConveQs workbook conversion. |
| Access control and evaluation | [auth_utils.py](libs/auth_utils.py), [judge.py](libs/judge.py) | YAML-backed roles/cookies and structured LLM comparison of generated lessons. |

### Major third-party libraries

| Library family | Role in DIG4EL |
| --- | --- |
| Streamlit and streamlit-authenticator | Multipage interface, session state, role-aware UI, and cookie-based authentication. |
| pandas, NumPy, SciPy, scikit-learn | Tabular transformations, probabilities, statistics, and evaluation support. |
| NetworkX, PyVis, streamlit-agraph, Graphviz | Concept/inference graph construction and visualization. |
| OpenPyXL, lxml, python-docx, PyYAML | Questionnaire/corpus import-export, XML parsing, Word generation, and YAML configuration. |
| Redis and RQ | Durable background jobs for sentence-pair augmentation. |
| OpenAI SDK and OpenAI Agents | Optional structured annotation, File Search, source synthesis, lesson generation, and judging. |
| SentenceTransformers, Torch, Transformers, FAISS | Reusable local semantic embeddings and similarity retrieval. |
| Plotly, Altair, Folium | Charts, probability exploration, and ConveQs map displays. |

### Calling a module from your own research code

The code is not published as an installable package. Work from the repository root, activate the project environment, and import a focused helper rather than a Streamlit page.

Some research modules currently emit development output during import. Treat **libs/** as internal source code rather than a quiet, stable SDK; when embedding a helper in another application, first remove or isolate any import-time debug output relevant to that integration.

Create a language workspace:

~~~python
from pathlib import Path

from libs.file_manager_utils import create_ld

storage = Path("ld/storage")
create_ld(str(storage), "Example language")
~~~

Convert a Pangloss XML file to the dashboard’s sentence-pair format:

~~~python
import json

from libs.file_format_utils import pangloss_xml_to_sentence_pairs_json

pairs = pangloss_xml_to_sentence_pairs_json(
    "my_corpus.xml",
    pivot_lang="fr",
    target_form_kind=("phono", "orth"),
)

with open("sentence_pairs.json", "w", encoding="utf-8") as handle:
    json.dump(pairs, handle, ensure_ascii=False, indent=2)
~~~

Explore parameter suggestions from the bundled conditional-probability tables:

~~~python
from pathlib import Path

from libs.ga_param_selection_utils import (
    BeliefState,
    load_all_cpts,
    suggest_parameters,
)

graph = load_all_cpts(Path("external_data"))
seed_value_id = next(iter(graph.nodes))
beliefs = BeliefState(priors={seed_value_id: 0.9})
suggestions = suggest_parameters(graph, beliefs)
print(suggestions)
~~~

The example selects a real bundled value ID only to make the helper runnable. In research use, initialize the belief state with evidence-backed WALS or Grambank value IDs; use the lookup helpers in **wals_utils.py** and **grambank_utils.py** to map between human names and dataset IDs.

Loading every bundled conditional-probability table creates a large directed graph, so use this helper in a batch or research process with appropriate memory rather than in a latency-sensitive UI callback.

## Advanced pages, operations, and evaluation

### Page guide

| Page or group | Intended use |
| --- | --- |
| [pages/dashboard.py](pages/dashboard.py) | Main per-language source dashboard. |
| [pages/record_cq_transcriptions.py](pages/record_cq_transcriptions.py) | Current DCQ translation/annotation editor and import/export workflow. |
| [pages/infer_from_knowledge_and_cqs.py](pages/infer_from_knowledge_and_cqs.py) | Current CQ inference and review workflow. |
| [pages/generate_grammar.py](pages/generate_grammar.py) | Current lesson/sketch generation workflow. |
| [pages/WALS_Explore.py](pages/WALS_Explore.py), [pages/Grambank_Explore.py](pages/Grambank_Explore.py), [pages/Conditional_proba_exploration.py](pages/Conditional_proba_exploration.py) | Advanced exploration of typological data and conditional probabilities. |
| [pages/General_agent_gawo_example.py](pages/General_agent_gawo_example.py), [pages/Testing_general_agents.py](pages/Testing_general_agents.py) | Inference experiments and demonstrations. |
| [pages/Conveqs_home.py](pages/Conveqs_home.py) | ConveQs catalog/map-oriented interface. |
| [pages/File_explorer.py](pages/File_explorer.py) | Administrator storage, user, and vector-store controls. It includes destructive actions; back up first. |
| [pages/judge_interface.py](pages/judge_interface.py) | Structured LLM comparison of two generated lessons; implemented in [libs/judge.py](libs/judge.py). |

[pages/Grammatical_Description.py](pages/Grammatical_Description.py), the numbered CQ pages, [libs/agents_markov_random_fields.py](libs/agents_markov_random_fields.py), [libs/evolutionary_utils.py](libs/evolutionary_utils.py), and much of [script/](script/) are valuable research or legacy material but are not the main v1 path. Treat them as code to inspect and adapt, rather than as a supported public command-line interface.

### Roles and data stewardship

The interface distinguishes guest, authenticated **user**, caretaker, and administrator behavior:

- **Guests** can explore a deliberately restricted collection but cannot add or augment language data.
- **Users** are ordinary authenticated accounts.
- **Caretakers** are normally users whose **caretaker** list in **auth_config.yaml** contains the currently selected language.
- **Administrators** can manage users, storage, and remote vector-store state.

For a language-scoped caretaker, use **role: user** plus a **caretaker: [language-name]** list. Avoid setting a literal **role: caretaker**: the current role check treats it as caretaker access without the selected-language membership test. This is an access-control convenience, not a substitute for data-governance decisions. Assign caretakers only with the permission of the relevant language community and project stakeholders.

### Deployment notes

There is no supported Docker Compose, production Dockerfile, or single-command hosting recipe in this repository. A real hosted deployment needs:

- a web process running Streamlit;
- a separate worker process for augmentation;
- shared Redis;
- a shared persistent volume mounted at the same **RAILWAY_VOLUME_MOUNT_PATH** in both processes;
- injected secrets for authentication and OpenAI;
- explicit backups, logging, and network hardening.

The checked-in [railway.json](railway.json) does not define a deploy command. [railway_old.json](railway_old.json) starts only Streamlit, while [railway.sh](railway.sh) starts the blocking worker before the Streamlit command and therefore cannot launch both services as one process. Configure web and worker services separately before treating Railway deployment as operational.

The bundled Streamlit configuration disables CORS and XSRF protection. Do not describe the default configuration as hardened for public exposure without a separate security review.

### Verification and evaluation

There is no maintained, top-level automated test suite or test configuration. The repository contains research and exploratory scripts under **script/** and **feature_tests/**, but they may have working-directory assumptions or external-service requirements.

Useful low-risk checks after installation are:

~~~bash
python -m pip check
python -m compileall -q home.py libs pages
~~~

Then perform a manual smoke test:

1. launch the landing page;
2. log in with a local administrator account;
3. open the dashboard and select/create a test workspace;
4. import a small sentence-pair file without augmentation;
5. if using augmentation, verify Redis and the worker before submitting a job.

The leave-one-language-out/general-agent research material and its summaries are in [script/general_agents_full_test_word_order.py](script/general_agents_full_test_word_order.py) and [test_result_analysis/](test_result_analysis/). It is evaluation material, not a turnkey CI command.

## Data governance, license, and citation

### Responsible use

DIG4EL is designed around the FAIR and CARE principles, but responsible operation depends on the people running it.

- Obtain appropriate permission before entering, uploading, processing, or sharing language data.
- Respect community rules about access, attribution, reuse, and deletion.
- Upload only documents that are public or otherwise authorized for the intended processing. The dashboard specifically asks users to use material compatible with Creative Commons BY-NC conditions.
- Sentence augmentation, OpenAI vector stores/File Search, lesson generation, and judging can send selected text, documents, and prompts to OpenAI services. Do not use these features with material that must remain local or confidential.
- Preserve source attribution, human annotations, evidence reviews, and generated-output traces.
- Treat generated material as a draft for expert and, where appropriate, community review before teaching, publishing, or redistributing it.

### License

The DIG4EL source code is licensed under the [GNU Affero General Public License v3.0](LICENSE.txt). The repository also includes third-party datasets with their own licenses and citation requirements. In particular, consult the bundled metadata and licenses for [WALS](external_data/wals-master/) and [Grambank](external_data/grambank-1.0.3/) before redistributing or publishing work that uses them.

### Citation

Use [CITATION.cff](CITATION.cff) as the repository’s citation metadata and record the exact runtime version from [version.json](version.json) plus the Git commit used in your work. The checked-in citation record currently identifies the archived 2024 software release:

~~~bibtex
@software{christian_2024_dig4el,
  author  = {Christian, Sebastien},
  title   = {DIG4EL},
  year    = {2024},
  version = {0.1.2},
  doi     = {10.5281/zenodo.14009843},
  url     = {https://github.com/alterfero/dig4el}
}
~~~

Also cite the exact WALS and Grambank releases used by your analysis. Their bundled READMEs and metadata provide their recommended citations. For methodological background, see the DIG4EL reference displayed in [home.py](home.py) and the linked Conversational Questionnaire literature.

### Contact and acknowledgements

For research or access enquiries, contact Sebastien Christian at sebastien.christian@upf.pf.

The project acknowledges the support and contributions of Jacques Vernaudon, Alexandre François, Mary Walworth, Nick Thieberger, Vanessa Raffin, the CNRS Heliceo project, the Maison des Sciences de l’Homme du Pacifique, the University of French Polynesia, and—above all—the community members and language experts who share their knowledge and time.
