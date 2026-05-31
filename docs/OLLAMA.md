# Ollama setup

FinOps AI Gateway uses Ollama for embeddings, simple-tier answers, and (optionally) local RAGAS judging.

## Default: bundled in Docker Compose

`docker compose up -d` starts `finops_ollama` on **http://localhost:11434**.

Pull required models (bootstrap script does this automatically):

```powershell
docker exec finops_ollama ollama pull nomic-embed-text
docker exec finops_ollama ollama pull qwen3:4b
```

| Model | Purpose |
|-------|---------|
| `nomic-embed-text` | Embeddings for ingest + retrieval |
| `qwen3:4b` | Simple-tier gateway answers (~2.5GB) |

Bundled Ollama runs **CPU-only** inside Docker. It is slower but reproducible on any machine without a GPU.

## Optional: host Ollama on Windows (GPU)

For faster demos on a machine with NVIDIA GPU (e.g. RTX 3050 4GB):

1. Install [Ollama for Windows](https://ollama.com/download).
2. Stop the compose service so port 11434 is free:

   ```powershell
   docker compose stop ollama
   ```

3. Pull models on the host:

   ```powershell
   ollama pull nomic-embed-text
   ollama pull qwen3:4b
   ```

4. Keep `.env` as:

   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   ```

The Python gateway always talks to `localhost:11434` — whether that is the Docker container or host Ollama.

## RAGAS eval only

If you run full local RAGAS judging (not the default demo path), you may also need:

```powershell
ollama pull llama3.2:1b
```

The interview demo publishes **saved 8-pair RAGAS scores** via `finops-publish-results` and does not re-run the judge.
