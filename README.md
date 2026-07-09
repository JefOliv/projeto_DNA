# 🧬 DNA MANUTENÇÃO - Sistema de Gestão

O **DNA MANUTENÇÃO** é um sistema integrado de gestão interna desenvolvido para otimizar o controle de estoque, funcionários, fornecedores, cronogramas e treinamentos regulamentares dentro de setores industriais e de manutenção. 

A aplicação conta com controle estrito de níveis de acesso (RBAC), persistência robusta em banco de dados e automação de rotinas preventivas.

---

## 💡 A História do Projeto (Do Excel ao Flask)

Este projeto nasceu de um desafio real na minha empresa: ajudar uma amiga Técnica de Segurança do Trabalho a gerenciar o fluxo de pessoas e treinamentos. Inicialmente, a solução seria uma planilha de Excel. No entanto, decidi usar essa necessidade real como a oportunidade perfeita para consolidar meus estudos em programação.

Transformei o que seria uma planilha em uma aplicação web funcional, utilizando **IA como Copilot** para acelerar o desenvolvimento, debugar códigos e discutir a melhor arquitetura de software.

> ⚠️ **Status do Projeto:** Atualmente o projeto encontra-se pausado devido a compromissos pessoais e profissionais. Apesar de não estar 100% finalizado, a base estrutural, o modelo de banco de dados e os módulos principais estão totalmente funcionais e servem como um forte portfólio do meu avanço na engenharia de software.

---

## 🚀 Funcionalidades Principais

### 🔒 Autenticação & Segurança (RBAC)
*   **Hierarquia de Permissões:** Controle baseado em papéis (`Programador`, `Gestor` e setores específicos como *Elétrica, Eletrônica, Refrigeração, Almoxarifado, Segurança do Trabalho, etc.*).
*   **Acesso Restrito:** Usuários visualizam e interagem apenas com dados permitidos para o seu setor comercial ou técnico.
*   **Segurança Avançada:** Criptografia de senhas usando `scrypt` via `werkzeug.security`.
*   **Políticas de Acesso:** Restrição de login para domínio institucional (`@dnamanutencao.com`) e fluxo forçado de troca de senha no primeiro acesso.

### 👥 Módulo de Funcionários e Treinamentos
*   **Cadastro Completo:** Registro de dados pessoais, documentos, endereços, status PCD e upload seguro de fotos de perfil.
*   **Gestão Dinâmica:** Associação flexível de múltiplos treinamentos por funcionário com interface interativa em JavaScript Vanilla.
*   **Cálculo Automatizado de Status:** Propriedades inteligentes em Python calculam em tempo real o vencimento dos treinamentos, classificando-os em *Válido, Vencendo, Vencido, Precisa Fazer ou Concluído*.

### 📅 Próximos Módulos (Planejados / Em Desenvolvimento)
*   **Notificações Inteligentes:** Sistema de segundo plano com `APScheduler` para alertar gestores sobre treinamentos próximos ao vencimento.
*   **Controle de Estoque e Financeiro:** Histórico de movimentações (entradas/saídas vinculadas a funcionários) e gráficos gerenciais com `Chart.js`.
*   **Módulo de Fornecedores & Calendário:** Cadastro de parceiros comerciais e agenda integrada de eventos/manutenções.

---

## 🛠️ Tecnologias Utilizadas

### Backend
*   **Python 3.x** / **Flask** (Web Framework)
*   **PostgreSQL** (Banco de dados relacional)
*   **SQLAlchemy** (ORM para persistência e modelagem de dados)
*   **Flask-Login** (Gerenciamento de sessão de usuários)
*   **Flask-APScheduler** (Agendamento de tarefas em background)

### Frontend
*   **Jinja2** (Renderização de templates HTML dinâmicos)
*   **HTML5 & CSS3** (Identidade visual moderna baseada nas cores corporativas `#004664` e `#15bdce`)
*   **JavaScript (Vanilla)** (Manipulação assíncrona e comportamento dinâmico do DOM)
*   **Font Awesome** (Pacote de ícones vetoriais)

---

## 📁 Estrutura do Projeto

```text
projeto-dna/
├── static/
│   ├── css/          # Arquivos de estilização (style, forms, tables)
│   ├── js/           # Scripts JavaScript (Vanilla JS)
│   └── uploads/      # Uploads de fotos dos funcionários (seguro via secure_filename)
├── templates/        # Arquivos HTML/Jinja2
├── models/
│   └── user.py       # Modelos do Banco de Dados (User, Employee, Training)
├── extensions.py     # Inicialização desacoplada do SQLAlchemy e LoginManager
├── app.py            # Fábrica do Aplicativo (Application Factory)
└── requirements.txt  # Dependências do projeto
