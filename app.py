# -*- coding: utf-8 -*-
import os
import pandas as pd
from datetime import datetime, date, timedelta
from functools import wraps
from threading import Thread, Lock
from dateutil import tz
from dateutil.relativedelta import relativedelta

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from flask_apscheduler import APScheduler
from sqlalchemy import func, and_, or_

# --- Configurações do Flask ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui_coloque_uma_forte_e_unica'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:testpass@127.0.0.1:5432/dnaman_db?client_encoding=UTF8&application_name=dnaman_app&options=-c%20client_encoding%3DUTF8'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SERVER_NAME'] = '127.0.0.1:5000'
app.config['PREFERRED_URL_SCHEME'] = 'http'

db = SQLAlchemy(app)

app.jinja_env.globals.update(now=datetime.now)

# --- Configurações para Upload de Imagens ---
UPLOAD_FOLDER = 'static/uploads/fotos_funcionarios'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Funções Auxiliares (Definidas antes dos Modelos para evitar NameErrors) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logado' not in session or not session['logado']:
            flash('Você precisa fazer login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

LOCAL_TZ = tz.gettz('America/Sao_Paulo')
SCHEDULER_TZ = tz.gettz('America/Sao_Paulo')

def convert_utc_to_local(utc_dt):
    if utc_dt is None:
        return None
    utc_dt_aware = utc_dt.replace(tzinfo=tz.tzutc())
    return utc_dt_aware.astimezone(LOCAL_TZ)

def get_now_local_aware():
    return datetime.now(LOCAL_TZ)

def get_now_utc_aware():
    return datetime.now(tz.tzutc())

def calcular_idade(data_nascimento):
    today = date.today()
    if not data_nascimento:
        return None
    return today.year - data_nascimento.year - ((today.month, today.day) < (data_nascimento.month, data_nascimento.day))


# --- Modelos de Banco de Dados ---
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(20), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)

    def set_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def __repr__(self):
        return f"Usuario('{self.usuario}', '{self.matricula}')"

class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco = db.Column(db.Float, nullable=False)
    estoque_minimo = db.Column(db.Integer, default=5, nullable=False)

    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=True)
    fornecedor = db.relationship('Fornecedor', backref='produtos_fornecidos', lazy=True)

    ca_numero = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"Produto('{self.nome}', '{self.quantidade}', '{self.preco}', Min: '{self.estoque_minimo}')"

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    descricao = db.Column(db.Text, nullable=True)
    local = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Evento('{self.titulo}', '{self.data_hora}')"

SETORES = [
    'Administrativo', 'Áreas Verdes', 'BHS Doméstico', 'BHS Internacional',
    'Civil', 'Elétrica', 'Eletrônica', 'Refrigeração', 'BMS', 'Hidráulica'
]

class Funcionario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    funcao = db.Column(db.String(100), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    data_nascimento = db.Column(db.Date, nullable=True)
    pcd = db.Column(db.Boolean, default=False)
    setor = db.Column(db.String(100), nullable=False)
    foto_url = db.Column(db.String(255), nullable=True)
    comentarios = db.Column(db.Text, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email_pessoal = db.Column(db.String(100), nullable=True)
    endereco_rua = db.Column(db.String(150), nullable=True)
    endereco_numero = db.Column(db.String(20), nullable=True)
    endereco_complemento = db.Column(db.String(100), nullable=True)
    endereco_bairro = db.Column(db.String(100), nullable=True)
    endereco_cidade = db.Column(db.String(100), nullable=True)
    endereco_estado = db.Column(db.String(50), nullable=True)
    endereco_pais = db.Column(db.String(50), nullable=True)
    endereco_cep = db.Column(db.String(10), nullable=True)
    rg_numero = db.Column(db.String(20), nullable=True)
    rg_estado_emissor = db.Column(db.String(2), nullable=True)
    rg_orgao_emissor = db.Column(db.String(20), nullable=True)
    rg_data_emissao = db.Column(db.Date, nullable=True)
    cpf_numero = db.Column(db.String(14), unique=True, nullable=True) # CPF é único, mas pode ser nulo
    ctps_numero = db.Column(db.String(20), nullable=True)
    ctps_serie = db.Column(db.String(10), nullable=True)
    ctps_estado_emissor = db.Column(db.String(2), nullable=True)
    ctps_data_emissao = db.Column(db.Date, nullable=True)
    pis_numero = db.Column(db.String(15), nullable=True)
    titulo_eleitor_numero = db.Column(db.String(20), nullable=True)
    titulo_eleitor_zona = db.Column(db.String(10), nullable=True)
    titulo_eleitor_secao = db.Column(db.String(10), nullable=True)
    certificado_reservista_numero = db.Column(db.String(20), nullable=True)
    cnh_numero = db.Column(db.String(20), nullable=True)
    cnh_orgao_emissor = db.Column(db.String(20), nullable=True)
    cnh_estado_emissor = db.Column(db.String(2), nullable=True)
    cnh_data_emissao = db.Column(db.Date, nullable=True)
    cnh_data_vencimento = db.Column(db.Date, nullable=True)
    genero = db.Column(db.String(20), nullable=True)
    nacionalidade = db.Column(db.String(50), nullable=True)
    naturalidade_cidade = db.Column(db.String(100), nullable=True)
    naturalidade_estado = db.Column(db.String(50), nullable=True)

    movimentacoes = db.relationship('MovimentacaoEstoque', backref='funcionario', lazy=True)

    def __repr__(self):
        return f"Funcionario('{self.nome_completo}', '{self.matricula}')"

class MovimentacaoEstoque(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionario.id'), nullable=True)
    tipo_movimentacao = db.Column(db.String(10), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    observacao = db.Column(db.Text, nullable=True)

    produto = db.relationship('Produto', backref='movimentacoes', lazy=True)

    def __repr__(self):
        return f"MovimentacaoEstoque(Produto ID: {self.produto_id}, Tipo: {self.tipo_movimentacao}, Qtd: {self.quantidade})"

class Fornecedor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), unique=True, nullable=False)
    contato = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    tipo_fornecedor = db.Column(db.String(50), nullable=False, default='compra_produtos')

    itens = db.relationship('FornecedorItem', backref='fornecedor', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"Fornecedor('{self.nome}')"

class FornecedorItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedor.id'), nullable=False)
    nome_produto_servico = db.Column(db.String(150), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    valor_unidade = db.Column(db.Float, nullable=False)
    quantidade_comprada = db.Column(db.Integer, nullable=True)
    data_compra_aluguel = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    setor = db.Column(db.String(100), nullable=False)

    valor_diaria = db.Column(db.Float, nullable=True)
    data_inicio_aluguel = db.Column(db.Date, nullable=True)
    data_fim_aluguel = db.Column(db.Date, nullable=True)

    def __repr__(self):
        return f"FornecedorItem('{self.nome_produto_servico}', Forn: {self.fornecedor_id}')"


# --- Criação do Banco de Dados e Usuário Admin (apenas na primeira execução) ---
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(usuario='admin').first():
        admin_user = Usuario(usuario='admin', matricula='0001')
        admin_user.set_senha('1234')
        db.session.add(admin_user)
        db.session.commit()
        print("Usuário 'admin' com senha '1234' e matrícula '0001' criado!")


# --- Variáveis Globais para Notificações ---
current_active_alerts = {}
current_active_alerts_lock = Lock()


# --- Tarefas Agendadas (APScheduler) - check_notifications() ---
def check_notifications():
    global current_active_alerts
    found_alerts = []

    now_local = get_now_local_aware()
    
    with app.app_context():
        today_start_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_start_local = today_start_local + timedelta(days=1)
        day_after_tomorrow_start_local = tomorrow_start_local + timedelta(days=1)

        today_events = Evento.query.filter(
            Evento.data_hora >= today_start_local.astimezone(tz.tzutc()),
            Evento.data_hora < tomorrow_start_local.astimezone(tz.tzutc())
        ).order_by(Evento.data_hora).all()
        for event in today_events:
            event_datetime_local = convert_utc_to_local(event.data_hora)
            found_alerts.append({
                'id': f"event_{event.id}",
                'type': 'info',
                'message': f'Lembrete: Evento "{event.titulo}" é HOJE às {event_datetime_local.strftime("%H:%M")}.',
                'datetime': event_datetime_local.strftime('%d/%m/%Y %H:%M'),
                'link': url_for('editar_evento', id=event.id)
            })

        tomorrow_events = Evento.query.filter(
            Evento.data_hora >= tomorrow_start_local.astimezone(tz.tzutc()),
            Evento.data_hora < day_after_tomorrow_start_local.astimezone(tz.tzutc())
        ).order_by(Evento.data_hora).all()
        for event in tomorrow_events:
            event_datetime_local = convert_utc_to_local(event.data_hora)
            found_alerts.append({
                'id': f"event_{event.id}",
                'type': 'info',
                'message': f'Lembrete: Evento "{event.titulo}" é AMANHÃ às {event_datetime_local.strftime("%H:%M")}.',
                'datetime': event_datetime_local.strftime('%d/%m/%Y %H:%M'),
                'link': url_for('editar_evento', id=event.id)
            })

        produtos_estoque_baixo = Produto.query.filter(Produto.quantidade <= Produto.estoque_minimo).all()
        for produto_alerta in produtos_estoque_baixo:
            found_alerts.append({
                'id': f"product_{produto_alerta.id}",
                'type': 'warning',
                'message': f'ALERTA: O produto "{produto_alerta.nome}" está com estoque baixo ({produto_alerta.quantidade} unidades).',
                'datetime': now_local.strftime('%d/%m/%Y %H:%M'),
                'link': url_for('editar_produto_individual', id=produto_alerta.id)
            })

    with current_active_alerts_lock:
        new_active_alerts = {}
        for alert in found_alerts:
            new_active_alerts[alert['id']] = alert
        current_active_alerts = new_active_alerts

    print(f"[{get_now_local_aware().strftime('%Y-%m-%d %H:%M:%S')}] Notificações verificadas. Total de alertas ativos: {len(current_active_alerts)}")

# --- Inicialização do Scheduler ---
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def _check_notifications_wrapped():
    with app.app_context():
        check_notifications()

if not scheduler.get_job('check_notifications_job'):
    scheduler.add_job(id='check_notifications_job', func=_check_notifications_wrapped, trigger='interval', minutes=1, timezone=SCHEDULER_TZ)
    print("Tarefa 'check_notifications_job' adicionada ao scheduler.")


# --- Context Processor para Notificações no Header ---
@app.context_processor
def inject_notifications_context():
    if 'seen_notification_ids' not in session or not isinstance(session['seen_notification_ids'], set):
        session['seen_notification_ids'] = set(session.get('seen_notification_ids', []))
        session.modified = True

    seen_ids_for_this_request = session['seen_notification_ids']

    unread_notifications_list = []
    unread_count = 0

    with current_active_alerts_lock:
        all_active_alerts_dict = current_active_alerts.copy()

    for alert_id, alert_details in all_active_alerts_dict.items():
        if alert_id not in seen_ids_for_this_request:
            unread_notifications_list.append(alert_details)
            unread_count += 1
    
    session['seen_notification_ids'] = list(seen_ids_for_this_request)
    session.modified = True

    return {
        'global_notifications_list': unread_notifications_list,
        'notifications_count': unread_count
    }

# --- Nova Rota API para Marcar Notificações como Lidas ---
@app.route('/api/notifications/mark_as_read', methods=['POST'])
@login_required
def mark_notifications_as_read():
    if 'seen_notification_ids' not in session or not isinstance(session['seen_notification_ids'], set):
        session['seen_notification_ids'] = set(session.get('seen_notification_ids', []))
        session.modified = True

    seen_ids_for_this_request = session['seen_notification_ids']

    with current_active_alerts_lock:
        for alert_id in current_active_alerts.keys():
            seen_ids_for_this_request.add(alert_id)
    
    session['seen_notification_ids'] = list(seen_ids_for_this_request)
    
    session.modified = True
    print(f"[{get_now_local_aware().strftime('%Y-%m-%d %H:%M:%S')}] Notificações marcadas como lidas na sessão do usuário {session.get('usuario')}.")

    return jsonify({'status': 'success', 'message': 'Notificações marcadas como lidas.'})


# --- ROTAS ---
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'logado' in session and session['logado']:
        return redirect(url_for('painel'))

    if request.method == 'POST':
        usuario_digitado = request.form['usuario']
        senha_digitada = request.form['senha']

        usuario_bd = Usuario.query.filter_by(usuario=usuario_digitado).first()

        if usuario_bd and usuario_bd.check_senha(senha_digitada):
            session['logado'] = True
            session['usuario'] = usuario_bd.usuario
            session['matricula'] = usuario_bd.matricula
            flash(f'Bem-vindo, {usuario_bd.usuario}!', 'success')
            return redirect(url_for('painel'))
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('logado', None)
    session.pop('usuario', None)
    session.pop('matricula', None)
    
    if 'seen_notification_ids' in session:
        if isinstance(session['seen_notification_ids'], set):
            session['seen_notification_ids'] = list(session['seen_notification_ids'])
            session.modified = True
        session.pop('seen_notification_ids', None)
    flash('Você foi desconectado.', 'info')
    return redirect(url_for('login'))

@app.route('/painel')
@login_required
def painel():
    return render_template('painel.html',
                           usuario=session.get('usuario'),
                           matricula=session.get('matricula'))

# --- ROTAS DE ESTOQUE (EDITOR PRODUTO) ---
@app.route('/editor_produto', methods=['GET'])
@login_required
def editor_produto():
    filtro = request.args.get('filtro', '').strip().lower()
    estoque_baixo_param = request.args.get('estoque_baixo')

    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')

    query = Produto.query.outerjoin(Fornecedor)

    if filtro:
        if filtro.isdigit():
            query = query.filter(or_(Produto.id == int(filtro), Fornecedor.id == int(filtro)))
        else:
            query = query.filter(or_(
                Produto.nome.ilike(f'%{filtro}%'),
                Produto.ca_numero.ilike(f'%{filtro}%'),
                Fornecedor.nome.ilike(f'%{filtro}%')
            ))

    if estoque_baixo_param == 'true':
        query = query.filter(Produto.quantidade <= Produto.estoque_minimo)

    if sort_by == 'id':
        query = query.order_by(Produto.id.asc() if sort_order == 'asc' else Produto.id.desc())
    elif sort_by == 'nome':
        query = query.order_by(Produto.nome.asc() if sort_order == 'asc' else Produto.nome.desc())
    elif sort_by == 'quantidade':
        query = query.order_by(Produto.quantidade.asc() if sort_order == 'asc' else Produto.quantidade.desc())
    elif sort_by == 'preco':
        query = query.order_by(Produto.preco.asc() if sort_order == 'asc' else Produto.preco.desc())
    elif sort_by == 'estoque_minimo':
        query = query.order_by(Produto.estoque_minimo.asc() if sort_order == 'asc' else Produto.estoque_minimo.desc())
    elif sort_by == 'fornecedor':
        query = query.order_by(Fornecedor.nome.asc() if sort_order == 'asc' else Fornecedor.nome.desc())
    elif sort_by == 'ca_numero':
        query = query.order_by(Produto.ca_numero.asc() if sort_order == 'asc' else Produto.ca_numero.desc())
    else:
        query = query.order_by(Produto.id.asc())

    produtos = query.all()

    produtos_com_alerta = []
    for p in produtos:
        alerta = p.quantidade <= p.estoque_minimo
        produtos_com_alerta.append({
            'produto': p,
            'alerta_estoque_baixo': alerta
        })

    fornecedores_para_autocomplete = Fornecedor.query.order_by(Fornecedor.nome).all()

    return render_template('editor_produto.html',
                           produtos=produtos_com_alerta,
                           usuario=session.get('usuario'),
                           matricula=session.get('matricula'),
                           filtro=filtro,
                           estoque_baixo_selecionado=estoque_baixo_param == 'true',
                           current_sort_by=sort_by,
                           current_sort_order=sort_order,
                           fornecedores_para_autocomplete=fornecedores_para_autocomplete)

@app.route('/adicionar_produto', methods=['POST'])
@login_required
def adicionar_produto():
    print(f"SETORES content: {SETORES}")
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])
        estoque_minimo = int(request.form.get('estoque_minimo', 5))

        fornecedor_id = request.form.get('fornecedor_id', type=int)
        ca_numero = request.form.get('ca_numero', '').strip()

        if not nome or quantidade < 0 or preco < 0 or estoque_minimo < 0:
            return render_template('adicionar_produto.html', setores=SETORES,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   nome_produto_input=request.form.get('nome', ''),
                                   quantidade_input=request.form.get('quantidade', 1),
                                   preco_input=request.form.get('preco', 0.00),
                                   estoque_minimo_input=request.form.get('estoque_minimo', 5),
                                   fornecedor_autocomplete_input=request.form.get('fornecedor_autocomplete', ''),
                                   fornecedor_id_input=request.form.get('fornecedor_id', ''),
                                   ca_numero_input=request.form.get('ca_numero', '')
                                   )

        if fornecedor_id is not None:
            fornecedor = db.session.get(Fornecedor, fornecedor_id)
            if not fornecedor:
                return render_template('adicionar_produto.html', setores=SETORES,
                                       usuario=session.get('usuario'), matricula=session.get('matricula'),
                                       nome_produto_input=request.form.get('nome', ''),
                                       quantidade_input=request.form.get('quantidade', 1),
                                       preco_input=request.form.get('preco', 0.00),
                                       estoque_minimo_input=request.form.get('estoque_minimo', 5),
                                       fornecedor_autocomplete_input=request.form.get('fornecedor_autocomplete', ''),
                                       fornecedor_id_input=request.form.get('fornecedor_id', ''),
                                       ca_numero_input=request.form.get('ca_numero', '')
                                       )
        else:
            fornecedor_id = None

        produto_existente = Produto.query.filter(func.lower(Produto.nome) == func.lower(nome)).first()

        if produto_existente:
            quantidade_anterior = produto_existente.quantidade
            produto_existente.quantidade += quantidade
            produto_existente.preco = preco
            produto_existente.estoque_minimo = estoque_minimo
            produto_existente.fornecedor_id = fornecedor_id
            produto_existente.ca_numero = ca_numero

            movimentacao = MovimentacaoEstoque(
                produto_id=produto_existente.id,
                tipo_movimentacao='entrada',
                quantidade=quantidade,
                observacao=f"Entrada por adição/atualização. Quantidade anterior: {quantidade_anterior}"
            )
            db.session.add(movimentacao)
            flash(f'Quantidade de "{produto_existente.nome}" atualizada e entrada registrada.', 'success')

        else:
            novo = Produto(
                nome=nome,
                quantidade=quantidade,
                preco=preco,
                estoque_minimo=estoque_minimo,
                fornecedor_id=fornecedor_id,
                ca_numero=ca_numero
            )
            db.session.add(novo)
            db.session.flush()

            movimentacao = MovimentacaoEstoque(
                produto_id=novo.id,
                tipo_movimentacao='entrada',
                quantidade=quantidade,
                observacao="Primeira entrada do produto"
            )
            db.session.add(movimentacao)
            flash(f'Novo produto "{novo.nome}" adicionado com sucesso!', 'success')

        db.session.commit()
        return redirect(url_for('editor_produto'))

@app.route('/excluir_produto/<int:id>')
@login_required
def excluir_produto(id):
    produto = db.session.get(Produto, id)
    if produto is None:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('editor_produto'))

    MovimentacaoEstoque.query.filter_by(produto_id=id).delete()

    db.session.delete(produto)
    db.session.commit()
    flash(f'Produto "{produto.nome}" e seu histórico de movimentação excluídos com sucesso.', 'success')
    return redirect(url_for('editor_produto'))

@app.route('/atualizar_produto/<int:id>', methods=['POST'])
@login_required
def atualizar_produto(id):
    produto = db.session.get(Produto, id)
    if produto is None:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('editor_produto'))

    quantidade_anterior = produto.quantidade

    produto.nome = request.form['nome'].strip()
    produto.quantidade = int(request.form['quantidade'])
    produto.preco = float(request.form['preco'])
    estoque_minimo = int(request.form.get('estoque_minimo', 5))
    produto.estoque_minimo = estoque_minimo

    fornecedor_id = request.form.get('fornecedor_id', type=int)
    ca_numero = request.form.get('ca_numero', '').strip()

    if fornecedor_id is not None:
        fornecedor = db.session.get(Fornecedor, fornecedor_id)
        if not fornecedor:
            flash('Fornecedor selecionado não é válido. Por favor, selecione da lista de sugestões.', 'danger')
            return render_template('editar_produto.html', produto=produto,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   fornecedor_nome_atual=request.form.get('fornecedor_autocomplete', ''),
                                   fornecedor_id_atual='',
                                   ca_numero_atual=ca_numero)
    else:
        fornecedor_id = None

    produto.fornecedor_id = fornecedor_id
    produto.ca_numero = ca_numero

    if produto.quantidade < 0 or produto.preco < 0 or estoque_minimo < 0:
        flash('Por favor, preencha todos os campos corretamente e com valores não negativos.', 'danger')
        return render_template('editar_produto.html', produto=produto,
                               usuario=session.get('usuario'), matricula=session.get('matricula'),
                               fornecedor_nome_atual=produto.fornecedor.nome if produto.fornecedor else '',
                               fornecedor_id_atual=produto.fornecedor_id if produto.fornecedor_id else '',
                               ca_numero_atual=produto.ca_numero)

    if produto.quantidade != quantidade_anterior:
        tipo = 'entrada' if produto.quantidade > quantidade_anterior else 'saida'
        quantidade_movimentada = abs(produto.quantidade - quantidade_anterior)

        movimentacao = MovimentacaoEstoque(
            produto_id=produto.id,
            tipo_movimentacao=tipo,
            quantidade=quantidade_movimentada,
            observacao=f"Ajuste manual de estoque. Quantidade anterior: {quantidade_anterior}"
        )
        db.session.add(movimentacao)

    db.session.commit()
    flash(f'Produto "{produto.nome}" atualizado com sucesso!', 'success')
    return redirect(url_for('editor_produto'))

@app.route('/editar_produto_individual/<int:id>')
@login_required
def editar_produto_individual(id):
    produto = db.session.get(Produto, id)
    if produto is None:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('editor_produto'))

    fornecedor_nome_atual = produto.fornecedor.nome if produto.fornecedor else ''
    fornecedor_id_atual = produto.fornecedor_id if produto.fornecedor_id else ''
    fornecedores_para_autocomplete = Fornecedor.query.order_by(Fornecedor.nome).all()

    return render_template('editar_produto.html', produto=produto,
                           usuario=session.get('usuario'), matricula=session.get('matricula'),
                           fornecedor_nome_atual=fornecedor_nome_atual,
                           fornecedor_id_atual=fornecedor_id_atual,
                           ca_numero_atual=produto.ca_numero,
                           fornecedores_para_autocomplete=fornecedores_para_autocomplete)

@app.route('/limpar-filtro_produto')
@login_required
def limpar_filtro_produto():
    return redirect(url_for('editor_produto'))

# --- ROTAS DE HISTÓRICO DE ESTOQUE ---
@app.route('/historico_estoque')
@login_required
def historico_estoque():
    filtro = request.args.get('filtro', '').strip().lower()
    filtro_tipo_mov = request.args.get('filtro_tipo_mov', '').strip()
    data_inicio_str = request.args.get('data_inicio', '').strip()
    data_fim_str = request.args.get('data_fim', '').strip()

    sort_by = request.args.get('sort_by', 'data_hora')
    sort_order = request.args.get('sort_order', 'desc')

    query = MovimentacaoEstoque.query.join(Produto).outerjoin(Funcionario)

    if filtro:
        query = query.filter(or_(
            Produto.nome.ilike(f'%{filtro}%'),
            Funcionario.nome_completo.ilike(f'%{filtro}%')
        ))

    if filtro_tipo_mov in ['entrada', 'saida']:
        query = query.filter(MovimentacaoEstoque.tipo_movimentacao == filtro_tipo_mov)

    if data_inicio_str:
        try:
            data_inicio_obj = datetime.strptime(data_inicio_str, '%Y-%m-%d').replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.filter(MovimentacaoEstoque.data_hora >= data_inicio_obj.astimezone(tz.tzutc()))
        except ValueError:
            flash('Formato de Data de Início inválido.', 'warning')
    if data_fim_str:
        try:
            data_fim_obj = datetime.strptime(data_fim_str, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(MovimentacaoEstoque.data_hora <= data_fim_obj.astimezone(tz.tzutc()))
        except ValueError:
            flash('Formato de Data de Fim inválido.', 'warning')

    if sort_by == 'data_hora':
        query = query.order_by(MovimentacaoEstoque.data_hora.asc() if sort_order == 'asc' else MovimentacaoEstoque.data_hora.desc())
    elif sort_by == 'produto':
        query = query.order_by(Produto.nome.asc() if sort_order == 'asc' else Produto.nome.desc())
    elif sort_by == 'quantidade':
        query = query.order_by(MovimentacaoEstoque.quantidade.asc() if sort_order == 'asc' else MovimentacaoEstoque.quantidade.desc())
    elif sort_by == 'tipo_movimentacao':
        query = query.order_by(MovimentacaoEstoque.tipo_movimentacao.asc() if sort_order == 'asc' else MovimentacaoEstoque.tipo_movimentacao.desc())
    elif sort_by == 'funcionario':
        query = query.order_by(Funcionario.nome_completo.asc() if sort_order == 'asc' else Funcionario.nome_completo.desc())
    else:
        query = query.order_by(MovimentacaoEstoque.data_hora.desc())

    movimentacoes = query.all()

    movimentacoes_local = []
    for mov in movimentacoes:
        mov.data_hora_local = convert_utc_to_local(mov.data_hora)
        movimentacoes_local.append(mov)

    return render_template('historico_estoque.html', movimentacoes=movimentacoes_local,
                           usuario=session.get('usuario'), matricula=session.get('matricula'),
                           current_sort_by=sort_by,
                           current_sort_order=sort_order,
                           filtro=filtro,
                           filtro_tipo_mov=filtro_tipo_mov,
                           data_inicio=data_inicio_str,
                           data_fim=data_fim_str)


@app.route('/limpar_filtro_historico')
@login_required
def limpar_filtro_historico():
    return redirect(url_for('historico_estoque'))


# --- ROTAS DE FUNCIONÁRIOS ---
@app.route('/funcionarios')
@login_required
def funcionarios():
    filtro = request.args.get('filtro', '').strip().lower()
    sort_by = request.args.get('sort_by', 'nome_completo')
    sort_order = request.args.get('sort_order', 'asc')

    query = Funcionario.query

    if filtro:
        if filtro.isdigit():
            query = query.filter(Funcionario.matricula.ilike(f'%{filtro}%'))
        else:
            query = query.filter(or_(
                Funcionario.nome_completo.ilike(f'%{filtro}%'),
                Funcionario.funcao.ilike(f'%{filtro}%'),
                Funcionario.setor.ilike(f'%{filtro}%')
            ))

    if sort_by == 'nome_completo':
        query = query.order_by(Funcionario.nome_completo.asc() if sort_order == 'asc' else Funcionario.nome_completo.desc())
    elif sort_by == 'matricula':
        query = query.order_by(Funcionario.matricula.asc() if sort_order == 'asc' else Funcionario.matricula.desc())
    elif sort_by == 'funcao':
        query = query.order_by(Funcionario.funcao.asc() if sort_order == 'asc' else Funcionario.funcao.desc())
    elif sort_by == 'data_admissao':
        query = query.order_by(Funcionario.data_admissao.asc() if sort_order == 'asc' else Funcionario.data_admissao.desc())
    else:
        query = query.order_by(Funcionario.nome_completo.asc())

    funcionarios = query.all()
    return render_template('funcionarios.html', funcionarios=funcionarios,
                           usuario=session.get('usuario'), matricula=session.get('matricula'),
                           current_sort_by=sort_by,
                           current_sort_order=sort_order,
                           filtro=filtro)

@app.route('/limpar_filtro_funcionario')
@login_required
def limpar_filtro_funcionario():
    return redirect(url_for('funcionarios'))

# Rota para exibir detalhes de um funcionário
@app.route('/funcionarios/<int:id>')
@login_required
def detalhe_funcionario(id):
    funcionario = db.session.get(Funcionario, id)
    if funcionario is None:
        flash('Funcionário não encontrado.', 'danger')
        return redirect(url_for('funcionarios'))

    idade = calcular_idade(funcionario.data_nascimento)

    itens_pegos_query = MovimentacaoEstoque.query.filter_by(
        funcionario_id=id,
        tipo_movimentacao='saida'
    ).order_by(MovimentacaoEstoque.data_hora.desc()).all()

    itens_pegos_local = []
    for item_mov in itens_pegos_query:
        item_mov.data_hora_local = convert_utc_to_local(item_mov.data_hora)
        itens_pegos_local.append(item_mov)

    return render_template('detalhe_funcionario.html',
                           funcionario=funcionario,
                           idade=idade,
                           itens_pegos=itens_pegos_local,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))

# Rota para adicionar um novo funcionário
@app.route('/adicionar_funcionario', methods=['GET', 'POST'])
@login_required
def adicionar_funcionario():
    print(f"SETORES content: {SETORES}")
    if request.method == 'POST':
        # Instanciar um NOVO Funcionario
        # Obter CPF e tratar se for string vazia para salvar como None
        cpf_numero_form = request.form.get('cpf_numero', '').strip()
        cpf_numero_to_save = cpf_numero_form if cpf_numero_form else None

        novo_funcionario = Funcionario(
            nome_completo = request.form['nome_completo'].strip(),
            matricula = request.form['matricula'].strip(),
            funcao = request.form['funcao'].strip(),
            data_admissao = datetime.strptime(request.form['data_admissao'], '%Y-%m-%d').date(),
            data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else None,
            pcd = 'pcd' in request.form,
            setor = request.form['setor'].strip(),
            comentarios = request.form.get('comentarios', '').strip(),
            telefone = request.form.get('telefone', '').strip(),
            email_pessoal = request.form.get('email_pessoal', '').strip(),
            endereco_rua = request.form.get('endereco_rua', '').strip(),
            endereco_numero = request.form.get('endereco_numero', '').strip(),
            endereco_complemento = request.form.get('endereco_complemento', '').strip(),
            endereco_bairro = request.form.get('endereco_bairro', '').strip(),
            endereco_cidade = request.form.get('cidade', '').strip(),
            endereco_estado = request.form.get('estado', '').strip(),
            endereco_pais = request.form.get('pais', '').strip(),
            endereco_cep = request.form.get('cep', '').strip(),
            rg_numero = request.form.get('rg_numero', '').strip(),
            rg_estado_emissor = request.form.get('rg_estado_emissor', '').strip(),
            rg_orgao_emissor = request.form.get('rg_orgao_emissor', '').strip(),
            rg_data_emissao = datetime.strptime(request.form['rg_data_emissao'], '%Y-%m-%d').date() if request.form.get('rg_data_emissao') else None,
            cpf_numero = cpf_numero_to_save, # Usar o valor tratado para CPF
            ctps_numero = request.form.get('ctps_numero', '').strip(),
            ctps_serie = request.form.get('ctps_serie', '').strip(),
            ctps_estado_emissor = request.form.get('ctps_estado_emissor', '').strip(),
            ctps_data_emissao = datetime.strptime(request.form['ctps_data_emissao'], '%Y-%m-%d').date() if request.form.get('ctps_data_emissao') else None,
            pis_numero = request.form.get('pis_numero', '').strip(),
            titulo_eleitor_numero = request.form.get('titulo_eleitor_numero', '').strip(),
            titulo_eleitor_zona = request.form.get('titulo_eleitor_zona', '').strip(),
            titulo_eleitor_secao = request.form.get('titulo_eleitor_secao', '').strip(),
            certificado_reservista_numero = request.form.get('certificado_reservista_numero', '').strip(),
            cnh_numero = request.form.get('cnh_numero', '').strip(),
            cnh_orgao_emissor = request.form.get('cnh_orgao_emissor', '').strip(),
            cnh_estado_emissor = request.form.get('cnh_estado_emissor', '').strip(),
            cnh_data_emissao = datetime.strptime(request.form['cnh_data_emissao'], '%Y-%m-%d').date() if request.form.get('cnh_data_emissao') else None,
            cnh_data_vencimento = datetime.strptime(request.form['cnh_data_vencimento'], '%Y-%m-%d').date() if request.form.get('cnh_data_vencimento') else None,
            genero = request.form.get('genero', '').strip(),
            nacionalidade = request.form.get('nacionalidade', '').strip(),
            naturalidade_cidade = request.form.get('naturalidade_cidade', '').strip(),
            naturalidade_estado = request.form.get('naturalidade_estado', '').strip()
        )

        # Lidar com a foto
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                novo_funcionario.foto_url = url_for('uploaded_file', filename=unique_filename)
            else:
                flash('Tipo de arquivo de foto não permitido.', 'warning')
        
        # Adicionar o novo funcionário ao banco de dados
        db.session.add(novo_funcionario)
        db.session.commit()
        flash(f'Funcionário "{novo_funcionario.nome_completo}" adicionado com sucesso!', 'success')
        return redirect(url_for('funcionarios')) # Redireciona para a lista de funcionários

    # GET request: renderiza o formulário vazio para adicionar
    return render_template('adicionar_funcionario.html', setores=SETORES,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))

# Rota para servir arquivos de upload
@app.route('/uploads/fotos_funcionarios/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota para editar um funcionário existente
@app.route('/editar_funcionario/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_funcionario(id):
    funcionario = db.session.get(Funcionario, id)
    if funcionario is None:
        flash('Funcionário não encontrado.', 'danger')
        return redirect(url_for('funcionarios'))

    if request.method == 'POST':
        # Obter CPF do formulário e tratar para salvar como None se for string vazia
        cpf_numero_form = request.form.get('cpf_numero', '').strip()
        funcionario.cpf_numero = cpf_numero_form if cpf_numero_form else None

        funcionario.nome_completo = request.form['nome_completo'].strip()
        funcionario.matricula = request.form['matricula'].strip()
        funcionario.funcao = request.form['funcao'].strip()
        funcionario.data_admissao = datetime.strptime(request.form['data_admissao'], '%Y-%m-%d').date()
        funcionario.data_nascimento = datetime.strptime(request.form['data_nascimento'], '%Y-%m-%d').date() if request.form.get('data_nascimento') else None
        funcionario.pcd = 'pcd' in request.form
        funcionario.setor = request.form['setor'].strip()
        funcionario.comentarios = request.form.get('comentarios', '').strip()
        funcionario.telefone = request.form.get('telefone', '').strip()
        funcionario.email_pessoal = request.form.get('email_pessoal', '').strip()

        # Endereço
        funcionario.endereco_rua = request.form.get('endereco_rua', '').strip()
        funcionario.endereco_numero = request.form.get('endereco_numero', '').strip()
        funcionario.endereco_complemento = request.form.get('endereco_complemento', '').strip()
        funcionario.endereco_bairro = request.form.get('endereco_bairro', '').strip()
        funcionario.endereco_cidade = request.form.get('cidade', '').strip()
        funcionario.endereco_estado = request.form.get('estado', '').strip()
        funcionario.endereco_pais = request.form.get('pais', '').strip()
        funcionario.endereco_cep = request.form.get('cep', '').strip()

        # Documentos
        funcionario.rg_numero = request.form.get('rg_numero', '').strip()
        funcionario.rg_estado_emissor = request.form.get('rg_estado_emissor', '').strip()
        funcionario.rg_orgao_emissor = request.form.get('rg_orgao_emissor', '').strip()
        funcionario.rg_data_emissao = datetime.strptime(request.form['rg_data_emissao'], '%Y-%m-%d').date() if request.form.get('rg_data_emissao') else None
        
        funcionario.ctps_numero = request.form.get('ctps_numero', '').strip()
        funcionario.ctps_serie = request.form.get('ctps_serie', '').strip()
        funcionario.ctps_estado_emissor = request.form.get('ctps_estado_emissor', '').strip()
        funcionario.ctps_data_emissao = datetime.strptime(request.form['ctps_data_emissao'], '%Y-%m-%d').date() if request.form.get('ctps_data_emissao') else None
        funcionario.pis_numero = request.form.get('pis_numero', '').strip()
        funcionario.titulo_eleitor_numero = request.form.get('titulo_eleitor_numero', '').strip()
        funcionario.titulo_eleitor_zona = request.form.get('titulo_eleitor_zona', '').strip()
        funcionario.titulo_eleitor_secao = request.form.get('titulo_eleitor_secao', '').strip()
        funcionario.certificado_reservista_numero = request.form.get('certificado_reservista_numero', '').strip()
        funcionario.cnh_numero = request.form.get('cnh_numero', '').strip()
        funcionario.cnh_orgao_emissor = request.form.get('cnh_orgao_emissor', '').strip()
        funcionario.cnh_estado_emissor = request.form.get('cnh_estado_emissor', '').strip()
        funcionario.cnh_data_emissao = datetime.strptime(request.form['cnh_data_emissao'], '%Y-%m-%d').date() if request.form.get('cnh_data_emissao') else None
        funcionario.cnh_data_vencimento = datetime.strptime(request.form['cnh_data_vencimento'], '%Y-%m-%d').date() if request.form.get('cnh_data_vencimento') else None
        funcionario.genero = request.form.get('genero', '').strip()
        funcionario.nacionalidade = request.form.get('nacionalidade', '').strip()
        funcionario.naturalidade_cidade = request.form.get('naturalidade_cidade', '').strip()
        funcionario.naturalidade_estado = request.form.get('naturalidade_estado', '').strip()

        # Lidar com a atualização da foto
        if 'foto' in request.files:
            file = request.files['foto']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                # Remover foto antiga se existir
                if funcionario.foto_url:
                    old_filename = os.path.basename(funcionario.foto_url)
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                funcionario.foto_url = url_for('uploaded_file', filename=unique_filename)
            elif file.filename == '' and 'foto_manter_existente' not in request.form: # Se não enviou nova foto e não marcou para manter existente
                # Lógica para remover a foto se o campo estiver vazio e não for para manter
                if funcionario.foto_url:
                    old_filename = os.path.basename(funcionario.foto_url)
                    old_filepath = os.path.join(app.config['UPLOAD_FOLDER'], old_filename)
                    if os.path.exists(old_filepath):
                        os.remove(old_filepath)
                    funcionario.foto_url = None
            # else: Se o campo está vazio mas marcou para manter existente, não faz nada com a foto_url existente

        try:
            db.session.commit()
            flash(f'Funcionário "{funcionario.nome_completo}" atualizado com sucesso!', 'success')
            return redirect(url_for('detalhe_funcionario', id=funcionario.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar funcionário: {e}', 'danger')
            # Renderizar o formulário novamente com os dados e erros
            return render_template('editar_funcionario.html', funcionario=funcionario, setores=SETORES,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

    # GET request: renderiza o formulário preenchido para edição
    return render_template('editar_funcionario.html', funcionario=funcionario, setores=SETORES,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))


@app.route('/excluir_funcionario/<int:id>')
@login_required
def excluir_funcionario(id):
    funcionario = db.session.get(Funcionario, id)
    if funcionario is None:
        flash('Funcionário não encontrado.', 'danger')
        return redirect(url_for('funcionarios'))

    MovimentacaoEstoque.query.filter_by(funcionario_id=id).update({'funcionario_id': None})

    if funcionario.foto_url:
        try:
            filename = os.path.basename(funcionario.foto_url)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Arquivo de foto {filename} removido.")
        except Exception as e:
            print(f"Erro ao remover arquivo de foto: {e}")


    db.session.delete(funcionario)
    db.session.commit()
    flash(f'Funcionário "{funcionario.nome_completo}" excluído com sucesso.', 'success')
    return redirect(url_for('funcionarios'))

@app.route('/autocomplete/produtos')
@login_required
def autocomplete_produtos():
    term = request.args.get('term', '').strip()
    if not term:
        return jsonify([])

    produtos = Produto.query.filter(Produto.nome.ilike(f'%{term}%')).limit(10).all()
    
    suggestions = [{'label': p.nome, 'value': p.id} for p in produtos]
    return jsonify(suggestions)


@app.route('/autocomplete/funcionarios')
@login_required
def autocomplete_funcionarios():
    term = request.args.get('term', '').strip()
    if not term:
        return jsonify([])

    funcionarios = Funcionario.query.filter(
        or_(
            Funcionario.nome_completo.ilike(f'%{term}%'),
            Funcionario.matricula.ilike(f'%{term}%')
        )
    ).limit(10).all()

    suggestions = [{'label': f"{f.nome_completo} ({f.matricula})", 'value': f.id} for f in funcionarios]
    return jsonify(suggestions)

@app.route('/entregar_item', methods=['GET', 'POST'])
@login_required
def entregar_item():
    produtos_disponiveis = Produto.query.filter(Produto.quantidade > 0).order_by(Produto.nome).all()
    funcionarios_disponiveis = Funcionario.query.order_by(Funcionario.nome_completo).all()

    produto_nome_input = ''
    produto_id_input = ''
    funcionario_nome_input = ''
    funcionario_id_input = ''
    quantidade_entregue_input = 1
    observacao_input = ''

    if request.method == 'POST':
        produto_id_str = request.form['produto_id'].strip()
        funcionario_id_str = request.form['funcionario_id'].strip()

        produto_id = int(produto_id_str) if produto_id_str.isdigit() else None
        funcionario_id = int(funcionario_id_str) if funcionario_id_str.isdigit() else None
        
        quantidade_entregue_input = request.form['quantidade']
        observacao_input = request.form.get('observacao', '').strip()
        
        produto_nome_input = request.form.get('produto_nome', '').strip()
        funcionario_nome_input = request.form.get('funcionario_nome', '').strip()

        if produto_id is None:
            flash('Por favor, selecione um produto válido da lista de sugestões.', 'danger')
            return render_template('entregar_item.html', produtos=produtos_disponiveis, funcionarios=funcionarios_disponiveis,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   produto_nome_input=produto_nome_input, produto_id_input=produto_id_input,
                                   funcionario_nome_input=funcionario_nome_input, funcionario_id_input=funcionario_id_input,
                                   quantidade_entregue=quantidade_entregue_input, observacao=observacao_input)

        if funcionario_id is None:
            flash('Por favor, selecione um funcionário válido da lista de sugestões.', 'danger')
            return render_template('entregar_item.html', produtos=produtos_disponiveis, funcionarios=funcionarios_disponiveis,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   produto_nome_input=produto_nome_input, produto_id_input=produto_id_input,
                                   funcionario_nome_input=funcionario_nome_input, funcionario_id_input=funcionario_id_input,
                                   quantidade_entregue=quantidade_entregue_input, observacao=observacao_input)


        produto = db.session.get(Produto, produto_id)
        funcionario = db.session.get(Funcionario, funcionario_id)

        if not produto or not funcionario:
            flash('Produto ou funcionário não encontrados ou inválidos após a seleção.', 'danger')
            return render_template('entregar_item.html', produtos=produtos_disponiveis, funcionarios=funcionarios_disponiveis,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   produto_nome_input=produto_nome_input, produto_id_input=produto_id_input,
                                   funcionario_nome_input=funcionario_nome_input, funcionario_id_input=funcionario_id_input,
                                   quantidade_entregue=quantidade_entregue_input, observacao=observacao_input)
        
        try:
            quantidade_entregue = int(quantidade_entregue_input)
        except ValueError:
            flash('Quantidade inválida. Por favor, insira um número inteiro.', 'danger')
            return render_template('entregar_item.html', produtos=produtos_disponiveis, funcionarios=funcionarios_disponiveis,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   produto_nome_input=produto_nome_input, produto_id_input=produto_id_input,
                                   funcionario_nome_input=funcionario_nome_input, funcionario_id_input=funcionario_id_input,
                                   quantidade_entregue=quantidade_entregue_input, 
                                   observacao=observacao_input)


        if quantidade_entregue <= 0 or quantidade_entregue > produto.quantidade:
            flash(f'Quantidade inválida ou insuficiente no estoque para "{produto.nome}". Quantidade disponível: {produto.quantidade}', 'danger')
            return render_template('entregar_item.html', produtos=produtos_disponiveis, funcionarios=funcionarios_disponiveis,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'),
                                   produto_nome_input=produto_nome_input, produto_id_input=produto_id_input,
                                   funcionario_nome_input=funcionario_nome_input, funcionario_id_input=funcionario_id_input,
                                   quantidade_entregue=quantidade_entregue,
                                   observacao=observacao_input)

        produto.quantidade -= quantidade_entregue

        movimentacao = MovimentacaoEstoque(
            produto_id=produto.id,
            funcionario_id=funcionario.id,
            tipo_movimentacao='saida',
            quantidade=quantidade_entregue,
            observacao=observacao_input
        )
        db.session.add(movimentacao)
        db.session.commit()
        
        flash(f'{quantidade_entregue} unidades de "{produto.nome}" entregues a "{funcionario.nome_completo}". O estoque de "{produto.nome}" agora é de {produto.quantidade}.', 'success')
        
        funcionario_full_label = f"{funcionario.nome_completo} ({funcionario.matricula})"
        
        return render_template('entregar_item.html', produtos=Produto.query.filter(Produto.quantidade > 0).order_by(Produto.nome).all(),
                               funcionarios=funcionarios_disponiveis,
                               usuario=session.get('usuario'), matricula=session.get('matricula'),
                               produto_nome_input='',
                               produto_id_input='',
                               funcionario_nome_input=funcionario_full_label,
                               funcionario_id_input=funcionario.id,
                               quantidade_entregue=1,
                               observacao='')


    return render_template('entregar_item.html', produtos=produtos_disponiveis, funcionarios=funcionarios_disponiveis,
                           usuario=session.get('usuario'), matricula=session.get('matricula'),
                           produto_nome_input=produto_nome_input, produto_id_input=produto_id_input,
                           funcionario_nome_input=funcionario_nome_input, funcionario_id_input=funcionario_id_input,
                           quantidade_entregue=quantidade_entregue_input,
                           observacao=observacao_input)

# --- ROTAS DO CALENDÁRIO (JSON API - Frontend precisará de JS para renderizar) ---
@app.route('/calendario')
@login_required
def calendario():
    eventos = Evento.query.all()
    eventos_for_template = []
    for e in eventos:
        event_datetime_local = convert_utc_to_local(e.data_hora)
        eventos_for_template.append({
            'id': e.id,
            'title': e.titulo,
            'start': event_datetime_local.isoformat() if e.data_hora else None,
            'description': e.descricao,
            'local': e.local
        })

    return render_template('calendario.html',
                           usuario=session.get('usuario'),
                           matricula=session.get('matricula'),
                           eventos=eventos_for_template)

@app.route('/eventos', methods=['GET'])
@login_required
def listar_eventos():
    eventos = Evento.query.all()
    eventos_for_template = []
    for e in eventos:
        event_datetime_local_aware = convert_utc_to_local(e.data_hora)
        
        eventos_for_template.append({
            'id': e.id,
            'title': e.titulo,
            'start': event_datetime_local_aware.isoformat(),
            'end': event_datetime_local_aware.isoformat(),
            'description': e.descricao,
            'local': e.local,
            'url': url_for('editar_evento', id=e.id)
        })
    return jsonify(eventos_for_template)

@app.route('/adicionar_evento', methods=['POST'])
@login_required
def adicionar_evento():
    titulo = request.form['titulo'].strip()
    data_hora_str = request.form['data_hora']
    descricao = request.form.get('descricao', '').strip()
    local = request.form.get('local', '').strip()

    if not titulo:
        return jsonify({'status': 'error', 'message': 'O título do evento é obrigatório.'}), 400

    try:
        data_hora_naive_from_form = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
        
        # Compensação de 3 horas para fuso horário (GMT-03:00)
        data_hora_compensada = data_hora_naive_from_form + timedelta(hours=3) # <<< CORREÇÃO DE COMPENSAÇÃO
        
        novo_evento = Evento(
            titulo=titulo,
            data_hora=data_hora_compensada, # Salva a hora compensada no banco (naive)
            descricao=descricao,
            local=local
        )

        db.session.add(novo_evento)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Evento adicionado com sucesso!', 'event': {'id': novo_evento.id}}), 200

    except ValueError:
        return jsonify({'status': 'error', 'message': 'Formato de Data/Hora inválido. Use AAAA-MM-DDTHH:MM.'}), 400
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao adicionar evento: {e}")
        return jsonify({'status': 'error', 'message': 'Erro interno ao adicionar evento.'}), 500

@app.route('/editar_evento/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_evento(id):
    evento = db.session.get(Evento, id)
    if evento is None:
        flash('Evento não encontrado.', 'danger')
        return redirect(url_for('calendario'))

    if request.method == 'POST':
        evento.titulo = request.form['titulo'].strip()
        data_hora_str = request.form['data_hora']
        evento.descricao = request.form.get('descricao', '').strip()
        evento.local = request.form.get('local', '').strip()

        try:
            data_hora_naive = datetime.strptime(data_hora_str, '%Y-%m-%dT%H:%M')
            
            data_hora_compensada = data_hora_naive + timedelta(hours=3)
            
            evento.data_hora = data_hora_compensada

            db.session.commit()
            flash(f'Evento "{evento.titulo}" atualizado com sucesso!', 'success')
            return redirect(url_for('calendario'))
        except ValueError:
            flash('Formato de Data/Hora inválido. Use AAAA-MM-DDTHH:MM.', 'danger')
            evento.data_hora_local_str = data_hora_str
            return render_template('editar_evento.html', evento=evento,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao atualizar evento: {e}")
            flash(f"Erro ao atualizar evento: {e}", 'danger')
            evento.data_hora_local_str = data_hora_str
            return render_template('editar_evento.html', evento=evento,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

    evento.data_hora_local_str = convert_utc_to_local(evento.data_hora).strftime('%Y-%m-%dT%H:%M')
    return render_template('editar_evento.html', evento=evento,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))

@app.route('/deletar_evento/<int:id>', methods=['DELETE'])
@login_required
def deletar_evento(id):
    evento = db.session.get(Evento, id)
    if evento is None:
        return jsonify({'status': 'error', 'message': 'Evento não encontrado.'}), 404

    try:
        db.session.delete(evento)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Evento excluído com sucesso!'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao deletar evento {id}: {e}")
        return jsonify({'status': 'error', 'message': 'Erro interno ao excluir evento.'}), 500

# --- ROTAS DE FORNECEDORES ---
@app.route('/fornecedores')
@login_required
def fornecedores():
    filtro = request.args.get('filtro', '').strip().lower()
    sort_by = request.args.get('sort_by', 'nome')
    sort_order = request.args.get('sort_order', 'asc')

    query = Fornecedor.query

    if filtro:
        query = query.filter(or_(
            Fornecedor.nome.ilike(f'%{filtro}%'),
            Fornecedor.contato.ilike(f'%{filtro}%'),
            Fornecedor.email.ilike(f'%{filtro}%')
        ))

    if sort_by == 'nome':
        query = query.order_by(Fornecedor.nome.asc() if sort_order == 'asc' else Fornecedor.nome.desc())
    elif sort_by == 'tipo_fornecedor':
        query = query.order_by(Fornecedor.tipo_fornecedor.asc() if sort_order == 'asc' else Fornecedor.tipo_fornecedor.desc())
    else:
        query = query.order_by(Fornecedor.nome.asc())

    fornecedores = query.all()
    return render_template('fornecedores.html', fornecedores=fornecedores,
                           usuario=session.get('usuario'), matricula=session.get('matricula'),
                           filtro=filtro, current_sort_by=sort_by, current_sort_order=sort_order)

@app.route('/limpar_filtro_fornecedor')
@login_required
def limpar_filtro_fornecedor():
    return redirect(url_for('fornecedores'))

# Rota para exibir detalhes de um fornecedor
@app.route('/fornecedores/<int:fornecedor_id>')
@login_required
def detalhe_fornecedor(fornecedor_id):
    fornecedor = db.session.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores'))

    # Itens associados a este fornecedor
    itens_fornecidos = FornecedorItem.query.filter_by(fornecedor_id=fornecedor_id).order_by(FornecedorItem.data_compra_aluguel.desc()).all()

    # Calcular o custo mensal estimado para cada item alugado
    for item in itens_fornecidos:
        item.custo_mensal_estimado = None
        if item.tipo == 'aluguel' and item.valor_diaria:
            # Estimativa simples: valor_diaria * 30 dias (pode ser mais complexa se houver dias úteis, etc.)
            item.custo_mensal_estimado = item.valor_diaria * 30

    return render_template('detalhe_fornecedor.html',
                           fornecedor=fornecedor,
                           itens_fornecidos=itens_fornecidos,
                           usuario=session.get('usuario'),
                           matricula=session.get('matricula'))

# Rota para adicionar um novo fornecedor
@app.route('/adicionar_fornecedor', methods=['GET', 'POST'])
@login_required
def adicionar_fornecedor():
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        contato = request.form.get('contato', '').strip()
        telefone = request.form.get('telefone', '').strip()
        email = request.form.get('email', '').strip()
        observacoes = request.form.get('observacoes', '').strip()
        tipo_fornecedor = request.form.get('tipo_fornecedor', 'compra_produtos').strip()

        if not nome:
            flash('O nome do fornecedor é obrigatório.', 'danger')
            return render_template('adicionar_fornecedor.html',
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        fornecedor_existente = Fornecedor.query.filter(func.lower(Fornecedor.nome) == func.lower(nome)).first()
        if fornecedor_existente:
            flash(f'Já existe um fornecedor com o nome "{nome}".', 'danger')
            return render_template('adicionar_fornecedor.html',
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        novo_fornecedor = Fornecedor(
            nome=nome, contato=contato, telefone=telefone, email=email,
            observacoes=observacoes, tipo_fornecedor=tipo_fornecedor
        )
        db.session.add(novo_fornecedor)
        db.session.commit()
        flash(f'Fornecedor "{nome}" adicionado com sucesso!', 'success')
        return redirect(url_for('fornecedores'))
    return render_template('adicionar_fornecedor.html',
                           usuario=session.get('usuario'), matricula=session.get('matricula'))

# Rota para editar um fornecedor existente
@app.route('/editar_fornecedor/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_fornecedor(id):
    fornecedor = db.session.get(Fornecedor, id)
    if fornecedor is None:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores'))

    if request.method == 'POST':
        fornecedor.nome = request.form['nome'].strip()
        fornecedor.contato = request.form.get('contato', '').strip()
        fornecedor.telefone = request.form.get('telefone', '').strip()
        fornecedor.email = request.form.get('email', '').strip()
        fornecedor.observacoes = request.form.get('observacoes', '').strip()
        fornecedor.tipo_fornecedor = request.form.get('tipo_fornecedor', 'compra_produtos').strip()

        if not fornecedor.nome:
            flash('O nome do fornecedor é obrigatório.', 'danger')
            return render_template('editar_fornecedor.html', fornecedor=fornecedor,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        try:
            db.session.commit()
            flash(f'Fornecedor "{fornecedor.nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('fornecedores'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar fornecedor: {e}', 'danger')
            return render_template('editar_fornecedor.html', fornecedor=fornecedor,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

    return render_template('editar_fornecedor.html', fornecedor=fornecedor,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))


@app.route('/adicionar_item_fornecedor/<int:fornecedor_id>', methods=['GET', 'POST'])
@login_required
def adicionar_item_fornecedor(fornecedor_id):
    fornecedor = db.session.get(Fornecedor, fornecedor_id)
    if fornecedor is None:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores'))

    if request.method == 'POST':
        nome_produto_servico = request.form['nome_produto_servico'].strip()
        tipo = request.form['tipo'].strip()
        valor_unidade = float(request.form['valor_unidade'])
        quantidade_comprada = request.form.get('quantidade_comprada', type=int)
        data_compra_aluguel_str = request.form.get('data_compra_aluguel', '').strip()
        setor = request.form['setor'].strip()

        valor_diaria = request.form.get('valor_diaria', type=float)
        data_inicio_aluguel_str = request.form.get('data_inicio_aluguel', '').strip()
        data_fim_aluguel_str = request.form.get('data_fim_aluguel', '').strip()

        if not nome_produto_servico or valor_unidade < 0:
            flash('Preencha os campos obrigatórios corretamente.', 'danger')
            return render_template('adicionar_item_fornecedor.html', fornecedor=fornecedor, setores=SETORES,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        try:
            data_compra_aluguel = datetime.strptime(data_compra_aluguel_str, '%Y-%m-%d').date() if data_compra_aluguel_str else None
            data_inicio_aluguel = datetime.strptime(data_inicio_aluguel_str, '%Y-%m-%d').date() if data_inicio_aluguel_str else None
            data_fim_aluguel = datetime.strptime(data_fim_aluguel_str, '%Y-%m-%d').date() if data_fim_aluguel_str else None
        except ValueError:
            flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
            return render_template('adicionar_item_fornecedor.html', fornecedor=fornecedor, setores=SETORES,
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        novo_item = FornecedorItem(
            fornecedor_id=fornecedor.id,
            nome_produto_servico=nome_produto_servico,
            tipo=tipo,
            valor_unidade=valor_unidade,
            quantidade_comprada=quantidade_comprada,
            data_compra_aluguel=data_compra_aluguel,
            setor=setor,
            valor_diaria=valor_diaria,
            data_inicio_aluguel=data_inicio_aluguel,
            data_fim_aluguel=data_fim_aluguel
        )
        db.session.add(novo_item)
        db.session.commit()
        flash(f'Item "{nome_produto_servico}" adicionado ao fornecedor "{fornecedor.nome}" com sucesso!', 'success')
        return redirect(url_for('detalhe_fornecedor', fornecedor_id=fornecedor.id))

    return render_template('adicionar_item_fornecedor.html', fornecedor=fornecedor, setores=SETORES,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))





@app.route('/editar_item_fornecedor/<int:item_id>', methods=['GET', 'POST'])
@login_required
def editar_item_fornecedor(item_id):
    item = db.session.get(FornecedorItem, item_id)
    if item is None:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('fornecedores'))

    fornecedor = item.fornecedor

    if request.method == 'POST':
        # Corrigir o erro de NameError: name 'nome_produto_servico' is not defined
        nome_produto_servico_form = request.form['nome_produto_servico'].strip()
        valor_unidade_form = float(request.form['valor_unidade'])

        item.nome_produto_servico = nome_produto_servico_form
        item.tipo = request.form['tipo'].strip()
        item.valor_unidade = valor_unidade_form
        item.setor = request.form['setor'].strip()

        item.quantidade_comprada = request.form.get('quantidade_comprada', type=int)
        data_compra_aluguel_str = request.form.get('data_compra_aluguel', '').strip()

        item.valor_diaria = request.form.get('valor_diaria', type=float)
        data_inicio_aluguel_str = request.form.get('data_inicio_aluguel', '').strip()
        data_fim_aluguel_str = request.form.get('data_fim_aluguel', '').strip()

        if not nome_produto_servico_form or valor_unidade_form < 0: # Use as variáveis do formulário
            flash('Preencha os campos obrigatórios corretamente.', 'danger')
            return render_template('editar_item_fornecedor.html', item=item, fornecedor=fornecedor, setores=SETORES, # Nome do template ajustado
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        try: # Bloco try-except para as datas
            if data_compra_aluguel_str:
                item.data_compra_aluguel = datetime.strptime(data_compra_aluguel_str, '%Y-%m-%d').date()
            else:
                item.data_compra_aluguel = None # Define como None se vazio

            if data_inicio_aluguel_str:
                item.data_inicio_aluguel = datetime.strptime(data_inicio_aluguel_str, '%Y-%m-%d').date()
            else:
                item.data_inicio_aluguel = None # Define como None se vazio

            if data_fim_aluguel_str:
                item.data_fim_aluguel = datetime.strptime(data_fim_aluguel_str, '%Y-%m-%d').date()
            else:
                item.data_fim_aluguel = None # Define como None se vazio

        except ValueError:
            flash('Formato de data inválido. Use AAAA-MM-DD.', 'danger')
            return render_template('editar_item_fornecedor.html', item=item, fornecedor=fornecedor, setores=SETORES, # Nome do template ajustado
                                   usuario=session.get('usuario'), matricula=session.get('matricula'))

        db.session.commit()
        flash(f'Item "{item.nome_produto_servico}" do fornecedor "{fornecedor.nome}" atualizado com sucesso!', 'success')
        return redirect(url_for('detalhe_fornecedor', fornecedor_id=fornecedor.id))
    
    return render_template('editar_item_fornecedor.html', item=item, fornecedor=fornecedor, setores=SETORES,
                           usuario=session.get('usuario'), matricula=session.get('matricula'))


@app.route('/excluir_fornecedor/<int:id>')
@login_required
def excluir_fornecedor(id):
    fornecedor = db.session.get(Fornecedor, id)
    if fornecedor is None:
        flash('Fornecedor não encontrado.', 'danger')
        return redirect(url_for('fornecedores'))

    # Excluir itens associados ao fornecedor antes de excluir o fornecedor
    FornecedorItem.query.filter_by(fornecedor_id=id).delete()
    Produto.query.filter_by(fornecedor_id=id).update({'fornecedor_id': None}) # Opcional: desvincula produtos do fornecedor

    db.session.delete(fornecedor)
    db.session.commit()
    flash(f'Fornecedor "{fornecedor.nome}" e seus itens/produtos associados excluídos/desvinculados com sucesso.', 'success')
    return redirect(url_for('fornecedores'))

@app.route('/excluir_item_fornecedor/<int:item_id>')
@login_required
def excluir_item_fornecedor(item_id):
    item = db.session.get(FornecedorItem, item_id)
    if item is None:
        flash('Item não encontrado.', 'danger')
        return redirect(url_for('fornecedores'))

    fornecedor_id = item.fornecedor_id

    db.session.delete(item)
    db.session.commit()
    flash(f'Item "{item.nome_produto_servico}" excluído com sucesso.', 'success')
    return redirect(url_for('detalhe_fornecedor', fornecedor_id=fornecedor_id))


# --- API Routes for Charts ---
@app.route('/api/consumo/fornecedores/<int:fornecedor_id>')
@login_required
def api_consumo_fornecedores(fornecedor_id):
    period = request.args.get('period', 'monthly')
    
    if period not in ['monthly', 'quarterly', 'yearly', '5years']:
        return jsonify({'error': 'Período inválido.'}), 400

    labels = []
    data_bought = []
    data_rented_cost = []

    now = datetime.utcnow().date()
    
    items_in_scope = FornecedorItem.query.filter_by(fornecedor_id=fornecedor_id).all()

    if period == 'monthly':
        for i in range(5, -1, -1):
            month_start = (now - relativedelta(months=i)).replace(day=1)
            next_month_start = (month_start + relativedelta(months=1)).replace(day=1)
            month_end = next_month_start - timedelta(days=1)
            
            labels.append(month_start.strftime('%b/%Y'))
            
            current_bought_sum = 0
            current_rented_sum = 0

            for item in items_in_scope:
                if item.tipo == 'produto' and item.data_compra_aluguel and month_start <= item.data_compra_aluguel <= month_end:
                    current_bought_sum += item.quantidade_comprada if item.quantidade_comprada else 0
                
                if item.tipo == 'aluguel' and item.data_inicio_aluguel and item.valor_diaria:
                    rental_start = item.data_inicio_aluguel
                    rental_end = item.data_fim_aluguel or date.max

                    overlap_start = max(rental_start, month_start)
                    overlap_end = min(rental_end, month_end)

                    if overlap_start <= overlap_end:
                        days_active_in_month = (overlap_end - overlap_start).days + 1
                        current_rented_sum += item.valor_diaria * days_active_in_month
            
            data_bought.append(current_bought_sum)
            data_rented_cost.append(current_rented_sum)

    elif period == 'quarterly':
        for i in range(3, -1, -1):
            current_quarter_num = (now.month - 1) // 3 + 1
            current_quarter_year = now.year

            target_year = current_quarter_year
            target_quarter_num = current_quarter_num - i
            
            while target_quarter_num <= 0:
                target_quarter_num += 4
                target_year -= 1

            quarter_start_month = (target_quarter_num - 1) * 3 + 1
            quarter_start = date(target_year, quarter_start_month, 1)
            quarter_end = (quarter_start + relativedelta(months=3)) - timedelta(days=1)
            
            labels.append(f'Q{target_quarter_num}/{target_year}')
            
            current_bought_sum = 0
            current_rented_sum = 0

            for item in items_in_scope:
                if item.tipo == 'produto' and item.data_compra_aluguel and quarter_start <= item.data_compra_aluguel <= quarter_end:
                    current_bought_sum += item.quantidade_comprada if item.quantidade_comprada else 0
                
                if item.tipo == 'aluguel' and item.valor_diaria and item.data_inicio_aluguel:
                    rental_start = item.data_inicio_aluguel
                    rental_end = item.data_fim_aluguel or date.max

                    overlap_start = max(rental_start, quarter_start)
                    overlap_end = min(rental_end, quarter_end)

                    if overlap_start <= overlap_end:
                        days_active_in_quarter = (overlap_end - overlap_start).days + 1
                        current_rented_sum += item.valor_diaria * days_active_in_quarter
            
            data_bought.append(current_bought_sum)
            data_rented_cost.append(current_rented_sum)

    elif period == 'yearly':
        for i in range(4, -1, -1):
            year_start = date(now.year - i, 1, 1)
            year_end = date(now.year - i, 12, 31)
            
            labels.append(str(now.year - i))
            
            current_bought_sum = 0
            current_rented_sum = 0

            for item in items_in_scope:
                if item.tipo == 'produto' and item.data_compra_aluguel and year_start <= item.data_compra_aluguel <= year_end:
                    current_bought_sum += item.quantidade_comprada if item.quantidade_comprada else 0
                
                if item.tipo == 'aluguel' and item.valor_diaria and item.data_inicio_aluguel:
                    rental_start = item.data_inicio_aluguel
                    rental_end = item.data_fim_aluguel or date.max

                    overlap_start = max(rental_start, year_start)
                    overlap_end = min(rental_end, year_end)

                    if overlap_start <= overlap_end:
                        days_active_in_year = (overlap_end - overlap_start).days + 1
                        current_rented_sum += item.valor_diaria * days_active_in_year
            
            data_bought.append(current_bought_sum)
            data_rented_cost.append(current_rented_sum)
    
    elif period == '5years':
        labels = ['Últimos 5 Anos']
        total_bought = 0
        total_rented_cost = 0

        five_years_ago_date = now - relativedelta(years=5)
        
        for item in items_in_scope:
            item_date_for_filter = item.data_compra_aluguel or item.data_inicio_aluguel
            if not item_date_for_filter: continue
            
            if item_date_for_filter >= five_years_ago_date:
                if item.tipo == 'produto':
                    total_bought += item.quantidade_comprada if item.quantidade_comprada else 0
                
                if item.tipo == 'aluguel' and item.data_inicio_aluguel and item.valor_diaria:
                    rental_start = item.data_inicio_aluguel
                    rental_end = item.data_fim_aluguel or date.max

                    overlap_start = max(rental_start, five_years_ago_date)
                    overlap_end = min(rental_end, now)
                    
                    if overlap_start <= overlap_end:
                        days_active = (overlap_end - overlap_start).days + 1
                        total_rented_cost += item.valor_diaria * days_active
        
        data_bought = [total_bought]
        data_rented_cost = [total_rented_cost]

    return jsonify({
        'labels': labels,
        'data_bought': data_bought,
        'data_rented_cost': data_rented_cost
    })


# --- Funcionalidade de Carga de CSV (Pandas) ---
def carregar_produtos_do_csv(caminho_arquivo='dados/produtos_iniciais.csv'):
    print(f"Tentando carregar dados de produtos do arquivo: {caminho_arquivo}")
    try:
        dados_csv = pd.read_csv(caminho_arquivo, encoding="utf-8", sep=';')
        print(f"Arquivo '{caminho_arquivo}' lido com sucesso. {len(dados_csv)} linhas encontradas.")

        with app.app_context():
            for index, row in dados_csv.iterrows():
                try:
                    nome = row['Nome do Produto'].strip()
                    quantidade = int(row['Quantidade'])
                    preco = float(row['Preco'])
                    estoque_minimo = int(row.get('Estoque Minimo', 5))
                    fornecedor_nome = row.get('Fornecedor', '').strip()
                    ca_numero = row.get('CA Numero', '').strip()

                    fornecedor_id = None
                    if fornecedor_nome:
                        fornecedor = Fornecedor.query.filter(func.lower(Fornecedor.nome) == func.lower(fornecedor_nome)).first()
                        if not fornecedor:
                            fornecedor = Fornecedor(nome=fornecedor_nome, tipo_fornecedor='compra_produtos')
                            db.session.add(fornecedor)
                            db.session.flush()
                            print(f"Fornecedor '{fornecedor_nome}' criado.")
                        fornecedor_id = fornecedor.id

                    produto_existente = Produto.query.filter(func.lower(Produto.nome) == func.lower(nome)).first()

                    if produto_existente:
                        quantidade_anterior = produto_existente.quantidade
                        produto_existente.quantidade += quantidade
                        produto_existente.preco = preco
                        produto_existente.estoque_minimo = estoque_minimo
                        produto_existente.fornecedor_id = fornecedor_id
                        produto_existente.ca_numero = ca_numero
                        db.session.add(produto_existente)

                        movimentacao = MovimentacaoEstoque(
                            produto_id=produto_existente.id,
                            tipo_movimentacao='entrada',
                            quantidade=quantidade,
                            observacao=f"Entrada via CSV. Qtd. anterior: {quantidade_anterior}"
                        )
                        db.session.add(movimentacao)
                        print(f"Produto '{nome}' atualizado e entrada registrada via CSV.")
                    else:
                        novo_produto = Produto(
                            nome=nome, quantidade=quantidade, preco=preco, # Changed 'quantity' to 'quantidade'
                            estoque_minimo=estoque_minimo, fornecedor_id=fornecedor_id, ca_numero=ca_numero
                        )
                        db.session.add(novo_produto)
                        db.session.flush()

                        movimentacao = MovimentacaoEstoque(
                            produto_id=novo_produto.id,
                            tipo_movimentacao='entrada',
                            quantidade=quantidade, # Changed 'quantity' to 'quantidade'
                            observacao="Primeira entrada via CSV"
                        )
                        db.session.add(movimentacao)
                        print(f"Novo produto '{nome}' adicionado via CSV.")

                except KeyError as ke:
                    print(f"Erro: Coluna '{ke}' não encontrada na linha {index} do CSV. Verifique os nomes das colunas.")
                    db.session.rollback()
                    continue
                except ValueError as ve:
                    print(f"Erro de valor: {ve} na linha {index} do CSV para o produto '{nome}'.")
                    db.session.rollback()
                    continue
                except Exception as e:
                    print(f"Erro inesperado processando linha {index} para produto '{nome}': {e}")
                    db.session.rollback()
                    continue

            db.session.commit()
            print("Carga de dados de produtos do CSV concluída com sucesso!")

    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado. Certifique-se de que ele existe na pasta 'dados/' ou ajuste o caminho.")
    except pd.errors.EmptyDataError:
        print(f"Erro: O arquivo '{caminho_arquivo}' está vazio.")
    except pd.errors.ParserError as pe:
        print(f"Erro de parsing no CSV: {pe}. Verifique o separador (';') e a codificação ('utf-8').")
    except Exception as e:
        print(f"Ocorreu um erro geral durante a carga de dados do CSV: {e}")
        db.session.rollback()

# --- Bloco de inicialização principal ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        