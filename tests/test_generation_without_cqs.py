"""Generation with Bayesian priors but no CQ evidence must not call the CQ agent."""
import ast
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock, patch

from streamlit.testing.v1 import AppTest

from libs import grammar_generation_agents as gga
from libs import grammar_generation_utils as ggu


PAGE = Path(__file__).resolve().parents[1] / "pages" / "generate_grammar.py"
SOURCE = PAGE.read_text()
HELPERS = "\n\n".join(
    ast.unparse(node) for node in ast.parse(SOURCE).body
    if isinstance(node, ast.FunctionDef) and node.name in {
        "reset", "initialize_generation_progress", "update_generation_progress",
        "complete_generation_step",
    }
)
# Exercise the real source controls, generation, aggregation, and trace writing,
# without depending on login, unrelated language workspaces, or output rendering.
WORKFLOW = SOURCE.split("# GATHERING MATERIAL\n", 1)[1].split(
    "# =========== DISPLAY, STORAGE, CONVERSION", 1
)[0]
PRIORS = [{"Parameter": "Order of Subject, Object and Verb", "Origin": "Inferred",
           "Winner": "SVO", "Confidence": 95, "Examples by value": {}}]
SENTENCES = [{"source_english": "I walk.", "target_raw": "Test sentence.",
              "alterlingua": "Test<>(IP: | RP:) sentence<>"}]
CONTRIBUTION = {"explanation": "CQ-based explanation.", "examples": []}


class AlterlinguaAgentTests(unittest.TestCase):
    def test_empty_input_never_calls_runner(self):
        with patch.object(gga.Runner, "run", new_callable=AsyncMock) as runner:
            self.assertEqual(gga.contribute_from_alterlingua_sync("Word order", []), {})
        runner.assert_not_awaited()

    def test_nonempty_input_still_uses_agent(self):
        with patch.object(gga.Runner, "run", new_callable=AsyncMock) as runner:
            runner.return_value = SimpleNamespace(final_output=gga.Contribution(**CONTRIBUTION))
            result = gga.contribute_from_alterlingua_sync("Word order", SENTENCES)
        self.assertEqual(result, CONTRIBUTION)
        runner.assert_awaited_once()
        self.assertIs(runner.call_args.args[0], gga.cq_alterlingua_agent)


class GenerationWithoutCQTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ["cq/cq_knowledge", "cq/cq_translations",
                          "sentence_pairs/vectors", "sentence_pairs/augmented_pairs"]:
            (self.root / "Test" / directory).mkdir(parents=True)
        self.knowledge_path = self.root / "Test/cq/cq_knowledge/cq_knowledge.json"
        self.seeds = self.root / "grammar_seeds.json"
        self.seeds.write_text("{}")
        self.addCleanup(patch.stopall)
        patch.object(ggu, "BASE_LD_FOLDER", str(self.root)).start()
        self.selector = patch.object(gga, "select_parameters_sync",
                                     return_value=[PRIORS[0]["Parameter"]]).start()
        self.cq_agent = patch.object(gga, "contribute_from_alterlingua_sync",
                                     return_value=CONTRIBUTION).start()
        self.lesson = patch.object(gga, "create_lesson_sync",
                                   side_effect=lambda **kwargs: {"title": "Test lesson"}).start()
        self.sketch = patch.object(gga, "create_sketch_sync",
                                   side_effect=lambda **kwargs: {"title": "Test sketch"}).start()
        self.document_agent = patch.object(gga, "file_search_request_sync",
                                           side_effect=AssertionError("Unexpected document call")).start()

    def app(self, knowledge, **state):
        if knowledge is not None:
            self.knowledge_path.write_text(json.dumps(knowledge))
        defaults = dict(
            indi="Test", is_cq=False, is_gp=False, is_doc=False, is_pairs=False,
            use_cq=True, use_gp=True, use_pseudo_gloss=True, use_doc=True, use_pairs=True,
            info_dict={"documents": {"oa_vector_store_name": "", "oa_vector_store_id": None}},
            run_sources=False, run_aggregation=True, seed=None, bare_query=None, query=None,
            relevant_parameters=None, alterlingua_contribution=None,
            documents_contribution=None, selected_pairs=None, output_dict=None,
            document_format="Grammar lesson", polished_output=False,
            readers_language="English", readers_type="Adults", show_all_details=False,
        )
        defaults.update(state)
        setup = f'''
import json
import os
from datetime import datetime
from types import SimpleNamespace
import openai
import streamlit as st
from libs import grammar_generation_agents as gga
from libs import grammar_generation_utils as ggu
BASE_LD_PATH = {str(self.root)!r}
GRAMMAR_SEEDS_PATH = {str(self.seeds)!r}
role = "guest"
username = "test"
u = SimpleNamespace(clean_sentence=lambda sentence, **kwargs: "topic")
if "test_initialized" not in st.session_state:
    st.session_state.update({defaults!r})
    st.session_state.test_initialized = True
'''
        return AppTest.from_string(setup + HELPERS + "\n" + WORKFLOW + '''
if "generation_progress" in locals():
    st.session_state.test_steps = (generation_progress["current_step"],
                                  generation_progress["total_steps"])
''').run()

    def submit(self, app, document_format="Grammar lesson"):
        if document_format == "Grammar sketch":
            next(item for item in app.selectbox if item.label == "Format").select(document_format).run()
        app.text_input[0].input("Word order").run()
        next(button for button in app.button if button.label == "submit").click().run()
        self.assertEqual([error.value for error in app.exception], [])
        self.assertFalse(app.session_state.run_sources)
        self.assertFalse(app.session_state.run_aggregation)
        self.assertEqual(app.session_state.test_steps[0], app.session_state.test_steps[1])
        return (self.sketch if document_format == "Grammar sketch" else self.lesson).call_args.kwargs

    def test_priors_only_finish_lesson_and_sketch_without_cq_request(self):
        for document_format in ["Grammar lesson", "Grammar sketch"]:
            for sentences in [{"sentences": []}, {}, {"sentences": None}]:
                with self.subTest(document_format=document_format, sentences=sentences):
                    app = self.app({"grammar_priors": PRIORS, **sentences})
                    self.assertTrue(app.session_state.is_gp)
                    self.assertFalse(app.session_state.is_cq)
                    self.assertIn("Use inferred GPs", [toggle.label for toggle in app.toggle])
                    self.assertNotIn("Use pseudo-gloss", [toggle.label for toggle in app.toggle])
                    inputs = self.submit(app, document_format)
                    self.assertEqual(json.loads(inputs["grammatical_params"]), PRIORS)
                    self.assertEqual(inputs["alterlingua_explanation"], "No description from sentence analysis.")
                    self.assertEqual(app.session_state.alterlingua_contribution, {})
                    self.assertNotIn("cqs", app.session_state.output_dict["sources"])
                    self.assertEqual(app.session_state.test_steps, (4, 4))
        self.cq_agent.assert_not_called()
        self.document_agent.assert_not_called()
        self.assertEqual(self.selector.call_count, 6)

    def test_real_cq_evidence_is_still_used(self):
        (self.root / "Test/cq/cq_translations/cq.json").write_text("{}")
        app = self.app({"grammar_priors": PRIORS, "sentences": SENTENCES})
        inputs = self.submit(app)
        self.cq_agent.assert_called_once()
        self.assertEqual(self.cq_agent.call_args.args[1], [
            {"source": "I walk.", "target": "Test sentence.",
             "alterlingua": "Test sentence", "comments": ""}
        ])
        self.assertEqual(inputs["alterlingua_explanation"], CONTRIBUTION["explanation"])
        self.assertEqual(app.session_state.output_dict["sources"]["cqs"], ["cq.json"])
        self.assertEqual(app.session_state.test_steps, (5, 5))

    def test_source_toggles_skip_only_the_disabled_input(self):
        for disabled in ["use_cq", "use_pseudo_gloss", "use_gp"]:
            with self.subTest(disabled=disabled):
                self.cq_agent.reset_mock()
                self.selector.reset_mock()
                app = self.app({"grammar_priors": PRIORS, "sentences": SENTENCES}, **{disabled: False})
                inputs = self.submit(app)
                self.assertEqual(app.session_state.test_steps, (4, 4))
                if disabled == "use_gp":
                    self.selector.assert_not_called()
                    self.cq_agent.assert_called_once()
                    self.assertEqual(inputs["grammatical_params"], "No relevant grammatical parameter.")
                else:
                    self.cq_agent.assert_not_called()
                    self.selector.assert_called_once()
                    self.assertEqual(json.loads(inputs["grammatical_params"]), PRIORS)

    def test_cq_sentences_without_priors_skip_parameter_selection(self):
        app = self.app({"sentences": SENTENCES})
        self.submit(app)
        self.selector.assert_not_called()
        self.cq_agent.assert_called_once()
        self.assertEqual(app.session_state.test_steps, (4, 4))

    def test_missing_or_empty_knowledge_clears_stale_availability(self):
        for knowledge in [None, {}, {"grammar_priors": [], "sentences": []}]:
            with self.subTest(knowledge=knowledge):
                app = self.app(knowledge, is_cq=True, is_gp=True)
                self.assertEqual([error.value for error in app.exception], [])
                self.assertFalse(app.session_state.is_cq)
                self.assertFalse(app.session_state.is_gp)
                self.assertEqual(len(app.text_input), 0)
        self.cq_agent.assert_not_called()
        self.selector.assert_not_called()


if __name__ == "__main__":
    unittest.main()
