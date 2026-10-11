CREATE TABLE IF NOT EXISTS users (
    user_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    registration_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY unique_email (email)
) ENGINE=InnoDB;
CREATE TABLE IF NOT EXISTS todos (
    todo_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    is_done TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (todo_id),
    KEY idx_todos_user_id (user_id),
    CONSTRAINT fk_todos_users
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE
) ENGINE=InnoDB;