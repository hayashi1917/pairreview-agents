"""Run the existing review pipeline on the pinned ICLR 2027 submission PDF of SciAudit.

Usage: .venv/bin/python reports/2026-11-12-sciaudit/run_submission_review.py /path/source.pdf
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

TITLE = 'SciAudit: Benchmarking MLLMs for Scientific Error Detection'
OUT = ROOT / 'output/2026-11-12-sciaudit'


def run(pdf_path):
    pdf_path = Path(pdf_path).resolve()
    if hashlib.sha256(pdf_path.read_bytes()).hexdigest() != '0fc360d7fb45b23c150eda7e1ab181c5b63ac9b5bb837268237f4a1157306a53':
        raise ValueError('PDF does not match the pinned SciAudit submission PDF')
    OUT.mkdir(parents=True, exist_ok=True)
    subprocess.run(['pdftotext', '-layout', str(pdf_path), str(OUT / 'paper.txt')], check=True)
    subprocess.run(['pdftoppm', '-scale-to', '1200', '-png', str(pdf_path), str(OUT / 'page')], check=True)
    pages = sorted(OUT.glob('page-*.png'))
    if len(pages) != 46:
        raise ValueError(f'Expected the pinned 46-page submission, got {len(pages)} pages')
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
            'The following are all 46 pages of the same submitted paper, in page order, including figures, tables, references and appendix.'}] + images))
        return messages
    debate._build_paper_ingestion_messages = ingestion
    metadata = {
        'title': TITLE,
        'forum': 'https://openreview.net/forum?id=xagiYitqc0',
        'source_pdf': 'OpenReview /pdf/1ec14e1c42873058eb6366585960da4d37e5f4df.pdf, saved 2026-11-12 (SHA-1 878e5f236b500b2fb2fc989b84c091f9e33fa52c)',
        'version': 'ICLR 2027 submission as reviewed: PDF created 2026-09-25, submission last modified 2026-10-05, reviews released 2026-11-05, saved before any author response',
        'source_pdf_sha256': hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        'text_characters': len(paper.main_text),
        'prepared_input_sha256': hashlib.sha256(prepared.read_bytes()).hexdigest(),
        'page_images': len(images),
        'image_max_dimension': 1200,
        'scope': 'All 46 pages, including title, figures, tables, references and appendix',
        'models': {'debate':'gpt-4.1','relation_extraction':'gpt-4.1-mini','embedding':'text-embedding-3-small'},
        'trained_weights_present': (ROOT / 'models/hgt_ffn.pt').exists(),
        'official_reviews_or_author_replies_given_to_generation': False,
        'selection': 'User asked for one peer-review-related ICLR 2027 submission whose reviewed PDF is still available; SciAudit chosen for topic fit and specific reviews before seeing any generated output',
        'started_at': datetime.now(ZoneInfo('Asia/Tokyo')).isoformat(),
    }
    (OUT / 'run_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    pipeline.main(str(prepared), str(OUT), str(OUT / 'no_trained_model.pt'))
    metadata['completed_at'] = datetime.now(ZoneInfo('Asia/Tokyo')).isoformat()
    (OUT / 'run_metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    run(sys.argv[1])
