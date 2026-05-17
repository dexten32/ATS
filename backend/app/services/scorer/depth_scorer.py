import re
from typing import Dict, Any, List

class DepthScorer:
    @staticmethod
    def calculate_technical_depth(text_lower: str, power_verbs: int) -> Dict[str, Any]:
        known_tools = [
            "python","java","javascript","typescript","node","react","django","flask","spring",
            "docker","kubernetes","redis","mongodb","postgresql","mysql","kafka","rabbitmq",
            "aws","gcp","azure","terraform","nginx","linux","git","graphql","fastapi",
            "oracle","rman","asm","oem","data guard","elasticsearch","cassandra","spark",
            "hadoop","airflow","pytorch","tensorflow","scikit","pandas","numpy",
            "keras", "opencv", "spacy", "nltk", "huggingface", "transformers", "langchain",
            "llama", "openai", "pinecone", "weaviate", "milvus", "dvc", "mlflow", "sagemaker",
            "wandb", "onnx", "tensorboard", "xgboost", "lightgbm", "catboost",
            "langgraph", "ollama", "faiss", "hnsw", "chromadb", "qdrant", "mistral", "anthropic",
            "clickhouse", "snowflake", "databricks", "airflow", "dagster", "prefect",
            "prometheus", "grafana", "opentelemetry", "datadog", "new relic", "splunk", "elk"
        ]
        
        verified_tools = set()
        implementation_keywords = ["troubleshot", "debugged", "refactored", "root cause", "concurrency", "bottleneck", "profiling", "migration", "failover", "idempotency", "zero-downtime", "managed", "deployed", "implemented", "optimized", "integrated", "tuned", "upgraded"]
        
        sentences = re.split(r'[.\n]', text_lower)
        for s in sentences:
            if len(s.strip()) < 10: continue
            has_impl = any(kw in s for kw in implementation_keywords)
            for tool in known_tools:
                if tool in s:
                    if has_impl: verified_tools.add(tool)
        
        tool_hits = len(verified_tools)
        raw_hits = sum(1 for t in known_tools if t in text_lower and t not in verified_tools)
        tool_score = min(50, tool_hits * 6 + raw_hits * 1.5)
        
        scale_signals = ["petabytes", "terabytes", "millions", "throughput", "concurrency", "low-latency", "high-availability", "distributed", "scalability"]
        scale_hits = sum(1 for s in scale_signals if s in text_lower)
        depth_score = min(25, (power_verbs * 2) + (scale_hits * 4))
        
        impact_hits = len(re.findall(r'\d+\s*%|\d+x\b|reduced|improved|increased|saved|latency', text_lower))
        impact_score = min(25, 10 + (impact_hits - 1) * 3) if impact_hits > 0 else 0
        
        return {
            "total_depth": tool_score + depth_score + impact_score,
            "tool_score": tool_score,
            "depth_score": depth_score,
            "impact_score": impact_score,
            "verified_tools": list(verified_tools),
            "tool_hits": tool_hits
        }
