import json
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from libs import knowledge_graph_utils as kgu
from io import BytesIO

import jinja2

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

