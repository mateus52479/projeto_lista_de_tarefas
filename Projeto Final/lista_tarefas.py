
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
import mysql.connector
from mysql.connector import pooling

# --------------------------------- Configuração ---------------------------------

ctk.set_appearance_mode("dark")

ctk.set_default_color_theme("blue")


COLOR_PRIMARY = "#6A48A6"  # Roxo Principal
COLOR_SECONDARY = "#4A3876" # Roxo Secundário
COLOR_BACKGROUND = "#1E1E25" # Fundo Escuro
COLOR_FORM_BG = "#2E2E36"    # Fundo de Formulário


DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "tarefas_db"
}

# --------------------------------- Banco de Dados ---------------------------------


try:
    db_pool = pooling.MySQLConnectionPool(
        pool_name="task_manager_pool",
        pool_size=5, # Número de conexões no pool
        **DB_CONFIG
    )
except mysql.connector.Error as err:
 
    db_pool = None


def get_db_connection():
  
    if db_pool:
        try:
            return db_pool.get_connection()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Conexão", f"Falha ao obter conexão do pool:\n{err}")
            return None
    else:
      
        try:
        
            config_no_db = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
            return mysql.connector.connect(**config_no_db)
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Conexão", f"Erro ao conectar ao banco:\n{err}")
            return None


def inicializar_banco():
 
    conexao = None
    try:
     
        config_no_db = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
        conexao = mysql.connector.connect(**config_no_db)
        cursor = conexao.cursor()

      
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
        cursor.execute(f"USE {DB_CONFIG['database']}")


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario VARCHAR(100) UNIQUE NOT NULL,
            senha VARCHAR(100) NOT NULL
        )
        """)

     
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarefas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario_id INT NOT NULL,
            titulo VARCHAR(255),
            data VARCHAR(20),
            descricao TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE
        )
        """)

     
        cursor.execute("SELECT * FROM usuarios WHERE usuario = 'admin'")
        if not cursor.fetchone():
      
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", ('admin', '1234'))
            conexao.commit()

    except mysql.connector.Error as err:
        messagebox.showerror("Erro de Inicialização", f"Falha ao inicializar o banco de dados:\n{err}")
    finally:
        if conexao and conexao.is_connected():
            cursor.close()
            conexao.close()


# --------------------------------- Classes da Interface ---------------------------------

class App(ctk.CTk):
  
    def __init__(self):
        super().__init__()
        self.title("Gerenciador de Tarefas")
        self.geometry("950x650")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BACKGROUND)

        inicializar_banco()
        self.usuario_id = None
        self.usuario_nome = None

      
        self.frame_login = LoginFrame(self, self.abrir_tela_principal)
        self.frame_login.pack(fill="both", expand=True)

    def abrir_tela_principal(self, usuario_id, usuario_nome):
      
        self.usuario_id = usuario_id
        self.usuario_nome = usuario_nome
        self.frame_login.pack_forget()

        if usuario_nome == "admin":
            self.frame_admin = AdminFrame(self)
            self.frame_admin.pack(fill="both", expand=True)
        else:
            self.frame_tarefas = ListaDeTarefas(self, usuario_id)
            self.frame_tarefas.pack(fill="both", expand=True)

    def voltar_login(self):

        if hasattr(self, "frame_tarefas") and self.frame_tarefas.winfo_exists():
            self.frame_tarefas.pack_forget()
        if hasattr(self, "frame_admin") and self.frame_admin.winfo_exists():
            self.frame_admin.pack_forget()

      
        self.frame_login = LoginFrame(self, self.abrir_tela_principal)
        self.frame_login.pack(fill="both", expand=True)


class LoginFrame(ctk.CTkFrame):

    def __init__(self, master, callback_login_sucesso):
     
        super().__init__(master, fg_color=COLOR_FORM_BG, corner_radius=15)
        self.callback_login_sucesso = callback_login_sucesso
        self._setup_ui()

    def _setup_ui(self):
    
        self.label_titulo = ctk.CTkLabel(self, text="LOGIN", font=("Arial Black", 30), text_color="white")
        self.label_titulo.pack(pady=(100, 40))

        self.label_usuario = ctk.CTkLabel(self, text="Usuário", font=("Arial", 14))
        self.label_usuario.pack()
       
        self.entry_usuario = ctk.CTkEntry(self, width=250, corner_radius=8, border_width=1)
        self.entry_usuario.pack(pady=5)

        self.label_senha = ctk.CTkLabel(self, text="Senha", font=("Arial", 14))
        self.label_senha.pack()
    
        self.entry_senha = ctk.CTkEntry(self, width=250, show="*", corner_radius=8, border_width=1)
        self.entry_senha.pack(pady=10)

      
        self.botao_login = ctk.CTkButton(self, text="Entrar", fg_color=COLOR_PRIMARY, width=120, corner_radius=8, command=self.validar_login)
        self.botao_login.pack(pady=10)

        self.botao_cadastro = ctk.CTkButton(self, text="Criar conta", width=120, fg_color=COLOR_PRIMARY,
                                            hover_color="#479cd3", corner_radius=8, command=self.criar_conta)
        self.botao_cadastro.pack(pady=5)

    def validar_login(self):
      
        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return

        conexao = get_db_connection()
        if not conexao:
            return

        try:
     
            cursor = conexao.cursor(dictionary=True)
         
            cursor.execute("SELECT id, senha FROM usuarios WHERE usuario = %s", (usuario,))
            user = cursor.fetchone()


            if user and user["senha"] == senha:
                messagebox.showinfo("Sucesso", "Login bem-sucedido!")
                self.callback_login_sucesso(user["id"], usuario)
            else:
                messagebox.showerror("Erro", "Usuário ou senha incorretos!")

        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro durante o login:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

    def criar_conta(self):

        usuario = self.entry_usuario.get().strip()
        senha = self.entry_senha.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha usuário e senha para criar conta!")
            return

        conexao = get_db_connection()
        if not conexao:
            return

        try:
            cursor = conexao.cursor()
   
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", (usuario, senha))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Conta criada com sucesso! Faça login.")
        except mysql.connector.IntegrityError:

            messagebox.showerror("Erro", "Usuário já existe!")
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao criar conta:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()


class ListaDeTarefas(ctk.CTkFrame):
 
    def __init__(self, master, usuario_id):
      
        super().__init__(master, fg_color=COLOR_BACKGROUND)
        self.usuario_id = usuario_id
        self.tarefas = []
        self.indice_editando = None
        self._setup_ui()
        self.carregar_tarefas()

    def _setup_ui(self):
     
        self.titulo_label = ctk.CTkLabel(self, text="LISTA DE TAREFAS", font=("Arial Black", 30), text_color="white")
        self.titulo_label.pack(pady=(15, 10))

        self.botao_logout = ctk.CTkButton(self, text="Logout", width=100, fg_color="#a63a3a",
                                          hover_color="#c44", corner_radius=8, command=self.logout)
        self.botao_logout.place(relx=0.88, rely=0.05)

        # Frame esquerdo (formulário)
        self.frame_esquerda = ctk.CTkFrame(self, fg_color=COLOR_FORM_BG, corner_radius=15)
        self.frame_esquerda.place(relx=0.03, rely=0.18, relwidth=0.45, relheight=0.75)
        self._setup_form_ui()

        # Frame direito (lista de tarefas)
        self.frame_direita = ctk.CTkFrame(self, fg_color=COLOR_BACKGROUND, corner_radius=15)
        self.frame_direita.place(relx=0.5, rely=0.16, relwidth=0.47, relheight=0.86)
        self._setup_list_ui()

    def _setup_form_ui(self):
        self.label_titulo = ctk.CTkLabel(self.frame_esquerda, text="Título", font=("Arial", 14))
        self.label_titulo.pack(pady=(15, 0))
        # Entry com corner_radius
        self.entry_titulo = ctk.CTkEntry(self.frame_esquerda, width=250, corner_radius=8)
        self.entry_titulo.pack(pady=5)

        self.label_data = ctk.CTkLabel(self.frame_esquerda, text="Data (dd/mm/aaaa)", font=("Arial", 14))
        self.label_data.pack()
        # Entry com corner_radius
        self.entry_data = ctk.CTkEntry(self.frame_esquerda, width=250, corner_radius=8)
        self.entry_data.pack(pady=5)

        self.label_desc = ctk.CTkLabel(self.frame_esquerda, text="Descrição", font=("Arial", 14))
        self.label_desc.pack()
        # Textbox com corner_radius
        self.text_desc = ctk.CTkTextbox(self.frame_esquerda, width=250, height=120, corner_radius=8)
        self.text_desc.pack(pady=10)

        # Botões com corner_radius
        self.botao_adicionar = ctk.CTkButton(self.frame_esquerda, text="Adicionar", width=100, fg_color=COLOR_PRIMARY, corner_radius=8, command=self.adicionar_ou_editar_tarefa)
        self.botao_adicionar.pack(pady=10)

        self.botao_cancelar = ctk.CTkButton(self.frame_esquerda, text="Cancelar Edição", width=100, fg_color="gray", corner_radius=8,
                                            command=self.cancelar_edicao)
    

    def _setup_list_ui(self):
        self.titulo_tarefas = ctk.CTkLabel(self.frame_direita, text="MINHAS TAREFAS", font=("Arial Black", 20), text_color="white")
        self.titulo_tarefas.pack(pady=10)

        # Barra de busca e filtros
        filtro_frame = ctk.CTkFrame(self.frame_direita, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=10)

        # Entries com corner_radius
        self.entry_search = ctk.CTkEntry(filtro_frame, placeholder_text="Buscar por título ou descrição...", width=220, corner_radius=8)
        self.entry_search.pack(side="left", padx=(0, 5))
        self.entry_search.bind('<Return>', lambda e: self.aplicar_filtros())

        self.entry_filter_data = ctk.CTkEntry(filtro_frame, placeholder_text="dd/mm/aaaa ou vazio", width=140, corner_radius=8)
        self.entry_filter_data.pack(side="left", padx=5)

        # Botões com corner_radius
        self.btn_filtrar = ctk.CTkButton(filtro_frame, text="Filtrar", width=80, fg_color=COLOR_PRIMARY, corner_radius=8, command=self.aplicar_filtros)
        self.btn_filtrar.pack(side="left", padx=5)

        self.btn_limpar = ctk.CTkButton(filtro_frame, text="Limpar", width=80, fg_color="gray", corner_radius=8, command=self.limpar_filtros)
        self.btn_limpar.pack(side="left", padx=5)

        self.scroll_frame_tarefas = ctk.CTkScrollableFrame(self.frame_direita, fg_color=COLOR_BACKGROUND, corner_radius=15)
        self.scroll_frame_tarefas.pack(padx=10, pady=10, fill="both", expand=True)

    def validar_data(self, data_str):

        if not data_str:
            return True
        try:
            datetime.strptime(data_str, "%d/%m/%Y")
            return True
        except ValueError:
            return False

    def carregar_tarefas(self, termo="", data_filtro=""):
        conexao = get_db_connection()
        if not conexao:
            return

        query = "SELECT * FROM tarefas WHERE usuario_id = %s"
        params = [self.usuario_id]

        if termo:
            query += " AND (titulo LIKE %s OR descricao LIKE %s)"
            like_termo = f"%{termo}%"
            params.extend([like_termo, like_termo])

        if data_filtro:
            if not self.validar_data(data_filtro):
                messagebox.showerror("Erro", "Data inválida no filtro. Use dd/mm/aaaa")
                return
            query += " AND data = %s"
            params.append(data_filtro)

        query += " ORDER BY id DESC"

        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(query, tuple(params))
            self.tarefas = cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao carregar tarefas:\n{err}")
            self.tarefas = []
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

        self.mostrar_tarefas()

    def aplicar_filtros(self):
        termo = self.entry_search.get().strip()
        data = self.entry_filter_data.get().strip()
        self.carregar_tarefas(termo, data)

    def limpar_filtros(self):
        self.entry_search.delete(0, "end")
        self.entry_filter_data.delete(0, "end")
        self.carregar_tarefas()

    def mostrar_tarefas(self):
        for widget in self.scroll_frame_tarefas.winfo_children():
            widget.destroy()

        if not self.tarefas:
            ctk.CTkLabel(self.scroll_frame_tarefas, text="Nenhuma tarefa encontrada.", text_color="gray").pack(pady=20)
            return

        for tarefa in self.tarefas:
            self._criar_card_tarefa(tarefa)

    def _criar_card_tarefa(self, tarefa):
        card = ctk.CTkFrame(self.scroll_frame_tarefas, fg_color=COLOR_SECONDARY, corner_radius=12)
        card.pack(fill="x", pady=8, padx=10)

        # Frame para o conteúdo e botões
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=5)

        # Título e Data
        lbl_titulo = ctk.CTkLabel(content_frame, text=f"Título: {tarefa['titulo']}", font=("Arial Bold", 14))
        lbl_titulo.pack(anchor="w")

        lbl_data = ctk.CTkLabel(content_frame, text=f"Data: {tarefa['data']}", font=("Arial", 12))
        lbl_data.pack(anchor="w")

        # Descrição
        lbl_desc = ctk.CTkLabel(content_frame, text=f"Descrição: {tarefa['descricao']}", wraplength=350, justify="left")
        lbl_desc.pack(anchor="w", pady=(5, 10))

        # Botões de Ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 5))

        btn_editar = ctk.CTkButton(btn_frame, text="Editar", width=80, fg_color="#3a7ca6", corner_radius=8,
                                   command=lambda t=tarefa: self.preparar_edicao(t))
        btn_editar.pack(side="right", padx=5)

        btn_excluir = ctk.CTkButton(btn_frame, text="Excluir", width=80, fg_color="#a63a3a", corner_radius=8,
                                    command=lambda tid=tarefa['id']: self.excluir_tarefa(tid))
        btn_excluir.pack(side="right", padx=5)

    def preparar_edicao(self, tarefa):
        self.indice_editando = tarefa['id']
        self.entry_titulo.delete(0, "end")
        self.entry_titulo.insert(0, tarefa['titulo'])
        self.entry_data.delete(0, "end")
        self.entry_data.insert(0, tarefa['data'])
        self.text_desc.delete("1.0", "end")
        self.text_desc.insert("1.0", tarefa['descricao'])

        self.botao_adicionar.configure(text="Salvar Edição", fg_color="#3a7ca6")
        self.botao_cancelar.pack(pady=5) 

    def cancelar_edicao(self):
        self.indice_editando = None
        self.entry_titulo.delete(0, "end")
        self.entry_data.delete(0, "end")
        self.text_desc.delete("1.0", "end")

        self.botao_adicionar.configure(text="Adicionar", fg_color=COLOR_PRIMARY)
        self.botao_cancelar.pack_forget() 

    def adicionar_ou_editar_tarefa(self):
        titulo = self.entry_titulo.get().strip()
        data = self.entry_data.get().strip()
        descricao = self.text_desc.get("1.0", "end").strip()

        if not titulo or not descricao:
            messagebox.showwarning("Aviso", "Título e Descrição são obrigatórios!")
            return

        if data and not self.validar_data(data):
            messagebox.showerror("Erro", "Data inválida. Use dd/mm/aaaa")
            return

        conexao = get_db_connection()
        if not conexao:
            return

        try:
            cursor = conexao.cursor()
            if self.indice_editando is None:
                query = "INSERT INTO tarefas (usuario_id, titulo, data, descricao) VALUES (%s, %s, %s, %s)"
                params = (self.usuario_id, titulo, data, descricao)
                cursor.execute(query, params)
                messagebox.showinfo("Sucesso", "Tarefa adicionada!")
            else:
                query = "UPDATE tarefas SET titulo=%s, data=%s, descricao=%s WHERE id=%s AND usuario_id=%s"
                params = (titulo, data, descricao, self.indice_editando, self.usuario_id)
                cursor.execute(query, params)
                messagebox.showinfo("Sucesso", "Tarefa atualizada!")
                self.cancelar_edicao()

            conexao.commit()
            self.carregar_tarefas()
            if self.indice_editando is None:
                self.entry_titulo.delete(0, "end")
                self.entry_data.delete(0, "end")
                self.text_desc.delete("1.0", "end")

        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao salvar tarefa:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

    def excluir_tarefa(self, tarefa_id):
        if not messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir esta tarefa?"):
            return

        conexao = get_db_connection()
        if not conexao:
            return

        try:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM tarefas WHERE id=%s AND usuario_id=%s", (tarefa_id, self.usuario_id))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Tarefa excluída com sucesso!")
            self.carregar_tarefas()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao excluir tarefa:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

    def logout(self):
        self.master.voltar_login()


class AdminFrame(ctk.CTkFrame):
    def __init__(self, master):
        # Fundo principal da tela de admin
        super().__init__(master, fg_color=COLOR_BACKGROUND)
        self._setup_ui()
        self.mostrar_usuarios()
        self.mostrar_todas_tarefas()

    def _setup_ui(self):
        self.titulo_label = ctk.CTkLabel(self, text="PAINEL DE ADMINISTRAÇÃO", font=("Arial Black", 30), text_color="white")
        self.titulo_label.pack(pady=(15, 10))

        # Botão de Logout
        self.botao_logout = ctk.CTkButton(self, text="Logout", width=100, fg_color="#a63a3a",
                                          hover_color="#c44", corner_radius=8, command=self.logout)
        self.botao_logout.place(relx=0.88, rely=0.05)

        # Tabview
        self.tabs = ctk.CTkTabview(self, width=900, height=500, corner_radius=15)
        self.tabs.pack(padx=20, pady=10, fill="both", expand=True)

        self.tab_usuarios = self.tabs.add("Gerenciar Usuários")
        self.tab_tarefas = self.tabs.add("Todas as Tarefas")

        self._setup_usuarios_tab()

        self._setup_tarefas_tab()

    def _setup_usuarios_tab(self):
        frame_criar = ctk.CTkFrame(self.tab_usuarios, fg_color=COLOR_FORM_BG, corner_radius=12)
        frame_criar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(frame_criar, text="Criar Novo Usuário", font=("Arial Bold", 16)).pack(pady=5)

        frame_entries = ctk.CTkFrame(frame_criar, fg_color="transparent")
        frame_entries.pack(pady=5)

        ctk.CTkLabel(frame_entries, text="Usuário:").pack(side="left", padx=5)
        self.entry_novo_usuario = ctk.CTkEntry(frame_entries, width=150, corner_radius=8)
        self.entry_novo_usuario.pack(side="left", padx=5)

        ctk.CTkLabel(frame_entries, text="Senha:").pack(side="left", padx=5)
        self.entry_nova_senha = ctk.CTkEntry(frame_entries, width=150, show="*", corner_radius=8)
        self.entry_nova_senha.pack(side="left", padx=5)

        ctk.CTkButton(frame_criar, text="Criar", fg_color=COLOR_PRIMARY, corner_radius=8, command=self.criar_usuario).pack(pady=10)

        ctk.CTkLabel(self.tab_usuarios, text="Lista de Usuários", font=("Arial Bold", 16)).pack(pady=(10, 5))
        self.scroll_frame_usuarios = ctk.CTkScrollableFrame(self.tab_usuarios, fg_color=COLOR_BACKGROUND, corner_radius=15)
        self.scroll_frame_usuarios.pack(fill="both", expand=True, padx=10, pady=10)

    def _setup_tarefas_tab(self):
        filtro_frame = ctk.CTkFrame(self.tab_tarefas, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=10, pady=10)

        self.entry_search_admin = ctk.CTkEntry(filtro_frame, placeholder_text="Buscar (título/descrição/usuário)", width=300, corner_radius=8)
        self.entry_search_admin.pack(side="left", padx=5)
        self.entry_search_admin.bind('<Return>', lambda e: self.mostrar_todas_tarefas())

        self.entry_filter_data_admin = ctk.CTkEntry(filtro_frame, placeholder_text="dd/mm/aaaa", width=140, corner_radius=8)
        self.entry_filter_data_admin.pack(side="left", padx=5)

        ctk.CTkButton(filtro_frame, text="Filtrar", fg_color=COLOR_PRIMARY, corner_radius=8, command=self.mostrar_todas_tarefas).pack(side="left", padx=5)
        ctk.CTkButton(filtro_frame, text="Limpar", fg_color="gray", corner_radius=8, command=self.limpar_filtros_admin).pack(side="left", padx=5)

        self.scroll_frame_todas_tarefas = ctk.CTkScrollableFrame(self.tab_tarefas, fg_color=COLOR_BACKGROUND, corner_radius=15)
        self.scroll_frame_todas_tarefas.pack(fill="both", expand=True, padx=10, pady=10)

    # --------------------------------- Funções Admin - Usuários ---------------------------------

    def mostrar_usuarios(self):
        for widget in self.scroll_frame_usuarios.winfo_children():
            widget.destroy()

        conexao = get_db_connection()
        if not conexao:
            return

        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT id, usuario FROM usuarios ORDER BY id")
            usuarios = cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao carregar usuários:\n{err}")
            usuarios = []
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

        for user in usuarios:
            self._criar_card_usuario(user)

    def _criar_card_usuario(self, user):
        card = ctk.CTkFrame(self.scroll_frame_usuarios, fg_color=COLOR_SECONDARY, corner_radius=12)
        card.pack(fill="x", pady=5, padx=10)

        lbl_usuario = ctk.CTkLabel(card, text=f"ID: {user['id']} | Usuário: {user['usuario']}", font=("Arial Bold", 14))
        lbl_usuario.pack(side="left", padx=10, pady=10)

        # Botões de Ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=10, pady=5)

        # Botões
        btn_gerenciar = ctk.CTkButton(btn_frame, text="Gerenciar Tarefas", width=120, fg_color="#3a7ca6", corner_radius=8,
                                      command=lambda uid=user['id'], unome=user['usuario']: self.abrir_gerenciar_usuario(uid, unome))
        btn_gerenciar.pack(side="right", padx=5)

        btn_resetar = ctk.CTkButton(btn_frame, text="Resetar Senha", width=100, fg_color="#d39c47", corner_radius=8,
                                    command=lambda uid=user['id']: self.resetar_senha(uid))
        btn_resetar.pack(side="right", padx=5)


        if user['usuario'] != 'admin':
            btn_excluir = ctk.CTkButton(btn_frame, text="Excluir", width=80, fg_color="#a63a3a", corner_radius=8,
                                        command=lambda uid=user['id']: self.excluir_usuario(uid))
            btn_excluir.pack(side="right", padx=5)

    def criar_usuario(self):

        usuario = self.entry_novo_usuario.get().strip()
        senha = self.entry_nova_senha.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Aviso", "Preencha todos os campos!")
            return

        conexao = get_db_connection()
        if not conexao:
            return

        try:
            cursor = conexao.cursor()
            cursor.execute("INSERT INTO usuarios (usuario, senha) VALUES (%s, %s)", (usuario, senha))
            conexao.commit()
            messagebox.showinfo("Sucesso", "Usuário criado com sucesso!")
            self.entry_novo_usuario.delete(0, "end")
            self.entry_nova_senha.delete(0, "end")
            self.mostrar_usuarios()
        except mysql.connector.IntegrityError:
            messagebox.showerror("Erro", "Usuário já existe!")
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao criar usuário:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

    def excluir_usuario(self, usuario_id):
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir este usuário e suas tarefas?"):
            conexao = get_db_connection()
            if not conexao:
                return
            try:
                cursor = conexao.cursor()
                cursor.execute("DELETE FROM usuarios WHERE id=%s", (usuario_id,))
                conexao.commit()
                messagebox.showinfo("Sucesso", "Usuário excluído com sucesso!")
                self.mostrar_usuarios()
                self.mostrar_todas_tarefas() # Atualiza a lista de tarefas também
            except mysql.connector.Error as err:
                messagebox.showerror("Erro de Banco de Dados", f"Erro ao excluir usuário:\n{err}")
            finally:
                if conexao and conexao.is_connected():
                    cursor.close()
                    conexao.close()

    def resetar_senha(self, usuario_id):
        # Reseta a senha de um usuário para '1234'
        conexao = get_db_connection()
        if not conexao:
            return
        try:
            cursor = conexao.cursor()
            nova_senha = "1234"
            cursor.execute("UPDATE usuarios SET senha=%s WHERE id=%s", (nova_senha, usuario_id))
            conexao.commit()
            messagebox.showinfo("Senha Redefinida", f"A nova senha do usuário é: {nova_senha}")
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao resetar senha:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

    # --------------------------------- Funções Admin - Tarefas ---------------------------------

    def limpar_filtros_admin(self):
        self.entry_search_admin.delete(0, "end")
        self.entry_filter_data_admin.delete(0, "end")
        self.mostrar_todas_tarefas()

    def mostrar_todas_tarefas(self):
        for widget in self.scroll_frame_todas_tarefas.winfo_children():
            widget.destroy()

        termo = self.entry_search_admin.get().strip()
        data_filtro = self.entry_filter_data_admin.get().strip()

        conexao = get_db_connection()
        if not conexao:
            return

        query = """
        SELECT t.*, u.usuario
        FROM tarefas t
        JOIN usuarios u ON t.usuario_id = u.id
        WHERE 1=1
        """
        params = []

        if termo:
            query += " AND (t.titulo LIKE %s OR t.descricao LIKE %s OR u.usuario LIKE %s)"
            like_termo = f"%{termo}%"
            params.extend([like_termo, like_termo, like_termo])

        if data_filtro:
            if not ListaDeTarefas(self.master, 0).validar_data(data_filtro):
                messagebox.showerror("Erro", "Data inválida no filtro. Use dd/mm/aaaa")
                return
            query += " AND t.data = %s"
            params.append(data_filtro)

        query += " ORDER BY t.id DESC"

        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute(query, tuple(params))
            tarefas = cursor.fetchall()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao carregar todas as tarefas:\n{err}")
            tarefas = []
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

        if not tarefas:
            ctk.CTkLabel(self.scroll_frame_todas_tarefas, text="Nenhuma tarefa encontrada.", text_color="gray").pack(pady=20)
            return

        for tarefa in tarefas:
            self._criar_card_todas_tarefas(tarefa)

    def _criar_card_todas_tarefas(self, tarefa):
        card = ctk.CTkFrame(self.scroll_frame_todas_tarefas, fg_color=COLOR_SECONDARY, corner_radius=12)
        card.pack(fill="x", pady=8, padx=10)
        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(fill="x", padx=10, pady=5)

        lbl_user = ctk.CTkLabel(content_frame, text=f"Usuário: {tarefa['usuario']}", font=("Arial Bold", 13))
        lbl_user.pack(anchor="w")

        lbl_titulo = ctk.CTkLabel(content_frame, text=f"Título: {tarefa['titulo']}", font=("Arial", 13))
        lbl_titulo.pack(anchor="w")

        lbl_data = ctk.CTkLabel(content_frame, text=f"Data: {tarefa['data']}", font=("Arial", 12))
        lbl_data.pack(anchor="w")

        lbl_desc = ctk.CTkLabel(content_frame, text=f"Descrição: {tarefa['descricao']}", wraplength=700, justify="left")
        lbl_desc.pack(anchor="w", pady=(5, 10))

        # Botões de Ação
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=(0, 5))

        btn_editar = ctk.CTkButton(btn_frame, text="Editar", width=80, fg_color="#3a7ca6", corner_radius=8,
                                   command=lambda tid=tarefa['id']: self.abrir_editar_admin(tid))
        btn_editar.pack(side="right", padx=5)

        btn_excluir = ctk.CTkButton(btn_frame, text="Excluir", width=80, fg_color="#a63a3a", corner_radius=8,
                                    command=lambda tid=tarefa['id']: self.excluir_tarefa_admin(tid))
        btn_excluir.pack(side="right", padx=5)

    def excluir_tarefa_admin(self, tarefa_id):

        if not messagebox.askyesno("Confirmar", "Excluir esta tarefa?"):
            return
        conexao = get_db_connection()
        if not conexao:
            return
        try:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM tarefas WHERE id=%s", (tarefa_id,))
            conexao.commit()
            messagebox.showinfo("OK", "Tarefa excluída.")
            self.mostrar_todas_tarefas() # Atualiza a lista de todas as tarefas
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao excluir tarefa:\n{err}")
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

    def abrir_editar_admin(self, tarefa_id):
        conexao = get_db_connection()
        if not conexao:
            return

        try:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM tarefas WHERE id=%s", (tarefa_id,))
            tarefa = cursor.fetchone()
        except mysql.connector.Error as err:
            messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar tarefa:\n{err}")
            return
        finally:
            if conexao and conexao.is_connected():
                cursor.close()
                conexao.close()

        if not tarefa:
            messagebox.showerror("Erro", "Tarefa não encontrada")
            return

        # Janela de edição
        top = ctk.CTkToplevel(self, fg_color=COLOR_FORM_BG)
        top.title("Editar Tarefa (Admin)")
        top.geometry("500x420")
        top.transient(self.master)

        lbl_t = ctk.CTkLabel(top, text="Título", font=("Arial", 12))
        lbl_t.pack(pady=(12,0))
        e_t = ctk.CTkEntry(top, width=420, corner_radius=8)
        e_t.pack(pady=6)
        e_t.insert(0, tarefa['titulo'])

        lbl_d = ctk.CTkLabel(top, text="Data (dd/mm/aaaa)", font=("Arial", 12))
        lbl_d.pack(pady=(8,0))
        e_d = ctk.CTkEntry(top, width=200, corner_radius=8)
        e_d.pack(pady=6)
        e_d.insert(0, tarefa['data'])

        lbl_desc = ctk.CTkLabel(top, text="Descrição", font=("Arial", 12))
        lbl_desc.pack(pady=(8,0))
        t_desc = ctk.CTkTextbox(top, width=420, height=150, corner_radius=8)
        t_desc.pack(pady=6)
        t_desc.insert("1.0", tarefa['descricao'])

        def salvar():
            novo_t = e_t.get().strip()
            novo_d = e_d.get().strip()
            novo_desc = t_desc.get("1.0", "end").strip()

            if not novo_t or not novo_desc:
                messagebox.showwarning("Aviso", "Título e Descrição são obrigatórios")
                return

            if novo_d and not ListaDeTarefas(self.master, 0).validar_data(novo_d):
                messagebox.showerror("Erro", "Data inválida. Use dd/mm/aaaa")
                return

            conexao_salvar = get_db_connection()
            if not conexao_salvar:
                return

            try:
                cursor_salvar = conexao_salvar.cursor()
                query = "UPDATE tarefas SET titulo=%s, data=%s, descricao=%s WHERE id=%s"
                params = (novo_t, novo_d, novo_desc, tarefa_id)
                cursor_salvar.execute(query, params)
                conexao_salvar.commit()
                messagebox.showinfo("Sucesso", "Tarefa atualizada")
                top.destroy()
                self.mostrar_todas_tarefas()
            except mysql.connector.Error as err:
                messagebox.showerror("Erro de Banco de Dados", f"Erro ao salvar tarefa:\n{err}")
            finally:
                if conexao_salvar and conexao_salvar.is_connected():
                    cursor_salvar.close()
                    conexao_salvar.close()

        # Botão com corner_radius
        ctk.CTkButton(top, text="Salvar", width=120, fg_color=COLOR_PRIMARY, corner_radius=8, command=salvar).pack(pady=10)

    def abrir_gerenciar_usuario(self, usuario_id, usuario_nome):
        janela = ctk.CTkToplevel(self, fg_color=COLOR_BACKGROUND)
        janela.title(f"Tarefas de {usuario_nome}")
        janela.geometry("700x550")
        janela.transient(self.master)

        topo = ctk.CTkFrame(janela, fg_color=COLOR_FORM_BG, corner_radius=12)
        topo.pack(fill="x", padx=10, pady=10)

        lbl = ctk.CTkLabel(topo, text=f"Gerenciando tarefas de: {usuario_nome}", font=("Arial Black", 16))
        lbl.pack(side="left", padx=6)

        filtro_frame = ctk.CTkFrame(janela, fg_color="transparent")
        filtro_frame.pack(fill="x", padx=10)

        entry_search = ctk.CTkEntry(filtro_frame, placeholder_text="Buscar (título/descrição)", width=300, corner_radius=8)
        entry_search.pack(side="left", padx=6)

        entry_data = ctk.CTkEntry(filtro_frame, placeholder_text="dd/mm/aaaa", width=140, corner_radius=8)
        entry_data.pack(side="left", padx=6)

        frame_scroll = ctk.CTkScrollableFrame(janela, fg_color=COLOR_BACKGROUND, corner_radius=15)
        frame_scroll.pack(fill="both", expand=True, padx=10, pady=10)

        def carregar_tarefas():
            termo = entry_search.get().strip()
            dataf = entry_data.get().strip()

            query = "SELECT * FROM tarefas WHERE usuario_id = %s"
            params = [usuario_id]

            if termo:
                query += " AND (titulo LIKE %s OR descricao LIKE %s)"
                like = f"%{termo}%"
                params.extend([like, like])

            if dataf:
                if not ListaDeTarefas(self.master, 0).validar_data(dataf):
                    messagebox.showerror("Erro", "Data inválida no filtro. Use dd/mm/aaaa")
                    return
                query += " AND data = %s"
                params.append(dataf)

            query += " ORDER BY id DESC"

            conexao = get_db_connection()
            if not conexao:
                return

            try:
                cursor = conexao.cursor(dictionary=True)
                cursor.execute(query, tuple(params))
                tarefas = cursor.fetchall()
            except mysql.connector.Error as err:
                messagebox.showerror("Erro de Banco de Dados", f"Erro ao carregar tarefas:\n{err}")
                tarefas = []
            finally:
                if conexao and conexao.is_connected():
                    cursor.close()
                    conexao.close()

            for w in frame_scroll.winfo_children():
                w.destroy()

            for tarefa in tarefas:
                card = ctk.CTkFrame(frame_scroll, fg_color=COLOR_SECONDARY, corner_radius=12)
                card.pack(fill="x", pady=8, padx=6)

                ctk.CTkLabel(card, text=f"Título: {tarefa['titulo']}", font=("Arial", 13)).pack(anchor="w", padx=8, pady=(6,0))
                ctk.CTkLabel(card, text=f"Data: {tarefa['data']}", font=("Arial", 12)).pack(anchor="w", padx=8)
                ctk.CTkLabel(card, text=f"Descrição: {tarefa['descricao']}", wraplength=600, justify="left").pack(anchor="w", padx=8, pady=(4,6))

                btns = ctk.CTkFrame(card, fg_color="transparent")
                btns.pack(fill="x", padx=6, pady=(0,6))

                # Botões com corner_radius
                ctk.CTkButton(btns, text="Editar", width=80, fg_color="#3a7ca6", corner_radius=8,
                              command=lambda tid=tarefa['id']: abrir_editar_admin_janela(tid, carregar_tarefas)).pack(side="right", padx=6)
                ctk.CTkButton(btns, text="Excluir", width=80, fg_color="#a63a3a", corner_radius=8,
                              command=lambda tid=tarefa['id']: excluir_tarefa_admin_janela(tid, carregar_tarefas)).pack(side="right", padx=6)

        def excluir_tarefa_admin_janela(tarefa_id, refresh_cb):
            if not messagebox.askyesno("Confirmar", "Excluir esta tarefa?"):
                return
            conexao = get_db_connection()
            if not conexao:
                return
            try:
                cursor = conexao.cursor()
                cursor.execute("DELETE FROM tarefas WHERE id=%s", (tarefa_id,))
                conexao.commit()
                messagebox.showinfo("OK", "Tarefa excluída.")
                refresh_cb()
                self.mostrar_todas_tarefas() 
            except mysql.connector.Error as err:
                messagebox.showerror("Erro de Banco de Dados", f"Erro ao excluir tarefa:\n{err}")
            finally:
                if conexao and conexao.is_connected():
                    cursor.close()
                    conexao.close()

        def abrir_editar_admin_janela(tarefa_id, refresh_cb):
            conexao = get_db_connection()
            if not conexao:
                return

            try:
                cursor = conexao.cursor(dictionary=True)
                cursor.execute("SELECT * FROM tarefas WHERE id=%s", (tarefa_id,))
                tarefa = cursor.fetchone()
            except mysql.connector.Error as err:
                messagebox.showerror("Erro de Banco de Dados", f"Erro ao buscar tarefa:\n{err}")
                return
            finally:
                if conexao and conexao.is_connected():
                    cursor.close()
                    conexao.close()

            if not tarefa:
                messagebox.showerror("Erro", "Tarefa não encontrada")
                return

            # Janela de edição
            top = ctk.CTkToplevel(janela, fg_color=COLOR_FORM_BG)
            top.title("Editar Tarefa")
            top.geometry("500x420")
            top.transient(janela)

            lbl_t = ctk.CTkLabel(top, text="Título", font=("Arial", 12))
            lbl_t.pack(pady=(12,0))
            e_t = ctk.CTkEntry(top, width=420, corner_radius=8)
            e_t.pack(pady=6)
            e_t.insert(0, tarefa['titulo'])

            lbl_d = ctk.CTkLabel(top, text="Data (dd/mm/aaaa)", font=("Arial", 12))
            lbl_d.pack(pady=(8,0))
            e_d = ctk.CTkEntry(top, width=200, corner_radius=8)
            e_d.pack(pady=6)
            e_d.insert(0, tarefa['data'])

            lbl_desc = ctk.CTkLabel(top, text="Descrição", font=("Arial", 12))
            lbl_desc.pack(pady=(8,0))
            # Textbox
            t_desc = ctk.CTkTextbox(top, width=420, height=150, corner_radius=8)
            t_desc.pack(pady=6)
            t_desc.insert("1.0", tarefa['descricao'])

            def salvar():
                novo_t = e_t.get().strip()
                novo_d = e_d.get().strip()
                novo_desc = t_desc.get("1.0", "end").strip()

                if not novo_t or not novo_desc:
                    messagebox.showwarning("Aviso", "Título e Descrição são obrigatórios")
                    return

                if novo_d and not ListaDeTarefas(self.master, 0).validar_data(novo_d):
                    messagebox.showerror("Erro", "Data inválida. Use dd/mm/aaaa")
                    return

                conexao_salvar = get_db_connection()
                if not conexao_salvar:
                    return

                try:
                    cursor_salvar = conexao_salvar.cursor()
                    query = "UPDATE tarefas SET titulo=%s, data=%s, descricao=%s WHERE id=%s"
                    params = (novo_t, novo_d, novo_desc, tarefa_id)
                    cursor_salvar.execute(query, params)
                    conexao_salvar.commit()
                    messagebox.showinfo("Sucesso", "Tarefa atualizada")
                    top.destroy()
                    refresh_cb() 
                    self.mostrar_todas_tarefas()
                except mysql.connector.Error as err:
                    messagebox.showerror("Erro de Banco de Dados", f"Erro ao salvar tarefa:\n{err}")
                finally:
                    if conexao_salvar and conexao_salvar.is_connected():
                        cursor_salvar.close()
                        conexao_salvar.close()


            ctk.CTkButton(top, text="Salvar", width=120, fg_color=COLOR_PRIMARY, corner_radius=8, command=salvar).pack(pady=10)


        # Botões de filtro
        btn_buscar = ctk.CTkButton(filtro_frame, text="Buscar", fg_color=COLOR_PRIMARY, corner_radius=8, command=carregar_tarefas)
        btn_buscar.pack(side="left", padx=6)

        btn_limpar = ctk.CTkButton(filtro_frame, text="Limpar", fg_color="gray", corner_radius=8, command=lambda: [entry_search.delete(0,'end'), entry_data.delete(0,'end'), carregar_tarefas()])
        btn_limpar.pack(side="left", padx=6)

        # carrega inicialmente
        carregar_tarefas()

    def logout(self):
        self.master.voltar_login()


# --------------------------------- Execução ---------------------------------

if __name__ == "__main__":
    app = App()
    app.mainloop()
