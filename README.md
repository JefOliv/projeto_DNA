# 🚀 Gestão Integrada: Controle Empresarial & Segurança

Este projeto nasceu da necessidade de centralizar as principais operações de uma empresa em uma única plataforma web de forma simples e intuitiva. Aqui, resolvi o desafio de integrar fluxos complexos (como controle de estoque e fluxo financeiro) a um sistema rígido de permissões de acesso, onde cada nível de usuário vê apenas o que lhe é de direito.

---

## 🎯 O que o sistema faz?

*   **📊 Inteligência Financeira & Estoque:** Controle de entradas e saídas de produtos integrado a relatórios visuais (gráficos) para tomada de decisão em tempo real.
*   **👥 Operação e Pessoas:** Gestão de funcionários, fornecedores e controle de treinamentos (com alertas/validações de presença e vencimento).
*   **📅 Organização:** Agenda integrada para compromissos e prazos do negócio.
*   **🔒 Segurança em Camadas (Gatekeeper):** O grande diferencial técnico. O sistema possui três níveis de acesso (Admin, Gestor e Funcionário). Novas contas entram como `Inativas` por padrão e **só são liberadas** após aprovação explícita no painel do Admin/Gestor.

---

## 🛠️ Tecnologias e Desafios Técnicos


*   **Backend:** Python com Flask (focado em rotas limpas e lógica estruturada)
*   **Banco de Dados:** SQLite (com relacionamentos bem definidos entre tabelas de usuários, estoque e finanças)
*   **Interface e Gráficos:** HTML5, CSS3, JavaScript e **Chart.js** para a renderização dinâmica dos relatórios.

---

## 🚀 Como Rodar o Projeto Localmente

### Pré-requisitos
Você vai precisar do **Git** e do **Python 3.x** instalados.

### Passo a Passo

```bash
# 1. Clonar o repositório
$ git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)

# 2. Entrar na pasta
$ cd seu-repositorio

# 3. Criar e ativar o ambiente virtual (Boa prática)
$ python -m venv venv
$ source venv/bin/activate  # Linux/Mac
$ venv\Scripts\activate     # Windows

# 4. Instalar as dependências do projeto
$ pip install -r requirements.txt

# 5. Iniciar a aplicação
$ python app.py
```
🧑‍💻 Autor
Desenvolvido por Jeferson — Conecte-se comigo no LinkedIn www.linkedin.com/in/jeferson-torres-a42948212 🚀

