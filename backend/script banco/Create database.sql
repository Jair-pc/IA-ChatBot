CREATE DATABASE IF NOT EXISTS empresa_inseminacao;
USE empresa_inseminacao;

-- tabela de endereços --
CREATE TABLE endereco (
	id INT AUTO_INCREMENT PRIMARY KEY,
    rua VARCHAR(100),
	numero int,
    bairro VARCHAR(100),
    cidade VARCHAR(100),
    estado VARCHAR(2),
	pais VARCHAR(100)
);

-- Tabela de Clientes (Fazendas)
CREATE TABLE clientes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_endereco INT,
    nome_cliente VARCHAR(100),
    email VARCHAR(100),
    telefone VARCHAR(20),
	FOREIGN KEY (id_endereco) REFERENCES endereco(id)
);

-- Tabela de Fazendas
CREATE TABLE fazendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
	id_cliente INT,
	id_endereco INT,
    nome_fazenda VARCHAR(100),
	FOREIGN KEY (id_cliente) REFERENCES clientes(id),
	FOREIGN KEY (id_endereco) REFERENCES endereco(id)
);

-- Tabela de vacas
CREATE TABLE vacas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_fazenda INT,
    numero_animal INT,
    lote VARCHAR(50),
    vaca VARCHAR(50),
    categoria VARCHAR(50),
    ECC FLOAT,
    ciclicidade INT,
    FOREIGN KEY (id_fazenda) REFERENCES fazendas(id)
);

-- Tabela de Protocolos de Inseminação
CREATE TABLE protocolos_inseminacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    protocolo VARCHAR(100),
    dias_protocolo INT,
    implante_P4 VARCHAR(100),
    empresa VARCHAR(100),
    GnRH_NA_IA TINYINT,
    PGF_NO_D0 INT,
    dose_PGF_retirada DECIMAL(10,2),
    marca_PGF_retirada VARCHAR(100),
    dose_CE DECIMAL(10,2),
    eCG VARCHAR(100),
    dose_eCG DECIMAL(10,2)
);

-- Tabela de Inseminadores
CREATE TABLE inseminadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_inseminador VARCHAR(100)
);

-- Tabela de Touros
CREATE TABLE touros (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_touro VARCHAR(100),
    raca_touro VARCHAR(50),
    empresa_touro VARCHAR(100)
);

CREATE TABLE vendedor (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    cpf VARCHAR(11) UNIQUE NOT NULL
);

CREATE TABLE visitas(
    id int AUTO_INCREMENT PRIMARY KEY,
    id_fazenda int NOT NULL,
    data_visita date NOT NULL,
    FOREIGN KEY (id_fazenda) REFERENCES fazendas(id)
);

-- Tabela de Vendas
CREATE TABLE vendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT,
	id_vendedor INT,
    data_venda DATE,
    valor_total DECIMAL(10, 2),
    FOREIGN KEY (id_cliente) REFERENCES clientes(id),
	FOREIGN KEY (id_vendedor) REFERENCES vendedor(id)
);


-- Tabela de Resultados de Inseminação
CREATE TABLE resultados_inseminacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_vaca INT,
    id_protocolo INT,
    id_touro INT,
    id_inseminador INT,
    id_venda INT,
    data_inseminacao DATE,
    numero_IATF VARCHAR(100),
    DG TINYINT,
    vazia_Com_Ou_Sem_CL tinyint,
    perda TINYINT,
    FOREIGN KEY (id_vaca) REFERENCES vacas(id),
    FOREIGN KEY (id_protocolo) REFERENCES protocolos_inseminacao(id),
    FOREIGN KEY (id_touro) REFERENCES touros(id),
    FOREIGN KEY (id_inseminador) REFERENCES inseminadores(id),
    FOREIGN KEY (id_venda) REFERENCES vendas(id)
);

CREATE TABLE IF NOT EXISTS produtos (
  id INT NOT NULL AUTO_INCREMENT,
  nome VARCHAR(100) NULL DEFAULT NULL,
  quantidade INT NULL DEFAULT NULL,
  preco DECIMAL(10,2),
  touro INT NULL DEFAULT NULL,
  PRIMARY KEY (id),
  FOREIGN KEY (touro) REFERENCES touros (id));

CREATE TABLE IF NOT EXISTS item_venda (
  vendas_id INT NOT NULL,
  produto_id INT NOT NULL,
  quantidade INT NULL,
  preco_unitario DECIMAL(10, 2),
  PRIMARY KEY (vendas_id, produto_id),
  FOREIGN KEY (vendas_id) REFERENCES vendas (id),
  FOREIGN KEY (produto_id) REFERENCES produtos (id)
);

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(25) UNIQUE NOT NULL,
    password VARCHAR(25) NOT NULL
);

CREATE TABLE chats (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(40) NOT NULL,
    user_id INT NOT NULL,
    id_gpt TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    text_usuario TEXT NOT NULL,
    text_servidor TEXT NOT NULL,
    chat_id INT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);