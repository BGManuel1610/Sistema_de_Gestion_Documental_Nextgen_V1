-- ==============================================================================
-- Sistema de Gestión Documental V1.1 — DocuSol (Soluciones en Documentación)
-- Base de Datos: nextgen_gd_db
-- Alcance Actual: Sprint 1 (HU001-HU005) & Sprint 2 (HU006-HU010)
-- Preparado para extensión a Sprint 3 (HU011-HU015), Sprint 4 (HU016-HU020) y Sprint 5 (HU021-HU030)
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS nextgen_gd_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE nextgen_gd_db;
SET NAMES utf8mb4;

-- ------------------------------------------------------------------------------
-- 1. Tabla: tbl_usuarios (HU001, HU002, Auditoría)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tbl_usuarios (
    usr_id INT AUTO_INCREMENT PRIMARY KEY,
    usr_nombre VARCHAR(100) NOT NULL,
    usr_email VARCHAR(120) NOT NULL UNIQUE,
    usr_password_hash VARCHAR(255) NOT NULL,
    usr_rol VARCHAR(50) NOT NULL,
    usr_sede VARCHAR(50) NOT NULL,
    usr_estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVO',
    usr_fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_usuarios_email (usr_email),
    INDEX idx_usuarios_rol (usr_rol),
    INDEX idx_usuarios_sede (usr_sede)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 2. Tabla: tbl_radicados (HU003, HU005, HU006, HU007, HU008, HU009, HU010)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tbl_radicados (
    rad_id INT AUTO_INCREMENT PRIMARY KEY,
    rad_codigo VARCHAR(30) NOT NULL UNIQUE,
    rad_remitente VARCHAR(150) NOT NULL,
    rad_asunto TEXT NOT NULL,
    rad_tipo_doc VARCHAR(50) NOT NULL,
    rad_sede_origen VARCHAR(50) NULL,
    rad_sede_destino VARCHAR(50) NOT NULL,
    rad_sede_actual VARCHAR(50) NOT NULL,
    rad_estado VARCHAR(50) NOT NULL DEFAULT 'RADICADO',
    rad_usuario_radicador INT NOT NULL,
    rad_usuario_gestionador INT NULL,
    rad_fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rad_fecha_limite DATETIME NOT NULL,
    CONSTRAINT fk_radicados_usr_radicador FOREIGN KEY (rad_usuario_radicador)
        REFERENCES tbl_usuarios(usr_id) ON UPDATE CASCADE,
    CONSTRAINT fk_radicados_usr_gestionador FOREIGN KEY (rad_usuario_gestionador)
        REFERENCES tbl_usuarios(usr_id) ON UPDATE CASCADE,
    INDEX idx_radicados_codigo (rad_codigo),
    INDEX idx_radicados_sede_actual (rad_sede_actual),
    INDEX idx_radicados_estado (rad_estado),
    INDEX idx_radicados_fecha_limite (rad_fecha_limite)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 3. Tabla: tbl_anexos (HU004)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tbl_anexos (
    anx_id INT AUTO_INCREMENT PRIMARY KEY,
    anx_rad_id INT NOT NULL,
    anx_nombre_original VARCHAR(255) NOT NULL,
    anx_ruta_archivo VARCHAR(500) NOT NULL,
    anx_tamano_kb DECIMAL(10, 2) NOT NULL,
    anx_fecha_carga DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    anx_usuario_id INT NULL,
    CONSTRAINT fk_anexos_radicado FOREIGN KEY (anx_rad_id)
        REFERENCES tbl_radicados(rad_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_anexos_usuario FOREIGN KEY (anx_usuario_id)
        REFERENCES tbl_usuarios(usr_id) ON UPDATE CASCADE,
    INDEX idx_anexos_rad_id (anx_rad_id),
    INDEX idx_anexos_usuario (anx_usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 4. Tabla: tbl_historial_traslados (HU005, HU008)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tbl_historial_traslados (
    tra_id INT AUTO_INCREMENT PRIMARY KEY,
    tra_rad_id INT NOT NULL,
    tra_sede_origen VARCHAR(50) NOT NULL,
    tra_sede_destino VARCHAR(50) NOT NULL,
    tra_usuario_id INT NOT NULL,
    tra_motivo TEXT NOT NULL,
    tra_fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tra_ip_origen VARCHAR(45) NULL,
    CONSTRAINT fk_traslados_radicado FOREIGN KEY (tra_rad_id)
        REFERENCES tbl_radicados(rad_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_traslados_usuario FOREIGN KEY (tra_usuario_id)
        REFERENCES tbl_usuarios(usr_id) ON UPDATE CASCADE,
    INDEX idx_traslados_rad_id (tra_rad_id),
    INDEX idx_traslados_fecha (tra_fecha_hora)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tbl_historial_aceptaciones (
    acep_id INT AUTO_INCREMENT PRIMARY KEY,
    acep_rad_id INT NOT NULL,
    acep_usuario_id INT NOT NULL,
    acep_sede VARCHAR(50) NOT NULL,
    acep_fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    acep_ip_origen VARCHAR(45) NULL,
    CONSTRAINT fk_aceptaciones_radicado FOREIGN KEY (acep_rad_id)
        REFERENCES tbl_radicados(rad_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_aceptaciones_usuario FOREIGN KEY (acep_usuario_id)
        REFERENCES tbl_usuarios(usr_id) ON UPDATE CASCADE,
    INDEX idx_aceptaciones_rad_id (acep_rad_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------------------------
-- 5. Tabla: tbl_respuestas (HU007)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tbl_respuestas (
    res_id INT AUTO_INCREMENT PRIMARY KEY,
    res_rad_id INT NOT NULL,
    res_ruta_pdf VARCHAR(500) NOT NULL,
    res_observacion TEXT NOT NULL,
    res_fecha_cierre DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_respuestas_radicado FOREIGN KEY (res_rad_id)
        REFERENCES tbl_radicados(rad_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_respuestas_rad_id (res_rad_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tbl_historial_cierres (
    cierre_id INT AUTO_INCREMENT PRIMARY KEY,
    cierre_rad_id INT NOT NULL,
    cierre_usuario_id INT NOT NULL,
    cierre_sede VARCHAR(50) NOT NULL,
    cierre_fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cierre_ip_origen VARCHAR(45) NULL,
    CONSTRAINT fk_cierres_radicado FOREIGN KEY (cierre_rad_id)
        REFERENCES tbl_radicados(rad_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_cierres_usuario FOREIGN KEY (cierre_usuario_id)
        REFERENCES tbl_usuarios(usr_id) ON UPDATE CASCADE,
    UNIQUE INDEX idx_cierres_rad_id (cierre_rad_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==============================================================================
-- DATOS SEMILLA (Seed Data inicial para pruebas de HU001-HU010)
-- Contraseña para todos los usuarios semilla: Password123!
-- Hash bcrypt correspondiente: $2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS
-- ==============================================================================

INSERT INTO tbl_usuarios (usr_id, usr_nombre, usr_email, usr_password_hash, usr_rol, usr_sede, usr_estado)
VALUES 
(1, 'Carlos Admin', 'admin@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Administrador', 'Bogotá', 'ACTIVO'),
(2, 'Laura Radicadora Bogotá', 'radicador.bogota@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Radicador', 'Bogotá', 'ACTIVO'),
(3, 'Andrés Gestionador Bogotá', 'gestionador.bogota@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Gestionador', 'Bogotá', 'ACTIVO'),
(4, 'Marta Radicadora Medellín', 'radicador.medellin@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Radicador', 'Medellín', 'ACTIVO'),
(5, 'Felipe Gestionador Medellín', 'gestionador.medellin@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Gestionador', 'Medellín', 'ACTIVO'),
(6, 'Diana Radicadora Cali', 'radicador.cali@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Radicador', 'Cali', 'ACTIVO'),
(7, 'Santiago Gestionador Cali', 'gestionador.cali@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Gestionador', 'Cali', 'ACTIVO')
ON DUPLICATE KEY UPDATE usr_email=usr_email;

INSERT INTO tbl_usuarios (usr_id, usr_nombre, usr_email, usr_password_hash, usr_rol, usr_sede, usr_estado)
VALUES
(8, 'Sofía Administradora Medellín', 'admin.medellin@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Administrador', 'Medellín', 'ACTIVO'),
(9, 'Julián Administrador Cali', 'admin.cali@docusol.com', '$2b$12$Nq99qB1lVnS68V5mK0oVTe9Wd0vO8E8B/4zszW32bKsqBwK6uN5vS', 'Administrador', 'Cali', 'ACTIVO')
ON DUPLICATE KEY UPDATE usr_email=usr_email;
