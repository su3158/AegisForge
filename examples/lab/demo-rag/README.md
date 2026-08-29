# AegisForge demo RAG lab

The RAG lab is shaped for Compose with Qdrant:

```yaml
qdrant:
  image: qdrant/qdrant:v1.19.0
  ports:
    - "6333:6333"
```

Seed documents live in `seed.jsonl`. The scanner slice only defines the lab
shape; the root Compose file is owned by the integration slice.

