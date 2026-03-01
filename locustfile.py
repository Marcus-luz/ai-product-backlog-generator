from locust import HttpUser, task, between

class AIProductOwnerUser(HttpUser):
    # Simula o tempo de leitura de um usuário real entre um clique e outro (1 a 3 segundos)
    wait_time = between(1, 3)
    
    def on_start(self):
        """Este método roda uma vez para cada usuário simulado assim que ele nasce."""
        # Vamos fazer login para pegar o JWT
        response = self.client.post("/auth/login", json={
            "username": "po_cypress", # Use o usuário que criamos no teste automatizado
            "password": "senha_segura"
        })
        
        # Se o login der certo, guardamos o token no header para as próximas requisições
        if response.status_code == 200:
            token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {token}"})

    @task(3)
    def view_dashboard(self):
        """Simula o usuário abrindo a tela de Dashboard principal"""
        self.client.get("/dashboard")

    @task(1)
    def fetch_api_products(self):
        """Simula o usuário buscando os produtos via API"""
        # Substitua /products pela rota exata da sua API que retorna os projetos em JSON
        self.client.get("/products")