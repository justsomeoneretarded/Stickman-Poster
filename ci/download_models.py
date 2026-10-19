from huggingface_hub import snapshot_download, hf_hub_download
from studio.writer import MODEL_ID, MODEL_REVISION
from studio.voice import MODEL_REVISIONS
from studio.local_llm import MODEL_FILE
hf_hub_download(MODEL_ID, MODEL_FILE, revision=MODEL_REVISION, local_dir='models/script-qwen3')
snapshot_download('ResembleAI/chatterbox-turbo', revision=MODEL_REVISIONS['turbo'],
                  local_dir='models/chatterbox-turbo', allow_patterns=['ve.safetensors', 's3gen_meanflow.safetensors',
                  't3_turbo_v1.safetensors', '*.json', '*.txt', '*.yaml'])

snapshot_download('Systran/faster-whisper-base.en', revision='3d3d5dee26484f91867d81cb899cfcf72b96be6c',
                  local_dir='models/asr-base-en', allow_patterns=['config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt'])
