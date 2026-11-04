"""Document retrieval regressions using SDK models and an in-memory HTTP transport."""
import ast
import asyncio
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import httpx
import openai
from openai.types.responses import Response
from streamlit.testing.v1 import AppTest

from libs import grammar_generation_agents as gga


def search_item(**overrides):
    return {
        "id": "fs_test",
        "type": "file_search_call",
        "status": "completed",
        "queries": ["Tahitian pronouns"],
        "results": [{"file_id": "file_test", "filename": "grammar.pdf",
                     "score": 0.9, "text": "A passage about pronouns."}],
        **overrides,
    }


def message_item(text="A document-based answer.", annotations=None):
    return {
        "id": "msg_test", "type": "message", "status": "completed", "role": "assistant",
        "content": [{"type": "output_text", "text": text,
                     "annotations": annotations if annotations is not None else [
                         {"type": "file_citation", "file_id": "file_test",
                          "filename": "grammar.pdf", "index": 0}]}],
    }


def response_payload(output=None, **overrides):
    return {
        "id": "resp_test", "object": "response", "created_at": 1,
        "status": "completed", "model": "gpt-6-luna", "parallel_tool_calls": True,
        "tool_choice": {"type": "file_search"}, "tools": [],
        "output": output if output is not None else [search_item(), message_item()],
        **overrides,
    }


class DocumentResponseTests(unittest.TestCase):
    def parse(self, output=None, **overrides):
        response = Response.model_validate(response_payload(output, **overrides))
        return gga.extract_document_contribution(response)

    def test_collects_all_text_and_citations_after_reasoning_and_multiple_searches(self):
        first_message = message_item("First passage.")
        first_message["content"].append(message_item("Second passage.")["content"][0])
        final_message = message_item("Third passage.", [
            {"type": "url_citation", "url": "https://example.com", "title": "Other",
             "start_index": 0, "end_index": 1},
            {"type": "file_citation", "file_id": "file_other",
             "filename": "notes.pdf", "index": 0},
        ])
        result = self.parse([
            {"id": "rs_test", "type": "reasoning", "summary": []},
            search_item(), search_item(id="fs_second"), first_message, final_message,
        ])
        self.assertEqual(result["text"], "First passage.\n\nSecond passage.\n\nThird passage.")
        self.assertEqual(result["sources"], ["grammar.pdf", "notes.pdf"])
        self.assertEqual(result["search_result_count"], 2)

    def test_accepts_original_response_layout(self):
        result = self.parse()
        self.assertEqual(result["text"], "A document-based answer.")
        self.assertEqual(result["sources"], ["grammar.pdf"])

    def test_does_not_label_retrieved_but_uncited_files_as_sources(self):
        self.assertEqual(self.parse([search_item(), message_item(annotations=[])])["sources"], [])

    def test_no_matches_does_not_pass_unsupported_model_text_to_generation(self):
        result = self.parse([search_item(results=[]), message_item("Unsupported claim.")])
        self.assertEqual(result["search_result_count"], 0)
        self.assertEqual(result["sources"], [])
        self.assertNotIn("Unsupported claim", result["text"])
        self.assertIn("No relevant information", result["text"])

    def test_rejects_missing_failed_or_unverifiable_search(self):
        for searches in [[], [search_item(status="failed")],
                         [search_item(status="incomplete")], [search_item(results=None)]]:
            with self.subTest(searches=searches), self.assertRaises(ValueError):
                self.parse(searches + [message_item()])

    def test_rejects_failed_or_incomplete_response(self):
        for status in ["failed", "incomplete", "in_progress"]:
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.parse(status=status)
        with self.assertRaises(ValueError):
            gga.extract_document_contribution(None)

    def test_rejects_empty_answer_or_refusal(self):
        refusal = message_item()
        refusal["content"] = [{"type": "refusal", "refusal": "Cannot answer."}]
        for messages in [[], [message_item("  ")], [refusal]]:
            with self.subTest(messages=messages), self.assertRaises(ValueError):
                self.parse([search_item()] + messages)


class DocumentRequestTests(unittest.TestCase):
    def test_searches_saved_ids_without_listing_stores_and_closes_client(self):
        requests = []

        def handle(request):
            requests.append(request)
            if request.url.path != "/v1/responses":
                return httpx.Response(500, json={"error": {"message": "Store listing unavailable"}})
            return httpx.Response(200, json=response_payload())

        client = openai.AsyncOpenAI(
            api_key="test-key", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))
        )
        with patch.object(gga.openai, "AsyncOpenAI", return_value=client):
            response = gga.file_search_request_sync("Tahitian", ["vs_saved"], "Pronouns")
        self.assertTrue(client.is_closed())
        self.assertEqual([(r.method, r.url.path) for r in requests], [("POST", "/v1/responses")])
        payload = json.loads(requests[0].content)
        self.assertEqual(payload["tools"], [{"type": "file_search", "vector_store_ids": ["vs_saved"]}])
        self.assertEqual(payload["tool_choice"], {"type": "file_search"})
        self.assertEqual(payload["include"], ["file_search_call.results"])
        self.assertEqual(gga.extract_document_contribution(response)["sources"], ["grammar.pdf"])

    def test_propagates_api_errors_instead_of_returning_empty_contribution(self):
        for code, error in [(404, openai.NotFoundError), (500, openai.InternalServerError)]:
            with self.subTest(code=code):
                client = openai.AsyncOpenAI(
                    api_key="test-key", max_retries=0,
                    http_client=httpx.AsyncClient(transport=httpx.MockTransport(
                        lambda request: httpx.Response(
                            code, json={"error": {"message": "Retrieval failed"}},
                            headers={"x-request-id": "req_test"},
                        )
                    )),
                )
                with patch.object(gga.openai, "AsyncOpenAI", return_value=client):
                    with self.assertRaises(error) as raised:
                        gga.file_search_request_sync("Tahitian", ["vs_saved"], "Pronouns")
                self.assertEqual(raised.exception.request_id, "req_test")
                self.assertTrue(client.is_closed())

    def test_rejects_missing_store_before_any_api_call(self):
        for vsids in [[], [""], [None], ["  "], ["vs_valid", ""]]:
            with self.subTest(vsids=vsids), patch.object(gga.openai, "AsyncOpenAI") as client:
                with self.assertRaises(ValueError):
                    asyncio.run(gga.file_search_request("Tahitian", vsids, "Pronouns"))
                client.assert_not_called()


class DocumentPageTests(unittest.TestCase):
    def test_retrieval_failure_stops_generation_and_allows_retry(self):
        # Run the real document step in isolation from login and local language data.
        page = Path(__file__).resolve().parents[1] / "pages" / "generate_grammar.py"
        tree = ast.parse(page.read_text())
        generation = next(node for node in tree.body if isinstance(node, ast.If)
                          and ast.unparse(node.test) == "st.session_state.run_sources")
        document_step = next(node for node in generation.body if isinstance(node, ast.If)
                             and ast.unparse(node.test) == "st.session_state.is_doc and st.session_state.use_doc")
        setup = '''
import streamlit as st
import openai
from libs import grammar_generation_agents as gga
st.session_state.update(is_doc=True, use_doc=True, indi="Tahitian", query="Pronouns",
    info_dict={"documents": {"oa_vector_store_id": "vs_saved"}},
    documents_contribution={"text": "Stale text", "sources": []},
    output_dict={"title": "Old lesson"}, run_sources=True, run_aggregation=True)
role = "guest"
generation_progress = {"status_placeholder": st.empty()}
def update_generation_progress(*args):
    pass
'''
        for error in [ValueError("Search did not complete"), openai.InternalServerError(
                "Server error", response=httpx.Response(500, request=httpx.Request("POST", "https://api.openai.com/v1/responses")),
                body=None)]:
            with self.subTest(error=type(error).__name__), patch.object(
                gga, "file_search_request_sync", side_effect=error
            ):
                app = AppTest.from_string(setup + ast.unparse(document_step)
                                          + '\nst.success("Aggregation reached")').run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(app.success), 0)
            self.assertTrue(any("Generation stopped" in item.value for item in app.error))
            self.assertIsNone(app.session_state.documents_contribution)
            self.assertIsNone(app.session_state.output_dict)
            self.assertIsNone(app.session_state.query)
            self.assertFalse(app.session_state.run_sources)
            self.assertFalse(app.session_state.run_aggregation)


if __name__ == "__main__":
    unittest.main()
