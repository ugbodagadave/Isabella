# Vision OCR Pivot Plan

## Objective
Replace the current OCR-only extractor with an IBM vision LLM (`ibm/granite-llama-3-2-11b-vision-instruct`) to improve text fidelity for receipts. Roll out behind a feature flag with tests and docs.

## Configuration (inline for this phase)
- `OCR_BACKEND=ocr|vision|hybrid`
- `VISION_MODEL_ID=ibm/granite-llama-3-2-11b-vision-instruct`
- `VISION_TEMPERATURE=0.0`
- `VISION_MAX_TOKENS=2048`
- `VISION_PAGE_LIMIT=4`
- `VISION_IMAGE_MAX_DIM=2048`

## Phased Rollout
- Phase 1 (non-breaking): Add `VisionTextExtractor` that outputs plain text. Keep the rest of the pipeline the same (Vision → text → existing `ReceiptProcessor`).
- Phase 2 (optional): Let the vision model produce structured JSON; keep Granite as fallback.

## Components to Add
- `models/vision_client.py`
  - Multimodal call to watsonx vision-instruct endpoint.
  - Reuse IAM token flow; retries with backoff.
- `tools/vision_text_extractor.py`
  - Input: image/PDF; Output: text only.
  - PDF rendering at 300 DPI (up to `VISION_PAGE_LIMIT` pages).
  - Image downscaling to `VISION_IMAGE_MAX_DIM` max dimension.
- `config/prompts.py`
  - `VISION_RECEIPT_OCR_PROMPT` for text-only transcription.

## Runner Wiring
- In `tools/slack_socket_runner.py`, choose extractor based on `OCR_BACKEND`:
  - `ocr`: use existing `TextExtractor`
  - `vision`: use `VisionTextExtractor`
  - `hybrid`: try vision, fallback to OCR on failure

## Prompt (text-only OCR)
System:
- "You are a receipt OCR engine. Transcribe the receipt exactly as printed."
- "Return ONLY the transcribed text. No explanations. No markdown."
User:
- "Extract every line. Preserve numeric formatting and decimal points. Do not infer; transcribe only. If illegible, output '?' for characters."

## Data Quality Controls
- Keep `_extract_total_from_text` override; accuracy improves with better text.
- Optional: item-sum consistency check (tolerance ±1%).

## Error Handling
- Hybrid fallback when `vision` fails/timeouts.
- Structured logs with durations for vision vs OCR.

## Testing (pytest)
- Unit:
  - `test_models/test_vision_client.py`: payload formation, retry on 429/5xx, result extraction.
  - `test_tools/test_vision_text_extractor.py`: image/PDF handling, page limits, failures.
  - `test_tools/test_total_extraction.py`: totals for Trader Joe's, Spotify.
- Integration:
  - Mock vision endpoint; set `OCR_BACKEND=vision`; ensure controller path works.
- E2E (optional): mark with `@pytest.mark.e2e` using real keys.
- Matrix: run suites with `OCR_BACKEND=ocr` and `vision` (vision mocked by default).

## Step-by-step Implementation
1. Branch created: `feat/vision-ocr-llama-3.2-11b`.
2. Add settings surface (constants inside new modules; no .env changes for this phase).
3. Implement `models/vision_client.py`.
4. Implement `tools/vision_text_extractor.py`.
5. Wire `slack_socket_runner.py` to `OCR_BACKEND`.
6. Add unit/integration tests; run `pytest -q`.
7. Update docs and memory-bank with feature flag and usage.
8. Push branch and open PR.
9. Manual smoke with Trader Joe's receipt (`OCR_BACKEND=vision`).
10. Rollout: `hybrid` → `vision`.

## Risks & Mitigations
- Latency/cost: caching by content hash; fallback to OCR when needed.
- API limits: backoff retries; page limits.
- Very long receipts: image height downscale; multi-request chunking if necessary.
- Model drift: schema validation unchanged; totals check remains defensive. 