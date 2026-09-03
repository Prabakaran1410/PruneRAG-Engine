from locust import HttpUser, between, task


class RAGUser(HttpUser):
    wait_time = between(0.5, 2.0)

    @task
    def query_rag_endpoint(self):
        self.client.post("/api/v1/query", json={"query": "key financial performance metrics", "enable_pruning": True})