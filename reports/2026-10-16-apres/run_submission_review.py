"""Run the existing review pipeline on a pinned, user-supplied revised PDF.

Usage: .venv/bin/python reports/2026-10-16-apres/run_submission_review.py /path/source.pdf
Requires Poppler (pdftotext and pdftoppm). No training is performed.
"""
from pathlib import Path
import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from langchain_core.messages import HumanMessage
from src import debate
from src.schemas import PaperContent
import main as pipeline

TITLE = 'APRES: An Agentic Paper Revision and Evaluation System'
OUT = ROOT / 'output/2026-10-16-apres'


def run(pdf_path):
    pdf_path = Path(pdf_path).resolve()
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != 'b0aa814ffa46de6faaa867dfceaac4a4f71d43f1a2e5a90e8d6d5d06e4dace57':
        raise ValueError('PDF does not match the pinned user-supplied APRES PDF')
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(['pdftotext', '-layout', str(pdf_path), str(OUT / 'paper.txt')], check=True)
    subprocess.run(['pdftoppm', '-scale-to', '1200', '-png', str(pdf_path), str(OUT / 'page')], check=True)
    pages = sorted(OUT.glob('page-*.png'))
    if len(pages) != 35:
        raise ValueError(f'Expected the pinned 35-page submission, got {len(pages)} pages')
    text = (OUT / 'paper.txt').read_text()
    paper = PaperContent(title=TITLE, main_text=TITLE + '\n\n' + text)
    prepared = OUT / 'paper_content.json'
    prepared.write_text(paper.model_dump_json(indent=2))
    images = [{
        'type': 'image_url',
        'image_url': {'url': 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode(), 'detail': 'high'},
    } for p in pages]
    original = debate._build_paper_ingestion_messages
    def ingestion(paper):
        messages = original(paper)
        messages.append(HumanMessage(content=[{'type': 'text', 'text':
            'The following are all 35 pages of the same submitted paper, in page order, including figures, tables, references and appendix.'}] + images))
        return messages
    debate._build_paper_ingestion_messages = ingestion
    metadata = {
        'title': TITLE,
        'forum': 'https://openreview.net/forum?id=I2hLjiqNAv',
        'source_pdf': 'User attachment: 5663_APRES_An_Agentic_Paper_Re.pdf',
        'version': 'Revised manuscript created 2025-12-03; not the initial review version',
        'source_pdf_sha256': hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        'text_characters': len(paper.main_text),
        'prepared_input_sha256': hashlib.sha256(prepared.read_bytes()).hexdigest(),
        'page_images': len(images),
        'image_max_dimension': 1200,
        'scope': 'All 35 pages, including title, figures, tables, references and appendix',
        'models': {'debate':'gpt-4.1','relation_extraction':'gpt-4.1-mini','embedding':'text-embedding-3-small'},
        'trained_weights_present': (ROOT / 'models/hgt_ffn.pt').exists(),
        'official_reviews_or_author_replies_given_to_generation': False,
        'selection': 'User explicitly selected APRES and supplied this revised PDF; initial review version unavailable in public revision history',
        'started_at': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
    }
    (OUT / 'run_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    pipeline.main(str(prepared), str(OUT), str(OUT / 'no_trained_model.pt'))
    metadata['completed_at'] = datetime.now(ZoneInfo('Asia/Tokyo')).isoformat()
    (OUT / 'run_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    run(sys.argv[1])
