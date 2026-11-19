
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "saude-em-dia-chave-secreta"


# BANCO DE DADOS
def conectar_banco():
    conexao = sqlite3.connect("saude.db")
    conexao.row_factory = sqlite3.Row
    return conexao


def criar_banco():
    conexao = conectar_banco()

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    conexao.execute("""
        CREATE TABLE IF NOT EXISTS avaliacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            sono TEXT,
            atividade TEXT,
            alimentacao TEXT,
            agua TEXT,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    conexao.commit()
    conexao.close()


criar_banco()


# PÁGINA INICIAL
@app.route("/", methods=["GET", "POST"])
def inicio():
    resultados = None

    if request.method == "POST":
        sono = request.form.get("sono")
        atividade = request.form.get("atividade")
        alimentacao = request.form.get("alimentacao")
        agua = request.form.get("agua")

        resultados = []

        if sono == "bom":
            resultados.append({
                "titulo": "Sono",
                "status": "Bom",
                "mensagem": "Seus hábitos de sono parecem positivos."
            })
        else:
            resultados.append({
                "titulo": "Sono",
                "status": "Pode melhorar",
                "mensagem": "Tente manter horários regulares de descanso."
            })

        if atividade == "sim":
            resultados.append({
                "titulo": "Atividade física",
                "status": "Positivo",
                "mensagem": "Continue mantendo atividades adequadas."
            })
        else:
            resultados.append({
                "titulo": "Atividade física",
                "status": "Pode melhorar",
                "mensagem": "Procure incluir movimentos na rotina."
            })

        if alimentacao == "boa":
            resultados.append({
                "titulo": "Alimentação",
                "status": "Positivo",
                "mensagem": "Continue buscando variedade nos alimentos."
            })
        else:
            resultados.append({
                "titulo": "Alimentação",
                "status": "Pode melhorar",
                "mensagem": "Procure incluir variedade nas refeições."
            })

        if agua == "sim":
            resultados.append({
                "titulo": "Hidratação",
                "status": "Positivo",
                "mensagem": "Continue prestando atenção à hidratação."
            })
        else:
            resultados.append({
                "titulo": "Hidratação",
                "status": "Pode melhorar",
                "mensagem": "Lembre-se de beber água regularmente."
            })

    return render_template("index.html", resultados=resultados)


# CADASTRO
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    mensagem = ""

    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")

        if not nome or not email or not senha:
            mensagem = "Preencha todos os campos."
        else:
            conexao = conectar_banco()

            try:
                senha_hash = generate_password_hash(senha)

                conexao.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                    (nome, email, senha_hash)
                )

                conexao.commit()
                return redirect(url_for("login"))

            except sqlite3.IntegrityError:
                mensagem = "Este e-mail já está cadastrado."

            finally:
                conexao.close()

    return render_template("cadastro.html", mensagem=mensagem)


# LOGIN
@app.route("/login", methods=["GET", "POST"])
def login():
    mensagem = ""

    if request.method == "POST":
        email = request.form.get("email")
        senha = request.form.get("senha")

        conexao = conectar_banco()

        usuario = conexao.execute(
            "SELECT * FROM usuarios WHERE email = ?",
            (email,)
        ).fetchone()

        conexao.close()

        if usuario and check_password_hash(usuario["senha"], senha):
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]

            return redirect(url_for("painel"))

        mensagem = "E-mail ou senha incorretos."

    return render_template("login.html", mensagem=mensagem)


# PAINEL DO USUÁRIO
@app.route("/painel")
def painel():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "painel.html",
        nome=session["usuario_nome"]
    )


# AVALIAÇÃO
@app.route("/avaliacao", methods=["GET", "POST"])
def avaliacao():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        sono = request.form.get("sono")
        atividade = request.form.get("atividade")
        alimentacao = request.form.get("alimentacao")
        agua = request.form.get("agua")

        conexao = conectar_banco()

        conexao.execute("""
            INSERT INTO avaliacoes
            (usuario_id, sono, atividade, alimentacao, agua)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["usuario_id"],
            sono,
            atividade,
            alimentacao,
            agua
        ))

        conexao.commit()
        conexao.close()

        return redirect(url_for("historico"))

    return render_template("avaliacao.html")


# HISTÓRICO
@app.route("/historico")
def historico():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conexao = conectar_banco()

    avaliacoes = conexao.execute("""
        SELECT * FROM avaliacoes
        WHERE usuario_id = ?
        ORDER BY id DESC
    """, (session["usuario_id"],)).fetchall()

    conexao.close()

    return render_template("historico.html", avaliacoes=avaliacoes)


# SAIR
@app.route("/sair")
def sair():
    session.clear()
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)
