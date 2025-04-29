import json
from docx import Document
from libs import knowledge_graph_utils as kgu
from io import BytesIO
import re
from collections import defaultdict
import pandas as pd

import jinja2

def generate_transcription_doc(cq, target_language, pivot_language):
    if target_language in ["English", ""]:
        target_language = "target language"

    document = Document()
    document.add_heading('Conversational Questionnaire', 0)
    document.add_heading(f'"{cq["title"]}"', 0)
    document.add_heading("Information", 1)
    table = document.add_table(rows=5, cols=2, style="Light Grid")  # Fixed column count
    row_cells0 = table.rows[0].cells
    row_cells0[0].text = "Target language"
    if target_language != "target language":
        row_cells0[1].text = target_language
    row_cells1 = table.rows[1].cells
    row_cells1[0].text = "Transcription made by"
    row_cells2 = table.rows[2].cells
    row_cells2[0].text = f"Content in {target_language} provided by"
    row_cells3 = table.rows[3].cells
    row_cells3[0].text = "Location"
    row_cells4 = table.rows[4].cells
    row_cells4[0].text = "Date"

    document.add_page_break()

    document.add_heading("Full dialog in English", 1)
    document.add_paragraph(cq["context"])
    dialog_table = document.add_table(rows=1, cols=3, style="Table Grid")  # Fixed column count
    hdr_cells = dialog_table.rows[0].cells
    hdr_cells[0].text = "Index"
    hdr_cells[1].text = cq["speakers"]["A"]["name"]
    hdr_cells[2].text = cq["speakers"]["B"]["name"]
    dialog_length = len(cq["dialog"])
    for index in range(1, dialog_length + 1):
        content = cq["dialog"][str(index)]
        row_cells = dialog_table.add_row().cells
        if content.get("legacy index", "") != "":
            i = content["legacy index"]
        else:
            i = str(index)
        row_cells[0].text = i
        if content["speaker"] == "A":
            row_cells[1].text = content["text"]
            row_cells[2].text = ""
        elif content["speaker"] == "B":
            row_cells[1].text = ""
            row_cells[2].text = content["text"]

    document.add_page_break()

    document.add_heading("Transcription", 1)

    for index in range(1, dialog_length + 1):
        content = cq["dialog"][str(index)]
        if content.get("legacy index", "") != "":
            i = content["legacy index"]
        else:
            i = str(index)
        document.add_paragraph("")
        document.add_heading(f'{i}: {content["text"]}', 2)
        transcription_table = document.add_table(rows=0, cols=2, style="Table Grid")
        row_cells = transcription_table.add_row().cells
        row_cells[0].text = "Pivot (if not English)"
        row_cells[1].text = ""
        row_cells = transcription_table.add_row().cells
        row_cells[0].text = f'Sentence in {target_language}'
        row_cells[1].text = ""
        document.add_paragraph(" ")
        p = document.add_paragraph()
        p.add_run("Connections between word(s) and concept(s):").bold = True
        document.add_paragraph("In this segment, which word(s) contribute to which concept(s) below? One word can appear in multiple concepts, or in none. Multiple words can appear in a single concept.")
        concept_table = document.add_table(rows=1, cols=2, style="Table Grid")
        hdr_cells = concept_table.rows[0].cells
        hdr_cells[0].text = "Concept"
        hdr_cells[1].text = "Word(s) contributing to this concept"
        if content.get("intent", []) != []:
            row_cells = concept_table.add_row().cells
            row_cells[0].text = f'Intent: {"+".join(content["intent"])}'
            row_cells[1].text = ""
        if content.get("predicate", []) != []:
            row_cells = concept_table.add_row().cells
            row_cells[0].text = f'Type of predicate: {"+".join(content["predicate"])}'
            row_cells[1].text = ""
        for c in content["concept"]:
            row_cells = concept_table.add_row().cells
            row_cells[0].text = c
            row_cells[1].text = ""

    # Save to a BytesIO buffer instead of disk
    docx_buffer = BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)  # Reset buffer position

    return docx_buffer



def generate_docx_from_kg_index_list(kg, delimiters, kg_index_list):
    document = Document()
    document.add_heading('Partial corpus', 0)
    item_counter = 0
    for index in kg_index_list:
        item_counter += 1
        data = kg[index]
        gloss = kgu.build_super_gloss_df(kg, index, delimiters,  output_dict=True)
        document.add_paragraph("""Entry {}""".format(item_counter), style='List Bullet')
        pex = document.add_paragraph(" ", "Normal")
        pex.add_run(f'{data["recording_data"]["translation"]}', style='Strong')
        document.add_paragraph(f'{data["sentence_data"]["text"]}', "Normal")
        document.add_paragraph(f'''
        Intent: {", ".join(data["sentence_data"]["intent"])}
        Type of predicate: {", ".join(data["sentence_data"]["predicate"])}
        ''', "Normal")

        # Define the number of rows (one header + words) and columns
        num_words = len(gloss)
        table = document.add_table(rows=num_words + 1, cols=4, style="Light Shading Accent 1")  # Fixed column count

        # Populate header row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = ""
        hdr_cells[1].text = "Concept"
        hdr_cells[2].text = "Internal Particularisation"
        hdr_cells[3].text = "Relational Particularisation"

        # Populate the table with data
        for i, w in enumerate(gloss, start=1):
            row_cells = table.rows[i].cells
            row_cells[0].text = w["word"]
            row_cells[1].text = w["concept"]
            row_cells[2].text = w["internal particularization"]
            row_cells[3].text = w["relational particularization"]
        document.add_paragraph("""   """)

    # Save to a BytesIO buffer instead of disk
    docx_buffer = BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)  # Reset buffer position

    return docx_buffer


def generate_docx_from_hybrid_output(content, language):
    document = Document()
    document.add_heading('Learning {}: Elements of grammar.'.format(language), 0)
    document.add_heading('Introduction', 1)
    document.add_paragraph(content["introduction"]["description"])
    for chapter in content["chapters"]:
        document.add_heading(chapter["title"], 1)
        document.add_paragraph(chapter["explanation"])
        e_counter = 0
        for example in chapter["examples"]:
            e_counter += 1
            document.add_paragraph("""Example {}""".format(e_counter), style='List Bullet')
            pex = document.add_paragraph(" ", "Normal")
            pex.add_run(f'{example["target"]}', style='Strong')
            document.add_paragraph(f'{example["english"]}', "Normal")

            df = parse_alterlingua(example["gloss"])

            table = document.add_table(rows=1, cols=len(df.columns), style="Light Shading Accent 1")

            # Add headers
            hdr_cells = table.rows[0].cells
            for i, column_name in enumerate(df.columns):
                hdr_cells[i].text = column_name

            # Add rows
            for _, row in df.iterrows():
                cells = table.add_row().cells
                for i, value in enumerate(row):
                    cells[i].text = str(value)

            document.add_paragraph("""   """)

    # Save to a BytesIO buffer instead of disk
    docx_buffer = BytesIO()
    document.save(docx_buffer)
    docx_buffer.seek(0)  # Reset buffer position

    return docx_buffer


def generate_docx_from_grammar_json(grammar_json, language):
    h1_index = 0
    h2_index = 0
    document = Document()
    document.add_heading('{}: Elements of grammar.'.format(language), 0)
    for topic, content in grammar_json.items():
        h1_index += 1
        document.add_heading(f"{str(h1_index)}. {topic}", 1)
        for parameter, description in content.items():
            h2_index += 1
            document.add_heading(f"{str(h1_index)}.{str(h2_index)}. {topic}: {parameter}", 2)
            intro_text = f"""
            In {language}, {parameter} is mainly {description["main value"]}
            """
            p = document.add_paragraph(intro_text)
            for value, examples in description["examples by value"].items():
                document.add_heading(f"""Example of {value}: """, 3)
                example_counter = 0
                for example in examples:
                    example_counter += 1
                    document.add_paragraph("""Example {}""".format(example_counter), style='List Bullet')
                    pex = document.add_paragraph(" ", "Normal")
                    pex.add_run(f'{example["translation"]}', style='Strong')
                    document.add_paragraph(f'{example["english sentence"]}', "Normal")


                    # Define the number of rows (one header + words) and columns
                    num_words = len(example["gloss"])
                    table = document.add_table(rows=num_words + 1, cols=4, style="Light Shading Accent 1")  # Fixed column count

                    # Populate header row
                    hdr_cells = table.rows[0].cells
                    hdr_cells[0].text = language
                    hdr_cells[1].text = "Concept"
                    hdr_cells[2].text = "Internal Particularisation"
                    hdr_cells[3].text = "Relational Particularisation"

                    # Populate the table with data
                    for i, (w, g) in enumerate(example["gloss"].items(), start=1):
                        row_cells = table.rows[i].cells
                        row_cells[0].text = w
                        row_cells[1].text = g["concept"]
                        row_cells[2].text = g["internal particularization"]
                        row_cells[3].text = g["relational particularization"]
                    document.add_paragraph("""   """)

        # Save to a BytesIO buffer instead of disk
        docx_buffer = BytesIO()
        document.save(docx_buffer)
        docx_buffer.seek(0)  # Reset buffer position
        return docx_buffer
    return None


def parse_alterlingua(text):
    # Regex to find all target word blocks
    word_blocks = re.findall(r'(\S+)<([^>]*)>', text)

    results = []

    for target_word, content in word_blocks:
        if not content.strip():
            continue  # skip empty concept blocks

        # Split multiple concepts joined by '&'
        concepts = [c.strip() for c in content.split('&')]

        for idx, concept in enumerate(concepts, start=1):
            # Regex to extract the concept name and its IP / RP fields
            concept_match = re.match(r'([^()]+)\(([^)]*)\)', concept)
            if concept_match:
                concept_name, fields = concept_match.groups()
                concept_name = concept_name.strip()

                # Extract IP and RP using regex or string methods
                ip_match = re.search(r'IP:\s*([^|]*)', fields)
                rp_match = re.search(r'RP:\s*([^|]*)', fields)
                ip = ip_match.group(1).strip() if ip_match else ""
                rp = rp_match.group(1).strip() if rp_match else ""

                entry = {
                    "target_word": f"{target_word}({idx})" if len(concepts) > 1 else target_word,
                    "concept": concept_name,
                    "IP": ip,
                    "RP": rp
                }
                results.append(entry)

    return pd.DataFrame(results)

