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

-- Tabela de Fazendas
CREATE TABLE fazendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
	id_endereco INT,
    nome_fazenda VARCHAR(100),
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
    peso DECIMAL(10,3),
    FOREIGN KEY (id_fazenda) REFERENCES fazendas(id)
);

-- Tabela de Inseminadores
CREATE TABLE inseminadores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome_inseminador VARCHAR(100)
);

CREATE TABLE vendedores (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    cpf VARCHAR(11) UNIQUE NOT NULL
);

-- Tabela de Vendas
CREATE TABLE vendas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_fazenda INT,
	id_vendedor INT,
	protocolo varchar(100),
    data_venda DATE,
    valor_total DECIMAL(10, 2),
    FOREIGN KEY (id_fazenda) REFERENCES fazendas(id),
	FOREIGN KEY (id_vendedor) REFERENCES vendedores(id)
);

CREATE TABLE visitas(
    id int AUTO_INCREMENT PRIMARY KEY,
    id_fazenda int NOT NULL,
    id_vendedor int NOT NULL,
    id_venda int,
    data_visita date NOT NULL,
    houve_venda TINYINT NOT NULL,
    FOREIGN KEY (id_vendedor) REFERENCES vendedores(id),
    FOREIGN KEY (id_fazenda) REFERENCES fazendas(id)
);

-- Tabela de Resultados de Inseminação
CREATE TABLE resultados_inseminacao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_vaca INT,
	protocolo varchar(100),
    touro varchar(100),
    id_inseminador INT,
    id_venda INT,
    data_inseminacao DATE,
    numero_IATF VARCHAR(100),
    DG TINYINT,
    vazia_Com_Ou_Sem_CL TINYINT,
    perda TINYINT,
    FOREIGN KEY (id_vaca) REFERENCES vacas(id),
    FOREIGN KEY (id_inseminador) REFERENCES inseminadores(id),
    FOREIGN KEY (id_venda) REFERENCES vendas(id)
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